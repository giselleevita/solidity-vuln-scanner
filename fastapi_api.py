"""
FastAPI REST API for Solidity Vuln Scanner
Provides endpoints for contract analysis and report generation
"""

import time
import json
import asyncio
from typing import Optional, List
from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException, File, UploadFile, Depends, Request
from fastapi.responses import JSONResponse, HTMLResponse, Response
from pathlib import Path
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
from webhook_manager import webhook_manager
from monitoring import MetricsMiddleware, record_analysis, get_metrics_endpoint, get_health_check

# Optional PDF support
try:
    from pdf_report import generate_pdf_report_bytes
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    if 'app_logger' in globals():
        app_logger.warning("PDF reports not available (reportlab not installed)")

# Optional queue system
try:
    from queue_system import submit_analysis_job, get_job_status
    QUEUE_AVAILABLE = True
except ImportError:
    QUEUE_AVAILABLE = False
    if 'app_logger' in globals():
        app_logger.warning("Queue system not available (celery/redis not installed)")
    def submit_analysis_job(*args, **kwargs):
        raise HTTPException(status_code=503, detail="Queue system not available")
    def get_job_status(*args, **kwargs):
        return {"status": "unavailable", "error": "Queue system not available"}

from multi_file_analyzer import multi_file_analyzer
try:
    from professional_auditor import ProfessionalAuditor, ProfessionalAuditResult
    from professional_report import (
        generate_professional_audit_report_pdf,
        generate_professional_audit_report_json,
        generate_professional_audit_report_html
    )
    PROFESSIONAL_AUDIT_AVAILABLE = True
except ImportError as e:
    PROFESSIONAL_AUDIT_AVAILABLE = False
    app_logger.warning(f"Professional audit features not available: {e}")
from pathlib import Path
import re
import os

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


# Import shared models
from models import (
    ContractAnalysisRequest,
    ContractAnalysisResponse,
    CrossValidateRequest,
    CrossValidateResponse,
    HealthResponse,
    ErrorResponse,
    ProfessionalAuditRequest
)
from fastapi.responses import JSONResponse
import uuid


# Setup logging
logger = setup_logging(log_level="INFO" if not get_config().debug else "DEBUG")
app_logger = get_logger(__name__)

# Initialize app
app = FastAPI(
    title="Solidity Vuln Scanner API",
    description="AI-powered vulnerability detection for Ethereum smart contracts",
    version="1.0.0"
)

# Add request ID middleware for tracing
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """Add unique request ID to each request for tracing"""
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response

# Global exception handler for standardized error responses
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Standardized error response format"""
    request_id = getattr(request.state, "request_id", "unknown")
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=exc.detail if isinstance(exc.detail, str) else "An error occurred",
            code=f"HTTP_{exc.status_code}",
            message=exc.detail if isinstance(exc.detail, str) else None,
            details={"request_id": request_id}
        ).dict()
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions"""
    request_id = getattr(request.state, "request_id", "unknown")
    app_logger.error(f"Unhandled exception: {exc}", exc_info=True, extra={"request_id": request_id})
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal server error",
            code="INTERNAL_ERROR",
            message="An unexpected error occurred",
            details={"request_id": request_id}
        ).dict()
    )

# Include versioned API router (after app creation to avoid circular imports)
# Defer import to avoid circular dependency
def _include_v1_router():
    try:
        from api_v1 import router as v1_router
        app.include_router(v1_router)
        app_logger.info("API v1 router included")
    except Exception as e:
        app_logger.warning(f"Failed to include v1 router: {e}")

# Call after app is fully initialized
_include_v1_router()

# Add CORS middleware (configurable with security restrictions)
config = get_config()
if config.cors_origins == "*":
    cors_origins = ["*"]
    # Security warning: wildcard + credentials is dangerous
    if config.production_mode:
        app_logger.warning(
            "⚠️  SECURITY WARNING: CORS allows all origins with credentials enabled. "
            "This is insecure. Set CORS_ORIGINS to specific domains in production."
        )
    # Disable credentials when using wildcard (security best practice)
    allow_creds = False
else:
    cors_origins = [origin.strip() for origin in config.cors_origins.split(",") if origin.strip()]
    allow_creds = True  # Safe to allow credentials with specific origins

# Default to localhost if no origins specified and not wildcard
if not cors_origins or (cors_origins == ["*"] and config.production_mode):
    cors_origins = ["http://localhost:8501", "http://localhost:3000"]
    app_logger.warning("CORS origins defaulted to localhost. Set CORS_ORIGINS for production.")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=allow_creds,
    allow_methods=["GET", "POST", "OPTIONS"],  # Restrict methods
    allow_headers=["Content-Type", "Authorization", "X-API-Key"],  # Restrict headers
)
app_logger.info(f"CORS configured with origins: {cors_origins}, credentials: {allow_creds}")

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


