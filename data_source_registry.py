"""
Data Source Registry - Extensible Data Universe Framework

This module provides a centralized, consistent way to:
1. Register new data sources with minimal boilerplate
2. Ensure all data points align to the standard monthly grid
3. Track data source metadata (layer, frequency, fill strategy)
4. Make the data universe easily extensible

ADDING A NEW DATA SOURCE:
=========================
1. Define your source in DATA_SOURCES dict below
2. Add a fetch method to DataFetcher class
3. Add a fill strategy to get_fill_strategy_for_variable_type()
4. Run setup script to add variables to database
5. Deploy and trigger data ingestion

All sources automatically:
- Normalize to first-of-month timestamps
- Use consistent fill strategies
- Integrate with correlation analysis
- Support Granger causality testing
"""

from typing import Dict, List, Optional, Any
from enum import Enum
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


class SignalLayer(Enum):
    """
    Temporal signal layers for cascade detection.
    Fast layers predict Medium/Slow layer movements.
    """
    PROTO_FAST = 0   # Micro-signals (minutes/hours) - Future
    FAST = 1         # Behavioral (days/weeks) - Wikipedia, Reddit, GitHub
    MEDIUM = 2       # Market/Operational (weeks/months) - Stocks, Trials, arXiv
    SLOW = 3         # Structural (months/years) - GDP, Demographics


class UpdateFrequency(Enum):
    """How often the source data updates"""
    REALTIME = "realtime"
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUAL = "annual"


class FillStrategy(Enum):
    """How to handle missing data points in the standard grid"""
    FORWARD_FILL = "ffill"      # Repeat last known value (good for slow-changing data)
    INTERPOLATE = "interpolate"  # Linear interpolation (good for smooth trends)
    BACKWARD_FILL = "bfill"      # Use next known value
    ZERO = "zero"               # Fill with zero (good for counts)
    NONE = "none"               # Leave gaps (may break correlations)


@dataclass
class DataSourceConfig:
    """Configuration for a data source"""
    name: str                          # Unique source identifier
    display_name: str                  # Human-readable name
    layer: SignalLayer                 # Which temporal layer
    update_frequency: UpdateFrequency  # How often data updates
    fill_strategy: FillStrategy        # How to handle missing data
    requires_api_key: bool = False     # Whether API key is needed
    api_key_env_var: Optional[str] = None  # Environment variable name
    rate_limit_delay: float = 0.0      # Seconds between API calls
    max_history_months: int = 60       # How much history to fetch
    is_active: bool = True             # Whether source is enabled
    notes: str = ""                    # Additional documentation


# ==============================================================================
# MASTER DATA SOURCE REGISTRY
# ==============================================================================
# Add new sources here. The system will automatically handle normalization,
# correlation analysis, and Granger causality testing.

