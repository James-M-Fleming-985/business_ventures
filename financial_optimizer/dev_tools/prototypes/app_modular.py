# Core Python imports
import sys
import traceback
from datetime import datetime

# Dash and UI imports
import dash
from dash import Dash, html, dcc, callback_context
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc

# Data and visualization imports
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.graph_objects import Figure

# Add these error collection utilities near the top of app.py
import traceback
import sys
from datetime import datetime

# Add near the top of app.py, around line 20-30
from shared.types import PlotlyLayout, InvestmentMetrics

# In app.py, replace the error handling functions with:
from shared.error_handling import (
    collect_error,
    get_all_errors,
    clear_errors,
    register_error_handling_callbacks,
)

# Type hints
from typing import (
    List,
    Dict,
    Any,
    Tuple,
    Optional,
    Union,
    Callable,
    TypeVar,
    cast,
    TypedDict,
    TYPE_CHECKING,
)

# Your application components
from shared.layout import create_layout

# Shared/Global modules
from shared.error_handling import (
    register_error_handling_callbacks,
    collect_error,
    get_all_errors,
    clear_errors,
)

# Module callback registrations
from modules.investment_mgmt.callbacks import register_investment_mgmt_callbacks
from modules.financial_dashboard.callbacks import register_financial_dashboard_callbacks

# Define type for project_financials
ProjectFinancialsType = Callable[
    ...,  # Accept any parameters
    Union[pd.DataFrame, Tuple[pd.DataFrame, pd.DataFrame]],  # Return type
]

# Business logic and models
from modules.financial_dashboard.models.projections import (
    project_financials as _project_financials_raw,
)

_project_financials = cast(ProjectFinancialsType, _project_financials_raw)
from modules.financial_statements.layout.financial_statements import (
    create_financial_statements as _create_financial_statements,
)
from modules.investment_analysis.models.scenarios import (
    run_scenario_analysis,
    get_scenario_summary,
)
from services.sample_data import get_sample_data

# Component callback registrations (conditional imports to avoid circular dependencies)
if TYPE_CHECKING:
    # Type-only imports for better IDE support
    def register_input_callbacks(app: Dash) -> None: ...
    def register_chart_callbacks(app: Dash) -> None: ...
    def register_economic_climate_callbacks(app: Dash) -> None: ...
    def register_investment_optimizer_callbacks(app: Dash) -> None: ...

else:
    # Runtime imports
    from modules.investment_mgmt.logic import (
        register_input_callbacks,
        register_chart_callbacks,
        register_economic_climate_callbacks,
        register_investment_optimizer_callbacks,
    )

# Type definitions
RegisterCallbacksType = Callable[[Dash], None]

# Type alias for documentation purposes
CalculateInvestmentMetricsType = Callable[[List[float], float], InvestmentMetrics]


# This logic has been migrated to invesmtment_mgmt/logic/__init__.py
def project_financials(
    financial_data: Any,
    months: int = 60,
    investment_amount: float = 0,
    investment_type: Optional[str] = None,
    investment_rate: float = 5.0,
    investment_lifespan: int = 5,
    efficiency_impact: float = 0,
    calculate_baseline: bool = False,
    oee_availability: Optional[float] = 0,
    oee_performance: Optional[float] = 0,
    oee_quality: Optional[float] = 0,
    staff_count: int = 1,
    ramp_up_period: int = 3,
    training_cost: float = 2000,
) -> Union[pd.DataFrame, Tuple[pd.DataFrame, pd.DataFrame]]:
    """Wrapper for project_financials with proper type annotations."""
    result: Union[pd.DataFrame, Tuple[pd.DataFrame, pd.DataFrame]] = (
        _project_financials(
            financial_data=financial_data,
            months=int(months),  # Add explicit int conversion here
            investment_amount=int(investment_amount),
            investment_type=investment_type or "cash",  # Provide default value if None
            investment_rate=investment_rate,
            investment_lifespan=investment_lifespan,
            efficiency_impact=int(efficiency_impact),
            calculate_baseline=calculate_baseline,
            oee_availability=(
                int(oee_availability) if oee_availability is not None else 0
            ),
            oee_performance=int(oee_performance) if oee_performance is not None else 0,
            oee_quality=int(oee_quality) if oee_quality is not None else 0,
            staff_count=staff_count,
            ramp_up_period=ramp_up_period,
            training_cost=int(training_cost),
        )
    )
    return cast(Union[pd.DataFrame, Tuple[pd.DataFrame, pd.DataFrame]], result)


def create_financial_statements(
    financial_data: Any, projection_horizon: int = 60
) -> Dict[str, List[Any]]:
    return cast(
        Dict[str, List[Any]],
        _create_financial_statements(financial_data, projection_horizon),
    )


from typing import List, Dict, Any, Union, Tuple, Optional, TypeVar, cast, TypedDict


# This logic calculates the percent complete based on a timeline.
# This function takes a start date, end date, and current date,and returns a float representing the percentage of completion.
# This logic has been migrated to investment_mgmt/logic/__init__.py
def calculate_percent_complete(
    start_date: pd.Timestamp, end_date: pd.Timestamp, current_date: pd.Timestamp
) -> float:
    """Calculate percent complete based on timeline."""
    if current_date <= start_date:
        return 0.0
    if current_date >= end_date:
        return 1.0

    total_days = (end_date - start_date).total_seconds() / (24 * 3600)
    elapsed_days = (current_date - start_date).total_seconds() / (24 * 3600)

    if total_days <= 0:
        return 1.0

    return min(1.0, max(0.0, elapsed_days / total_days))


# Import the function with proper typing and provide explicit type information
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import List, Dict

    def _calculate_investment_metrics(
        cash_flows: List[float], initial_investment: float
    ) -> Dict[str, float]: ...

else:
    # Runtime import
    from modules.investment_analysis.models.investment_analysis import (
        calculate_investment_metrics as _calculate_investment_metrics,
    )


# Create a properly typed wrapper for the function
# This function calculates investment metrics such as ROI, IRR, payback period, and NPV.
# It takes a list of cash flows and an initial investment amount, and returns a dictionary with the calculated metrics.
# This logic has been migrated to investment_mgmt/logic/__init__.py
def calculate_investment_metrics(
    cash_flows: List[float], initial_investment: float
) -> InvestmentMetrics:
    """Wrapper with proper type annotations for the investment metrics calculation function."""
    result = _calculate_investment_metrics(cash_flows, initial_investment)
    # Explicitly cast the result to InvestmentMetrics to satisfy type checking
    return cast(InvestmentMetrics, result)


from modules.investment_analysis.models.scenarios import (
    run_scenario_analysis,
    get_scenario_summary,
)
from services.sample_data import get_sample_data

# Import data handling
# Register callbacks from other modules - types already defined above
from dash import Dash
from typing import cast, Callable, Any

app: Dash = dash.Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        "https://use.fontawesome.com/releases/v5.15.4/css/all.css",
    ],
    suppress_callback_exceptions=True,
)

# Register error handling callbacks first
register_error_handling_callbacks(app)

# Register dashboard callbacks
register_financial_dashboard_callbacks(app)

# Import what we need for callbacks but don't try to type annotate app.callback
# Dash's callback typing is complex and handled internally by Dash
from dash.dependencies import Input, Output, State

# Import main layout from shared
from shared.layout_new import create_layout

# Add use case switching imports
from core.config import UseCase, get_current_use_case, DEVELOPMENT_MODE


def create_application_layout_with_use_cases() -> html.Div:
    """Create the application layout with use case switching capability."""

    # Get current use case
    current_use_case = get_current_use_case()

    # Development mode selector (will be removed in production)
    development_controls = html.Div()
    if DEVELOPMENT_MODE:
        development_controls = html.Div(
            [
                dbc.Alert(
                    [
                        html.H6("🔧 Development Mode", className="mb-2"),
                        html.P(
                            "Toggle between use cases for development:",
                            className="mb-2",
                        ),
                        dcc.RadioItems(
                            id="dev-use-case-selector",
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
                            "This will be replaced by subscription logic in production.",
                            className="text-muted",
                        ),
                    ],
                    color="info",
                    className="mb-3",
                )
            ]
        )

    # Data stores for use case management
    use_case_stores = html.Div(
        [
            dcc.Store(id="use-case-store", data=current_use_case.value),
            dcc.Store(id="use-case-config-store"),
        ]
    )

    # Main application layout
    main_layout = html.Div(id="main-app-content")

    return html.Div([development_controls, use_case_stores, main_layout])


# Create the application layout with use case switching
app.layout = create_application_layout_with_use_cases()

# Register minimal callbacks for basic functionality
from shared.minimal_callbacks import register_minimal_callbacks

register_minimal_callbacks(app)

# Register callbacks from other modules
register_input_callbacks(app)
register_chart_callbacks(app)
register_economic_climate_callbacks(app)
register_investment_optimizer_callbacks(app)
register_investment_mgmt_callbacks(app)

# Add use case switching callback
if DEVELOPMENT_MODE:
    from core.config import get_current_use_case_from_string

    @app.callback(
        [Output("main-app-content", "children"), Output("use-case-store", "data")],
        Input("dev-use-case-selector", "value"),
    )
    def update_use_case_content(selected_use_case):
        """Update content based on selected use case."""
        print(f"🔄 Switching to use case: {selected_use_case}")

        if not selected_use_case:
            selected_use_case = "business"

        try:
            # Update the global use case configuration
            use_case = get_current_use_case_from_string(selected_use_case)

            # Return the main layout - it will now reflect the new use case
            layout = create_layout()
            print(f"📄 Layout created for use case: {selected_use_case}")
            return layout, selected_use_case
        except Exception as e:
            print(f"❌ Error creating layout for {selected_use_case}: {e}")
            return (
                html.Div(
                    [
                        dbc.Alert(
                            f"Error loading {selected_use_case}: {str(e)}",
                            color="danger",
                        )
                    ]
                ),
                selected_use_case,
            )


# Initial content load callback
@app.callback(
    Output("main-app-content", "children"),
    Input("use-case-store", "data"),
    prevent_initial_call=False,
)
def load_initial_content(use_case_data):
    """Load initial content based on stored use case."""
    print(f"🔄 Loading initial content for use case: {use_case_data}")

    if not use_case_data:
        use_case_data = "business"

    try:
        return create_layout()
    except Exception as e:
        print(f"❌ Error loading initial content: {e}")
        return html.Div(
            [dbc.Alert(f"Error loading application: {str(e)}", color="danger")]
        )


# Callback to toggle investment parameters based on selected type
# This callback updates the visibility of investment parameter containers based on the selected investment type.
# It shows the appropriate parameters for capital, process, or people investments.
# This logic has been migrated to investment_mgmt/callbacks/__init__.py
@app.callback(  # type: ignore
    [
        Output("capital-equipment-params", "style"),
        Output("process-improvement-params", "style"),
        Output("people-training-params", "style"),
    ],
    [Input("investment-mgmt-type-input", "value")],
)
def toggle_investment_params(
    investment_type: str,
) -> tuple[dict[str, str], dict[str, str], dict[str, str]]:
    """Show parameters based on selected investment type."""
    # Default: all hidden
    capital_style = {"display": "none"}
    process_style = {"display": "none"}
    people_style = {"display": "none"}

    # Show the appropriate container based on selection
    if investment_type == "capital":
        capital_style = {"display": "block"}
    elif investment_type == "process":
        process_style = {"display": "block"}
    elif investment_type == "people":
        people_style = {"display": "block"}

    return capital_style, process_style, people_style


# Callback to toggle production line selection based on investment scope
# This callback updates the visibility of the production line selection container based on the selected investment scope.
# It shows the production line selection only when the scope is set to "line".
# This logic has been migrated to investment_mgmt/callbacks/__init__.py
@app.callback(  # type: ignore
    Output("production-line-container", "style"),
    Input("investment-scope-input", "value"),
)
def toggle_production_line_selection(scope: Optional[str]) -> Dict[str, str]:
    """Show/hide production line selection based on investment scope."""
    if scope == "line":
        return {"display": "block"}
    return {"display": "none"}


# Callback to update app title based on mode
# This callback updates the application title based on the selected mode (business or personal).
# It changes the title text to reflect the current mode, providing context for the user.
# This logic has been migrated to shared/callbacks/__init__.py
@app.callback(  # type: ignore
    Output("app-title", "children"), [Input("app-mode", "value")]
)
def update_app_title(mode: Optional[str]) -> str:
    """Update the app title based on the selected mode."""
    if mode == "business":
        return "SLS Surface Finish Finance"
    else:
        return "Financial Optimizer"


# Update the existing metric titles callback to include spending metric
# This callback updates the metric titles based on the application mode.
# It changes the titles for worth, flow, and spending metrics to reflect the current mode (business or personal).
# This logic has been migrated to shared/callbacks/__init__.py
@app.callback(  # type: ignore
    [
        Output("worth-metric-title", "children"),
        Output("flow-metric-title", "children"),
        Output("spend-metric-title", "children"),
    ],  # New output for spending
    [Input("app-mode", "value")],
)
def update_metric_titles(mode: Optional[str]):
    """Update metric titles based on application mode."""
    if mode == "business":
        worth_title = "Department Contribution"
        flow_title = "Departmental Savings"
        spend_title = "Departmental Spending"  # New title for business mode
    else:
        worth_title = "Net Worth"
        flow_title = "Cash Flow"
        spend_title = "Monthly Expenses"  # Personal finance equivalent

    return worth_title, flow_title, spend_title


