"""
LLM Auditor for Smart Contract Analysis
Uses OpenAI/Claude to perform intelligent security auditing
Supports both sync and async operations
"""

import json
import os
import asyncio
from typing import Optional, Dict, List
import time
from dataclasses import dataclass
from app_config import get_config
from logger_config import get_logger
from exceptions import LLMAuditException

# Retry logic
try:
    from tenacity import (
        retry,
        stop_after_attempt,
        wait_exponential,
        retry_if_exception_type
    )
    RETRY_AVAILABLE = True
except ImportError:
    RETRY_AVAILABLE = False

logger = get_logger(__name__)
config = get_config()


@dataclass
class LLMAuditResult:
    """Result of LLM-based audit"""
    summary: str
    recommendations: List[str]
    logic_vulnerabilities: List[str]
    best_practices: List[str]
    risk_assessment: str
    tokens_used: int = 0
    
    def to_dict(self):
        return {
            "summary": self.summary,
            "recommendations": self.recommendations,
            "logic_vulnerabilities": self.logic_vulnerabilities,
            "best_practices": self.best_practices,
            "risk_assessment": self.risk_assessment,
            "tokens_used": self.tokens_used
        }


class LLMAuditor:
    """
    Uses OpenAI/Claude API to perform intelligent security analysis
    Complements pattern-based static analysis with semantic understanding
    """
    
    def __init__(self, api_key: str = None, model: str = "gpt-4o-mini", provider: str = "openai"):
        """
        Initialize LLM auditor
        
        Args:
            api_key: API key for LLM provider (uses env var if not provided)
            model: Model name (gpt-4o-mini for OpenAI, claude-3-sonnet for Anthropic)
            provider: "openai" or "anthropic"
        """
        self.api_key = api_key or os.getenv("LLM_API_KEY")
        self.model = model
        self.provider = provider
        
        if not self.api_key:
            raise ValueError("LLM_API_KEY environment variable not set")
        
        if provider == "openai":
            try:
                import openai
                # Initialize OpenAI client with only api_key to avoid version conflicts
                self.client = openai.OpenAI(api_key=self.api_key)
                # Also create async client
                try:
                    self.async_client = openai.AsyncOpenAI(api_key=self.api_key)
                except Exception:
                    self.async_client = None
                    logger.warning("Async OpenAI client not available")
            except TypeError as e:
                # Handle version compatibility issues gracefully
                if "unexpected keyword argument" in str(e):
                    raise ValueError(f"OpenAI client version incompatibility: {e}. Try: pip install --upgrade openai")
                raise
            except ImportError:
                raise ImportError("openai package not installed. Run: pip install openai")
        elif provider == "anthropic":
            try:
                import anthropic
                self.client = anthropic.Anthropic(api_key=self.api_key)
                self.async_client = None  # Anthropic async support can be added later
            except ImportError:
                raise ImportError("anthropic package not installed. Run: pip install anthropic")
        
        logger.info(f"LLM auditor initialized with provider: {provider}, model: {model}")
    
    def audit(self, contract_code: str, contract_name: str = "Contract") -> LLMAuditResult:
        """
        Perform LLM-based security audit of smart contract
        
        Args:
            contract_code: Solidity source code
            contract_name: Name of contract
            
        Returns:
            LLMAuditResult with audit findings
        """
        if not contract_code.strip():
            return LLMAuditResult(
                summary="No contract code provided",
                recommendations=[],
                logic_vulnerabilities=[],
                best_practices=[],
                risk_assessment="UNKNOWN"
            )
        
        # Handle large contracts (use config limit, warn if truncated)
        max_size = config.llm_max_contract_size
        original_size = len(contract_code)
        if original_size > max_size:
            logger.warning(f"Contract code truncated from {original_size} to {max_size} chars for LLM analysis")
            contract_code = contract_code[:max_size] + "\n... [truncated - contract too large for full analysis]"
        
        try:
            if self.provider == "openai":
                return self._audit_with_openai(contract_code, contract_name)
            elif self.provider == "anthropic":
                return self._audit_with_anthropic(contract_code, contract_name)
            else:
                raise ValueError(f"Unknown provider: {self.provider}")
        except Exception as e:
            logger.error(f"LLM audit failed: {e}", exc_info=True)
            raise LLMAuditException(f"LLM audit failed: {str(e)}")
    
    async def audit_async(self, contract_code: str, contract_name: str = "Contract") -> LLMAuditResult:
        """
        Async version of audit method
        
        Args:
            contract_code: Solidity source code
            contract_name: Name of contract
            
        Returns:
            LLMAuditResult with audit findings
        """
        if not contract_code.strip():
            return LLMAuditResult(
                summary="No contract code provided",
                recommendations=[],
                logic_vulnerabilities=[],
                best_practices=[],
                risk_assessment="UNKNOWN"
            )
        
        # Handle large contracts
        max_size = config.llm_max_contract_size
        original_size = len(contract_code)
        if original_size > max_size:
            logger.warning(f"Contract code truncated from {original_size} to {max_size} chars for LLM analysis")
            contract_code = contract_code[:max_size] + "\n... [truncated - contract too large for full analysis]"
        
        try:
            if self.provider == "openai" and self.async_client:
                return await self._audit_with_openai_async(contract_code, contract_name)
            elif self.provider == "openai":
                # Fallback to sync if async client not available
                logger.warning("Async client not available, using sync method")
                return self.audit(contract_code, contract_name)
            elif self.provider == "anthropic":
                # Anthropic async can be added later
                logger.warning("Async not yet supported for Anthropic, using sync method")
                return self.audit(contract_code, contract_name)
            else:
                raise ValueError(f"Unknown provider: {self.provider}")
        except Exception as e:
            logger.error(f"Async LLM audit failed: {e}", exc_info=True)
            raise LLMAuditException(f"LLM audit failed: {str(e)}")
    
    def _audit_with_openai(self, contract_code: str, contract_name: str) -> LLMAuditResult:
        """Perform audit using OpenAI API (sync)"""
        
        prompt = self._build_audit_prompt(contract_code, contract_name)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert Solidity security auditor. Analyze smart contracts for vulnerabilities, logic flaws, and best practice violations. Return a valid JSON response."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=2000,
                response_format={"type": "json_object"}
            )
            
            response_text = response.choices[0].message.content
            tokens_used = response.usage.total_tokens if hasattr(response, 'usage') else 0
            result = self._parse_audit_response(response_text)
            result.tokens_used = tokens_used
            return result
            
        except Exception as e:
            logger.warning(f"OpenAI JSON mode failed, trying fallback: {e}")
            # Fallback: try without JSON mode
            return self._audit_with_openai_fallback(contract_code, contract_name)
    
    async def _audit_with_openai_async(self, contract_code: str, contract_name: str) -> LLMAuditResult:
        """Perform audit using OpenAI API (async) with retry logic"""
        
        prompt = self._build_audit_prompt(contract_code, contract_name)
        
        # Retry function with exponential backoff
        async def _call_api_with_retry():
            max_attempts = 3
            for attempt in range(max_attempts):
                try:
                    response = await asyncio.wait_for(
                        self.async_client.chat.completions.create(
                            model=self.model,
                            messages=[
                                {
                                    "role": "system",
                                    "content": "You are an expert Solidity security auditor. Analyze smart contracts for vulnerabilities, logic flaws, and best practice violations. Return a valid JSON response."
                                },
                                {
                                    "role": "user",
                                    "content": prompt
                                }
                            ],
                            temperature=0.3,
                            max_tokens=2000,
                            response_format={"type": "json_object"}
                        ),
                        timeout=60.0  # 60 second timeout
                    )
                    return response
                except asyncio.TimeoutError:
                    if attempt < max_attempts - 1:
                        wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                        logger.warning(f"OpenAI API timeout (attempt {attempt + 1}/{max_attempts}), retrying in {wait_time}s...")
                        await asyncio.sleep(wait_time)
                    else:
                        raise LLMAuditException("OpenAI API request timed out after 3 attempts")
                except Exception as e:
                    if attempt < max_attempts - 1:
                        wait_time = 2 ** attempt
                        logger.warning(f"OpenAI API error (attempt {attempt + 1}/{max_attempts}): {e}, retrying in {wait_time}s...")
                        await asyncio.sleep(wait_time)
                    else:
                        raise
        
        try:
            response = await _call_api_with_retry()
            response_text = response.choices[0].message.content
            tokens_used = response.usage.total_tokens if hasattr(response, 'usage') else 0
            result = self._parse_audit_response(response_text)
            result.tokens_used = tokens_used
            return result
            
        except Exception as e:
            logger.warning(f"OpenAI async JSON mode failed, trying fallback: {e}")
            # Fallback: try without JSON mode
            return await self._audit_with_openai_fallback_async(contract_code, contract_name)
    
    def _audit_with_openai_fallback(self, contract_code: str, contract_name: str) -> LLMAuditResult:
        """Fallback audit without JSON mode (sync)"""
        
        simple_prompt = f"""Analyze this Solidity contract for security issues:

{contract_code}

Provide a brief security assessment covering:
1. Critical vulnerabilities
2. Recommendations
3. Risk level (LOW/MEDIUM/HIGH/CRITICAL)"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a Solidity security expert. Provide practical security advice."
                    },
                    {
                        "role": "user",
                        "content": simple_prompt
                    }
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            summary = response.choices[0].message.content
            tokens_used = response.usage.total_tokens if hasattr(response, 'usage') else 0
            
            return LLMAuditResult(
                summary=summary,
                recommendations=["Conduct professional security audit for production deployment"],
                logic_vulnerabilities=[],
                best_practices=[],
                risk_assessment="MEDIUM",
                tokens_used=tokens_used
            )
        except Exception as e:
            logger.error(f"OpenAI fallback failed: {e}", exc_info=True)
            raise LLMAuditException(f"LLM audit failed: {str(e)}")
    
    async def _audit_with_openai_fallback_async(self, contract_code: str, contract_name: str) -> LLMAuditResult:
        """Fallback audit without JSON mode (async)"""
        
        simple_prompt = f"""Analyze this Solidity contract for security issues:

