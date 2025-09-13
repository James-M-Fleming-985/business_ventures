#!/usr/bin/env python3
"""
Investment Management Tab Implementation
Shows table of available investments with calculations based on uploaded data
"""

from dash import html, dash_table, dcc, Input, Output, State, callback
import dash_bootstrap_components as dbc
import pandas as pd
from investment_calculations import calculate_investment_savings


def create_investment_management_tab():
    """Create the investment management tab with table and calculations."""
    return html.Div([
        html.H3("Investment Management"),
        html.P("Manage and analyze your investments using uploaded data."),

        # Investment Summary Cards
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4("0", id="total-investments-count"),
                        html.P("Total Investments", className="text-muted")
                    ])
                ], color="primary", outline=True)
            ], width=3),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4("£0", id="total-potential-savings"),
                        html.P("Total Potential Savings",
                               className="text-muted")
                    ])
                ], color="success", outline=True)
            ], width=3),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4("£0", id="total-investment-cost"),
                        html.P("Total Investment Cost", className="text-muted")
                    ])
                ], color="warning", outline=True)
            ], width=3),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4("0:1", id="average-roi-ratio"),
                        html.P("Average ROI Ratio", className="text-muted")
                    ])
                ], color="info", outline=True)
            ], width=3)
        ], className="mb-4"),

        # Investment Creation Form
        dbc.Card([
            dbc.CardBody([
                html.H5("Create New Investment"),
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Investment Name"),
                        dbc.Input(id="new-investment-name",
                                  placeholder="Enter investment name...")
                    ], width=4),
                    dbc.Col([
                        dbc.Label("Investment Type"),
                        dcc.Dropdown(
                            id="new-investment-type",
                            placeholder="Select investment type...",
                            options=[]  # Will be populated based on available data
                        )
                    ], width=4),
                    dbc.Col([
                        dbc.Label("Initial Cost (£)"),
                        dbc.Input(id="new-investment-cost",
                                  type="number", placeholder="Enter cost...")
                    ], width=4)
                ], className="mb-3"),
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Production Line"),
                        dcc.Dropdown(
                            id="new-investment-line",
                            options=[
                                {'label': 'Line 1 - Surface Finish Primary',
                                    'value': 'line_1'},
                                {'label': 'Line 2 - Surface Finish Secondary',
                                    'value': 'line_2'},
                                {'label': 'Line 3 - Plating Line A',
                                    'value': 'line_3'},
                                {'label': 'Line 4 - Plating Line B',
                                    'value': 'line_4'},
                                {'label': 'Line 5 - Quality Control',
                                    'value': 'line_5'},
                                {'label': 'Line 6 - Packaging/Finishing',
                                    'value': 'line_6'},
                                {'label': 'All Lines', 'value': 'all_lines'}
                            ],
                            placeholder="Select production line..."
                        )
                    ], width=4),
                    dbc.Col([
                        dbc.Label("Implementation Time (months)"),
                        dbc.Input(id="new-investment-timeline", type="number",
                                  value=3, min=1, max=36)
                    ], width=4),
                    dbc.Col([
                        dbc.Button("Create Investment", id="create-investment-btn",
                                   color="primary", className="mt-4 w-100")
                    ], width=4)
                ])
            ])
        ], className="mb-4"),

        # Business Model Context Display
        dbc.Alert(id="business-model-context", color="info", className="mb-3"),

        # Investment Table
        dbc.Card([
            dbc.CardBody([
                html.H5("Investment Portfolio"),
                html.Div(id="investment-table-container"),

                # Calculate All Button
                dbc.Row([
                    dbc.Col([
                        dbc.Button("Calculate All Investments", id="calculate-all-btn",
                                   color="success", size="lg", className="w-100 mt-3")
                    ], width=12)
                ])
            ])
        ], className="mb-4"),

        # Detailed Calculation Results
        html.Div(id="calculation-results")
    ])


def create_investment_table(investments_data):
    """Create DataTable for investments."""
    if not investments_data:
        return html.P("No investments created yet. Create an investment above to get started.",
                      className="text-muted")

    columns = [
        {"name": "Investment Name", "id": "name"},
        {"name": "Type", "id": "type"},
        {"name": "Business Model", "id": "business_model"},
        {"name": "Production Line", "id": "production_line"},
        {"name": "Initial Cost (£)", "id": "cost", "type": "numeric", "format": {
            "specifier": ",.0f"}},
        {"name": "Annual Savings (£)", "id": "savings", "type": "numeric", "format": {
            "specifier": ",.0f"}},
        {"name": "ROI Ratio", "id": "roi_ratio"},
        {"name": "Payback (months)", "id": "payback_months",
         "type": "numeric", "format": {"specifier": ".1f"}},
        {"name": "Status", "id": "status"}
    ]

    return dash_table.DataTable(
        id="investment-table",
        columns=columns,
        data=investments_data,
        style_cell={'textAlign': 'left'},
        style_data_conditional=[
            {
                'if': {'filter_query': '{roi_ratio} > 3:1'},
                'backgroundColor': '#d4edda',
                'color': 'black',
            },
            {
                'if': {'filter_query': '{roi_ratio} < 2:1'},
                'backgroundColor': '#f8d7da',
                'color': 'black',
            }
        ],
        sort_action="native",
        filter_action="native",
        page_size=10,
        style_table={'overflowX': 'auto'}
    )