# Add this new callback after your update_metrics function
# This callback updates the spending metrics based on budget control.
# It calculates current and projected spending based on the selected time horizon, budget, and investment parameters and returns formatted strings for display.
# This logic has been migrated to shared/callbacks/__init__.py
@app.callback(  # type: ignore
    [
        Output("current-spending", "children"),
        Output("projected-spending", "children"),
        Output("spending-optimization", "children"),
    ],
    [
        Input("time-horizon-slider", "value"),
        Input("budget-slider", "value"),
        Input("budget-timeframe", "value"),
        Input("investment-type-input", "value"),
        Input("investment-rate-input", "value"),
        Input("investment-lifespan-input", "value"),
        Input("investment-efficiency-input", "value"),
        Input("app-mode", "value"),
    ],
    [State("financial-data-store", "data")],
)
def update_spending_metrics(
    months: Optional[int],
    budget: Optional[float],
    timeframe: Optional[int],
    investment_type: Optional[str],
    investment_rate: Optional[float],
    investment_lifespan: Optional[int],
    efficiency_impact: Optional[float],
    mode: Optional[str],
    stored_data: Optional[Dict[str, Any]],
) -> Tuple[str, str, str]:
    """Update the spending metrics based on budget control."""
    # Default to sample data if no stored data with explicit typing
    if stored_data is not None:
        financial_data: Dict[str, Any] = stored_data  # Keep type annotation here
    else:
        sample_data: Dict[str, Any] = cast(Dict[str, Any], get_sample_data())
        financial_data = (
            sample_data  # Remove type annotation here - it's already defined above
        )

    # Handle possible None values for months
    effective_months: int
    if months is None:
        effective_months = (
            timeframe * 12 if timeframe else 60
        )  # Convert years to months or default to 60
    else:
        effective_months = months

    # Use timeframe for investment lifespan if available - ensure type consistency
    effective_investment_lifespan: int
    if timeframe:
        effective_investment_lifespan = timeframe
    else:
        effective_investment_lifespan = (
            investment_lifespan if investment_lifespan is not None else 5
        )

    # Calculate baseline (no investment)
    effective_months = months if months is not None else 60
    baseline_result = project_financials(
        financial_data,
        months=effective_months,
        investment_amount=0.0,
        investment_type=investment_type,
        investment_rate=investment_rate if investment_rate is not None else 5.0,
        investment_lifespan=effective_investment_lifespan,
        efficiency_impact=0,
    )

    # Extract DataFrame from result (handle both single DataFrame and tuple returns)
    if isinstance(baseline_result, tuple):
        baseline_df = baseline_result[0]
    else:
        baseline_df = baseline_result
    # Calculate with investment
    investment_result = project_financials(
        financial_data,
        months=effective_months,
        investment_amount=budget if budget is not None else 0,
        investment_type=investment_type,
        investment_rate=investment_rate if investment_rate is not None else 5.0,
        investment_lifespan=effective_investment_lifespan,
        efficiency_impact=efficiency_impact if efficiency_impact is not None else 0,
    )

    # Extract DataFrame from result (handle both single DataFrame and tuple returns)
    if isinstance(investment_result, tuple):
        investment_df = investment_result[0]
    else:
        investment_df = investment_result

    # Define safe_float_convert function at the proper scope
    def safe_float_convert(val: Any) -> float:
        """Safely convert any value to float."""
        import math

        if val is None or (isinstance(val, float) and math.isnan(val)):
            return 0.0
        try:
            return float(val)
        except (ValueError, TypeError):
            return 0.0

    # Get spending metrics - check for available expense-related columns
    expense_columns = ["operating_expenses", "expenses", "total_expenses", "spending"]

    # Find the first available expense column in baseline_df
    expense_col = next(
        (col for col in expense_columns if col in baseline_df.columns), None
    )

    # If no expense column is found, use a default or fallback approach
    if expense_col:
        # Use safe value extraction with explicit typing and error handling
        try:
            baseline_current_val = cast(Any, baseline_df[expense_col].iat[0])
            baseline_current: float = safe_float_convert(baseline_current_val)

            baseline_projected_val = cast(Any, baseline_df[expense_col].iat[-1])
            baseline_projected: float = safe_float_convert(baseline_projected_val)

            # We don't need the current investment value, only the projected value
            investment_projected_val = cast(Any, investment_df[expense_col].iat[-1])
            investment_projected: float = safe_float_convert(investment_projected_val)
        except (IndexError, KeyError, ValueError, TypeError):
            # Fallback if indexing fails
            baseline_current = 0.0
            baseline_projected = 0.0
            # Remove unused variable assignment
            investment_projected = 0.0
    else:
        # Fallback: If no expense column is found, look at the DataFrame columns
        print(f"Available columns: {baseline_df.columns.tolist()}")

        # Try to use EBITDA or other related columns as a proxy, or default to zero
        if "ebitda" in baseline_df.columns:
            # Use negative EBITDA as a proxy for expenses (not ideal but better than error)
            baseline_current_val = cast(Any, baseline_df["ebitda"].iat[0])
            baseline_current_adjusted: float = (
                safe_float_convert(baseline_current_val) * -1
            )
            baseline_projected_val = cast(Any, baseline_df["ebitda"].iat[-1])
            baseline_projected_adjusted: float = (
                safe_float_convert(baseline_projected_val) * -1
            )
            investment_current_val = cast(Any, investment_df["ebitda"].iat[0])
            # Removed unused variable assignment
            investment_projected_val = cast(Any, investment_df["ebitda"].iat[-1])
            # We only need the projected value for the calculation
            investment_projected_val = cast(Any, investment_df["ebitda"].iat[-1])
            investment_projected_adjusted: float = (
                safe_float_convert(investment_projected_val) * -1
            )
            baseline_projected_zero: float = 0.0
            investment_current: float = 0.0
            investment_projected_zero: float = 0.0

    # Calculate spending optimization (how much is saved on operational expenses)
    spending_optimization = baseline_projected - investment_projected
    optimization_percentage = (
        (spending_optimization / baseline_projected) * 100
        if baseline_projected > 0
        else 0
    )

    # Format the output based on mode
    if mode == "business":
        current_spending = f"£{baseline_current:,.2f}/mo"
        projected_spending = f"£{investment_projected:,.2f}/mo"
        savings_text = (
            f"Save £{spending_optimization:,.2f}/mo ({optimization_percentage:.1f}%)"
        )
    else:
        current_spending = f"£{baseline_current:,.2f}/mo"
        projected_spending = f"£{investment_projected:,.2f}/mo"
        savings_text = (
            f"Save £{spending_optimization:,.2f}/mo ({optimization_percentage:.1f}%)"
        )

    return current_spending, projected_spending, savings_text


# New callback for projected savings
# This callback updates the projected savings based on budget and timeframe.
# It calculates the annual savings based on the selected budget, investment type, rate, efficiency impact, and mode.
# It returns a formatted string for display.
# This logic has been migrated to investment_mgmt/callbacks/__init__.py
@app.callback(  # type: ignore
    Output("projected-savings", "children"),
    [
        Input("budget-slider", "value"),
        Input("budget-timeframe", "value"),
        Input("investment-type-input", "value"),
        Input("investment-rate-input", "value"),
        Input("investment-efficiency-input", "value"),
        Input("app-mode", "value"),
    ],
    [State("financial-data-store", "data")],
)
def update_projected_savings(
    budget: Optional[float],
    timeframe: Optional[int],
    investment_type: Optional[str],
    investment_rate: Optional[float],
    efficiency_impact: Optional[float],
    mode: Optional[str],
    stored_data: Optional[Dict[str, Any]],
) -> str:
    """Update the projected savings based on budget and timeframe."""
    if budget is None or budget <= 0:
        return "£0"

    # Default to sample data if no stored data with explicit typing
    if stored_data is not None:
        financial_data: Dict[str, Any] = stored_data
    else:
        from typing import cast

        sample_data: Dict[str, Any] = cast(Dict[str, Any], get_sample_data())
        financial_data = (
            sample_data  # Remove type annotation here - it's already defined above
        )

    # Calculate projections with timeframe in mind
    months = timeframe * 12 if timeframe else 60  # Convert years to months

    df = project_financials(
        financial_data,
        months=months,
        investment_amount=budget,
        investment_type=investment_type,
        investment_rate=investment_rate if investment_rate is not None else 5.0,
        investment_lifespan=timeframe if timeframe else 5,  # Use timeframe as lifespan
        efficiency_impact=efficiency_impact if efficiency_impact is not None else 0,
    )

    # Extract DataFrame from result if it's a tuple
    if isinstance(df, tuple):
        df_data = df[0]
    else:
        df_data = df

    # Calculate annual savings with proper type handling
    if mode == "business":
        if "ebitda" in df_data.columns:
            ebitda_series = df_data["ebitda"].astype(float)
            # Use .iloc to get values with proper type handling
            if len(ebitda_series) > 0:
                first_val = (
                    float(ebitda_series.iloc[0])
                    if ebitda_series.iloc[0] is not None
                    else 0.0
                )
                last_val = (
                    float(ebitda_series.iloc[-1])
                    if ebitda_series.iloc[-1] is not None
                    else 0.0
                )
                annual_savings = (last_val - first_val) * 12
            else:
                annual_savings = 0.0
        else:
            annual_savings = 0.0
    else:
        if "cash_flow" in df_data.columns:
            cash_flow_series: pd.Series[float] = df_data["cash_flow"].astype(float)
            if len(cash_flow_series) > 0:
                # Safely extract first and last values with proper type handling
                first_raw = cash_flow_series.iloc[0]
                last_raw = cash_flow_series.iloc[-1]

                # Convert to float with None checking and proper type conversion
                try:
                    first_numeric = pd.to_numeric(first_raw, errors="coerce")  # type: ignore
                    # Check if the result is NaN using math.isnan for better type safety
                    import math

                    if math.isnan(float(first_numeric)):
                        first_val = 0.0
                    else:
                        first_val = float(first_numeric)
                except (ValueError, TypeError):
                    first_val = 0.0

                try:
                    last_numeric = pd.to_numeric(last_raw, errors="coerce")  # type: ignore
                    # Check if the result is NaN using math.isnan for better type safety
                    import math

                    if math.isnan(float(last_numeric)):
                        last_val = 0.0
                    else:
                        last_val = float(last_numeric)
                except (ValueError, TypeError):
                    last_val = 0.0
                annual_savings = (last_val - first_val) * 12
            else:
                annual_savings = 0.0
        else:
            annual_savings = 0.0

    return f"£{annual_savings:,.2f}"


# Callback for updating metrics
# This callback updates the financial metrics based on the selected time horizon, budget, investment parameters, and application mode.
# It calculates current and projected net worth, cash flow, and returns formatted strings for display.
# This logic has been migrated to shared/callbacks/__init__.py
@app.callback(  # type: ignore
    [
        Output("current-net-worth", "children"),
        Output("projected-net-worth", "children"),
        Output("current-cash-flow", "children"),
        Output("projected-cash-flow", "children"),
    ],
    [
        Input("time-horizon-slider", "value"),
        Input("budget-slider", "value"),  # Changed from investment-slider
        Input("budget-timeframe", "value"),  # Added new input
        Input("investment-type-input", "value"),
        Input("investment-rate-input", "value"),
        Input("investment-lifespan-input", "value"),
        Input("investment-efficiency-input", "value"),
        Input("app-mode", "value"),
    ],
    [State("financial-data-store", "data")],
)
def update_metrics(
    months: Optional[int],
    budget: Optional[float],
    timeframe: Optional[int],
    investment_type: Optional[str],
    investment_rate: Optional[float],
    investment_lifespan: Optional[int],
    efficiency_impact: Optional[float],
    mode: Optional[str],
    stored_data: Optional[Dict[str, Any]],
) -> Tuple[str, str, str, str]:
    """Update the financial metrics based on budget control."""
    # Default to sample data if no stored data with explicit typing
    # Handle None case explicitly for clearer type inference
    if stored_data is not None:
        financial_data_dict: Dict[str, Any] = stored_data
    else:
        financial_data_dict = cast(
            Dict[str, Any], get_sample_data()
        )  # Cast to expected type

    # Use timeframe for investment lifespan if available
    if timeframe:
        investment_lifespan = timeframe

    # Calculate projections with proper type handling for months
    df = project_financials(
        financial_data_dict,
        months=months if months is not None else 60,  # Default to 60 months if None
        investment_amount=budget if budget is not None else 0.0,  # Handle None budget
        investment_type=investment_type,
        investment_rate=investment_rate if investment_rate is not None else 5.0,
        investment_lifespan=(
            investment_lifespan if investment_lifespan is not None else 5
        ),
        efficiency_impact=efficiency_impact if efficiency_impact is not None else 0,
    )

    # Handle the case where df might be a tuple or DataFrame
    if isinstance(df, tuple):
        df_data = df[0]  # Use the first DataFrame from the tuple
    else:
        df_data = df

    # Ensure we have a DataFrame with numeric data and proper type casting
    df_numeric = df_data.select_dtypes(include=["number"]).fillna(0)

    # Format metrics based on mode with proper type casting using pd.to_numeric
    if mode == "business":
        current_metric = (
            f"£{pd.to_numeric(df_numeric['net_worth'].iloc[0], errors='coerce'):,.2f}"
        )
        projected_metric = (
            f"£{pd.to_numeric(df_numeric['net_worth'].iloc[-1], errors='coerce'):,.2f}"
        )
        current_flow = (
            f"£{pd.to_numeric(df_numeric['ebitda'].iloc[0], errors='coerce'):,.2f}"
        )
        projected_flow = (
            f"£{pd.to_numeric(df_numeric['ebitda'].iloc[-1], errors='coerce'):,.2f}"
        )
    else:
        current_metric = (
            f"£{pd.to_numeric(df_numeric['net_worth'].iloc[0], errors='coerce'):,.2f}"
        )
        projected_metric = (
            f"£{pd.to_numeric(df_numeric['net_worth'].iloc[-1], errors='coerce'):,.2f}"
        )
        current_flow = (
            f"£{pd.to_numeric(df_numeric['cash_flow'].iloc[0], errors='coerce'):,.2f}"
        )
        projected_flow = (
            f"£{pd.to_numeric(df_numeric['cash_flow'].iloc[-1], errors='coerce'):,.2f}"
        )

    return current_metric, projected_metric, current_flow, projected_flow


# Callback to update investment fields based on selected type
# This callback updates the investment form fields based on the selected investment type and application mode.
# It changes the rate label and visibility of lifespan, efficiency, OEE, and staffing fields depending on the investment type and mode (business or personal finance).
# It also updates the budget label to reflect the context of the investment.
# This logic has been migrated to investment_mgmt/callbacks/__init__.py
@app.callback(
    [
        Output("investment-rate-label", "children"),
        Output("investment-lifespan-container", "style"),
        Output("investment-efficiency-container", "style"),
        Output("oee-container", "style"),
        Output("staffing-container", "style"),
        Output("budget-label", "children"),
    ],  # New output for budget label
    [Input("investment-type-input", "value"), Input("app-mode", "value")],
)
def update_investment_fields(
    investment_type: Optional[str], mode: Optional[str]
) -> Tuple[str, Dict[str, str], Dict[str, str], Dict[str, str], Dict[str, str], str]:
    """Update investment form fields based on selected investment type."""
    rate_label = "Growth/Return Rate (%):"
    show_lifespan = {"display": "none"}
    show_efficiency = {"display": "none"}
    show_oee = {"display": "none"}
    show_staffing = {"display": "none"}

    # Set budget label based on mode
    if mode == "business":
        budget_label = "Department Budget (£):"
    else:
        budget_label = "Investment Budget (£):"

    # Business mode
    if mode == "business":
        if investment_type == "cash":
            rate_label = "Interest/Return Rate (%):"
        elif investment_type == "equipment":
            rate_label = "Depreciation Rate (%):"
            show_lifespan = {"display": "block"}
            show_efficiency = {"display": "block"}
            show_oee = {"display": "block"}  # Show OEE components for equipment
        elif investment_type == "property":
            rate_label = "Appreciation Rate (%):"
            show_lifespan = {"display": "block"}
        elif investment_type == "rd":
            rate_label = "Expected Return Rate (%):"
            show_efficiency = {"display": "block"}
        elif investment_type in ["marketing", "it", "training"]:
            rate_label = "Impact Rate (%):"
            show_efficiency = {"display": "block"}
        elif investment_type == "staffing":  # New staff option
            rate_label = "Long-term Productivity Rate (%):"
            show_efficiency = {"display": "block"}
            show_staffing = {"display": "block"}  # Show staffing inputs
    # Personal finance mode
    else:
        if investment_type == "cash":
            rate_label = "Interest Rate (%):"
        elif investment_type == "stocks":
            rate_label = "Expected Return (%):"
        elif investment_type == "bonds":
            rate_label = "Yield (%):"
        elif investment_type == "property":
            rate_label = "Appreciation Rate (%):"
            show_lifespan = {"display": "block"}
        elif investment_type == "education":
            rate_label = "Income Impact Rate (%):"
            show_efficiency = {"display": "block"}
        elif investment_type == "business":
            rate_label = "Expected ROI (%):"
            show_efficiency = {"display": "block"}

    return (
        rate_label,
        show_lifespan,
        show_efficiency,
        show_oee,
        show_staffing,
        budget_label,
    )


