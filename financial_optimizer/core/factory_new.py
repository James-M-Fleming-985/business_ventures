"""
Factory pattern for creating use case specific applications.
This implements the recommended architecture restructure.
"""

from typing import Dict, Type, Optional
from .config import UseCase, get_config_for_use_case
from .base_app import BaseFinancialApp, DevelopmentApp


class ApplicationFactory:
    """
    Factory for creating different types of financial applications.
    This follows the factory pattern to create use case specific apps.
    """

    @staticmethod
    def create_app(use_case: UseCase, development_mode: bool = False) -> BaseFinancialApp:
        """
        Create an application instance for the specified use case.
        
        Args:
            use_case: The use case to create an app for
            development_mode: Whether to create a development app with switching
            
        Returns:
            BaseFinancialApp: Application instance
        """
        if development_mode:
            return DevelopmentApp()
        
        # Get configuration for this use case
        config = get_config_for_use_case(use_case)
        
        # For now, we'll use the DevelopmentApp as our base implementation
        # Later, we can create specialized apps for each use case
        app_instance = DevelopmentApp()
        app_instance.use_case = use_case
        app_instance.config = config
        
        return app_instance

    @staticmethod
    def create_development_app() -> DevelopmentApp:
        """Create a development app with use case switching."""
        return DevelopmentApp()

    @staticmethod
    def get_available_use_cases() -> Dict[str, UseCase]:
        """Get all available use cases."""
        return {
            "business": UseCase.BUSINESS,
            "personal": UseCase.PERSONAL,
            "charity": UseCase.CHARITY,
            "non_profit": UseCase.NON_PROFIT,
        }


# Legacy factory for backward compatibility
class UseCaseFactory:
    """Factory for creating use-case-specific components."""

    def __init__(self, use_case: UseCase):
        self.use_case = use_case
        self.config = get_config_for_use_case(use_case)

    def create_layout(self) -> any:
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

            return html.Div([
                dbc.Alert(
                    f"Layout for {self.use_case.value} not implemented yet. Using fallback.",
                    color="warning"
                ),
                html.H3(f"{self.use_case.value.title()} Mode"),
                html.P("This layout is under development.")
            ])
