```python
import sqlite3
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from threading import Lock
import json


@dataclass
class EngagementEvent:
    event_id: str
    user_id: str
    event_type: str
    timestamp: float
    metadata: Dict[str, Any]


class EngagementStorage:
    """High-performance engagement event storage with time-based queries and retention policy."""
    
    def __init__(self, db_path: str = ":memory:", retention_days: int = 90):
        """
        Initialize the engagement storage layer.
        
        Args:
            db_path: Path to SQLite database file or ":memory:" for in-memory
            retention_days: Number of days to retain events (default 90)
        """
        self.db_path = db_path
        self.retention_days = retention_days
        self._lock = Lock()
        self._conn = None
        self._init_db()
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get or create database connection."""
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
        return self._conn
    
    def _init_db(self):
        """Initialize database schema with indexes for performance."""
        conn = self._get_connection()
        with self._lock:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS engagement_events (
                    event_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    timestamp REAL NOT NULL,
                    metadata TEXT NOT NULL
                )
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_timestamp 
                ON engagement_events(timestamp)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_user_timestamp 
                ON engagement_events(user_id, timestamp)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_event_type_timestamp 
                ON engagement_events(event_type, timestamp)
            """)
            
            conn.commit()
    
    def store_event(self, event: EngagementEvent) -> bool:
        """
        Store an engagement event with <1 second write latency.
        
        Args:
            event: EngagementEvent to store
            
        Returns:
            bool: True if stored successfully, False otherwise
        """
        try:
            conn = self._get_connection()
            with self._lock:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO engagement_events 
                    (event_id, user_id, event_type, timestamp, metadata)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    event.event_id,
                    event.user_id,
                    event.event_type,
                    event.timestamp,
                    json.dumps(event.metadata)
                ))
                conn.commit()
            return True
        except Exception as e:
            return False
    
    def store_events_batch(self, events: List[EngagementEvent]) -> int:
        """
        Store multiple events in a batch for high write volume.
        
        Args:
            events: List of EngagementEvent objects
            
        Returns:
            int: Number of events successfully stored
        """
        if not events:
            return 0
        
        try:
            conn = self._get_connection()
            with self._lock:
                cursor = conn.cursor()
                data = [
                    (e.event_id, e.user_id, e.event_type, e.timestamp, json.dumps(e.metadata))
                    for e in events
                ]
                cursor.executemany("""
                    INSERT OR REPLACE INTO engagement_events 
                    (event_id, user_id, event_type, timestamp, metadata)
                    VALUES (?, ?, ?, ?, ?)
                """, data)
                conn.commit()
            return len(events)
        except Exception as e:
            return 0
    
    def query_by_time_range(
        self,
        start_time: float,
        end_time: float,
        user_id: Optional[str] = None,
        event_type: Optional[str] = None
    ) -> List[EngagementEvent]:
        """
        Query events within a time range with <2 second response.
        
        Args:
            start_time: Start timestamp (inclusive)
            end_time: End timestamp (inclusive)
            user_id: Optional filter by user_id
            event_type: Optional filter by event_type
            
        Returns:
            List of EngagementEvent objects matching criteria
        """
        try:
            conn = self._get_connection()
            
            query = """
                SELECT event_id, user_id, event_type, timestamp, metadata
                FROM engagement_events
                WHERE timestamp >= ? AND timestamp <= ?
            """
            params = [start_time, end_time]
            
            if user_id is not None:
                query += " AND user_id = ?"
                params.append(user_id)
            
            if event_type is not None:
                query += " AND event_type = ?"
                params.append(event_type)
            
            query += " ORDER BY timestamp ASC"
            
            with self._lock:
                cursor = conn.cursor()
                cursor.execute(query, params)
                rows = cursor.fetchall()
            
            events = []
            for row in rows:
                events.append(EngagementEvent(
                    event_id=row['event_id'],
                    user_id=row['user_id'],
                    event_type=row['event_type'],
                    timestamp=row['timestamp'],
                    metadata=json.loads(row['metadata'])
                ))
            
            return events
        except Exception as e:
            return []
    
    def apply_retention_policy(self) -> int:
        """
        Apply data retention policy, removing events older than retention_days.
        
        Returns:
            int: Number of events deleted
        """
        try:
            cutoff_time = time.time() - (self.retention_days * 86400)
            conn = self._get_connection()
            
            with self._lock:
                cursor = conn.cursor()
                cursor.execute("""
                    DELETE FROM engagement_events
                    WHERE timestamp < ?
                """, (cutoff_time,))
                deleted_count = cursor.rowcount
                conn.commit()
            
            return deleted_count
        except Exception as e:
            return 0
    
    def get_event_count(self) -> int:
        """
        Get total number of events in storage.
        
        Returns:
            int: Total event count
        """
        try:
            conn = self._get_connection()
            with self._lock:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) as count FROM engagement_events")
                result = cursor.fetchone()
            return result['count'] if result else 0
        except Exception:
            return 0
    
    def clear_all_events(self):
        """Clear all events from storage (for testing purposes)."""
        try:
            conn = self._get_connection()
            with self._lock:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM engagement_events")
                conn.commit()
        except Exception:
            pass
    
    def close(self):
        """Close database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


def create_engagement_storage(
    db_path: str = ":memory:",
    retention_days: int = 90
) -> EngagementStorage:
    """
    Factory function to create an EngagementStorage instance.
    
    Args:
        db_path: Path to SQLite database file or ":memory:" for in-memory
        retention_days: Number of days to retain events
        
    Returns:
        EngagementStorage instance
    """
    return EngagementStorage(db_path=db_path, retention_days=retention_days)
```