# Update scenario dropdown options based on mode
@app.callback(Output("scenario-selector", "options"), [Input("app-mode", "value")])
def update_scenario_options(mode: Optional[str]):
    """Update available scenario options based on selected mode."""
    if mode == "business":
        from modules.investment_analysis.models.scenarios import get_business_scenarios

        scenarios = get_business_scenarios()
    else:
        from modules.investment_analysis.models.scenarios import get_personal_scenarios

        scenarios = get_personal_scenarios()

    return [{"label": data["name"], "value": key} for key, data in scenarios.items()]


# Run scenario analysis and display results
@app.callback(
    [
        Output("scenario-results", "style"),
        Output("scenario-net-worth-chart", "figure"),
        Output("scenario-cash-flow-chart", "figure"),
        Output("scenario-revenue-chart", "figure"),
        Output("scenario-ebitda-chart", "figure"),
        Output("scenario-summary-table", "data"),
        Output("scenario-description", "children"),
    ],
    [Input("run-scenario-button", "n_clicks")],
    [
        State("app-mode", "value"),
        State("scenario-selector", "value"),
        State("time-horizon-slider", "value"),
        State("budget-slider", "value"),  # Changed from investment-slider
        State("budget-timeframe", "value"),  # Added new input
        State("investment-type-input", "value"),
        State("investment-rate-input", "value"),
        State("investment-lifespan-input", "value"),
        State("investment-efficiency-input", "value"),
        State("financial-data-store", "data"),
    ],
)
def run_and_display_scenarios(
    n_clicks: Optional[int],
    mode: Optional[str],
    selected_scenarios: Optional[str],
    months: Optional[int],
    budget: Optional[float],
    timeframe: Optional[int],
    investment_type: Optional[str],
    investment_rate: Optional[float],
    investment_lifespan: Optional[int],
    efficiency_impact: Optional[float],
    financial_data: Optional[Dict[str, Any]],
) -> Tuple[
    Dict[str, str],
    Figure,
    Figure,
    Figure,
    Figure,
    List[Dict[str, Any]],
    Union[str, html.Div],
]:
    """Run scenario analysis and display results."""
    import plotly.graph_objs as go  # type: ignore
    from dash import html
    from dash import dcc
    from typing import Dict, List, Union, Tuple

    # Initialize outputs
    show_results = {"display": "none"}
    empty_fig = go.Figure()
    empty_table: List[Dict[str, Any]] = []
    no_description = ""

    # Return empty results if button not clicked or no scenarios selected
    if not n_clicks or not selected_scenarios:
        return (
            show_results,
            empty_fig,
            empty_fig,
            empty_fig,
            empty_fig,
            empty_table,
            no_description,
        )

    # Default to sample data if no stored data
    if not financial_data:
        financial_data = get_sample_data(mode)

    # Use timeframe for investment lifespan if available
    if timeframe:
        investment_lifespan = timeframe

    # Run scenario analysis
    scenario_results = run_scenario_analysis(
        financial_data,
        base_months=months,
        investment_amount=budget or 0.0,  # Changed from investment to budget
        investment_type=investment_type,
        investment_rate=investment_rate if investment_rate is not None else 5.0,
        investment_lifespan=(
            investment_lifespan if investment_lifespan is not None else 5
        ),
        efficiency_impact=efficiency_impact if efficiency_impact is not None else 0,
        scenario_params=selected_scenarios,
        mode=mode if mode is not None else "personal",  # Provide default when None
    )

    # Create comparison charts
    net_worth_fig = go.Figure()
    cash_flow_fig = go.Figure()
    revenue_fig = go.Figure()
    ebitda_fig = go.Figure()

    # For each scenario, add traces to the relevant charts
    for scenario_key, data in scenario_results.items():
        scenario_name = data["name"]
        proj = data["projection"]

        # Add net worth/equity trace
        value_label = "Department Contribution" if mode == "business" else "Net Worth"
        net_worth_fig.add_trace(
            go.Scatter(  # type: ignore
                x=proj["date"], y=proj["net_worth"], name=scenario_name, mode="lines"
            )
        )

        # Add cash flow trace
        cash_flow_fig.add_trace(
            go.Scatter(  # type: ignore
                x=proj["date"], y=proj["cash_flow"], name=scenario_name, mode="lines"
            )
        )

        # Add revenue trace
        revenue_fig.add_trace(
            go.Scatter(  # type: ignore
                x=proj["date"], y=proj["revenue"], name=scenario_name, mode="lines"
            )
        )

        # Add EBITDA/profit trace
        metric_name = "EBITDA" if mode == "business" else "Net Income"
        ebitda_fig.add_trace(
            go.Scatter(  # type: ignore
                x=proj["date"], y=proj["ebitda"], name=scenario_name, mode="lines"
            )
        )

    # Update chart layouts
    net_worth_fig.update_layout(
        title=f"{'Department Contribution' if mode == 'business' else 'Net Worth'} Comparison",
        xaxis_title="Date",
        yaxis_title="Amount (£)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode="x unified",
    )

    cash_flow_fig.update_layout(
        title="Cash Flow Comparison",
        xaxis_title="Date",
        yaxis_title="Amount (£)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode="x unified",
    )

    revenue_fig.update_layout(
        title="Revenue Comparison",
        xaxis_title="Date",
        yaxis_title="Amount (£)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode="x unified",
    )

    ebitda_fig.update_layout(
        title=f"{'EBITDA' if mode == 'business' else 'Net Income'} Comparison",
        xaxis_title="Date",
        yaxis_title="Amount (£)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode="x unified",
    )

    # Generate summary table
    summary_df = get_scenario_summary(scenario_results)

    # Create description of selected scenarios
    descriptions = [
        f"**{data['name']}**: {data['description']}"
        for _, data in scenario_results.items()
    ]
    description_text = html.Div(
        [
            html.H5("Scenario Descriptions:"),
            html.Ul([html.Li(dcc.Markdown(desc)) for desc in descriptions]),
        ]
    )

    return (
        {"display": "block"},
        net_worth_fig,
        cash_flow_fig,
        revenue_fig,
        ebitda_fig,
        summary_df.to_dict("records"),
        description_text,
    )


