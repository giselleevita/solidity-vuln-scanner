"""
Tests for input validation and sanitization
"""

import pytest
from input_validator import (
    validate_contract_code,
    sanitize_contract_code,
    validate_contract_name
)


class TestContractCodeValidation:
    """Test contract code validation"""
    
    def test_empty_code_rejected(self):
        """Test that empty code is rejected"""
        is_valid, error = validate_contract_code("")
        assert not is_valid
        assert "empty" in error.lower()
    
    def test_whitespace_only_rejected(self):
        """Test that whitespace-only code is rejected"""
        is_valid, error = validate_contract_code("   \n\t  ")
        assert not is_valid
    
    def test_valid_code_accepted(self):
        """Test that valid Solidity code is accepted"""
        code = "pragma solidity ^0.8.0; contract X {}"
        is_valid, error = validate_contract_code(code)
        assert is_valid
        assert error is None
    
    def test_large_code_rejected(self):
        """Test that extremely large code is rejected"""
        # Create code larger than default limit (1MB = 1,000,000 chars)
        large_code = "pragma solidity ^0.8.0;\n" + "x" * 2000000
        is_valid, error = validate_contract_code(large_code)
        assert not is_valid
        assert "too large" in error.lower()
    
    def test_null_bytes_rejected(self):
        """Test that null bytes are rejected"""
        code = "pragma solidity ^0.8.0;\x00contract X {}"
        is_valid, error = validate_contract_code(code)
        assert not is_valid
        assert "null bytes" in error.lower()
    
    def test_extremely_long_line_rejected(self):
        """Test that extremely long lines are rejected (DoS protection)"""
        long_line = "x" * 15000
        code = f"pragma solidity ^0.8.0;\n{long_line}\ncontract X {{}}"
        is_valid, error = validate_contract_code(code)
        assert not is_valid
        assert "too long" in error.lower()


class TestContractCodeSanitization:
    """Test contract code sanitization"""
    
    def test_null_bytes_removed(self):
        """Test that null bytes are removed"""
        code = "pragma solidity ^0.8.0;\x00contract X {}"
        sanitized = sanitize_contract_code(code)
        assert "\x00" not in sanitized
    
    def test_line_endings_normalized(self):
        """Test that line endings are normalized"""
        code = "line1\r\nline2\rline3\n"
        sanitized = sanitize_contract_code(code)
        assert "\r" not in sanitized
        assert "\n" in sanitized
    
    def test_valid_code_unchanged(self):
        """Test that valid code is unchanged"""
        code = "pragma solidity ^0.8.0; contract X {}"
        sanitized = sanitize_contract_code(code)
        assert sanitized == code


class TestContractNameValidation:
    """Test contract name validation"""
    
    def test_empty_name_rejected(self):
        """Test that empty name is rejected"""
        is_valid, error = validate_contract_name("")
        assert not is_valid
        assert "empty" in error.lower()
    
    def test_valid_name_accepted(self):
        """Test that valid names are accepted"""
        valid_names = ["MyContract", "Token_ERC20", "Vault_v2", "_private"]
        for name in valid_names:
            is_valid, error = validate_contract_name(name)
            assert is_valid, f"Name '{name}' should be valid"
            assert error is None
    
    def test_invalid_characters_rejected(self):
        """Test that invalid characters are rejected"""
        invalid_names = ["My-Contract", "Token.ERC20", "Vault v2", "123Contract"]
        for name in invalid_names:
            is_valid, error = validate_contract_name(name)
            assert not is_valid, f"Name '{name}' should be invalid"
            assert "invalid" in error.lower()
    
    def test_too_long_name_rejected(self):
        """Test that too long names are rejected"""
        long_name = "A" * 300
        is_valid, error = validate_contract_name(long_name)
        assert not is_valid
        assert "too long" in error.lower()
