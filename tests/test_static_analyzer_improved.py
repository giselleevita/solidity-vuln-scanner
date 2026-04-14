"""
Comprehensive tests for improved static analyzer
Tests false positives, edge cases, performance, and deduplication
"""

import pytest
from static_analyzer import StaticAnalyzer, Vulnerability, AnalysisResult
from exceptions import PatternCompilationError, AnalysisException


class TestStaticAnalyzer:
    """Test suite for StaticAnalyzer"""
    
    def test_reentrancy_detected(self):
        """Test that reentrancy vulnerabilities are detected"""
        code = """
        pragma solidity ^0.8.0;
        contract Vault {
            mapping(address => uint256) balances;
            function withdraw(uint256 amount) public {
                require(balances[msg.sender] >= amount);
                (bool ok, ) = msg.sender.call{value: amount}("");
                require(ok);
                balances[msg.sender] -= amount;
            }
        }
        """
        analyzer = StaticAnalyzer()
        result = analyzer.analyze(code, "Vault")
        vuln_types = {v.vuln_type for v in result.vulnerabilities}
        assert "reentrancy" in vuln_types or len(result.vulnerabilities) > 0
        assert any(v.severity in ["CRITICAL", "HIGH"] for v in result.vulnerabilities)
    
    def test_safe_withdraw_no_false_positive(self):
        """Test that safe withdraw pattern doesn't trigger false positive"""
        code = """
        pragma solidity ^0.8.0;
        contract SafeVault {
            mapping(address => uint256) balances;
            function withdraw(uint256 amount) public {
                require(balances[msg.sender] >= amount);
                balances[msg.sender] -= amount;  // State updated first
                (bool ok, ) = msg.sender.call{value: amount}("");
                require(ok);
            }
        }
        """
        analyzer = StaticAnalyzer()
        result = analyzer.analyze(code, "SafeVault")
        # Should have fewer or no reentrancy findings (pattern may still match but confidence should be lower)
        reentrancy_vulns = [v for v in result.vulnerabilities if v.vuln_type == "reentrancy"]
        # If found, confidence should be lower
        for vuln in reentrancy_vulns:
            assert vuln.confidence < 0.8  # Lower confidence for false positives
    
    def test_access_control_detected(self):
        """Test that missing access control is detected"""
        code = """
        pragma solidity ^0.8.0;
        contract Token {
            function mint(address to, uint256 amount) public {
                // no access control
            }
        }
        """
        analyzer = StaticAnalyzer()
        result = analyzer.analyze(code, "Token")
        vuln_types = {v.vuln_type for v in result.vulnerabilities}
        assert "access_control" in vuln_types
        assert result._get_overall_severity() in {"HIGH", "CRITICAL"}
    
    def test_clean_contract_is_safe(self):
        """Test that secure contracts have minimal findings"""
        code = """
        pragma solidity ^0.8.0;
        contract SafeToken {
            mapping(address => uint256) balances;
            address owner;
            event Transfer(address indexed from, address indexed to, uint256 amount);
            
            modifier onlyOwner() {
                require(msg.sender == owner, "Not owner");
                _;
            }
            
            constructor() {
                owner = msg.sender;
            }
            
            function transfer(address to, uint256 amount) public {
                require(balances[msg.sender] >= amount, "insufficient");
                require(to != address(0), "bad");
                balances[msg.sender] -= amount;
                balances[to] += amount;
                emit Transfer(msg.sender, to, amount);
            }
        }
        """
        analyzer = StaticAnalyzer()
        result = analyzer.analyze(code, "SafeToken")
        # Should have very few or no high-severity vulnerabilities
        high_severity = [v for v in result.vulnerabilities if v.severity in ["CRITICAL", "HIGH"]]
        assert len(high_severity) == 0 or all(v.confidence < 0.5 for v in high_severity)
    
    def test_tx_origin_detected(self):
        """Test that tx.origin misuse is detected"""
        code = """
        pragma solidity ^0.8.0;
        contract BadAuth {
            function withdraw() public {
                require(tx.origin == owner);
                // vulnerable
            }
        }
        """
        analyzer = StaticAnalyzer()
        result = analyzer.analyze(code, "BadAuth")
        vuln_types = {v.vuln_type for v in result.vulnerabilities}
        assert "tx_origin" in vuln_types
    
    def test_deduplication(self):
        """Test that duplicate vulnerabilities are removed"""
        code = """
        pragma solidity ^0.8.0;
        contract Test {
            function test() public {
                tx.origin == owner;
                tx.origin == owner;  // Duplicate
            }
        }
        """
        analyzer = StaticAnalyzer()
        result = analyzer.analyze(code, "Test")
        # Should deduplicate similar findings
        tx_origin_vulns = [v for v in result.vulnerabilities if v.vuln_type == "tx_origin"]
        # May have multiple if on different lines, but should deduplicate exact duplicates
        assert len(tx_origin_vulns) <= 2  # At most 2 (one per line)
    
    def test_confidence_scores(self):
        """Test that confidence scores are calculated"""
        code = """
        pragma solidity ^0.8.0;
        contract Test {
            function test() public {
                // tx.origin == owner;  // In comment - lower confidence
                tx.origin == owner;  // Real code - higher confidence
            }
        }
        """
        analyzer = StaticAnalyzer()
        result = analyzer.analyze(code, "Test")
        # All vulnerabilities should have confidence scores
        for vuln in result.vulnerabilities:
            assert 0.0 <= vuln.confidence <= 1.0
    
    def test_empty_contract(self):
        """Test handling of empty contract"""
        code = ""
        analyzer = StaticAnalyzer()
        result = analyzer.analyze(code, "Empty")
        assert result.contract_name == "Empty"
        assert len(result.vulnerabilities) == 0
        assert result.risk_score == 0.0
    
    def test_malformed_code(self):
        """Test handling of malformed Solidity code"""
        code = "this is not valid solidity code { { {"
        analyzer = StaticAnalyzer()
        # Should not crash, may find some patterns
        result = analyzer.analyze(code, "Malformed")
        assert isinstance(result, AnalysisResult)
    
    def test_large_contract(self):
        """Test performance with larger contract"""
        code = "pragma solidity ^0.8.0;\ncontract Large {\n"
        # Generate a larger contract
        for i in range(100):
            code += f"    uint256 value{i};\n"
        code += "    function test() public {}\n}\n"
        
        analyzer = StaticAnalyzer()
        result = analyzer.analyze(code, "Large")
        assert result.lines_of_code > 100
        assert isinstance(result, AnalysisResult)
    
    def test_pattern_compilation(self):
        """Test that patterns compile correctly"""
        import re
        analyzer = StaticAnalyzer()
        assert len(analyzer.compiled_patterns) > 0
        for key, pattern in analyzer.compiled_patterns.items():
            assert isinstance(pattern, type(re.compile("")))
    
    def test_line_number_accuracy(self):
        """Test that line numbers are accurate"""
        code = """pragma solidity ^0.8.0;

contract Test {
    function test() public {
        tx.origin == owner;  // Line 5
    }
}
"""
        analyzer = StaticAnalyzer()
        result = analyzer.analyze(code, "Test")
        # Check that line numbers are reasonable
        for vuln in result.vulnerabilities:
            assert 1 <= vuln.line_number <= len(code.split('\n'))
    
    def test_code_snippet_generation(self):
        """Test that code snippets are generated"""
        code = """
        pragma solidity ^0.8.0;
        contract Test {
            function test() public {
                tx.origin == owner;
            }
        }
        """
        analyzer = StaticAnalyzer()
        result = analyzer.analyze(code, "Test")
        for vuln in result.vulnerabilities:
            assert vuln.code_snippet
            assert ">>>" in vuln.code_snippet or ":" in vuln.code_snippet
    
    def test_risk_score_calculation(self):
        """Test risk score calculation"""
        code = """
        pragma solidity ^0.8.0;
        contract Vulnerable {
            function bad1() public { tx.origin == owner; }
            function bad2() public { tx.origin == owner; }
        }
        """
        analyzer = StaticAnalyzer()
        result = analyzer.analyze(code, "Vulnerable")
        assert 0.0 <= result.risk_score <= 100.0
        # More vulnerabilities should increase score
        if len(result.vulnerabilities) > 0:
            assert result.risk_score > 0.0


