# components/charts.py
from dash import html, dcc
import plotly.graph_objs as go
import plotly.express as px
import dash_bootstrap_components as dbc
import pandas as pd

def create_chart_section():
    """Create the chart section of the application."""
    return html.Div([
        html.H2("Financial Projections"),
        
        # Chart controls
        html.Div([
            html.Label("Projection Horizon (months):"),
            dcc.Slider(
                id='time-horizon-slider',
                min=6,
                max=300,
                step=6,
                value=60,
                marks={i: str(i) for i in range(0, 301, 60)},
                tooltip={"placement": "bottom", "always_visible": True}
            ),
            
            html.Label("Investment Amount (£):"),
            dcc.Slider(
                id='investment-amount-slider',
                min=0,
                max=50000,
                step=1000,
                value=0,
                marks={i: f"£{i:,}" for i in range(0, 50001, 10000)},
                tooltip={"placement": "bottom", "always_visible": True}
            )
        ], className="control-panel"),
        
        # Charts container
        dbc.Row([
            dbc.Col([
                html.Div([
                    html.H4("Net Worth Projection"),
                    dcc.Graph(id='net-worth-chart')
                ], className="chart-container")
            ], width=12),
            
            dbc.Col([
                html.Div([
                    html.H4("Cash Flow Projection"),
                    dcc.Graph(id='cash-flow-chart')
                ], className="chart-container")
            ], width=6),
            
            dbc.Col([
                html.Div([
                    html.H4("Asset Allocation"),
                    dcc.Graph(id='allocation-chart')
                ], className="chart-container")
            ], width=6)
        ])
    ])

def create_net_worth_chart(df, mode='department'):
    """Create equity projection chart."""
    fig = go.Figure()
    
    # Use business terminology
    chart_title = 'Equity Projection' if mode in ['department', 'enterprise'] else 'Net Worth Projection'
    y_axis_title = 'Amount (£)'
    
    # Adjust labels based on mode
    net_worth_label = "Shareholders' Equity" if mode in ['department', 'enterprise'] else 'Net Worth'
    
    fig.add_trace(go.Scatter(
        x=df['date'], 
        y=df['net_worth'], 
        name=net_worth_label,
        line=dict(color='#1f77b4', width=3)
    ))
    
    fig.add_trace(go.Scatter(
        x=df['date'], 
        y=df['assets'], 
        name='Assets',
        line=dict(color='#2ca02c', width=2)
    ))
    
    fig.add_trace(go.Scatter(
        x=df['date'], 
        y=df['liabilities'], 
        name='Liabilities',
        line=dict(color='#d62728', width=2)
    ))
    
    fig.update_layout(
        title=chart_title,
        xaxis_title='Date',
        yaxis_title=y_axis_title,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode="x unified"
    )
    
    # Add range selector
    fig.update_xaxes(
        rangeslider_visible=True,
        rangeselector=dict(
            buttons=list([
                dict(count=1, label="1m", step="month", stepmode="backward"),
                dict(count=6, label="6m", step="month", stepmode="backward"),
                dict(count=1, label="YTD", step="year", stepmode="todate"),
                dict(count=1, label="1y", step="year", stepmode="backward"),
                dict(step="all")
            ])
        )
    )
    
    return fig

def create_cash_flow_chart(df):
    """Create cash flow projection chart."""
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=df['date'], 
        y=df['cash_flow'],
        name='Monthly Cash Flow',
        marker_color='#1f77b4'
    ))
    
    fig.update_layout(
        title='Cash Flow Projection',
        xaxis_title='Date',
        yaxis_title='Amount (£)',
        hovermode="x unified"
    )
    
    return fig

def create_allocation_chart(financial_data):
    """Create an asset allocation pie chart."""
    # Extract asset values
    assets = {}
    for item in financial_data.get('investments', []) + financial_data.get('savings', []):
        name = item.get('name', '')
        value = item.get('value', 0) if 'value' in item else item.get('balance', 0)
        assets[name] = value
    
    # Create pie chart
    fig = go.Figure(data=[go.Pie(
        labels=list(assets.keys()),
        values=list(assets.values()),
        hole=.3,
        textinfo='label+percent',
        insidetextorientation='radial'
    )])
    
    fig.update_layout(title='Asset Allocation')
    
    return fig

def register_chart_callbacks(app):
    """Register callbacks for chart components."""
    from dash.dependencies import Input, Output, State
    from dash import dcc
    import json
    from modules.financial_dashboard.models.projections import project_financials
    from shared.io import get_sample_data
    
    @app.callback(
        [Output('net-worth-chart', 'figure'),
         Output('cash-flow-chart', 'figure'),
         Output('allocation-chart', 'figure')],
        [Input('calculate-button', 'n_clicks'),
         Input('time-horizon-slider', 'value'),
         Input('investment-amount-slider', 'value')],
        [State('income-table', 'data'),
         State('assets-table', 'data'),
         State('liabilities-table', 'data'),
         State('expenses-table', 'data')],
        prevent_initial_call=True
    )
    def update_charts(n_clicks, months, investment, income_data, assets_data, liabilities_data, expenses_data):
        # If not triggered by calculate button, use sample data for initial load
        financial_data = {
            "income": income_data if income_data else [],
            "investments": [item for item in assets_data if item] if assets_data else [],
            "debts": liabilities_data if liabilities_data else [],
            "spending": expenses_data if expenses_data else [],
            "savings": []  # We'll populate this from assets that are savings
        }
        
        # Separate investments and savings
        if assets_data:
            for item in assets_data:
                if item and item.get('return', 0) <= 2:  # Assuming low return items are savings
                    financial_data["savings"].append(item)
                    financial_data["investments"].remove(item)
        
        # Calculate projections
        df = project_financials(financial_data, months=months, investment_amount=investment)
        
        # Create charts
        net_worth_fig = create_net_worth_chart(df)
        cash_flow_fig = create_cash_flow_chart(df)
        allocation_fig = create_allocation_chart(financial_data)
        
        return net_worth_fig, cash_flow_fig, allocation_fig