"""
Webhook Manager - Send notifications when analysis completes
Supports custom webhooks for CI/CD integration, Slack, Discord, etc.
"""

import asyncio
import json
from typing import List, Optional, Dict, Any
from datetime import datetime
import httpx
from app_config import get_config
from logger_config import get_logger

logger = get_logger(__name__)
config = get_config()


class WebhookManager:
    """Manages webhook notifications for analysis events"""
    
    def __init__(self):
        self.webhooks: List[Dict[str, Any]] = []
        self.timeout = 5.0  # 5 second timeout for webhook calls
    
    def register_webhook(
        self,
        url: str,
        events: List[str] = None,
        secret: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Register a webhook URL
        
        Args:
            url: Webhook URL to call
            events: List of events to subscribe to (default: all)
            secret: Optional secret for HMAC signing
            headers: Optional custom headers
            
        Returns:
            Webhook ID
        """
        import uuid
        webhook_id = str(uuid.uuid4())
        
        webhook = {
            "id": webhook_id,
            "url": url,
            "events": events or ["analysis.completed", "analysis.failed"],
            "secret": secret,
            "headers": headers or {},
            "created_at": datetime.utcnow().isoformat(),
            "active": True
        }
        
        self.webhooks.append(webhook)
        logger.info(f"Registered webhook {webhook_id} for {url}")
        return webhook_id
    
    def unregister_webhook(self, webhook_id: str) -> bool:
        """Unregister a webhook"""
        for i, webhook in enumerate(self.webhooks):
            if webhook["id"] == webhook_id:
                self.webhooks.pop(i)
                logger.info(f"Unregistered webhook {webhook_id}")
                return True
        return False
    
    async def trigger_webhook(
        self,
        event: str,
        data: Dict[str, Any],
        webhook: Dict[str, Any]
    ) -> bool:
        """
        Trigger a single webhook
        
        Args:
            event: Event name (e.g., "analysis.completed")
            data: Event data payload
            webhook: Webhook configuration
            
        Returns:
            True if successful, False otherwise
        """
        if event not in webhook["events"]:
            return False
        
        if not webhook["active"]:
            return False
        
        payload = {
            "event": event,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data
        }
        
        # Add HMAC signature if secret provided
        if webhook.get("secret"):
            import hmac
            import hashlib
            payload_str = json.dumps(payload, sort_keys=True)
            signature = hmac.new(
                webhook["secret"].encode(),
                payload_str.encode(),
                hashlib.sha256
            ).hexdigest()
            payload["signature"] = signature
        
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Solidity-Vuln-Scanner/1.0.0",
            **webhook.get("headers", {})
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    webhook["url"],
                    json=payload,
                    headers=headers
                )
                response.raise_for_status()
                logger.info(f"Webhook {webhook['id']} triggered successfully: {event}")
                return True
        except Exception as e:
            logger.error(f"Webhook {webhook['id']} failed: {e}")
            return False
    
    async def notify_analysis_completed(
        self,
        contract_name: str,
        analysis_result: Dict[str, Any],
        analysis_id: Optional[str] = None
    ):
        """Notify all webhooks that analysis completed"""
        data = {
            "analysis_id": analysis_id,
            "contract_name": contract_name,
            "risk_score": analysis_result.get("risk_score", 0),
            "severity": analysis_result.get("severity", "UNKNOWN"),
            "vulnerability_count": len(analysis_result.get("vulnerabilities", [])),
            "analysis_time_ms": analysis_result.get("analysis_time_ms", 0)
        }
        
        tasks = [
            self.trigger_webhook("analysis.completed", data, webhook)
            for webhook in self.webhooks
        ]
        
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            success_count = sum(1 for r in results if r is True)
            logger.info(f"Notified {success_count}/{len(tasks)} webhooks of analysis completion")
    
    async def notify_analysis_failed(
        self,
        contract_name: str,
        error: str,
        analysis_id: Optional[str] = None
    ):
        """Notify all webhooks that analysis failed"""
        data = {
            "analysis_id": analysis_id,
            "contract_name": contract_name,
            "error": error
        }
        
        tasks = [
            self.trigger_webhook("analysis.failed", data, webhook)
            for webhook in self.webhooks
        ]
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)


# Global webhook manager instance
webhook_manager = WebhookManager()
