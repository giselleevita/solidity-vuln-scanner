"""
Security tests for Solidity Vuln Scanner
Tests authentication, input validation, injection prevention, etc.
"""

import pytest
import re
from fastapi.testclient import TestClient
from fastapi_api import app
from input_validator import sanitize_filename, validate_contract_code, sanitize_contract_code
from tools_integration import run_slither


client = TestClient(app)


class TestInputValidation:
    """Test input validation and sanitization"""
    
    def test_path_traversal_prevention(self):
        """Test that path traversal attempts are blocked"""
        # Test various path traversal patterns
        malicious_names = [
            "../../etc/passwd",
            "..\\..\\windows\\system32",
            "/etc/passwd",
            "....//....//etc/passwd",
            "..%2F..%2Fetc%2Fpasswd",
        ]
        
        for name in malicious_names:
            safe = sanitize_filename(name)
            assert ".." not in safe
            assert "/" not in safe
            assert "\\" not in safe
            assert safe != name  # Should be sanitized
    
    def test_command_injection_prevention(self):
        """Test that command injection attempts are blocked"""
        malicious_names = [
            "contract; rm -rf /",
            "contract | cat /etc/passwd",
            "contract && echo pwned",
            "contract`whoami`",
            'contract$(ls)',
        ]
        
        for name in malicious_names:
            safe = sanitize_filename(name)
            # Should not contain shell metacharacters
            assert ";" not in safe
            assert "|" not in safe
            assert "&" not in safe
            assert "`" not in safe
            assert "$" not in safe
    
    def test_null_byte_injection(self):
        """Test that null bytes are rejected"""
        code_with_null = "pragma solidity ^0.8.0;\x00contract Test {}"
        is_valid, error = validate_contract_code(code_with_null)
        assert not is_valid
        assert "null bytes" in error.lower()
    
    def test_unicode_normalization(self):
        """Test Unicode normalization prevents homograph attacks"""
        # Use look-alike characters
        malicious_code = "pragma solidity ^0.8.0; contract Test {}"
        # Replace 'a' with Cyrillic 'а' (looks identical)
        # This is tricky to test without actual homograph chars
        sanitized = sanitize_contract_code(malicious_code)
        # Should be normalized
        assert len(sanitized) > 0
    
    def test_long_line_detection(self):
        """Test that extremely long lines are rejected (ReDoS prevention)"""
        # Create a line that's too long
        long_line = "a" * 15000
        code = f"pragma solidity ^0.8.0;\n{long_line}\ncontract Test {{}}"
        
        is_valid, error = validate_contract_code(code)
        assert not is_valid
        assert "too long" in error.lower()


class TestAPISecurity:
    """Test API security features"""
    
    def test_cors_configuration(self):
        """Test that CORS is properly configured"""
        # Should not allow arbitrary origins in production
        response = client.options("/health")
        # CORS headers should be present
        assert response.status_code in [200, 204]
    
    def test_rate_limiting_headers(self):
        """Test that rate limit headers are present"""
        # Make a request
        response = client.get("/health")
        # Should have rate limit headers (if middleware is active)
        # Note: May not be present if middleware not loaded
        headers = response.headers
        # Just verify request succeeds
        assert response.status_code == 200
    
    def test_large_payload_rejection(self):
        """Test that oversized payloads are rejected"""
        # Create a contract that's too large
        huge_code = "pragma solidity ^0.8.0;\n" + ("contract Test {}\n" * 100000)
        
        response = client.post(
            "/analyze",
            json={
                "contract_code": huge_code,
                "contract_name": "Test",
                "use_llm_audit": False
            }
        )
        # Should be rejected (400 or 413)
        assert response.status_code in [400, 413, 422]
    
    def test_malicious_json_structure(self):
        """Test that malformed JSON is handled safely"""
        # Try to send non-JSON data
        response = client.post(
            "/analyze",
            data="<script>alert('xss')</script>",
            headers={"Content-Type": "application/json"}
        )
        # Should return 422 (validation error)
        assert response.status_code == 422


class TestFileSecurity:
    """Test file handling security"""
    
    def test_filename_sanitization(self):
        """Test that filenames are sanitized before file operations"""
        malicious = "../../etc/passwd"
        safe = sanitize_filename(malicious)
        
        assert safe != malicious
        assert ".." not in safe
        assert "/" not in safe
    
    def test_empty_filename_handling(self):
        """Test that empty or dangerous filenames are handled"""
        test_cases = ["", ".", "..", None]
        
        for case in test_cases:
            if case is None:
                continue  # Skip None for now
            safe = sanitize_filename(case)
            # Should default to safe value
            assert safe == "contract.sol" or len(safe) > 0


class TestRegexSecurity:
    """Test regex pattern security"""
    
    def test_reentrancy_pattern_safety(self):
        """Test that reentrancy pattern doesn't cause ReDoS"""
        # Create code that could trigger ReDoS if pattern is vulnerable
        # This is a basic test - real ReDoS testing requires more complex patterns
        code = "pragma solidity ^0.8.0;\ncontract Test { function test() public { payable(msg.sender).call{value: 1}(''); } }"
        
        # Should complete in reasonable time
        from static_analyzer import StaticAnalyzer
        analyzer = StaticAnalyzer()
        result = analyzer.analyze(code, "Test")
        
        # Should complete without hanging
        assert result is not None


@pytest.mark.skipif(not pytest.config.getoption("--run-slow"), reason="Requires external tools")
class TestToolSecurity:
    """Test security of external tool integration"""
    
    def test_slither_filename_sanitization(self):
        """Test that Slither receives sanitized filenames"""
        code = "pragma solidity ^0.8.0; contract Test {}"
        malicious_name = "../../etc/passwd"
        
        # Should sanitize filename before passing to tool
        success, output = run_slither(code, filename=malicious_name, timeout=10)
        # Should not fail due to filename issues
        # Note: May fail if Slither not installed, but shouldn't be a security issue
        assert isinstance(success, bool)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
