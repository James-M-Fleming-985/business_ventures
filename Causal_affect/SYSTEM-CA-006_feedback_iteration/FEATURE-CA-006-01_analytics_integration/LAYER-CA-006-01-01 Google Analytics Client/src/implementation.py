```python
import json
import time
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import os

try:
    from google.analytics.data_v1beta import BetaAnalyticsDataClient
    from google.analytics.data_v1beta.types import (
        RunReportRequest,
        DateRange,
        Dimension,
        Metric,
    )
    from google.oauth2 import service_account
    from google.api_core import exceptions as google_exceptions
except ImportError:
    # Fallback for testing without Google libraries
    BetaAnalyticsDataClient = None
    RunReportRequest = None
    DateRange = None
    Dimension = None
    Metric = None
    service_account = None
    google_exceptions = None


class GoogleAnalyticsClient:
    """Client for interacting with Google Analytics 4 API."""

    def __init__(self, service_account_json: Optional[str] = None):
        """
        Initialize the Google Analytics client.

        Args:
            service_account_json: Path to service account JSON file or JSON string
        """
        self.client = None
        self.credentials = None
        self.max_retries = 5
        self.base_delay = 1.0

        if service_account_json:
            self.authenticate(service_account_json)

    def authenticate(self, service_account_json: str) -> bool:
        """
        Authenticate using service account JSON.

        Args:
            service_account_json: Path to service account JSON file or JSON string

        Returns:
            bool: True if authentication successful

        Raises:
            ValueError: If authentication fails
        """
        try:
            # Try to parse as JSON string first
            if service_account_json.strip().startswith('{'):
                credentials_info = json.loads(service_account_json)
                self.credentials = service_account.Credentials.from_service_account_info(
                    credentials_info,
                    scopes=['https://www.googleapis.com/auth/analytics.readonly']
                )
            else:
                # Treat as file path
                if not os.path.exists(service_account_json):
                    raise ValueError(f"Service account file not found: {service_account_json}")
                
                self.credentials = service_account.Credentials.from_service_account_file(
                    service_account_json,
                    scopes=['https://www.googleapis.com/auth/analytics.readonly']
                )

            self.client = BetaAnalyticsDataClient(credentials=self.credentials)
            return True

        except Exception as e:
            raise ValueError(f"Authentication failed: {str(e)}")

    def fetch_metrics(
        self,
        property_id: str,
        metrics: List[str],
        dimensions: Optional[List[str]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        timeout: float = 10.0
    ) -> Dict[str, Any]:
        """
        Fetch metrics from Google Analytics 4.

        Args:
            property_id: GA4 property ID
            metrics: List of metric names to fetch
            dimensions: List of dimension names to fetch
            start_date: Start date in YYYY-MM-DD format (default: 30 days ago)
            end_date: End date in YYYY-MM-DD format (default: today)
            timeout: Maximum time to wait for response in seconds

        Returns:
            Dict containing fetched data

        Raises:
            TimeoutError: If request takes longer than timeout
            ValueError: If client not authenticated or invalid parameters
        """
        if not self.client:
            raise ValueError("Client not authenticated. Call authenticate() first.")

        if not property_id:
            raise ValueError("property_id is required")

        if not metrics:
            raise ValueError("metrics list cannot be empty")

        # Set default date range if not provided
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')

        start_time = time.time()

        # Build request
        request = RunReportRequest(
            property=f"properties/{property_id}",
            date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
            metrics=[Metric(name=metric) for metric in metrics],
            dimensions=[Dimension(name=dim) for dim in dimensions] if dimensions else []
        )

        # Execute with retry logic
        response = self._execute_with_retry(request, timeout, start_time)

        elapsed_time = time.time() - start_time
        if elapsed_time > timeout:
            raise TimeoutError(f"Request exceeded timeout of {timeout} seconds")

        return self._transform_response(response)

    def _execute_with_retry(
        self,
        request: Any,
        timeout: float,
        start_time: float
    ) -> Any:
        """
        Execute request with exponential backoff retry logic.

        Args:
            request: The request to execute
            timeout: Maximum time to wait
            start_time: Request start time

        Returns:
            Response from API

        Raises:
            Exception: If all retries exhausted or timeout exceeded
        """
        for attempt in range(self.max_retries):
            try:
                elapsed = time.time() - start_time
                if elapsed >= timeout:
                    raise TimeoutError(f"Request exceeded timeout of {timeout} seconds")

                response = self.client.run_report(request)
                return response

            except Exception as e:
                # Check if this is a rate limit error
                is_rate_limit = False
                if google_exceptions and isinstance(e, google_exceptions.ResourceExhausted):
                    is_rate_limit = True
                elif hasattr(e, 'code') and e.code == 429:
                    is_rate_limit = True
                elif 'rate limit' in str(e).lower() or 'quota' in str(e).lower():
                    is_rate_limit = True

                if is_rate_limit and attempt < self.max_retries - 1:
                    # Calculate backoff delay
                    delay = self.base_delay * (2 ** attempt)
                    
                    # Check if we have time for retry
                    elapsed = time.time() - start_time
                    if elapsed + delay >= timeout:
                        raise TimeoutError(f"Request exceeded timeout of {timeout} seconds")
                    
                    time.sleep(delay)
                    continue
                
                # Not a rate limit error or out of retries
                raise

    def _transform_response(self, response: Any) -> Dict[str, Any]:
        """
        Transform GA4 response to common schema.

        Args:
            response: GA4 API response

        Returns:
            Transformed data in common schema format
        """
        transformed = {
            'dimensions': [],
            'metrics': [],
            'rows': [],
            'row_count': 0,
            'metadata': {}
        }

        # Extract dimension headers
        if hasattr(response, 'dimension_headers'):
            transformed['dimensions'] = [
                header.name for header in response.dimension_headers
            ]

        # Extract metric headers
        if hasattr(response, 'metric_headers'):
            transformed['metrics'] = [
                header.name for header in response.metric_headers
            ]

        # Extract rows
        if hasattr(response, 'rows'):
            for row in response.rows:
                row_data = {}
                
                # Add dimension values
                if hasattr(row, 'dimension_values'):
                    for i, dim_value in enumerate(row.dimension_values):
                        dim_name = transformed['dimensions'][i] if i < len(transformed['dimensions']) else f'dimension_{i}'
                        row_data[dim_name] = dim_value.value

                # Add metric values
                if hasattr(row, 'metric_values'):
                    for i, metric_value in enumerate(row.metric_values):
                        metric_name = transformed['metrics'][i] if i < len(transformed['metrics']) else f'metric_{i}'
                        row_data[metric_name] = metric_value.value

                transformed['rows'].append(row_data)

        transformed['row_count'] = len(transformed['rows'])

        # Add metadata
        if hasattr(response, 'row_count'):
            transformed['metadata']['total_rows'] = response.row_count
        if hasattr(response, 'metadata'):
            transformed['metadata']['currency_code'] = getattr(response.metadata, 'currency_code', None)
            transformed['metadata']['time_zone'] = getattr(response.metadata, 'time_zone', None)

        return transformed

    def handle_rate_limit(self, error: Exception, attempt: int) -> float:
        """
        Calculate backoff delay for rate limit errors.

        Args:
            error: The exception that was raised
            attempt: Current attempt number (0-indexed)

        Returns:
            float: Delay in seconds before retry
        """
        return self.base_delay * (2 ** attempt)


def create_client(service_account_json: Optional[str] = None) -> GoogleAnalyticsClient:
    """
    Factory function to create a GoogleAnalyticsClient instance.

    Args:
        service_account_json: Path to service account JSON file or JSON string

    Returns:
        GoogleAnalyticsClient instance
    """
    return GoogleAnalyticsClient(service_account_json)
```