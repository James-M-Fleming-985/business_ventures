"""
Simple test to isolate the dropdown issue.
"""

import dash
from dash import Dash, html, dcc, callback, Input, Output
import dash_bootstrap_components as dbc

# Initialize the Dash application
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Simple layout with just the dropdown
app.layout = html.Div(
    [
        html.H1("Simple Test"),
        html.Div(
            [
                html.Label("Select Use Case:"),
                dcc.RadioItems(
                    id="test-selector",
                    options=[
                        {"label": "🏢 Business Mode", "value": "business"},
                        {"label": "🏠 Personal Finance", "value": "personal"},
                        {"label": "❤️ Charity", "value": "charity"},
                        {"label": "🏛️ Non-Profit", "value": "non_profit"},
                    ],
                    value="business",
                    inline=True,
                ),
            ]
        ),
        html.Hr(),
        html.Div(id="test-output"),
    ]
)


@callback(Output("test-output", "children"), Input("test-selector", "value"))
def update_output(value):
    return f"Selected: {value}"


if __name__ == "__main__":
    print("🧪 Running simple test on http://localhost:8051")
    app.run(debug=True, port=8051)