# Callback to calculate and store financial data
# This callback calculates financial data based on user inputs and stores it in the data store.
# It processes income, assets, liabilities, and expenses data, calculates projections, and returns the financial data and projection results.
# It also handles the case where no button clicks have occurred, returning sample data for initial load.
# This logic has been migrated to shared/callbacks/__init__.py
@app.callback(
    [
        Output("financial-data-store", "data"),
        Output("projection-results-store", "data"),
    ],
    [Input("calculate-button", "n_clicks"), Input("app-mode", "value")],
    [
        State("income-table", "data"),
        State("assets-table", "data"),
        State("liabilities-table", "data"),
        State("expenses-table", "data"),
        State("time-horizon-slider", "value"),
        State("budget-slider", "value"),  # Changed from investment-slider
        State("budget-timeframe", "value"),  # Added new input
        State("investment-type-input", "value"),
        State("investment-rate-input", "value"),
        State("investment-lifespan-input", "value"),
        State("investment-efficiency-input", "value"),
    ],
)
def calculate_and_store_data(
    n_clicks: Optional[int],
    mode: Optional[str],
    income_data: Optional[List[Dict[str, Any]]],
    assets_data: Optional[List[Dict[str, Any]]],
    liabilities_data: Optional[List[Dict[str, Any]]],
    expenses_data: Optional[List[Dict[str, Any]]],
    months: Optional[int],
    budget: Optional[float],
    timeframe: Optional[int],
    investment_type: Optional[str],
    investment_rate: Optional[float],
    investment_lifespan: Optional[int],
    efficiency_impact: Optional[float],
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """Calculate and store financial data with enhanced budget parameters."""
    from typing import Any

    if n_clicks is None:
        # Return sample data for initial load based on mode
        effective_mode = (
            mode if mode is not None else "personal"
        )  # Default to 'personal' if mode is None
        # Get sample data and explicitly cast to the expected type to resolve type checking issues
        from typing import cast, Optional, Dict

        untyped_sample_data = cast(
            Optional[Dict[str, Any]], get_sample_data(effective_mode)
        )
        sample_data: Dict[str, Any] = {}
        if untyped_sample_data is not None:
            sample_data.update(untyped_sample_data)
        projection_result = project_financials(sample_data, months=60)
        # Handle both single DataFrame and tuple returns
        if isinstance(projection_result, tuple):
            projection_df = projection_result[0]
        else:
            projection_df = projection_result
        # Use a direct approach with explicit typing to avoid type checking issues
        from typing import Dict, List, Any, Iterator

        # Create a properly typed list with correct type annotation
        projection_data: List[Dict[str, Any]] = []
        # Iterate through the rows and create dictionaries directly
        from typing import Tuple, cast

        # Use explicit variable assignment with proper typing
        from pandas import Series
        from typing import Any

        # Use a more generic type annotation with explicit type information
        from typing import Iterator, Tuple, cast
        from pandas import Series

        # Use a more general type annotation to avoid type checking issues with iterrows()
        iter_rows: Iterator[Tuple[Any, Any]] = projection_df.iterrows()  # type: ignore
        for _, row in iter_rows:
            # Explicitly annotate row as Series[Any]
            row_series: Series[Any] = row
            # Convert row to dictionary with string keys and explicit type annotation
            row_dict: Dict[str, Any] = {
                str(col): row_series[col] for col in projection_df.columns
            }
            # Now we don't need to cast since the type is already specified
            projection_data.append(row_dict)
        # Return directly without the unnecessary cast
        return sample_data, projection_data

    # Process the input data
    investments: List[Dict[str, Any]] = []
    savings: List[Dict[str, Any]] = []

    if assets_data:
        for item in assets_data:
            if (
                item and item.get("return", 0) <= 2
            ):  # Assuming low return items are savings
                savings.append(
                    {
                        "name": item.get("name", ""),
                        "balance": item.get("value", 0),
                        "rate": item.get("return", 0),
                        "contribution": item.get("contribution", 0),
                    }
                )
            else:
                investments.append(
                    {
                        "name": item.get("name", ""),
                        "value": item.get("value", 0),
                        "return": item.get("return", 0),
                        "contribution": item.get("contribution", 0),
                    }
                )

    financial_data = {
        "income": income_data if income_data else [],
        "savings": savings,
        "investments": investments,
        "debts": liabilities_data if liabilities_data else [],
        "spending": expenses_data if expenses_data else [],
    }

    # Calculate projections with the parsed financial data
    effective_months = months if months is not None else 60
    projection_result = project_financials(
        financial_data,
        months=effective_months,
        investment_amount=budget if budget is not None else 0,
        investment_type=investment_type,
        investment_rate=investment_rate if investment_rate is not None else 5.0,
        investment_lifespan=(
            investment_lifespan if investment_lifespan is not None else 5
        ),
        efficiency_impact=efficiency_impact if efficiency_impact is not None else 0,
    )

    # Handle both single DataFrame and tuple returns
    if isinstance(projection_result, tuple):
        projection_df = projection_result[0]
    else:
        projection_df = projection_result

    # Convert projection dataframe to records with explicit handling for type checking
    from typing import List, Dict, Any, cast

    # Get the records with explicit type annotation instead of casting
    from typing import List, Dict, Any

    # Use type: ignore to bypass the complex overload resolution
    raw_records: List[Dict[str, Any]] = projection_df.to_dict(orient="records")  # type: ignore
    # Create a properly typed list with correct type annotation
    projection_data_empty: List[Dict[str, Any]] = []
    for record in raw_records:
        # Convert keys to strings to satisfy the type checker
        projection_data.append({str(k): v for k, v in record.items()})

    # Return the financial data and projection data
    return financial_data, projection_data


# Callback to update the overview chart
# This callback updates the overview chart based on budget control, investment parameters, and application mode.
# It calculates financial projections and returns a Plotly figure for display.
# It handles None values for months, budget, and investment parameters, and uses sample data if no stored data is available.
# This logic has been migrated to shared/callbacks/__init__.py
@app.callback(
    Output("overview-chart", "figure"),
    [
        Input("time-horizon-slider", "value"),
        Input("budget-slider", "value"),
        Input("budget-timeframe", "value"),
        Input("investment-type-input", "value"),
        Input("investment-rate-input", "value"),
        Input("investment-lifespan-input", "value"),
        Input("investment-efficiency-input", "value"),
        Input("app-mode", "value"),
        Input("show-impact-toggle", "value"),
    ],
    [State("financial-data-store", "data")],
)
def update_overview_chart(
    months: Optional[int],
    budget: Optional[float],
    timeframe: Optional[int],
    investment_type: Optional[str],
    investment_rate: Optional[float],
    investment_lifespan: Optional[int],
    efficiency_impact: Optional[float],
    mode: Optional[str],
    show_impact: Optional[List[str]],
    stored_data: Optional[Dict[str, Any]],
) -> "Figure":
    """Update the overview chart based on budget control."""
    # Default to sample data if no stored data with explicit typing
    # Import typing utilities locally to ensure they're available
    from typing import Dict, Any, cast

    # Handle stored_data more explicitly for type checking
    if stored_data is not None:
        # Convert to Dict[str, Any] with proper type annotation
        financial_data: Dict[str, Any] = dict(stored_data)
    else:
        # Create sample data with explicit typing
        sample_data: Dict[str, Any] = cast(Dict[str, Any], get_sample_data())
        financial_data = dict(sample_data)

    # Handle possible None values for months
    if months is None:
        months = timeframe * 12 if timeframe else 60

    # Use timeframe for investment lifespan if available
    if timeframe:
        investment_lifespan = timeframe

    # Determine if we should show impact
    show_impact_flag = show_impact and len(show_impact) > 0 and "show" in show_impact

    # Handle None budget value
    if budget is None:
        budget = 0.0

    # Define helper function inside this function
    def get_expense_column(df: pd.DataFrame) -> "pd.Series[float]":
        """Helper function to find an appropriate expense column or create a fallback."""
        # Try to find an expense-related column
        expense_columns = [
            "operating_expenses",
            "expenses",
            "total_expenses",
            "spending",
        ]

        for col in expense_columns:
            if col in df.columns:
                return df[col].astype(float)

        # If no expense columns exist, try to derive it from other columns
        if "revenue" in df.columns and "ebitda" in df.columns:
            # Estimate expenses as revenue minus EBITDA
            return (df["revenue"] - df["ebitda"]).astype(float)
        elif "revenue" in df.columns and "net_income" in df.columns:
            # Estimate expenses as revenue minus net income
            return (df["revenue"] - df["net_income"]).astype(float)

        # Last resort, return a series of zeros
        print(
            "Warning: No expense columns found and couldn't derive expenses. Using zeros instead."
        )
        return pd.Series([0.0] * len(df), index=df.index, dtype=float)

    # Calculate projections with budget
    if show_impact_flag and budget > 0:
        projection_result = project_financials(
            financial_data,
            months=months,
            investment_amount=budget,
            investment_type=investment_type,
            investment_rate=investment_rate if investment_rate is not None else 5.0,
            investment_lifespan=(
                investment_lifespan if investment_lifespan is not None else 5
            ),
            efficiency_impact=efficiency_impact if efficiency_impact is not None else 0,
            calculate_baseline=True,
        )
        # Handle both single DataFrame and tuple returns
        if isinstance(projection_result, tuple):
            df, baseline_df = projection_result
        else:
            df = projection_result
            baseline_df = None
    else:
        projection_result = project_financials(
            financial_data,
            months=months,
            investment_amount=budget,
            investment_type=investment_type,
            investment_rate=investment_rate if investment_rate is not None else 5.0,
            investment_lifespan=(
                investment_lifespan if investment_lifespan is not None else 5
            ),
            efficiency_impact=efficiency_impact if efficiency_impact is not None else 0,
        )
        # Handle both single DataFrame and tuple returns
        if isinstance(projection_result, tuple):
            df = projection_result[0]
        else:
            df = projection_result
        baseline_df = None

    # Create figure
    fig = go.Figure()

    # Add Monthly Savings
    if mode == "business":
        metric_name = "Departmental Savings"
        # Add trace directly to avoid type issues
        fig.add_trace(
            go.Scatter(  # type: ignore
                x=df["date"],
                y=df["cash_flow"],
                name=(
                    f"{metric_name} (with Investment)"
                    if show_impact_flag and budget > 0
                    else metric_name
                ),
                line=dict(color="#1f77b4", width=2),
            )
        )
    else:
        metric_name = "Monthly Cash Flow"
        fig.add_trace(
            go.Scatter(  # type: ignore
                x=df["date"],
                y=df["cash_flow"],
                name=(
                    f"{metric_name} (with Investment)"
                    if show_impact_flag and budget > 0
                    else metric_name
                ),
                line=dict(color="#1f77b4", width=2),
            )
        )

    # Add Departmental Spending using the helper function
    departmental_spending = get_expense_column(df)
    fig.add_trace(
        go.Scatter(  # type: ignore
            x=df["date"],
            y=departmental_spending,
            name=(
                "Dept. Spending (with Investment)"
                if show_impact_flag and budget > 0
                else "Dept. Spending"
            ),
            line=dict(color="#d62728", width=2),
        )
    )

    # Add baseline for comparison if showing impact
    if show_impact_flag and budget > 0 and baseline_df is not None:
        # Add baseline Monthly Savings
        fig.add_trace(
            go.Scatter(  # type: ignore
                x=baseline_df["date"],
                y=baseline_df["cash_flow"],
                name=f"{metric_name} (without Investment)",
                line=dict(color="#1f77b4", width=2, dash="dash"),
            )
        )

        # Add baseline Departmental Spending
        baseline_spending = get_expense_column(baseline_df)
        fig.add_trace(
            go.Scatter(  # type: ignore
                x=baseline_df["date"],
                y=baseline_spending,
                name="Dept. Spending (without Investment)",
                line=dict(color="#d62728", width=2, dash="dash"),
            )
        )

    # Update layout with proper typing
    from typing import cast, Any

    cast(Any, fig).update_layout(
        title="Financial Projections",
        xaxis_title="Date",
        yaxis_title="Amount (£)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode="x unified",
    )

    return fig


# Callback for financial statement display
@app.callback(
    Output("financial-statement-container", "children"),
    [Input("statement-selector", "value"), Input("calculate-button", "n_clicks")],
    [State("financial-data-store", "data")],
)
def display_financial_statement(
    statement_type: Optional[str],
    n_clicks: Optional[int],
    stored_data: Optional[Dict[str, Any]],
) -> html.Div:
    """Display the selected financial statement."""
    if n_clicks is None or stored_data is None:
        return html.Div(
            [
                html.P(
                    "Please enter your financial data and calculate projections first."
                )
            ]
        )

    # Generate financial statements
    statements = create_financial_statements(stored_data)

    if statement_type == "income":
        # Display income statement
        df = pd.DataFrame(statements["income_statements"])

        table_header = [
            html.Thead(
                html.Tr(
                    [
                        html.Th("Period"),
                        html.Th("Revenue"),
                        html.Th("Gross Profit"),
                        html.Th("Operating Expenses"),
                        html.Th("EBITDA"),
                        html.Th("Depreciation"),
                        html.Th("EBIT"),
                        html.Th("Interest"),
                        html.Th("Taxes"),
                        html.Th("Net Income"),
                    ]
                )
            )
        ]

        rows: List[html.Tr] = []
        for i in df.index:
            row = df.loc[i]  # Let type inference handle this
            # Safely extract values with proper type conversion
            # Safely extract month value with explicit type handling
            month_raw: Any = row["month"] if "month" in row else None
            if month_raw is not None:
                try:
                    # Check for NaN using math.isnan for float values
                    import math

                    # First check if it's already a number type, then convert to float safely
                    if isinstance(month_raw, (int, float)):
                        month_float = float(month_raw)
                    elif hasattr(month_raw, "__float__"):
                        month_float = float(month_raw)
                    else:
                        # Convert to string first, then to float for proper type safety
                        # Use cast to explicitly tell the type checker this is a string
                        month_str = str(month_raw) if month_raw is not None else "0"
                        month_float = float(month_str)

                    if math.isnan(month_float):
                        month_val = 1
                    else:
                        month_val = int(month_float + 1)
                except (ValueError, TypeError, AttributeError):
                    month_val = 1
            else:
                month_val = 1
            revenue_val = (
                float(row["revenue"])
                if row["revenue"] is not None and pd.notna(row["revenue"])
                else 0.0
            )
            gross_profit_val = (
                float(row["gross_profit"])
                if row["gross_profit"] is not None and pd.notna(row["gross_profit"])
                else 0.0
            )
            operating_expenses_val = (
                float(row["operating_expenses"])
                if row["operating_expenses"] is not None
                and pd.notna(row["operating_expenses"])
                else 0.0
            )
            ebitda_val = (
                float(row["ebitda"])
                if row["ebitda"] is not None and pd.notna(row["ebitda"])
                else 0.0
            )
            depreciation_val = (
                float(row["depreciation"])
                if row["depreciation"] is not None and pd.notna(row["depreciation"])
                else 0.0
            )
            ebit_val = (
                float(row["ebit"])
                if row["ebit"] is not None and pd.notna(row["ebit"])
                else 0.0
            )
            interest_expense_val = (
                float(row["interest_expense"])
                if row["interest_expense"] is not None
                and pd.notna(row["interest_expense"])
                else 0.0
            )
            taxes_val = (
                float(row["taxes"])
                if row["taxes"] is not None and pd.notna(row["taxes"])
                else 0.0
            )
            try:
                net_income_raw = row["net_income"]
                if net_income_raw is not None and pd.notna(net_income_raw):
                    net_income_val = float(
                        pd.to_numeric(net_income_raw, errors="coerce")
                    )
                    if pd.isna(net_income_val):
                        net_income_val = 0.0
                else:
                    net_income_val = 0.0
            except (ValueError, TypeError):
                net_income_val = 0.0

            rows.append(
                html.Tr(
                    [
                        html.Td(f"Month {month_val}"),
                        html.Td(f"£{revenue_val:,.2f}"),
                        html.Td(f"£{gross_profit_val:,.2f}"),
                        html.Td(f"£{operating_expenses_val:,.2f}"),
                        html.Td(f"£{ebitda_val:,.2f}"),
                        html.Td(f"£{depreciation_val:,.2f}"),
                        html.Td(f"£{ebit_val:,.2f}"),
                        html.Td(f"£{interest_expense_val:,.2f}"),
                        html.Td(f"£{taxes_val:,.2f}"),
                        html.Td(f"£{net_income_val:,.2f}"),
                    ]
                )
            )

        table_body = [html.Tbody(rows)]
        table = dbc.Table(table_header + table_body, bordered=True, striped=True)

        return html.Div([html.H3("Income Statement"), table])

    elif statement_type == "balance":
        # Display balance sheet
        df = pd.DataFrame(statements["balance_sheets"])

        # Similar structure for balance sheet display
        return html.Div([html.P("Balance sheet display will go here.")])

    else:  # cash flow statement
        # Display cash flow statement
        df = pd.DataFrame(statements["cash_flow_statements"])

        # Similar structure for cash flow statement display
        return html.Div([html.P("Cash flow statement display will go here.")])


# Callback to calculate investment analysis metrics
# This callback calculates and displays investment analysis metrics based on user inputs.
# It computes ROI, IRR, and payback period based on the budget, investment parameters, and OEE inputs.
# It also handles staffing inputs for business mode and uses sample data if no stored data is available.
# This logic has been migrated to globalinvestment_mgmt/callbacks/__init__.py
@app.callback(
    [
        Output("roi-metric", "children"),
        Output("irr-metric", "children"),
        Output("payback-metric", "children"),
    ],
    [
        Input("budget-slider", "value"),  # Changed from investment-slider
        Input("budget-timeframe", "value"),  # Added new input
        Input("investment-type-input", "value"),
        Input("investment-rate-input", "value"),
        Input("investment-lifespan-input", "value"),
        Input("investment-efficiency-input", "value"),
        # New OEE inputs
        Input("availability-input", "value"),
        Input("performance-input", "value"),
        Input("quality-input", "value"),
        # New staffing inputs
        Input("staff-count-input", "value"),
        Input("ramp-up-input", "value"),
        Input("training-cost-input", "value"),
    ],
    [State("financial-data-store", "data")],
)
def update_investment_metrics(
    budget: Optional[float],
    timeframe: Optional[int],
    investment_type: Optional[str],
    investment_rate: Optional[float],
    investment_lifespan: Optional[int],
    efficiency_impact: Optional[float],
    availability: Optional[float],
    performance: Optional[float],
    quality: Optional[float],
    staff_count: Optional[int],
    ramp_up: Optional[int],
    training_cost: Optional[float],
    stored_data: Optional[Dict[str, Any]],
) -> Tuple[str, str, str]:
    """Calculate and display investment analysis metrics."""
    from typing import (
        Dict,
        Any,
        cast,
    )  # Import at function level to ensure Any is in scope

    if budget is None or budget <= 0:
        return "N/A", "N/A", "N/A"

    # Default to sample data if no stored data with explicit typing
    financial_data: Dict[str, Any] = (
        stored_data
        if stored_data is not None
        else cast(Dict[str, Any], get_sample_data())
    )

    # Use timeframe for investment lifespan if available
    if timeframe:
        investment_lifespan = timeframe

    # Calculate baseline (no investment)
    baseline_df = project_financials(financial_data, months=60, investment_amount=0)

    # Calculate with investment
    investment_df = project_financials(
        financial_data,
        months=60,
        investment_amount=budget,  # Budget is already checked for None earlier in the function
        investment_type=investment_type,
        investment_rate=investment_rate if investment_rate is not None else 5.0,
        investment_lifespan=(
            investment_lifespan if investment_lifespan is not None else 5
        ),
        efficiency_impact=efficiency_impact if efficiency_impact is not None else 0,
        # New parameters - convert float to int
        oee_availability=int(availability) if availability is not None else 0,
        oee_performance=int(performance) if performance is not None else 0,
        oee_quality=int(quality) if quality is not None else 0,
        staff_count=staff_count if staff_count is not None else 1,
        ramp_up_period=ramp_up if ramp_up is not None else 3,
        training_cost=training_cost if training_cost is not None else 2000,
    )

    # Calculate incremental cash flows (difference between investment and baseline)
    incremental_cash_flows: List[float] = []
    for i in range(len(investment_df)):
        if i == 0:
            # Skip the initial month
            continue
        # Extract DataFrame from result if it's a tuple (handle both cases)
        if isinstance(investment_df, tuple):
            inv_df = investment_df[0]
        else:
            inv_df = investment_df

        if isinstance(baseline_df, tuple):
            base_df = baseline_df[0]
        else:
            base_df = baseline_df

        # Initialize variables with default values
        investment_value = 0.0
        baseline_value = 0.0

        # Use safer pandas value extraction with proper type handling
        try:
            # Extract values safely using .iat for single value access with explicit type
            from typing import Any  # Import only what we need

            # Use Any for initial extraction, then handle the type conversion explicitly
            inv_raw_value: Any = None
            if "cash_flow" in inv_df.columns:
                try:
                    # First get the value with proper type handling
                    # Import float for type hint and use explicit casting
                    from typing import Any, cast

                    # Get the value with explicit type annotation directly
                    inv_raw_value = cast(Any, inv_df["cash_flow"].iat[i])
                except (IndexError, KeyError):
                    inv_raw_value = None

            base_raw_value: Any = None
            if "cash_flow" in base_df.columns:
                try:
                    # Get the value with explicit type annotation and cast
                    from typing import cast

                    base_raw_value = cast(Any, base_df["cash_flow"].iat[i])
                except (IndexError, KeyError):
                    base_raw_value = None

            # Initialize values to defaults
            investment_value = 0.0
            baseline_value = 0.0

            # Use safe type handling for inv_raw_value
            if inv_raw_value is not None:
                # Use math.isnan rather than pd.isna for better type safety
                import math

                # First ensure we have a float value to check
                try:
                    # Explicitly cast to avoid type issues
                    from typing import cast

                    float_convertible = cast(float, inv_raw_value)
                    inv_float_value = float(float_convertible)
                    if math.isnan(inv_float_value):
                        investment_value = 0.0
                except (ValueError, TypeError):
                    # If we can't convert to float, treat as non-NaN
                    investment_value = 0.0
                else:
                    try:
                        # First convert to a Python primitive type that float can handle
                        # No need to cast since inv_raw_value is already Any
                        from typing import Any

                        inv_value_any = inv_raw_value  # inv_raw_value is already Any
                        if hasattr(inv_value_any, "item"):
                            # Handle numpy or pandas numeric type
                            numpy_value = inv_value_any
                            primitive_value = numpy_value.item()
                        else:
                            # Try string conversion as fallback
                            # inv_raw_value is already of type Any, no need to cast
                            primitive_value = str(inv_raw_value)
                        investment_value = float(primitive_value)
                    except (ValueError, TypeError, AttributeError):
                        investment_value = 0.0

            # Convert investment value to float with proper error handling
            if inv_raw_value is not None:
                # Convert to float directly instead of using pd.to_numeric
                from typing import Any

                # Handle None case directly without intermediate variable
                try:
                    if inv_raw_value is None:
                        investment_value = 0.0
                    # Handle numeric types directly
                    elif isinstance(inv_raw_value, (int, float)):
                        investment_value = float(inv_raw_value)
                    # Try string conversion for other types
                    else:
                        investment_value = float(str(inv_raw_value))
                except (ValueError, TypeError):
                    # Handle conversion errors
                    pass
                # Use pd.isna instead of math.isnan for better compatibility with pandas values
                # Convert to float and check for NaN using math.isnan which has clearer typing
                try:
                    # Handle numeric_result by first checking for NaN, then explicitly casting to float
                    import math

                    # First convert numeric_result to float and handle NaN cases
                    try:
                        # Convert to Python primitive type first
                        # Import Any and cast to satisfy the type checker's requirements for hasattr
                        from typing import cast, Any

                        # Directly convert to float instead of using pd.to_numeric
                        if inv_raw_value is None:
                            numeric_result = 0.0
                        else:
                            try:
                                # Try direct float conversion first
                                numeric_result = float(inv_raw_value)
                            except (ValueError, TypeError):
                                # Fall back to 0.0 if conversion fails
                                numeric_result = 0.0
                        numeric_result_any = cast(Any, numeric_result)
                        if hasattr(numeric_result_any, "item"):
                            # Handle numpy scalar types
                            primitive_value = numeric_result_any.item()
                        else:
                            # Use explicit cast to handle type checking
                            # First convert to string, then to float to avoid type errors
                            primitive_value = float(str(numeric_result_any))

                        float_numeric = float(primitive_value)
                        if math.isnan(float_numeric):
                            float_value = 0.0
                        else:
                            float_value = float_numeric
                    except (ValueError, TypeError):
                        float_value = 0.0
                    if not math.isnan(float_value):
                        investment_value = float_value
                except (ValueError, TypeError):
                    # If conversion fails, keep default value
                    pass

            # Convert baseline value to float with proper error handling
            if base_raw_value is not None:
                base_numeric = pd.to_numeric(base_raw_value, errors="coerce")  # type: ignore
                import math

                # Check if base_numeric is not None and not NaN before converting to float
                # Use isinstance to check the type before using math.isnan for clearer type inference
                if base_numeric is not None:
                    try:
                        # Check type explicitly before conversion
                        if isinstance(base_numeric, (int, float)):
                            base_numeric_float = float(base_numeric)
                            if not math.isnan(base_numeric_float):
                                baseline_value = base_numeric_float
                    except (ValueError, TypeError):
                        pass

            incremental_cf = investment_value - baseline_value
            incremental_cash_flows.append(incremental_cf)
        except (IndexError, KeyError, ValueError, TypeError):
            # Skip this iteration if there's an error accessing the data
            incremental_cash_flows.append(0.0)

    # Calculate investment metrics
    metrics = calculate_investment_metrics(
        incremental_cash_flows, budget
    )  # Changed from investment to budget

    # Format results with robust error handling
    try:
        roi = f"{metrics['roi']:.1f}%"
    except (TypeError, ValueError):
        roi = "N/A"

    try:
        irr = f"{metrics['irr']:.1f}%"
    except (TypeError, ValueError):
        irr = "N/A"

    payback = (
        f"{metrics['payback_period']:.1f} months"
        if metrics["payback_period"] < float("inf")
        else "N/A"
    )

    return roi, irr, payback


# Callback for investment comparison chart
# This callback generates a comparison chart between different investment options.
# It takes inputs for budget, investment parameters, and OEE/staffing metrics, and uses stored financial data or sample data if none is available.
# It handles None values for budget and investment parameters, and uses the budget slider value instead of investment slider.
# This logic has been migrated to investment_mgmt/callbacks/__init__.py
@app.callback(
    Output("investment-comparison-chart", "figure"),
    [
        Input("budget-slider", "value"),  # Changed from investment-slider
        Input("budget-timeframe", "value"),  # Added new input
        Input("investment-type-input", "value"),
        Input("investment-rate-input", "value"),
        Input("investment-lifespan-input", "value"),
        Input("investment-efficiency-input", "value"),
        Input("alternative-investment-type", "value"),
        Input("alternative-rate-input", "value"),
        # New OEE inputs
        Input("availability-input", "value"),
        Input("performance-input", "value"),
        Input("quality-input", "value"),
        # New staffing inputs
        Input("staff-count-input", "value"),
        Input("ramp-up-input", "value"),
        Input("training-cost-input", "value"),
    ],
    [State("financial-data-store", "data")],
)
def update_investment_comparison(
    budget: Optional[float],
    timeframe: Optional[int],
    investment_type: Optional[str],
    investment_rate: Optional[float],
    investment_lifespan: Optional[int],
    efficiency_impact: Optional[float],
    alt_type: Optional[str],
    alt_rate: Optional[float],
    availability: Optional[float],
    performance: Optional[float],
    quality: Optional[float],
    staff_count: Optional[int],
    ramp_up: Optional[int],
    training_cost: Optional[float],
    stored_data: Optional[Dict[str, Any]],
) -> "Figure":
    """Generate a comparison chart between different investment options."""
    # Default to sample data if no stored data with explicit typing
    # Import typing utilities locally to ensure they're available
    from typing import Dict, Any, cast

    # Handle stored_data more explicitly for type checking
    if stored_data is not None:
        # Convert to Dict[str, Any] with proper type annotation
        financial_data: Dict[str, Any] = dict(stored_data)
    else:
        # Create sample data with explicit typing
        sample_data: Dict[str, Any] = cast(Dict[str, Any], get_sample_data())
        financial_data = dict(sample_data)

    # Use timeframe for investment lifespan if available
    if timeframe:
        investment_lifespan = timeframe

    # Calculate baseline (no investment)
    baseline_df = project_financials(financial_data, months=60, investment_amount=0)

    # Calculate with primary investment
    primary_result = project_financials(
        financial_data,
        months=60,
        investment_amount=(
            budget if budget is not None else 0.0
        ),  # Provide default when None
        investment_type=investment_type,
        investment_rate=investment_rate if investment_rate is not None else 5.0,
        investment_lifespan=(
            investment_lifespan if investment_lifespan is not None else 5
        ),
        efficiency_impact=efficiency_impact if efficiency_impact is not None else 0,
        # New parameters
        oee_availability=availability if availability is not None else 0,
        oee_performance=performance if performance is not None else 0,
        oee_quality=quality if quality is not None else 0,
        staff_count=staff_count if staff_count is not None else 1,
        ramp_up_period=ramp_up if ramp_up is not None else 3,
        training_cost=training_cost if training_cost is not None else 2000,
    )

    # Extract DataFrame from result if it's a tuple
    if isinstance(primary_result, tuple):
        primary_df = primary_result[0]
    else:
        primary_df = primary_result

    # Calculate with alternative investment if selected
    if alt_type == "none":
        # Handle both single DataFrame and tuple returns for baseline_df
        if isinstance(baseline_df, tuple):
            alt_df = baseline_df[0].copy()
        else:
            alt_df = baseline_df.copy()
        alt_name = "No Investment (Baseline)"
    else:
        alt_result = project_financials(
            financial_data,
            months=60,
            investment_amount=(
                budget if budget is not None else 0.0
            ),  # Changed from investment to budget
            investment_type=alt_type,
            investment_rate=alt_rate if alt_rate is not None else 3.0,
            investment_lifespan=(
                investment_lifespan if investment_lifespan is not None else 5
            ),
            efficiency_impact=efficiency_impact if efficiency_impact is not None else 0,
            # For simplicity, use same OEE/staffing parameters for alt investment - convert float to int
            oee_availability=int(availability) if availability is not None else 0,
            oee_performance=int(performance) if performance is not None else 0,
            oee_quality=int(quality) if quality is not None else 0,
            staff_count=staff_count if staff_count is not None else 1,
            ramp_up_period=ramp_up if ramp_up is not None else 3,
            training_cost=training_cost if training_cost is not None else 2000,
        )
        # Extract DataFrame from result if it's a tuple
        if isinstance(alt_result, tuple):
            alt_df = alt_result[0]
        else:
            alt_df = alt_result
        alt_name = (
            f"{alt_type.title() if alt_type is not None else 'Alternative'} Investment"
        )

    # Create comparison chart
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(  # type: ignore
            x=primary_df["date"],
            y=primary_df["net_worth"],
            name=f"{investment_type.title() if investment_type else 'Default'} Investment",
            line=dict(color="#1f77b4", width=2),
        )
    )

    # Cast figure to Any to resolve type checking issues
    from typing import cast, Any

    cast(Any, fig).add_trace(
        go.Scatter(
            x=alt_df["date"],
            y=alt_df["net_worth"],
            name=alt_name,
            line=dict(color="#ff7f0e", width=2),
        )
    )

    fig.update_layout(  # type: ignore
        title=f"Investment Comparison: {investment_type.title() if investment_type else 'Default'} vs {alt_name}",
        xaxis_title="Date",
        yaxis_title="Net Worth (£)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode="x unified",
    )

    return fig