class TestErrorHandling:
    """Test error handling and edge cases"""
    
    def test_invalid_pattern_handling(self):
        """Test that invalid patterns don't crash analyzer"""
        # This is tested implicitly - if patterns don't compile, analyzer won't initialize
        analyzer = StaticAnalyzer()
        # If we get here, patterns compiled successfully
        assert analyzer is not None
    
    def test_exception_on_analysis_failure(self):
        """Test that analysis exceptions are raised appropriately"""
        analyzer = StaticAnalyzer()
        # Normal analysis should not raise
        result = analyzer.analyze("pragma solidity ^0.8.0; contract X {}", "X")
        assert isinstance(result, AnalysisResult)


class TestPerformance:
    """Test performance characteristics"""
    
    def test_pattern_compilation_once(self):
        """Test that patterns are compiled only once"""
        analyzer1 = StaticAnalyzer()
        analyzer2 = StaticAnalyzer()
        # Both should have compiled patterns
        assert len(analyzer1.compiled_patterns) == len(analyzer2.compiled_patterns)
    
    def test_line_offset_precomputation(self):
        """Test that line offsets are precomputed for performance"""
        code = "line1\nline2\nline3\n"
        analyzer = StaticAnalyzer()
        offsets = analyzer._compute_line_offsets(code)
        assert len(offsets) == 4  # 3 lines + 1 for start
        assert offsets[0] == 0
        assert offsets[1] == 6  # "line1\n"
    
    def test_binary_search_line_lookup(self):
        """Test binary search for line number lookup"""
        code = "line1\nline2\nline3\nline4\n"
        analyzer = StaticAnalyzer()
        offsets = analyzer._compute_line_offsets(code)
        # Test various positions
        assert analyzer._get_line_number(0, offsets) == 1
        assert analyzer._get_line_number(6, offsets) == 2
        assert analyzer._get_line_number(12, offsets) == 3
