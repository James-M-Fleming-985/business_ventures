from dash import Input, Output, State, callback_context, Dash, html
from typing import Dict, List, Any, Optional, Tuple, Union, cast, Callable
from dash._callback import NoUpdate
import plotly.graph_objects as go
from plotly.graph_objects import Figure
import traceback
import pandas as pd
from financial_optimizer.utils import get_sample_data as _get_sample_data, project_financials as _project_financials  # type: ignore

# Create a properly typed wrapper for get_sample_data
def get_sample_data(mode: Optional[str] = None) -> Dict[str, Any]:
    """Wrapper for get_sample_data with proper type annotations."""
    return cast(Dict[str, Any], _get_sample_data(mode))

# Create a properly typed wrapper for project_financials
def project_financials(
    financial_data: Dict[str, Any],
    months: int = 60,
    investment_amount: float = 0.0,
    investment_type: Optional[str] = None,
    investment_rate: float = 5.0,
    investment_lifespan: int = 5,
    efficiency_impact: float = 0,
    calculate_baseline: bool = False
) -> Union[pd.DataFrame, Tuple[pd.DataFrame, pd.DataFrame]]:
    """Wrapper for project_financials with proper type annotations."""
    result: Union[pd.DataFrame, Tuple[pd.DataFrame, pd.DataFrame]] = _project_financials(
        financial_data=financial_data,
        months=months,
        investment_amount=investment_amount,
        investment_type=investment_type,
        investment_rate=investment_rate,
        investment_lifespan=investment_lifespan,
        efficiency_impact=efficiency_impact,
        calculate_baseline=calculate_baseline
    )
    # Explicitly cast the result to match the return type annotation
    if isinstance(result, tuple) and len(result) == 2:
        return cast(Tuple[pd.DataFrame, pd.DataFrame], result)
    else:
        return cast(pd.DataFrame, result)

def collect_error(function_name: str) -> None:
    """Log errors from callbacks for tracking purposes."""
    print(f"Error in {function_name}:")
    print(traceback.format_exc())

def create_empty_cumulative_chart() -> "Figure":
    """Create an empty chart for when no investments are available."""
    fig = go.Figure()
    # Cast to Any to bypass type checking limitations with Plotly
    from typing import cast, Any
    cast(Any, fig).add_annotation(
        text="No investment data available",
        xref="paper", yref="paper",
        x=0.5, y=0.5, showarrow=False
    )
    cast(Any, fig).update_layout(
        title='Investment Savings Over Time',
        xaxis_title='Date',
        yaxis_title='Monthly Savings (£)',
        template='plotly_white'
    )
    return fig

from datetime import datetime, date
from typing import Union

def calculate_percent_complete(start_date: Union[datetime, date], end_date: Union[datetime, date], current_date: Union[datetime, date]) -> float:
    """
    Calculate the percentage of completion between two dates.
    """
    # If the start and end dates are the same, return 100% complete
    if start_date == end_date:
        return 1.0
    
    # Convert date objects to datetime if necessary
    from datetime import datetime, date
    
    if isinstance(start_date, date) and not isinstance(start_date, datetime):
        start_date = datetime.combine(start_date, datetime.min.time())
    
    if isinstance(end_date, date) and not isinstance(end_date, datetime):
        end_date = datetime.combine(end_date, datetime.min.time())
    
    if isinstance(current_date, date) and not isinstance(current_date, datetime):
        current_date = datetime.combine(current_date, datetime.min.time())
    
    # Now all variables are datetime objects
    total_duration = (end_date - start_date).total_seconds()
    elapsed_duration = (current_date - start_date).total_seconds()
    
    # Calculate percentage (bounded between 0 and 1)
    percentage = elapsed_duration / total_duration if total_duration > 0 else 0
    return max(0, min(1, percentage))

