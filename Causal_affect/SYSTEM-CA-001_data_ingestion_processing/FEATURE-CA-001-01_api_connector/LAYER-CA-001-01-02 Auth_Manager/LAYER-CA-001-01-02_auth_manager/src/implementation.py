```python
import time
import json
import base64
from datetime import datetime, timedelta
from typing import Dict, Optional, Any
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import os
import threading
import requests


class AuthManager:
    """Manages authentication for API connections with automatic token refresh and encryption."""
    
    def __init__(self, db_connection: Any, encryption_key: Optional[str] = None):
        """
        Initialize AuthManager with database connection and encryption.
        
        Args:
            db_connection: Database connection object
            encryption_key: Optional encryption key, generates new one if not provided
        """
        self.db = db_connection
        self._setup_encryption(encryption_key)
        self._refresh_thread = None
        self._refresh_lock = threading.Lock()
        self._token_cache = {}
        self._stop_refresh = False
        
    def _setup_encryption(self, encryption_key: Optional[str] = None):
        """Setup encryption for credentials."""
        if encryption_key:
            self.cipher = Fernet(encryption_key.encode() if isinstance(encryption_key, str) else encryption_key)
        else:
            key = Fernet.generate_key()
            self.cipher = Fernet(key)
            
    def store_credentials(self, service_name: str, credentials: Dict[str, Any]) -> None:
        """
        Store encrypted credentials in database.
        
        Args:
            service_name: Name of the service
            credentials: Dictionary containing credentials
        """
        encrypted_creds = self.cipher.encrypt(json.dumps(credentials).encode())
        
        # Store in database
        cursor = self.db.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO auth_credentials 
            (service_name, encrypted_credentials, created_at, updated_at) 
            VALUES (?, ?, ?, ?)
        """, (service_name, encrypted_creds, datetime.now(), datetime.now()))
        self.db.commit()
        
    def get_credentials(self, service_name: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve and decrypt credentials from database.
        
        Args:
            service_name: Name of the service
            
        Returns:
            Decrypted credentials dictionary or None
        """
        cursor = self.db.cursor()
        cursor.execute(
            "SELECT encrypted_credentials FROM auth_credentials WHERE service_name = ?",
            (service_name,)
        )
        result = cursor.fetchone()
        
        if result:
            encrypted_creds = result[0]
            decrypted = self.cipher.decrypt(encrypted_creds)
            return json.loads(decrypted.decode())
        return None
        
    def setup_oauth2(self, service_name: str, client_id: str, client_secret: str,
                     token_url: str, refresh_threshold: int = 300) -> None:
        """
        Setup OAuth2 authentication with automatic refresh.
        
        Args:
            service_name: Name of the service
            client_id: OAuth2 client ID
            client_secret: OAuth2 client secret
            token_url: Token endpoint URL
            refresh_threshold: Seconds before expiry to refresh token (default: 300)
        """
        credentials = {
            'type': 'oauth2',
            'client_id': client_id,
            'client_secret': client_secret,
            'token_url': token_url,
            'refresh_threshold': refresh_threshold
        }
        
        self.store_credentials(service_name, credentials)
        
        # Get initial token
        self._get_oauth2_token(service_name)
        
        # Start refresh thread
        self._start_refresh_thread(service_name)
        
    def _get_oauth2_token(self, service_name: str) -> Dict[str, Any]:
        """Get OAuth2 token using client credentials."""
        creds = self.get_credentials(service_name)
        if not creds or creds.get('type') != 'oauth2':
            raise ValueError(f"OAuth2 credentials not found for {service_name}")
            
        response = requests.post(
            creds['token_url'],
            data={
                'grant_type': 'client_credentials',
                'client_id': creds['client_id'],
                'client_secret': creds['client_secret']
            }
        )
        response.raise_for_status()
        
        token_data = response.json()
        token_data['expires_at'] = datetime.now() + timedelta(seconds=token_data.get('expires_in', 3600))
        
        # Cache token
        self._token_cache[service_name] = token_data
        
        return token_data
        
    def _refresh_oauth2_token(self, service_name: str) -> None:
        """Refresh OAuth2 token before expiry."""
        with self._refresh_lock:
            creds = self.get_credentials(service_name)
            if not creds:
                return
                
            token_data = self._token_cache.get(service_name, {})
            expires_at = token_data.get('expires_at')
            
            if not expires_at:
                self._get_oauth2_token(service_name)
                return
                
            # Check if refresh needed
            refresh_threshold = creds.get('refresh_threshold', 300)
            if datetime.now() >= expires_at - timedelta(seconds=refresh_threshold):
                self._get_oauth2_token(service_name)
                
    def _start_refresh_thread(self, service_name: str) -> None:
        """Start background thread for token refresh."""
        def refresh_loop():
            while not self._stop_refresh:
                try:
                    self._refresh_oauth2_token(service_name)
                except Exception:
                    pass
                time.sleep(60)  # Check every minute
                
        self._refresh_thread = threading.Thread(target=refresh_loop, daemon=True)
        self._refresh_thread.start()
        
    def setup_api_key(self, service_name: str, api_key: str, 
                      location: str = 'header', key_name: str = 'X-API-Key') -> None:
        """
        Setup API key authentication.
        
        Args:
            service_name: Name of the service
            api_key: API key value
            location: Where to inject key ('header' or 'query')
            key_name: Name of the key parameter
        """
        credentials = {
            'type': 'api_key',
            'api_key': api_key,
            'location': location,
            'key_name': key_name
        }
        
        self.store_credentials(service_name, credentials)
        
    def get_auth_headers(self, service_name: str) -> Dict[str, str]:
        """
        Get authentication headers for a service.
        
        Args:
            service_name: Name of the service
            
        Returns:
            Dictionary of headers to include in requests
        """
        creds = self.get_credentials(service_name)
        if not creds:
            return {}
            
        headers = {}
        
        if creds.get('type') == 'oauth2':
            # Get current token
            token_data = self._token_cache.get(service_name)
            if not token_data or datetime.now() >= token_data.get('expires_at', datetime.min):
                token_data = self._get_oauth2_token(service_name)
                
            headers['Authorization'] = f"Bearer {token_data['access_token']}"
            
        elif creds.get('type') == 'api_key' and creds.get('location') == 'header':
            headers[creds['key_name']] = creds['api_key']
            
        return headers
        
    def get_auth_params(self, service_name: str) -> Dict[str, str]:
        """
        Get authentication query parameters for a service.
        
        Args:
            service_name: Name of the service
            
        Returns:
            Dictionary of query parameters to include in requests
        """
        creds = self.get_credentials(service_name)
        if not creds:
            return {}
            
        params = {}
        
        if creds.get('type') == 'api_key' and creds.get('location') == 'query':
            params[creds['key_name']] = creds['api_key']
            
        return params
        
    def make_authenticated_request(self, service_name: str, method: str, url: str, **kwargs) -> requests.Response:
        """
        Make an authenticated HTTP request.
        
        Args:
            service_name: Name of the service
            method: HTTP method
            url: Request URL
            **kwargs: Additional arguments for requests
            
        Returns:
            Response object
        """
        # Add authentication
        headers = kwargs.get('headers', {})
        headers.update(self.get_auth_headers(service_name))
        kwargs['headers'] = headers
        
        params = kwargs.get('params', {})
        params.update(self.get_auth_params(service_name))
        kwargs['params'] = params
        
        # Make request
        response = requests.request(method, url, **kwargs)
        
        # Handle 401 for OAuth2
        if response.status_code == 401:
            creds = self.get_credentials(service_name)
            if creds and creds.get('type') == 'oauth2':
                # Force refresh and retry
                self._get_oauth2_token(service_name)
                headers.update(self.get_auth_headers(service_name))
                response = requests.request(method, url, **kwargs)
                
        return response
        
    def close(self) -> None:
        """Clean up resources."""
        self._stop_refresh = True
        if self._refresh_thread:
            self._refresh_thread.join(timeout=1)
```