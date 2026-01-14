"""
Static Analyzer for Solidity Smart Contracts
Detects common vulnerabilities using improved pattern matching with context awareness
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Tuple, Set
from app_config import VULN_TYPES, SEVERITY_LEVELS, get_config
from logger_config import get_logger
from exceptions import PatternCompilationError, AnalysisException
from swc_registry import get_swc_info

logger = get_logger(__name__)
config = get_config()


@dataclass
class Vulnerability:
    """Represents a detected vulnerability"""
    vuln_type: str
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW, INFO
    line_number: int
    description: str
    code_snippet: str
    remediation: str
    confidence: float = 0.8  # Confidence score 0.0-1.0
    unique_id: Optional[str] = None  # For deduplication
    
    def to_dict(self):
        """Convert to dictionary with enhanced professional audit information"""
        base_dict = {
            "type": self.vuln_type,
            "severity": self.severity,
            "line": self.line_number,
            "description": self.description,
            "code_snippet": self.code_snippet,
            "remediation": self.remediation,
            "confidence": self.confidence
        }
        
        # Add SWC classification for professional audits
        try:
            swc_info = get_swc_info(self.vuln_type)
            base_dict["swc_id"] = swc_info.get("swc_id", "N/A")
            base_dict["swc_title"] = swc_info.get("swc_title", "N/A")
            base_dict["cwe"] = swc_info.get("cwe", "N/A")
            base_dict["owasp"] = swc_info.get("owasp", "N/A")
        except:
            pass  # Don't fail if SWC registry not available
        
        return base_dict
    
    def __hash__(self):
        """Hash for deduplication"""
        if self.unique_id:
            return hash(self.unique_id)
        return hash((self.vuln_type, self.line_number, self.description))
    
    def __eq__(self, other):
        """Equality for deduplication"""
        if not isinstance(other, Vulnerability):
            return False
        if self.unique_id and other.unique_id:
            return self.unique_id == other.unique_id
        return (self.vuln_type == other.vuln_type and 
                self.line_number == other.line_number and
                self.description == other.description)


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
    Improved vulnerability detector for Solidity contracts
    Uses compiled regex patterns with context awareness and deduplication
    """
    
    def __init__(self):
        """Initialize analyzer with compiled patterns"""
        self.pattern_configs = self._init_patterns()
        self.compiled_patterns: Dict[str, re.Pattern] = {}
        self._compile_patterns()
        logger.info(f"Static analyzer initialized with {len(self.compiled_patterns)} patterns")
    
    def _compile_patterns(self):
        """Compile all regex patterns once for performance"""
        for vuln_key, config in self.pattern_configs.items():
            try:
                pattern_str = config["pattern"]
                self.compiled_patterns[vuln_key] = re.compile(
                    pattern_str,
                    re.IGNORECASE | re.DOTALL | re.MULTILINE
                )
            except re.error as e:
                logger.error(f"Failed to compile pattern for {vuln_key}: {e}")
                raise PatternCompilationError(f"Pattern compilation failed for {vuln_key}: {e}")
    
    def _init_patterns(self) -> dict:
        """Initialize vulnerability detection patterns with improved accuracy"""
        return {
            "reentrancy": {
                "pattern": r"(?:\.call|\.send|\.transfer)\s*\([^)]*\)[^;]*?[;\n][^;]*?(?:balances|amount|_balance)\s*[-=]",
                "severity": "CRITICAL",
                "description": "Potential reentrancy vulnerability: external call before state update",
                "remediation": "Use Checks-Effects-Interactions pattern. Update state BEFORE external calls.",
                "confidence_base": 0.7
            },
            "unchecked_call": {
                "pattern": r"(?:\.call|\.send|\.delegatecall)\s*\([^)]*\)\s*[^;]*(?!.*require)(?!.*assert);",
                "severity": "HIGH",
                "description": "Unchecked external call result. May fail silently.",
                "remediation": "Always check return value of low-level calls or use safe wrappers (e.g., SafeTransfer).",
                "confidence_base": 0.8
            },
            "overflow_underflow": {
                "pattern": r"(?:\+|\-|\*|\/)\s*(?:amount|value|balance|count)\s*(?!.*SafeMath)(?!.*unchecked)",
                "severity": "HIGH",
                "description": "Potential integer overflow/underflow without SafeMath or unchecked block",
                "remediation": "Use SafeMath library or Solidity 0.8+ checked arithmetic. Use unchecked{} only when safe.",
                "confidence_base": 0.6
            },
            "access_control": {
                "pattern": r"(?:public|external)\s+function\s+(?:transfer|mint|burn|withdraw|execute|setAdmin|setOwner)\s*\([^)]*\)\s*(?!.*onlyOwner)(?!.*onlyAdmin)(?!.*modifier\s)",
                "severity": "HIGH",
                "description": "Sensitive function without access control modifiers",
                "remediation": "Add onlyOwner, onlyAdmin, or other access control checks.",
                "confidence_base": 0.7
            },
            "bad_randomness": {
                "pattern": r"(?:blockhash|block\.number|block\.timestamp|now)\s*.*?random",
                "severity": "MEDIUM",
                "description": "Using blockchain properties for randomness. Predictable and exploitable.",
                "remediation": "Use Chainlink VRF or other secure randomness oracle.",
                "confidence_base": 0.8
            },
            "tx_origin": {
                "pattern": r"tx\.origin\s*(?:==|!=|require|if)",
                "severity": "HIGH",
                "description": "Using tx.origin for authorization. Vulnerable to phishing attacks.",
                "remediation": "Use msg.sender instead of tx.origin for access control.",
                "confidence_base": 0.9
            },
            "delegatecall": {
                "pattern": r"\.delegatecall\s*\([^)]*\)\s*(?!.*abi\.encodeWithSelector)",
                "severity": "HIGH",
                "description": "Unsafe delegatecall to dynamically determined address",
                "remediation": "Ensure delegatecall target is trusted and validated.",
                "confidence_base": 0.7
            },
            "gas_dos": {
                "pattern": r"for\s*\([^)]*\)\s*\{[^}]*?(?:balances|holders|users|amount)\[",
                "severity": "MEDIUM",
                "description": "Loop over unbounded array may cause gas limit exception",
                "remediation": "Implement pagination or batch processing patterns.",
                "confidence_base": 0.6
            },
            "timestamp": {
                "pattern": r"(?:require|if|assert)\s*\(\s*block\.timestamp\s*(?:<|>|==|!=)",
                "severity": "LOW",
                "description": "Relying on block.timestamp for critical logic. Miners can manipulate slightly.",
                "remediation": "Use timestamps only for non-critical timing. Not suitable for tight time windows.",
                "confidence_base": 0.8
            },
            "selfdestruct": {
                "pattern": r"selfdestruct\s*\([^)]*\);",
                "severity": "MEDIUM",
                "description": "Contract can be destroyed, potentially freezing funds",
                "remediation": "Implement proper access controls or remove selfdestruct if not needed.",
                "confidence_base": 0.9
            },
            "no_events": {
                "pattern": r"(?:function\s+(?:transfer|mint|burn|withdraw))\s*\([^)]*\)[^{]*\{[^}]*\}(?!.*emit)",
                "severity": "LOW",
                "description": "Critical state change without event emission",
                "remediation": "Emit events for all state changes to enable off-chain monitoring.",
                "confidence_base": 0.5
            },
            "missing_input_validation": {
                "pattern": r"function\s+\w+\s*\([^)]+\).*?(?:public|external)[^{]*\{[^}]*\}(?!.*require)(?!.*assert)(?!.*modifier\s)",
                "severity": "HIGH",
                "description": "Function without input validation checks",
                "remediation": "Add require() statements to validate function inputs.",
                "confidence_base": 0.3  # Lower confidence - many functions have validation in body
            },
            "front_running": {
                "pattern": r"(?:require|if)\s*\(\s*.*?\s*(?:<|>|==|!=)\s*.*?\s*\)\s*.*?\.call|\.transfer|\.send",
                "severity": "MEDIUM",
                "description": "Transaction order dependence (front-running vulnerability)",
                "remediation": "Use commit-reveal schemes or on-chain randomness to prevent front-running.",
                "confidence_base": 0.6
            },
            "logic_error": {
                "pattern": r"(?:require|assert)\s*\(\s*(?:false|true|0|1)\s*\)",
                "severity": "MEDIUM",
                "description": "Logic error: require/assert with constant values",
                "remediation": "Review logic - constant require/assert indicates logic flaw.",
                "confidence_base": 0.9
            },
            "centralization": {
                "pattern": r"(?:onlyOwner|onlyAdmin)\s+function\s+(?:transfer|mint|burn|pause|unpause|setAdmin|setOwner)",
                "severity": "MEDIUM",
                "description": "Centralization risk: single point of control over critical functions",
                "remediation": "Consider multi-signature, timelock, or decentralized governance mechanisms.",
                "confidence_base": 0.8
            },
            "uninitialized_storage": {
                "pattern": r"mapping|struct\s+\w+\s+[a-zA-Z_][a-zA-Z0-9_]*\s*;(?!.*=)",
                "severity": "MEDIUM",
                "description": "Uninitialized storage pointer",
                "remediation": "Initialize storage variables before use.",
                "confidence_base": 0.5
            },
            "locked_ether": {
                "pattern": r"contract\s+\w+\s*\{[^}]*\}(?!.*payable)(?!.*receive)(?!.*fallback)",
                "severity": "LOW",
                "description": "Contract can receive ether but has no way to withdraw",
                "remediation": "Add withdraw function or make contract payable with proper withdrawal mechanism.",
                "confidence_base": 0.4
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
            
        Raises:
            AnalysisException: If analysis fails
        """
        try:
            result = AnalysisResult(contract_name=contract_name)
            result.lines_of_code = len(contract_code.split('\n'))
            
            if not contract_code.strip():
                logger.warning(f"Empty contract code for {contract_name}")
                return result
            
            # Remove comments for cleaner analysis
            clean_code = self._remove_comments(contract_code)
            lines = clean_code.split('\n')
            
            # Precompute line offsets for performance
            line_offsets = self._compute_line_offsets(clean_code)
            
            # Check each pattern with timeout protection
            all_vulnerabilities = []
            for vuln_key, vuln_config in self.pattern_configs.items():
                try:
                    matches = self._find_pattern_matches(
                        clean_code,
                        lines,
                        line_offsets,
                        vuln_key,
                        vuln_config
                    )
                    all_vulnerabilities.extend(matches)
                    
                    # Safety check: limit total vulnerabilities to prevent DoS
                    if len(all_vulnerabilities) > 1000:
                        logger.warning(f"Too many vulnerabilities found ({len(all_vulnerabilities)}), stopping analysis")
                        break
                except Exception as e:
                    logger.error(f"Error checking pattern {vuln_key}: {e}", exc_info=True)
                    # Continue with other patterns
            
            # Deduplicate vulnerabilities
            result.vulnerabilities = self._deduplicate_vulnerabilities(all_vulnerabilities)
            
            # Calculate risk score
            result.risk_score = self._calculate_risk_score(result)
            
            logger.info(f"Analysis complete: {len(result.vulnerabilities)} vulnerabilities found in {contract_name}")
            return result
            
        except Exception as e:
            logger.error(f"Analysis failed for {contract_name}: {e}", exc_info=True)
            raise AnalysisException(f"Analysis failed: {str(e)}")
    
    def _compute_line_offsets(self, code: str) -> List[int]:
        """Precompute line start offsets for O(1) line number lookup"""
        offsets = [0]  # First line starts at 0
        for i, char in enumerate(code):
            if char == '\n':
                offsets.append(i + 1)
        return offsets
    
    def _get_line_number(self, position: int, line_offsets: List[int]) -> int:
        """Get line number from position using binary search (O(log n))"""
        # Binary search for the line containing this position
        left, right = 0, len(line_offsets) - 1
        while left < right:
            mid = (left + right + 1) // 2
            if line_offsets[mid] <= position:
                left = mid
            else:
                right = mid - 1
        return left + 1  # Line numbers are 1-indexed
    
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
        line_offsets: List[int],
        vuln_key: str,
        vuln_config: Dict
    ) -> List[Vulnerability]:
        """Find all matches for a vulnerability pattern with improved context awareness"""
        vulnerabilities = []
        pattern = self.compiled_patterns.get(vuln_key)
        
        if not pattern:
            logger.warning(f"Pattern not compiled for {vuln_key}")
            return vulnerabilities
        
        try:
            # Limit matches per pattern to prevent ReDoS and excessive processing
            max_matches_per_pattern = 100
            matches_found = 0
            
            for match in pattern.finditer(code):
                matches_found += 1
                
                # Safety limit to prevent DoS attacks via ReDoS
                if matches_found > max_matches_per_pattern:
                    logger.warning(f"Pattern {vuln_key} found >{max_matches_per_pattern} matches, limiting results (DoS protection)")
                    break
                
                start_pos = match.start()
                line_num = self._get_line_number(start_pos, line_offsets)
                
                # Get code snippet (context around match)
                snippet = self._get_code_snippet(lines, line_num, config.code_snippet_context_lines)
                
                # Calculate confidence based on context
                confidence = self._calculate_confidence(
                    vuln_key,
                    match,
                    code,
                    lines,
                    line_num,
                    vuln_config.get("confidence_base", 0.7)
                )
                
                # Generate unique ID for deduplication
                unique_id = f"{vuln_key}:{line_num}:{hash(match.group(0))}"
                
                vuln = Vulnerability(
                    vuln_type=vuln_key,
                    severity=vuln_config["severity"],
                    line_number=line_num,
                    description=vuln_config["description"],
                    code_snippet=snippet,
                    remediation=vuln_config["remediation"],
                    confidence=confidence,
                    unique_id=unique_id
                )
                vulnerabilities.append(vuln)
                
        except re.error as e:
            logger.error(f"Regex error for pattern {vuln_key}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error matching pattern {vuln_key}: {e}", exc_info=True)
        
        return vulnerabilities
    
    def _calculate_confidence(
        self,
        vuln_type: str,
        match: re.Match,
        code: str,
        lines: List[str],
        line_num: int,
        base_confidence: float
    ) -> float:
        """
        Calculate confidence score for a vulnerability match
        Higher confidence = more likely to be a real vulnerability
        """
        confidence = base_confidence
        
        # Check if match is in a comment (reduce confidence)
        line_content = lines[line_num - 1] if line_num <= len(lines) else ""
        if "//" in line_content or "/*" in line_content:
            confidence *= 0.3  # Much lower confidence for comments
        
        # Check if match is in a test function (reduce confidence)
        # Look backwards for function definition
        for i in range(max(0, line_num - 10), line_num):
            if i < len(lines) and re.search(r'function\s+test', lines[i], re.IGNORECASE):
                confidence *= 0.5
                break
        
        # Check if match is in a modifier (reduce confidence for some vuln types)
        if vuln_type == "access_control":
            for i in range(max(0, line_num - 5), line_num):
                if i < len(lines) and "modifier" in lines[i]:
                    confidence *= 0.3
                    break
        
        # Check context around match for additional indicators
        context_start = max(0, match.start() - 100)
        context_end = min(len(code), match.end() + 100)
        context = code[context_start:context_end]
        
        # Increase confidence if we see related patterns
        if vuln_type == "reentrancy":
            if "require" in context.lower() and "balance" in context.lower():
                confidence *= 1.1  # Slight boost
        
        # Cap confidence at 1.0
        return min(confidence, 1.0)
    
    def _get_code_snippet(self, lines: List[str], line_num: int, context: int = None) -> str:
        """Get code snippet with context around line number"""
        if context is None:
            context = config.code_snippet_context_lines
        
        start = max(0, line_num - context - 1)
        end = min(len(lines), line_num + context)
        
        snippet_lines = []
        for i in range(start, end):
            prefix = ">>> " if i == line_num - 1 else "    "
            snippet_lines.append(f"{prefix}{i+1}: {lines[i]}")
        
        return '\n'.join(snippet_lines)
    
    def _deduplicate_vulnerabilities(self, vulnerabilities: List[Vulnerability]) -> List[Vulnerability]:
        """Remove duplicate vulnerabilities"""
        seen: Set[Vulnerability] = set()
        unique_vulns = []
        
        for vuln in vulnerabilities:
            if vuln not in seen:
                seen.add(vuln)
                unique_vulns.append(vuln)
            else:
                logger.debug(f"Deduplicated vulnerability: {vuln.vuln_type} at line {vuln.line_number}")
        
        return unique_vulns
    
    def _calculate_risk_score(self, result: AnalysisResult) -> float:
        """
        Calculate overall risk score (0-100)
        Based on vulnerability count, severity, confidence, and code size
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
        
        # Calculate base score (weighted by confidence)
        score = 0
        for vuln in result.vulnerabilities:
            base_weight = severity_weights.get(vuln.severity, 0)
            # Adjust weight by confidence
            adjusted_weight = base_weight * vuln.confidence
            score += adjusted_weight
        
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
        print(f"\n  - {vuln.vuln_type.upper()}: {vuln.severity} (confidence: {vuln.confidence:.2f})")
        print(f"    Line {vuln.line_number}: {vuln.description}")
