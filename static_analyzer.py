"""
Static Analyzer for Solidity Smart Contracts
Detects common vulnerabilities using regex patterns and AST-like analysis
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional
from app_config import VULN_TYPES, SEVERITY_LEVELS


@dataclass
class Vulnerability:
    """Represents a detected vulnerability"""
    vuln_type: str
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW, INFO
    line_number: int
    description: str
    code_snippet: str
    remediation: str
    
    def to_dict(self):
        return {
            "type": self.vuln_type,
            "severity": self.severity,
            "line": self.line_number,
            "description": self.description,
            "code_snippet": self.code_snippet,
            "remediation": self.remediation
        }


@dataclass
class AnalysisResult:
    """Result of contract analysis"""
    contract_name: str
    vulnerabilities: List[Vulnerability] = field(default_factory=list)
    risk_score: float = 0.0  # 0-100
    lines_of_code: int = 0
    analysis_time_ms: int = 0
    
    def severity_distribution(self) -> dict:
        """Return count of vulnerabilities by severity"""
        dist = {severity: 0 for severity in SEVERITY_LEVELS.keys()}
        for vuln in self.vulnerabilities:
            dist[vuln.severity] += 1
        return dist
    
    def to_dict(self):
        return {
            "contract_name": self.contract_name,
            "risk_score": self.risk_score,
            "severity": self._get_overall_severity(),
            "vulnerabilities": [v.to_dict() for v in self.vulnerabilities],
            "severity_distribution": self.severity_distribution(),
            "lines_of_code": self.lines_of_code,
            "analysis_time_ms": self.analysis_time_ms
        }
    
    def _get_overall_severity(self) -> str:
        """Determine overall risk level"""
        if any(v.severity == "CRITICAL" for v in self.vulnerabilities):
            return "CRITICAL"
        elif any(v.severity == "HIGH" for v in self.vulnerabilities):
            return "HIGH"
        elif any(v.severity == "MEDIUM" for v in self.vulnerabilities):
            return "MEDIUM"
        elif any(v.severity == "LOW" for v in self.vulnerabilities):
            return "LOW"
        return "SAFE"


class StaticAnalyzer:
    """
    Pattern-based vulnerability detector for Solidity contracts
    Uses regex and text analysis to find common security issues
    """
    
    def __init__(self):
        self.patterns = self._init_patterns()
    
    def _init_patterns(self) -> dict:
        """Initialize vulnerability detection patterns"""
        return {
            "reentrancy": {
                "pattern": r"(?:call|send|transfer)\s*\(\s*\).*?(?:balances|amount|_balance)\s*[-\[].*?\]?\s*[=-]",
                "severity": "CRITICAL",
                "description": "Potential reentrancy vulnerability: external call before state update",
                "remediation": "Use Checks-Effects-Interactions pattern. Update state BEFORE external calls."
            },
            "unchecked_call": {
                "pattern": r"(?:call|send|delegatecall)\s*\(\s*\)[^;]*?(?!require|assert)",
                "severity": "HIGH",
                "description": "Unchecked external call result. May fail silently.",
                "remediation": "Always check return value of low-level calls or use safe wrappers (e.g., SafeTransfer)."
            },
            "overflow_underflow": {
                "pattern": r"(?:\+|-|\*|/)\s*(?:amount|value|balance|count)(?!.*?SafeMath)(?!.*?checked)",
                "severity": "HIGH",
                "description": "Potential integer overflow/underflow without SafeMath",
                "remediation": "Use SafeMath library or Solidity 0.8+ checked arithmetic."
            },
            "access_control": {
                "pattern": r"(?:public|external)\s+function\s+(?:transfer|mint|burn|withdraw|execute|setAdmin)",
                "severity": "HIGH",
                "description": "Sensitive function without access control modifiers",
                "remediation": "Add onlyOwner, onlyAdmin, or other access control checks."
            },
            "bad_randomness": {
                "pattern": r"(?:blockhash|block\.number|block\.timestamp|now).*?random",
                "severity": "MEDIUM",
                "description": "Using blockchain properties for randomness. Predictable and exploitable.",
                "remediation": "Use Chainlink VRF or other secure randomness oracle."
            },
            "tx_origin": {
                "pattern": r"tx\.origin\s*(?:==|!=|require)",
                "severity": "HIGH",
                "description": "Using tx.origin for authorization. Vulnerable to phishing attacks.",
                "remediation": "Use msg.sender instead of tx.origin for access control."
            },
            "delegatecall": {
                "pattern": r"delegatecall\s*\(\s*(?!abi\.encodeWithSelector)[^;]*\);",
                "severity": "HIGH",
                "description": "Unsafe delegatecall to dynamically determined address",
                "remediation": "Ensure delegatecall target is trusted and validated."
            },
            "gas_dos": {
                "pattern": r"for\s*\(\s*\w+\s*(?:in|=|:).*?(?:balances|holders|users|amount).*?\)",
                "severity": "MEDIUM",
                "description": "Loop over unbounded array may cause gas limit exception",
                "remediation": "Implement pagination or batch processing patterns."
            },
            "timestamp": {
                "pattern": r"(?:require|if|assert)\s*\(\s*block\.timestamp.*?(?:<|>|==|!=)",
                "severity": "LOW",
                "description": "Relying on block.timestamp for critical logic. Miners can manipulate slightly.",
                "remediation": "Use timestamps only for non-critical timing. Not suitable for tight time windows."
            },
            "selfdestruct": {
                "pattern": r"selfdestruct\s*\(\s*[^;]*\);",
                "severity": "MEDIUM",
                "description": "Contract can be destroyed, potentially freezing funds",
                "remediation": "Implement proper access controls or remove selfdestruct if not needed."
            },
            "no_events": {
                "pattern": r"(?:transfer|mint|burn|withdraw)\s*\([^)]*\)\s*(?:{|$)(?!.*emit\s+\w+)",
                "severity": "LOW",
                "description": "Critical state change without event emission",
                "remediation": "Emit events for all state changes to enable off-chain monitoring."
            }
        }
    
    def analyze(self, contract_code: str, contract_name: str = "Contract") -> AnalysisResult:
        """
        Analyze Solidity contract code for vulnerabilities
        
        Args:
            contract_code: Full Solidity source code
            contract_name: Name of the contract being analyzed
            
        Returns:
            AnalysisResult object with detected vulnerabilities
        """
        result = AnalysisResult(contract_name=contract_name)
        result.lines_of_code = len(contract_code.split('\n'))
        
        # Remove comments for cleaner analysis
        clean_code = self._remove_comments(contract_code)
        lines = clean_code.split('\n')
        
        # Check each pattern
        for vuln_key, vuln_pattern in self.patterns.items():
            matches = self._find_pattern_matches(
                clean_code,
                lines,
                vuln_pattern["pattern"],
                vuln_key,
                vuln_pattern["severity"],
                vuln_pattern["description"],
                vuln_pattern["remediation"]
            )
            result.vulnerabilities.extend(matches)
        
        # Calculate risk score
        result.risk_score = self._calculate_risk_score(result)
        
        return result
    
    def _remove_comments(self, code: str) -> str:
        """Remove single-line and multi-line comments"""
        # Remove multi-line comments
        code = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)
        # Remove single-line comments
        code = re.sub(r'//.*?$', '', code, flags=re.MULTILINE)
        return code
    
    def _find_pattern_matches(
        self,
        code: str,
        lines: List[str],
        pattern: str,
        vuln_type: str,
        severity: str,
        description: str,
        remediation: str
    ) -> List[Vulnerability]:
        """Find all matches for a vulnerability pattern"""
        vulnerabilities = []
        
        try:
            for match in re.finditer(pattern, code, re.IGNORECASE | re.DOTALL):
                # Determine line number
                line_num = code[:match.start()].count('\n') + 1
                
                # Get code snippet (context around match)
                snippet = self._get_code_snippet(lines, line_num)
                
                vuln = Vulnerability(
                    vuln_type=vuln_type,
                    severity=severity,
                    line_number=line_num,
                    description=description,
                    code_snippet=snippet,
                    remediation=remediation
                )
                vulnerabilities.append(vuln)
        except Exception as e:
            # Log pattern compilation errors silently
            pass
        
        return vulnerabilities
    
    def _get_code_snippet(self, lines: List[str], line_num: int, context: int = 2) -> str:
        """Get code snippet with context around line number"""
        start = max(0, line_num - context - 1)
        end = min(len(lines), line_num + context)
        
        snippet_lines = []
        for i in range(start, end):
            prefix = ">>> " if i == line_num - 1 else "    "
            snippet_lines.append(f"{prefix}{i+1}: {lines[i]}")
        
        return '\n'.join(snippet_lines)
    
    def _calculate_risk_score(self, result: AnalysisResult) -> float:
        """
        Calculate overall risk score (0-100)
        Based on vulnerability count, severity, and code size
        """
        if not result.vulnerabilities:
            return 0.0
        
        # Severity weights
        severity_weights = {
            "CRITICAL": 25,
            "HIGH": 15,
            "MEDIUM": 8,
            "LOW": 3,
            "INFO": 1
        }
        
        # Calculate base score
        score = 0
        for vuln in result.vulnerabilities:
            score += severity_weights.get(vuln.severity, 0)
        
        # Normalize and cap at 100
        # Add bonus for code size (larger code = more risk)
        size_factor = min(result.lines_of_code / 100, 5)  # Cap at 500 LoC
        normalized_score = min(score * (1 + size_factor * 0.1), 100)
        
        return round(normalized_score, 2)


# Example usage and testing
if __name__ == "__main__":
    # Example vulnerable contract
    example_contract = '''
    pragma solidity ^0.8.0;
    
    contract VulnerableVault {
        mapping(address => uint256) balances;
        
        function withdraw(uint256 amount) public {
            require(balances[msg.sender] >= amount);
            // Reentrancy vulnerability: external call before state update
            (bool success, ) = msg.sender.call{value: amount}("");
            require(success);
            balances[msg.sender] -= amount;
        }
        
        function transfer(address recipient, uint256 amount) public {
            // No access control
            balances[recipient] += amount;
        }
    }
    '''
    
    analyzer = StaticAnalyzer()
    result = analyzer.analyze(example_contract, "VulnerableVault")
    
    print(f"Contract: {result.contract_name}")
    print(f"Risk Score: {result.risk_score}")
    print(f"Vulnerabilities found: {len(result.vulnerabilities)}")
    for vuln in result.vulnerabilities:
        print(f"\n  - {vuln.vuln_type.upper()}: {vuln.severity}")
        print(f"    Line {vuln.line_number}: {vuln.description}")
