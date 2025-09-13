"""
Component for investment optimization and timeline analysis.
"""
from dash import html, dcc, dash_table, callback
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
import plotly.graph_objs as go
import plotly.express as px
import pandas as pd
import numpy as np

def create_investment_optimizer_section():
    """
    Create the investment optimizer section for the application.
    
    Returns:
        html.Div: The investment optimizer component
    """
    return html.Div([
        html.H2("Investment Optimization", className="mb-3"),
        
        # Investment portfolio builder
        html.Div([
            html.H4("Build Your Investment Portfolio", className="mb-3"),
            
            # Investment input form
            dbc.Row([
                dbc.Col([
                    html.Label("Investment Name:"),
                    dbc.Input(
                        id="investment-name-input",
                        type="text",
                        placeholder="e.g., New Equipment, Stock Purchase",
                        value="Investment 1"
                    ),
                ], width=6),
                
                dbc.Col([
                    html.Label("Investment Type:"),
                    dcc.Dropdown(
                        id="investment-type-input",
                        options=[
                            {'label': 'Cash/Working Capital', 'value': 'cash'},
                            {'label': 'Equipment/Machinery', 'value': 'equipment'},
                            {'label': 'Property/Facilities', 'value': 'property'},
                            {'label': 'Research & Development', 'value': 'rd'},
                            {'label': 'Marketing/Brand', 'value': 'marketing'},
                            {'label': 'IT/Software', 'value': 'it'},
                            {'label': 'Training/Human Capital', 'value': 'training'},
                            {'label': 'New Staff Onboarding', 'value': 'staffing'},
                            {'label': 'Stocks', 'value': 'stocks'},
                            {'label': 'Cryptocurrency', 'value': 'crypto'},
                            {'label': 'Bonds', 'value': 'bonds'},
                            {'label': 'Real Estate', 'value': 'realestate'}
                        ],
                        value="cash"
                    ),
                ], width=6)
            ], className="mb-3"),
            
            dbc.Row([
                dbc.Col([
                    html.Label("Investment Amount (£):"),
                    dbc.Input(
                        id="investment-amount-input",
                        type="number",
                        min=0,
                        step=1000,
                        value=10000
                    ),
                ], width=4),
                
                dbc.Col([
                    html.Label("Expected Return/Growth Rate (%):"),
                    dbc.Input(
                        id="investment-rate-input",
                        type="number",
                        min=-100,
                        max=1000,
                        step=0.1,
                        value=5.0
                    ),
                ], width=4),
                
                dbc.Col([
                    html.Label("Investment Timeframe (months):"),
                    dbc.Input(
                        id="investment-timeframe-input",
                        type="number",
                        min=1,
                        max=600,
                        step=1,
                        value=60
                    ),
                ], width=4),
            ], className="mb-3"),
            
            # Advanced parameters section (initially collapsed)
            dbc.Collapse(
                dbc.Card(
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                html.Label("Asset Lifespan (years):"),
                                dbc.Input(
                                    id="investment-lifespan-input",
                                    type="number",
                                    min=1,
                                    max=50,
                                    step=1,
                                    value=10
                                ),
                            ], width=4),
                            
                            dbc.Col([
                                html.Label("Risk Level (1-10):"),
                                dbc.Input(
                                    id="investment-risk-input",
                                    type="number",
                                    min=1,
                                    max=10,
                                    step=1,
                                    value=5
                                ),
                            ], width=4),
                            
                            dbc.Col([
                                html.Label("Liquidity (1-10):"),
                                dbc.Input(
                                    id="investment-liquidity-input",
                                    type="number",
                                    min=1,
                                    max=10,
                                    step=1,
                                    value=5
                                ),
                            ], width=4),
                        ], className="mb-3"),
                        
                        dbc.Row([
                            dbc.Col([
                                html.Label("Initial Cost (£):"),
                                dbc.Input(
                                    id="initial-cost-input",
                                    type="number",
                                    min=0,
                                    step=100,
                                    value=0
                                ),
                            ], width=4),
                            
                            dbc.Col([
                                html.Label("Recurring Costs (£/month):"),
                                dbc.Input(
                                    id="recurring-cost-input",
                                    type="number",
                                    min=0,
                                    step=10,
                                    value=0
                                ),
                            ], width=4),
                            
                            dbc.Col([
                                html.Label("Tax Rate (%):"),
                                dbc.Input(
                                    id="tax-rate-input",
                                    type="number",
                                    min=0,
                                    max=100,
                                    step=1,
                                    value=20
                                ),
                            ], width=4),
                        ]),
                        
                        # Scenario parameters
                        html.H5("Scenario Parameters", className="mt-3"),
                        dbc.Row([
                            dbc.Col([
                                html.Label("Performance in Economic Downturn (%):"),
                                dbc.Input(
                                    id="downturn-performance-input",
                                    type="number",
                                    min=-100,
                                    max=100,
                                    step=0.1,
                                    value=-10
                                ),
                            ], width=6),
                            
                            dbc.Col([
                                html.Label("Performance in Economic Boom (%):"),
                                dbc.Input(
                                    id="boom-performance-input",
                                    type="number",
                                    min=-100,
                                    max=1000,
                                    step=0.1,
                                    value=15
                                ),
                            ], width=6),
                        ]),
                    ])
                ),
                id="advanced-parameters-collapse",
                is_open=False,
            ),
            
            # Toggle for advanced parameters
            dbc.Button(
                "Advanced Parameters",
                id="advanced-parameters-toggle",
                className="mb-3 mt-2",
                color="secondary"
            ),
            
            # Add investment button
            dbc.Button(
                "Add to Investment Portfolio",
                id="add-investment-button",
                color="primary",
                className="mt-2 mb-4"
            ),

            # OEE Parameters section - add directly after the Add Investment button
            html.Div([
                html.H5("OEE Improvement Parameters", className="mb-3 mt-4"),
                dbc.Row([
                    dbc.Col([
                        html.Label("Availability Improvement (%):"),
                        dbc.Input(
                            id="availability-input",
                            type="number",
                            placeholder="0-100",
                            min=0,
                            max=100,
                            step=1,
                            value=0
                        )
                    ], width=4),
                    
                    dbc.Col([
                        html.Label("Performance Improvement (%):"),
                        dbc.Input(
                            id="performance-input",
                            type="number",
                            placeholder="0-100",
                            min=0,
                            max=100,
                            step=1,
                            value=0
                        )
                    ], width=4),
                    
                    dbc.Col([
                        html.Label("Quality Improvement (%):"),
                        dbc.Input(
                            id="quality-input",
                            type="number",
                            placeholder="0-100",
                            min=0,
                            max=100,
                            step=1,
                            value=0
                        )
                    ], width=4),
                ]),
            ], id="oee-container", style={"display": "none"}),  # Hidden by default

            # Staffing Parameters section - add after the OEE container  
            html.Div([
                html.H5("Staffing Parameters", className="mb-3 mt-4"),
                dbc.Row([
                    dbc.Col([
                        html.Label("Staff Count:"),
                        dbc.Input(
                            id="staff-count-input",
                            type="number",
                            placeholder="Number of staff",
                            min=1,
                            step=1,
                            value=1
                        )
                    ], width=4),
                    
                    dbc.Col([
                        html.Label("Ramp-Up Period (months):"),
                        dbc.Input(
                            id="ramp-up-input",
                            type="number",
                            placeholder="Months",
                            min=1,
                            max=24,
                            step=1,
                            value=3
                        )
                    ], width=4),
                    
                    dbc.Col([
                        html.Label("Training Cost per Staff (£):"),
                        dbc.Input(
                            id="training-cost-input",
                            type="number",
                            placeholder="Cost",
                            min=0,
                            step=100,
                            value=2000
                        )
                    ], width=4),
                ]),
            ], id="staffing-container", style={"display": "none"}),  # Hidden by default

            # Show Impact toggle - add after the staffing container
            dbc.Row([
                dbc.Col([
                    html.Label("Investment Impact:"),
                    dbc.Checklist(
                        id="show-impact-toggle",
                        options=[{"label": "Show Investment Impact", "value": "show"}],
                        value=["show"],  # Default to showing impact
                        switch=True
                    )
                ], width=12),
            ], className="mb-3"),

            # This is the closing bracket for the overall container
            ], className="border p-3 rounded mb-4"),
        
        # Results section
        html.Div([
            html.H4("Investment Comparison Results", className="mb-3"),
            
            # Results will be displayed here
            html.Div(id="investment-comparison-results"),
            
            # Timeline visualization
            html.Div([
                html.H4("Optimal Investment Timeline", className="mt-4"),
                html.Div(id="optimal-timeline-container")
            ], id="timeline-section", style={"display": "none"}),
            
            # Report generation section
            html.Div([
                html.H4("Investment Report", className="mt-4"),
                dbc.Button(
                    "Generate Detailed Report",
                    id="generate-report-button",
                    color="primary",
                    className="mt-2"
                ),
                html.Div(id="investment-report-container", className="mt-3")
            ], id="report-section", style={"display": "none"}),
        ], id="results-section", style={"display": "none"}),
        
        # Store for investment portfolio data
        dcc.Store(id="investment-portfolio-store", data=[]),
        
        # Store for investment comparison results
        dcc.Store(id="investment-comparison-results-store", data={}),
        
        # Store for optimal timeline data
        dcc.Store(id="optimal-timeline-store", data={}),
    ])