{contract_code}

Provide a brief security assessment covering:
1. Critical vulnerabilities
2. Recommendations
3. Risk level (LOW/MEDIUM/HIGH/CRITICAL)"""
        
        try:
            response = await self.async_client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a Solidity security expert. Provide practical security advice."
                    },
                    {
                        "role": "user",
                        "content": simple_prompt
                    }
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            summary = response.choices[0].message.content
            tokens_used = response.usage.total_tokens if hasattr(response, 'usage') else 0
            
            return LLMAuditResult(
                summary=summary,
                recommendations=["Conduct professional security audit for production deployment"],
                logic_vulnerabilities=[],
                best_practices=[],
                risk_assessment="MEDIUM",
                tokens_used=tokens_used
            )
        except Exception as e:
            logger.error(f"OpenAI async fallback failed: {e}", exc_info=True)
            raise LLMAuditException(f"LLM audit failed: {str(e)}")
    
    def _audit_with_anthropic(self, contract_code: str, contract_name: str) -> LLMAuditResult:
        """Perform audit using Anthropic/Claude API"""
        
        prompt = self._build_audit_prompt(contract_code, contract_name)
        
        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            response_text = message.content[0].text
            tokens_used = message.usage.input_tokens + message.usage.output_tokens if hasattr(message, 'usage') else 0
            result = self._parse_audit_response(response_text)
            result.tokens_used = tokens_used
            return result
            
        except Exception as e:
            logger.error(f"Anthropic API call failed: {e}", exc_info=True)
            raise LLMAuditException(f"Anthropic audit failed: {str(e)}")
    
    def _build_audit_prompt(self, contract_code: str, contract_name: str) -> str:
        """Build the audit prompt for LLM"""
        
        return f"""Analyze this Solidity smart contract "{contract_name}" for security vulnerabilities:

