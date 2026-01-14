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
    
    # Rate limiting
    rate_limit_max_requests: int = int(os.getenv("RATE_LIMIT_MAX_REQUESTS", "60"))
    rate_limit_window_seconds: int = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))
    
    # Caching
    cache_max_size: int = int(os.getenv("CACHE_MAX_SIZE", "100"))
    cache_ttl_seconds: int = int(os.getenv("CACHE_TTL_SECONDS", "3600"))
    
    # CORS
    cors_origins: str = os.getenv("CORS_ORIGINS", "*")  # Comma-separated or "*" for all
    
    # LLM limits
    llm_max_contract_size: int = int(os.getenv("LLM_MAX_CONTRACT_SIZE", "50000"))  # Increased from 5000
    
    # Analysis constants
    max_contract_size_chars: int = int(os.getenv("MAX_CONTRACT_SIZE_CHARS", "1000000"))  # ~1MB
    code_snippet_context_lines: int = int(os.getenv("CODE_SNIPPET_CONTEXT_LINES", "2"))
    
    # Database settings
    database_type: str = os.getenv("DATABASE_TYPE", "sqlite")  # sqlite or postgresql
    database_path: str = os.getenv("DATABASE_PATH", "scanner.db")
    database_user: str = os.getenv("DATABASE_USER", "postgres")
    database_password: str = os.getenv("DATABASE_PASSWORD", "")
    database_host: str = os.getenv("DATABASE_HOST", "localhost")
    database_port: str = os.getenv("DATABASE_PORT", "5432")
    database_name: str = os.getenv("DATABASE_NAME", "scanner")
    
    # Redis settings
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # JWT settings
    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY", "change-this-secret-key-in-production")
    jwt_expire_minutes: int = int(os.getenv("JWT_EXPIRE_MINUTES", "1440"))  # 24 hours
    require_auth: bool = os.getenv("REQUIRE_AUTH", "false").lower() == "true"  # Require auth by default
    production_mode: bool = os.getenv("PRODUCTION_MODE", "false").lower() == "true"
    
    def get(self, key: str, default=None):
        """Get config value (for compatibility)"""
        return getattr(self, key, default)


@lru_cache(maxsize=1)
def get_config() -> Config:
    """Get singleton configuration instance"""
    config = Config()
    
    # Security validation
    if config.production_mode:
        # In production, enforce secure defaults
        if config.jwt_secret_key == "change-this-secret-key-in-production":
            raise ValueError(
                "JWT_SECRET_KEY must be set in production mode. "
                "Generate a secure secret: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
            )
        
        # Warn about insecure CORS
        if config.cors_origins == "*":
            import warnings
            warnings.warn(
                "⚠️  SECURITY WARNING: CORS allows all origins in production mode. "
                "Set CORS_ORIGINS to specific domains.",
                UserWarning
            )
    
    return config


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