def create_calculation_results(results):
    """Create detailed calculation results display."""
    if not results:
        return html.Div()

    cards = []
    for investment_name, result in results.items():
        cards.append(
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6(investment_name),
                        html.P(f"Type: {result['type']}"),
                        html.P(f"Business Model: {result['business_model']}"),
                        html.Hr(),
                        html.P([
                            html.Strong("Annual Savings: "),
                            f"£{result['savings']:,.2f}"
                        ]),
                        html.P([
                            html.Strong("ROI Ratio: "),
                            result['roi_ratio']
                        ]),
                        html.P([
                            html.Strong("Payback Period: "),
                            f"{result['payback_months']:.1f} months"
                        ]),
                        html.P([
                            html.Strong("Confidence Level: "),
                            f"{result['confidence']:.0%}"
                        ])
                    ])
                ], color="success" if result['roi_ratio'] > "3:1" else "warning")
            ], width=4, className="mb-3")
        )

    return html.Div([
        html.H5("Detailed Calculation Results"),
        dbc.Row(cards)
    ])

# Callback to update available investment types based on uploaded data


@callback(
    [Output("new-investment-type", "options"),
     Output("business-model-context", "children")],
    Input("business-model-selection", "value")  # From data input tab
)
def update_available_investment_types(business_model):
    """Update available investment types based on business model and uploaded data."""
    if not business_model:
        return [], "No business model selected"

    # This would check which investment types have data uploaded
    # For now, showing all available types
    from investment_config import INVESTMENT_CONFIGS

    options = []
    for investment_type, config in INVESTMENT_CONFIGS.items():
        if business_model in config:
            options.append({
                'label': config['label'],
                'value': investment_type
            })

    context_text = f"Current Business Model: {business_model.replace('_', ' ').title()}"
    if business_model == "cost_center":
        context_text += " - Calculations focus on cost reduction and operational efficiency"
    else:
        context_text += " - Calculations focus on revenue generation and market opportunity"

    return options, context_text

# Callback to create new investment


@callback(
    Output("investment-table-container", "children"),
    [Input("create-investment-btn", "n_clicks")],
    [State("new-investment-name", "value"),
     State("new-investment-type", "value"),
     State("new-investment-cost", "value"),
     State("new-investment-line", "value"),
     State("new-investment-timeline", "value"),
     State("business-model-selection", "value")]
)
def create_new_investment(n_clicks, name, inv_type, cost, line, timeline, business_model):
    """Create new investment entry."""
    if not n_clicks or not all([name, inv_type, cost, line, business_model]):
        return create_investment_table([])

    # This would normally save to a data store
    # For now, creating sample data
    sample_investment = {
        'name': name,
        'type': inv_type,
        'business_model': business_model,
        'production_line': line,
        'cost': cost,
        'savings': 0,  # Will be calculated
        'roi_ratio': 'Not calculated',
        'payback_months': 0,
        'status': 'Data Required'
    }

    return create_investment_table([sample_investment])

# Callback to calculate all investments


@callback(
    [Output("calculation-results", "children"),
     Output("total-investments-count", "children"),
     Output("total-potential-savings", "children"),
     Output("total-investment-cost", "children"),
     Output("average-roi-ratio", "children")],
    Input("calculate-all-btn", "n_clicks")
)
def calculate_all_investments(n_clicks):
    """Calculate all investments using uploaded data."""
    if not n_clicks:
        return html.Div(), "0", "£0", "£0", "0:1"

    # This would use actual investment data and uploaded data
    # For now, creating sample results
    sample_results = {
        "Equipment Upgrade": {
            'type': 'Capital Equipment',
            'business_model': 'cost_center',
            'savings': 87500,
            'roi_ratio': '3.5:1',
            'payback_months': 8.6,
            'confidence': 0.85
        }
    }

    results_display = create_calculation_results(sample_results)

    return results_display, "1", "£87,500", "£25,000", "3.5:1"