def register_investment_optimizer_callbacks(app):
    """
    Register callbacks for the investment optimizer component.
    
    Args:
        app: The Dash application instance
    """
    @app.callback(
        Output("advanced-parameters-collapse", "is_open"),
        [Input("advanced-parameters-toggle", "n_clicks")],
        [State("advanced-parameters-collapse", "is_open")],
    )
    def toggle_advanced_parameters(n_clicks, is_open):
        if n_clicks:
            return not is_open
        return is_open
    
    @app.callback(
        Output("investment-portfolio-store", "data"),
        Output("investments-table", "data", allow_duplicate=True),
        Input("add-investment-button", "n_clicks"),
        State("investment-name-input", "value"),
        State("investment-type-input", "value"),
        State("investment-amount-input", "value"),
        State("investment-rate-input", "value"),
        State("investment-timeframe-input", "value"),
        State("investment-portfolio-store", "data"),
        # Advanced parameters
        State("investment-lifespan-input", "value"),
        State("investment-risk-input", "value"),
        State("investment-liquidity-input", "value"),
        State("initial-cost-input", "value"),
        State("recurring-cost-input", "value"),
        State("tax-rate-input", "value"),
        State("downturn-performance-input", "value"),
        State("boom-performance-input", "value"),
        prevent_initial_call=True
    )
    def add_investment_to_portfolio(n_clicks, name, inv_type, amount, rate, timeframe,
                                   portfolio, lifespan, risk, liquidity, initial_cost,
                                   recurring_cost, tax_rate, downturn_perf, boom_perf):
        if not n_clicks:
            return portfolio, []
        
        # Create new investment entry
        new_investment = {
            "id": f"investment_{len(portfolio) + 1}",
            "name": name,
            "type": inv_type,
            "amount": amount,
            "rate": rate,
            "timeframe": timeframe,
            "lifespan": lifespan,
            "risk": risk,
            "liquidity": liquidity,
            "initial_cost": initial_cost,
            "recurring_cost": recurring_cost,
            "tax_rate": tax_rate,
            "downturn_performance": downturn_perf,
            "boom_performance": boom_perf
        }
        
        # Add to portfolio
        updated_portfolio = portfolio + [new_investment]
        
        # Create table data
        table_data = []
        for i, inv in enumerate(updated_portfolio):
            table_data.append({
                "name": inv["name"],
                "type": inv["type"],
                "amount": inv["amount"],
                "rate": inv["rate"],
                "timeframe": inv["timeframe"],
                "remove": f"<button class='btn btn-danger btn-sm' id='remove-investment-{i}'>Remove</button>"
            })
        
        return updated_portfolio, table_data
    
    @app.callback(
        Output("results-section", "style"),
        Output("investment-comparison-results", "children"),
        Input("run-investment-comparison-button", "n_clicks"),
        State("investment-portfolio-store", "data"),
        prevent_initial_call=True
    )
    def run_investment_comparison(n_clicks, portfolio):
        if not n_clicks or not portfolio:
            return {"display": "none"}, []
        
        # Create comparison charts and analysis
        return {"display": "block"}, [
            html.Div([
                html.H5("ROI Comparison"),
                dcc.Graph(
                    figure=create_roi_comparison_chart(portfolio),
                    id="roi-comparison-chart"
                )
            ]),
            
            html.Div([
                html.H5("Investment Growth Over Time", className="mt-4"),
                dcc.Graph(
                    figure=create_growth_comparison_chart(portfolio),
                    id="growth-comparison-chart"
                )
            ]),
            
            html.Div([
                html.H5("Risk vs. Return Analysis", className="mt-4"),
                dcc.Graph(
                    figure=create_risk_return_chart(portfolio),
                    id="risk-return-chart"
                )
            ]),
            
            # Investment metrics table
            html.Div([
                html.H5("Investment Metrics", className="mt-4"),
                dash_table.DataTable(
                    id='investment-metrics-table',
                    columns=[
                        {"name": "Investment", "id": "name"},
                        {"name": "ROI (%)", "id": "roi", "type": "numeric", "format": {"specifier": ".2f"}},
                        {"name": "IRR (%)", "id": "irr", "type": "numeric", "format": {"specifier": ".2f"}},
                        {"name": "Payback (months)", "id": "payback", "type": "numeric", "format": {"specifier": ".1f"}},
                        {"name": "Final Value (£)", "id": "final_value", "type": "numeric", "format": {"specifier": ",.2f"}},
                        {"name": "Risk Score", "id": "risk_score", "type": "numeric", "format": {"specifier": ".1f"}}
                    ],
                    data=calculate_investment_metrics(portfolio),
                    style_cell={'textAlign': 'left', 'padding': '10px'},
                    style_header={
                        'backgroundColor': 'rgb(230, 230, 230)',
                        'fontWeight': 'bold'
                    },
                    style_table={'overflowX': 'auto'},
                    sort_action='native'
                ),
            ]),
            
            # Recommendation box
            html.Div([
                html.H5("Investment Recommendations", className="mt-4"),
                html.Div(
                    generate_investment_recommendations(portfolio),
                    id="investment-recommendations",
                    className="border p-3 rounded"
                )
            ]),
            
            # Show timeline section button
            html.Div([
                dbc.Button(
                    "Show Optimal Timeline Analysis",
                    id="show-timeline-button",
                    color="primary",
                    className="mt-4"
                ),
            ]),
        ]
    
    @app.callback(
        Output("timeline-section", "style"),
        Output("optimal-timeline-container", "children"),
        Input("show-timeline-button", "n_clicks"),
        State("investment-portfolio-store", "data"),
        prevent_initial_call=True
    )
    def show_optimal_timeline(n_clicks, portfolio):
        if not n_clicks or not portfolio:
            return {"display": "none"}, []
        
        # Generate timeline visualization
        return {"display": "block"}, [
            html.P("This timeline shows the optimal sequence and timing for your investments based on their characteristics and projected performance:"),
            dcc.Graph(
                figure=create_optimal_timeline_chart(portfolio),
                id="optimal-timeline-chart"
            ),
            html.Div([
                html.H5("Timeline Recommendations", className="mt-3"),
                html.Div(
                    generate_timeline_recommendations(portfolio),
                    id="timeline-recommendations",
                    className="border p-3 rounded mt-2"
                )
            ]),
            # Enable report generation
            html.Div([
                dbc.Button(
                    "Generate Investment Report",
                    id="show-report-button",
                    color="success",
                    className="mt-3"
                ),
            ]),
        ]
    
    @app.callback(
        Output("report-section", "style"),
        Output("investment-report-container", "children"),
        Input("show-report-button", "n_clicks"),
        State("investment-portfolio-store", "data"),
        prevent_initial_call=True
    )
    def show_investment_report(n_clicks, portfolio):
        if not n_clicks or not portfolio:
            return {"display": "none"}, []
        
        # Generate report
        return {"display": "block"}, generate_investment_report(portfolio)

