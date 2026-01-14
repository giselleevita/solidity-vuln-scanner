"""
Professional Audit Framework
Enhanced analysis for professional security audits
Includes compliance checking, risk assessment, and professional reporting
"""

from typing import List, Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime, timezone
from static_analyzer import StaticAnalyzer, AnalysisResult, Vulnerability
from swc_registry import get_swc_info, get_dasp_info, get_compliance_report
from logger_config import get_logger

logger = get_logger(__name__)


@dataclass
class ProfessionalAuditResult:
    """Professional audit result with compliance and risk assessment"""
    contract_name: str
    analysis_date: str
    audit_version: str = "2.0.0"
    
    # Analysis results
    static_analysis: AnalysisResult = None
    vulnerabilities: List[Vulnerability] = field(default_factory=list)
    
    # Professional metrics
    risk_score: float = 0.0
    overall_severity: str = "SAFE"
    confidence_level: str = "HIGH"  # HIGH, MEDIUM, LOW
    
    # Compliance
    swc_compliance: Dict = field(default_factory=dict)
    compliance_status: str = "COMPLIANT"
    
    # Code metrics
    lines_of_code: int = 0
    cyclomatic_complexity: float = 0.0
    function_count: int = 0
    public_function_count: int = 0
    
    # Vulnerability summary
    vulnerability_summary: Dict = field(default_factory=dict)
    severity_distribution: Dict = field(default_factory=dict)
    
    # Recommendations
    critical_findings: List[str] = field(default_factory=list)
    high_priority_recommendations: List[str] = field(default_factory=list)
    audit_notes: List[str] = field(default_factory=list)
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            "audit_metadata": {
                "contract_name": self.contract_name,
                "analysis_date": self.analysis_date,
                "audit_version": self.audit_version,
                "confidence_level": self.confidence_level
            },
            "risk_assessment": {
                "risk_score": self.risk_score,
                "overall_severity": self.overall_severity,
                "severity_distribution": self.severity_distribution
            },
            "compliance": {
                "status": self.compliance_status,
                "swc_findings": self.swc_compliance.get("swc_findings", []),
                "cwe_findings": self.swc_compliance.get("cwe_findings", {}),
                "owasp_findings": self.swc_compliance.get("owasp_findings", {})
            },
            "code_metrics": {
                "lines_of_code": self.lines_of_code,
                "cyclomatic_complexity": self.cyclomatic_complexity,
                "function_count": self.function_count,
                "public_function_count": self.public_function_count
            },
            "vulnerabilities": [
                self._enhance_vuln_dict(v) for v in self.vulnerabilities
            ],
            "recommendations": {
                "critical_findings": self.critical_findings,
                "high_priority": self.high_priority_recommendations,
                "audit_notes": self.audit_notes
            }
        }
    
    def _enhance_vuln_dict(self, vuln: Vulnerability) -> Dict:
        """Enhance vulnerability dict with SWC/CWE/OWASP info"""
        base_dict = vuln.to_dict()
        swc_info = get_swc_info(vuln.vuln_type)
        dasp_info = get_dasp_info(vuln.vuln_type)
        
        base_dict.update({
            "swc_id": swc_info["swc_id"],
            "swc_title": swc_info["swc_title"],
            "cwe": swc_info.get("cwe", "N/A"),
            "owasp": swc_info.get("owasp", "N/A"),
            "dasp": dasp_info.get("dasp", "N/A"),
            "impact": swc_info.get("impact", "Unknown"),
            "remediation_detailed": self._get_detailed_remediation(vuln, swc_info)
        })
        return base_dict
    
    def _get_detailed_remediation(self, vuln: Vulnerability, swc_info: Dict) -> Dict:
        """Get detailed remediation guidance with examples"""
        remediation_type = vuln.vuln_type
        
        remediations = {
            "reentrancy": {
                "pattern": "Checks-Effects-Interactions",
                "example": """
// VULNERABLE:
balances[msg.sender] -= amount;
payable(msg.sender).transfer(amount);

// SECURE:
require(balances[msg.sender] >= amount);
balances[msg.sender] -= amount;  // Effects first
payable(msg.sender).transfer(amount);  // Interactions last
// Or use ReentrancyGuard from OpenZeppelin
                """.strip(),
                "libraries": ["OpenZeppelin ReentrancyGuard"],
                "references": ["SWC-107", "https://swcregistry.io/docs/SWC-107"]
            },
            "unchecked_call": {
                "pattern": "Always check return values",
                "example": """
// VULNERABLE:
someAddress.call{value: amount}("");

// SECURE:
(bool success, ) = someAddress.call{value: amount}("");
require(success, "Transfer failed");
// Or use SafeTransfer libraries
                """.strip(),
                "libraries": ["OpenZeppelin SafeTransfer"],
                "references": ["SWC-104", "https://swcregistry.io/docs/SWC-104"]
            },
            "access_control": {
                "pattern": "Use access control modifiers",
                "example": """
// VULNERABLE:
function withdraw() public { ... }

// SECURE:
modifier onlyOwner() {
    require(msg.sender == owner, "Not owner");
    _;
}

function withdraw() public onlyOwner { ... }
// Or use OpenZeppelin Ownable/Roles
                """.strip(),
                "libraries": ["OpenZeppelin Ownable", "OpenZeppelin AccessControl"],
                "references": ["SWC-105", "https://swcregistry.io/docs/SWC-105"]
            }
        }
        
        return remediations.get(remediation_type, {
            "pattern": vuln.remediation,
            "example": "See remediation field",
            "libraries": [],
            "references": [swc_info.get("swc_id", "N/A")]
        })


