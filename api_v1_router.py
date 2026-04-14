"""White-label API v1 router for Solidity Vulnerability Scanner.

Mount this router in the existing FastAPI app to expose versioned
endpoints suitable for audit-firm white-label integration.
"""

from __future__ import annotations

import hashlib
import time
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from auth import require_api_key_user
from database import create_audit_log, store_analysis_result

router = APIRouter(prefix="/api/v1", tags=["v1"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class ScanRequest(BaseModel):
    source_code: str = Field(..., min_length=1, max_length=500_000)
    report_format: str = Field(default="json", pattern="^(json|sarif|html|markdown)$")
    branding: dict[str, str] | None = None


class Finding(BaseModel):
    id: str
    title: str
    severity: str
    swc_id: str | None = None
    cwe_id: str | None = None
    description: str
    location: dict[str, Any] | None = None
    recommendation: str | None = None


class ScanResponse(BaseModel):
    scan_id: str
    status: str
    source_hash: str
    duration_ms: float
    risk_score: float | None = None
    findings: list[Finding] = []
    report: str | None = None
    branding: dict[str, str] | None = None


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "1.0.0"


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse()


@router.post("/scan", response_model=ScanResponse)
async def scan(
    request: Request,
    body: ScanRequest,
    current_user: dict = Depends(require_api_key_user),
) -> ScanResponse:
    start = time.monotonic()
    source_hash = hashlib.sha256(body.source_code.encode()).hexdigest()
    scan_id = f"scan_{source_hash[:12]}_{int(time.time())}"

    try:
        from static_analyzer import StaticAnalyzer
        analyzer = StaticAnalyzer()
        result = analyzer.analyze(body.source_code)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {exc}") from exc

    findings: list[Finding] = []
    for vuln in getattr(result, "vulnerabilities", []):
        findings.append(Finding(
            id=getattr(vuln, "id", f"V-{len(findings)+1}"),
            title=getattr(vuln, "title", "Unknown"),
            severity=getattr(vuln, "severity", "MEDIUM"),
            swc_id=getattr(vuln, "swc_id", None),
            cwe_id=getattr(vuln, "cwe_id", None),
            description=getattr(vuln, "description", ""),
            location=getattr(vuln, "location", None),
            recommendation=getattr(vuln, "recommendation", None),
        ))

    report_content: str | None = None
    if body.report_format != "json":
        try:
            from report_generator import generate_html_report, generate_markdown_report, generate_sarif_report
            if body.report_format == "html":
                report_content = generate_html_report(result)
            elif body.report_format == "markdown":
                report_content = generate_markdown_report(result)
            elif body.report_format == "sarif":
                report_content = generate_sarif_report(result, body.source_code)
        except ImportError:
            pass

    duration_ms = (time.monotonic() - start) * 1000
    result_payload = {
        "scan_id": scan_id,
        "status": "completed",
        "source_hash": source_hash,
        "risk_score": getattr(result, "risk_score", None),
        "findings": [finding.model_dump() for finding in findings],
        "analysis_time_ms": round(duration_ms, 2),
        "severity": "UNKNOWN" if not findings else findings[0].severity,
        "lines_of_code": body.source_code.count("\n") + 1,
        "branding": body.branding,
    }

    analysis_id = store_analysis_result(
        current_user.get("user_id"),
        contract_name=scan_id,
        contract_code_hash=source_hash,
        result=result_payload,
    )
    create_audit_log(
        action="analysis.scan.completed",
        user_id=current_user.get("user_id"),
        resource_type="analysis",
        resource_id=analysis_id,
        ip_address=getattr(request.client, "host", None),
        user_agent=request.headers.get("user-agent"),
        details={
            "scan_id": scan_id,
            "source_hash": source_hash,
            "finding_count": len(findings),
            "auth_type": current_user.get("auth_type"),
        },
    )

    return ScanResponse(
        scan_id=scan_id,
        status="completed",
        source_hash=source_hash,
        duration_ms=round(duration_ms, 2),
        risk_score=getattr(result, "risk_score", None),
        findings=findings,
        report=report_content,
        branding=body.branding,
    )