# Helper functions for creating charts and analysis
def create_roi_comparison_chart(portfolio):
    """Create a bar chart comparing ROI across investments."""
    names = [inv["name"] for inv in portfolio]
    # Simple ROI calculation
    rois = [inv["rate"] for inv in portfolio]
    
    fig = go.Figure(data=[
        go.Bar(
            x=names,
            y=rois,
            text=[f"{roi:.2f}%" for roi in rois],
            textposition='auto',
            marker_color='rgb(55, 83, 109)'
        )
    ])
    
    fig.update_layout(
        title="Return on Investment (ROI) Comparison",
        xaxis_title="Investment",
        yaxis_title="ROI (%)",
        template="plotly_white"
    )
    
    return fig

def create_growth_comparison_chart(portfolio):
    """Create line charts showing growth over time for each investment."""
    fig = go.Figure()
    
    for inv in portfolio:
        # Simple compound growth calculation
        months = list(range(0, inv["timeframe"] + 1))
        values = [inv["amount"] * (1 + inv["rate"]/100/12) ** month for month in months]
        
        fig.add_trace(go.Scatter(
            x=months,
            y=values,
            mode='lines',
            name=inv["name"]
        ))
    
    fig.update_layout(
        title="Investment Growth Over Time",
        xaxis_title="Months",
        yaxis_title="Value (£)",
        template="plotly_white"
    )
    
    return fig

