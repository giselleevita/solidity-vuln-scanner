"""
LLM Auditor for Smart Contract Analysis
Uses OpenAI/Claude to perform intelligent security auditing
"""

import json
import os
from typing import Optional, Dict, List
import time
from dataclasses import dataclass


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
            except ImportError:
                raise ImportError("anthropic package not installed. Run: pip install anthropic")
    
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
        
        # Truncate large contracts
        if len(contract_code) > 5000:
            contract_code = contract_code[:5000] + "\n... [truncated]"
        
        try:
            if self.provider == "openai":
                return self._audit_with_openai(contract_code, contract_name)
            elif self.provider == "anthropic":
                return self._audit_with_anthropic(contract_code, contract_name)
            else:
                raise ValueError(f"Unknown provider: {self.provider}")
        except Exception as e:
            # Graceful fallback on LLM errors
            return LLMAuditResult(
                summary=f"LLM audit unavailable: {str(e)}",
                recommendations=["Run additional static analysis tools like Slither or Mythril"],
                logic_vulnerabilities=[],
                best_practices=[],
                risk_assessment="UNKNOWN"
            )
    
    def _audit_with_openai(self, contract_code: str, contract_name: str) -> LLMAuditResult:
        """Perform audit using OpenAI API"""
        
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
            return self._parse_audit_response(response_text)
            
        except Exception as e:
            # Fallback: try without JSON mode
            return self._audit_with_openai_fallback(contract_code, contract_name)
    
    def _audit_with_openai_fallback(self, contract_code: str, contract_name: str) -> LLMAuditResult:
        """Fallback audit without JSON mode"""
        
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
            
            return LLMAuditResult(
                summary=summary,
                recommendations=["Conduct professional security audit for production deployment"],
                logic_vulnerabilities=[],
                best_practices=[],
                risk_assessment="MEDIUM"
            )
        except Exception as e:
            raise e
    
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
            return self._parse_audit_response(response_text)
            
        except Exception as e:
            raise e
    
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
