"""
Base application class that provides the foundation for all use cases.
This implements the recommended architecture restructure.
"""

import dash
from dash import Dash, html, dcc, Input, Output, State
import dash_bootstrap_components as dbc
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod

from .config import UseCase, UseCaseConfig, get_current_use_case, get_config_for_use_case


class BaseFinancialApp(ABC):
    """
    Base class for all financial optimizer applications.
    This provides the common foundation that all use cases inherit from.
    """

    def __init__(self, use_case: UseCase, config: UseCaseConfig):
        self.use_case = use_case
        self.config = config
        self.app = Dash(
            __name__,
            external_stylesheets=[dbc.themes.BOOTSTRAP],
            suppress_callback_exceptions=True,
        )
        self._setup_app()

    def _setup_app(self):
        """Setup the basic app structure."""
        self.app.layout = self._create_layout()
        self._register_callbacks()

    def _create_layout(self) -> html.Div:
        """Create the main layout structure."""
        return html.Div([
            self._create_header(),
            self._create_navigation(),
            self._create_content_area(),
            self._create_footer(),
        ])

    def _create_header(self) -> html.Div:
        """Create the header with use case specific branding."""
        title = self._get_app_title()
        return html.Div([
            html.H1(title, className="app-title"),
            html.P(self._get_app_description(), className="app-description"),
        ], className="app-header")

    def _create_navigation(self) -> html.Div:
        """Create navigation tabs based on use case configuration."""
        tabs = []
        for tab_id in self.config.tab_layout:
            tab_config = self._get_tab_config(tab_id)
            if tab_config:
                tabs.append(
                    dbc.Tab(
                        label=tab_config["label"],
                        tab_id=tab_id,
                        active_label_style={"color": "#007bff"},
                    )
                )

        return dbc.Tabs(
            tabs,
            id="main-tabs",
            active_tab=self.config.tab_layout[0] if self.config.tab_layout else "dashboard",
            className="mb-3",
        )

    def _create_content_area(self) -> html.Div:
        """Create the main content area."""
        return html.Div(
            id="page-content",
            className="content-area",
            children=[
                dcc.Store(id="current-use-case", data=self.use_case.value),
                dcc.Store(id="app-state", data={}),
                html.Div(id="tab-content"),
            ]
        )

    def _create_footer(self) -> html.Div:
        """Create the footer."""
        return html.Div([
            html.P(f"© 2025 Financial Optimizer - {self.use_case.value.title()} Edition",
                   className="footer-text"),
        ], className="app-footer")

    def _register_callbacks(self):
        """Register all callbacks for this application."""
        self._register_navigation_callbacks()
        self._register_use_case_callbacks()
        self._register_custom_callbacks()

    def _register_navigation_callbacks(self):
        """Register navigation callbacks."""
        @self.app.callback(
            Output("tab-content", "children"),
            Input("main-tabs", "active_tab"),
            prevent_initial_call=False,
        )
        def render_tab_content(active_tab):
            if active_tab:
                return self._render_tab_content(active_tab)
            return html.Div("Select a tab to view content.")

    def _register_use_case_callbacks(self):
        """Register use case specific callbacks."""
        pass  # Override in subclasses

    @abstractmethod
    def _register_custom_callbacks(self):
        """Register custom callbacks for specific use cases."""
        pass

    @abstractmethod
    def _get_app_title(self) -> str:
        """Get the title for this use case."""
        pass

    @abstractmethod
    def _get_app_description(self) -> str:
        """Get the description for this use case."""
        pass

    @abstractmethod
    def _get_tab_config(self, tab_id: str) -> Optional[Dict[str, Any]]:
        """Get configuration for a specific tab."""
        pass

    @abstractmethod
    def _render_tab_content(self, tab_id: str) -> html.Div:
        """Render content for a specific tab."""
        pass

    def run(self, debug: bool = True, port: int = 8050):
        """Run the application."""
        print(f"🚀 Starting {self.use_case.value.title()} Financial Optimizer")
        print(f"📊 Features: {', '.join(self.config.enabled_features)}")
        print(f"🌐 Access at: http://localhost:{port}")
        self.app.run(debug=debug, port=port)


