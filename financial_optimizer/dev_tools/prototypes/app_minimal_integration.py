"""
Minimal integration approach - just add use case switching to your existing app.py
This creates a thin wrapper that preserves all your existing functionality.
"""

import dash
from dash import Dash, html, dcc, Input, Output, State
import dash_bootstrap_components as dbc
from typing import Dict, Any, Optional

# Import your existing app
import sys

sys.path.append(".")

# Import the core use case system
from core.config import (
    UseCase,
    get_current_use_case,
    DEVELOPMENT_MODE,
    set_current_use_case,
)

# Create a new minimal app that wraps your existing functionality
app = Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    suppress_callback_exceptions=True,
)


def create_minimal_layout():
    """Create a minimal layout that just adds use case switching."""

    # Get current use case
    current_use_case = get_current_use_case()

    # Development mode selector
    development_controls = html.Div()
    if DEVELOPMENT_MODE:
        development_controls = dbc.Alert(
            [
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
                    value=current_use_case.value,
                    inline=True,
                    className="mb-2",
                ),
                html.Small(
                    "Use case switching enabled - your original app is below.",
                    className="text-muted",
                ),
            ],
            color="info",
            className="mb-3",
        )

    # Import and use your existing layout
    from shared.layout_new import create_layout

    original_layout = create_layout()

    return html.Div(
        [
            development_controls,
            dcc.Store(id="current-use-case", data=current_use_case.value),
            html.Div(id="main-content", children=original_layout),
        ]
    )


app.layout = create_minimal_layout()

# Minimal use case switching callback
if DEVELOPMENT_MODE:

    @app.callback(
        [
            Output("current-use-case", "data"),
            Output("main-content", "children", allow_duplicate=True),
        ],
        Input("use-case-switcher", "value"),
        prevent_initial_call=True,
    )
    def switch_use_case(selected_use_case):
        """Switch the use case and refresh the layout."""
        if selected_use_case:
            # Update the global use case
            use_case = UseCase(selected_use_case)
            set_current_use_case(use_case)
            print(f"🔄 Use case switched to: {selected_use_case}")

            # Get use case configuration
            from core.config import get_config_for_use_case

            config = get_config_for_use_case(use_case)
            print(f"📋 New config - Features: {config.enabled_features}")
            print(f"📋 New config - Tab layout: {config.tab_layout}")

            # Refresh the layout with the new use case
            from shared.layout_new import create_layout

            new_layout = create_layout()

            return selected_use_case, new_layout
        return dash.no_update, dash.no_update


# Import and register ALL your existing callbacks
from shared.error_handling import register_error_handling_callbacks
from modules.financial_dashboard.callbacks import register_financial_dashboard_callbacks
from shared.minimal_callbacks import register_minimal_callbacks

# Register all your existing callbacks
register_error_handling_callbacks(app)
register_financial_dashboard_callbacks(app)
register_minimal_callbacks(app)

# Import the rest of your callback registrations
from modules.investment_mgmt.callbacks import register_investment_mgmt_callbacks

register_investment_mgmt_callbacks(app)

if __name__ == "__main__":
    print("🚀 Starting MINIMAL Integration")
    print("📊 This preserves all your original functionality")
    print("🔧 Use case switching: Simple global configuration")
    print("🌐 Access at: http://localhost:8055")

    app.run(debug=True, port=8055)
