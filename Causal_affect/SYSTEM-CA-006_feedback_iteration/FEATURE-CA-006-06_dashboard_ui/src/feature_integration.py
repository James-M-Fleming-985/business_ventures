"""
Feature Integration Module for Dashboard User Interface
FEATURE ID: FEATURE-CA-006-06

This module orchestrates all layers of the dashboard UI feature to provide
a cohesive interface for portfolio management and MVP analytics.
"""

from pathlib import Path
import sys
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum
import logging
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Layer imports
try:
    from LAYER_CA_006_06_01_dashboard_container_routing.src.implementation import (
        ErrorBoundary
    )
except ImportError:
    ErrorBoundary = None

try:
    from LAYER_CA_006_06_02_portfolio_overview_components.src.implementation import (
        StatCard,
        TopPerformersTable,
        ArchiveCandidatesTable,
        PortfolioTrendsChart,
        LoadingSkeleton,
        ResponsiveGrid,
        PortfolioView,
        APIClient as PortfolioAPIClient
    )
except ImportError:
    StatCard = None
    TopPerformersTable = None
    ArchiveCandidatesTable = None
    PortfolioTrendsChart = None
    LoadingSkeleton = None
    ResponsiveGrid = None
    PortfolioView = None
    PortfolioAPIClient = None

try:
    from LAYER_CA_006_06_03_mvp_detail_view_components.src.implementation import (
        WebSocketStatus,
        DimensionScore,
        ScoreBreakdown,
        Metric,
        EngagementMetrics,
        RevenueMetrics,
        FunnelStage,
        ConversionFunnel,
        TrafficSource,
        TrafficSources,
        LiveEvent,
        DataPoint,
        EngagementTrend,
        MVPData,
        WebSocketClient as MVPWebSocketClient,
        ScoreBreakdownCard,
        KeyMetricsGrid,
        ConversionFunnelChart,
        TrafficSourcesTable,
        LiveEventFeed,
        EngagementTrendChart,
        Breadcrumb,
        MVPDetailView
    )
except ImportError:
    WebSocketStatus = None
    DimensionScore = None
    ScoreBreakdown = None
    Metric = None
    EngagementMetrics = None
    RevenueMetrics = None
    FunnelStage = None
    ConversionFunnel = None
    TrafficSource = None
    TrafficSources = None
    LiveEvent = None
    DataPoint = None
    EngagementTrend = None
    MVPData = None
    MVPWebSocketClient = None
    ScoreBreakdownCard = None
    KeyMetricsGrid = None
    ConversionFunnelChart = None
    TrafficSourcesTable = None
    LiveEventFeed = None
    EngagementTrendChart = None
    Breadcrumb = None
    MVPDetailView = None

try:
    from LAYER_CA_006_06_04_chart_visualization_library.src.implementation import (
        TrendDirection,
        ChartVisualizationLibrary,
        TimeSeriesChart,
        BarChart,
        FunnelChart,
        ProgressBar,
        TrendIndicator,
        ResponsiveChartMixin
    )
except ImportError:
    TrendDirection = None
    ChartVisualizationLibrary = None
    TimeSeriesChart = None
    BarChart = None
    FunnelChart = None
    ProgressBar = None
    TrendIndicator = None
    ResponsiveChartMixin = None

try:
    from LAYER_CA_006_06_05_api_integration_realtime_updates.src.implementation import (
        ConnectionState,
        APIResponse,
        WebSocketMessage,
        ToastNotification,
        APIClient,
        WebSocketClient,
        PortfolioDataHook,
        MVPDetailHook
    )
except ImportError:
    ConnectionState = None
    APIResponse = None
    WebSocketMessage = None
    ToastNotification = None
    APIClient = None
    WebSocketClient = None
    PortfolioDataHook = None
    MVPDetailHook = None


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FeatureStatus(Enum):
    """Status enumeration for feature operations."""
    SUCCESS = "success"
    ERROR = "error"
    PARTIAL = "partial"
    INITIALIZING = "initializing"
    READY = "ready"


