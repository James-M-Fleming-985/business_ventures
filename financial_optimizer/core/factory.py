"""
Use case factory for creating use-case-specific instances.
This handles the dynamic loading of features based on configuration.
"""

from typing import Dict, Any, List, Optional, Type, Union
from core.config import UseCase, get_config_for_use_case, is_feature_enabled
import importlib


class UseCaseFactory:
    """Factory for creating use-case-specific components."""

    def __init__(self, use_case: UseCase):
        self.use_case = use_case
        self.config = get_config_for_use_case(use_case)

    def create_layout(self) -> Any:
        """Create the layout for this use case."""
        # Import the appropriate layout module based on use case
        try:
            if self.use_case == UseCase.BUSINESS:
                from use_cases.business.layout import create_business_layout

                return create_business_layout()
            elif self.use_case == UseCase.PERSONAL:
                from use_cases.personal.layout import create_personal_layout

                return create_personal_layout()
            elif self.use_case == UseCase.CHARITY:
                from use_cases.charity.layout import create_charity_layout

                return create_charity_layout()
            elif self.use_case == UseCase.NON_PROFIT:
                from use_cases.non_profit.layout import create_nonprofit_layout

                return create_nonprofit_layout()
            else:
                # Fallback to basic layout
                from shared.layout_new import create_layout

                return create_layout()
        except ImportError:
            # If use case specific layout not found, use fallback
            from dash import html
            import dash_bootstrap_components as dbc

            return html.Div(
                [
                    dbc.Alert(
                        f"Layout for {self.use_case.value} use case is not yet implemented.",
                        color="warning",
                        className="m-3",
                    )
                ]
            )

    def register_callbacks(self, app: Any) -> None:
        """Register callbacks for this use case."""
        # Import and register use-case-specific callbacks
        try:
            if self.use_case == UseCase.BUSINESS:
                from use_cases.business.callbacks import register_business_callbacks

                register_business_callbacks(app, self.config)
            elif self.use_case == UseCase.PERSONAL:
                from use_cases.personal.callbacks import register_personal_callbacks

                register_personal_callbacks(app, self.config)
            elif self.use_case == UseCase.CHARITY:
                from use_cases.charity.callbacks import register_charity_callbacks

                register_charity_callbacks(app, self.config)
            elif self.use_case == UseCase.NON_PROFIT:
                from use_cases.non_profit.callbacks import register_nonprofit_callbacks

                register_nonprofit_callbacks(app, self.config)
        except ImportError as e:
            print(
                f"Warning: Could not register callbacks for {self.use_case.value}: {e}"
            )

    def get_data_processor(self) -> Any:
        """Get the data processor for this use case."""
        try:
            if self.use_case == UseCase.BUSINESS:
                from use_cases.business.data_processor import BusinessDataProcessor

                return BusinessDataProcessor(self.config)
            elif self.use_case == UseCase.PERSONAL:
                from use_cases.personal.data_processor import PersonalDataProcessor

                return PersonalDataProcessor(self.config)
            elif self.use_case == UseCase.CHARITY:
                from use_cases.charity.data_processor import CharityDataProcessor

                return CharityDataProcessor(self.config)
            elif self.use_case == UseCase.NON_PROFIT:
                from use_cases.non_profit.data_processor import NonProfitDataProcessor

                return NonProfitDataProcessor(self.config)
        except ImportError:
            # Return a generic processor if specific one not found
            return None

    def get_algorithm_suite(self) -> Any:
        """Get the algorithm suite for this use case."""
        try:
            if self.use_case == UseCase.BUSINESS:
                from use_cases.business.algorithms import BusinessAlgorithms

                return BusinessAlgorithms(self.config)
            elif self.use_case == UseCase.PERSONAL:
                from use_cases.personal.algorithms import PersonalAlgorithms

                return PersonalAlgorithms(self.config)
            elif self.use_case == UseCase.CHARITY:
                from use_cases.charity.algorithms import CharityAlgorithms

                return CharityAlgorithms(self.config)
            elif self.use_case == UseCase.NON_PROFIT:
                from use_cases.non_profit.algorithms import NonProfitAlgorithms

                return NonProfitAlgorithms(self.config)
        except ImportError:
            # Return a generic algorithm suite if specific one not found
            return None

    def is_feature_available(self, feature: str) -> bool:
        """Check if a feature is available in this use case."""
        return is_feature_enabled(self.use_case, feature)


def create_use_case_instance(use_case: UseCase) -> UseCaseFactory:
    """Create a use case factory instance."""
    return UseCaseFactory(use_case)
