"""
SWC (Smart Contract Weakness Classification) Registry
Maps vulnerabilities to SWC IDs for professional audit compliance
Based on SWC Registry: https://swcregistry.io/
Enhanced with recent vulnerabilities
"""

# SWC Registry - Smart Contract Weakness Classification
SWC_REGISTRY = {
    "reentrancy": {
        "swc_id": "SWC-107",
        "swc_title": "Reentrancy",
        "severity": "CRITICAL",
        "description": "External call to user-supplied address before state changes",
        "impact": "Allows attacker to reenter contract and drain funds",
        "cwe": "CWE-841",
        "owasp": "A03:2021 – Injection"
    },
    "unchecked_call": {
        "swc_id": "SWC-104",
        "swc_title": "Unchecked Call Return Value",
        "severity": "HIGH",
        "description": "The return value of a low-level call is not checked",
        "impact": "Silent failures, unexpected behavior",
        "cwe": "CWE-252",
        "owasp": "A01:2021 – Broken Access Control"
    },
    "overflow_underflow": {
        "swc_id": "SWC-101",
        "swc_title": "Integer Overflow and Underflow",
        "severity": "HIGH",
        "description": "Integer arithmetic without overflow protection",
        "impact": "Unexpected value wraps, potential fund loss",
        "cwe": "CWE-190",
        "owasp": "A03:2021 – Injection"
    },
    "access_control": {
        "swc_id": "SWC-105",
        "swc_title": "Unprotected Ether Withdrawal",
        "severity": "HIGH",
        "description": "Sensitive functions without access control",
        "impact": "Unauthorized fund withdrawals or state changes",
        "cwe": "CWE-284",
        "owasp": "A01:2021 – Broken Access Control"
    },
    "bad_randomness": {
        "swc_id": "SWC-120",
        "swc_title": "Weak Sources of Randomness from Chain Attributes",
        "severity": "MEDIUM",
        "description": "Using block attributes for randomness",
        "impact": "Predictable outcomes, exploitable randomness",
        "cwe": "CWE-330",
        "owasp": "A02:2021 – Cryptographic Failures"
    },
    "tx_origin": {
        "swc_id": "SWC-115",
        "swc_title": "Authorization through tx.origin",
        "severity": "HIGH",
        "description": "Using tx.origin for authorization",
        "impact": "Phishing attacks, authorization bypass",
        "cwe": "CWE-345",
        "owasp": "A01:2021 – Broken Access Control"
    },
    "delegatecall": {
        "swc_id": "SWC-112",
        "swc_title": "Delegatecall to Untrusted Callee",
        "severity": "HIGH",
        "description": "Delegatecall to user-controlled address",
        "impact": "Arbitrary code execution, complete control",
        "cwe": "CWE-829",
        "owasp": "A03:2021 – Injection"
    },
    "gas_dos": {
        "swc_id": "SWC-128",
        "swc_title": "DoS With Block Gas Limit",
        "severity": "MEDIUM",
        "description": "Loops over unbounded arrays",
        "impact": "Contract unusable, transaction failures",
        "cwe": "CWE-400",
        "owasp": "A04:2021 – Insecure Design"
    },
    "timestamp": {
        "swc_id": "SWC-116",
        "swc_title": "Timestamp Dependence",
        "severity": "LOW",
        "description": "Critical logic depends on block.timestamp",
        "impact": "Miners can manipulate timing slightly",
        "cwe": "CWE-367",
        "owasp": "A04:2021 – Insecure Design"
    },
    "selfdestruct": {
        "swc_id": "SWC-106",
        "swc_title": "Unprotected SELFDESTRUCT Instruction",
        "severity": "MEDIUM",
        "description": "Contract can be destroyed without proper checks",
        "impact": "Funds frozen, contract destroyed",
        "cwe": "CWE-284",
        "owasp": "A01:2021 – Broken Access Control"
    },
    "no_events": {
        "swc_id": "SWC-118",
        "swc_title": "Incorrect Constructor Name",
        "severity": "LOW",
        "description": "Missing event emissions for state changes",
        "impact": "Reduced observability, off-chain monitoring issues",
        "cwe": "CWE-312",
        "owasp": "A09:2021 – Security Logging and Monitoring Failures"
    },
    "missing_input_validation": {
        "swc_id": "SWC-123",
        "swc_title": "Requirement Violation",
        "severity": "HIGH",
        "description": "Missing input validation",
        "impact": "Invalid inputs accepted, unexpected behavior",
        "cwe": "CWE-20",
        "owasp": "A03:2021 – Injection"
    },
    "front_running": {
        "swc_id": "SWC-114",
        "swc_title": "Transaction Order Dependence",
        "severity": "MEDIUM",
        "description": "Front-running vulnerability",
        "impact": "Attackers can front-run transactions",
        "cwe": "CWE-362",
        "owasp": "A04:2021 – Insecure Design"
    },
    "logic_error": {
        "swc_id": "SWC-110",
        "swc_title": "Assert Violation",
        "severity": "MEDIUM",
        "description": "Logic errors in contract",
        "impact": "Unexpected contract behavior",
        "cwe": "CWE-691",
        "owasp": "A04:2021 – Insecure Design"
    },
    "centralization": {
        "swc_id": "SWC-105",
        "swc_title": "Unprotected Ether Withdrawal",
        "severity": "MEDIUM",
        "description": "Centralization risks, single point of failure",
        "impact": "Single entity can control contract",
        "cwe": "CWE-284",
        "owasp": "A04:2021 – Insecure Design"
    }
}