def create_risk_return_chart(portfolio):
    """Create a scatter plot of risk vs. return."""
    names = [inv["name"] for inv in portfolio]
    risks = [inv.get("risk", 5) for inv in portfolio]  # Default to 5 if not specified
    returns = [inv["rate"] for inv in portfolio]
    sizes = [inv["amount"] / 1000 for inv in portfolio]  # Size proportional to investment amount
    
    fig = go.Figure(data=[
        go.Scatter(
            x=risks,
            y=returns,
            mode='markers+text',
            marker=dict(
                size=sizes,
                sizemode='area',
                sizeref=2.*max(sizes)/(40.**2),
                color=risks,
                colorscale='Viridis',
                showscale=True,
                colorbar=dict(title="Risk Score")
            ),
            text=names,
            textposition="top center"
        )
    ])
    
    fig.update_layout(
        title="Risk vs. Return Analysis",
        xaxis_title="Risk Score (1-10)",
        yaxis_title="Expected Return (%)",
        template="plotly_white"
    )
    
    return fig

def calculate_investment_metrics(portfolio):
    """Calculate various investment metrics for comparison."""
    metrics = []
    
    for inv in portfolio:
        # Calculate ROI (simple)
        roi = inv["rate"]
        
        # Calculate Internal Rate of Return (simplified)
        # In a real implementation, use numpy's IRR function with proper cash flows
        monthly_rate = inv["rate"] / 100 / 12
        irr = ((1 + monthly_rate) ** 12 - 1) * 100
        
        # Calculate payback period (simplified)
        if inv["rate"] > 0:
            payback = 100 / (inv["rate"] / 12)  # months to recover 100%
        else:
            payback = float('inf')
        
        # Calculate final value
        final_value = inv["amount"] * (1 + inv["rate"]/100/12) ** inv["timeframe"]
        
        # Risk score is either provided or default to 5
        risk_score = inv.get("risk", 5)
        
        metrics.append({
            "name": inv["name"],
            "roi": roi,
            "irr": irr,
            "payback": payback,
            "final_value": final_value,
            "risk_score": risk_score
        })
    
    return metrics

