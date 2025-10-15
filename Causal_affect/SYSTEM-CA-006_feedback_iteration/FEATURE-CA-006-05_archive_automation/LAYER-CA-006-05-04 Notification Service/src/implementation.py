```python
import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json
import aiohttp


class NotificationChannel(Enum):
    """Supported notification channels."""
    EMAIL = "email"
    SLACK = "slack"


class WorkflowEventType(Enum):
    """Types of workflow events that trigger notifications."""
    ARCHIVE_STARTED = "archive_started"
    ARCHIVE_COMPLETED = "archive_completed"
    ARCHIVE_FAILED = "archive_failed"
    ROLLBACK_REQUIRED = "rollback_required"
    ROLLBACK_COMPLETED = "rollback_completed"


@dataclass
class RollbackInstructions:
    """Complete rollback instructions for a workflow event."""
    steps: List[str] = field(default_factory=list)
    prerequisites: List[str] = field(default_factory=list)
    verification_steps: List[str] = field(default_factory=list)
    estimated_time: str = ""
    risk_level: str = "medium"
    contact_info: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert rollback instructions to dictionary."""
        return {
            "steps": self.steps,
            "prerequisites": self.prerequisites,
            "verification_steps": self.verification_steps,
            "estimated_time": self.estimated_time,
            "risk_level": self.risk_level,
            "contact_info": self.contact_info
        }
    
    def to_text(self) -> str:
        """Convert rollback instructions to formatted text."""
        text = "=== ROLLBACK INSTRUCTIONS ===\n\n"
        
        if self.prerequisites:
            text += "Prerequisites:\n"
            for i, prereq in enumerate(self.prerequisites, 1):
                text += f"{i}. {prereq}\n"
            text += "\n"
        
        text += "Steps:\n"
        for i, step in enumerate(self.steps, 1):
            text += f"{i}. {step}\n"
        text += "\n"
        
        if self.verification_steps:
            text += "Verification Steps:\n"
            for i, step in enumerate(self.verification_steps, 1):
                text += f"{i}. {step}\n"
            text += "\n"
        
        if self.estimated_time:
            text += f"Estimated Time: {self.estimated_time}\n"
        if self.risk_level:
            text += f"Risk Level: {self.risk_level}\n"
        if self.contact_info:
            text += f"Contact: {self.contact_info}\n"
        
        return text


@dataclass
class WorkflowEvent:
    """Represents a workflow event that triggers notifications."""
    event_type: WorkflowEventType
    timestamp: datetime
    workflow_id: str
    details: Dict[str, Any] = field(default_factory=dict)
    rollback_instructions: Optional[RollbackInstructions] = None


@dataclass
class Notification:
    """Represents a notification to be sent."""
    event: WorkflowEvent
    channels: List[NotificationChannel]
    recipients: List[str]
    subject: str = ""
    message: str = ""
    sent_at: Optional[datetime] = None
    status: str = "pending"


class EmailSender:
    """Handles sending email notifications."""
    
    def __init__(self, smtp_host: str = "localhost", smtp_port: int = 587,
                 username: Optional[str] = None, password: Optional[str] = None,
                 from_address: str = "noreply@example.com"):
        """Initialize email sender with SMTP configuration."""
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.from_address = from_address
    
    async def send(self, recipients: List[str], subject: str, message: str) -> bool:
        """Send email notification."""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.from_address
            msg['To'] = ', '.join(recipients)
            msg['Subject'] = subject
            
            msg.attach(MIMEText(message, 'plain'))
            
            # Run in executor to avoid blocking
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._send_smtp, msg, recipients)
            return True
        except Exception as e:
            print(f"Failed to send email: {e}")
            return False
    
    def _send_smtp(self, msg: MIMEMultipart, recipients: List[str]):
        """Send email via SMTP (blocking operation)."""
        with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
            if self.username and self.password:
                server.starttls()
                server.login(self.username, self.password)
            server.send_message(msg)


class SlackSender:
    """Handles sending Slack notifications."""
    
    def __init__(self, webhook_url: Optional[str] = None, token: Optional[str] = None):
        """Initialize Slack sender with webhook URL or token."""
        self.webhook_url = webhook_url
        self.token = token
    
    async def send(self, channels: List[str], message: str, subject: Optional[str] = None) -> bool:
        """Send Slack notification."""
        try:
            if self.webhook_url:
                return await self._send_webhook(message, subject)
            elif self.token:
                return await self._send_api(channels, message, subject)
            else:
                print("No Slack webhook URL or token configured")
                return False
        except Exception as e:
            print(f"Failed to send Slack message: {e}")
            return False
    
    async def _send_webhook(self, message: str, subject: Optional[str] = None) -> bool:
        """Send message via Slack webhook."""
        text = f"*{subject}*\n\n{message}" if subject else message
        payload = {"text": text}
        
        async with aiohttp.ClientSession() as session:
            async with session.post(self.webhook_url, json=payload) as response:
                return response.status == 200
    
    async def _send_api(self, channels: List[str], message: str, subject: Optional[str] = None) -> bool:
        """Send message via Slack API."""
        text = f"*{subject}*\n\n{message}" if subject else message
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        
        success = True
        async with aiohttp.ClientSession() as session:
            for channel in channels:
                payload = {
                    "channel": channel,
                    "text": text
                }
                async with session.post("https://slack.com/api/chat.postMessage",
                                       headers=headers, json=payload) as response:
                    if response.status != 200:
                        success = False
        
        return success


class NotificationService:
    """
    Service for sending notifications about workflow events.
    
    Sends notifications within 2 minutes of workflow events,
    includes complete rollback instructions, and supports email and Slack channels.
    """
    
    def __init__(self, email_config: Optional[Dict[str, Any]] = None,
                 slack_config: Optional[Dict[str, Any]] = None):
        """
        Initialize notification service.
        
        Args:
            email_config: Configuration for email notifications
            slack_config: Configuration for Slack notifications
        """
        self.email_sender = EmailSender(**(email_config or {}))
        self.slack_sender = SlackSender(**(slack_config or {}))
        self.notification_queue: asyncio.Queue = asyncio.Queue()
        self.pending_notifications: List[Notification] = []
        self.sent_notifications: List[Notification] = []
        self._processing_task: Optional[asyncio.Task] = None
        self._running = False
    
    def start(self):
        """Start the notification service."""
        if not self._running:
            self._running = True
            self._processing_task = asyncio.create_task(self._process_notifications())
    
    async def stop(self):
        """Stop the notification service."""
        self._running = False
        if self._processing_task:
            await self._processing_task
    
    async def notify(self, event: WorkflowEvent, channels: List[NotificationChannel],
                    recipients: List[str]) -> Notification:
        """
        Send notification about a workflow event.
        
        Args:
            event: The workflow event to notify about
            channels: List of channels to send notification to
            recipients: List of recipient addresses/identifiers
        
        Returns:
            Notification object with sending status
        """
        notification = self._create_notification(event, channels, recipients)
        self.pending_notifications.append(notification)
        await self.notification_queue.put(notification)
        return notification
    
    def _create_notification(self, event: WorkflowEvent,
                           channels: List[NotificationChannel],
                           recipients: List[str]) -> Notification:
        """Create a notification from a workflow event."""
        subject = self._generate_subject(event)
        message = self._generate_message(event)
        
        return Notification(
            event=event,
            channels=channels,
            recipients=recipients,
            subject=subject,
            message=message
        )
    
    def _generate_subject(self, event: WorkflowEvent) -> str:
        """Generate notification subject from event."""
        event_titles = {
            WorkflowEventType.ARCHIVE_STARTED: "Archive Workflow Started",
            WorkflowEventType.ARCHIVE_COMPLETED: "Archive Workflow Completed",
            WorkflowEventType.ARCHIVE_FAILED: "Archive Workflow Failed",
            WorkflowEventType.ROLLBACK_REQUIRED: "Rollback Required",
            WorkflowEventType.ROLLBACK_COMPLETED: "Rollback Completed"
        }
        
        title = event_titles.get(event.event_type, "Workflow Event")
        return f"{title} - Workflow {event.workflow_id}"
    
    def _generate_message(self, event: WorkflowEvent) -> str:
        """Generate notification message from event."""
        message = f"Workflow Event: {event.event_type.value}\n"
        message += f"Workflow ID: {event.workflow_id}\n"
        message += f"Timestamp: {event.timestamp.isoformat()}\n\n"
        
        if event.details:
            message += "Details:\n"
            for key, value in event.details.items():
                message += f"  {key}: {value}\n"
            message += "\n"
        
        if event.rollback_instructions:
            message += event.rollback_instructions.to_text()
        
        return message
    
    async def _process_notifications(self):
        """Process notifications from the queue."""
        while self._running:
            try:
                notification = await asyncio.wait_for(
                    self.notification_queue.get(),
                    timeout=0.1
                )
                await self._send_notification(notification)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                print(f"Error processing notification: {e}")
    
    async def _send_notification(self, notification: Notification):
        """Send a notification through configured channels."""
        # Check if notification should be sent within 2 minutes
        time_elapsed = datetime.now() - notification.event.timestamp
        if time_elapsed > timedelta(minutes=2):
            notification.status = "expired"
            return
        
        success = True
        
        if NotificationChannel.EMAIL in notification.channels:
            email_success = await self.email_sender.send(
                notification.recipients,
                notification.subject,
                notification.message
            )
            success = success and email_success
        
        if NotificationChannel.SLACK in notification.channels:
            slack_success = await self.slack_sender.send(
                notification.recipients,
                notification.message,
                notification.subject
            )
            success = success and slack_success
        
        notification.sent_at = datetime.now()
        notification.status = "sent" if success else "failed"
        
        if notification in self.pending_notifications:
            self.pending_notifications.remove(notification)
        self.sent_notifications.append(notification)
    
    def get_notification_status(self, workflow_id: str) -> List[Dict[str, Any]]:
        """Get status of all notifications for a workflow."""
        statuses = []
        
        all_notifications = self.pending_notifications + self.sent_notifications
        for notification in all_notifications:
            if notification.event.workflow_id == workflow_id:
                statuses.append({
                    "event_type": notification.event.event_type.value,
                    "status": notification.status,
                    "sent_at": notification.sent_at.isoformat() if notification.sent_at else None,
                    "channels": [ch.value for ch in notification.channels],
                    "recipients": notification.recipients
                })
        
        return statuses
    
    def is_sent_within_time_limit(self, notification: Notification,
                                  time_limit_minutes: int = 2) -> bool:
        """
        Check if notification was sent within time limit.
        
        Args:
            notification: Notification to check
            time_limit_minutes: Maximum time allowed in minutes
        
        Returns:
            True if sent within time limit, False otherwise
        """
        if not notification.sent_at:
            return False
        
        time_diff = notification.sent_at - notification.event.timestamp
        return time_diff <= timedelta(minutes=time_limit_minutes)
    
    def has_rollback_instructions(self, notification: Notification) -> bool:
        """Check if notification includes rollback instructions."""
        return notification.event.rollback_instructions is not None
    
    def validate_rollback_instructions(self, instructions: RollbackInstructions) -> bool:
        """
        Validate that rollback instructions are complete.
        
        Args:
            instructions: Rollback instructions to validate
        
        Returns:
            True if instructions are complete, False otherwise
        """
        return (
            len(instructions.steps) > 0 and
            len(instructions.verification_steps) > 0 and
            bool(instructions.estimated_time) and
            bool(instructions.risk_level)
        )


async def create_notification_service(email_config: Optional[Dict[str, Any]] = None,
                                     slack_config: Optional[Dict[str, Any]] = None) -> NotificationService:
    """
    Create and start a notification service.
    
    Args:
        email_config: Configuration for email notifications
        slack_config: Configuration for Slack notifications
    
    Returns:
        Started NotificationService instance
    """
    service = NotificationService(email_config, slack_config)
    service.start()
    return service
```