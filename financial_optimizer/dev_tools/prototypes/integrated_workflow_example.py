#!/usr/bin/env python3
"""
Complete Application Integration
Shows how Data Input workflow integrates with Investment Management
"""

from dash import Dash, html, dcc, Input, Output, State, callback
import dash_bootstrap_components as dbc
from data_input_workflow import create_data_input_tab
from investment_management_workflow import create_investment_management_tab

# Create the app
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP],
           suppress_callback_exceptions=True)

# Main application layout
app.layout = html.Div([
    dbc.Container([
        html.H1("Financial Optimizer - Integrated Workflow",
                className="text-center mb-4"),

        # Navigation tabs
        dbc.Tabs([
            dbc.Tab(
                label="Data Input",
                tab_id="data-input",
                children=[create_data_input_tab()]
            ),
            dbc.Tab(
                label="Investment Management",
                tab_id="investment-management",
                children=[create_investment_management_tab()]
            )
        ], id="main-tabs", active_tab="data-input"),

        # Data store for cross-tab communication
        dcc.Store(id="uploaded-data-store"),
        dcc.Store(id="business-model-store"),
        dcc.Store(id="investments-store")
    ])
])

# Example usage demonstration


def demonstrate_workflow():
    """Demonstrate the proposed workflow with examples."""
    return html.Div([
        dbc.Alert([
            html.H4("Your Proposed Workflow in Action:",
                    className="alert-heading"),
            html.Hr(),
            html.P("1. Data Input Tab → Select 'Cost Center' business model"),
            html.P(
                "2. Investment type boxes appear (Capital Equipment, Process Improvement, etc.)"),
            html.P("3. Click 'Capital Equipment' box → Opens detailed form"),
            html.P(
                "4. Upload OEE data file OR enter: Current OEE 65%, Target 85%, Labor Rate £25/hr"),
            html.P(
                "5. Click 'Process Improvement' → Upload cycle time data OR enter manually"),
            html.P("6. Investment Management Tab → Shows available investment types"),
            html.P(
                "7. Create investment → 'Equipment Upgrade' using Capital Equipment data"),
            html.P(
                "8. Calculate → Uses Cost Center methodology: £87,500 annual savings"),
            html.Hr(),
            html.P("✅ Each investment type has its own data requirements"),
            html.P("✅ Business model (Cost/Profit Center) drives calculation method"),
            html.P("✅ Clean separation between data input and analysis"),
            html.P("✅ Scalable - easy to add new investment types")
        ], color="success")
    ])


if __name__ == '__main__':
    # Add demonstration to the layout for testing
    app.layout.children[0].children.append(demonstrate_workflow())
    app.run_server(debug=True, port=8052)
