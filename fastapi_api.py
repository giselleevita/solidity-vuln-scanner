"""
FastAPI REST API for Solidity Vuln Scanner
Provides endpoints for contract analysis and report generation
"""

import time
import json
from typing import Optional
from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.responses import JSONResponse, HTMLResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from report_generator import generate_html_report, generate_markdown_report, generate_sarif_report
from tools_integration import run_slither, run_mythril, check_slither_installed, check_mythril_installed
from static_analyzer import StaticAnalyzer, AnalysisResult
from llm_auditor import LLMAuditor
from app_config import get_config
from logger_config import setup_logging, get_logger
from exceptions import (
    AnalysisException, ValidationError, LLMAuditException,
    PatternCompilationError, ScannerException
)
from input_validator import validate_contract_code, sanitize_contract_code, validate_contract_name
import re

# Import optional features
try:
    from middleware import analysis_cache
except ImportError as e:
    analysis_cache = None
    print("⚠️  Caching not available")

# Import rate limiting components (safe import with fallback)
# Initialize variables first to avoid NameError
RateLimitMiddleware = None
rate_limiter = None

try:
    from middleware import RateLimitMiddleware, rate_limiter
    # Update analysis_cache if not already set
    if 'analysis_cache' not in globals() or analysis_cache is None:
        try:
            from middleware import analysis_cache
        except ImportError:
            analysis_cache = None
except ImportError as e:
    print("⚠️  Rate limiting middleware not available")


# Request/Response models
class ContractAnalysisRequest(BaseModel):
    contract_code: str
    contract_name: str = "Contract"
    use_llm_audit: bool = True


class ContractAnalysisResponse(BaseModel):
    contract_name: str
    analysis_date: str
    risk_score: float
    severity: str
    vulnerabilities: list
    llm_audit: Optional[dict] = None
    lines_of_code: int
    analysis_time_ms: int
    slither: Optional[dict] = None
    mythril: Optional[dict] = None


class CrossValidateRequest(BaseModel):
    contract_code: str
    contract_name: str = "Contract"
    run_slither: bool = False
    run_mythril: bool = False
    use_llm_audit: bool = True


class CrossValidateResponse(BaseModel):
    analysis: ContractAnalysisResponse
    slither: Optional[dict] = None
    mythril: Optional[dict] = None


class HealthResponse(BaseModel):
    status: str
    version: str
    llm_enabled: bool


# Setup logging
logger = setup_logging(log_level="INFO" if not get_config().debug else "DEBUG")
app_logger = get_logger(__name__)

# Initialize app
app = FastAPI(
    title="Solidity Vuln Scanner API",
    description="AI-powered vulnerability detection for Ethereum smart contracts",
    version="1.0.0"
)

