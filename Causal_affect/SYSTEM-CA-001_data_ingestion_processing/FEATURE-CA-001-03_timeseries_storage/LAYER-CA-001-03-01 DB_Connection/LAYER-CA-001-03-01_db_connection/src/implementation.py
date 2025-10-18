```python
"""Database connection module with connection pooling and transaction support."""

import sqlite3
import threading
from contextlib import contextmanager
from typing import Optional, Dict, Any, List, Tuple
import logging

logger = logging.getLogger(__name__)


class DatabaseConnectionError(Exception):
    """Raised when database connection errors occur."""
    pass


class DatabaseConnection:
    """Manages database connections with pooling and transaction support."""
    
    def __init__(self, db_path: str = ":memory:", pool_size: int = 5):
        """
        Initialize database connection manager.
        
        Args:
            db_path: Path to the database file or :memory: for in-memory database
            pool_size: Maximum number of connections in the pool
        """
        self.db_path = db_path
        self.pool_size = pool_size
        self._connections = []
        self._available_connections = []
        self._lock = threading.Lock()
        self._closed = False
        self._transaction_active = False
        self._current_connection = None
        
        # Initialize connection pool
        self._initialize_pool()
    
    def _initialize_pool(self):
        """Initialize the connection pool."""
        try:
            for _ in range(self.pool_size):
                conn = sqlite3.connect(self.db_path, check_same_thread=False)
                conn.row_factory = sqlite3.Row
                self._connections.append(conn)
                self._available_connections.append(conn)
        except sqlite3.Error as e:
            raise DatabaseConnectionError(f"Failed to initialize connection pool: {e}")
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get a connection from the pool."""
        with self._lock:
            if self._closed:
                raise DatabaseConnectionError("Connection pool is closed")
            
            if self._transaction_active and self._current_connection:
                return self._current_connection
            
            if not self._available_connections:
                # Pool exhausted, create a new connection temporarily
                conn = sqlite3.connect(self.db_path, check_same_thread=False)
                conn.row_factory = sqlite3.Row
                return conn
            
            return self._available_connections.pop()
    
    def _return_connection(self, conn: sqlite3.Connection):
        """Return a connection to the pool."""
        with self._lock:
            if conn in self._connections and conn not in self._available_connections:
                self._available_connections.append(conn)
    
    def execute(self, query: str, params: Optional[Tuple] = None) -> List[Dict[str, Any]]:
        """
        Execute a query and return results.
        
        Args:
            query: SQL query to execute
            params: Query parameters
            
        Returns:
            List of dictionaries representing rows
        """
        if self._closed:
            raise DatabaseConnectionError("Connection pool is closed")
        
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            # Handle different query types
            if query.strip().upper().startswith(('SELECT', 'PRAGMA')):
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
            else:
                # For INSERT, UPDATE, DELETE
                if not self._transaction_active:
                    conn.commit()
                return []
                
        except sqlite3.Error as e:
            if conn and not self._transaction_active:
                conn.rollback()
            raise DatabaseConnectionError(f"Query execution failed: {e}")
        finally:
            if not self._transaction_active and conn:
                self._return_connection(conn)
    
    def executemany(self, query: str, params_list: List[Tuple]) -> None:
        """
        Execute a query multiple times with different parameters.
        
        Args:
            query: SQL query to execute
            params_list: List of parameter tuples
        """
        if self._closed:
            raise DatabaseConnectionError("Connection pool is closed")
        
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.executemany(query, params_list)
            
            if not self._transaction_active:
                conn.commit()
                
        except sqlite3.Error as e:
            if conn and not self._transaction_active:
                conn.rollback()
            raise DatabaseConnectionError(f"Batch execution failed: {e}")
        finally:
            if not self._transaction_active and conn:
                self._return_connection(conn)
    
    @contextmanager
    def transaction(self):
        """
        Context manager for database transactions.
        
        Usage:
            with db.transaction():
                db.execute("INSERT INTO users (name) VALUES (?)", ("Alice",))
                db.execute("UPDATE users SET active = 1 WHERE name = ?", ("Alice",))
        """
        if self._closed:
            raise DatabaseConnectionError("Connection pool is closed")
        
        if self._transaction_active:
            raise DatabaseConnectionError("Transaction already active")
        
        conn = None
        try:
            conn = self._get_connection()
            self._current_connection = conn
            self._transaction_active = True
            
            # Begin transaction
            conn.execute("BEGIN")
            
            yield self
            
            # Commit transaction
            conn.commit()
            
        except Exception as e:
            # Rollback on any error
            if conn:
                try:
                    conn.rollback()
                except:
                    pass
            raise DatabaseConnectionError(f"Transaction failed: {e}")
        finally:
            self._transaction_active = False
            self._current_connection = None
            if conn:
                self._return_connection(conn)
    
    def close(self):
        """Close all connections in the pool."""
        with self._lock:
            if self._closed:
                return
            
            self._closed = True
            
            for conn in self._connections:
                try:
                    conn.close()
                except:
                    pass
            
            self._connections.clear()
            self._available_connections.clear()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
    
    def create_table(self, table_name: str, schema: str):
        """
        Create a table with the given schema.
        
        Args:
            table_name: Name of the table to create
            schema: Table schema definition
        """
        query = f"CREATE TABLE IF NOT EXISTS {table_name} ({schema})"
        self.execute(query)
    
    def table_exists(self, table_name: str) -> bool:
        """
        Check if a table exists.
        
        Args:
            table_name: Name of the table to check
            
        Returns:
            True if table exists, False otherwise
        """
        query = "SELECT name FROM sqlite_master WHERE type='table' AND name=?"
        result = self.execute(query, (table_name,))
        return len(result) > 0
```