def generate_investment_recommendations(portfolio):
    """Generate investment recommendations based on the portfolio."""
    # Find best performing investment (by ROI)
    best_roi_inv = max(portfolio, key=lambda x: x["rate"])
    
    # Find lowest risk investment
    lowest_risk_inv = min(portfolio, key=lambda x: x.get("risk", 5))
    
    # Find best risk-adjusted return (simple Sharpe ratio analog)
    best_risk_adjusted = max(portfolio, key=lambda x: x["rate"] / x.get("risk", 5) if x.get("risk", 5) > 0 else 0)
    
    return html.Div([
        html.P([
            html.Strong("Highest Return: "),
            f"{best_roi_inv['name']} with an expected return of {best_roi_inv['rate']}%"
        ]),
        html.P([
            html.Strong("Lowest Risk: "),
            f"{lowest_risk_inv['name']} with a risk score of {lowest_risk_inv.get('risk', 5)}/10"
        ]),
        html.P([
            html.Strong("Best Risk-Adjusted Return: "),
            f"{best_risk_adjusted['name']} balances return and risk effectively"
        ]),
        html.P([
            html.Strong("Recommendation: "),
            "Consider diversifying your investment portfolio across these options to optimize " +
            "return while managing risk. The optimal timeline analysis will provide more detailed guidance."
        ]),
    ])

def create_optimal_timeline_chart(portfolio):
    """Create a Gantt chart showing optimal investment timing."""
    # Sort investments by some optimization criteria (simplified here)
    # In a real implementation, use a more sophisticated algorithm
    sorted_portfolio = sorted(portfolio, key=lambda x: -x["rate"])
    
    # Assign start times based on investment characteristics
    # This is a simplified approach - a real implementation would use optimization
    start_times = []
    current_start = 0
    
    for inv in sorted_portfolio:
        # Higher return investments start sooner
        start_times.append(current_start)
        # Stagger start times based on investment characteristics
        current_start += max(1, min(6, int(10 / (inv["rate"] + 1))))
    
    fig = go.Figure()
    
    # Add investment timeline bars
    for i, inv in enumerate(sorted_portfolio):
        fig.add_trace(go.Bar(
            y=[inv["name"]],
            x=[inv["timeframe"]],
            base=[start_times[i]],
            orientation='h',
            name=inv["name"],
            hoverinfo="text",
            hovertext=[
                f"Name: {inv['name']}<br>" +
                f"Type: {inv['type']}<br>" +
                f"Amount: £{inv['amount']:,.2f}<br>" +
                f"Return: {inv['rate']}%<br>" +
                f"Start: Month {start_times[i]}<br>" +
                f"Duration: {inv['timeframe']} months"
            ]
        ))
    
    fig.update_layout(
        title="Optimal Investment Timeline",
        xaxis_title="Months",
        yaxis_title="Investment",
        barmode='overlay',
        template="plotly_white",
        height=400,
        showlegend=False
    )
    
    return fig