# This callback validates the investment cost input.
# It checks if the input is None or empty and returns an appropriate message.
# This logic has been migrated to investment_mgmt/callbacks/__init__.py
@app.callback(
    Output("cost-validation-output", "children"),
    Input("investment-cost-input", "value"),
)
def validate_cost(value: Optional[float]) -> str:
    if value is None:
        return "Please enter a cost value"
    return ""


# Replace the current misplaced function definition with this complete version:
# This call will add a new investment to the table and store it in the investments store.
# This callback has been migrated to investment management/callbacks/__init__.py
@app.callback(
    [
        Output("investments-table", "data"),
        Output("investments-store", "data"),
        # Clear form fields
        Output("investment-mgmt-name-input", "value"),
        Output("investment-mgmt-type-input", "value"),
        Output("investment-cost-input", "value"),
        Output("investment-savings-input", "value"),
        Output("implementation-time-input", "value"),
        Output("investment-efficiency-input", "value"),
        Output("risk-slider", "value"),
    ],
    [Input("add-investment-button", "n_clicks")],
    [
        State("investment-mgmt-name-input", "value"),
        State("investment-mgmt-type-input", "value"),
        State("investment-cost-input", "value"),
        State("investment-savings-input", "value"),
        State("implementation-time-input", "value"),
        State("investment-efficiency-input", "value"),
        State("risk-slider", "value"),
        # Capital Equipment Parameters
        State("oee-current-availability-input", "value"),
        State("oee-current-performance-input", "value"),
        State("oee-current-quality-input", "value"),
        State("oee-availability-improvement-input", "value"),
        State("oee-performance-improvement-input", "value"),
        State("oee-quality-improvement-input", "value"),
        State("equipment-hourly-rate-input", "value"),
        State("operating-hours-input", "value"),
        State("maintenance-reduction-input", "value"),
        # Process Improvement Parameters
        State("current-cycle-time-input", "value"),
        State("current-downtime-input", "value"),
        State("current-defect-rate-input", "value"),
        State("cycle-time-reduction-input", "value"),
        State("downtime-reduction-input", "value"),
        State("defect-reduction-input", "value"),
        State("product-value-input", "value"),
        State("production-volume-input", "value"),
        State("material-cost-input", "value"),
        # New States
        State("investment-scope-input", "value"),
        State("production-line-selector", "value"),
        State("implementation-start-date", "date"),
        State("implementation-end-date", "date"),
        State("implementation-status", "value"),
        # Existing data
        State("investments-table", "data"),
        State("investments-store", "data"),
    ],
    prevent_initial_call=True,
)
def add_investment(
    n_clicks: int,
    name: str,
    inv_type: str,
    cost: Optional[float],
    savings: Optional[float],
    impl_time: Optional[int],
    efficiency: Optional[float],
    risk: Optional[int],
    # Capital Equipment Parameters
    oee_current_availability: Union[float, None],
    oee_current_performance: Union[float, None],
    oee_current_quality: Union[float, None],
    oee_availability_improvement: float,
    oee_performance_improvement: float,
    oee_quality_improvement: float,
    equipment_hourly_rate: float,
    operating_hours: float,
    maintenance_reduction: float,
    # Process Improvement Parameters
    current_cycle_time: float,
    current_downtime: float,
    current_defect_rate: float,
    cycle_time_reduction: float,
    downtime_reduction: float,
    defect_reduction: float,
    product_value: float,
    production_volume: int,
    material_cost: float,
    # New States
    scope: Optional[str],
    production_lines: Optional[List[str]],
    implementation_start_date: Optional[str],
    implementation_end_date: Optional[str],
    implementation_status: Optional[str],
    # Existing data
    current_table_data: Optional[list[dict[str, Any]]],
    stored_investments: Optional[list[dict[str, Any]]],
):
    """Add a new investment to the table and store it."""
    try:
        print(f"Add investment clicked: {n_clicks}")
        print(f"Investment name: {name}, type: {inv_type}, cost: {cost}")
        print(f"Cost type: {type(cost).__name__ if cost is not None else 'None'}")

        # Check if we have valid data to add
        if not name or not inv_type or not cost:
            # Return existing data and don't clear form if validation fails
            return (
                current_table_data or [],
                stored_investments or [],
                name,
                inv_type,
                cost,
                savings,
                impl_time,
                efficiency,
                risk,
            )

        # Initialize calculated savings
        calculated_savings = savings if savings is not None else 0

        # Create the investment object with updated type annotation to include all possible types
        investment: Dict[str, Union[str, float, int, List[str], None]] = {
            "name": name,
            "type": inv_type,
            "cost": float(cost or 0),
            "savings": float(calculated_savings or 0),
            "implementation_time": impl_time or 3,
            "efficiency": efficiency or 5,
            "risk": risk or 3,
            "roi": (
                float(calculated_savings or 0) / float(cost or 1)
                if cost and calculated_savings
                else 0
            ),
            "scope": scope or "department",
            "production_lines": (
                ", ".join(map(str, production_lines))
                if scope == "line" and production_lines
                else ""
            ),
            "implementation_start": implementation_start_date,
            "implementation_end": implementation_end_date,
            "status": implementation_status or "planned",
        }

        # Make safe copies of data with proper type annotation
        # Use a more inclusive type annotation that matches the investment dictionary
        table_data: List[Dict[str, Union[str, float, int, List[str], None]]] = (
            [] if not current_table_data else list(current_table_data)
        )
        # No need to check instance type since the type annotation guarantees it's a list

        # Handle stored_investments based on its current type
        if stored_investments is None:
            investments: List[Dict[str, Union[str, float, int, List[str], None]]] = []
        # If it's a dict, convert to list (handle possible single investment case)
        elif isinstance(stored_investments, dict):
            # Single investment stored as dict - convert to list
            investments = [stored_investments]
        # Otherwise use as list (as per type annotation)
        else:
            investments = list(stored_investments)

        table_data.append(investment)
        investments.append(investment)

        print(f"Added investment to table: {name}")
        print(f"Table now has {len(table_data)} investments")
        print(f"Investment store now has {len(investments)} investments")
        if table_data:
            print(f"First investment type: {type(table_data[0]).__name__}")

        # Return updated data and clear form fields
        return table_data, investments, "", None, None, None, None, None, 3

    except Exception as e:
        # Collect the error without storing the return value
        collect_error("add_investment")
        print(f"Error in add_investment: {str(e)}")
        # Return existing data and don't clear form if an error occurs
        return (
            current_table_data or [],
            stored_investments or [],
            name,
            inv_type,
            cost,
            savings,
            impl_time,
            efficiency,
            risk,
        )


