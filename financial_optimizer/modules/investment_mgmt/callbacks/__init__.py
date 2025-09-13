from dash import Input, Output, State, dash, no_update, html
from typing import List, Dict, Any, Optional, Union, Callable
# Use direct annotations instead of importing from dash.typing
from dash import Input, Output, State, dash, no_update, callback_context
from typing import List, Dict, Any, Optional, Union, TypeVar, Callable, Tuple
import pandas as pd  # Add any missing imports
import logging  # For error logging
import plotly.graph_objects as go  # type: ignore
from plotly.graph_objects import Figure  # type: ignore  # Updated import path with better type support
from datetime import datetime, timedelta

# Define the get_sample_data function
def get_sample_data() -> Dict[str, Any]:
    """
    Generate sample financial data for testing and demonstration purposes.
    Returns a dictionary with financial metrics that can be used by the app.
    """
    # Current date for starting point
    start_date = datetime.now()
    
    # Generate 24 months of sample data
    dates = [(start_date + timedelta(days=30*i)).strftime('%Y-%m-%d') for i in range(24)]
    
    # Sample revenue, costs, and calculated fields
    revenue = [50000 + (i * 1000) + ((-1)**i * 2000) for i in range(24)]  # Growing with some variation
    costs = [30000 + (i * 500) for i in range(24)]  # Gradually increasing costs
    
    # Calculate derived metrics
    ebitda = [rev - cost for rev, cost in zip(revenue, costs)]
    cash_flow = [ebitda[i] - 2000 for i in range(24)]  # Cash flow with some capital expenditure
    net_worth = [200000]  # Starting net worth
    for cf in cash_flow[:-1]:
        net_worth.append(net_worth[-1] + cf)  # Accumulate cash flow
    
    # Create a sample data dictionary
    return {
        'dates': dates,
        'revenue': revenue,
        'costs': costs,
        'ebitda': ebitda,
        'cash_flow': cash_flow,
        'net_worth': net_worth,
        'metrics': {
            'current_assets': 150000,
            'current_liabilities': 70000,
            'long_term_debt': 100000,
            'annual_revenue': 600000,
            'annual_profit': 120000
        }
    }

# Define the project_financials function
def project_financials(financial_data: Dict[str, Any], months: int = 60, investment_amount: float = 0,
                       investment_type: Optional[str] = None, investment_rate: float = 5.0,
                       investment_lifespan: int = 5, efficiency_impact: float = 0,
                       oee_availability: int = 0, oee_performance: int = 0, oee_quality: int = 0,
                       staff_count: int = 1, ramp_up_period: int = 3, training_cost: float = 2000) -> Union[pd.DataFrame, Tuple[pd.DataFrame, Any]]:
    """
    Project financial outcomes based on current data and investment parameters.
    Returns a DataFrame with projected financial metrics.
    """
    # Create DataFrame from existing data
    start_date = datetime.now()
    dates = [(start_date + timedelta(days=30*i)).strftime('%Y-%m-%d') for i in range(months)]
    
    # Initialize with baseline values
    base_revenue = financial_data.get('revenue', [50000])[0] if financial_data.get('revenue') else 50000
    base_costs = financial_data.get('costs', [30000])[0] if financial_data.get('costs') else 30000
    base_net_worth = financial_data.get('net_worth', [200000])[0] if financial_data.get('net_worth') else 200000
    
    # Apply investment effects
    revenue_growth = 0.01  # 1% monthly growth
    if investment_type == 'equipment' or investment_type == 'capital':
        revenue_growth += (investment_rate / 100) * 0.02  # Equipment improves revenue growth
    elif investment_type == 'process':
        revenue_growth += (efficiency_impact / 100) * 0.03  # Process improvements boost efficiency
    
    # Generate projected data
    revenue = [base_revenue]
    costs = [base_costs + (investment_amount if investment_amount > 0 else 0)]  # Add investment to initial costs
    for i in range(1, months):
        revenue.append(revenue[-1] * (1 + revenue_growth))
        costs.append(base_costs * (1 + 0.005*i))  # Slight cost increase over time
    
    ebitda = [rev - cost for rev, cost in zip(revenue, costs)]
    cash_flow = ebitda.copy()  # Simplified: cash flow equals EBITDA
    
    net_worth = [base_net_worth]
    for cf in cash_flow[1:]:
        net_worth.append(net_worth[-1] + cf)
    
    # Create DataFrame
    df = pd.DataFrame({
        'date': dates,
        'revenue': revenue,
        'costs': costs,
        'ebitda': ebitda,
        'cash_flow': cash_flow,
        'net_worth': net_worth
    })
    
    return df

