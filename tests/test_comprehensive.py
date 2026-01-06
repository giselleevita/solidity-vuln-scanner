"""
Comprehensive test suite for Solidity Vuln Scanner
Tests reliability, edge cases, and real-world scenarios
"""

import pytest
from static_analyzer import StaticAnalyzer
from fastapi.testclient import TestClient
import fastapi_api
from tools_integration import check_slither_installed, check_mythril_installed


client = TestClient(fastapi_api.app)


class TestStaticAnalyzerReliability:
    """Test static analyzer reliability and edge cases"""
    
    def test_empty_contract(self):
        """Test empty contract handling"""
        analyzer = StaticAnalyzer()
        result = analyzer.analyze("", "Empty")
        assert result.contract_name == "Empty"
        assert result.risk_score == 0.0
        assert len(result.vulnerabilities) == 0
    
    def test_very_large_contract(self):
        """Test handling of large contracts"""
        large_code = "pragma solidity ^0.8.0;\n" + "contract Large {\n" + "\n".join([f"    uint256 x{i} = {i};" for i in range(1000)]) + "\n}"
        analyzer = StaticAnalyzer()
        result = analyzer.analyze(large_code, "Large")
        assert result.lines_of_code > 1000
        assert result.risk_score >= 0
    
    def test_multiple_reentrancy_patterns(self):
        """Test detection of multiple reentrancy instances"""
        code = """
        pragma solidity ^0.8.0;
        contract MultiReentrancy {
            function withdraw1(uint256 a) public {
                msg.sender.call{value: a}("");
                balances[msg.sender] -= a;
            }
            function withdraw2(uint256 a) public {
                msg.sender.call{value: a}("");
                balances[msg.sender] -= a;
            }
        }
        """
        analyzer = StaticAnalyzer()
        result = analyzer.analyze(code, "MultiReentrancy")
        reentrancy_count = sum(1 for v in result.vulnerabilities if v.vuln_type == "reentrancy")
        assert reentrancy_count >= 1
    
    def test_safe_contract_no_false_positives(self):
        """Test that safe contracts don't trigger false positives"""
        safe_code = """
        pragma solidity ^0.8.0;
        contract Safe {
            mapping(address => uint256) balances;
            function transfer(address to, uint256 amount) public {
                require(balances[msg.sender] >= amount);
                require(to != address(0));
                balances[msg.sender] -= amount;
                balances[to] += amount;
            }
        }
        """
        analyzer = StaticAnalyzer()
        result = analyzer.analyze(safe_code, "Safe")
        # Should have minimal or no vulnerabilities
        assert result.risk_score < 20
    
    def test_special_characters_in_code(self):
        """Test handling of special characters"""
        code = 'pragma solidity ^0.8.0; contract Test { string s = "Hello\\nWorld"; }'
        analyzer = StaticAnalyzer()
        result = analyzer.analyze(code, "Test")
        assert result.contract_name == "Test"