@dataclass
class FeatureResponse:
    """Unified response structure for feature operations."""
    status: FeatureStatus
    message: str
    data: Optional[Dict[str, Any]] = None
    errors: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert response to dictionary."""
        return {
            "status": self.status.value,
            "message": self.message,
            "data": self.data,
            "errors": self.errors,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class FeatureConfig:
    """Configuration for dashboard UI feature."""
    api_base_url: str = "http://localhost:8000"
    websocket_url: str = "ws://localhost:8000/ws"
    enable_real_time: bool = True
    auto_refresh_interval: int = 30  # seconds
    max_retry_attempts: int = 3
    connection_timeout: int = 10  # seconds
    chart_animation: bool = True
    theme: str = "light"
    debug_mode: bool = False
    
    def validate(self) -> Tuple[bool, List[str]]:
        """Validate configuration parameters."""
        errors = []
        
        if not self.api_base_url:
            errors.append("API base URL is required")
        
        if not self.websocket_url and self.enable_real_time:
            errors.append("WebSocket URL is required when real-time is enabled")
        
        if self.auto_refresh_interval < 1:
            errors.append("Auto refresh interval must be at least 1 second")
        
        if self.max_retry_attempts < 0:
            errors.append("Max retry attempts cannot be negative")
        
        if self.connection_timeout < 1:
            errors.append("Connection timeout must be at least 1 second")
        
        if self.theme not in ["light", "dark"]:
            errors.append("Theme must be 'light' or 'dark'")
        
        return len(errors) == 0, errors


class LayerInitializationError(Exception):
    """Exception raised when layer initialization fails."""
    pass


class FeatureOrchestrator:
    """
    Main orchestrator for Dashboard UI Feature.
    
    Coordinates interactions between all layers:
    - Dashboard Container & Routing
    - Portfolio Overview Components
    - MVP Detail View Components
    - Chart Visualization Library
    - API Integration & Real-time Updates
    """
    
    def __init__(self, config: Optional[FeatureConfig] = None):
        """
        Initialize the feature orchestrator.
        
        Args:
            config: Feature configuration object
        
        Raises:
            LayerInitializationError: If layer initialization fails
        """
        self.config = config or FeatureConfig()
        self.status = FeatureStatus.INITIALIZING
        self.layers_initialized: Dict[str, bool] = {}
        self.layer_instances: Dict[str, Any] = {}
        self.initialization_errors: List[str] = []
        
        # Validate configuration
        is_valid, validation_errors = self.config.validate()
        if not is_valid:
            raise LayerInitializationError(
                f"Invalid configuration: {', '.join(validation_errors)}"
            )
        
        # Initialize layers
        self._initialize_layers()
        
        # Set status based on initialization results
        if all(self.layers_initialized.values()):
            self.status = FeatureStatus.READY
            logger.info("Feature orchestrator initialized successfully")
        elif any(self.layers_initialized.values()):
            self.status = FeatureStatus.PARTIAL
            logger.warning(
                f"Feature orchestrator partially initialized. Errors: {self.initialization_errors}"
            )
        else:
            self.status = FeatureStatus.ERROR
            raise LayerInitializationError(
                f"Failed to initialize any layers: {', '.join(self.initialization_errors)}"
            )
    
    def _initialize_layers(self) -> None:
        """Initialize all layer components."""
        # Layer 1: Dashboard Container & Routing
        try:
            if ErrorBoundary:
                self.layer_instances["error_boundary"] = ErrorBoundary
                self.layers_initialized["layer_01"] = True
                logger.info("Layer 01 (Dashboard Container) initialized")
            else:
                raise ImportError("ErrorBoundary not available")
        except Exception as e:
            self.layers_initialized["layer_01"] = False
            self.initialization_errors.append(f"Layer 01: {str(e)}")
            logger.error(f"Failed to initialize Layer 01: {e}")
        
        # Layer 2: Portfolio Overview Components
        try:
            if PortfolioView and PortfolioAPIClient:
                self.layer_instances["portfolio_view"] = PortfolioView
                self.layer_instances["portfolio_components"] = {
                    "StatCard": StatCard,
                    "TopPerformersTable": TopPerformersTable,
                    "ArchiveCandidatesTable": ArchiveCandidatesTable,
                    "PortfolioTrendsChart": PortfolioTrendsChart,
                    "LoadingSkeleton": LoadingSkeleton,
                    "ResponsiveGrid": ResponsiveGrid
                }
                self.layers_initialized["layer_02"] = True
                logger.info("Layer 02 (Portfolio Overview) initialized")
            else:
                raise ImportError("Portfolio components not available")
        except Exception as e:
            self.layers_initialized["layer_02"] = False
            self.initialization_errors.append(f"Layer 02: {str(e)}")
            logger.error(f"Failed to initialize Layer 02: {e}")
        
        # Layer 3: MVP Detail View Components
        try:
            if MVPDetailView and MVPData:
                self.layer_instances["mvp_detail_view"] = MVPDetailView
                self.layer_instances["mvp_components"] = {
                    "ScoreBreakdownCard": ScoreBreakdownCard,
                    "KeyMetricsGrid": KeyMetricsGrid,
                    "ConversionFunnelChart": ConversionFunnelChart,
                    "TrafficSourcesTable": TrafficSourcesTable,
                    "LiveEventFeed": LiveEventFeed,
                    "EngagementTrendChart": EngagementTrendChart,
                    "Breadcrumb": Breadcrumb
                }
                self.layer_instances["mvp_data_models"] = {
                    "WebSocketStatus": WebSocketStatus,
                    "DimensionScore": DimensionScore,
                    "ScoreBreakdown": ScoreBreakdown,
                    "Metric": Metric,
                    "EngagementMetrics": EngagementMetrics,
                    "RevenueMetrics": RevenueMetrics,
                    "FunnelStage": FunnelStage,
                    "ConversionFunnel": ConversionFunnel,
                    "TrafficSource": TrafficSource,
                    "LiveEvent": LiveEvent,
                    "DataPoint": DataPoint
                }
                self.layers_initialized["layer_03"] = True
                logger.info("Layer 03 (MVP Detail View) initialized")
            else:
                raise ImportError("MVP detail components not available")
        except Exception as e:
            self.layers_initialized["layer_03"] = False
            self.initialization_errors.append(f"Layer 03: {str(e)}")
            logger.error(f"Failed to initialize Layer 03: {e}")
        
        # Layer 4: Chart Visualization Library
        try:
            if ChartVisualizationLibrary:
                self.layer_instances["chart_library"] = ChartVisualizationLibrary
                self.layer_instances["chart_components"] = {
                    "TimeSeriesChart": TimeSeriesChart,
                    "BarChart": BarChart,
                    "FunnelChart": FunnelChart,
                    "ProgressBar": ProgressBar,
                    "TrendIndicator": TrendIndicator
                }
                if TrendDirection:
                    self.layer_instances["chart_utils"] = {
                        "TrendDirection": TrendDirection
                    }
                self.layers_initialized["layer_04"] = True
                logger.info("Layer 04 (Chart Visualization) initialized")
            else:
                raise ImportError("Chart visualization components not available")
        except Exception as e:
            self.layers_initialized["layer_04"] = False
            self.initialization_errors.append(f"Layer 04: {str(e)}")
            logger.error(f"Failed to initialize Layer 04: {e}")
        
        # Layer 5: API Integration & Real-time Updates
        try:
            if APIClient and WebSocketClient:
                self.layer_instances["api_client"] = APIClient(
                    base_url=self.config.api_base_url,
                    timeout=self.config.connection_timeout,
                    max_retries=self.config.max_retry_attempts
                ) if callable(APIClient) else APIClient
                
                if self.config.enable_real_time:
                    self.layer_instances["websocket_client"] = WebSocketClient(
                        url=self.config.websocket_url
                    ) if callable(WebSocketClient) else WebSocketClient
                
                self.layer_instances["data_hooks"] = {
                    "PortfolioDataHook": PortfolioDataHook,
                    "MVPDetailHook": MVPDetailHook
                }
                self.layer_instances["api_models"] = {
                    "ConnectionState": ConnectionState,
                    "APIResponse": APIResponse,
                    "WebSocketMessage": WebSocketMessage,
                    "ToastNotification": ToastNotification
                }
                self.layers_initialized["layer_05"] = True
                logger.info("Layer 05 (API Integration) initialized")
            else:
                raise ImportError("API integration components not available")
        except Exception as e:
            self.layers_initialized["layer_05"] = False
            self.initialization_errors.append(f"Layer 05: {str(e)}")
            logger.error(f"Failed to initialize Layer 05: {e}")
    
    def get_portfolio_view_config(self) -> FeatureResponse:
        """
        Get configuration for portfolio overview view.
        
        Returns:
            FeatureResponse with portfolio view configuration
        """
        try:
            if not self.layers_initialized.get("layer_02"):
                return FeatureResponse(
                    status=FeatureStatus.ERROR,
                    message="Portfolio overview layer not initialized",
                    errors=["Layer 02 initialization failed"]
                )
            
            config_data = {
                "components": list(self.layer_instances.get("portfolio_components", {}).keys()),
                "view_class": "PortfolioView",
                "auto_refresh": self.config.auto_refresh_interval,
                "theme": self.config.theme
            }
            
            return FeatureResponse(
                status=FeatureStatus.SUCCESS,
                message="Portfolio view configuration retrieved",
                data=config_data
            )
        except Exception as e:
            logger.error(f"Error getting portfolio view config: {e}")
            return FeatureResponse(
                status=FeatureStatus.ERROR,
                message="Failed to get portfolio view configuration",
                errors=[str(e)]
            )
    
    def get_mvp_detail_view_config(self, mvp_id: str) -> FeatureResponse:
        """
        Get configuration for MVP detail view.
        
        Args:
            mvp_id: ID of the MVP to configure
        
        Returns:
            FeatureResponse with MVP detail view configuration
        """
        try:
            if not self.layers_initialized.get("layer_03"):
                return FeatureResponse(
                    status=FeatureStatus.ERROR,
                    message="MVP detail view layer not initialized",
                    errors=["Layer 03 initialization failed"]
                )
            
            config_data = {
                "mvp_id": mvp_id,
                "components": list(self.layer_instances.get("mvp_components", {}).keys()),
                "view_class": "MVPDetailView",
                "real_time_enabled": self.config.enable_real_time,
                "auto_refresh": self.config.auto_refresh_interval,
                "theme": self.config.theme
            }
            
            return FeatureResponse(
                status=FeatureStatus.SUCCESS,
                message=f"MVP detail view configuration retrieved for {mvp_id}",
                data=config_data
            )
        except Exception as e:
            logger.error(f"Error getting MVP detail view config: {e}")
            return FeatureResponse(
                status=FeatureStatus.ERROR,
                message="Failed to get MVP detail view configuration",
                errors=[str(e)]
            )
    
    def get_chart_library_config(self) -> FeatureResponse:
        """
        Get configuration for chart visualization library.
        
        Returns:
            FeatureResponse with chart library configuration
        """
        try:
            if not self.layers_initialized.get("layer_04"):
                return FeatureResponse(
                    status=FeatureStatus.ERROR,
                    message="Chart visualization layer not initialized",
                    errors=["Layer 04 initialization failed"]
                )
            
            config_data = {
                "components": list(self.layer_instances.get("chart_components", {}).keys()),
                "animation_enabled": self.config.chart_animation,
                "theme": self.config.theme
            }
            
            return FeatureResponse(
                status=FeatureStatus.SUCCESS,
                message="Chart library configuration retrieved",
                data=config_data
            )
        except Exception as e:
            logger.error(f"Error getting chart library config: {e}")
            return FeatureResponse(
                status=FeatureStatus.ERROR,
                message="Failed to get chart library configuration",
                errors=[str(e)]
            )
    
    def initialize_api_connection(self) -> FeatureResponse:
        """
        Initialize API and WebSocket connections.
        
        Returns:
            FeatureResponse with connection status
        """
        try:
            if not self.layers_initialized.get("layer_05"):
                return FeatureResponse(
                    status=FeatureStatus.ERROR,
                    message="API integration layer not initialized",
                    errors=["Layer 05 initialization failed"]
                )
            
            connection_data = {
                "api_client": "initialized",
                "api_base_url": self.config.api_base_url,
                "websocket_enabled": self.config.enable_real_time,
                "websocket_url": self.config.websocket_url if self.config.enable_real_time else None,
                "max_retries": self.config.max_retry_attempts,
                "timeout": self.config.connection_timeout
            }
            
            return FeatureResponse(
                status=FeatureStatus.SUCCESS,
                message="API connections initialized",
                data=connection_data
            )
        except Exception as e:
            logger.error(f"Error initializing API connection: {e}")
            return FeatureResponse(
                status=FeatureStatus.ERROR,
                message="Failed to initialize API connections",
                errors=[str(e)]
            )
    
    def get_routing_config(self) -> FeatureResponse:
        """
        Get routing configuration for dashboard navigation.
        
        Returns:
            FeatureResponse with routing configuration
        """
        try:
            if not self.layers_initialized.get("layer_01"):
                return FeatureResponse(
                    status=FeatureStatus.ERROR,
                    message="Dashboard container layer not initialized",
                    errors=["Layer 01 initialization failed"]
                )
            
            routing_data = {
                "routes": [
                    {
                        "path": "/",
                        "view": "PortfolioView",
                        "layer": "layer_02"
                    },
                    {
                        "path": "/mvp/:id",
                        "view": "MVPDetailView",
                        "layer": "layer_03"
                    }
                ],
                "error_boundary": "ErrorBoundary",
                "theme": self.config.theme
            }
            
            return FeatureResponse(
                status=FeatureStatus.SUCCESS,
                message="Routing configuration retrieved",
                data=routing_data
            )
        except Exception as e:
            logger.error(f"Error getting routing config: {e}")
            return FeatureResponse(
                status=FeatureStatus.ERROR,
                message="Failed to get routing configuration",
                errors=[str(e)]
            )
    
    def get_feature_status(self) -> FeatureResponse:
        """
        Get overall feature status and health check.
        
        Returns:
            FeatureResponse with feature status information
        """
        try:
            initialized_count = sum(1 for v in self.layers_initialized.values() if v)
            total_layers = len(self.layers_initialized)
            
            status_data = {
                "overall_status": self.status.value,
                "layers_initialized": initialized_count,
                "total_layers": total_layers,
                "initialization_percentage": (initialized_count / total_layers * 100) if total_layers > 0 else 0,
                "layer_status": {
                    "layer_01_container": self.layers_initialized.get("layer_01", False),
                    "layer_02_portfolio": self.layers_initialized.get("layer_02", False),
                    "layer_03_mvp_detail": self.layers_initialized.get("layer_03", False),
                    "layer_04_charts": self.layers_initialized.get("layer_04", False),
                    "layer_05_api": self.layers_initialized.get("layer_05", False)
                },
                "errors": self.initialization_errors,
                "config": {
                    "api_base_url": self.config.api_base_url,
                    "real_time_enabled": self.config.enable_real_time,
                    "theme": self.config.theme,
                    "debug_mode": self.config.debug_mode
                }
            }
            
            return FeatureResponse(
                status=self.status,
                message=f"Feature status: {initialized_count}/{total_layers} layers initialized",
                data=status_data
            )
        except Exception as e:
            logger.error(f"Error getting feature status: {e}")
            return FeatureResponse(
                status=FeatureStatus.ERROR,
                message="Failed to get feature status",
                errors=[str(e)]
            )
    
    def orchestrate_portfolio_dashboard(self) -> FeatureResponse:
        """
        Orchestrate the complete portfolio dashboard view.
        
        Coordinates layers 1, 2, 4, and 5 to provide the portfolio overview.
        
        Returns:
            FeatureResponse with orchestration result
        """
        try:
            required_layers = ["layer