@app.get("/health/detailed")
async def health_check_detailed():
    """Detailed health check with system metrics"""
    return get_health_check()


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    from monitoring import generate_latest, CONTENT_TYPE_LATEST
    from fastapi.responses import Response
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )


@app.post("/analyze-async")
async def analyze_contract_async(request: ContractAnalysisRequest):
    """Submit analysis job to queue (async processing)"""
    if not QUEUE_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Queue system not available. Install celery and redis: pip install celery redis"
        )
    try:
        task_id = submit_analysis_job(
            request.contract_code,
            request.contract_name,
            request.use_llm_audit
        )
        return {
            "task_id": task_id,
            "status": "submitted",
            "message": "Analysis job submitted to queue"
        }
    except Exception as e:
        logger.error(f"Failed to submit job: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to submit job: {str(e)}")


@app.get("/jobs/{task_id}")
async def get_job(task_id: str):
    """Get status of an analysis job"""
    status = get_job_status(task_id)
    return status


@app.post("/analyze-project")
async def analyze_project(file: UploadFile = File(...)):
    """Analyze a project (zip file with contracts) with secure file handling"""
    import zipfile
    import tempfile
    from input_validator import sanitize_filename
    
    if not file.filename or not file.filename.endswith('.zip'):
        raise HTTPException(status_code=400, detail="File must be a .zip archive")
    
    # Sanitize filename
    safe_filename = sanitize_filename(file.filename)
    
    try:
        # Use secure temporary directory (auto-cleans up)
        with tempfile.TemporaryDirectory() as tmpdir:
            # Save uploaded file to secure location
            temp_zip_path = os.path.join(tmpdir, safe_filename)
            content = await file.read()
            
            # Check file size before writing
            max_size = config.max_file_size_mb * 1024 * 1024
            if len(content) > max_size:
                raise HTTPException(
                    status_code=400,
                    detail=f"File too large ({len(content)} bytes, max {max_size} bytes)"
                )
            
            with open(temp_zip_path, 'wb') as f:
                f.write(content)
            
            # Extract and analyze (zipfile auto-handles traversal attempts)
            extract_dir = os.path.join(tmpdir, "extracted")
            os.mkdir(extract_dir)
            
            with zipfile.ZipFile(temp_zip_path, 'r') as zip_ref:
                # Validate zip file first
                zip_ref.testzip()
                # Extract to secure directory
                zip_ref.extractall(extract_dir)
            
            project_path = Path(extract_dir)
            results = multi_file_analyzer.analyze_project(project_path)
            
            # Convert Path objects to strings for JSON serialization
            return {
                "project_type": multi_file_analyzer.detect_project_type(project_path),
                "files_analyzed": len(results),
                "results": {
                    str(k): v.to_dict() for k, v in results.items()
                }
            }
            # Temporary directory auto-cleans up here
    except zipfile.BadZipFile:
        raise HTTPException(status_code=400, detail="Invalid zip file")
    except Exception as e:
        logger.error(f"Project analysis failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Project analysis failed: {str(e)}")


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
        
        # Record metrics
        try:
            result_dict = result.dict() if hasattr(result, 'dict') else result
            record_analysis(
                severity=result_dict.get('severity', 'UNKNOWN'),
                has_llm=result_dict.get('llm_audit') is not None,
                duration=(time.time() - start_time),
                analysis_type="static",
                vulnerability_count=len(result_dict.get('vulnerabilities', [])),
                vulnerabilities=result_dict.get('vulnerabilities', [])
            )
        except Exception as e:
            app_logger.warning(f"Metrics recording failed: {e}")
        
        # Trigger webhooks (async, don't wait)
        try:
            result_dict = result.dict() if hasattr(result, 'dict') else result
            asyncio.create_task(webhook_manager.notify_analysis_completed(
                request.contract_name,
                result_dict
            ))
        except Exception as e:
            app_logger.warning(f"Webhook notification failed: {e}")
        
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