# This callback updates the investments table from the stored data.
# It uses the stored data to populate the table, allowing for dynamic updates.
# This callback is triggered by changes in the investments store.
# It also includes a check to avoid updates when the table is being cleared or deleted.
# This callback has been migrated to investment management/callbacks/__init__.py
@app.callback(
    Output("investments-table", "data", allow_duplicate=True),
    Input("investments-store", "data"),
    prevent_initial_call=True,
    # Add a callback_context check in the function to avoid updates from deletion actions
)
def update_investments_table(
    stored_data: Optional[Union[List[Dict[str, Any]], Dict[str, Any]]],
) -> Union[List[Dict[str, Any]], Any]:
    """Update investments table from stored data."""
    from typing import Any, List, Dict

    try:
        ctx = callback_context

        # Skip update if triggered by a deletion operation
        # Use triggered property which is a list of dictionaries with known structure
        if ctx.triggered and len(ctx.triggered) > 0:
            # Get the property ID string directly from the triggered list
            # Use proper type annotation with cast to ensure type safety
            from typing import cast, Dict, Any

            # First cast the trigger object to a dictionary type
            trigger_dict = cast(Dict[str, Any], ctx.triggered[0])
            trigger_id_str: str = (
                cast(str, trigger_dict["prop_id"])
                if trigger_dict.get("prop_id") is not None
                else ""
            )
            # Check if the representation contains 'investments-table'
            if "investments-table" in trigger_id_str:
                return dash.no_update

        # Safely get the type name
        if stored_data is not None:
            try:
                # Get type safely without using cast
                from typing import Any

                type_obj = type(stored_data)
                type_name = (
                    type_obj.__name__
                    if hasattr(type_obj, "__name__")
                    else repr(type_obj)
                )
            except:
                type_name = "Unknown"
        else:
            type_name = "None"

        print(f"Type of stored_data: {type_name}")

        if (
            stored_data is not None
            and hasattr(stored_data, "__len__")
            and len(stored_data) > 0
        ):
            try:
                # Check data structure type with proper type handling
                if isinstance(
                    stored_data, (list, tuple)
                ):  # Explicitly check if it's a list or tuple
                    from typing import cast, List, Any

                    # Use cast to tell type checker this is a list
                    list_data = cast(List[Any], stored_data)
                    first_item = list_data[0] if list_data else None
                elif hasattr(stored_data, "keys") and not isinstance(stored_data, list):
                    # For dictionaries, get first key's value
                    first_key = next(iter(stored_data.keys()))
                    first_item = stored_data[first_key]
                else:
                    first_item = None

                if first_item is not None:
                    first_item_type = type(first_item).__name__
                else:
                    first_item_type = "None"
            except (IndexError, TypeError, AttributeError):
                first_item_type = "Unknown"
            print(f"First item type: {first_item_type}")

        # Handle case where stored_data might be empty
        if not stored_data:
            return []

        # Handle case where stored_data might be a single dict
        if hasattr(stored_data, "keys") and not isinstance(stored_data, list):
            print("Converting single dict to list for table")
            return [stored_data]

        # Normal case: stored_data is a list
        table_data: List[Dict[str, Union[str, float, int]]] = []
        # Add type annotation for the loop
        stored_data_list: List[Union[Dict[str, Any], str]] = cast(
            List[Union[Dict[str, Any], str]], stored_data
        )
        for investment_item in stored_data_list:
            # Handle strings if any are still present
            if isinstance(investment_item, str):
                try:
                    import json

                    investment_dict = json.loads(investment_item)
                except Exception as e:
                    print(f"Failed to parse investment as JSON: {e}")
                    # Skip invalid items
                    continue
            else:
                investment_dict = investment_item

            # Now we can safely access dictionary methods
            table_data.append(
                {
                    "name": investment_dict.get("name", ""),
                    "type": investment_dict.get("type", ""),
                    "cost": investment_dict.get("cost", 0),
                    "savings": investment_dict.get("savings", 0),
                    "implementation_time": investment_dict.get(
                        "implementation_time", 0
                    ),
                    "efficiency": investment_dict.get("efficiency", 0),
                    "risk": investment_dict.get("risk", 0),
                    "roi": investment_dict.get("roi", 0),
                }
            )

        print(f"Table data created with {len(table_data)} items")
        return table_data

    except Exception as e:
        # Collect the error
        collect_error("update_investments_table")
        print(f"Error in update_investments_table: {str(e)}")
        # Return empty data instead of crashing
        return []


# This callback updates the investments store when rows are deleted from the table.
# It compares the previous and current table data to determine which rows were deleted.
# Type ignore here because Dash's callback typing is complex and dynamically generated
# This callback has been migrated to shared/callbacks/__init__.py
@app.callback(  # type: ignore
    [Output("investments-store", "data", allow_duplicate=True)],
    [Input("investments-table", "data_previous"), Input("investments-table", "data")],
    [State("investments-store", "data")],
    prevent_initial_call=True,
)
def update_investments_store(
    previous_table: Optional[List[Dict[str, Any]]],
    current_table: Optional[List[Dict[str, Any]]],
    stored_investments: Optional[List[Dict[str, Any]]],
) -> List[Dict[str, Any]]:
    """Update the investments store when rows are deleted from the table."""
    if previous_table is None or current_table is None:
        return stored_investments or []  # Return data directly, not wrapped

    # If stored_investments is None, use an empty list
    investments = stored_investments or []

    # If a row was deleted
    if len(current_table) < len(previous_table):
        # Find the deleted row by comparing the two tables
        deleted_names = {row["name"] for row in previous_table} - {
            row["name"] for row in current_table
        }

        if deleted_names:
            # Filter the store to remove deleted investments
            new_store = [
                inv for inv in investments if inv.get("name", "") not in deleted_names
            ]
            print(
                f"Deleted {len(deleted_names)} investment(s): {', '.join(deleted_names)}"
            )
            print(f"Store now has {len(new_store)} investments")
            return new_store  # Return data directly without wrapping in another list

    return investments  # Return data directly, not wrapped


# This callback updates the investment totals displayed on the dashboard.
# It calculates the total investment cost, total annual savings, and average ROI based on the investments table data.
# It uses the investments table data to compute these values and updates the display accordingly.
# Update investment totals
# This callback has been migrated to shared/callbacks/__init__.py
@app.callback(
    [
        Output("total-investment-cost", "children", allow_duplicate=True),
        Output("total-annual-savings", "children"),
        Output("average-roi", "children"),
    ],
    [Input("investments-table", "data")],
    prevent_initial_call=True,
)
def update_investment_totals(investments):
    try:
        # Initialize variables
        total_cost = 0.0
        total_savings = 0.0

        # Make sure we have data to process
        data = investments if investments else []

        for item in data:
            # Get cost value, default to 0 if missing or None
            cost_val = item.get("cost", 0)
            if cost_val is not None:
                try:
                    total_cost += float(cost_val)
                except (ValueError, TypeError):
                    pass  # Skip invalid values

            # Get savings value, default to 0 if missing or None
            savings_val = item.get("savings", 0)
            if savings_val is not None:
                try:
                    total_savings += float(savings_val)
                except (ValueError, TypeError):
                    pass  # Skip invalid values

        # Calculate ROI
        avg_roi = (total_savings / total_cost * 100) if total_cost > 0 else 0

        # Format the outputs
        return f"£{total_cost:,.2f}", f"£{total_savings:,.2f}/year", f"{avg_roi:.1f}%"

    except Exception as e:
        print(f"Error in update_investment_totals: {str(e)}")
        return "£0", "£0/year", "0%"


# This callback updates the status message after adding an investment.
# It checks if the investment name, type, and cost are provided, and returns an appropriate message.
# This callback has been migrated to investment management/callbacks/__init__.py
@app.callback(
    Output("investment-add-status", "children"),
    [Input("add-investment-button", "n_clicks")],
    [
        State("investment-mgmt-name-input", "value"),
        State("investment-mgmt-type-input", "value"),
        State("investment-cost-input", "value"),
    ],
    prevent_initial_call=True,
)
def update_investment_add_status(
    n_clicks: Optional[int],
    name: Optional[str],
    inv_type: Optional[str],
    cost: Optional[float],
) -> html.Span:
    """Show status message after adding investment."""
    if not name:
        return html.Span("Please enter investment name", style={"color": "red"})

    if not inv_type:
        return html.Span("Please select investment type", style={"color": "red"})

    if not cost:
        return html.Span("Please enter investment cost", style={"color": "red"})

    return html.Span("Investment added successfully!", style={"color": "green"})


# This callback updates the budget allocation chart based on selected criteria and display options.
# It generates a Plotly figure showing the budget allocation across different investments.
# This callback has been migrated to shared/callbacks/__init__.py
@app.callback(
    [
        Output("budget-allocation-chart", "figure"),
        Output("budget-utilization-display", "children"),
    ],
    [
        Input("investments-store", "data"),
        Input("budget-slider", "value"),
        Input("prioritization-criteria", "value"),
        Input("display-options", "value"),
    ],
)
def update_budget_allocation_chart(
    investments: Optional[List[Dict[str, Any]]],
    budget: Optional[float],
    criteria: Optional[List[str]],
    display_options: Optional[List[str]],
) -> Tuple["Figure", html.Div]:
    """
    Generate a budget allocation chart based on selected criteria and display options.
    Features smooth updates when budget changes.
    """
    try:
        # Import Any at the beginning of the function to ensure it's available in this scope
        from typing import Any, Dict, List

        # Debug info
        print(f"Budget chart update - investments type: {type(investments).__name__}")
        print(
            f"Investments length: {len(investments) if investments is not None and hasattr(investments, '__len__') else 'N/A'}"
        )

        # Create empty chart if no investments
        if not investments:
            empty_fig = go.Figure()
            # Cast to Any to bypass type checking limitations with Plotly
            from typing import cast, Any

            cast(Any, empty_fig).update_layout(
                title="Investment Budget Allocation",
                xaxis_title="Investments",
                yaxis_title="Cost (£)",
                yaxis_range=[0, budget * 1.1] if budget else [0, 100000],
                template="plotly_white",
                showlegend=False,
            )
            # Cast to Any to bypass type checking issues with Plotly
            from typing import cast, Any

            cast(Any, empty_fig).add_annotation(
                text="No investments available",
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5,
                showarrow=False,
            )

            utilization_info = html.Div(
                [
                    html.H6("Budget Utilization:"),
                    html.P(f"£0 / £{budget or 0:,.0f}"),
                    html.P("0% of budget allocated"),
                ]
            )

            return empty_fig, utilization_info

        # Handle different investment data types
        parsed_investments: List[Dict[str, Any]] = []
        if isinstance(investments, dict):
            # Single investment
            parsed_investments = [investments]
        else:
            # Process each investment (investments is already a list based on type annotation)
            for inv in investments:
                if isinstance(inv, str):
                    try:
                        import json

                        parsed_inv = json.loads(inv)
                        parsed_investments.append(parsed_inv)
                    except:
                        # Skip invalid items
                        continue
                else:
                    # Already a dict or other object - try to use as is
                    parsed_investments.append(inv)
        # No need for another else block since empty list case is handled at the beginning

        # Ensure we have criteria and display options (defensive coding)
        if criteria is None:
            criteria = ["roi"]  # Default to ROI if none selected

        if display_options is None:
            display_options = ["budget_line", "cumulative"]

        # Define weights for prioritization
        weights = {
            "roi": 0.5 if "roi" in criteria else 0,
            "risk": 0.2 if "risk" in criteria else 0,
            "time": 0.1 if "time" in criteria else 0,
            "efficiency": 0.1 if "efficiency" in criteria else 0,
            "savings": 0.1 if "savings" in criteria else 0,
        }

        # Normalize weights to sum to 1
        total_weight = sum(weights.values()) or 1  # Avoid division by zero
        weights = {k: v / total_weight for k, v in weights.items()}

        # Calculate score for each investment
        scored_investments: List[Dict[str, Any]] = []
        for inv in parsed_investments:
            try:
                # Extract values safely
                roi = float(inv.get("roi", 0) or 0)
                risk = float(inv.get("risk", 3) or 3)
                impl_time = float(inv.get("implementation_time", 6) or 6)
                efficiency = float(inv.get("efficiency", 0) or 0)
                savings = float(inv.get("savings", 0) or 0)

                # Normalize values
                norm_roi = roi  # Already a ratio
                norm_risk = (6 - risk) / 5  # Invert risk (lower is better)
                norm_time = 1 / (impl_time or 1)  # Invert time (shorter is better)
                norm_efficiency = efficiency / 100  # Convert to ratio

                # Find max savings for normalizing
                all_savings = [
                    float(i.get("savings", 0) or 0) for i in parsed_investments
                ]
                max_savings = max(all_savings) if all_savings else 1
                norm_savings = savings / max_savings if max_savings else 0

                # Calculate composite score
                score = (
                    weights["roi"] * norm_roi
                    + weights["risk"] * norm_risk
                    + weights["time"] * norm_time
                    + weights["efficiency"] * norm_efficiency
                    + weights["savings"] * norm_savings
                )

                # Copy investment and add score
                scored_inv = dict(inv)
                scored_inv["priority_score"] = score
                scored_investments.append(scored_inv)
            except Exception as e:
                print(f"Error scoring investment {inv.get('name', 'unknown')}: {e}")
                continue

        # Sort by score (highest first)
        sorted_investments = sorted(
            scored_investments, key=lambda x: x.get("priority_score", 0), reverse=True
        )

        # Select investments within budget
        selected: List[Dict[str, Any]] = []
        unselected: List[Dict[str, Any]] = []
        running_total: float = 0.0

        # Default budget if not provided
        if budget is None:
            budget = 0

        for inv in sorted_investments:
            cost = float(inv.get("cost", 0) or 0)
            if running_total + cost <= budget:
                selected.append(inv)
                running_total += cost
            else:
                unselected.append(inv)

        # Create figure
        fig = go.Figure()

        # Color mapping
        color_map = {
            "capital": "#1f77b4",  # Blue
            "process": "#ff7f0e",  # Orange
            "people": "#2ca02c",  # Green
            "software": "#d62728",  # Red
            "facility": "#9467bd",  # Purple
            "other": "#8c564b",  # Brown
        }

        # Add bars and track cumulative
        cumulative_x: List[int] = []
        cumulative_y: List[float] = []
        running_sum: float = 0.0

        # Add selected investments
        for i, inv in enumerate(selected):
            name = inv.get("name", f"Investment {i+1}")
            cost = float(inv.get("cost", 0) or 0)
            inv_type = str(inv.get("type", "other")).lower()
            roi = float(inv.get("roi", 0) or 0)

            fig.add_trace(
                go.Bar(  # type: ignore
                    x=[i],
                    y=[cost],
                    name=name,
                    text=f"{name}<br>£{cost:,.0f}<br>ROI: {roi:.1%}",
                    hoverinfo="text",
                    marker_color=color_map.get(inv_type, color_map["other"]),
                    showlegend=False,
                )
            )

            # Update cumulative
            running_sum += cost
            cumulative_x.append(i)
            cumulative_y.append(running_sum)

        # Add unselected if requested
        if "unselected" in display_options:
            for j, inv in enumerate(unselected):
                i = j + len(selected)
                name = inv.get("name", f"Investment {i+1}")
                cost = float(inv.get("cost", 0) or 0)
                inv_type = str(inv.get("type", "other")).lower()
                roi = float(inv.get("roi", 0) or 0)

                fig.add_trace(
                    go.Bar(  # type: ignore
                        x=[i],
                        y=[cost],
                        name=name,
                        text=f"{name} (Over Budget)<br>£{cost:,.0f}<br>ROI: {roi:.1%}",
                        hoverinfo="text",
                        marker_color=color_map.get(inv_type, color_map["other"]),
                        marker_opacity=0.4,
                        showlegend=False,
                    )
                )

        # Add cumulative line
        if "cumulative" in display_options and cumulative_x:
            fig.add_trace(
                go.Scatter(  # type: ignore
                    x=cumulative_x,
                    y=cumulative_y,
                    mode="lines+markers",
                    name="Cumulative Cost",
                    line=dict(color="red", width=3),
                    hoverinfo="y",
                    text=[f"Cumulative: £{y:,.0f}" for y in cumulative_y],
                )
            )

        # Add budget line
        if "budget_line" in display_options:
            display_width = len(selected) + (
                len(unselected) if "unselected" in display_options else 0
            )
            display_width = max(1, display_width)  # At least 1 for drawing

            # Cast to Any to bypass type checking limitations with Plotly
            from typing import cast, Any

            cast(Any, fig).add_shape(
                type="line",
                x0=-0.5,
                y0=budget,
                x1=display_width - 0.5,
                y1=budget,
                line=dict(color="green", width=2, dash="dash"),
            )

            # Budget annotation
            if selected:
                # Cast to Any to bypass type checking limitations with Plotly
                cast(Any, fig).add_annotation(
                    x=len(selected) / 2,
                    y=budget,
                    text=f"Budget Limit: £{budget:,.0f}",
                    showarrow=False,
                    yshift=10,
                    font=dict(color="green"),
                )

        # Update layout
        chart_max = (
            max(budget * 1.1, running_sum * 1.1) if budget or running_sum else 100000
        )
        # Cast to Any to bypass type checking limitations with Plotly
        from typing import cast, Any

        fig_any = cast(Any, fig)
        fig_any.update_layout(
            title="Investment Budget Allocation",
            xaxis_title="Prioritized Investments",
            yaxis_title="Cost (£)",
            yaxis_range=[0, chart_max],
            template="plotly_white",
            margin=dict(l=50, r=50, t=50, b=50),
            hovermode="closest",
            transition_duration=500,  # Smooth animation
        )

        # Add tick labels if we have investments
        if selected or (unselected and "unselected" in display_options):
            shown_investments = selected + (
                unselected if "unselected" in display_options else []
            )
            # Cast to Any to bypass type checking limitations with Plotly
            from typing import cast, Any

            cast(Any, fig).update_layout(
                xaxis=dict(
                    tickmode="array",
                    tickvals=list(range(len(shown_investments))),
                    ticktext=[
                        inv.get("name", f"Inv {i+1}")
                        for i, inv in enumerate(shown_investments)
                    ],
                )
            )

        # Create utilization display
        pct_utilized = (running_sum / budget * 100) if budget and budget > 0 else 0
        utilization_info = html.Div(
            [
                html.H6("Budget Utilization:"),
                html.P(f"£{running_sum:,.0f} / £{budget:,.0f}"),
                html.Div(
                    [
                        html.Span(
                            f"{pct_utilized:.1f}% of budget allocated",
                            style={"color": "green" if pct_utilized <= 100 else "red"},
                        )
                    ]
                ),
                html.Hr(),
                html.H6("Investments:"),
                html.P(f"{len(selected)} selected, {len(unselected)} excluded"),
                html.P(
                    f"Average ROI: {(sum([float(inv.get('roi', 0) or 0) for inv in selected]) / len(selected) if selected else 0):.1%}"
                ),
            ]
        )

        return fig, utilization_info

    except Exception as e:
        # Use error collector
        collect_error("update_budget_allocation_chart")
        print(f"Error in budget allocation chart: {str(e)}")

        # Return fallback figure
        error_fig = go.Figure()
        # Cast to Any to bypass type checking limitations with Plotly
        from typing import cast, Any

        cast(Any, error_fig).add_annotation(
            text=f"Error rendering chart: {str(e)}",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(color="red"),
        )

        error_info = html.Div(
            [html.H6("Error in chart:"), html.P(str(e), style={"color": "red"})]
        )

        return error_fig, error_info


