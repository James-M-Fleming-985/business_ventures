import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
import json
from typing import Dict, Any

from features.FEATURE_CA_006_01_analytics_integration.services.google_analytics_client import (
    GoogleAnalyticsClient,
    GoogleAnalyticsError,
    GoogleAnalyticsAuthError,
    GoogleAnalyticsAPIError
)
from features.FEATURE_CA_006_01_analytics_integration.models.analytics import (
    AnalyticsRequest,
    AnalyticsResponse,
    Metric,
    Dimension,
    DateRange,
    OrderBy,
    OrderType,
    MetricType,
    DimensionType,
    AnalyticsData,
    DimensionValue,
    MetricValue
)


class TestGoogleAnalyticsClient:
    """Test suite for Google Analytics client."""

    @pytest.fixture
    def mock_credentials(self):
        """Mock Google Analytics credentials."""
        return {
            "type": "service_account",
            "project_id": "test-project",
            "private_key_id": "key-id",
            "private_key": "-----BEGIN PRIVATE KEY-----\ntest\n-----END PRIVATE KEY-----",
            "client_email": "test@test.iam.gserviceaccount.com",
            "client_id": "123456789",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/test%40test.iam.gserviceaccount.com"
        }

    @pytest.fixture
    def client(self, mock_credentials):
        """Create test client instance."""
        with patch("builtins.open", mock_open(read_data=json.dumps(mock_credentials))):
            return GoogleAnalyticsClient(
                property_id="123456",
                credentials_path="/path/to/creds.json"
            )

    @pytest.fixture
    def sample_request(self) -> AnalyticsRequest:
        """Create sample analytics request."""
        return AnalyticsRequest(
            date_ranges=[
                DateRange(
                    start_date=datetime.now() - timedelta(days=7),
                    end_date=datetime.now()
                )
            ],
            metrics=[
                Metric(name=MetricType.SESSIONS),
                Metric(name=MetricType.USERS)
            ],
            dimensions=[Dimension(name=DimensionType.DATE)],
            limit=10
        )

    @pytest.fixture
    def mock_response_data(self) -> Dict[str, Any]:
        """Mock Google Analytics API response."""
        return {
            "dimensionHeaders": [{"name": "date"}],
            "metricHeaders": [
                {"name": "sessions", "type": "TYPE_INTEGER"},
                {"name": "totalUsers", "type": "TYPE_INTEGER"}
            ],
            "rows": [
                {
                    "dimensionValues": [{"value": "20240101"}],
                    "metricValues": [
                        {"value": "1234"},
                        {"value": "567"}
                    ]
                },
                {
                    "dimensionValues": [{"value": "20240102"}],
                    "metricValues": [
                        {"value": "2345"},
                        {"value": "678"}
                    ]
                }
            ],
            "rowCount": 2,
            "metadata": {
                "dataLossFromOtherRow": False
            }
        }

    @pytest.mark.asyncio
    async def test_client_initialization(self, mock_credentials):
        """Test client initialization with credentials."""
        with patch("builtins.open", mock_open(read_data=json.dumps(mock_credentials))):
            client = GoogleAnalyticsClient(
                property_id="123456",
                credentials_path="/path/to/creds.json"
            )
            assert client.property_id == "123456"
            assert client._analytics is None

    @pytest.mark.asyncio
    async def test_client_initialization_invalid_credentials(self):
        """Test client initialization with invalid credentials."""
        with patch("builtins.open", side_effect=FileNotFoundError()):
            with pytest.raises(GoogleAnalyticsAuthError, match="Failed to load credentials"):
                GoogleAnalyticsClient(
                    property_id="123456",
                    credentials_path="/invalid/path.json"
                )

    @pytest.mark.asyncio
    async def test_get_analytics_data_success(self, client, sample_request, mock_response_data):
        """Test successful analytics data retrieval."""
        mock_analytics = Mock()
        mock_properties = Mock()
        mock_analytics.properties.return_value = mock_properties
        
        mock_run_report = AsyncMock()
        mock_run_report.return_value = Mock(**mock_response_data)
        mock_properties.runReport = mock_run_report
        
        with patch.object(client, "_get_analytics_service", return_value=mock_analytics):
            response = await client.get_analytics_data(sample_request)
            
            assert isinstance(response, AnalyticsResponse)
            assert len(response.data) == 2
            assert response.data[0].dimensions[0].value == "20240101"
            assert response.data[0].metrics[0].value == 1234
            assert response.data[0].metrics[1].value == 567

    @pytest.mark.asyncio
    async def test_get_analytics_data_with_filters(self, client):
        """Test analytics data retrieval with dimension filters."""
        request = AnalyticsRequest(
            date_ranges=[DateRange(
                start_date=datetime.now() - timedelta(days=7),
                end_date=datetime.now()
            )],
            metrics=[Metric(name=MetricType.SESSIONS)],
            dimensions=[Dimension(name=DimensionType.COUNTRY)],
            dimension_filter={
                "filter": {
                    "fieldName": "country",
                    "stringFilter": {
                        "value": "United States"
                    }
                }
            }
        )
        
        mock_analytics = Mock()
        mock_properties = Mock()
        mock_analytics.properties.return_value = mock_properties
        
        mock_run_report = AsyncMock()
        mock_run_report.return_value = Mock(
            dimensionHeaders=[{"name": "country"}],
            metricHeaders=[{"name": "sessions", "type": "TYPE_INTEGER"}],
            rows=[{
                "dimensionValues": [{"value": "United States"}],
                "metricValues": [{"value": "1000"}]
            }],
            rowCount=1
        )
        mock_properties.runReport = mock_run_report
        
        with patch.object(client, "_get_analytics_service", return_value=mock_analytics):
            response = await client.get_analytics_data(request)
            
            # Verify filter was applied in request
            call_args = mock_run_report.call_args[1]
            assert "dimensionFilter" in call_args["request"]
            assert call_args["request"]["dimensionFilter"]["filter"]["fieldName"] == "country"

    @pytest.mark.asyncio
    async def test_get_analytics_data_with_ordering(self, client):
        """Test analytics data retrieval with ordering."""
        request = AnalyticsRequest(
            date_ranges=[DateRange(
                start_date=datetime.now() - timedelta(days=7),
                end_date=datetime.now()
            )],
            metrics=[Metric(name=MetricType.SESSIONS)],
            dimensions=[Dimension(name=DimensionType.DATE)],
            order_by=[OrderBy(
                field="sessions",
                order_type=OrderType.DESC
            )]
        )
        
        mock_analytics = Mock()
        mock_properties = Mock()
        mock_analytics.properties.return_value = mock_properties
        
        mock_run_report = AsyncMock()
        mock_run_report.return_value = Mock(
            dimensionHeaders=[{"name": "date"}],
            metricHeaders=[{"name": "sessions", "type": "TYPE_INTEGER"}],
            rows=[],
            rowCount=0
        )
        mock_properties.runReport = mock_run_report
        
        with patch.object(client, "_get_analytics_service", return_value=mock_analytics):
            await client.get_analytics_data(request)
            
            # Verify ordering was applied
            call_args = mock_run_report.call_args[1]
            assert "orderBys" in call_args["request"]
            assert call_args["request"]["orderBys"][0]["metric"]["metricName"] == "sessions"
            assert call_args["request"]["orderBys"][0]["desc"] is True

    @pytest.mark.asyncio
    async def test_get_analytics_data_api_error(self, client, sample_request):
        """Test API error handling."""
        mock_analytics = Mock()
        mock_properties = Mock()
        mock_analytics.properties.return_value = mock_properties
        
        mock_run_report = AsyncMock()
        mock_run_report.side_effect = Exception("API Error")
        mock_properties.runReport = mock_run_report
        
        with patch.object(client, "_get_analytics_service", return_value=mock_analytics):
            with pytest.raises(GoogleAnalyticsAPIError, match="Failed to fetch analytics data"):
                await client.get_analytics_data(sample_request)

    @pytest.mark.asyncio
    async def test_get_analytics_data_auth_error(self, client, sample_request):
        """Test authentication error handling."""
        with patch.object(client, "_get_analytics_service", side_effect=GoogleAnalyticsAuthError("Auth failed")):
            with pytest.raises(GoogleAnalyticsAuthError):
                await client.get_analytics_data(sample_request)

    @pytest.mark.asyncio
    async def test_build_request_with_all_parameters(self, client):
        """Test request building with all parameters."""
        request = AnalyticsRequest(
            date_ranges=[
                DateRange(
                    start_date=datetime(2024, 1, 1),
                    end_date=datetime(2024, 1, 7)
                ),
                DateRange(
                    start_date=datetime(2024, 1, 8),
                    end_date=datetime(2024, 1, 14)
                )
            ],
            metrics=[
                Metric(name=MetricType.SESSIONS),
                Metric(name=MetricType.BOUNCE_RATE)
            ],
            dimensions=[
                Dimension(name=DimensionType.DATE),
                Dimension(name=DimensionType.COUNTRY)
            ],
            dimension_filter={
                "filter": {
                    "fieldName": "country",
                    "stringFilter": {"value": "US"}
                }
            },
            metric_filter={
                "filter": {
                    "fieldName": "sessions",
                    "numericFilter": {
                        "operation": "GREATER_THAN",
                        "value": {"int64Value": "100"}
                    }
                }
            },
            order_by=[
                OrderBy(field="sessions", order_type=OrderType.DESC),
                OrderBy(field="date", order_type=OrderType.ASC)
            ],
            limit=100,
            offset=50
        )
        
        built_request = client._build_request(request)
        
        assert len(built_request["dateRanges"]) == 2
        assert built_request["dateRanges"][0]["startDate"] == "2024-01-01"
        assert built_request["dateRanges"][0]["endDate"] == "2024-01-07"
        
        assert len(built_request["metrics"]) == 2
        assert built_request["metrics"][0]["name"] == "sessions"
        assert built_request["metrics"][1]["name"] == "bounceRate"
        
        assert len(built_request["dimensions"]) == 2
        assert built_request["dimensions"][0]["name"] == "date"
        assert built_request["dimensions"][1]["name"] == "country"
        
        assert "dimensionFilter" in built_request
        assert "metricFilter" in built_request
        assert len(built_request["orderBys"]) == 2
        assert built_request["limit"] == 100
        assert built_request["offset"] == 50

    @pytest.mark.asyncio
    async def test_parse_response_empty_data(self, client):
        """Test parsing empty response."""
        mock_response = Mock(
            dimensionHeaders=[],
            metricHeaders=[],
            rows=[],
            rowCount=0
        )
        
        response = client._parse_response(mock_response)
        
        assert isinstance(response, AnalyticsResponse)
        assert len(response.data) == 0
        assert response.row_count == 0

    @pytest.mark.asyncio
    async def test_parse_response_with_metadata(self, client):
        """Test parsing response with metadata."""
        mock_response = Mock(
            dimensionHeaders=[{"name": "date"}],
            metricHeaders=[{"name": "sessions", "type": "TYPE_INTEGER"}],
            rows=[{
                "dimensionValues": [{"value": "20240101"}],
                "metricValues": [{"value": "1000"}]
            }],
            rowCount=1,
            metadata={
                "dataLossFromOtherRow": True,
                "currencyCode": "USD",
                "timeZone": "America/New_York"
            },
            propertyQuota={
                "tokensPerDay": {
                    "consumed": 50,
                    "remaining": 24950
                },
                "tokensPerHour": {
                    "consumed": 10,
                    "remaining": 990
                }
            }
        )
        
        response = client._parse_response(mock_response)
        
        assert response.metadata["dataLossFromOtherRow"] is True
        assert response.metadata["currencyCode"] == "USD"
        assert response.property_quota["tokensPerDay"]["consumed"] == 50

    def test_metric_name_mapping(self, client):
        """Test metric name mapping to GA4 API names."""
        assert client._get_metric_name(MetricType.SESSIONS) == "sessions"
        assert client._get_metric_name(MetricType.USERS) == "totalUsers"
        assert client._get_metric_name(MetricType.NEW_USERS) == "newUsers"
        assert client._get_metric_name(MetricType.BOUNCE_RATE) == "bounceRate"
        assert client._get_metric_name(MetricType.AVG_SESSION_DURATION) == "averageSessionDuration"
        assert client._get_metric_name(MetricType.CONVERSIONS) == "conversions"

    def test_dimension_name_mapping(self, client):
        """Test dimension name mapping to GA4 API names."""
        assert client._get_dimension_name(DimensionType.DATE) == "date"
        assert client._get_dimension_name(DimensionType.COUNTRY) == "country"
        assert client._get_dimension_name(DimensionType.CITY) == "city"
        assert client._get_dimension_name(DimensionType.SOURCE) == "source"
        assert client._get_dimension_name(DimensionType.MEDIUM) == "medium"
        assert client._get_dimension_name(DimensionType.CAMPAIGN) == "campaignName"

    @pytest.mark.asyncio
    async def test_concurrent_requests(self, client, sample_request, mock_response_data):
        """Test handling concurrent analytics requests."""
        mock_analytics = Mock()
        mock_properties = Mock()
        mock_analytics.properties.return_value = mock_properties
        
        mock_run_report = AsyncMock()
        mock_run_report.return_value = Mock(**mock_response_data)
        mock_properties.runReport = mock_run_report
        
        with patch.object(client, "_get_analytics_service", return_value=mock_analytics):
            # Run multiple concurrent requests
            import asyncio
            tasks = [
                client.get_analytics_data(sample_request)
                for _ in range(5)
            ]
            responses = await asyncio.gather(*tasks)
            
            assert len(responses) == 5
            for response in responses:
                assert isinstance(response, AnalyticsResponse)
                assert len(response.data) == 2

    @pytest.mark.asyncio
    async def test_service_initialization_caching(self, client):
        """Test that analytics service is cached after first initialization."""
        mock_service = Mock()
        
        with patch("google.analytics.data_v1beta.BetaAnalyticsDataClient", return_value=mock_service):
            # First call
            service1 = client._get_analytics_service()
            # Second call should return cached service
            service2 = client._get_analytics_service()
            
            assert service1 is service2
            assert service1 is mock_service


def mock_open(read_data):
    """Helper to mock file opening."""
    from unittest.mock import mock_open as _mock_open
    return _mock_open(read_data=read_data)