```solidity
{contract_code}
```

Provide a security audit in JSON format with these fields:
{{
    "summary": "Brief overview of contract security posture",
    "recommendations": ["List of actionable recommendations"],
    "logic_vulnerabilities": ["Logic-level vulnerabilities not caught by static analysis"],
    "best_practices": ["Best practices this contract should follow"],
    "risk_assessment": "CRITICAL|HIGH|MEDIUM|LOW|INFO"
}}

Focus on:
- Reentrancy and state management
- Access control and authorization
- Arithmetic operations and overflow/underflow
- External calls and dependencies
- Business logic flaws
- Gas optimization issues
- Compliance with DASP TOP 10

Be specific with line references where possible."""
    
    def _parse_audit_response(self, response_text: str) -> LLMAuditResult:
        """Parse LLM response into structured format"""
        
        try:
            # Try to extract JSON from response
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                audit_data = json.loads(json_str)
            else:
                # Fallback: parse as plain text
                audit_data = {
                    "summary": response_text[:500],
                    "recommendations": ["Review audit output above"],
                    "logic_vulnerabilities": [],
                    "best_practices": [],
                    "risk_assessment": "MEDIUM"
                }
            
            return LLMAuditResult(
                summary=audit_data.get("summary", ""),
                recommendations=audit_data.get("recommendations", []),
                logic_vulnerabilities=audit_data.get("logic_vulnerabilities", []),
                best_practices=audit_data.get("best_practices", []),
                risk_assessment=audit_data.get("risk_assessment", "MEDIUM")
            )
            
        except json.JSONDecodeError:
            # Last resort: return raw response
            return LLMAuditResult(
                summary=response_text[:500],
                recommendations=["See summary above"],
                logic_vulnerabilities=[],
                best_practices=[],
                risk_assessment="MEDIUM"
            )


# Example usage
if __name__ == "__main__":
    contract = '''
    pragma solidity ^0.8.0;
    
    contract Token {
        mapping(address => uint256) balances;
        address owner;
        
        constructor() {
            owner = msg.sender;
        }
        
        function transfer(address to, uint256 amount) public {
            require(balances[msg.sender] >= amount);
            balances[msg.sender] -= amount;
            balances[to] += amount;
        }
    }
    '''
    
    # Requires LLM_API_KEY environment variable to be set
    auditor = LLMAuditor()
    result = auditor.audit(contract)
    print(json.dumps(result.to_dict(), indent=2))
