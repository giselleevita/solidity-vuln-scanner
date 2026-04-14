"""
Custom exceptions for the Solidity vulnerability scanner
"""


class ScannerException(Exception):
    """Base exception for all scanner errors"""
    pass


class AnalysisException(ScannerException):
    """Exception raised during contract analysis"""
    pass


class PatternCompilationError(ScannerException):
    """Exception raised when pattern compilation fails"""
    pass


class LLMAuditException(ScannerException):
    """Exception raised during LLM audit"""
    pass


class ValidationError(ScannerException):
    """Exception raised for input validation errors"""
    pass


class ToolExecutionError(ScannerException):
    """Exception raised when external tool execution fails"""
    pass


class ConfigurationError(ScannerException):
    """Exception raised for configuration errors"""
    pass