def register_shared_callbacks(app: Dash):
    """Register callbacks that affect multiple tabs"""

    # Create a local reference to the outer functions
    local_collect_error = collect_error
    local_create_empty_cumulative_chart = create_empty_cumulative_chart
    local_calculate_percent_complete = calculate_percent_complete
    local_get_sample_data = get_sample_data  # Add this line
    local_project_financials = project_financials  # Also add this as it will likely be needed
    
    # @app.callback(  # type: ignore
    #     [Output('total-investment-cost', 'children'),
    #      Output('total-annual-savings', 'children'),
    #      Output('average-roi', 'children')],
    #     Input('investments-store', 'data')
    # )
    # def update_shared_metrics(investments_data: Optional[List[Dict[str, Any]]]) -> Tuple[Union[float, NoUpdate], Union[float, NoUpdate], Union[float, NoUpdate]]:
    #     """Update global investment metrics based on stored data."""
    #     try:
    #         ctx = callback_context
    #         if not investments_data:
    #             return 0, 0, 0
    #         total_cost = sum(item.get('cost', 0) for item in investments_data)
    #         total_savings = sum(item.get('savings', 0) for item in investments_data)
    #         average_roi = total_savings / total_cost if total_cost else 0
    #         return total_cost, total_savings, average_roi
    #     except Exception as e:
    #         print(f"Error updating shared metrics: {e}")
    #         return NoUpdate(), NoUpdate(), NoUpdate()
        
    # This callback updates the investments store when rows are deleted from the table.
    # It compares the previous and current table data to determine which rows were deleted.
    # Type ignore here because Dash's callback typing is complex and dynamically generated
    @app.callback(  # type: ignore
        [Output('investments-store', 'data', allow_duplicate=True)],
        [Input('investments-table', 'data_previous'),
        Input('investments-table', 'data')],
        [State('investments-store', 'data')],
        prevent_initial_call=True
    )
    def update_investments_store(previous_table: Optional[List[Dict[str, Any]]], current_table: Optional[List[Dict[str, Any]]],  # type: ignore[unused-function]
                            stored_investments: Optional[List[Dict[str, Any]]]) -> Tuple[List[Dict[str, Any]]]:  # type: ignore
        """Update the investments store when rows are deleted from the table."""
        if previous_table is None or current_table is None:
            return (stored_investments or [],)  # Return as a tuple with one element
        
        # If stored_investments is None, use an empty list
        investments = stored_investments or []
        
        # If a row was deleted
        if len(current_table) < len(previous_table):
            # Find the deleted row by comparing the two tables
            deleted_names = {row['name'] for row in previous_table} - {row['name'] for row in current_table}
            
            if deleted_names:
                # Filter the store to remove deleted investments
                new_store = [inv for inv in investments if inv.get('name', '') not in deleted_names]
                print(f"Deleted {len(deleted_names)} investment(s): {', '.join(deleted_names)}")
                print(f"Store now has {len(new_store)} investments")
                return (new_store,)  # Return as a tuple with one element
        
        return (investments,)  # Return as a tuple with one element

    # This callback updates the investment totals displayed on the dashboard.
    # It calculates the total investment cost, total annual savings, and average ROI based on the investments table data.
    # It uses the investments table data to compute these values and updates the display accordingly.
    # Update investment totals
    # This callback has been migrated to shared/callbacks/__init__.py
    # @app.callback(  # type: ignore
    #     [
    #         Output('total-investment-cost', 'children', allow_duplicate=True),
    #         Output('total-annual-savings', 'children'),
    #         Output('average-roi', 'children'),
    #     ],
    #     [Input('investments-table', 'data')],
    #     prevent_initial_call=True
    # )
    # def update_investment_totals(investments):
    #     try:
    #         # Initialize variables
    #         total_cost = 0.0
    #         total_savings = 0.0
    #         
    #         # Make sure we have data to process
    #         data = investments if investments else []
    #         
    #         for item in data:
    #             # Get cost value, default to 0 if missing or None
    #             cost_val = item.get('cost', 0)
    #             if cost_val is not None:
    #                 try:
    #                     total_cost += float(cost_val)
    #                 except (ValueError, TypeError):
    #                     pass  # Skip invalid values
    #             
    #             # Get savings value, default to 0 if missing or None
    #             savings_val = item.get('savings', 0)
    #             if savings_val is not None:
    #                 try:
    #                     total_savings += float(savings_val)
    #                 except (ValueError, TypeError):
    #                     pass  # Skip invalid values
    #         
    #         # Calculate ROI
    #         avg_roi = (total_savings / total_cost * 100) if total_cost > 0 else 0
    #         
    #         # Format the outputs
    #         return f"£{total_cost:,.2f}", f"£{total_savings:,.2f}/year", f"{avg_roi:.1f}%"
    #     
    #     except Exception as e:
    #         print(f"Error in update_investment_totals: {str(e)}")
    #         return "£0", "£0/year", "0%"
        
    # This callback updates the budget allocation chart based on selected criteria and display options.
    # It generates a Plotly figure showing the budget allocation across different investments.  
    @app.callback(  # type: ignore
        [Output('budget-allocation-chart', 'figure'),
        Output('budget-utilization-display', 'children')],
        [Input('investments-store', 'data'),
        Input('budget-slider', 'value'),
        Input('prioritization-criteria', 'value'),
        Input('display-options', 'value')]
    )
    def update_budget_allocation_chart(investments: Optional[List[Dict[str, Any]]],  # noqa
                                    budget: Optional[float], 
                                    criteria: Optional[List[str]], 
                                    display_options: Optional[List[str]]) -> Tuple['Figure', html.Div]:
        """
        Generate a budget allocation chart based on selected criteria and display options.
        Features smooth updates when budget changes.
        """
        try:
            # Import Any at the beginning of the function to ensure it's available in this scope
            from typing import Any, Dict, List
            
            # Debug info
            print(f"Budget chart update - investments type: {type(investments).__name__}")
            print(f"Investments length: {len(investments) if investments is not None and hasattr(investments, '__len__') else 'N/A'}")
            
            # Create empty chart if no investments
            if not investments:
                empty_fig = go.Figure()
                # Cast to Any to bypass type checking limitations with Plotly
                from typing import cast, Any
                cast(Any, empty_fig).update_layout(
                    title='Investment Budget Allocation',
                    xaxis_title='Investments',
                    yaxis_title='Cost (£)',
                    yaxis_range=[0, budget * 1.1] if budget else [0, 100000],
                    template='plotly_white',
                    showlegend=False
                )
                # Cast to Any to bypass type checking issues with Plotly
                from typing import cast, Any
                cast(Any, empty_fig).add_annotation(
                    text="No investments available",
                    xref="paper", yref="paper",
                    x=0.5, y=0.5, showarrow=False
                )
                
                utilization_info = html.Div([
                    html.H6("Budget Utilization:"),
                    html.P(f"£0 / £{budget or 0:,.0f}"),
                    html.P("0% of budget allocated")
                ])
                
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
                'roi': 0.5 if 'roi' in criteria else 0,
                'risk': 0.2 if 'risk' in criteria else 0,
                'time': 0.1 if 'time' in criteria else 0,
                'efficiency': 0.1 if 'efficiency' in criteria else 0,
                'savings': 0.1 if 'savings' in criteria else 0
            }
            
            # Normalize weights to sum to 1
            total_weight = sum(weights.values()) or 1  # Avoid division by zero
            weights = {k: v/total_weight for k, v in weights.items()}
            
            # Calculate score for each investment
            scored_investments: List[Dict[str, Any]] = []
            for inv in parsed_investments:
                try:
                    # Extract values safely
                    roi = float(inv.get('roi', 0) or 0)
                    risk = float(inv.get('risk', 3) or 3)
                    impl_time = float(inv.get('implementation_time', 6) or 6)
                    efficiency = float(inv.get('efficiency', 0) or 0)
                    savings = float(inv.get('savings', 0) or 0)
                    
                    # Normalize values
                    norm_roi = roi  # Already a ratio
                    norm_risk = (6 - risk) / 5  # Invert risk (lower is better)
                    norm_time = 1 / (impl_time or 1)  # Invert time (shorter is better)
                    norm_efficiency = efficiency / 100  # Convert to ratio
                    
                    # Find max savings for normalizing
                    all_savings = [float(i.get('savings', 0) or 0) for i in parsed_investments]
                    max_savings = max(all_savings) if all_savings else 1
                    norm_savings = savings / max_savings if max_savings else 0
                    
                    # Calculate composite score
                    score = (
                        weights['roi'] * norm_roi +
                        weights['risk'] * norm_risk +
                        weights['time'] * norm_time +
                        weights['efficiency'] * norm_efficiency +
                        weights['savings'] * norm_savings
                    )
                    
                    # Copy investment and add score
                    scored_inv = dict(inv)
                    scored_inv['priority_score'] = score
                    scored_investments.append(scored_inv)
                except Exception as e:
                    print(f"Error scoring investment {inv.get('name', 'unknown')}: {e}")
                    continue
                    
            # Sort by score (highest first)
            sorted_investments = sorted(
                scored_investments,
                key=lambda x: x.get('priority_score', 0),
                reverse=True
            )
            
            # Select investments within budget
            selected: List[Dict[str, Any]] = []
            unselected: List[Dict[str, Any]] = []
            running_total: float = 0.0
            
            # Default budget if not provided
            if budget is None:
                budget = 0.0

            for inv in sorted_investments:
                cost = float(inv.get('cost', 0) or 0)
                if running_total + cost <= budget:
                    selected.append(inv) # <-- THIS IS LINE 268
                    running_total += cost
                else:
                    unselected.append(inv)
                    
            # Create figure
            fig = go.Figure()
            
            # Color mapping
            color_map = {
                'capital': '#1f77b4',    # Blue
                'process': '#ff7f0e',    # Orange
                'people': '#2ca02c',     # Green
                'software': '#d62728',   # Red
                'facility': '#9467bd',   # Purple
                'other': '#8c564b'       # Brown
            }
            
            # Add bars and track cumulative
            cumulative_x: List[int] = []
            cumulative_y: List[float] = []
            running_sum: float = 0.0
            
            # Add selected investments
            for i, inv in enumerate(selected):
                name = inv.get('name', f'Investment {i+1}')
                cost = float(inv.get('cost', 0) or 0)
                inv_type = str(inv.get('type', 'other')).lower()
                roi = float(inv.get('roi', 0) or 0)
                
                fig.add_trace(go.Bar(  # type: ignore
                    x=[i],
                    y=[cost],
                    name=name,
                    text=f"{name}<br>£{cost:,.0f}<br>ROI: {roi:.1%}",
                    hoverinfo='text',
                    marker_color=color_map.get(inv_type, color_map['other']),
                    showlegend=False
                ))
                
            # Add bars and track cumulative
            cumulative_x = []
            cumulative_y = []
            running_sum = 0.0  # Change to float initialization

            # Add unselected if requested
            if 'unselected' in display_options:
                for j, inv in enumerate(unselected):
                    i = j + len(selected)
                    name = inv.get('name', f'Investment {i+1}')
                    cost = float(inv.get('cost', 0) or 0)
                    inv_type = str(inv.get('type', 'other')).lower()
                    roi = float(inv.get('roi', 0) or 0)
                    
                    fig.add_trace(go.Bar(  # type: ignore
                        x=[i],
                        y=[cost],
                        name=name,
                        text=f"{name} (Over Budget)<br>£{cost:,.0f}<br>ROI: {roi:.1%}",
                        hoverinfo='text',
                        marker_color=color_map.get(inv_type, color_map['other']),
                        marker_opacity=0.4,
                        showlegend=False
                    ))
                    
            # Add cumulative line
            if 'cumulative' in display_options and cumulative_x:
                fig.add_trace(go.Scatter(  # type: ignore
                    x=cumulative_x,
                    y=cumulative_y,
                    mode='lines+markers',
                    name='Cumulative Cost',
                    line=dict(color='red', width=3),
                    hoverinfo='y',
                    text=[f"Cumulative: £{y:,.0f}" for y in cumulative_y],
                ))
                
            # Add budget line
            if 'budget_line' in display_options:
                display_width = len(selected) + (len(unselected) if 'unselected' in display_options else 0)
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
                        font=dict(color="green")
                    ) 
                    
            # Update layout
            chart_max = max(budget * 1.1, running_sum * 1.1) if budget or running_sum else 100000
            # Cast to Any to bypass type checking limitations with Plotly
            from typing import cast, Any
            fig_any = cast(Any, fig)
            fig_any.update_layout(
                title='Investment Budget Allocation',
                xaxis_title='Prioritized Investments',
                yaxis_title='Cost (£)',
                yaxis_range=[0, chart_max],
                template='plotly_white',
                margin=dict(l=50, r=50, t=50, b=50),
                hovermode='closest',
                transition_duration=500  # Smooth animation
            )
            
            # Add tick labels if we have investments
            if selected or (unselected and 'unselected' in display_options):
                shown_investments = selected + (unselected if 'unselected' in display_options else [])
                # Cast to Any to bypass type checking limitations with Plotly
                from typing import cast, Any
                cast(Any, fig).update_layout(
                    xaxis=dict(
                        tickmode='array',
                        tickvals=list(range(len(shown_investments))),
                        ticktext=[inv.get('name', f'Inv {i+1}') for i, inv in enumerate(shown_investments)]
                    )
                )
                
            # Create utilization display
            pct_utilized = (running_sum / budget * 100) if budget and budget > 0 else 0
            utilization_info = html.Div([
                html.H6("Budget Utilization:"),
                html.P(f"£{running_sum:,.0f} / £{budget:,.0f}"),
                html.Div([
                    html.Span(f"{pct_utilized:.1f}% of budget allocated", 
                        style={"color": "green" if pct_utilized <= 100 else "red"})
                ]),
                html.Hr(),
                html.H6("Investments:"),
                html.P(f"{len(selected)} selected, {len(unselected)} excluded"),
                html.P(f"Average ROI: {(sum([float(inv.get('roi', 0) or 0) for inv in selected]) / len(selected) if selected else 0):.1%}")
            ])
            
            return fig, utilization_info
            
        except Exception as e:
            # Use error collector
            local_collect_error("update_budget_allocation_chart")
            print(f"Error in budget allocation chart: {str(e)}")
            
            # Return fallback figure
            error_fig = go.Figure()
            # Cast to Any to bypass type checking limitations with Plotly
            from typing import cast, Any
            cast(Any, error_fig).add_annotation(
                text=f"Error rendering chart: {str(e)}",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(color="red")
            )
            
            error_info = html.Div([
                html.H6("Error in chart:"),
                html.P(str(e), style={"color": "red"})
            ])
            
            return error_fig, error_info
        
    # This function is already defined above with a callback decorator
    # This callback updates the investment summary statistics displayed on the dashboard.
    # It generates a summary of the investments, including total cost, annual savings, ROI, andpayback period, and displays it in a formatted HTML div.
    # It uses the investments store data to compute these values and updates the display accordingly.
    # This callback has been migrated to shared/callbacks/__init__.py
    @app.callback(
        Output("investment-summary-stats", "children"),
        Input("investments-store", "data")
    )
    def update_investment_summary(investments: Optional[List[Dict[str, Any]]]) -> html.Div:
        """Generate summary statistics about investments."""
        if not investments:
            return html.Div([html.P("No investments available.")])
        
        try:
            # Calculate totals
            total_investments = len(investments)
            total_cost = sum(float(inv.get('cost', 0) or 0) for inv in investments)
            total_annual_savings = sum(float(inv.get('savings', 0) or 0) for inv in investments)
            
            # Count by status
            completed = sum(1 for inv in investments if inv.get('status') == 'completed')
            in_progress = sum(1 for inv in investments if inv.get('status') == 'in_progress')
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
                payback_period = float('inf')
            
            # Create summary
            return html.Div([
                html.Div([
                    html.Div([
                        html.H6("Total Investments"),
                        html.P(f"{total_investments}", className="stat-value")
                    ], className="summary-stat"),
                    
                    html.Div([
                        html.H6("Total Cost"),
                        html.P(f"£{total_cost:,.0f}", className="stat-value")
                    ], className="summary-stat"),
                    
                    html.Div([
                        html.H6("Annual Savings"),
                        html.P(f"£{total_annual_savings:,.0f}", className="stat-value")
                    ], className="summary-stat")
                ], className="stat-row"),
                
                html.Div([
                    html.Div([
                        html.H6("Overall ROI"),
                        html.P(f"{overall_roi:.1%}", className="stat-value")
                    ], className="summary-stat"),
                    
                    html.Div([
                        html.H6("Payback Period"),
                        html.P(f"{payback_period:.1f} years" if payback_period < 100 else "N/A", 
                            className="stat-value")
                    ], className="summary-stat"),
                    
                    html.Div([
                        html.H6("Status Breakdown"),
                        html.P([
                            html.Span(f"{completed} Completed", style={"color": "green"}),
                            html.Span(" • "),
                            html.Span(f"{in_progress} In Progress", style={"color": "orange"}),
                            html.Span(" • "),
                            html.Span(f"{planned} Planned", style={"color": "blue"})
                        ], className="stat-value")
                    ], className="summary-stat")
                ], className="stat-row")
            ])
        
        except Exception as e:
            local_collect_error("update_investment_summary")
            return html.Div(f"Error generating summary: {str(e)}", style={"color": "red"})
        
    @app.callback(
        Output("cumulative-savings-chart", "figure"),
        Input("investments-store", "data")
    )
    def update_cumulative_savings_chart(investments: Optional[List[Dict[str, Any]]]) -> "Figure":
        """Create a chart showing cumulative savings over time."""
        import pandas as pd
        
        if not investments:
            return local_create_empty_cumulative_chart()
        
        try:
            # Get current date for reference
            current_date = pd.Timestamp.now()
            
            # Create date range from 12 months ago to 5 years in the future
            start_date = current_date - pd.DateOffset(months=12)
            end_date = current_date + pd.DateOffset(years=5)
            date_range = pd.date_range(start=start_date, end=end_date, freq='M')
            
            # Initialize dataframe
            df = pd.DataFrame({'date': date_range})
            df['monthly_savings'] = 0.0  # Explicitly initialize as float
            df['cumulative_savings'] = 0.0  # Explicitly initialize as float
            
            # Add savings from each investment
            for inv in investments:
                # Define name with default value before try block to avoid "name is possibly unbound" error
                name = 'Unknown'
                try:
                    # Extract values safely
                    name = inv.get('name', 'Unnamed')
                    savings = float(inv.get('savings', 0) or 0)
                    monthly_savings = savings / 12
                    
                    # Get implementation dates with fallbacks
                    try:
                        # Import and use pandas directly for type safety
                        import pandas as pd
                        
                        implementation_start = inv.get('implementation_start')
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
                            impl_time = int(inv.get('implementation_time', 3) or 3)
                            start_date = current_date - pd.DateOffset(months=impl_time//2)
                            
                        implementation_end = inv.get('implementation_end')
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
                                impl_time = int(inv.get('implementation_time', 3) or 3)
                                end_date = pd.Timestamp(start_date + pd.DateOffset(months=impl_time))
                        else:
                            # Use implementation_time from start date if no end date
                            impl_time = int(inv.get('implementation_time', 3) or 3)
                            # Skip intermediate variable and directly convert to Timestamp
                            end_date = pd.Timestamp(start_date + pd.DateOffset(months=impl_time))
                    except:
                        # Fallback if date parsing fails
                        start_date = current_date - pd.DateOffset(months=1)
                        end_date = current_date + pd.DateOffset(months=2)
                    
                    # Get investment status
                    status = inv.get('status', 'planned')
                    
                    # Add monthly savings based on status and implementation dates
                    for i, date in enumerate(date_range):
                        if status == 'completed' and date > end_date:
                            # Full savings for completed investments
                            # Get current value and ensure it's numeric using direct float conversion
                            try:
                                # Re-import Any directly at the usage site to ensure it's recognized
                                from typing import Any, cast
                                # Use cast to explicitly tell the type checker to treat the value as Any
                                raw_value = cast(Any, df.loc[i, 'monthly_savings'])
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
                                        if isinstance(numeric_result, float) and math.isnan(numeric_result):
                                            numeric_value = 0.0
                                        else:
                                            numeric_value = float(numeric_result)
                                        
                                        if isinstance(numeric_value, float) and math.isnan(numeric_value):
                                            current_value = 0.0
                                        else:
                                            current_value = float(numeric_value)
                                    except:
                                        current_value = 0.0
                            except (ValueError, TypeError, KeyError, IndexError):
                                current_value = 0.0
                            df.loc[i, 'monthly_savings'] = current_value + monthly_savings
                        elif status == 'in_progress':
                            # Scale savings by completion percentage for in-progress investments
                            if date > start_date:
                                if date <= end_date:
                                    # During implementation - partial benefit
                                    pct_complete = calculate_percent_complete(start_date, end_date, date)
                                    try:
                                        # Access the value with explicit cast to Any
                                        from typing import Any, cast
                                        raw_value = cast(Any, df.loc[i, 'monthly_savings'])
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
                                    df.loc[i, 'monthly_savings'] = current_value + (monthly_savings * pct_complete)
                        elif status == 'planned':
                            # Only add savings after implementation for planned investments
                            if date > end_date:
                                try:
                                    # Handle type conversion explicitly with proper typing
                                    from typing import Any, cast
                                    raw_value = cast(Any, df.loc[i, 'monthly_savings'])
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
                                df.loc[i, 'monthly_savings'] = current_value + monthly_savings
                except Exception as e:
                    print(f"Error processing investment {name}: {str(e)}")
                    continue
                    
            # Calculate cumulative savings
            df['cumulative_savings'] = df['monthly_savings'].cumsum()
            
            # Create figure
            fig = go.Figure()
            
            # Add bar chart for monthly savings
            fig.add_trace(go.Bar(  # type: ignore
                x=df['date'],
                y=df['monthly_savings'],
                name='Monthly Savings',
                marker_color='lightblue'
            ))
            
            # Add line chart for cumulative savings
            fig.add_trace(go.Scatter(  # type: ignore
                x=df['date'],
                y=df['cumulative_savings'],
                name='Cumulative Savings',
                mode='lines',
                line=dict(color='darkblue', width=2),
                yaxis='y2'
            ))
            
            # Add vertical line for current date
            from typing import cast, Any
            # Assign the cast result to a variable for clearer type handling
            any_fig = cast(Any, fig)
            any_fig.add_shape(
                type="line",
                x0=current_date,
                y0=0,
                x1=current_date,
                y1=df['monthly_savings'].max() * 1.2 if df['monthly_savings'].max() > 0 else 10000,
                line=dict(color="black", width=1, dash="dot"),
            )
            
            # Layout with two y-axes - use type casting to avoid type checking issues
            from typing import cast, Any
            # Assign the cast result to a variable for clearer type handling
            any_fig = cast(Any, fig)
            any_fig.update_layout(
                title='Investment Savings Over Time',
                xaxis_title='Date',
                yaxis_title='Monthly Savings (£)',
                yaxis2=dict(
                    title='Cumulative Savings (£)',
                    titlefont=dict(color='darkblue'),
                    tickfont=dict(color='darkblue'),
                    overlaying='y',
                    side='right'
                ),
                template='plotly_white',
                hovermode='x unified',
                barmode='stack',
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                )
            )
            
            return fig
            
        except Exception as e:
            local_collect_error("update_cumulative_savings_chart")
            print(f"Error creating cumulative savings chart: {str(e)}")
            return local_create_empty_cumulative_chart()
        
    # Callback to update app title based on mode
    # This callback updates the application title based on the selected mode (business or personal).
    # It changes the title text to reflect the current mode, providing context for the user.
    # This logic has been migrated to shared/callbacks/__init__.py
    @app.callback(  # type: ignore
        Output('app-title', 'children'),
        [Input('app-mode', 'value')]
    )
    def update_app_title(mode: Optional[str]) -> str:
        """Update the app title based on the selected mode."""
        if mode == 'business':
            return "SLS Surface Finish Finance"
        else:
            return "Financial Optimizer"
        
    # Update the existing metric titles callback to include spending metric
    # This callback updates the metric titles based on the application mode.
    # It changes the titles for worth, flow, and spending metrics to reflect the current mode (business or personal).
    # This logic has been migrated to shared/callbacks/__init__.py
    @app.callback(  # type: ignore
        [Output('worth-metric-title', 'children'),
        Output('flow-metric-title', 'children'),
        Output('spend-metric-title', 'children')],  # New output for spending
        [Input('app-mode', 'value')]
    )
    def update_metric_titles(mode: Optional[str]):
        """Update metric titles based on application mode."""
        if mode == 'business':
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
        [Output('current-spending', 'children'),
        Output('projected-spending', 'children'),
        Output('spending-optimization', 'children')],
        [Input('time-horizon-slider', 'value'),
        Input('budget-slider', 'value'),
        Input('budget-timeframe', 'value'),
        Input('investment-type-input', 'value'),
        Input('investment-rate-input', 'value'),
        Input('investment-lifespan-input', 'value'),
        Input('investment-efficiency-input', 'value'),
        Input('app-mode', 'value')],
        [State('financial-data-store', 'data')]
    )
    def update_spending_metrics(months: Optional[int], budget: Optional[float], timeframe: Optional[int], 
                            investment_type: Optional[str], investment_rate: Optional[float], 
                            investment_lifespan: Optional[int], efficiency_impact: Optional[float], 
                            mode: Optional[str], stored_data: Optional[Dict[str, Any]]) -> Tuple[str, str, str]:
        """Update the spending metrics based on budget control."""
        # Default to sample data if no stored data with explicit typing
        financial_data: Dict[str, Any]
        if stored_data is not None:
            financial_data = stored_data
        else:
            financial_data = cast(Dict[str, Any], local_get_sample_data())

        # Declare variable types once at the beginning
        baseline_current: float
        baseline_projected: float
        investment_projected: float
        
        # Handle possible None values for months
        effective_months: int
        if months is None:
            effective_months = timeframe * 12 if timeframe else 60  # Convert years to months or default to 60
        else:
            effective_months = months
        
        # Use timeframe for investment lifespan if available - ensure type consistency
        effective_investment_lifespan: int
        if timeframe:
            effective_investment_lifespan = timeframe
        else:
            effective_investment_lifespan = investment_lifespan if investment_lifespan is not None else 5
        
        # Calculate baseline (no investment)
        effective_months = months if months is not None else 60
        baseline_result = local_project_financials(
            financial_data,
            months=effective_months,
            investment_amount=0.0,
            investment_type=investment_type,
            investment_rate=investment_rate if investment_rate is not None else 5.0,
            investment_lifespan=effective_investment_lifespan,
            efficiency_impact=0
        )
        
        # Extract DataFrame from result (handle both single DataFrame and tuple returns)
        if isinstance(baseline_result, tuple):
            baseline_df = baseline_result[0]
        else:
            baseline_df = baseline_result
        # Calculate with investment
        investment_result = local_project_financials(
            financial_data,
            months=effective_months,
            investment_amount=budget if budget is not None else 0,
            investment_type=investment_type,
            investment_rate=investment_rate if investment_rate is not None else 5.0,
            investment_lifespan=effective_investment_lifespan,
            efficiency_impact=efficiency_impact if efficiency_impact is not None else 0
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
        expense_columns = ['operating_expenses', 'expenses', 'total_expenses', 'spending']
        
        # Find the first available expense column in baseline_df
        expense_col = next((col for col in expense_columns if col in baseline_df.columns), None)
        
        # If no expense column is found, use a default or fallback approach
        if expense_col:
            # Use safe value extraction with explicit typing and error handling
            try:
                baseline_current_val = cast(Any, baseline_df[expense_col].iat[0])
                baseline_current = safe_float_convert(baseline_current_val)
                
                baseline_projected_val = cast(Any, baseline_df[expense_col].iat[-1])
                baseline_projected = safe_float_convert(baseline_projected_val)
                
                # Get investment current value but don't store in a separate variable since it's not used
                # We're intentionally not using this value, just fetching it
                _ = cast(Any, investment_df[expense_col].iat[0])
                
                investment_projected_val = cast(Any, investment_df[expense_col].iat[-1])
                investment_projected = safe_float_convert(investment_projected_val)
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
            if 'ebitda' in baseline_df.columns:
                # Use negative EBITDA as a proxy for expenses (not ideal but better than error)
                baseline_current_val = cast(Any, baseline_df['ebitda'].iat[0])
                baseline_current = safe_float_convert(baseline_current_val) * -1
                baseline_projected_val = cast(Any, baseline_df['ebitda'].iat[-1])
                baseline_projected = safe_float_convert(baseline_projected_val) * -1
                # Get investment current value but don't store in a variable since it's not used
                _ = cast(Any, investment_df['ebitda'].iat[0])
                investment_projected_val = cast(Any, investment_df['ebitda'].iat[-1])
                investment_projected = safe_float_convert(investment_projected_val) * -1
            else:
                # No appropriate columns found, default to zero
                baseline_current = 0.0
                baseline_projected = 0.0
                # Removed unused variable
                investment_projected = 0.0

        # Calculate spending optimization (how much is saved on operational expenses)
        spending_optimization = baseline_projected - investment_projected
        optimization_percentage = (spending_optimization / baseline_projected) * 100 if baseline_projected > 0 else 0
        
        # Format the output based on mode
        if mode == 'business':
            current_spending = f"£{baseline_current:,.2f}/mo"
            projected_spending = f"£{investment_projected:,.2f}/mo"
            savings_text = f"Save £{spending_optimization:,.2f}/mo ({optimization_percentage:.1f}%)"
        else:
            current_spending = f"£{baseline_current:,.2f}/mo"
            projected_spending = f"£{investment_projected:,.2f}/mo"
            savings_text = f"Save £{spending_optimization:,.2f}/mo ({optimization_percentage:.1f}%)"
        
        return current_spending, projected_spending, savings_text

    # Callback for updating metrics
    # This callback updates the financial metrics based on the selected time horizon, budget, investment parameters, and application mode.
    # It calculates current and projected net worth, cash flow, and returns formatted strings for display.
    # This logic has been migrated to shared/callbacks/__init__.py
    @app.callback(  # type: ignore
        [Output('current-net-worth', 'children'),
        Output('projected-net-worth', 'children'),
        Output('current-cash-flow', 'children'),
        Output('projected-cash-flow', 'children')],
        [Input('time-horizon-slider', 'value'),
        Input('budget-slider', 'value'),  # Changed from investment-slider
        Input('budget-timeframe', 'value'),  # Added new input
        Input('investment-type-input', 'value'),
        Input('investment-rate-input', 'value'),
        Input('investment-lifespan-input', 'value'),
        Input('investment-efficiency-input', 'value'),
        Input('app-mode', 'value')],
        [State('financial-data-store', 'data')]
    )
    def update_metrics(months: Optional[int], budget: Optional[float], timeframe: Optional[int], 
                    investment_type: Optional[str], investment_rate: Optional[float], 
                    investment_lifespan: Optional[int], efficiency_impact: Optional[float], 
                    mode: Optional[str], stored_data: Optional[Dict[str, Any]]) -> Tuple[str, str, str, str]:
        """Update the financial metrics based on budget control."""
        # Default to sample data if no stored data with explicit typing
        # Handle None case explicitly for clearer type inference
        financial_data: Dict[str, Any]
        if stored_data is not None:
            financial_data = stored_data
        else:
            financial_data = cast(Dict[str, Any], local_get_sample_data())
        
        # Use timeframe for investment lifespan if available
        if timeframe:
            investment_lifespan = timeframe
        
        # Calculate projections with proper type handling for months
        df = local_project_financials(
            financial_data,
            months=months if months is not None else 60,  # Default to 60 months if None
            investment_amount=budget if budget is not None else 0.0,  # Handle None budget
            investment_type=investment_type,
            investment_rate=investment_rate if investment_rate is not None else 5.0,
            investment_lifespan=investment_lifespan if investment_lifespan is not None else 5,
            efficiency_impact=efficiency_impact if efficiency_impact is not None else 0
        )

        # Add explicit cast to ensure df is treated as DataFrame
        from typing import cast
        import pandas as pd
        df = cast(pd.DataFrame, df)
        
        # Format metrics based on mode
        if mode == 'business':
            current_metric = f"£{df['net_worth'].iloc[0]:,.2f}"
            projected_metric = f"£{df['net_worth'].iloc[-1]:,.2f}"
            current_flow = f"£{df['ebitda'].iloc[0]:,.2f}"
            projected_flow = f"£{df['ebitda'].iloc[-1]:,.2f}"
        else:
            current_metric = f"£{df['net_worth'].iloc[0]:,.2f}"
            projected_metric = f"£{df['net_worth'].iloc[-1]:,.2f}"
            current_flow = f"£{df['cash_flow'].iloc[0]:,.2f}"
            projected_flow = f"£{df['cash_flow'].iloc[-1]:,.2f}"
        
        return current_metric, projected_metric, current_flow, projected_flow

    # Callback to calculate and store financial data
    # This callback calculates financial data based on user inputs and stores it in the data store.
    # It processes income, assets, liabilities, and expenses data, calculates projections, and returns the financial data and projection results.
    # It also handles the case where no button clicks have occurred, returning sample data for initial load.
    # This logic has been migrated to shared/callbacks/__init__.py
    @app.callback(
        [Output('financial-data-store', 'data'),
        Output('projection-results-store', 'data')],
        [Input('calculate-button', 'n_clicks'),
        Input('app-mode', 'value')],
        [State('income-table', 'data'),
        State('assets-table', 'data'),
        State('liabilities-table', 'data'),
        State('expenses-table', 'data'),
        State('time-horizon-slider', 'value'),
        State('budget-slider', 'value'),  # Changed from investment-slider
        State('budget-timeframe', 'value'),  # Added new input
        State('investment-type-input', 'value'),
        State('investment-rate-input', 'value'),
        State('investment-lifespan-input', 'value'),
        State('investment-efficiency-input', 'value')]
    )
    def calculate_and_store_data(n_clicks: Optional[int], mode: Optional[str], 
                            income_data: Optional[List[Dict[str, Any]]], 
                            assets_data: Optional[List[Dict[str, Any]]], 
                            liabilities_data: Optional[List[Dict[str, Any]]], 
                            expenses_data: Optional[List[Dict[str, Any]]], 
                            months: Optional[int], budget: Optional[float], 
                            timeframe: Optional[int], investment_type: Optional[str], 
                            investment_rate: Optional[float], 
                            investment_lifespan: Optional[int], 
                            efficiency_impact: Optional[float]) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """Calculate and store financial data with enhanced budget parameters."""
        from typing import Any

        from typing import Dict, List
        projection_data: List[Dict[str, Any]]
        
        if n_clicks is None:
            # Return sample data for initial load based on mode
            effective_mode = mode if mode is not None else 'personal'  # Default to 'personal' if mode is None
            # Get sample data and explicitly cast to the expected type to resolve type checking issues
            from typing import cast, Optional, Dict
            untyped_sample_data = cast(Optional[Dict[str, Any]], local_get_sample_data(effective_mode))
            sample_data: Dict[str, Any] = {}
            if untyped_sample_data is not None:
                sample_data.update(untyped_sample_data)
            projection_result = local_project_financials(sample_data, months=60)
            # Handle both single DataFrame and tuple returns
            if isinstance(projection_result, tuple):
                projection_df = projection_result[0]
            else:
                projection_df = projection_result
            # Use a direct approach with explicit typing to avoid type checking issues
            from typing import Dict, List, Any, Iterator
            # Create a properly typed list with correct type annotation
            projection_data = []
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
                row_dict: Dict[str, Any] = {str(col): row_series[col] for col in projection_df.columns}
                # Now we don't need to cast since the type is already specified
                projection_data.append(row_dict)
            # Return directly without the unnecessary cast
            return sample_data, projection_data
        
        # Process the input data
        investments: List[Dict[str, Any]] = []
        savings: List[Dict[str, Any]] = []
        
        if assets_data:
            for item in assets_data:
                if item and item.get('return', 0) <= 2:  # Assuming low return items are savings
                    savings.append({
                        "name": item.get("name", ""),
                        "balance": item.get("value", 0),
                        "rate": item.get("return", 0),
                        "contribution": item.get("contribution", 0)
                    })
                else:
                    investments.append({
                        "name": item.get("name", ""),
                        "value": item.get("value", 0),
                        "return": item.get("return", 0),
                        "contribution": item.get("contribution", 0)
                    })
        
        financial_data = {
            "income": income_data if income_data else [],
            "savings": savings,
            "investments": investments,
            "debts": liabilities_data if liabilities_data else [],
            "spending": expenses_data if expenses_data else [],
        }
        
        # Calculate projections with the parsed financial data
        effective_months = months if months is not None else 60
        projection_result = local_project_financials(
            financial_data,
            months=effective_months,
            investment_amount=budget if budget is not None else 0,
            investment_type=investment_type,
            investment_rate=investment_rate if investment_rate is not None else 5.0,
            investment_lifespan=investment_lifespan if investment_lifespan is not None else 5,
            efficiency_impact=efficiency_impact if efficiency_impact is not None else 0
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
        raw_records: List[Dict[str, Any]] = projection_df.to_dict(orient='records')  # type: ignore
        # Create a properly typed list with correct type annotation
        projection_data = []
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
        Output('overview-chart', 'figure'),
        [Input('time-horizon-slider', 'value'),
        Input('budget-slider', 'value'),
        Input('budget-timeframe', 'value'),
        Input('investment-type-input', 'value'),
        Input('investment-rate-input', 'value'),
        Input('investment-lifespan-input', 'value'),
        Input('investment-efficiency-input', 'value'),
        Input('app-mode', 'value'),
        Input('show-impact-toggle', 'value')],
        [State('financial-data-store', 'data')]
    )

    def update_overview_chart(months: Optional[int], budget: Optional[float], timeframe: Optional[int], 
                            investment_type: Optional[str], investment_rate: Optional[float], 
                            investment_lifespan: Optional[int], efficiency_impact: Optional[float], 
                            mode: Optional[str], show_impact: Optional[List[str]], 
                            stored_data: Optional[Dict[str, Any]]) -> 'Figure':
        """Update the overview chart based on budget control."""
        # Default to sample data if no stored data with explicit typing
        # Import typing utilities locally to ensure they're available
        from typing import Dict, Any, cast

        import pandas as pd
        
        # Handle stored_data more explicitly for type checking
        from typing import Dict, Any, cast
        
        if stored_data is not None:
            # Convert to Dict[str, Any] with explicit cast
            financial_data = cast(Dict[str, Any], dict(stored_data))
        else:
            # Create sample data with explicit typing and casting
            sample_data = local_get_sample_data()
            financial_data = cast(Dict[str, Any], dict(sample_data))
                
        # Handle possible None values for months
        if months is None:
            months = timeframe * 12 if timeframe else 60
        
        # Use timeframe for investment lifespan if available
        if timeframe:
            investment_lifespan = timeframe
        
        # Determine if we should show impact
        show_impact_flag = show_impact and len(show_impact) > 0 and 'show' in show_impact
        
        # Handle None budget value
        if budget is None:
            budget = 0.0

        # Define helper function inside this function
        def get_expense_column(df: pd.DataFrame) -> "pd.Series[float]":
            """Helper function to find an appropriate expense column or create a fallback."""
            import pandas as pd
            
            # Try to find an expense-related column
            expense_columns = ['operating_expenses', 'expenses', 'total_expenses', 'spending']
            
            for col in expense_columns:
                if col in df.columns:
                    return df[col].astype(float)
            
            # If no expense columns exist, try to derive it from other columns
            if 'revenue' in df.columns and 'ebitda' in df.columns:
                # Estimate expenses as revenue minus EBITDA
                return (df['revenue'] - df['ebitda']).astype(float)
            elif 'revenue' in df.columns and 'net_income' in df.columns:
                # Estimate expenses as revenue minus net income
                return (df['revenue'] - df['net_income']).astype(float)
            
            # Last resort, return a series of zeros
            print("Warning: No expense columns found and couldn't derive expenses. Using zeros instead.")
            return pd.Series([0.0] * len(df), index=df.index, dtype=float)
        
        # Calculate projections with budget
        if show_impact_flag and budget > 0:
            projection_result = local_project_financials(
                financial_data,
                months=months,
                investment_amount=budget,
                investment_type=investment_type,
                investment_rate=investment_rate if investment_rate is not None else 5.0,
                investment_lifespan=investment_lifespan if investment_lifespan is not None else 5,
                efficiency_impact=efficiency_impact if efficiency_impact is not None else 0,
                calculate_baseline=True
            )
            # Handle both single DataFrame and tuple returns
            if isinstance(projection_result, tuple):
                df, baseline_df = projection_result
            else:
                df = projection_result
                baseline_df = None
        else:
            projection_result = local_project_financials(
                financial_data,
                months=months,
                investment_amount=budget,
                investment_type=investment_type,
                investment_rate=investment_rate if investment_rate is not None else 5.0,
                investment_lifespan=investment_lifespan if investment_lifespan is not None else 5,
                efficiency_impact=efficiency_impact if efficiency_impact is not None else 0
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
        if mode == 'business':
            metric_name = 'Departmental Savings'
            # Add trace directly to avoid type issues
            fig.add_trace(go.Scatter(  # type: ignore
                x=df['date'], 
                y=df['cash_flow'], 
                name=f'{metric_name} (with Investment)' if show_impact_flag and budget > 0 else metric_name,
                line=dict(color='#1f77b4', width=2)
            ))
        else:
            metric_name = 'Monthly Cash Flow'
            fig.add_trace(go.Scatter(  # type: ignore
                x=df['date'], 
                y=df['cash_flow'], 
                name=f'{metric_name} (with Investment)' if show_impact_flag and budget > 0 else metric_name,
                line=dict(color='#1f77b4', width=2)
            ))
        
        # Add Departmental Spending using the helper function
        departmental_spending = get_expense_column(df)
        fig.add_trace(go.Scatter(  # type: ignore
            x=df['date'], 
            y=departmental_spending, 
            name='Dept. Spending (with Investment)' if show_impact_flag and budget > 0 else 'Dept. Spending',
            line=dict(color='#d62728', width=2)
        ))
        
        # Add baseline for comparison if showing impact
        if show_impact_flag and budget > 0 and baseline_df is not None:
            # Add baseline Monthly Savings
            fig.add_trace(go.Scatter(  # type: ignore
                x=baseline_df['date'], 
                y=baseline_df['cash_flow'], 
                name=f'{metric_name} (without Investment)',
                line=dict(color='#1f77b4', width=2, dash='dash')
            ))
            
            # Add baseline Departmental Spending
            baseline_spending = get_expense_column(baseline_df)
            fig.add_trace(go.Scatter(  # type: ignore
                x=baseline_df['date'], 
                y=baseline_spending, 
                name='Dept. Spending (without Investment)',
                line=dict(color='#d62728', width=2, dash='dash')
            ))
        
        # Update layout with proper typing
        from typing import cast, Any
        cast(Any, fig).update_layout(
            title="Financial Projections",
            xaxis_title="Date",
            yaxis_title="Amount (£)",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            hovermode="x unified"
        )
        
        return fig