DATA_SOURCES: Dict[str, DataSourceConfig] = {
    # =========================================================================
    # LAYER 1: FAST (Behavioral Signals)
    # =========================================================================
    "wikipedia": DataSourceConfig(
        name="wikipedia",
        display_name="Wikipedia Pageviews",
        layer=SignalLayer.FAST,
        update_frequency=UpdateFrequency.DAILY,
        fill_strategy=FillStrategy.INTERPOLATE,
        requires_api_key=False,
        rate_limit_delay=0.5,
        max_history_months=60,
        notes="FREE API, no rate limits. Replaces Google Trends."
    ),
    
    "reddit": DataSourceConfig(
        name="reddit",
        display_name="Reddit Activity",
        layer=SignalLayer.FAST,
        update_frequency=UpdateFrequency.DAILY,
        fill_strategy=FillStrategy.INTERPOLATE,
        requires_api_key=False,  # Public API has limits
        rate_limit_delay=2.0,
        max_history_months=36,
        notes="Reddit JSON API. For full history, use Pullpush.io"
    ),
    
    "github": DataSourceConfig(
        name="github",
        display_name="GitHub Repository Stars",
        layer=SignalLayer.FAST,
        update_frequency=UpdateFrequency.DAILY,
        fill_strategy=FillStrategy.FORWARD_FILL,
        requires_api_key=False,  # Optional but recommended
        api_key_env_var="GITHUB_TOKEN",
        rate_limit_delay=1.0,
        max_history_months=60,
        notes="60 req/hr unauthenticated, 5000 req/hr with token"
    ),
    
    "google_trends": DataSourceConfig(
        name="google_trends",
        display_name="Google Trends",
        layer=SignalLayer.FAST,
        update_frequency=UpdateFrequency.WEEKLY,
        fill_strategy=FillStrategy.INTERPOLATE,
        requires_api_key=False,
        rate_limit_delay=5.0,
        max_history_months=60,
        is_active=False,  # BLOCKED - IP rate limiting
        notes="BLOCKED: pytrends scraping blocked from data centers"
    ),
    
    # =========================================================================
    # LAYER 2: MEDIUM (Market/Operational Signals)
    # =========================================================================
    "alpha_vantage": DataSourceConfig(
        name="alpha_vantage",
        display_name="Stock Prices",
        layer=SignalLayer.MEDIUM,
        update_frequency=UpdateFrequency.DAILY,
        fill_strategy=FillStrategy.INTERPOLATE,
        requires_api_key=True,
        api_key_env_var="ALPHA_VANTAGE_API_KEY",
        rate_limit_delay=12.0,  # 5 calls/min on free tier
        max_history_months=300,  # 25 years available
        notes="Free tier: 5 API calls/min, 500/day"
    ),
    
    "fred": DataSourceConfig(
        name="fred",
        display_name="FRED Economic Data",
        layer=SignalLayer.MEDIUM,
        update_frequency=UpdateFrequency.MONTHLY,
        fill_strategy=FillStrategy.INTERPOLATE,
        requires_api_key=True,
        api_key_env_var="FRED_API_KEY",
        rate_limit_delay=0.5,
        max_history_months=300,  # Decades available
        notes="800,000+ economic time series. Free API key required."
    ),
    
    "arxiv": DataSourceConfig(
        name="arxiv",
        display_name="arXiv Papers",
        layer=SignalLayer.MEDIUM,
        update_frequency=UpdateFrequency.DAILY,
        fill_strategy=FillStrategy.INTERPOLATE,
        requires_api_key=False,
        rate_limit_delay=3.0,
        max_history_months=60,
        notes="Research paper counts by topic. Free, rate-limited."
    ),
    
    "clinicaltrials": DataSourceConfig(
        name="clinicaltrials",
        display_name="Clinical Trials",
        layer=SignalLayer.MEDIUM,
        update_frequency=UpdateFrequency.WEEKLY,
        fill_strategy=FillStrategy.FORWARD_FILL,
        requires_api_key=False,
        rate_limit_delay=1.0,
        max_history_months=60,
        notes="ClinicalTrials.gov API. Trial counts by condition."
    ),
    
    "usgs": DataSourceConfig(
        name="usgs",
        display_name="USGS Earthquakes",
        layer=SignalLayer.MEDIUM,
        update_frequency=UpdateFrequency.DAILY,
        fill_strategy=FillStrategy.FORWARD_FILL,
        requires_api_key=False,
        rate_limit_delay=0.5,
        max_history_months=300,
        notes="Earthquake counts/magnitudes. 100+ years available."
    ),
    
    "usgs_enhanced": DataSourceConfig(
        name="usgs_enhanced",
        display_name="USGS Earthquakes (Enhanced)",
        layer=SignalLayer.MEDIUM,
        update_frequency=UpdateFrequency.DAILY,
        fill_strategy=FillStrategy.FORWARD_FILL,
        requires_api_key=False,
        rate_limit_delay=0.5,
        max_history_months=300,
        notes="Count, avg magnitude, max magnitude by month."
    ),
    
    "nasa_eonet": DataSourceConfig(
        name="nasa_eonet",
        display_name="NASA Environmental Events",
        layer=SignalLayer.MEDIUM,
        update_frequency=UpdateFrequency.DAILY,
        fill_strategy=FillStrategy.FORWARD_FILL,
        requires_api_key=False,
        rate_limit_delay=1.0,
        max_history_months=60,
        notes="Wildfires, storms, volcanoes by category."
    ),
    
    # =========================================================================
    # LAYER 3: SLOW (Structural Signals)
    # =========================================================================
    "worldbank": DataSourceConfig(
        name="worldbank",
        display_name="World Bank (GDP)",
        layer=SignalLayer.SLOW,
        update_frequency=UpdateFrequency.ANNUAL,
        fill_strategy=FillStrategy.FORWARD_FILL,
        requires_api_key=False,
        rate_limit_delay=1.0,
        max_history_months=240,  # 20 years
        notes="GDP, population, emissions by country. Annual data."
    ),
}


