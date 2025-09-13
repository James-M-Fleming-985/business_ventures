"""
Financial Optimizer Application - Clean Baseline Architecture
This uses the working simple approach with essential features added back.
"""

import dash
from dash import Dash, html, dcc, callback, Input, Output
import dash_bootstrap_components as dbc

# Use case layouts
from use_cases.business.layout import create_business_layout
from use_cases.personal.layout import create_personal_layout
from use_cases.charity.layout import create_charity_layout
from use_cases.non_profit.layout import create_nonprofit_layout

# Initialize the Dash application
app = Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        "https://use.fontawesome.com/releases/v5.15.4/css/all.css",
    ],
    suppress_callback_exceptions=True,
)

# Application layout
app.layout = html.Div(
    [
        # Development Mode Controls
        dbc.Alert(
            [
                html.H6("🔧 Development Mode", className="mb-2"),
                html.P("Toggle between use cases for development:", className="mb-2"),
                dcc.RadioItems(
                    id="dev-use-case-selector",
                    options=[
                        {"label": "🏢 Business Mode", "value": "business"},
                        {"label": "🏠 Personal Finance", "value": "personal"},
                        {"label": "❤️ Charity", "value": "charity"},
                        {"label": "🏛️ Non-Profit", "value": "non_profit"},
                    ],
                    value="business",
                    inline=True,
                    className="mb-2",
                ),
                html.Small(
                    "This will be replaced by subscription logic in production.",
                    className="text-muted",
                ),
            ],
            color="info",
            className="mb-3",
        ),
        # Data stores
        dcc.Store(id="financial-data-store"),
        dcc.Store(id="projection-results-store"),
        dcc.Store(id="use-case-store", data="business"),
        # Dynamic content area
        html.Div(id="dynamic-content"),
    ]
)


@callback(
    [Output("dynamic-content", "children"), Output("use-case-store", "data")],
    Input("dev-use-case-selector", "value"),
)
def update_use_case_content(selected_use_case):
    """Update content based on selected use case."""
    print(f"🔄 Switching to use case: {selected_use_case}")

    if not selected_use_case:
        selected_use_case = "business"

    # Create layout based on use case
    try:
        if selected_use_case == "business":
            layout = create_business_layout()
        elif selected_use_case == "personal":
            layout = create_personal_layout()
        elif selected_use_case == "charity":
            layout = create_charity_layout()
        elif selected_use_case == "non_profit":
            layout = create_nonprofit_layout()
        else:
            layout = html.Div(
                [dbc.Alert(f"Unknown use case: {selected_use_case}", color="danger")]
            )

        print(f"📄 Layout created successfully for: {selected_use_case}")
        return layout, selected_use_case

    except Exception as e:
        print(f"❌ Error creating layout for {selected_use_case}: {e}")
        return (
            html.Div(
                [
                    dbc.Alert(
                        f"Error loading {selected_use_case}: {str(e)}", color="danger"
                    )
                ]
            ),
            selected_use_case,
        )


if __name__ == "__main__":
    print("🚀 Starting Financial Optimizer - Clean Baseline")
    print("📊 Development Mode: True")
    print("🔍 Available Use Cases: ['business', 'personal', 'charity', 'non_profit']")
    print("🌐 Access the application at: http://localhost:8053")

    app.run(debug=True, port=8053)
