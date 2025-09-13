"""
Simplified baseline app to isolate the issue.
"""

import dash
from dash import Dash, html, dcc, callback, Input, Output
import dash_bootstrap_components as dbc

# Simple imports
from core.config import UseCase
from use_cases.business.layout import create_business_layout
from use_cases.personal.layout import create_personal_layout
from use_cases.charity.layout import create_charity_layout
from use_cases.non_profit.layout import create_nonprofit_layout

# Initialize the Dash application
app = Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    suppress_callback_exceptions=True,
)

# Simple layout
app.layout = html.Div(
    [
        # Development controls
        dbc.Alert(
            [
                html.H6("🔧 Development Mode"),
                html.Label("Select Use Case:"),
                dcc.RadioItems(
                    id="simple-use-case-selector",
                    options=[
                        {"label": "🏢 Business Mode", "value": "business"},
                        {"label": "🏠 Personal Finance", "value": "personal"},
                        {"label": "❤️ Charity", "value": "charity"},
                        {"label": "🏛️ Non-Profit", "value": "non_profit"},
                    ],
                    value="business",
                    inline=True,
                ),
            ],
            color="info",
            className="mb-3",
        ),
        # Content area
        html.Div(id="simple-content"),
    ]
)


@callback(
    Output("simple-content", "children"), Input("simple-use-case-selector", "value")
)
def update_content(selected_use_case):
    """Update content based on selected use case."""
    print(f"🔄 Switching to: {selected_use_case}")

    if selected_use_case == "business":
        return create_business_layout()
    elif selected_use_case == "personal":
        return create_personal_layout()
    elif selected_use_case == "charity":
        return create_charity_layout()
    elif selected_use_case == "non_profit":
        return create_nonprofit_layout()
    else:
        return html.Div("Unknown use case")


if __name__ == "__main__":
    print("🧪 Running simplified baseline on http://localhost:8052")
    app.run(debug=True, port=8052)