def get_source_config(source_name: str) -> Optional[DataSourceConfig]:
    """Get configuration for a data source"""
    return DATA_SOURCES.get(source_name)


def get_active_sources() -> List[DataSourceConfig]:
    """Get all active data sources"""
    return [s for s in DATA_SOURCES.values() if s.is_active]


def get_sources_by_layer(layer: SignalLayer) -> List[DataSourceConfig]:
    """Get all sources in a specific temporal layer"""
    return [s for s in DATA_SOURCES.values() if s.layer == layer and s.is_active]


def get_fill_strategy(source_name: str) -> str:
    """Get fill strategy for a source (returns string for compatibility)"""
    config = get_source_config(source_name)
    if config:
        return config.fill_strategy.value
    return FillStrategy.FORWARD_FILL.value


def validate_data_source(source_name: str) -> Dict[str, Any]:
    """
    Validate a data source is properly configured.
    Returns dict with validation status and any issues.
    """
    import os
    
    config = get_source_config(source_name)
    if not config:
        return {
            "valid": False,
            "source": source_name,
            "error": f"Unknown source: {source_name}"
        }
    
    issues = []
    
    # Check API key if required
    if config.requires_api_key and config.api_key_env_var:
        if not os.getenv(config.api_key_env_var):
            issues.append(f"Missing API key: {config.api_key_env_var}")
    
    # Check if source is active
    if not config.is_active:
        issues.append(f"Source is disabled: {config.notes}")
    
    return {
        "valid": len(issues) == 0,
        "source": source_name,
        "config": {
            "layer": config.layer.name,
            "frequency": config.update_frequency.value,
            "fill_strategy": config.fill_strategy.value,
            "max_history": f"{config.max_history_months} months"
        },
        "issues": issues
    }


def print_data_universe_summary():
    """Print a summary of the data universe configuration"""
    print("\n" + "=" * 70)
    print("DATA UNIVERSE SUMMARY")
    print("=" * 70)
    
    for layer in SignalLayer:
        sources = get_sources_by_layer(layer)
        if sources:
            print(f"\n{layer.name} (Layer {layer.value}):")
            print("-" * 40)
            for s in sources:
                status = "✅" if s.is_active else "❌"
                key_status = "🔑" if s.requires_api_key else "🆓"
                print(f"  {status} {key_status} {s.display_name}")
                print(f"       Fill: {s.fill_strategy.value}, History: {s.max_history_months}mo")
    
    print("\n" + "=" * 70)
    total = len([s for s in DATA_SOURCES.values() if s.is_active])
    print(f"Total Active Sources: {total}")
    print("=" * 70 + "\n")


# ==============================================================================
# STANDARD GRID CONFIGURATION
# ==============================================================================
# All data sources normalize to this standard grid for consistency

STANDARD_GRID_CONFIG = {
    "frequency": "monthly",
    "day_of_month": 1,          # First of month
    "default_history_months": 60,  # 5 years default
    "max_history_months": 300,  # 25 years max
    "timezone": "UTC"
}


if __name__ == "__main__":
    print_data_universe_summary()
    
    print("\nValidating all sources...")
    for source_name in DATA_SOURCES:
        result = validate_data_source(source_name)
        status = "✅" if result["valid"] else "❌"
        print(f"  {status} {source_name}")
        for issue in result.get("issues", []):
            print(f"       ⚠️  {issue}")