def generate_timeline_recommendations(portfolio):
    """Generate recommendations for investment timing."""
    return html.Div([
        html.P([
            "Based on the analysis of your investment portfolio, we recommend the following implementation timeline:"
        ]),
        html.Ul([
            html.Li([
                html.Strong("Short-term investments (0-6 months): "),
                "Focus on high-liquidity options with moderate returns to build a foundation."
            ]),
            html.Li([
                html.Strong("Medium-term investments (6-24 months): "),
                "Introduce higher-return investments once initial returns are realized from short-term investments."
            ]),
            html.Li([
                html.Strong("Long-term investments (24+ months): "),
                "Allocate remaining capital to longer-timeframe investments with potentially higher returns."
            ]),
        ]),
        html.P([
            "This staggered approach allows you to:",
            html.Ul([
                html.Li("Capitalize on compounding returns"),
                html.Li("Maintain sufficient liquidity"),
                html.Li("Adjust strategy based on initial performance"),
                html.Li("Optimize overall portfolio return")
            ])
        ]),
    ])

def generate_investment_report(portfolio):
    """Generate a comprehensive investment report."""
    # This would be expanded significantly in a real implementation
    metrics = calculate_investment_metrics(portfolio)
    
    # Find best performing investment
    best_inv = max(metrics, key=lambda x: x["roi"])
    
    return html.Div([
        html.H4("Investment Analysis Report"),
        
        html.Div([
            html.H5("Executive Summary"),
            html.P([
                f"This report analyzes {len(portfolio)} investments with a total value of ",
                html.Strong(f"£{sum(inv['amount'] for inv in portfolio):,.2f}"),
                ". The portfolio has an average expected return of ",
                html.Strong(f"{sum(inv['rate'] for inv in portfolio)/len(portfolio):.2f}%"),
                " with the highest performing investment being ",
                html.Strong(f"{best_inv['name']}"),
                f" (ROI: {best_inv['roi']:.2f}%)."
            ]),
        ], className="border p-3 rounded mb-3"),
        
        html.Div([
            html.H5("Key Performance Metrics"),
            dash_table.DataTable(
                columns=[
                    {"name": "Metric", "id": "metric"},
                    {"name": "Value", "id": "value"}
                ],
                data=[
                    {"metric": "Total Investment", "value": f"£{sum(inv['amount'] for inv in portfolio):,.2f}"},
                    {"metric": "Average ROI", "value": f"{sum(inv['rate'] for inv in portfolio)/len(portfolio):.2f}%"},
                    {"metric": "Average Risk Score", "value": f"{sum(inv.get('risk', 5) for inv in portfolio)/len(portfolio):.1f}/10"},
                    {"metric": "Projected Final Value", "value": f"£{sum(m['final_value'] for m in metrics):,.2f}"},
                    {"metric": "Average Payback Period", "value": f"{sum(m['payback'] for m in metrics)/len(metrics):.1f} months"}
                ],
                style_cell={'textAlign': 'left', 'padding': '10px'},
                style_header={
                    'backgroundColor': 'rgb(230, 230, 230)',
                    'fontWeight': 'bold'
                },
            ),
        ], className="mb-3"),
        
        html.Div([
            html.H5("Recommended Action Plan"),
            html.P([
                "Based on our analysis, we recommend the following actions:"
            ]),
            html.Ol([
                html.Li(f"Proceed with {best_inv['name']} as your primary investment"),
                html.Li("Follow the optimal timeline for remaining investments"),
                html.Li("Review and rebalance your portfolio quarterly"),
                html.Li("Consider adding more diverse investments to reduce overall risk")
            ]),
        ], className="border p-3 rounded mb-3"),
        
        dbc.Button("Download Full Report (PDF)", id="download-report-button", color="success", className="mt-2"),
    ])