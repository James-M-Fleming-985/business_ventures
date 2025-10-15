"""
Feature Integration Module for Revenue & Conversion Tracking
FEATURE ID: FEATURE-CA-006-03

This module orchestrates all layers of the revenue tracking feature to provide
end-to-end functionality for revenue event collection, conversion tracking,
financial metrics calculation, revenue aggregation, and financial reporting.
"""

from pathlib import Path
import sys
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from enum import Enum
import logging

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Layer imports
from layer_ca_006_03_01.src.implementation import (
    RevenueEvent,
    EventQueue,
    RevenueEventCollector
)
from layer_ca_006_03_02.src.implementation import (
    ConversionFunnelTracker
)
from layer_ca_006_03_03.src.implementation import (
    AttributionModel,
    FinancialMetricsCalculator
)
from layer_ca_006_03_04.src.implementation import (
    Period,
    RevenueRecord,
    ExchangeRate,
    AggregatedRevenue,
    ExchangeRateCache,
    CurrencyConverter,
    RevenueAggregator
)
from layer_ca_006_03_05.src.implementation import (
    AnomalyType,
    DashboardData,
    RevenueForecast,
    RevenueAnomaly,
    CohortAnalysis,
    FinancialReportingLayer
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FeatureStatus(Enum):
    """Status enum for feature operations"""
    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    FAILURE = "failure"
    ERROR = "error"


@dataclass
class FeatureConfig:
    """Configuration for the Revenue & Conversion Tracking feature"""
    # Event Collection Config
    stripe_api_key: Optional[str] = None
    paypal_client_id: Optional[str] = None
    paypal_client_secret: Optional[str] = None
    event_batch_size: int = 100
    event_processing_interval: int = 60  # seconds
    
    # Conversion Tracking Config
    funnel_stages: List[str] = field(default_factory=lambda: [
        "impression", "click", "view", "add_to_cart", "checkout", "purchase"
    ])
    
    # Financial Metrics Config
    attribution_model: str = "linear"  # linear, last_touch, first_touch
    cohort_periods: List[str] = field(default_factory=lambda: ["day", "week", "month"])
    
    # Aggregation Config
    base_currency: str = "USD"
    aggregation_periods: List[str] = field(default_factory=lambda: ["day", "week", "month"])
    exchange_rate_cache_ttl: int = 3600  # seconds
    
    # Reporting Config
    dashboard_refresh_interval: int = 300  # seconds (5 minutes)
    forecast_horizon_days: int = 30
    anomaly_detection_enabled: bool = True
    anomaly_threshold: float = 2.0  # standard deviations
    
    # Storage Config
    database_url: Optional[str] = None
    cache_backend: str = "memory"  # memory, redis
    
    def validate(self) -> List[str]:
        """Validate configuration and return list of issues"""
        issues = []
        
        if not self.base_currency:
            issues.append("base_currency is required")
        
        if self.event_batch_size < 1:
            issues.append("event_batch_size must be positive")
        
        if self.attribution_model not in ["linear", "last_touch", "first_touch"]:
            issues.append(f"Invalid attribution_model: {self.attribution_model}")
        
        if len(self.funnel_stages) < 2:
            issues.append("funnel_stages must have at least 2 stages")
        
        return issues


@dataclass
class FeatureResponse:
    """Unified response structure for feature operations"""
    status: FeatureStatus
    data: Optional[Dict[str, Any]] = None
    message: str = ""
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    execution_time_ms: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert response to dictionary"""
        return {
            "status": self.status.value,
            "data": self.data,
            "message": self.message,
            "errors": self.errors,
            "warnings": self.warnings,
            "timestamp": self.timestamp.isoformat(),
            "execution_time_ms": self.execution_time_ms
        }


class FeatureOrchestrator:
    """
    Main orchestrator for Revenue & Conversion Tracking feature.
    
    This class coordinates all five layers to provide comprehensive revenue
    tracking and reporting functionality.
    """
    
    def __init__(self, config: FeatureConfig):
        """
        Initialize the feature orchestrator with configuration.
        
        Args:
            config: FeatureConfig object with all necessary configuration
            
        Raises:
            ValueError: If configuration is invalid
        """
        self.config = config
        self._validate_config()
        self._initialized = False
        
        # Layer instances
        self.revenue_collector: Optional[RevenueEventCollector] = None
        self.funnel_tracker: Optional[ConversionFunnelTracker] = None
        self.metrics_calculator: Optional[FinancialMetricsCalculator] = None
        self.revenue_aggregator: Optional[RevenueAggregator] = None
        self.reporting_layer: Optional[FinancialReportingLayer] = None
        
        # Supporting components
        self.currency_converter: Optional[CurrencyConverter] = None
        self.attribution_model: Optional[AttributionModel] = None
        
        logger.info("FeatureOrchestrator initialized with config")
    
    def _validate_config(self) -> None:
        """Validate configuration and raise exception if invalid"""
        issues = self.config.validate()
        if issues:
            raise ValueError(f"Configuration validation failed: {', '.join(issues)}")
    
    def initialize(self) -> FeatureResponse:
        """
        Initialize all layers and components.
        
        Returns:
            FeatureResponse indicating success or failure of initialization
        """
        start_time = datetime.utcnow()
        errors = []
        warnings = []
        
        try:
            # Initialize Layer 1: Revenue Event Collector
            logger.info("Initializing Revenue Event Collector...")
            try:
                self.revenue_collector = RevenueEventCollector(
                    stripe_api_key=self.config.stripe_api_key,
                    paypal_client_id=self.config.paypal_client_id,
                    paypal_client_secret=self.config.paypal_client_secret
                )
            except Exception as e:
                errors.append(f"Revenue Event Collector initialization failed: {str(e)}")
                logger.error(f"Failed to initialize Revenue Event Collector: {e}")
            
            # Initialize Layer 2: Conversion Funnel Tracker
            logger.info("Initializing Conversion Funnel Tracker...")
            try:
                self.funnel_tracker = ConversionFunnelTracker(
                    stages=self.config.funnel_stages
                )
            except Exception as e:
                errors.append(f"Conversion Funnel Tracker initialization failed: {str(e)}")
                logger.error(f"Failed to initialize Conversion Funnel Tracker: {e}")
            
            # Initialize Layer 3: Financial Metrics Calculator
            logger.info("Initializing Financial Metrics Calculator...")
            try:
                self.attribution_model = AttributionModel(
                    model_type=self.config.attribution_model
                )
                self.metrics_calculator = FinancialMetricsCalculator(
                    attribution_model=self.attribution_model
                )
            except Exception as e:
                errors.append(f"Financial Metrics Calculator initialization failed: {str(e)}")
                logger.error(f"Failed to initialize Financial Metrics Calculator: {e}")
            
            # Initialize Layer 4: Revenue Aggregator
            logger.info("Initializing Revenue Aggregator...")
            try:
                exchange_rate_cache = ExchangeRateCache(
                    ttl_seconds=self.config.exchange_rate_cache_ttl
                )
                self.currency_converter = CurrencyConverter(
                    cache=exchange_rate_cache,
                    base_currency=self.config.base_currency
                )
                self.revenue_aggregator = RevenueAggregator(
                    currency_converter=self.currency_converter,
                    base_currency=self.config.base_currency
                )
            except Exception as e:
                errors.append(f"Revenue Aggregator initialization failed: {str(e)}")
                logger.error(f"Failed to initialize Revenue Aggregator: {e}")
            
            # Initialize Layer 5: Financial Reporting Layer
            logger.info("Initializing Financial Reporting Layer...")
            try:
                self.reporting_layer = FinancialReportingLayer(
                    forecast_horizon_days=self.config.forecast_horizon_days,
                    anomaly_threshold=self.config.anomaly_threshold
                )
            except Exception as e:
                errors.append(f"Financial Reporting Layer initialization failed: {str(e)}")
                logger.error(f"Failed to initialize Financial Reporting Layer: {e}")
            
            # Check if all critical components initialized
            if errors:
                self._initialized = False
                execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
                return FeatureResponse(
                    status=FeatureStatus.FAILURE,
                    message="Feature initialization failed",
                    errors=errors,
                    warnings=warnings,
                    execution_time_ms=execution_time
                )
            
            self._initialized = True
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            logger.info("All layers initialized successfully")
            return FeatureResponse(
                status=FeatureStatus.SUCCESS,
                message="Feature initialized successfully",
                data={"layers_initialized": 5},
                warnings=warnings,
                execution_time_ms=execution_time
            )
            
        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            logger.error(f"Unexpected error during initialization: {e}")
            return FeatureResponse(
                status=FeatureStatus.ERROR,
                message="Unexpected error during initialization",
                errors=[str(e)],
                execution_time_ms=execution_time
            )
    
    def _ensure_initialized(self) -> None:
        """Ensure feature is initialized before operations"""
        if not self._initialized:
            raise RuntimeError("Feature not initialized. Call initialize() first.")
    
    def process_revenue_event(
        self,
        event_type: str,
        transaction_id: str,
        user_id: str,
        amount: float,
        currency: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> FeatureResponse:
        """
        Process a single revenue event through all layers.
        
        Args:
            event_type: Type of event (purchase, refund, subscription)
            transaction_id: Unique transaction identifier
            user_id: User identifier
            amount: Transaction amount
            currency: Currency code (e.g., USD, EUR)
            metadata: Additional event metadata
            
        Returns:
            FeatureResponse with processed event data
        """
        start_time = datetime.utcnow()
        self._ensure_initialized()
        
        try:
            # Layer 1: Collect revenue event
            revenue_event = RevenueEvent(
                event_type=event_type,
                transaction_id=transaction_id,
                user_id=user_id,
                amount=amount,
                currency=currency,
                timestamp=datetime.utcnow(),
                metadata=metadata or {}
            )
            
            self.revenue_collector.collect_event(revenue_event)
            
            # Layer 2: Update conversion funnel if purchase
            if event_type == "purchase":
                self.funnel_tracker.track_conversion(
                    user_id=user_id,
                    stage="purchase",
                    timestamp=revenue_event.timestamp
                )
            
            # Layer 4: Create revenue record and aggregate
            revenue_record = RevenueRecord(
                transaction_id=transaction_id,
                user_id=user_id,
                amount=amount,
                currency=currency,
                timestamp=revenue_event.timestamp,
                event_type=event_type
            )
            
            # Convert to base currency
            converted_amount = self.currency_converter.convert(
                amount=amount,
                from_currency=currency,
                to_currency=self.config.base_currency
            )
            
            # Aggregate revenue
            for period_type in self.config.aggregation_periods:
                self.revenue_aggregator.aggregate_revenue(
                    revenue_record=revenue_record,
                    period_type=period_type
                )
            
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            return FeatureResponse(
                status=FeatureStatus.SUCCESS,
                message=f"Revenue event processed successfully",
                data={
                    "transaction_id": transaction_id,
                    "event_type": event_type,
                    "original_amount": amount,
                    "original_currency": currency,
                    "converted_amount": converted_amount,
                    "base_currency": self.config.base_currency,
                    "processing_latency_ms": execution_time
                },
                execution_time_ms=execution_time
            )
            
        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            logger.error(f"Error processing revenue event: {e}")
            return FeatureResponse(
                status=FeatureStatus.ERROR,
                message="Failed to process revenue event",
                errors=[str(e)],
                execution_time_ms=execution_time
            )
    
    def track_funnel_stage(
        self,
        user_id: str,
        stage: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> FeatureResponse:
        """
        Track a user's progress through the conversion funnel.
        
        Args:
            user_id: User identifier
            stage: Funnel stage name
            metadata: Additional tracking metadata
            
        Returns:
            FeatureResponse with tracking status
        """
        start_time = datetime.utcnow()
        self._ensure_initialized()
        
        try:
            if stage not in self.config.funnel_stages:
                return FeatureResponse(
                    status=FeatureStatus.FAILURE,
                    message=f"Invalid funnel stage: {stage}",
                    errors=[f"Stage must be one of: {', '.join(self.config.funnel_stages)}"]
                )
            
            self.funnel_tracker.track_stage(
                user_id=user_id,
                stage=stage,
                timestamp=datetime.utcnow(),
                metadata=metadata or {}
            )
            
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            return FeatureResponse(
                status=FeatureStatus.SUCCESS,
                message=f"Funnel stage tracked: {stage}",
                data={
                    "user_id": user_id,
                    "stage": stage,
                    "timestamp": datetime.utcnow().isoformat()
                },
                execution_time_ms=execution_time
            )
            
        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            logger.error(f"Error tracking funnel stage: {e}")
            return FeatureResponse(
                status=FeatureStatus.ERROR,
                message="Failed to track funnel stage",
                errors=[str(e)],
                execution_time_ms=execution_time
            )
    
    def calculate_metrics(
        self,
        start_date: datetime,
        end_date: datetime,
        cohort_id: Optional[str] = None
    ) -> FeatureResponse:
        """
        Calculate financial metrics for a given period.
        
        Args:
            start_date: Start of analysis period
            end_date: End of analysis period
            cohort_id: Optional cohort identifier for cohort analysis
            
        Returns:
            FeatureResponse with calculated metrics
        """
        start_time = datetime.utcnow()
        self._ensure_initialized()
        
        try:
            # Get aggregated revenue data
            aggregated_data = self.revenue_aggregator.get_aggregated_revenue(
                start_date=start_date,
                end_date=end_date,
                period_type="day"
            )
            
            # Calculate financial metrics
            metrics = self.metrics_calculator.calculate_metrics(
                revenue_data=aggregated_data,
                start_date=start_date,
                end_date=end_date,
                cohort_id=cohort_id
            )
            
            # Get conversion funnel metrics
            funnel_metrics = self.funnel_tracker.get_funnel_metrics(
                start_date=start_date,
                end_date=end_date
            )
            
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            return FeatureResponse(
                status=FeatureStatus.SUCCESS,
                message="Metrics calculated successfully",
                data={
                    "period": {
                        "start_date": start_date.isoformat(),
                        "end_date": end_date.isoformat()
                    },
                    "financial_metrics": metrics,
                    "funnel_metrics": funnel_metrics,
                    "cohort_id": cohort_id
                },
                execution_time_ms=execution_time
            )
            
        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            logger.error(f"Error calculating metrics: {e}")
            return FeatureResponse(
                status=FeatureStatus.ERROR,
                message="Failed to calculate metrics",
                errors=[str(e)],
                execution_time_ms=execution_time
            )
    
    def generate_dashboard_data(
        self,
        period_days: int = 30,
        include_forecast: bool = True,
        include_anomalies: bool = True
    ) -> FeatureResponse:
        """
        Generate comprehensive dashboard data for financial reporting.
        
        Args:
            period_days: Number of days to include in dashboard
            include_forecast: Whether to include revenue forecast
            include_anomalies: Whether to detect and include anomalies
            
        Returns:
            FeatureResponse with dashboard data
        """
        start_time = datetime.utcnow()
        self._ensure_initialized()
        
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=period_days)
            
            # Get aggregated revenue
            revenue_data = self.revenue_aggregator.get_aggregated_revenue(
                start_date=start_date,
                end_date=end_date,
                period_type="day"
            )
            
            # Calculate metrics
            metrics = self.metrics_calculator.calculate_metrics(
                revenue_data=revenue_data,
                start_date=start_date,
                end_date=end_date
            )
            
            # Get funnel data
            funnel_data = self.funnel_tracker.get_funnel_metrics(
                start_date=start_date,
                end_date=end_date
            )
            
            # Generate forecast if requested
            forecast = None
            if include_forecast:
                forecast = self.reporting_layer.generate_forecast(
                    historical_data=revenue_data,
                    horizon_days=self.config.forecast_horizon_days
                )
            
            # Detect anomalies if requested
            anomalies = []
            if include_anomalies and self.config.anomaly_detection_enabled:
                anomalies = self.reporting_layer.detect_anomalies(
                    revenue_data=revenue_data,
                    threshold=self.config.anomaly_threshold
                )
            
            # Build dashboard data
            dashboard_data = self.reporting_layer.build_dashboard_data(
                revenue_data=revenue_data,
                metrics=metrics,
                funnel_data=funnel_data,
                forecast=forecast,
                anomalies=anomalies
            )
            
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            # Check latency requirement (<5 minutes = 300,000 ms)
            warnings = []
            if execution_time > 300000:
                warnings.append(
                    f"Dashboard generation exceeded 5-minute latency requirement: "
                    f"{execution_time}ms"
                )
            
            return FeatureResponse(
                status=FeatureStatus.SUCCESS,
                message="Dashboard data generated successfully",
                data={
                    "dashboard": dashboard_data,
                    "period_days": period_days,
                    "anomaly_count": len(anomalies),
                    "forecast_included": include_forecast
                },
                warnings=warnings,
                execution_time_ms=execution_time
            )
            
        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            logger.error(f"Error generating dashboard data: {e}")
            return FeatureResponse(
                status=FeatureStatus.ERROR,
                message="Failed to generate dashboard data",
                errors=[str(e)],
                execution_time_ms=execution_time
            )
    
    def perform_cohort_analysis(
        self,
        cohort_definition: Dict[str, Any],
        analysis_period_days: int = 90
    ) -> FeatureResponse:
        """
        Perform cohort analysis for lifetime value estimation.
        
        Args:
            cohort_definition: Definition of cohort parameters
            analysis_period_days: Number of days to analyze
            
        Returns:
            FeatureResponse with cohort analysis results
        """
        start_time = datetime.utcnow()
        self._ensure_initialized()
        
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=analysis_period_days)
            
            # Get cohort data
            cohort_users = self._identify_cohort_users(cohort_definition)
            
            # Calculate cohort metrics
            cohort_metrics = self.metrics_calculator.calculate_cohort_metrics(
                cohort_users=cohort_users,
                start_date=start_date,
                end_date=end_date
            )
            
            # Generate cohort analysis report
            cohort_analysis = self.reporting_layer.generate_cohort_analysis(
                cohort_metrics=cohort_metrics,
                cohort