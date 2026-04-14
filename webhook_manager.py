"""Webhook manager for authenticated, persistent integrations."""

import asyncio
import json
from typing import List, Optional, Dict, Any
from datetime import UTC, datetime

import httpx
from app_config import get_config
from database import create_audit_log, create_webhook_record, delete_webhook_record, list_webhook_records
from input_validator import validate_webhook_url
from logger_config import get_logger

logger = get_logger(__name__)
config = get_config()


class WebhookManager:
    """Manages webhook notifications for analysis events"""
    
    def __init__(self):
        self.timeout = 5.0  # 5 second timeout for webhook calls
    
    def register_webhook(
        self,
        url: str,
        events: List[str] = None,
        secret: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        user_id: Optional[int] = None,
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
        is_valid, error_message = validate_webhook_url(
            url,
            allow_private_networks=config.allow_private_webhooks,
        )
        if not is_valid:
            raise ValueError(error_message)

        webhook = create_webhook_record(
            user_id=user_id,
            url=url,
            events=events,
            secret=secret,
            headers=headers,
        )
        create_audit_log(
            action="webhook.registered",
            user_id=user_id,
            resource_type="webhook",
            resource_id=int(webhook["id"]),
            details={"url": url, "events": events or ["analysis.completed", "analysis.failed"]},
        )
        logger.info(f"Registered webhook {webhook['id']} for {url}")
        return webhook["id"]
    
    def unregister_webhook(self, webhook_id: str, user_id: Optional[int] = None) -> bool:
        """Unregister a webhook"""
        deleted = delete_webhook_record(webhook_id, user_id=user_id)
        if deleted:
            create_audit_log(
                action="webhook.unregistered",
                user_id=user_id,
                resource_type="webhook",
                resource_id=int(webhook_id),
            )
            logger.info(f"Unregistered webhook {webhook_id}")
        return deleted

    def list_webhooks(self, user_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """List persistent webhooks for the current user."""
        return list_webhook_records(user_id=user_id)
    
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

        is_valid, error_message = validate_webhook_url(
            webhook["url"],
            allow_private_networks=config.allow_private_webhooks,
        )
        if not is_valid:
            logger.warning("Blocked webhook delivery for %s: %s", webhook["url"], error_message)
            create_audit_log(
                action="webhook.delivery.blocked",
                resource_type="webhook",
                resource_id=int(webhook["id"]),
                user_id=webhook.get("user_id"),
                details={"event": event, "reason": error_message},
            )
            return False
        
        payload = {
            "event": event,
            "timestamp": datetime.now(UTC).isoformat(),
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
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=False) as client:
                response = await client.post(
                    webhook["url"],
                    json=payload,
                    headers=headers
                )
                response.raise_for_status()
                logger.info(f"Webhook {webhook['id']} triggered successfully: {event}")
                create_audit_log(
                    action="webhook.delivery.succeeded",
                    resource_type="webhook",
                    resource_id=int(webhook["id"]),
                    user_id=webhook.get("user_id"),
                    details={"event": event},
                )
                return True
        except Exception as e:
            logger.error(f"Webhook {webhook['id']} failed: {e}")
            create_audit_log(
                action="webhook.delivery.failed",
                resource_type="webhook",
                resource_id=int(webhook["id"]),
                user_id=webhook.get("user_id"),
                details={"event": event, "error": str(e)},
            )
            return False
    
    async def notify_analysis_completed(
        self,
        contract_name: str,
        analysis_result: Dict[str, Any],
        analysis_id: Optional[str] = None,
        user_id: Optional[int] = None,
    ):
        """Notify all webhooks that analysis completed"""
        if user_id is None:
            return

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
            for webhook in list_webhook_records(user_id=user_id, active_only=True, include_sensitive=True)
        ]
        
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            success_count = sum(1 for r in results if r is True)
            logger.info(f"Notified {success_count}/{len(tasks)} webhooks of analysis completion")
    
    async def notify_analysis_failed(
        self,
        contract_name: str,
        error: str,
        analysis_id: Optional[str] = None,
        user_id: Optional[int] = None,
    ):
        """Notify all webhooks that analysis failed"""
        if user_id is None:
            return

        data = {
            "analysis_id": analysis_id,
            "contract_name": contract_name,
            "error": error
        }
        
        tasks = [
            self.trigger_webhook("analysis.failed", data, webhook)
                    for webhook in list_webhook_records(user_id=user_id, active_only=True, include_sensitive=True)
        ]
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)


# Global webhook manager instance
webhook_manager = WebhookManager()