# This function is already defined above with a callback decorator
# This callback updates the investment summary statistics displayed on the dashboard.
# It generates a summary of the investments, including total cost, annual savings, ROI, andpayback period, and displays it in a formatted HTML div.
# It uses the investments store data to compute these values and updates the display accordingly.
# This callback has been migrated to shared/callbacks/__init__.py
@app.callback(
    Output("investment-summary-stats", "children"), Input("investments-store", "data")
)
def update_investment_summary(investments: Optional[List[Dict[str, Any]]]) -> html.Div:
    """Generate summary statistics about investments."""
    if not investments:
        return html.Div([html.P("No investments available.")])

    try:
        # Calculate totals
        total_investments = len(investments)
        total_cost = sum(float(inv.get("cost", 0) or 0) for inv in investments)
        total_annual_savings = sum(
            float(inv.get("savings", 0) or 0) for inv in investments
        )

        # Count by status
        completed = sum(1 for inv in investments if inv.get("status") == "completed")
        in_progress = sum(
            1 for inv in investments if inv.get("status") == "in_progress"
        )
        planned = total_investments - completed - in_progress

        # Calculate average ROI
        if total_cost > 0:
            overall_roi = total_annual_savings / total_cost
        else:
            overall_roi = 0

        # Calculate payback period (years)
        if total_annual_savings > 0:
            payback_period = total_cost / total_annual_savings
        else:
            payback_period = float("inf")

        # Create summary
        return html.Div(
            [
                html.Div(
                    [
                        html.Div(
                            [
                                html.H6("Total Investments"),
                                html.P(f"{total_investments}", className="stat-value"),
                            ],
                            className="summary-stat",
                        ),
                        html.Div(
                            [
                                html.H6("Total Cost"),
                                html.P(f"£{total_cost:,.0f}", className="stat-value"),
                            ],
                            className="summary-stat",
                        ),
                        html.Div(
                            [
                                html.H6("Annual Savings"),
                                html.P(
                                    f"£{total_annual_savings:,.0f}",
                                    className="stat-value",
                                ),
                            ],
                            className="summary-stat",
                        ),
                    ],
                    className="stat-row",
                ),
                html.Div(
                    [
                        html.Div(
                            [
                                html.H6("Overall ROI"),
                                html.P(f"{overall_roi:.1%}", className="stat-value"),
                            ],
                            className="summary-stat",
                        ),
                        html.Div(
                            [
                                html.H6("Payback Period"),
                                html.P(
                                    (
                                        f"{payback_period:.1f} years"
                                        if payback_period < 100
                                        else "N/A"
                                    ),
                                    className="stat-value",
                                ),
                            ],
                            className="summary-stat",
                        ),
                        html.Div(
                            [
                                html.H6("Status Breakdown"),
                                html.P(
                                    [
                                        html.Span(
                                            f"{completed} Completed",
                                            style={"color": "green"},
                                        ),
                                        html.Span(" • "),
                                        html.Span(
                                            f"{in_progress} In Progress",
                                            style={"color": "orange"},
                                        ),
                                        html.Span(" • "),
                                        html.Span(
                                            f"{planned} Planned",
                                            style={"color": "blue"},
                                        ),
                                    ],
                                    className="stat-value",
                                ),
                            ],
                            className="summary-stat",
                        ),
                    ],
                    className="stat-row",
                ),
            ]
        )

    except Exception as e:
        collect_error("update_investment_summary")
        return html.Div(f"Error generating summary: {str(e)}", style={"color": "red"})