# Define the calculate_investment_metrics function
def calculate_investment_metrics(cash_flows: List[float], initial_investment: float) -> Dict[str, float]:
    """
    Calculate investment metrics like ROI, IRR, and payback period.
    """
    # Simple implementation
    total_return = sum(cash_flows)
    roi = (total_return / initial_investment * 100) if initial_investment > 0 else 0
    
    # Simplified IRR calculation (real implementation would use numpy's IRR function)
    irr = roi / 60  # Rough approximation
    
    # Payback period calculation
    cumulative_cash_flow = 0.0
    payback_period = float('inf')  # Initialize to infinity
    for i, cf in enumerate(cash_flows):
        cumulative_cash_flow += cf # LINE 120 MARKER: This is line 120
        if cumulative_cash_flow >= initial_investment and payback_period == float('inf'):
            payback_period = float(i + 1)  # +1 because we start from month 1, not 0
    
    return {
        'roi': roi,
        'irr': irr,
        'payback_period': payback_period
    }

# Define the collect_error function
def collect_error(function_name: str) -> None:
    """Log errors from callback functions for monitoring and debugging."""
    logging.error(f"Error occurred in function: {function_name}")

# pyright: reportUnusedFunction=false

def register_investment_mgmt_callbacks(app: dash.Dash):
    """Register all callbacks for Investment Management tab"""
    # This callback is used by Dash at runtime
    @app.callback(  # type: ignore
        [Output('investments-table', 'data'),
        Output('investments-store', 'data'),
        # Clear form fields
        Output('investment-mgmt-name-input', 'value'),
        Output('investment-mgmt-type-input', 'value'),
        Output('investment-cost-input', 'value'),
        Output('investment-savings-input', 'value'),
        Output('implementation-time-input', 'value'),
        Output('investment-efficiency-input', 'value'),
        Output('risk-slider', 'value')],
        [Input('add-investment-button', 'n_clicks')],
        [State('investment-mgmt-name-input', 'value'),
        State('investment-mgmt-type-input', 'value'),
        State('investment-cost-input', 'value'),
        State('investment-savings-input', 'value'),
        State('implementation-time-input', 'value'),
        State('investment-efficiency-input', 'value'),
        State('risk-slider', 'value'),
        # Capital Equipment Parameters
        State('oee-current-availability-input', 'value'),
        State('oee-current-performance-input', 'value'),
        State('oee-current-quality-input', 'value'),
        State('oee-availability-improvement-input', 'value'),
        State('oee-performance-improvement-input', 'value'),
        State('oee-quality-improvement-input', 'value'),
        State('equipment-hourly-rate-input', 'value'),
        State('operating-hours-input', 'value'),
        State('maintenance-reduction-input', 'value'),
        # Process Improvement Parameters
        State('current-cycle-time-input', 'value'),
        State('current-downtime-input', 'value'),
        State('current-defect-rate-input', 'value'),
        State('cycle-time-reduction-input', 'value'),
        State('downtime-reduction-input', 'value'),
        State('defect-reduction-input', 'value'),
        State('product-value-input', 'value'),
        State('production-volume-input', 'value'),
        State('material-cost-input', 'value'),
        # New States
        State('investment-scope-input', 'value'),
        State('production-line-selector', 'value'),
        State('implementation-start-date', 'date'),
        State('implementation-end-date', 'date'),
        State('implementation-status', 'value'),
        # Existing data
        State('investments-table', 'data'),
        State('investments-store', 'data')],
        prevent_initial_call=True
    )
    def add_investment(n_clicks: int, name: str, inv_type: str, cost: Optional[float], savings: Optional[float], impl_time: Optional[int], efficiency: Optional[float], risk: Optional[int], 
                    # Capital Equipment Parameters
                    oee_current_availability: Union[float, None], oee_current_performance: Union[float, None], oee_current_quality: Union[float, None],
                    oee_availability_improvement: float, oee_performance_improvement: float, oee_quality_improvement: float,
                    equipment_hourly_rate: float, operating_hours: float, maintenance_reduction: float,
                    # Process Improvement Parameters
                    current_cycle_time: float, current_downtime: float, current_defect_rate: float,
                    cycle_time_reduction: float, downtime_reduction: float, defect_reduction: float,
                    product_value: float, production_volume: int, material_cost: float,
                    # New States
                    scope: Optional[str], production_lines: Optional[List[str]], implementation_start_date: Optional[str],
                    implementation_end_date: Optional[str], implementation_status: Optional[str],
                    # Existing data
                    current_table_data: Optional[list[dict[str, Any]]], stored_investments: Optional[list[dict[str, Any]]]):
                
        """Add a new investment to the table and store it."""
        try:
            print(f"Add investment clicked: {n_clicks}")
            print(f"Investment name: {name}, type: {inv_type}, cost: {cost}")
            print(f"Cost type: {type(cost).__name__ if cost is not None else 'None'}")
            
            # Check if we have valid data to add
            if not name or not inv_type or not cost:
                # Return existing data and don't clear form if validation fails
                return current_table_data or [], stored_investments or [], name, inv_type, cost, savings, impl_time, efficiency, risk
            
            # Initialize calculated savings
            calculated_savings = savings if savings is not None else 0
            
            # Create the investment object with updated type annotation to include all possible types
            investment: Dict[str, Union[str, float, int, List[str], None]] = {
                'name': name,
                'type': inv_type,
                'cost': float(cost or 0),
                'savings': float(calculated_savings or 0),
                'implementation_time': impl_time or 3,
                'efficiency': efficiency or 5,
                'risk': risk or 3,
                'roi': float(calculated_savings or 0) / float(cost or 1) if cost and calculated_savings else 0,
                'scope': scope or "department",
                'production_lines': ', '.join(map(str, production_lines)) if scope == "line" and production_lines else "",
                'implementation_start': implementation_start_date,
                'implementation_end': implementation_end_date,
                'status': implementation_status or "planned"
            }
            
            # Make safe copies of data with proper type annotation
            # Use a more inclusive type annotation that matches the investment dictionary
            table_data: List[Dict[str, Union[str, float, int, List[str], None]]] = [] if not current_table_data else list(current_table_data)
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
            return current_table_data or [], stored_investments or [], name, inv_type, cost, savings, impl_time, efficiency, risk

    # New callback for projected savings
    # This callback updates the projected savings based on budget and timeframe.
    # It calculates the annual savings based on the selected budget, investment type, rate, efficiency impact, and mode.
    # It returns a formatted string for display.
    # This logic has been migrated to investment_mgmt/callbacks/__init__.py
    @app.callback(  # type: ignore
        Output('projected-savings', 'children'),
        [Input('budget-slider', 'value'),
        Input('budget-timeframe', 'value'),
        Input('investment-type-input', 'value'),
        Input('investment-rate-input', 'value'),
        Input('investment-efficiency-input', 'value'),
        Input('app-mode', 'value')],
        [State('financial-data-store', 'data')],
        prevent_initial_call=True
    )
    def update_projected_savings(budget: Optional[float], timeframe: Optional[int], investment_type: Optional[str], investment_rate: Optional[float], 
                                efficiency_impact: Optional[float], mode: Optional[str], stored_data: Optional[Dict[str, Any]]) -> str:
        """Update the projected savings based on budget and timeframe."""
        if budget is None or budget <= 0:
            return "£0"
        
        # Default to sample data if no stored data with explicit typing
        if stored_data is not None:
            financial_data: Dict[str, Any] = stored_data
        else:
            sample_data: Dict[str, Any] = get_sample_data()
            financial_data = sample_data
        
        # Calculate projections with timeframe in mind
        months = timeframe * 12 if timeframe else 60  # Convert years to months
        
        # Define the return type for project_financials which could be DataFrame or tuple
        from typing import Union, Tuple
        import pandas as pd
        
        df: Union[pd.DataFrame, Tuple[pd.DataFrame, Any]] = project_financials(
            financial_data,
            months=months,
            investment_amount=budget,
            investment_type=investment_type,
            investment_rate=investment_rate if investment_rate is not None else 5.0,
            investment_lifespan=timeframe if timeframe else 5,  # Use timeframe as lifespan
            efficiency_impact=efficiency_impact if efficiency_impact is not None else 0
        )
        
        # Extract DataFrame from result if it's a tuple
        if isinstance(df, tuple):
            df_data = df[0]
        else:
            df_data = df
                
            # Initialize variables with default values
            first_val = 0.0
            last_val = 0.0
            annual_savings = 0.0
            
            # Calculate annual savings with proper type handling
            if mode == 'business':
                if 'ebitda' in df_data.columns:
                    ebitda_series = df_data['ebitda']
                    # Use .iloc to get values with proper type handling
                    ebitda_values = ebitda_series.iloc
                    if len(ebitda_series) > 0:
                        first_val = float(ebitda_values[0]) if ebitda_values[0] is not None else 0.0
                        last_val = float(ebitda_values[-1]) if ebitda_values[-1] is not None else 0.0
                        annual_savings = (last_val - first_val) * 12
                    else:
                        annual_savings = 0.0
                else:
                    annual_savings = 0.0
            else:
                if 'cash_flow' in df_data.columns:
                    cash_flow_series: pd.Series[float] = df_data['cash_flow'].astype(float)
                    if len(cash_flow_series) > 0:
                        # Safely extract first and last values with proper type handling
                        first_raw = cash_flow_series.iloc[0]
                        last_raw = cash_flow_series.iloc[-1]
                        
                        # Convert to float with None checking and proper type conversion
                        try:
                            first_numeric = pd.to_numeric(first_raw, errors='coerce')  # type: ignore
                            # Check if the result is NaN using math.isnan for better type safety
                            import math
                            if math.isnan(float(first_numeric)):
                                first_val = 0.0
                            else:
                                first_val = float(first_numeric)
                        except (ValueError, TypeError):
                            first_val = 0.0
                        
                        try:
                            last_numeric = pd.to_numeric(last_raw, errors='coerce')  # type: ignore
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
    
    # This callback updates the investments table from the stored data.
    # It uses the stored data to populate the table, allowing for dynamic updates.
    # This callback is triggered by changes in the investments store.
    # It also includes a check to avoid updates when the table is being cleared or deleted.
    # This callback has been migrated to investment management/callbacks/__init__.py
    @app.callback(  # type: ignore
        Output('investments-table', 'data', allow_duplicate=True),
        Input('investments-store', 'data'),
        prevent_initial_call=True,
        # Add a callback_context check in the function to avoid updates from deletion actions
    )
    def update_investments_table(stored_data: Optional[Union[List[Dict[str, Any]], Dict[str, Any]]]) -> Union[List[Dict[str, Any]], Any]:
        """Update investments table from stored data."""
        from typing import Any, List, Dict
        from dash import callback_context
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
                trigger_id_str: str = cast(str, trigger_dict['prop_id']) if trigger_dict.get('prop_id') is not None else ""
                # Check if the representation contains 'investments-table'
                if 'investments-table' in trigger_id_str:
                    return no_update
            
            # Safely get the type name
            if stored_data is not None:
                try:
                    # Get type safely without using cast
                    from typing import Any
                    type_obj = type(stored_data)
                    type_name = type_obj.__name__ if hasattr(type_obj, '__name__') else repr(type_obj)
                except:
                    type_name = "Unknown"
            else:
                type_name = "None"
                
            print(f"Type of stored_data: {type_name}")
            
            if stored_data is not None and hasattr(stored_data, '__len__') and len(stored_data) > 0:
                try:
                    # Check data structure type with proper type handling
                    if isinstance(stored_data, (list, tuple)):  # Explicitly check if it's a list or tuple
                        from typing import cast, List, Any
                        # Use cast to tell type checker this is a list
                        list_data = cast(List[Any], stored_data)
                        first_item = list_data[0] if list_data else None
                    elif hasattr(stored_data, 'keys') and not isinstance(stored_data, list):
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
            if hasattr(stored_data, 'keys') and not isinstance(stored_data, list):
                print("Converting single dict to list for table")
                return [stored_data]
                
            # Normal case: stored_data is a list
            table_data: List[Dict[str, Union[str, float, int]]] = []
            # Add type annotation for the loop
            stored_data_list: List[Union[Dict[str, Any], str]] = cast(List[Union[Dict[str, Any], str]], stored_data)
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
                table_data.append({
                    'name': investment_dict.get('name', ''),
                    'type': investment_dict.get('type', ''),
                    'cost': investment_dict.get('cost', 0),
                    'savings': investment_dict.get('savings', 0),
                    'implementation_time': investment_dict.get('implementation_time', 0),
                    'efficiency': investment_dict.get('efficiency', 0),
                    'risk': investment_dict.get('risk', 0),
                    'roi': investment_dict.get('roi', 0)
                })
                
            print(f"Table data created with {len(table_data)} items")
            return table_data
            
        except Exception as e:
            # Collect the error
            collect_error("update_investments_table")
            print(f"Error in update_investments_table: {str(e)}")
            # Return empty data instead of crashing
            return []

    # Callback to toggle investment parameters based on selected type
    # This callback updates the visibility of investment parameter containers based on the selected investment type.
    # It shows the appropriate parameters for capital, process, or people investments.
    # This logic has been migrated to investment_mgmt/callbacks/__init__.py
    @app.callback(  # type: ignore
        [Output('capital-equipment-params', 'style'),
        Output('process-improvement-params', 'style'),
        Output('people-training-params', 'style')],
        [Input('investment-mgmt-type-input', 'value')]
    )
    def toggle_investment_params(investment_type: str) -> tuple[dict[str, str], dict[str, str], dict[str, str]]:
        """Show parameters based on selected investment type."""
        # Default: all hidden
        capital_style = {"display": "none"}
        process_style = {"display": "none"}
        people_style = {"display": "none"}
        
        # Show the appropriate container based on selection
        if investment_type == 'capital':
            capital_style = {"display": "block"}
        elif investment_type == 'process':
            process_style = {"display": "block"}
        elif investment_type == 'people':
            people_style = {"display": "block"}
        
        return capital_style, process_style, people_style
    
    # Callback to update investment fields based on selected type
    # This callback updates the investment form fields based on the selected investment type and application mode.
    # It changes the rate label and visibility of lifespan, efficiency, OEE, and staffing fields depending on the investment type and mode (business or personal finance).
    # It also updates the budget label to reflect the context of the investment.  
    # This logic has been migrated to investment_mgmt/callbacks/__init__.py  
    @app.callback(
        [Output('investment-rate-label', 'children'),
        Output('investment-lifespan-container', 'style'),
        Output('investment-efficiency-container', 'style'),
        Output('oee-container', 'style'),
        Output('staffing-container', 'style'),
        Output('budget-label', 'children')],  # New output for budget label
        [Input('investment-type-input', 'value'),
        Input('app-mode', 'value')]
    )
    def update_investment_fields(investment_type: Optional[str], mode: Optional[str]) -> Tuple[str, Dict[str, str], Dict[str, str], Dict[str, str], Dict[str, str], str]:
        """Update investment form fields based on selected investment type."""
        rate_label = "Growth/Return Rate (%):"
        show_lifespan = {'display': 'none'}
        show_efficiency = {'display': 'none'}
        show_oee = {'display': 'none'}
        show_staffing = {'display': 'none'}
        
        # Set budget label based on mode
        if mode == 'business':
            budget_label = "Department Budget (£):"
        else:
            budget_label = "Investment Budget (£):"
        
        # Business mode
        if mode == 'business':
            if investment_type == 'cash':
                rate_label = "Interest/Return Rate (%):"
            elif investment_type == 'equipment':
                rate_label = "Depreciation Rate (%):"
                show_lifespan = {'display': 'block'}
                show_efficiency = {'display': 'block'}
                show_oee = {'display': 'block'}  # Show OEE components for equipment
            elif investment_type == 'property':
                rate_label = "Appreciation Rate (%):"
                show_lifespan = {'display': 'block'}
            elif investment_type == 'rd':
                rate_label = "Expected Return Rate (%):"
                show_efficiency = {'display': 'block'}
            elif investment_type in ['marketing', 'it', 'training']:
                rate_label = "Impact Rate (%):"
                show_efficiency = {'display': 'block'}
            elif investment_type == 'staffing':  # New staff option
                rate_label = "Long-term Productivity Rate (%):"
                show_efficiency = {'display': 'block'}
                show_staffing = {'display': 'block'}  # Show staffing inputs
        # Personal finance mode
        else:
            if investment_type == 'cash':
                rate_label = "Interest Rate (%):"
            elif investment_type == 'stocks':
                rate_label = "Expected Return (%):"
            elif investment_type == 'bonds':
                rate_label = "Yield (%):"
            elif investment_type == 'property':
                rate_label = "Appreciation Rate (%):"
                show_lifespan = {'display': 'block'}
            elif investment_type == 'education':
                rate_label = "Income Impact Rate (%):"
                show_efficiency = {'display': 'block'}
            elif investment_type == 'business':
                rate_label = "Expected ROI (%):"
                show_efficiency = {'display': 'block'}
        
        return rate_label, show_lifespan, show_efficiency, show_oee, show_staffing, budget_label

    # Register all callbacks for Investment Management tab# Callback to calculate investment analysis metrics
    # This callback calculates and displays investment analysis metrics based on user inputs.
    # It computes ROI, IRR, and payback period based on the budget, investment parameters, and OEE inputs.
    # It also handles staffing inputs for business mode and uses sample data if no stored data is available.
    # This logic has been migrated to globalinvestment_mgmt/callbacks/__init__.py
    @app.callback(
        [Output('roi-metric', 'children'),
        Output('irr-metric', 'children'),
        Output('payback-metric', 'children')],
        [Input('budget-slider', 'value'),  # Changed from investment-slider
        Input('budget-timeframe', 'value'),  # Added new input
        Input('investment-type-input', 'value'),
        Input('investment-rate-input', 'value'),
        Input('investment-lifespan-input', 'value'),
        Input('investment-efficiency-input', 'value'),
        # New OEE inputs
        Input('availability-input', 'value'),
        Input('performance-input', 'value'),
        Input('quality-input', 'value'),
        # New staffing inputs
        Input('staff-count-input', 'value'),
        Input('ramp-up-input', 'value'),
        Input('training-cost-input', 'value')],
        [State('financial-data-store', 'data')]
    )
    def update_investment_metrics(budget: Optional[float], timeframe: Optional[int], investment_type: Optional[str], investment_rate: Optional[float], 
                                investment_lifespan: Optional[int], efficiency_impact: Optional[float],
                                availability: Optional[float], performance: Optional[float], quality: Optional[float],
                                staff_count: Optional[int], ramp_up: Optional[int], training_cost: Optional[float], stored_data: Optional[Dict[str, Any]]) -> Tuple[str, str, str]:
        """Calculate and display investment analysis metrics."""
        from typing import Dict, Any, cast  # Import at function level to ensure Any is in scope
        
        if budget is None or budget <= 0:
            return "N/A", "N/A", "N/A"
        
        # Default to sample data if no stored data with explicit typing
        financial_data: Dict[str, Any] = stored_data if stored_data is not None else get_sample_data()
        
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
            investment_lifespan=investment_lifespan if investment_lifespan is not None else 5,
            efficiency_impact=efficiency_impact if efficiency_impact is not None else 0,
            # New parameters - convert float to int
            oee_availability=int(availability) if availability is not None else 0,
            oee_performance=int(performance) if performance is not None else 0,
            oee_quality=int(quality) if quality is not None else 0,
            staff_count=staff_count if staff_count is not None else 1,
            ramp_up_period=ramp_up if ramp_up is not None else 3,
            training_cost=training_cost if training_cost is not None else 2000
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
                if 'cash_flow' in inv_df.columns:
                    try:
                        # First get the value with proper type handling
                        # Import float for type hint and use explicit casting
                        from typing import Any, cast
                        # Get the value with explicit type annotation directly
                        inv_raw_value = cast(Any, inv_df['cash_flow'].iat[i])
                    except (IndexError, KeyError):
                        inv_raw_value = None
                        
                base_raw_value: Any = None
                if 'cash_flow' in base_df.columns:
                    try:
                        # Get the value with explicit type annotation and cast
                        from typing import cast
                        base_raw_value = cast(Any, base_df['cash_flow'].iat[i])
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
                            if hasattr(inv_value_any, 'item'):
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
                            if hasattr(numeric_result_any, 'item'):
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
                    base_numeric = pd.to_numeric(base_raw_value, errors='coerce')  # type: ignore
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
        metrics = calculate_investment_metrics(incremental_cash_flows, budget)  # Changed from investment to budget
        
        # Format results with robust error handling
        try:
            roi = f"{metrics['roi']:.1f}%"
        except (TypeError, ValueError):
            roi = "N/A"
            
        try:
            irr = f"{metrics['irr']:.1f}%"
        except (TypeError, ValueError):
            irr = "N/A"
            
        payback = f"{metrics['payback_period']:.1f} months" if metrics['payback_period'] < float('inf') else "N/A"
        
        return roi, irr, payback
    
    # Callback for investment comparison chart
    # This callback generates a comparison chart between different investment options.
    # It takes inputs for budget, investment parameters, and OEE/staffing metrics, and uses stored financial data or sample data if none is available.
    # It handles None values for budget and investment parameters, and uses the budget slider value instead of investment slider.
    # This logic has been migrated to investment_mgmt/callbacks/__init__.py
    @app.callback(
        Output('investment-comparison-chart', 'figure'),
        [Input('budget-slider', 'value'),  # Changed from investment-slider
        Input('budget-timeframe', 'value'),  # Added new input
        Input('investment-type-input', 'value'),
        Input('investment-rate-input', 'value'),
        Input('investment-lifespan-input', 'value'),
        Input('investment-efficiency-input', 'value'),
        Input('alternative-investment-type', 'value'),
        Input('alternative-rate-input', 'value'),
        # New OEE inputs
        Input('availability-input', 'value'),
        Input('performance-input', 'value'),
        Input('quality-input', 'value'),
        # New staffing inputs
        Input('staff-count-input', 'value'),
        Input('ramp-up-input', 'value'),
        Input('training-cost-input', 'value')],
        [State('financial-data-store', 'data')]
    )
    def update_investment_comparison(budget: Optional[float], timeframe: Optional[int], investment_type: Optional[str], investment_rate: Optional[float], 
                                    investment_lifespan: Optional[int], efficiency_impact: Optional[float],
                                    alt_type: Optional[str], alt_rate: Optional[float],
                                    availability: Optional[float], performance: Optional[float], quality: Optional[float],
                                    staff_count: Optional[int], ramp_up: Optional[int], training_cost: Optional[float], 
                                    stored_data: Optional[Dict[str, Any]]) -> 'Figure':
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
            sample_data: Dict[str, Any] = get_sample_data()
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
            investment_amount=budget if budget is not None else 0.0,  # Provide default when None
            investment_type=investment_type,
            investment_rate=investment_rate if investment_rate is not None else 5.0,
            investment_lifespan=investment_lifespan if investment_lifespan is not None else 5,
            efficiency_impact=efficiency_impact if efficiency_impact is not None else 0,
            # New parameters - convert float to int
            oee_availability=int(availability) if availability is not None else 0,
            oee_performance=int(performance) if performance is not None else 0,
            oee_quality=int(quality) if quality is not None else 0,
            staff_count=staff_count if staff_count is not None else 1,
            ramp_up_period=ramp_up if ramp_up is not None else 3,
            training_cost=training_cost if training_cost is not None else 2000
        )
        
        # Extract DataFrame from result if it's a tuple
        if isinstance(primary_result, tuple):
            primary_df = primary_result[0]
        else:
            primary_df = primary_result
        
        # Calculate with alternative investment if selected
        if alt_type == 'none':
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
                investment_amount=budget if budget is not None else 0.0,  # Changed from investment to budget
                investment_type=alt_type,
                investment_rate=alt_rate if alt_rate is not None else 3.0,
                investment_lifespan=investment_lifespan if investment_lifespan is not None else 5,
                efficiency_impact=efficiency_impact if efficiency_impact is not None else 0,
                # For simplicity, use same OEE/staffing parameters for alt investment - convert float to int
                oee_availability=int(availability) if availability is not None else 0,
                oee_performance=int(performance) if performance is not None else 0,
                oee_quality=int(quality) if quality is not None else 0,
                staff_count=staff_count if staff_count is not None else 1,
                ramp_up_period=ramp_up if ramp_up is not None else 3,
                training_cost=training_cost if training_cost is not None else 2000
            )
            # Extract DataFrame from result if it's a tuple
            if isinstance(alt_result, tuple):
                alt_df = alt_result[0]
            else:
                alt_df = alt_result
            alt_name = f"{alt_type.title() if alt_type is not None else 'Alternative'} Investment"
        
        # Create comparison chart
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(  # type: ignore
            x=primary_df['date'],
            y=primary_df['net_worth'],
            name=f"{investment_type.title() if investment_type else 'Default'} Investment",
            line=dict(color='#1f77b4', width=2)
        ))
        
        # Cast figure to Any to resolve type checking issues
        from typing import cast, Any
        cast(Any, fig).add_trace(go.Scatter(
            x=alt_df['date'],
            y=alt_df['net_worth'],
            name=alt_name,
            line=dict(color='#ff7f0e', width=2)
        ))
        
        fig.update_layout( # type: ignore
            title=f"Investment Comparison: {investment_type.title() if investment_type else 'Default'} vs {alt_name}",
            xaxis_title="Date",
            yaxis_title="Net Worth (£)",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            hovermode="x unified"
        )
        
        return fig
    
    # This callback validates the investment cost input.
    # It checks if the input is None or empty and returns an appropriate message.   
    # This logic has been migrated to investment_mgmt/callbacks/__init__.py
    @app.callback(
        Output("cost-validation-output", "children"),
        Input("investment-cost-input", "value")
    )
    def validate_cost(value: Optional[float]) -> str:
        if value is None:
            return "Please enter a cost value"
        return ""
    
    # This callback updates the status message after adding an investment.
    # It checks if the investment name, type, and cost are provided, and returns an appropriate message.
    # This callback has been migrated to investment management/callbacks/__init__.py
    @app.callback(
        Output("investment-add-status", "children"),
        [Input('add-investment-button', 'n_clicks')],
        [State('investment-mgmt-name-input', 'value'),
        State('investment-mgmt-type-input', 'value'),
        State('investment-cost-input', 'value')],
        prevent_initial_call=True
    )
    def update_investment_add_status(n_clicks: Optional[int], name: Optional[str], inv_type: Optional[str], cost: Optional[float]) -> html.Span:
        """Show status message after adding investment."""
        if not name:
            return html.Span("Please enter investment name", style={"color": "red"})
        
        if not inv_type:
            return html.Span("Please select investment type", style={"color": "red"})
        
        if not cost:
            return html.Span("Please enter investment cost", style={"color": "red"})
        
        return html.Span("Investment added successfully!", style={"color": "green"})