@app.post("/analyze-pdf")
async def analyze_contract_pdf(request: ContractAnalysisRequest):
    """Analyze contract and return PDF report"""
    if not PDF_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="PDF reports not available. Install reportlab: pip install reportlab"
        )
    
    from fastapi.responses import Response
    
    start_time = time.time()
    try:
        result = await _analyze_static_and_llm(request, start_time)
        result_dict = result.dict() if hasattr(result, 'dict') else result
        pdf_bytes = generate_pdf_report_bytes(result_dict)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{request.contract_name}_audit.pdf"'
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        app_logger.error(f"Error generating PDF: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/webhooks/register")
async def register_webhook(
    url: str,
    events: Optional[List[str]] = None,
    secret: Optional[str] = None
):
    """Register a webhook URL"""
    webhook_id = webhook_manager.register_webhook(url, events, secret)
    return {"webhook_id": webhook_id, "url": url, "status": "registered"}


@app.delete("/webhooks/{webhook_id}")
async def unregister_webhook(webhook_id: str):
    """Unregister a webhook"""
    success = webhook_manager.unregister_webhook(webhook_id)
    if success:
        return {"status": "unregistered", "webhook_id": webhook_id}
    else:
        raise HTTPException(status_code=404, detail="Webhook not found")


@app.get("/webhooks")
async def list_webhooks():
    """List all registered webhooks"""
    return {
        "webhooks": [
            {
                "id": w["id"],
                "url": w["url"],
                "events": w["events"],
                "active": w["active"],
                "created_at": w["created_at"]
            }
            for w in webhook_manager.webhooks
        ]
    }


@app.post("/professional-audit")
async def professional_audit(request: ProfessionalAuditRequest):
    """
    Professional security audit endpoint
    Provides comprehensive analysis suitable for professional security audits
    Includes SWC compliance, code metrics, and detailed remediation guidance
    
    Formats: json (default), html, pdf
    """
    if not PROFESSIONAL_AUDIT_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Professional audit features not available. Check dependencies."
        )
    
    start_time = time.time()
    
    try:
        # Input validation
        is_valid, error_msg = validate_contract_code(request.contract_code)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg)
        
        # Sanitize input
        sanitized_code = sanitize_contract_code(request.contract_code)
        
        # Perform professional audit
        professional_auditor = ProfessionalAuditor()
        audit_result = professional_auditor.audit(sanitized_code, request.contract_name)
        
        # Generate report based on format
        if request.report_format == "pdf":
            if not PDF_AVAILABLE:
                raise HTTPException(
                    status_code=503,
                    detail="PDF reports not available. Install reportlab: pip install reportlab"
                )
            
            pdf_bytes = generate_professional_audit_report_pdf(audit_result)
            return Response(
                content=pdf_bytes,
                media_type="application/pdf",
                headers={
                    "Content-Disposition": f'attachment; filename="{request.contract_name}_professional_audit.pdf"'
                }
            )
        elif request.report_format == "html":
            html_content = generate_professional_audit_report_html(audit_result)
            return HTMLResponse(content=html_content)
        else:  # json (default)
            return JSONResponse(content=audit_result.to_dict())
            
    except HTTPException:
        raise
    except Exception as e:
        app_logger.error(f"Professional audit failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Professional audit failed: {str(e)}")


@app.get("/swc-registry")
async def get_swc_registry():
    """Get SWC (Smart Contract Weakness Classification) registry"""
    from swc_registry import SWC_REGISTRY, get_all_swc_ids
    return {
        "swc_registry": SWC_REGISTRY,
        "supported_swc_ids": get_all_swc_ids(),
        "total_swc_issues_detected": len(SWC_REGISTRY)
    }


@app.get("/", response_class=HTMLResponse)
async def root():
    """Homepage - Serve explanatory HTML page"""
    try:
        # Try to serve the static homepage
        index_path = Path(__file__).parent / "static" / "index.html"
        if index_path.exists():
            html_content = index_path.read_text(encoding='utf-8')
            return HTMLResponse(content=html_content)
    except Exception as e:
        app_logger.warning(f"Could not serve static homepage: {e}")
    
    # Fallback to JSON response
    return JSONResponse({
        "name": "Solidity Vuln Scanner API",
        "version": "1.0.0",
        "message": "Welcome! Visit /docs for API documentation or http://localhost:8501 for the Web UI",
        "api_versions": ["v1"],
        "endpoints": {
            "homepage": "/",
            "docs": "/docs",
            "web_ui": "http://localhost:8501",
            "health": "/health",
            "analyze": "POST /analyze",
            "analyze-sarif": "POST /analyze-sarif",
            "analyze-pdf": "POST /analyze-pdf",
            "batch": "POST /analyze-batch",
            "upload": "POST /upload-and-analyze",
            "vulnerabilities": "GET /vulnerabilities",
            "webhooks": "POST /webhooks/register",
            "v1": "/v1/* (versioned API)"
        },
        "docs": "Visit /docs for interactive API documentation"
    })


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
