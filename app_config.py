"""
Core configuration management for Solidity Vuln Scanner
Handles environment variables and application settings
"""

import os
from dataclasses import dataclass
from functools import lru_cache
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    """Application configuration"""
    
    # LLM Settings
    llm_provider: str = os.getenv("LLM_PROVIDER", "openai")
    llm_api_key: str = os.getenv("LLM_API_KEY", "")
    llm_model: str = os.getenv("LLM_MODEL", "gpt-4o-mini")
    llm_temperature: float = float(os.getenv("LLM_TEMPERATURE", "0.3"))
    use_llm: bool = os.getenv("USE_LLM", "false").lower() == "true"  # Default to false for free mode
    
    # API Settings
    api_port: int = int(os.getenv("API_PORT", "8000"))
    api_host: str = os.getenv("API_HOST", "0.0.0.0")
    debug: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # Analysis Settings
    max_report_length: int = int(os.getenv("MAX_REPORT_LENGTH", "5000"))
    timeout_seconds: int = int(os.getenv("TIMEOUT_SECONDS", "30"))
    
    # File limits
    max_file_size_mb: int = int(os.getenv("MAX_FILE_SIZE_MB", "1"))


@lru_cache(maxsize=1)
def get_config() -> Config:
    """Get singleton configuration instance"""
    return Config()


# Vulnerability severity levels
SEVERITY_LEVELS = {
    "CRITICAL": 5,
    "HIGH": 4,
    "MEDIUM": 3,
    "LOW": 2,
    "INFO": 1
}

# DASP TOP 10 vulnerability types
VULN_TYPES = {
    "reentrancy": "Reentrancy Vulnerability",
    "unchecked_call": "Unchecked External Call",
    "overflow_underflow": "Integer Overflow/Underflow",
    "access_control": "Access Control Issue",
    "bad_randomness": "Bad Randomness",
    "front_running": "Front-Running Vulnerability",
    "gas_dos": "Gas Limit DoS",
    "delegatecall": "Delegatecall Risk",
    "tx_origin": "tx.origin Misuse",
    "timestamp": "Timestamp Dependency",
    "selfdestruct": "Selfdestruct Issue",
    "logic_error": "Logic Error",
    "missing_events": "Missing Event Logging",
    "centralization": "Centralization Risk",
    "no_input_validation": "Missing Input Validation"
}