# This callback updates the cumulative savings chart based on the investments store data.
# It generates a Plotly figure showing cumulative savings over time, allowing users to visualize the impact of investments on savings across a specified date range.
# This callback has been migrated to shared/callbacks/__init__.py
@app.callback(
    Output("cumulative-savings-chart", "figure"), Input("investments-store", "data")
)
def update_cumulative_savings_chart(
    investments: Optional[List[Dict[str, Any]]],
) -> Figure:
    """Create a chart showing cumulative savings over time."""
    import pandas as pd

    if not investments:
        return create_empty_cumulative_chart()

    try:
        # Get current date for reference
        current_date = pd.Timestamp.now()

        # Create date range from 12 months ago to 5 years in the future
        start_date = current_date - pd.DateOffset(months=12)
        end_date = current_date + pd.DateOffset(years=5)
        date_range = pd.date_range(start=start_date, end=end_date, freq="M")

        # Initialize dataframe
        df = pd.DataFrame({"date": date_range})
        df["monthly_savings"] = 0.0  # Explicitly initialize as float
        df["cumulative_savings"] = 0.0  # Explicitly initialize as float

        # Add savings from each investment
        for inv in investments:
            # Define name with default value before try block to avoid "name is possibly unbound" error
            name = "Unknown"
            try:
                # Extract values safely
                name = inv.get("name", "Unnamed")
                savings = float(inv.get("savings", 0) or 0)
                monthly_savings = savings / 12

                # Get implementation dates with fallbacks
                try:
                    # Import and use pandas directly for type safety
                    import pandas as pd

                    implementation_start = inv.get("implementation_start")
                    if implementation_start is not None:
                        # Convert to string explicitly first
                        start_date_str = str(implementation_start)
                        # Parse as datetime with proper handling for NaT return value
                        try:
                            # First get the result without explicit type annotation
                            # Use a more direct approach with pd.isna() to avoid type issues
                            from typing import cast, Any

                            # Convert the string to datetime and handle the result
                            try:
                                # Handle potential NaT result explicitly
                                # Use try-except instead of pd.isna() to avoid type checking issues
                                # Use typing imports only
                                from typing import cast

                                # Use a more explicit approach to avoid type checking issues
                                from typing import cast, Any

                                # Use try-except with Timestamp constructor for clearer type handling
                                try:
                                    # Use pandas Timestamp constructor directly which has clearer typing
                                    start_date = pd.Timestamp(str(start_date_str))
                                except ValueError:
                                    # If conversion fails, use fallback value
                                    start_date = current_date - pd.DateOffset(months=3)
                            except:
                                # Fallback for any unexpected issues
                                start_date = current_date - pd.DateOffset(months=3)
                        except Exception:
                            # Fallback for any parsing errors
                            start_date = current_date - pd.DateOffset(months=3)
                    else:
                        # Use implementation_time as months from current date if no start date
                        impl_time = int(inv.get("implementation_time", 3) or 3)
                        start_date = current_date - pd.DateOffset(months=impl_time // 2)

                    implementation_end = inv.get("implementation_end")
                    if implementation_end is not None:
                        # First convert to string, then try to parse as date
                        try:
                            # Use pandas' Timestamp constructor directly to avoid type checking issues
                            end_date_str = str(implementation_end)
                            try:
                                # Try to create a Timestamp directly
                                end_date = pd.Timestamp(end_date_str)
                            except ValueError:
                                # If conversion fails, raise our own error to trigger the except block
                                raise ValueError("Invalid date")
                        except:
                            # Fallback if date parsing fails
                            impl_time = int(inv.get("implementation_time", 3) or 3)
                            end_date = pd.Timestamp(
                                start_date + pd.DateOffset(months=impl_time)
                            )
                    else:
                        # Use implementation_time from start date if no end date
                        impl_time = int(inv.get("implementation_time", 3) or 3)
                        # Skip intermediate variable and directly convert to Timestamp
                        end_date = pd.Timestamp(
                            start_date + pd.DateOffset(months=impl_time)
                        )
                except:
                    # Fallback if date parsing fails
                    start_date = current_date - pd.DateOffset(months=1)
                    end_date = current_date + pd.DateOffset(months=2)

                # Get investment status
                status = inv.get("status", "planned")

                # Add monthly savings based on status and implementation dates
                for i, date in enumerate(date_range):
                    if status == "completed" and date > end_date:
                        # Full savings for completed investments
                        # Get current value and ensure it's numeric using direct float conversion
                        try:
                            # Re-import Any directly at the usage site to ensure it's recognized
                            from typing import Any, cast

                            # Use cast to explicitly tell the type checker to treat the value as Any
                            raw_value = cast(Any, df.loc[i, "monthly_savings"])
                            # More type-safe approach with explicit handling
                            if raw_value is None:
                                current_value = 0.0
                            else:
                                try:
                                    # Use direct float conversion instead of pd.to_numeric
                                    from typing import Any
                                    import math  # Ensure math is imported in this scope

                                    # Handle conversion directly with explicit error checking
                                    if raw_value is None:
                                        numeric_result = 0.0
                                    else:
                                        try:
                                            numeric_result = float(raw_value)
                                            # Check for NaN using math.isnan
                                        except (ValueError, TypeError):
                                            numeric_result = 0.0
                                    # Explicitly cast to float after checking for NaN
                                    if isinstance(numeric_result, float) and math.isnan(
                                        numeric_result
                                    ):
                                        numeric_value = 0.0
                                    else:
                                        numeric_value = float(numeric_result)

                                    if isinstance(numeric_value, float) and math.isnan(
                                        numeric_value
                                    ):
                                        current_value = 0.0
                                    else:
                                        current_value = float(numeric_value)
                                except:
                                    current_value = 0.0
                        except (ValueError, TypeError, KeyError, IndexError):
                            current_value = 0.0
                        df.loc[i, "monthly_savings"] = current_value + monthly_savings
                    elif status == "in_progress":
                        # Scale savings by completion percentage for in-progress investments
                        if date > start_date:
                            if date <= end_date:
                                # During implementation - partial benefit
                                pct_complete = calculate_percent_complete(
                                    start_date, end_date, date
                                )
                                try:
                                    # Access the value with explicit cast to Any
                                    from typing import Any, cast

                                    raw_value = cast(Any, df.loc[i, "monthly_savings"])
                                    if raw_value is None:
                                        current_value = 0.0
                                    else:
                                        try:
                                            current_value = float(raw_value)
                                            # Check for NaN after conversion
                                            import math

                                            if math.isnan(current_value):
                                                current_value = 0.0
                                        except (ValueError, TypeError):
                                            current_value = 0.0
                                except (ValueError, TypeError, KeyError, IndexError):
                                    current_value = 0.0
                                df.loc[i, "monthly_savings"] = current_value + (
                                    monthly_savings * pct_complete
                                )
                    elif status == "planned":
                        # Only add savings after implementation for planned investments
                        if date > end_date:
                            try:
                                # Handle type conversion explicitly with proper typing
                                from typing import Any, cast

                                raw_value = cast(Any, df.loc[i, "monthly_savings"])
                                # Use explicit None check and math.isnan for float values
                                if raw_value is None:
                                    current_value = 0.0
                                elif isinstance(raw_value, float):
                                    import math

                                    if math.isnan(raw_value):
                                        current_value = 0.0
                                    else:
                                        current_value = raw_value
                                else:
                                    try:
                                        current_value = float(raw_value)
                                    except (ValueError, TypeError):
                                        # If direct conversion fails, try pd.to_numeric and handle the result
                                        try:
                                            # First convert to float directly
                                            current_value = float(raw_value)
                                        except (ValueError, TypeError):
                                            # If direct conversion fails, try pd.to_numeric and handle the result
                                            try:
                                                # Direct float conversion with error handling
                                                if raw_value is None:
                                                    current_value = 0.0
                                                else:
                                                    try:
                                                        current_value = float(raw_value)
                                                        # Check for NaN
                                                        import math

                                                        if math.isnan(current_value):
                                                            current_value = 0.0
                                                    except (ValueError, TypeError):
                                                        current_value = 0.0
                                            except:
                                                current_value = 0.0
                            except (ValueError, TypeError, KeyError, IndexError):
                                current_value = 0.0
                            df.loc[i, "monthly_savings"] = (
                                current_value + monthly_savings
                            )
            except Exception as e:
                print(f"Error processing investment {name}: {str(e)}")
                continue

        # Calculate cumulative savings
        df["cumulative_savings"] = df["monthly_savings"].cumsum()

        # Create figure
        fig = go.Figure()

        # Add bar chart for monthly savings
        fig.add_trace(
            go.Bar(  # type: ignore
                x=df["date"],
                y=df["monthly_savings"],
                name="Monthly Savings",
                marker_color="lightblue",
            )
        )

        # Add line chart for cumulative savings
        fig.add_trace(
            go.Scatter(  # type: ignore
                x=df["date"],
                y=df["cumulative_savings"],
                name="Cumulative Savings",
                mode="lines",
                line=dict(color="darkblue", width=2),
                yaxis="y2",
            )
        )

        # Add vertical line for current date
        from typing import cast, Any

        # Assign the cast result to a variable for clearer type handling
        any_fig = cast(Any, fig)
        any_fig.add_shape(
            type="line",
            x0=current_date,
            y0=0,
            x1=current_date,
            y1=(
                df["monthly_savings"].max() * 1.2
                if df["monthly_savings"].max() > 0
                else 10000
            ),
            line=dict(color="black", width=1, dash="dot"),
        )

        # Layout with two y-axes - use type casting to avoid type checking issues
        from typing import cast, Any

        # Assign the cast result to a variable for clearer type handling
        any_fig = cast(Any, fig)
        any_fig.update_layout(
            title="Investment Savings Over Time",
            xaxis_title="Date",
            yaxis_title="Monthly Savings (£)",
            yaxis2=dict(
                title="Cumulative Savings (£)",
                titlefont=dict(color="darkblue"),
                tickfont=dict(color="darkblue"),
                overlaying="y",
                side="right",
            ),
            template="plotly_white",
            hovermode="x unified",
            barmode="stack",
            legend=dict(
                orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
            ),
        )

        return fig

    except Exception as e:
        collect_error("update_cumulative_savings_chart")
        print(f"Error creating cumulative savings chart: {str(e)}")
        return create_empty_cumulative_chart()


# Add after update_cumulative_savings_chart function (around line 1750)
# this function creates an empty cumulative chart when no data is available.
# It initializes a Plotly figure with a title and axes labels, and adds an annotation indicatingthat no investment data is available. This is used as a fallback when there are no investments to display.
# # This function has been migrated to investment_mgmt/utils.py
def create_empty_cumulative_chart():
    """Create an empty cumulative chart when no data is available."""
    fig = go.Figure()

    # Use cast to Any to bypass the type checking for all Plotly methods
    from typing import cast, Any

    fig_any = cast(Any, fig)  # Store casted figure in a different variable
    fig_any.update_layout(
        title="Investment Savings Over Time",
        xaxis_title="Date",
        yaxis_title="Savings (£)",
        template="plotly_white",
    )

    # Add annotation - now using the properly casted fig object
    fig_any.add_annotation(
        x=0.5,
        y=0.5,
        xref="paper",
        yref="paper",
        text="No investment data available",
        showarrow=False,
        font=dict(size=14),
    )

    return fig


# This function collects errors and stores them in a shared list.
# It is used to capture exceptions that occur during the execution of various callbacks in the application.
# # This function has been migrated to shared/error_handling/__init__.py
def display_all_errors(n_clicks: Optional[int]) -> Union[str, html.Pre]:
    """Display all collected errors when button is clicked."""
    if not n_clicks:
        return ""

    errors = get_all_errors()
    return html.Pre(
        errors,
        style={
            "backgroundColor": "#f8f9fa",
            "padding": "15px",
            "border": "1px solid #dee2e6",
            "borderRadius": "5px",
            "maxHeight": "500px",
            "overflowY": "auto",
        },
    )


@app.callback(  # type: ignore
    Output("error-collection-display", "children", allow_duplicate=True),
    Input("clear-errors-btn", "n_clicks"),
    prevent_initial_call=True,
)
def clear_all_errors(n_clicks: Optional[int]) -> Union[str, Any]:
    """Clear all collected errors when button is clicked."""
    if not n_clicks:
        return dash.no_update

    clear_errors()
    return "Errors cleared."


# This callback adds a new chart to the financial dashboard grid when the "Add Chart" button is clicked.
# It generates a unique ID for the new chart, creates a new chart component with a dropdown for chart type selection, and adds it to the existing grid layout.
# The new chart is added at the bottom of the grid, and the layout is updated accordingly.
# This callback has been migrated to financial_dashboard/callbacks/__init__.py
@app.callback(
    [
        Output("financial-dashboard-grid", "children", allow_duplicate=True),
        Output("financial-dashboard-grid", "layouts", allow_duplicate=True),
    ],
    Input("add-chart-btn", "n_clicks"),
    [
        State("financial-dashboard-grid", "children"),
        State("financial-dashboard-grid", "layouts"),
    ],
    prevent_initial_call=True,
)
def add_new_chart(
    n_clicks: Optional[int],
    current_children: List[html.Div],
    current_layouts: Dict[str, List[Dict[str, Any]]],
) -> Tuple[Any, Any]:
    """Add a new chart to the dashboard"""
    if not n_clicks:
        return dash.no_update, dash.no_update

    # Generate a unique ID for the new chart
    import uuid

    chart_id = f"new-chart-{str(uuid.uuid4())[:8]}"

    # Create new chart
    new_chart = html.Div(
        [
            html.Div(
                [
                    html.H5("New Chart", className="chart-title"),
                    html.Button("×", className="close-btn", id=f"close-{chart_id}"),
                    dcc.Dropdown(
                        id=f"chart-type-{chart_id}",
                        options=cast(
                            Any,
                            [
                                {"label": "Line Chart", "value": "line"},
                                {"label": "Bar Chart", "value": "bar"},
                                {"label": "Pie Chart", "value": "pie"},
                            ],
                        ),
                        value="line",
                        clearable=False,
                        className="mb-2",
                    ),
                    dcc.Graph(
                        id=f"chart-{chart_id}",
                        figure={
                            "data": [{"x": [1, 2, 3], "y": [4, 1, 2], "type": "bar"}],
                            "layout": {
                                "title": "New Chart",
                                "margin": {"l": 40, "r": 20, "t": 40, "b": 30},
                            },
                        },
                        config={"displayModeBar": False},
                        style={"height": "100%", "width": "100%"},
                    ),
                ],
                className="chart-container",
            )
        ],
        key=chart_id,
        className="grid-item",
    )

    # Add new chart to children
    new_children = current_children + [new_chart]

    # Add new chart to layouts
    new_layouts = {}
    for breakpoint, layout in current_layouts.items():
        # Find the maximum y position
        max_y = 0
        for item in layout:
            item_bottom = item["y"] + item["h"]
            if item_bottom > max_y:
                max_y = item_bottom

        # Add the new chart at the bottom
        new_layouts[breakpoint] = layout + [
            {
                "i": chart_id,
                "x": 0,
                "y": max_y,
                "w": min(6, current_layouts[breakpoint][0]["w"]),
                "h": 6,
                "minW": 3,
                "minH": 3,
            }
        ]

    return new_children, new_layouts


# This callback saves the current layout of the financial dashboard grid when it changes.
# It updates the layout store with the new layout data, allowing the layout to be persisted across page reloads.
# This callback has been migrated to financial_dashboard/callbacks/__init__.py
@app.callback(
    Output("dashboard-layout-store", "data"),
    Input("financial-dashboard-grid", "layouts"),
    State("dashboard-layout-store", "data"),
)
def save_layout(
    current_layout: Optional[Dict[str, Any]], stored_layout: Optional[Dict[str, Any]]
) -> Dict[str, Any]:
    """Save the current layout when it changes"""
    if current_layout is not None:
        return current_layout
    return stored_layout or {}


# This callback loads the saved layout from the layout store when the page is loaded.
# It checks if there is a stored layout and applies it to the financial dashboard grid.
# If no stored layout is found, it uses the current layout as a fallback.
# This callback has been migrated to financial_dashboard/callbacks/__init__.py
@app.callback(
    Output("financial-dashboard-grid", "layouts"),
    Input("dashboard-layout-store", "data"),
    State("financial-dashboard-grid", "layouts"),
)
def load_layout(stored_layout, current_layout):
    """Load saved layout on page load"""
    if stored_layout is not None:
        return stored_layout
    return current_layout


# This callback resets the layout of the financial dashboard grid to its default configuration when the reset button is clicked.
# It returns the default layout structure for different screen sizes (large, medium, small).
# This callback has been migrated to financial_dashboard/callbacks/__init__.py
@app.callback(
    Output("dashboard-layout-store", "data", allow_duplicate=True),
    Input("reset-layout-btn", "n_clicks"),
    prevent_initial_call=True,
)
def reset_layout(n_clicks):
    """Reset the layout to default when button is clicked"""
    if n_clicks:
        return {
            "lg": [
                {
                    "i": "budget-allocation",
                    "x": 0,
                    "y": 0,
                    "w": 6,
                    "h": 6,
                    "minW": 4,
                    "minH": 4,
                },
                {
                    "i": "savings-over-time",
                    "x": 6,
                    "y": 0,
                    "w": 6,
                    "h": 6,
                    "minW": 4,
                    "minH": 4,
                },
                {
                    "i": "metrics-panel",
                    "x": 0,
                    "y": 6,
                    "w": 12,
                    "h": 3,
                    "minW": 6,
                    "minH": 3,
                },
                {
                    "i": "overview-chart",
                    "x": 0,
                    "y": 9,
                    "w": 12,
                    "h": 6,
                    "minW": 6,
                    "minH": 4,
                },
            ],
            "md": [
                {"i": "budget-allocation", "x": 0, "y": 0, "w": 5, "h": 6},
                {"i": "savings-over-time", "x": 5, "y": 0, "w": 5, "h": 6},
                {"i": "metrics-panel", "x": 0, "y": 6, "w": 10, "h": 3},
                {"i": "overview-chart", "x": 0, "y": 9, "w": 10, "h": 6},
            ],
            "sm": [
                {"i": "budget-allocation", "x": 0, "y": 0, "w": 6, "h": 6},
                {"i": "savings-over-time", "x": 0, "y": 6, "w": 6, "h": 6},
                {"i": "metrics-panel", "x": 0, "y": 12, "w": 6, "h": 3},
                {"i": "overview-chart", "x": 0, "y": 15, "w": 6, "h": 6},
            ],
        }


# This callback removes a chart from the financial dashboard grid when its close button is clicked.
# It identifies which chart was closed based on the button ID and updates the grid's children and layouts accordingly.
# This callback has been migrated to financial_dashboard/callbacks/__init__.py
@app.callback(
    [
        Output("financial-dashboard-grid", "children"),
        Output("financial-dashboard-grid", "layouts"),
    ],
    [
        Input("close-budget-allocation", "n_clicks"),
        Input("close-savings-chart", "n_clicks"),
        Input("close-metrics-panel", "n_clicks"),
        Input("close-overview-chart", "n_clicks"),
    ],
    [
        State("financial-dashboard-grid", "children"),
        State("financial-dashboard-grid", "layouts"),
    ],
    prevent_initial_call=True,
)
def remove_chart(
    close_budget,
    close_savings,
    close_metrics,
    close_overview,
    current_children,
    current_layouts,
):
    """Remove a chart when its close button is clicked"""
    ctx = dash.callback_context
    if not ctx.triggered:
        return dash.no_update, dash.no_update

    triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]

    # Map close button IDs to chart IDs
    chart_map = {
        "close-budget-allocation": "budget-allocation",
        "close-savings-chart": "savings-over-time",
        "close-metrics-panel": "metrics-panel",
        "close-overview-chart": "overview-chart",
    }

    chart_id = chart_map.get(triggered_id)
    if not chart_id:
        return dash.no_update, dash.no_update

    # Remove the chart from children
    new_children = [
        child for child in current_children if child["props"]["key"] != chart_id
    ]

    # Remove the chart from layouts
    new_layouts = {}
    for breakpoint, layout in current_layouts.items():
        new_layouts[breakpoint] = [item for item in layout if item["i"] != chart_id]

    return new_children, new_layouts


# Add this to your app.py
app.clientside_callback(
    """
    function(layout) {
        if (layout) {
            // Trigger resize event for all graphs to ensure they fill their containers
            setTimeout(function() {
                window.dispatchEvent(new Event('resize'));
            }, 300);
        }
        return window.dash_clientside.no_update;
    }
    """,
    Output("dashboard-layout-store", "data", allow_duplicate=True),
    Input("financial-dashboard-grid", "layouts"),
    prevent_initial_call=True,
)

# At the end of your app.py file, replace the current startup code:
if __name__ == "__main__":
    print("Starting Financial Optimizer application server...")

    import signal
    import types

    # Register proper signal handlers
    def signal_handler(sig: int, frame: Optional[types.FrameType]) -> None:
        print("Shutting down Financial Optimizer...")
        import sys

        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    # Run the app with error handling
    try:
        # Use run_server instead of run for Dash applications
        app.run(debug=True, threaded=False)
    except Exception as e:
        print(f"Error starting server: {e}")
