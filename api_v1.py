"""
API v1 - Versioned endpoints
Maintains backward compatibility while allowing future versions
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from typing import Optional
from pydantic import BaseModel
import time
from datetime import datetime, timezone

from report_generator import generate_html_report, generate_markdown_report, generate_sarif_report
from tools_integration import run_slither, run_mythril, check_slither_installed, check_mythril_installed
from static_analyzer import StaticAnalyzer, AnalysisResult
from llm_auditor import LLMAuditor
from app_config import get_config
from logger_config import get_logger
from exceptions import AnalysisException, ValidationError
from input_validator import validate_contract_code, sanitize_contract_code, validate_contract_name
# Import types only to avoid circular import
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import time
from datetime import datetime, timezone

# Import shared models to avoid duplication
from models import (
    ContractAnalysisRequest,
    ContractAnalysisResponse,
    CrossValidateRequest,
    CrossValidateResponse
)

logger = get_logger(__name__)
config = get_config()

# Create v1 router
router = APIRouter(prefix="/v1", tags=["v1"])

# Initialize components (shared with main API)
try:
    static_analyzer = StaticAnalyzer()
    logger.info("Static analyzer initialized for v1")
except Exception as e:
    logger.error(f"Failed to initialize static analyzer: {e}")
    raise

llm_auditor = None
if config.use_llm and config.llm_api_key and config.llm_api_key.strip():
    try:
        llm_auditor = LLMAuditor(
            api_key=config.llm_api_key,
            model=config.llm_model,
            provider=config.llm_provider
        )
        logger.info("LLM auditor initialized for v1")
    except Exception as e:
        logger.warning(f"LLM auditor not available: {e}")


@router.get("/health")
async def health_check_v1():
    """Health check endpoint for v1"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "api_version": "v1",
        "llm_enabled": llm_auditor is not None
    }


@router.post("/analyze", response_model=ContractAnalysisResponse)
async def analyze_contract_v1(request: ContractAnalysisRequest):
    """
    Analyze contract endpoint (v1)
    Same functionality as main API but versioned
    """
    start_time = time.time()
    
    # Import the helper function from main API
    from fastapi_api import _analyze_static_and_llm
    
    try:
        # Use the helper function directly
        result = await _analyze_static_and_llm(request, start_time)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in v1 analyze: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/analyze-sarif")
async def analyze_contract_sarif_v1(request: ContractAnalysisRequest):
    """Analyze contract and return SARIF format (v1)"""
    from fastapi.responses import JSONResponse
    from fastapi_api import _analyze_static_and_llm
    from report_generator import generate_sarif_report
    
    start_time = time.time()
    try:
        result = await _analyze_static_and_llm(request, start_time)
        sarif = generate_sarif_report(result.dict() if hasattr(result, 'dict') else result)
        return JSONResponse(content=sarif, media_type="application/sarif+json")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating SARIF in v1: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cross-validate", response_model=CrossValidateResponse)
async def cross_validate_v1(request: CrossValidateRequest):
    """Cross-validate endpoint (v1)"""
    from fastapi_api import _analyze_static_and_llm
    
    start_time = time.time()
    
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


@router.get("/tools/status")
async def get_tools_status_v1():
    """Check status of external tools (v1)"""
    slither_ok, slither_msg = check_slither_installed()
    mythril_ok, mythril_msg = check_mythril_installed()
    
    return {
        "api_version": "v1",
        "slither": {
            "installed": slither_ok,
            "message": slither_msg
        },
        "mythril": {
            "installed": mythril_ok,
            "message": mythril_msg
        }
    }


@router.get("/vulnerabilities")
async def get_vulnerability_definitions_v1():
    """Get vulnerability definitions (v1)"""
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
        "api_version": "v1",
        "vulnerabilities": vuln_descriptions,
        "total": len(vuln_descriptions)
    }