class ProfessionalAuditor:
    """
    Professional security auditor with enhanced analysis
    Suitable for professional security audits
    """
    
    def __init__(self):
        self.static_analyzer = StaticAnalyzer()
        logger.info("Professional auditor initialized")
    
    def audit(self, contract_code: str, contract_name: str = "Contract") -> ProfessionalAuditResult:
        """
        Perform professional security audit
        
        Args:
            contract_code: Solidity source code
            contract_name: Contract name
            
        Returns:
            ProfessionalAuditResult with comprehensive audit information
        """
        # Perform static analysis
        static_result = self.static_analyzer.analyze(contract_code, contract_name)
        
        # Create professional audit result
        audit_result = ProfessionalAuditResult(
            contract_name=contract_name,
            analysis_date=datetime.now(timezone.utc).isoformat(),
            static_analysis=static_result,
            vulnerabilities=static_result.vulnerabilities,
            risk_score=static_result.risk_score,
            overall_severity=static_result._get_overall_severity(),
            lines_of_code=static_result.lines_of_code
        )
        
        # Calculate code metrics
        code_metrics = self._calculate_code_metrics(contract_code)
        audit_result.cyclomatic_complexity = code_metrics["complexity"]
        audit_result.function_count = code_metrics["function_count"]
        audit_result.public_function_count = code_metrics["public_function_count"]
        
        # Generate compliance report
        audit_result.swc_compliance = get_compliance_report(static_result.vulnerabilities)
        audit_result.compliance_status = audit_result.swc_compliance.get("compliance_level", "COMPLIANT")
        
        # Vulnerability summary
        audit_result.vulnerability_summary = {
            "total": len(static_result.vulnerabilities),
            "by_severity": static_result.severity_distribution(),
            "swc_issues": audit_result.swc_compliance.get("total_swc_issues", 0)
        }
        audit_result.severity_distribution = static_result.severity_distribution()
        
        # Calculate confidence level
        audit_result.confidence_level = self._calculate_confidence_level(
            audit_result,
            code_metrics
        )
        
        # Generate recommendations
        audit_result.critical_findings = self._generate_critical_findings(audit_result)
        audit_result.high_priority_recommendations = self._generate_recommendations(audit_result)
        audit_result.audit_notes = self._generate_audit_notes(audit_result)
        
        logger.info(f"Professional audit complete: {contract_name} - {audit_result.overall_severity} ({audit_result.risk_score:.1f})")
        
        return audit_result
    
    def _calculate_code_metrics(self, contract_code: str) -> Dict:
        """Calculate code complexity metrics"""
        import re
        
        lines = contract_code.split('\n')
        
        # Count functions
        function_pattern = r'function\s+\w+\s*\('
        functions = re.findall(function_pattern, contract_code, re.IGNORECASE)
        function_count = len(functions)
        
        # Count public/external functions
        public_pattern = r'(?:public|external)\s+function'
        public_functions = re.findall(public_pattern, contract_code, re.IGNORECASE)
        public_function_count = len(public_functions)
        
        # Simple cyclomatic complexity estimate
        # Count control flow statements
        complexity_keywords = ['if', 'else', 'for', 'while', 'case', 'catch', '&&', '||', '?']
        complexity = 1  # Base complexity
        for keyword in complexity_keywords:
            complexity += len(re.findall(rf'\b{keyword}\b', contract_code, re.IGNORECASE))
        
        # Normalize by function count
        if function_count > 0:
            complexity = complexity / function_count
        
        return {
            "function_count": function_count,
            "public_function_count": public_function_count,
            "complexity": round(complexity, 2)
        }
    
    def _calculate_confidence_level(self, audit_result: ProfessionalAuditResult, metrics: Dict) -> str:
        """Calculate overall confidence level for audit"""
        factors = []
        
        # Code size factor
        if audit_result.lines_of_code < 100:
            factors.append(0.8)  # Smaller code = higher confidence
        elif audit_result.lines_of_code < 500:
            factors.append(0.9)
        else:
            factors.append(0.85)
        
        # Complexity factor
        if metrics["complexity"] < 5:
            factors.append(0.9)
        elif metrics["complexity"] < 10:
            factors.append(0.85)
        else:
            factors.append(0.75)
        
        # Vulnerability count factor (fewer findings = higher confidence in completeness)
        if len(audit_result.vulnerabilities) == 0:
            factors.append(0.9)  # Clean code, high confidence it's safe
        elif len(audit_result.vulnerabilities) < 5:
            factors.append(0.85)
        else:
            factors.append(0.8)  # Many findings, might be more
        
        avg_confidence = sum(factors) / len(factors)
        
        if avg_confidence >= 0.85:
            return "HIGH"
        elif avg_confidence >= 0.75:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _generate_critical_findings(self, audit_result: ProfessionalAuditResult) -> List[str]:
        """Generate critical findings summary"""
        findings = []
        
        critical_vulns = [v for v in audit_result.vulnerabilities if v.severity == "CRITICAL"]
        if critical_vulns:
            findings.append(f"Found {len(critical_vulns)} CRITICAL vulnerability(ies) that require immediate attention")
        
        high_vulns = [v for v in audit_result.vulnerabilities if v.severity == "HIGH"]
        if high_vulns:
            findings.append(f"Found {len(high_vulns)} HIGH severity vulnerability(ies)")
        
        # Check for specific critical patterns
        vuln_types = {v.vuln_type for v in audit_result.vulnerabilities}
        
        if "reentrancy" in vuln_types:
            findings.append("CRITICAL: Reentrancy vulnerability detected. Contract is unsafe for production.")
        
        if "delegatecall" in vuln_types:
            findings.append("CRITICAL: Unsafe delegatecall detected. Contract may be vulnerable to complete takeover.")
        
        if audit_result.compliance_status == "NON_COMPLIANT":
            findings.append(f"Contract is NON-COMPLIANT with SWC standards ({audit_result.swc_compliance.get('total_swc_issues', 0)} SWC issues)")
        
        return findings
    
    def _generate_recommendations(self, audit_result: ProfessionalAuditResult) -> List[str]:
        """Generate high-priority recommendations"""
        recommendations = []
        
        # SWC compliance recommendations
        if audit_result.swc_compliance.get("total_swc_issues", 0) > 0:
            recommendations.append("Address all SWC-classified vulnerabilities before production deployment")
        
        # Code complexity recommendations
        if audit_result.cyclomatic_complexity > 10:
            recommendations.append("Reduce cyclomatic complexity. Consider breaking complex functions into smaller units.")
        
        # Public function recommendations
        if audit_result.public_function_count > audit_result.function_count * 0.7:
            recommendations.append("High ratio of public functions. Review if all need to be public/external.")
        
        # Access control recommendations
        access_control_issues = [v for v in audit_result.vulnerabilities if v.vuln_type == "access_control"]
        if access_control_issues:
            recommendations.append("Implement proper access control using modifiers (onlyOwner, role-based, etc.)")
        
        # Input validation recommendations
        validation_issues = [v for v in audit_result.vulnerabilities if v.vuln_type == "missing_input_validation"]
        if validation_issues:
            recommendations.append("Add input validation (require statements) to all public/external functions")
        
        # Testing recommendations
        if audit_result.risk_score > 50:
            recommendations.append("High risk score. Conduct comprehensive testing including fuzzing and property-based tests.")
        
        # Professional audit recommendation
        if audit_result.overall_severity in ["CRITICAL", "HIGH"]:
            recommendations.append("CRITICAL/HIGH severity findings detected. Engage professional security auditors before mainnet deployment.")
        
        return recommendations
    
    def _generate_audit_notes(self, audit_result: ProfessionalAuditResult) -> List[str]:
        """Generate professional audit notes"""
        notes = []
        
        notes.append(f"Audit conducted using automated analysis tools. Manual review recommended for production contracts.")
        notes.append(f"Confidence level: {audit_result.confidence_level}")
        
        if audit_result.lines_of_code > 1000:
            notes.append("Large codebase detected. Consider modular analysis and formal verification for complex contracts.")
        
        if audit_result.compliance_status == "COMPLIANT":
            notes.append("Contract passes automated SWC compliance checks. Manual review still recommended.")
        else:
            notes.append("Contract does not pass automated SWC compliance. All findings should be addressed.")
        
        # Vulnerability-specific notes
        vuln_types = {v.vuln_type for v in audit_result.vulnerabilities}
        if "reentrancy" in vuln_types:
            notes.append("Reentrancy protection (ReentrancyGuard or Checks-Effects-Interactions pattern) is critical.")
        
        if audit_result.function_count == 0:
            notes.append("No functions detected. Verify contract code is complete and valid.")
        
        return notes
