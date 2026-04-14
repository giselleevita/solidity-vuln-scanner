"""
Shared data models for API requests and responses
Used across main API and versioned endpoints to avoid duplication
"""

from pydantic import BaseModel
from typing import Optional, List


class ContractAnalysisRequest(BaseModel):
    """Request model for contract analysis"""
    contract_code: str
    contract_name: str = "Contract"
    use_llm_audit: bool = True


class ContractAnalysisResponse(BaseModel):
    """Response model for contract analysis"""
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


class ProfessionalAuditRequest(BaseModel):
    """Request model for professional audit"""
    contract_code: str
    contract_name: str = "Contract"
    report_format: str = "json"  # json, html, pdf


class CrossValidateRequest(BaseModel):
    """Request model for cross-validation analysis"""
    contract_code: str
    contract_name: str = "Contract"
    run_slither: bool = False
    run_mythril: bool = False
    use_llm_audit: bool = True


class CrossValidateResponse(BaseModel):
    """Response model for cross-validation analysis"""
    analysis: ContractAnalysisResponse
    slither: Optional[dict] = None
    mythril: Optional[dict] = None


class HealthResponse(BaseModel):
    """Health check response model"""
    status: str
    version: str
    llm_enabled: bool


class ErrorResponse(BaseModel):
    """Standardized error response model"""
    error: str
    code: str
    details: Optional[dict] = None
    message: Optional[str] = None
