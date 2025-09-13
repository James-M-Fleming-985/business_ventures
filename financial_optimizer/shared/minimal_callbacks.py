"""
Simple callbacks for the minimal layout to get basic functionality working.
"""

from dash import html, Input, Output, State, callback_context
from dash.exceptions import PreventUpdate
import plotly.graph_objects as go
from shared.error_handling import collect_error, get_all_errors_list


def register_minimal_callbacks(app):
    """Register minimal callbacks for basic functionality."""

    # Error display callback
    @app.callback(
        Output("error-collection-display", "children"),
        Input("show-errors-btn", "n_clicks"),
        prevent_initial_call=True,
    )
    def show_errors(n_clicks):
        """Display collected errors."""
        if not n_clicks:
            raise PreventUpdate

        try:
            errors = get_all_errors_list()
            if not errors:
                return html.Div("✅ No errors found!", className="text-success")

            error_items = []
            for i, error in enumerate(errors):
                error_item = html.Div(
                    [
                        html.H6(
                            f"Error #{i+1}: {error.get('type', 'Unknown')}",
                            className="text-danger",
                        ),
                        html.P(f"Callback: {error.get('callback', 'Unknown')}"),
                        html.P(f"Message: {error.get('message', 'No message')}"),
                        html.P(f"Time: {error.get('time', 'Unknown')}"),
                        html.Hr(),
                    ],
                    className="mb-2",
                )
                error_items.append(error_item)

            return html.Div(error_items)

        except Exception as e:
            collect_error("show_errors")
            return html.Div(
                f"Error displaying errors: {str(e)}", className="text-danger"
            )

    # Clear errors callback
    @app.callback(
        Output("error-collection-display", "children", allow_duplicate=True),
        Input("clear-errors-btn", "n_clicks"),
        prevent_initial_call=True,
    )
    def clear_errors(n_clicks):
        """Clear all errors."""
        if not n_clicks:
            raise PreventUpdate

        try:
            from shared.error_handling import clear_errors

            clear_errors()
            return html.Div("✅ Errors cleared!", className="text-success")
        except Exception as e:
            return html.Div(f"Error clearing errors: {str(e)}", className="text-danger")

    # Basic investment calculation callback
    @app.callback(
        [
            Output("roi-display", "children"),
            Output("payback-display", "children"),
            Output("total-investment", "children"),
        ],
        [Input("investment-cost", "value"), Input("investment-savings", "value")],
        prevent_initial_call=True,
    )
    def calculate_investment_metrics(cost, savings):
        """Calculate basic investment metrics."""
        try:
            if not cost or not savings or cost <= 0 or savings <= 0:
                return "0%", "0 years", "£0"

            roi = (savings / cost) * 100
            payback_years = cost / savings

            return f"{roi:.1f}%", f"{payback_years:.1f} years", f"£{cost:,.0f}"

        except Exception as e:
            collect_error("calculate_investment_metrics")
            return "Error", "Error", "Error"

    # Basic financial metrics callback
    @app.callback(
        [
            Output("net-worth-metric", "children"),
            Output("cash-flow-metric", "children"),
            Output("growth-rate-metric", "children"),
        ],
        [
            Input("monthly-revenue", "value"),
            Input("monthly-expenses", "value"),
            Input("current-assets", "value"),
            Input("current-liabilities", "value"),
        ],
        prevent_initial_call=True,
    )
    def calculate_financial_metrics(revenue, expenses, assets, liabilities):
        """Calculate basic financial metrics."""
        try:
            if not all([revenue, expenses, assets, liabilities]):
                return "£0", "£0", "0%"

            net_worth = assets - liabilities
            monthly_cash_flow = revenue - expenses
            annual_cash_flow = monthly_cash_flow * 12
            growth_rate = (annual_cash_flow / assets) * 100 if assets > 0 else 0

            return (
                f"£{net_worth:,.0f}",
                f"£{monthly_cash_flow:,.0f}",
                f"{growth_rate:.1f}%",
            )

        except Exception as e:
            collect_error("calculate_financial_metrics")
            return "Error", "Error", "Error"

    print("✅ Minimal callbacks registered successfully!")
    return True