# Add CORS middleware (configurable)
config = get_config()
cors_origins = ["*"] if config.cors_origins == "*" else [origin.strip() for origin in config.cors_origins.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app_logger.info(f"CORS configured with origins: {cors_origins}")

# Add rate limiting middleware (only if available)
if RateLimitMiddleware is not None and rate_limiter is not None:
    app.add_middleware(RateLimitMiddleware, rate_limiter=rate_limiter)
else:
    print("⚠️  Rate limiting middleware not available")

# Initialize components
try:
    config = get_config()
    app_logger.info("Configuration loaded successfully")
except Exception as e:
    app_logger.error(f"Failed to load configuration: {e}")
    raise

try:
    static_analyzer = StaticAnalyzer()
    app_logger.info("Static analyzer initialized")
except Exception as e:
    app_logger.error(f"Failed to initialize static analyzer: {e}")
    raise

# Initialize LLM ONLY if explicitly enabled AND API key is provided
# Default is disabled (free mode - static analysis only)
llm_auditor = None
if config.use_llm and config.llm_api_key and config.llm_api_key.strip():
    try:
        llm_auditor = LLMAuditor(
            api_key=config.llm_api_key,
            model=config.llm_model,
            provider=config.llm_provider
        )
        print("✅ LLM auditor initialized (AI features enabled)")
    except Exception as e:
        print(f"⚠️  Warning: LLM auditor not available: {e}")
        print("   Continuing with static analysis only (free mode).")
else:
    # LLM is disabled - this is normal for free mode
    if not config.use_llm:
        print("ℹ️  LLM features disabled - Running in free mode (static analysis only)")
    elif not config.llm_api_key or not config.llm_api_key.strip():
        print("ℹ️  No LLM API key configured - Running in free mode (static analysis only)")


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint
    Verifies API is running and LLM is configured
    """
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        llm_enabled=llm_auditor is not None
    )


async def _analyze_static_and_llm(request: ContractAnalysisRequest, start_time: float):
    """
    Helper function to run static analysis and optional LLM audit
    
    Args:
        request: ContractAnalysisRequest with contract code
        start_time: Timestamp when analysis started (for timing calculation)
        
    Returns:
        Complete security analysis report
        
    Raises:
        HTTPException: For validation or analysis errors
    """
    # Validate and sanitize input
    is_valid, error_msg = validate_contract_code(request.contract_code)
    if not is_valid:
        app_logger.warning(f"Invalid contract code: {error_msg}")
        raise HTTPException(status_code=400, detail=error_msg)
    
    is_valid, error_msg = validate_contract_name(request.contract_name)
    if not is_valid:
        app_logger.warning(f"Invalid contract name: {error_msg}")
        raise HTTPException(status_code=400, detail=error_msg)
    
    # Sanitize contract code
    sanitized_code = sanitize_contract_code(request.contract_code)
    
    app_logger.info(f"Analyzing contract: {request.contract_name} ({len(sanitized_code)} chars)")
    
    # Run static analysis
    try:
        static_result = static_analyzer.analyze(
            sanitized_code,
            request.contract_name
        )
        app_logger.info(f"Static analysis completed: {len(static_result.vulnerabilities)} vulnerabilities found")
    except Exception as e:
        app_logger.error(f"Static analysis failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Static analysis failed: {str(e)}"
        )
    
    # Run LLM audit if enabled and available (use async if available)
    llm_result = None
    if request.use_llm_audit and llm_auditor:
        try:
            app_logger.info("Starting LLM audit...")
            # Use async method if available (we're in async context)
            if hasattr(llm_auditor, 'audit_async') and llm_auditor.async_client:
                llm_result = await llm_auditor.audit_async(
                    sanitized_code,
                    request.contract_name
                )
            else:
                # Fallback to sync (run in executor to avoid blocking)
                import asyncio
                loop = asyncio.get_event_loop()
                llm_result = await loop.run_in_executor(
                    None,
                    llm_auditor.audit,
                    sanitized_code,
                    request.contract_name
                )
            app_logger.info(f"LLM audit completed: {llm_result.risk_assessment} (tokens: {llm_result.tokens_used})")
        except Exception as e:
            app_logger.error(f"LLM audit failed: {e}", exc_info=True)
            # Continue without LLM audit but log the error
            # Don't fail the entire request if LLM fails
    
    # Calculate analysis time
    analysis_time_ms = int((time.time() - start_time) * 1000)
    static_result.analysis_time_ms = analysis_time_ms
    
    # Build response
    response_data = {
        "contract_name": static_result.contract_name,
        "analysis_date": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
        "risk_score": static_result.risk_score,
        "severity": static_result._get_overall_severity(),
        "vulnerabilities": [v.to_dict() for v in static_result.vulnerabilities],
        "lines_of_code": static_result.lines_of_code,
        "analysis_time_ms": analysis_time_ms
    }
    
    if llm_result:
        response_data["llm_audit"] = llm_result.to_dict()
    
    return ContractAnalysisResponse(**response_data)
@app.post("/analyze", response_model=ContractAnalysisResponse)
async def analyze_contract(request: ContractAnalysisRequest):
    """
    Main analysis endpoint
    Performs static analysis and optional LLM audit
    Uses caching to avoid re-analyzing identical contracts
    """
    start_time = time.time()
    
    # Input validation is now handled in _analyze_static_and_llm
    
    # Check cache first (if available)
    if analysis_cache:
        cached_result = analysis_cache.get(request.contract_code, request.contract_name)
        if cached_result and not request.use_llm_audit:  # Only cache static analysis
            return ContractAnalysisResponse(**cached_result)
    
    try:
        result = _analyze_static_and_llm(request, start_time)
        
        # Cache static-only results (if cache available)
        if analysis_cache and not request.use_llm_audit:
            result_dict = result.dict() if hasattr(result, 'dict') else result
            analysis_cache.set(request.contract_code, request.contract_name, result_dict)
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        app_logger.error(f"Unexpected error in analyze_contract: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.post("/cross-validate", response_model=CrossValidateResponse)
async def cross_validate(request: CrossValidateRequest):
    """
    Run static/LLM analysis plus optional Slither/Mythril (if installed).
    """
    start_time = time.time()
    if not request.contract_code or not request.contract_code.strip():
        raise HTTPException(status_code=400, detail="Contract code cannot be empty")
    if len(request.contract_code) > config.max_file_size_mb * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail=f"Contract code too large (max {config.max_file_size_mb}MB)"
        )

    try:
        analysis = await _analyze_static_and_llm(
            ContractAnalysisRequest(
                contract_code=request.contract_code,
                contract_name=request.contract_name,
                use_llm_audit=request.use_llm_audit,
            ),
            start_time,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

    slither_out = None
    mythril_out = None

    if request.run_slither:
        try:
            ok, out = run_slither(request.contract_code, f"{request.contract_name}.sol")
            slither_out = {"success": ok, "output": out}
        except Exception as e:
            slither_out = {"success": False, "output": f"Error running Slither: {str(e)}"}

    if request.run_mythril:
        try:
            ok, out = run_mythril(request.contract_code, f"{request.contract_name}.sol")
            mythril_out = {"success": ok, "output": out}
        except Exception as e:
            mythril_out = {"success": False, "output": f"Error running Mythril: {str(e)}"}

    return CrossValidateResponse(
        analysis=analysis,
        slither=slither_out,
        mythril=mythril_out,
    )


@app.post("/analyze-batch")
async def analyze_batch(contracts: list[ContractAnalysisRequest]):
    """
    Batch analysis endpoint
    Analyze multiple contracts at once
    
    Args:
        contracts: List of contracts to analyze
        
    Returns:
        List of analysis results
    """
    if len(contracts) > 10:
        raise HTTPException(
            status_code=400,
            detail="Batch size limited to 10 contracts"
        )
    
    results = []
    for contract in contracts:
        try:
            # Recursively call analyze endpoint
            result = await analyze_contract(contract)
            results.append(result)
        except Exception as e:
            results.append({
                "contract_name": contract.contract_name,
                "error": str(e)
            })
    
    return results


@app.post("/upload-and-analyze")
async def upload_and_analyze(file: UploadFile = File(...)):
    """
    Upload contract file and analyze
    Accepts .sol files
    """
    if not file.filename.endswith('.sol'):
        raise HTTPException(
            status_code=400,
            detail="File must be a .sol Solidity contract"
        )
    
    try:
        content = await file.read()
        contract_code = content.decode('utf-8')
        
        request = ContractAnalysisRequest(
            contract_code=contract_code,
            contract_name=file.filename.replace('.sol', '')
        )
        
        return await analyze_contract(request)
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"File processing error: {str(e)}")


@app.get("/tools/status")
async def get_tools_status():
    """Check status of external tools (Slither, Mythril)"""
    slither_ok, slither_msg = check_slither_installed()
    mythril_ok, mythril_msg = check_mythril_installed()
    
    return {
        "slither": {
            "installed": slither_ok,
            "message": slither_msg
        },
        "mythril": {
            "installed": mythril_ok,
            "message": mythril_msg
        }
    }


@app.get("/vulnerabilities")
async def get_vulnerability_definitions():
    """
    Get definitions of all vulnerability types
    Useful for understanding what scanner detects
    """
    vuln_descriptions = {
        "reentrancy": "Reentrancy attacks allow a malicious contract to repeatedly call a function before the first execution is completed",
        "unchecked_call": "Low-level calls (send, call) may fail silently if return value is not checked",
        "overflow_underflow": "Integer arithmetic without SafeMath can overflow or underflow, causing unexpected behavior",
        "access_control": "Missing access control modifiers allow unauthorized calls to sensitive functions",
        "bad_randomness": "Using blockchain properties for randomness is predictable and exploitable",
        "tx_origin": "Using tx.origin for authorization is vulnerable to phishing attacks through contract intermediaries",
        "delegatecall": "Unsafe delegatecall to attacker-controlled addresses can lead to complete contract takeover",
        "gas_dos": "Unbounded loops or expensive operations can cause Out-of-Gas exceptions (Denial of Service)",
        "timestamp": "Relying on block.timestamp for critical logic is unreliable due to miner influence",
        "selfdestruct": "Selfdestruct can destroy contracts unexpectedly, freezing funds"
    }
    
    return {
        "vulnerabilities": vuln_descriptions,
        "total": len(vuln_descriptions)
    }


@app.post("/analyze-sarif")
async def analyze_contract_sarif(request: ContractAnalysisRequest):
    """
    Analyze contract and return SARIF format (for GitHub Code Scanning)
    """
    start_time = time.time()
    if not request.contract_code or not request.contract_code.strip():
        raise HTTPException(status_code=400, detail="Contract code cannot be empty")
    
    try:
        result = await _analyze_static_and_llm(request, start_time)
        sarif = generate_sarif_report(result.dict() if hasattr(result, 'dict') else result)
        return JSONResponse(content=sarif, media_type="application/sarif+json")
    except HTTPException:
        raise
    except Exception as e:
        app_logger.error(f"Error generating SARIF report: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
async def root():
    """Root endpoint with API documentation"""
    return {
        "name": "Solidity Vuln Scanner API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "analyze": "POST /analyze",
            "analyze-sarif": "POST /analyze-sarif",
            "batch": "POST /analyze-batch",
            "upload": "POST /upload-and-analyze",
            "vulnerabilities": "GET /vulnerabilities",
            "docs": "/docs"
        },
        "docs": "Visit /docs for interactive API documentation"
    }


def main():
    """Run the API server"""
    uvicorn.run(
        app,
        host=config.api_host,
        port=config.api_port,
        reload=config.debug
    )


if __name__ == "__main__":
    main()
