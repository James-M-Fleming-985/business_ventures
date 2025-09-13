#!/usr/bin/env python3
"""
Test script for Personal Mode Manual Entry System
"""

import dash
from dash import html
import dash_bootstrap_components as dbc
from modules.personal_mode.main import create_personal_mode_layout, register_personal_mode_callbacks

# Create Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Set up the layout
app.layout = html.Div([
    html.H1("Financial Optimizer - Personal Mode Test", className="mb-4"),
    create_personal_mode_layout()
])

# Register the callbacks
register_personal_mode_callbacks(app)

if __name__ == '__main__':
    print("🚀 Starting Personal Mode Test Server...")
    print("📊 Testing Enhanced Financial Dashboard")
    print("🔗 Open: http://localhost:8054")
    print("✅ Navigate to 'Data Input' tab to test manual entry")
    print("📈 Navigate to 'Financial Dashboard' tab to see interactive charts")

    app.run_server(debug=True, host='0.0.0.0', port=8054)