# DASP TOP 10 mapping
DASP_TOP10 = {
    "reentrancy": {"dasp": "DASP-3", "title": "Reentrancy"},
    "access_control": {"dasp": "DASP-6", "title": "Access Control"},
    "overflow_underflow": {"dasp": "DASP-5", "title": "Arithmetic Issues"},
    "bad_randomness": {"dasp": "DASP-9", "title": "Bad Randomness"},
    "tx_origin": {"dasp": "DASP-6", "title": "Access Control"},
    "delegatecall": {"dasp": "DASP-6", "title": "Access Control"},
    "gas_dos": {"dasp": "DASP-8", "title": "DoS"},
    "timestamp": {"dasp": "DASP-9", "title": "Bad Randomness"},
    "front_running": {"dasp": "DASP-7", "title": "Front Running"},
    "logic_error": {"dasp": "DASP-10", "title": "Unknown Unknowns"},
}


def get_swc_info(vuln_type: str) -> dict:
    """Get SWC classification information for a vulnerability type"""
    return SWC_REGISTRY.get(vuln_type, {
        "swc_id": "N/A",
        "swc_title": "Unknown Vulnerability",
        "severity": "UNKNOWN",
        "description": "Vulnerability not in SWC registry",
        "impact": "Unknown",
        "cwe": "N/A",
        "owasp": "N/A"
    })


def get_dasp_info(vuln_type: str) -> dict:
    """Get DASP TOP 10 classification"""
    return DASP_TOP10.get(vuln_type, {
        "dasp": "N/A",
        "title": "Not in DASP TOP 10"
    })


def get_all_swc_ids() -> list:
    """Get all SWC IDs that are detected"""
    return [info["swc_id"] for info in SWC_REGISTRY.values()]


def get_compliance_report(vulnerabilities: list) -> dict:
    """
    Generate compliance report for professional audits
    Maps vulnerabilities to SWC, CWE, OWASP classifications
    """
    swc_findings = {}
    cwe_findings = {}
    owasp_findings = {}
    
    for vuln in vulnerabilities:
        swc_info = get_swc_info(vuln.vuln_type)
        dasp_info = get_dasp_info(vuln.vuln_type)
        
        # Group by SWC ID
        swc_id = swc_info["swc_id"]
        if swc_id not in swc_findings:
            swc_findings[swc_id] = {
                "swc_id": swc_id,
                "swc_title": swc_info["swc_title"],
                "count": 0,
                "severity": swc_info["severity"],
                "vulnerabilities": []
            }
        
        swc_findings[swc_id]["count"] += 1
        swc_findings[swc_id]["vulnerabilities"].append({
            "line": vuln.line_number,
            "description": vuln.description,
            "confidence": vuln.confidence
        })
        
        # Group by CWE
        cwe_id = swc_info.get("cwe", "N/A")
        if cwe_id not in cwe_findings:
            cwe_findings[cwe_id] = {"count": 0, "vulnerabilities": []}
        cwe_findings[cwe_id]["count"] += 1
        
        # Group by OWASP
        owasp_id = swc_info.get("owasp", "N/A")
        if owasp_id not in owasp_findings:
            owasp_findings[owasp_id] = {"count": 0, "vulnerabilities": []}
        owasp_findings[owasp_id]["count"] += 1
    
    return {
        "swc_findings": list(swc_findings.values()),
        "cwe_findings": cwe_findings,
        "owasp_findings": owasp_findings,
        "total_swc_issues": len(swc_findings),
        "compliance_level": "COMPLIANT" if len(swc_findings) == 0 else "NON_COMPLIANT"
    }
