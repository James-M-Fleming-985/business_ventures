"""
Configuration system for managing different use cases.
This will handle feature flags and use-case-specific settings.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum


class UseCase(Enum):
    """Available use cases for the financial optimizer."""

    BUSINESS = "business"
    PERSONAL = "personal"
    CHARITY = "charity"
    NON_PROFIT = "non_profit"


@dataclass
class UseCaseConfig:
    """Configuration for a specific use case."""

    use_case: UseCase
    enabled_features: List[str]
    tab_layout: List[str]
    default_metrics: List[str]
    data_sources: List[str]
    algorithms: List[str]
    subscription_tier: Optional[str] = None


# Development configuration - this will be replaced by subscription logic later
DEVELOPMENT_CONFIG = {
    UseCase.BUSINESS: UseCaseConfig(
        use_case=UseCase.BUSINESS,
        enabled_features=[
            "oee_tracking",
            "production_analysis",
            "department_budgets",
            "capital_equipment",
            "process_improvement",
            "staff_management",
            "ebitda_analysis",
        ],
        tab_layout=[
            "dashboard",
            "data_input",
            "investment_mgmt",
            "financial_statements",
            "reports",
        ],
        default_metrics=[
            "department_contribution",
            "ebitda",
            "departmental_savings",
            "production_efficiency",
        ],
        data_sources=["production_data", "accounting_systems", "erp_integration"],
        algorithms=["oee_calculation", "capital_depreciation", "productivity_modeling"],
        subscription_tier="business_pro",
    ),
    UseCase.PERSONAL: UseCaseConfig(
        use_case=UseCase.PERSONAL,
        enabled_features=[
            "investment_tracking",
            "market_data",
            "portfolio_analysis",
            "tax_optimization",
            "retirement_planning",
            "ml_recommendations",
        ],
        tab_layout=[
            "dashboard",
            "data_input",
            "investment_mgmt",
            "investment_analysis",
            "market_dashboard",
            "reports",
        ],
        default_metrics=[
            "net_worth",
            "cash_flow",
            "investment_returns",
            "savings_rate",
        ],
        data_sources=["market_feeds", "bank_apis", "investment_platforms"],
        algorithms=["portfolio_optimization", "risk_assessment", "ml_predictions"],
        subscription_tier="personal_premium",
    ),
    UseCase.CHARITY: UseCaseConfig(
        use_case=UseCase.CHARITY,
        enabled_features=[
            "donation_tracking",
            "grant_management",
            "impact_measurement",
            "compliance_reporting",
            "volunteer_management",
        ],
        tab_layout=[
            "dashboard",
            "donations",
            "grants",
            "impact_analysis",
            "compliance",
            "reports",
        ],
        default_metrics=[
            "funds_raised",
            "program_efficiency",
            "impact_per_dollar",
            "donor_retention",
        ],
        data_sources=["donation_platforms", "grant_databases", "impact_tracking"],
        algorithms=["impact_calculation", "donor_analysis", "program_optimization"],
        subscription_tier="charity_standard",
    ),
    UseCase.NON_PROFIT: UseCaseConfig(
        use_case=UseCase.NON_PROFIT,
        enabled_features=[
            "budget_management",
            "fund_allocation",
            "program_tracking",
            "outcome_measurement",
            "stakeholder_reporting",
        ],
        tab_layout=[
            "dashboard",
            "budgets",
            "programs",
            "outcomes",
            "stakeholders",
            "compliance",
        ],
        default_metrics=[
            "program_spend",
            "outcome_efficiency",
            "stakeholder_satisfaction",
            "mission_impact",
        ],
        data_sources=["accounting_systems", "program_data", "outcome_tracking"],
        algorithms=["outcome_modeling", "budget_optimization", "impact_attribution"],
        subscription_tier="nonprofit_professional",
    ),
}


def get_config_for_use_case(use_case: UseCase) -> UseCaseConfig:
    """Get configuration for a specific use case."""
    return DEVELOPMENT_CONFIG[use_case]


def get_enabled_features(use_case: UseCase) -> List[str]:
    """Get enabled features for a use case."""
    config = get_config_for_use_case(use_case)
    return config.enabled_features


def get_tab_layout(use_case: UseCase) -> List[str]:
    """Get tab layout for a use case."""
    config = get_config_for_use_case(use_case)
    return config.tab_layout


def is_feature_enabled(use_case: UseCase, feature: str) -> bool:
    """Check if a feature is enabled for a use case."""
    enabled_features = get_enabled_features(use_case)
    return feature in enabled_features


def get_default_metrics(use_case: UseCase) -> List[str]:
    """Get default metrics for a use case."""
    config = get_config_for_use_case(use_case)
    return config.default_metrics


# Development toggle - this will be replaced by subscription verification later
DEVELOPMENT_MODE = True
CURRENT_USE_CASE = UseCase.BUSINESS  # Toggle this during development

# Global variable to track current use case during development
_current_use_case = UseCase.BUSINESS


def get_current_use_case() -> UseCase:
    """Get the current use case (development mode)."""
    if DEVELOPMENT_MODE:
        return _current_use_case
    else:
        # This is where subscription logic would go
        # return get_use_case_from_subscription(user_id)
        return UseCase.PERSONAL  # Default fallback


def set_current_use_case(use_case: UseCase) -> None:
    """Set the current use case (development mode only)."""
    global _current_use_case
    if DEVELOPMENT_MODE:
        _current_use_case = use_case
        print(f"🔄 Use case switched to: {use_case.value}")


def get_current_use_case_from_string(use_case_string: str) -> UseCase:
    """Convert string to UseCase enum and set as current."""
    use_case = UseCase(use_case_string)
    set_current_use_case(use_case)
    return use_case
