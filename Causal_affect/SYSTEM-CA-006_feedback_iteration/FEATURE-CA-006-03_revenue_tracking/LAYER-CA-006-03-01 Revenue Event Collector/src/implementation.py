```python
import hashlib
import hmac
import json
import time
from typing import Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass, field
from collections import defaultdict
import threading


@dataclass
class RevenueEvent:
    event_id: str
    event_type: str
    amount: float
    currency: str
    customer_id: str
    timestamp: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    idempotency_key: Optional[str] = None


class EventQueue:
    """Thread-safe event queue with latency tracking."""
    
    def __init__(self):
        self._queue = []
        self._lock = threading.Lock()
        self._processed_idempotency_keys = set()
        self._idempotency_lock = threading.Lock()
    
    def add(self, event: RevenueEvent) -> bool:
        """Add event to queue. Returns False if duplicate idempotency key."""
        if event.idempotency_key:
            with self._idempotency_lock:
                if event.idempotency_key in self._processed_idempotency_keys:
                    return False
                self._processed_idempotency_keys.add(event.idempotency_key)
        
        with self._lock:
            self._queue.append(event)
        return True
    
    def get_all(self):
        """Get all events from queue."""
        with self._lock:
            return list(self._queue)
    
    def clear(self):
        """Clear the queue."""
        with self._lock:
            self._queue.clear()
    
    def size(self) -> int:
        """Get queue size."""
        with self._lock:
            return len(self._queue)


class RevenueEventCollector:
    """Collects and processes revenue events from Stripe webhooks."""
    
    def __init__(self, webhook_secret: str):
        """
        Initialize the revenue event collector.
        
        Args:
            webhook_secret: Stripe webhook signing secret
        """
        self.webhook_secret = webhook_secret
        self.event_queue = EventQueue()
        self._latency_measurements = []
    
    def validate_webhook_signature(
        self,
        payload: bytes,
        signature_header: str,
        timestamp_tolerance: int = 300
    ) -> bool:
        """
        Validate Stripe webhook signature.
        
        Args:
            payload: Raw webhook payload bytes
            signature_header: Stripe-Signature header value
            timestamp_tolerance: Maximum age of webhook in seconds
        
        Returns:
            True if signature is valid, False otherwise
        """
        try:
            # Parse signature header
            sig_parts = {}
            for part in signature_header.split(','):
                key_value = part.strip().split('=', 1)
                if len(key_value) == 2:
                    sig_parts[key_value[0]] = key_value[1]
            
            if 't' not in sig_parts or 'v1' not in sig_parts:
                return False
            
            timestamp = int(sig_parts['t'])
            signature = sig_parts['v1']
            
            # Check timestamp tolerance
            current_time = int(time.time())
            if abs(current_time - timestamp) > timestamp_tolerance:
                return False
            
            # Compute expected signature
            signed_payload = f"{timestamp}.{payload.decode('utf-8')}"
            expected_signature = hmac.new(
                self.webhook_secret.encode('utf-8'),
                signed_payload.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            # Compare signatures
            return hmac.compare_digest(expected_signature, signature)
        
        except (ValueError, KeyError, AttributeError):
            return False
    
    def extract_transaction_details(self, webhook_payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Extract transaction details from webhook payload.
        
        Args:
            webhook_payload: Parsed webhook JSON payload
        
        Returns:
            Dictionary with transaction details or None if extraction fails
        """
        try:
            event_type = webhook_payload.get('type')
            event_id = webhook_payload.get('id')
            
            if not event_type or not event_id:
                return None
            
            data = webhook_payload.get('data', {})
            obj = data.get('object', {})
            
            # Extract common fields
            details = {
                'event_id': event_id,
                'event_type': event_type,
                'timestamp': webhook_payload.get('created', time.time())
            }
            
            # Extract amount and currency
            if 'amount' in obj:
                details['amount'] = obj['amount'] / 100.0  # Convert from cents
            elif 'amount_total' in obj:
                details['amount'] = obj['amount_total'] / 100.0
            else:
                details['amount'] = 0.0
            
            details['currency'] = obj.get('currency', 'usd')
            
            # Extract customer ID
            details['customer_id'] = obj.get('customer', obj.get('customer_id', ''))
            
            # Extract metadata
            details['metadata'] = obj.get('metadata', {})
            
            return details
        
        except (KeyError, TypeError, AttributeError):
            return None
    
    def process_webhook(
        self,
        payload: bytes,
        signature_header: str,
        idempotency_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a Stripe webhook event.
        
        Args:
            payload: Raw webhook payload bytes
            signature_header: Stripe-Signature header value
            idempotency_key: Optional idempotency key for duplicate detection
        
        Returns:
            Dictionary with processing result
        """
        start_time = time.time()
        
        # Validate signature
        if not self.validate_webhook_signature(payload, signature_header):
            return {
                'success': False,
                'error': 'Invalid signature'
            }
        
        # Parse payload
        try:
            webhook_payload = json.loads(payload.decode('utf-8'))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return {
                'success': False,
                'error': 'Invalid JSON payload'
            }
        
        # Extract transaction details
        details = self.extract_transaction_details(webhook_payload)
        if not details:
            return {
                'success': False,
                'error': 'Failed to extract transaction details'
            }
        
        # Create revenue event
        event = RevenueEvent(
            event_id=details['event_id'],
            event_type=details['event_type'],
            amount=details['amount'],
            currency=details['currency'],
            customer_id=details['customer_id'],
            timestamp=details['timestamp'],
            metadata=details['metadata'],
            idempotency_key=idempotency_key
        )
        
        # Add to queue (handle duplicates)
        added = self.event_queue.add(event)
        
        # Measure latency
        latency = time.time() - start_time
        self._latency_measurements.append(latency)
        
        if not added:
            return {
                'success': False,
                'error': 'Duplicate event',
                'latency': latency
            }
        
        return {
            'success': True,
            'event_id': event.event_id,
            'latency': latency
        }
    
    def get_queued_events(self):
        """Get all queued events."""
        return self.event_queue.get_all()
    
    def get_average_latency(self) -> float:
        """Get average processing latency."""
        if not self._latency_measurements:
            return 0.0
        return sum(self._latency_measurements) / len(self._latency_measurements)
    
    def clear_queue(self):
        """Clear the event queue."""
        self.event_queue.clear()


def create_collector(webhook_secret: str) -> RevenueEventCollector:
    """
    Factory function to create a RevenueEventCollector instance.
    
    Args:
        webhook_secret: Stripe webhook signing secret
    
    Returns:
        RevenueEventCollector instance
    """
    return RevenueEventCollector(webhook_secret)
```