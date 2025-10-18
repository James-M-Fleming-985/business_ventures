"""Alerting Service - Layer: Alerting

Triggers alerts based on thresholds and conditions.
"""

from typing import Dict, Any, List, Callable
from datetime import datetime
from pydantic import BaseModel
import logging
import asyncio

logger = logging.getLogger(__name__)


class Alert(BaseModel):
    """Represents an alert."""
    alert_id: str
    severity: str  # 'critical', 'warning', 'info'
    message: str
    source: str
    timestamp: str
    metadata: Dict[str, Any] = {}


class AlertRule(BaseModel):
    """Alert rule configuration."""
    rule_id: str
    name: str
    condition: str  # Description of condition
    threshold: float
    severity: str
    enabled: bool = True


class Alerting:
    """Manages alerting and notifications."""
    
    def __init__(self):
        """Initialize alerting service."""
        self.rules: Dict[str, AlertRule] = {}
        self.alerts: List[Alert] = []
        self.handlers: List[Callable] = []
        logger.info("Alerting service initialized")
    
    def register_rule(self, rule: AlertRule) -> None:
        """Register an alert rule.
        
        Args:
            rule: AlertRule configuration
        """
        self.rules[rule.rule_id] = rule
        logger.info(f"Alert rule registered: {rule.name}")
    
    def register_handler(self, handler: Callable) -> None:
        """Register alert handler (e.g., email, slack).
        
        Args:
            handler: Async function to handle alerts
        """
        self.handlers.append(handler)
        logger.info("Alert handler registered")
    
    async def trigger_alert(
        self,
        alert_id: str,
        severity: str,
        message: str,
        source: str,
        metadata: Dict[str, Any] = None
    ) -> Alert:
        """Trigger a new alert.
        
        Args:
            alert_id: Unique alert identifier
            severity: Alert severity level
            message: Alert message
            source: Source of the alert
            metadata: Additional context
            
        Returns:
            Created Alert object
        """
        alert = Alert(
            alert_id=alert_id,
            severity=severity,
            message=message,
            source=source,
            timestamp=datetime.utcnow().isoformat(),
            metadata=metadata or {}
        )
        
        self.alerts.append(alert)
        logger.warning(f"Alert triggered: {severity} - {message}")
        
        # Notify handlers
        await self._notify_handlers(alert)
        
        return alert
    
    async def _notify_handlers(self, alert: Alert) -> None:
        """Notify all registered handlers.
        
        Args:
            alert: Alert to send to handlers
        """
        tasks = [handler(alert) for handler in self.handlers]
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def check_threshold(
        self,
        rule_id: str,
        current_value: float
    ) -> bool:
        """Check if value exceeds rule threshold.
        
        Args:
            rule_id: ID of rule to check
            current_value: Current metric value
            
        Returns:
            True if threshold exceeded
        """
        if rule_id not in self.rules:
            logger.error(f"Rule not found: {rule_id}")
            return False
        
        rule = self.rules[rule_id]
        if not rule.enabled:
            return False
        
        if current_value > rule.threshold:
            await self.trigger_alert(
                alert_id=f"{rule_id}_{datetime.utcnow().timestamp()}",
                severity=rule.severity,
                message=f"{rule.name}: {current_value} > {rule.threshold}",
                source=rule_id,
                metadata={'value': current_value, 'threshold': rule.threshold}
            )
            return True
        
        return False
    
    async def get_active_alerts(
        self,
        severity: str = None,
        limit: int = 100
    ) -> List[Alert]:
        """Get recent alerts.
        
        Args:
            severity: Filter by severity
            limit: Maximum number of alerts
            
        Returns:
            List of recent alerts
        """
        alerts = self.alerts[-limit:]
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        return alerts
    
    def clear_alerts(self) -> int:
        """Clear all alerts.
        
        Returns:
            Number of alerts cleared
        """
        count = len(self.alerts)
        self.alerts.clear()
        logger.info(f"Cleared {count} alerts")
        return count