class DevelopmentApp(BaseFinancialApp):
    """
    Development version that allows switching between use cases.
    This is what we'll use for testing and development.
    """

    def __init__(self):
        # Start with business use case as default
        current_use_case = get_current_use_case()
        current_config = get_config_for_use_case(current_use_case)
        super().__init__(current_use_case, current_config)

    def _create_header(self) -> html.Div:
        """Create header with development controls."""
        base_header = super()._create_header()
        
        # Add development controls
        dev_controls = dbc.Alert([
            html.H6("🔧 Development Mode", className="mb-2"),
            html.P("Switch between use cases:", className="mb-2"),
            dcc.RadioItems(
                id="use-case-switcher",
                options=[
                    {"label": "🏢 Business Mode", "value": "business"},
                    {"label": "🏠 Personal Finance", "value": "personal"},
                    {"label": "❤️ Charity", "value": "charity"},
                    {"label": "🏛️ Non-Profit", "value": "non_profit"},
                ],
                value=self.use_case.value,
                inline=True,
                className="mb-2",
            ),
            html.Small("Switch to see different layouts and features", className="text-muted"),
        ], color="info", className="mb-3")

        return html.Div([dev_controls, base_header])

    def _register_use_case_callbacks(self):
        """Register development use case switching callbacks."""
        @self.app.callback(
            [
                Output("current-use-case", "data"),
                Output("main-tabs", "children"),
                Output("main-tabs", "active_tab"),
                Output("app-state", "data"),
            ],
            Input("use-case-switcher", "value"),
            prevent_initial_call=True,
        )
        def switch_use_case(selected_use_case):
            if selected_use_case:
                from .config import set_current_use_case
                
                # Update the global use case
                new_use_case = UseCase(selected_use_case)
                set_current_use_case(new_use_case)
                
                # Update app configuration
                self.use_case = new_use_case
                self.config = get_config_for_use_case(new_use_case)
                
                print(f"🔄 Switched to: {selected_use_case}")
                print(f"📋 Features: {', '.join(self.config.enabled_features)}")
                
                # Rebuild tabs
                new_tabs = []
                for tab_id in self.config.tab_layout:
                    tab_config = self._get_tab_config(tab_id)
                    if tab_config:
                        new_tabs.append(
                            dbc.Tab(
                                label=tab_config["label"],
                                tab_id=tab_id,
                                active_label_style={"color": "#007bff"},
                            )
                        )
                
                return (
                    selected_use_case,
                    new_tabs,
                    self.config.tab_layout[0] if self.config.tab_layout else "dashboard",
                    {"use_case": selected_use_case, "config": self.config.enabled_features}
                )
            return dash.no_update, dash.no_update, dash.no_update, dash.no_update

    def _register_custom_callbacks(self):
        """Development app doesn't need custom callbacks."""
        pass

    def _get_app_title(self) -> str:
        """Get title based on current use case."""
        titles = {
            UseCase.BUSINESS: "Business Financial Optimizer",
            UseCase.PERSONAL: "Personal Finance Manager",
            UseCase.CHARITY: "Charity Financial Tracker",
            UseCase.NON_PROFIT: "Non-Profit Financial Manager",
        }
        return titles.get(self.use_case, "Financial Optimizer")

    def _get_app_description(self) -> str:
        """Get description based on current use case."""
        descriptions = {
            UseCase.BUSINESS: "Comprehensive business financial analysis and optimization",
            UseCase.PERSONAL: "Personal investment tracking and financial planning",
            UseCase.CHARITY: "Donation tracking and impact measurement",
            UseCase.NON_PROFIT: "Grant management and compliance reporting",
        }
        return descriptions.get(self.use_case, "Financial optimization platform")

    def _get_tab_config(self, tab_id: str) -> Optional[Dict[str, Any]]:
        """Get tab configuration for any use case."""
        tab_configs = {
            "dashboard": {"label": "📊 Dashboard", "icon": "📊"},
            "data_input": {"label": "📝 Data Input", "icon": "📝"},
            "investment_mgmt": {"label": "💰 Investment Management", "icon": "💰"},
            "investment_analysis": {"label": "📈 Investment Analysis", "icon": "📈"},
            "financial_statements": {"label": "📋 Financial Statements", "icon": "📋"},
            "market_dashboard": {"label": "📊 Market Dashboard", "icon": "📊"},
            "market_analysis": {"label": "📊 Market Analysis", "icon": "📊"},
            "reports": {"label": "📄 Reports", "icon": "📄"},
            "planning": {"label": "🎯 Planning", "icon": "🎯"},
            "compliance": {"label": "✅ Compliance", "icon": "✅"},
            "grants": {"label": "💵 Grants", "icon": "💵"},
            "donations": {"label": "❤️ Donations", "icon": "❤️"},
            "impact": {"label": "🎯 Impact", "icon": "🎯"},
            "volunteers": {"label": "👥 Volunteers", "icon": "👥"},
        }
        return tab_configs.get(tab_id)

    def _render_tab_content(self, tab_id: str) -> html.Div:
        """Render content for any tab based on current use case."""
        content = html.Div([
            html.H3(f"{tab_id.replace('_', ' ').title()} - {self.use_case.value.title()} Mode"),
            html.P(f"This is the {tab_id} content for {self.use_case.value} use case."),
            html.Div([
                html.H5("Available Features:"),
                html.Ul([
                    html.Li(feature.replace('_', ' ').title()) 
                    for feature in self.config.enabled_features
                ]),
            ]),
            html.Div([
                html.H5("Configuration:"),
                html.Pre(f"Use Case: {self.use_case.value}\n" + 
                        f"Tab Layout: {self.config.tab_layout}\n" + 
                        f"Metrics: {self.config.default_metrics}\n" + 
                        f"Data Sources: {self.config.data_sources}")
            ]),
        ])
        
        return content