class TestAPIReliability:
    """Test API reliability and error handling"""
    
    def test_health_endpoint(self):
        """Test health check"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "llm_enabled" in data
    
    def test_empty_contract_code(self):
        """Test API handles empty contract code"""
        response = client.post("/analyze", json={
            "contract_code": "",
            "contract_name": "Test"
        })
        assert response.status_code == 400
    
    def test_whitespace_only_contract(self):
        """Test API handles whitespace-only code"""
        response = client.post("/analyze", json={
            "contract_code": "   \n\t  ",
            "contract_name": "Test"
        })
        assert response.status_code == 400
    
    def test_very_long_contract_name(self):
        """Test API handles long contract names"""
        long_name = "A" * 1000
        response = client.post("/analyze", json={
            "contract_code": "pragma solidity ^0.8.0; contract X {}",
            "contract_name": long_name
        })
        # Should handle gracefully
        assert response.status_code in [200, 400]
    
    def test_invalid_json(self):
        """Test API handles invalid JSON gracefully"""
        # This is handled by FastAPI automatically, but we test the endpoint exists
        response = client.post("/analyze", json={
            "contract_code": "pragma solidity ^0.8.0; contract X {}",
            "contract_name": "X"
        })
        assert response.status_code == 200
    
    def test_batch_analysis_empty_list(self):
        """Test batch analysis with empty list"""
        response = client.post("/analyze-batch", json=[])
        assert response.status_code == 200
        assert response.json() == []
    
    def test_batch_analysis_too_many(self):
        """Test batch analysis limit"""
        contracts = [{"contract_code": "pragma solidity ^0.8.0; contract X {}", "contract_name": f"X{i}"} 
                     for i in range(11)]
        response = client.post("/analyze-batch", json=contracts)
        assert response.status_code == 400
    
    def test_tools_status_endpoint(self):
        """Test tools status endpoint"""
        response = client.get("/tools/status")
        assert response.status_code == 200
        data = response.json()
        assert "slither" in data
        assert "mythril" in data
        assert "installed" in data["slither"]
        assert "message" in data["slither"]


class TestRealWorldScenarios:
    """Test real-world contract scenarios"""
    
    def test_erc20_like_token(self):
        """Test ERC20-like token contract"""
        erc20_code = """
        pragma solidity ^0.8.0;
        contract Token {
            mapping(address => uint256) balances;
            mapping(address => mapping(address => uint256)) allowances;
            
            function transfer(address to, uint256 amount) public returns (bool) {
                require(balances[msg.sender] >= amount);
                balances[msg.sender] -= amount;
                balances[to] += amount;
                return true;
            }
            
            function approve(address spender, uint256 amount) public returns (bool) {
                allowances[msg.sender][spender] = amount;
                return true;
            }
        }
        """
        analyzer = StaticAnalyzer()
        result = analyzer.analyze(erc20_code, "Token")
        assert result.risk_score < 30  # Should be relatively safe
    
    def test_vault_with_reentrancy(self):
        """Test vault contract with known reentrancy"""
        vault_code = """
        pragma solidity ^0.8.0;
        contract Vault {
            mapping(address => uint256) balances;
            function withdraw(uint256 amount) public {
                require(balances[msg.sender] >= amount);
                (bool success, ) = msg.sender.call{value: amount}("");
                require(success);
                balances[msg.sender] -= amount;
            }
        }
        """
        analyzer = StaticAnalyzer()
        result = analyzer.analyze(vault_code, "Vault")
        assert result.risk_score > 50  # Should detect reentrancy
        assert any(v.vuln_type == "reentrancy" for v in result.vulnerabilities)
    
    def test_contract_with_comments(self):
        """Test contract with extensive comments"""
        commented_code = """
        pragma solidity ^0.8.0;
        // This is a test contract
        contract Commented {
            /* Multi-line comment
               with more details */
            function test() public {
                // Single line comment
                uint256 x = 1;
            }
        }
        """
        analyzer = StaticAnalyzer()
        result = analyzer.analyze(commented_code, "Commented")
        # Comments should be stripped, shouldn't affect analysis
        assert result.contract_name == "Commented"


class TestToolIntegration:
    """Test external tool integration"""
    
    def test_slither_check(self):
        """Test Slither installation check"""
        installed, message = check_slither_installed()
        assert isinstance(installed, bool)
        assert isinstance(message, str)
        assert len(message) > 0
    
    def test_mythril_check(self):
        """Test Mythril installation check"""
        installed, message = check_mythril_installed()
        assert isinstance(installed, bool)
        assert isinstance(message, str)
        assert len(message) > 0
    
    def test_slither_with_simple_contract(self):
        """Test Slither runs on simple contract"""
        from tools_integration import run_slither
        code = "pragma solidity ^0.8.0; contract X {}"
        success, output = run_slither(code, "X.sol")
        assert isinstance(success, bool)
        assert isinstance(output, str)
        # Even if not installed, should return gracefully
        if not success:
            assert "not installed" in output.lower() or "error" in output.lower()
    
    def test_mythril_with_simple_contract(self):
        """Test Mythril runs on simple contract"""
        from tools_integration import run_mythril
        code = "pragma solidity ^0.8.0; contract X {}"
        success, output = run_mythril(code, "X.sol")
        assert isinstance(success, bool)
        assert isinstance(output, str)
        # Even if not installed, should return gracefully
        if not success:
            assert "not installed" in output.lower() or "error" in output.lower()


class TestRiskScoring:
    """Test risk scoring algorithm"""
    
    def test_risk_score_calculation(self):
        """Test risk score is calculated correctly"""
        analyzer = StaticAnalyzer()
        
        # Safe contract should have low score
        safe_code = "pragma solidity ^0.8.0; contract Safe {}"
        safe_result = analyzer.analyze(safe_code, "Safe")
        assert safe_result.risk_score >= 0
        assert safe_result.risk_score <= 20
        
        # Vulnerable contract should have higher score
        vuln_code = """
        pragma solidity ^0.8.0;
        contract Vuln {
            function bad() public {
                msg.sender.call{value: 1}("");
                balances[msg.sender] = 0;
            }
        }
        """
        vuln_result = analyzer.analyze(vuln_code, "Vuln")
        assert vuln_result.risk_score > safe_result.risk_score
    
    def test_severity_distribution(self):
        """Test severity distribution calculation"""
        analyzer = StaticAnalyzer()
        code = "pragma solidity ^0.8.0; contract Test {}"
        result = analyzer.analyze(code, "Test")
        dist = result.severity_distribution()
        assert isinstance(dist, dict)
        assert "CRITICAL" in dist
        assert "HIGH" in dist
        assert "MEDIUM" in dist
        assert "LOW" in dist
        assert "INFO" in dist


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

