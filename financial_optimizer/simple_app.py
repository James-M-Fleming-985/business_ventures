#!/usr/bin/env python3
"""
Financial Optimizer - COMPLETE MAIN APP with ALL FEATURES RESTORED

This version restores all original features (business, personal, charity, non-profit modes)
through the enhanced managed callback system to prevent conflicts while maintaining
all functionality from the previous commits.
"""

from dash import Dash, html
import dash_bootstrap_components as dbc

# Import the enhanced callback management system
from shared.enhanced_callbacks import EnhancedCallbackManager, register_all_callbacks

print("🚨 COMPLETE MAIN APP: Starting with ALL features restored...")

# Create the app
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP],
           suppress_callback_exceptions=True)

# Initialize enhanced callback manager
callback_manager = EnhancedCallbackManager(app)

# Register Personal Mode callbacks
try:
    from modules.personal_mode.callback_registration import register_personal_mode_callbacks
    register_personal_mode_callbacks()
except Exception as e:
    print(f"⚠️ Warning: Personal Mode callbacks not registered: {e}")

# COMPLETE LAYOUT with ALL ORIGINAL FEATURES
app.layout = html.Div([
    dbc.Container([
        html.H1("Financial Optimizer", className="text-center mb-4"),

        # Development Controls (restored original functionality)
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("Development Controls"),
                        html.P([
                            "Manual switching for development - ",
                            "will be subscription-based in production"
                        ], className="text-muted small"),
                        dbc.Select(
                            id="use-case-selector",
                            options=[
                                {"label": "Business", "value": "business"},
                                {"label": "Personal", "value": "personal"},
                                {"label": "Charity", "value": "charity"},
                                {"label": "Non-Profit", "value": "non_profit"},
                            ],
                            value="business",
                        ),
                        html.Hr(),
                        html.H6("🚨 DEBUG TEST"),
                        dbc.Button("TEST BUTTON - CLICK ME", id="test-button",
                                   color="danger", className="mt-2"),
                        html.Div("No clicks yet", id="test-output",
                                 className="mt-2"),
                    ])
                ])
            ], width=12, className="mb-4")
        ]),

        # MAIN TABS - ALL ORIGINAL MODES RESTORED
        html.Div(id="main-tabs"),

        # USE CASE CONTENT - Status and additional features
        html.Div(id="use-case-content", className="mt-4"),
    ])
])

# Register ALL callbacks including restored features
if __name__ == "__main__":
    print("🔥 REGISTERING ALL CALLBACKS (INCLUDING RESTORED FEATURES)...")
    callback_manager = register_all_callbacks(app, callback_manager)

    print("🔥 COMPLETE APP READY")
    print(f"🔥 Total callbacks registered: {len(callback_manager.registered_callbacks)}")

    # List all callbacks for debugging
    print("🔥 ALL REGISTERED CALLBACKS:")
    callback_manager.list_callbacks()

    print("Starting COMPLETE Financial Optimizer with ALL FEATURES...")
    app.run_server(debug=True, port=8050)
