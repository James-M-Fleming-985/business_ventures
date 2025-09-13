# This logic allows us to import these functions only during type checkingand avoids circular imports at runtime
# This is useful for type checking tools like mypy or PyCharm
# If TYPE_CHECKING is True, we import the functions with type annotations
# If TYPE_CHECKING is False, we import them normally
# This allows us to use type annotations without causing circular import issues
# This is a common pattern in Python to avoid circular imports while still providing type hints
# This logic has been migrated to investment_mgmt/logic/__init__.py
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from dash import Dash
    # Change this to match what actually exists in callbacks/__init__.py
    def register_investment_mgmt_callbacks(app: Dash) -> None: ...
else:
    # Import the function that actually exists
    from ..callbacks import register_investment_mgmt_callbacks
    
    # If you need backwards compatibility, create aliases
    register_input_callbacks = register_investment_mgmt_callbacks
    register_chart_callbacks = register_investment_mgmt_callbacks
    register_economic_climate_callbacks = register_investment_mgmt_callbacks
    register_investment_optimizer_callbacks = register_investment_mgmt_callbacks

import dash
from dash import Dash, html, callback_context, Output, Input
from typing import List, Dict, Any, Optional, Union, Tuple, TypedDict, Callable, cast
import pandas as pd

# Import the financial projection function
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    def _project_financials(
        financial_data: Any,
        months: int,
        investment_amount: float,
        investment_type: str,
        investment_rate: float,
        investment_lifespan: int,
        efficiency_impact: float,
        calculate_baseline: bool,
        oee_availability: float,
        oee_performance: float,
        oee_quality: float,
        staff_count: int,
        ramp_up_period: int,
        training_cost: float
    ) -> Union[pd.DataFrame, Tuple[pd.DataFrame, pd.DataFrame]]: ...
else:
    # Import directly from the callbacks module
    from ..callbacks import project_financials as _project_financials
    
# This logic has been migrated to investment_mgmt/logic/__init__.py
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
    training_cost: float = 2000
) -> Union[pd.DataFrame, Tuple[pd.DataFrame, pd.DataFrame]]:
    """Wrapper for project_financials with proper type annotations."""
    result: Union[pd.DataFrame, Tuple[pd.DataFrame, pd.DataFrame]] = _project_financials(
        financial_data=financial_data,
        months=int(months),  # Add explicit int conversion here
        investment_amount=int(investment_amount),
        investment_type=investment_type or "cash",  # Provide default value if None
        investment_rate=investment_rate,
        investment_lifespan=investment_lifespan,
        efficiency_impact=int(efficiency_impact),
        calculate_baseline=calculate_baseline,
        oee_availability=int(oee_availability) if oee_availability is not None else 0,
        oee_performance=int(oee_performance) if oee_performance is not None else 0,
        oee_quality=int(oee_quality) if oee_quality is not None else 0,
        staff_count=staff_count,
        ramp_up_period=ramp_up_period,
        training_cost=int(training_cost)
    )
    return cast(Union[pd.DataFrame, Tuple[pd.DataFrame, pd.DataFrame]], result)

# This logic calculates the percent complete based on a timeline.
# This function takes a start date, end date, and current date,and returns a float representing the percentage of completion.
# This logic has been migrated to investment_mgmt/logic/__init__.py
def calculate_percent_complete(start_date: pd.Timestamp, end_date: pd.Timestamp, current_date: pd.Timestamp) -> float:
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

# Define the return type for calculate_investment_metrics
class InvestmentMetrics(TypedDict):
    roi: float
    irr: float
    payback_period: float
    npv: float

# First import the module
from modules.investment_analysis.models import investment_analysis
# Import the function with proper typing and provide explicit type information
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import List, Dict
    def _calculate_investment_metrics(cash_flows: List[float], initial_investment: float) -> Dict[str, float]: ...
else:
    # Runtime import
    from modules.investment_analysis.models.investment_analysis import calculate_investment_metrics as _calculate_investment_metrics

# Create a properly typed wrapper for the function
# This function calculates investment metrics such as ROI, IRR, payback period, and NPV.
# It takes a list of cash flows and an initial investment amount, and returns a dictionary with the calculated metrics.
# This logic has been migrated to investment_mgmt/logic/__init__.py
def calculate_investment_metrics(cash_flows: List[float], initial_investment: float) -> InvestmentMetrics:
    """Wrapper with proper type annotations for the investment metrics calculation function."""
    result = _calculate_investment_metrics(cash_flows, initial_investment)
    # Explicitly cast the result to InvestmentMetrics to satisfy type checking
    return cast(InvestmentMetrics, result)

# Type alias for documentation purposes
# (Removed unused CalculateInvestmentMetricsType)
# Type alias for documentation purposes
CalculateInvestmentMetricsType = Callable[[List[float], float], InvestmentMetrics]

from modules.investment_analysis.models.scenarios import run_scenario_analysis, get_scenario_summary
from services.sample_data import get_sample_data

# Import data handling
# Register callbacks from other modules - types already defined above
from dash import Dash
import dash_bootstrap_components as dbc  # type: ignore
# Define a type for callback registration functions
RegisterCallbacksType = Callable[[Dash], None]

app: Dash = dash.Dash(
    __name__, 
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        "https://use.fontawesome.com/releases/v5.15.4/css/all.css"
    ],
    suppress_callback_exceptions=True
)

# Callback to toggle production line selection based on investment scope
# This callback updates the visibility of the production line selection container based on the selected investment scope.
# It shows the production line selection only when the scope is set to "line".
# This logic has been migrated to investment_mgmt/callbacks/__init__.py
@app.callback(  # type: ignore
    Output("production-line-container", "style"),
    Input("investment-scope-input", "value")
)
def toggle_production_line_selection(scope: Optional[str]) -> Dict[str, str]:
    """Show/hide production line selection based on investment scope."""
    if scope == "line":
        return {"display": "block"}
    return {"display": "none"}