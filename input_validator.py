"""
Input validation and sanitization for contract code
"""

import re
import unicodedata
from pathlib import Path
from typing import Tuple, Optional
from app_config import get_config
from logger_config import get_logger
from exceptions import ValidationError

logger = get_logger(__name__)
config = get_config()


def validate_contract_code(contract_code: str) -> Tuple[bool, Optional[str]]:
    """
    Validate and sanitize contract code input
    
    Args:
        contract_code: Raw contract code string
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not contract_code or not contract_code.strip():
        return False, "Contract code cannot be empty"
    
    # Check size limits
    code_size = len(contract_code)
    max_size = config.max_contract_size_chars
    
    if code_size > max_size:
        return False, f"Contract code too large ({code_size} chars, max {max_size})"
    
    # Check for potentially malicious patterns (basic sanitization)
    # Prevent regex DoS attacks by checking for extremely long lines
    lines = contract_code.split('\n')
    for i, line in enumerate(lines, 1):
        if len(line) > 10000:  # Very long line could be regex DoS
            logger.warning(f"Line {i} is extremely long ({len(line)} chars), may cause performance issues")
            return False, f"Line {i} is too long (potential DoS risk)"
    
    # Check for null bytes (could cause issues)
    if '\x00' in contract_code:
        return False, "Contract code contains null bytes"
    
    # Basic Solidity validation (must contain pragma or contract keyword)
    if not re.search(r'(pragma\s+solidity|contract\s+\w+)', contract_code, re.IGNORECASE):
        logger.warning("Contract code doesn't appear to be valid Solidity")
        # Don't reject, just warn - might be partial code
    
    return True, None


def sanitize_contract_code(contract_code: str) -> str:
    """
    Sanitize contract code (remove dangerous characters, normalize)
    
    Args:
        contract_code: Raw contract code
        
    Returns:
        Sanitized contract code
    """
    # Remove null bytes
    sanitized = contract_code.replace('\x00', '')
    
    # Normalize Unicode (prevent homograph attacks and normalize variants)
    try:
        sanitized = unicodedata.normalize('NFKC', sanitized)
    except Exception as e:
        logger.warning(f"Unicode normalization failed: {e}")
    
    # Remove control characters except newline, tab, and carriage return
    # This prevents hidden control chars that could cause issues
    sanitized = ''.join(
        c for c in sanitized 
        if unicodedata.category(c)[0] != 'C' or c in '\n\t\r'
    )
    
    # Normalize line endings
    sanitized = sanitized.replace('\r\n', '\n').replace('\r', '\n')
    
    return sanitized


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent path traversal and command injection
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename safe for use in file operations
    """
    # Get just the basename (no directory traversal)
    safe_name = Path(filename).name
    
    # Remove any remaining path separators
    safe_name = safe_name.replace('/', '').replace('\\', '')
    
    # Remove control characters and dangerous characters
    safe_name = ''.join(c for c in safe_name if c.isprintable() and c not in '<>:"|?*')
    
    # Limit length
    if len(safe_name) > 255:
        safe_name = safe_name[:255]
    
    # Ensure it's not empty or just dots
    if not safe_name or safe_name in ('.', '..'):
        safe_name = "contract.sol"
    
    return safe_name


def validate_contract_name(contract_name: str) -> Tuple[bool, Optional[str]]:
    """
    Validate contract name
    
    Args:
        contract_name: Contract name string
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not contract_name or not contract_name.strip():
        return False, "Contract name cannot be empty"
    
    if len(contract_name) > 255:
        return False, "Contract name too long (max 255 characters)"
    
    # Check for valid identifier characters
    if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', contract_name):
        return False, "Contract name contains invalid characters"
    
    return True, None
