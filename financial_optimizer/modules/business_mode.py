"""Business Mode Layout Module - Financial Optimizer

Created: 2025-07-21
Author: Development Team
Purpose: Business Mode 4-tab layout implementation based on specifications
"""

from dash import html, dcc, dash_table, callback, Input, Output, State
import dash_bootstrap_components as dbc
import logging
import json
import os

# Configure logging
logger = logging.getLogger(__name__)


def create_business_mode_layout():
    """Creates the complete Business Mode 4-tab layout"""

    print("🏗️ LAYOUT DEBUG: Creating Business Mode layout...")
    print("🏗️ This should appear when switching to Business Mode")

    return dbc.Container([
        # Business Mode Header
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4("🏢 Business Mode",
                                className="text-primary mb-2"),
                        html.P([
                            "Optimize your business investments across cost centers and profit centers. ",
                            "Input potential investments, upload data, and receive optimal investment strategies."
                        ], className="text-muted mb-0")
                    ])
                ], className="mb-4")
            ])
        ]),

        # Main Business Mode Tabs
        dbc.Tabs([
            # Tab 1: Investment Management
            dbc.Tab(
                label="Investment Management",
                tab_id="business-investment-management",
                children=[_create_investment_management_tab()]
            ),

            # Tab 2: Data Input
            dbc.Tab(
                label="Data Input",
                tab_id="business-data-input",
                children=[_create_data_input_tab()]
            ),

            # Tab 3: Financial Dashboard
            dbc.Tab(
                label="Financial Dashboard",
                tab_id="business-financial-dashboard",
                children=[_create_financial_dashboard_tab()]
            ),

            # Tab 4: Investment Reports
            dbc.Tab(
                label="Investment Reports",
                tab_id="business-investment-reports",
                children=[_create_investment_reports_tab()]
            )
        ], id="business-mode-tabs", active_tab="business-investment-management")
    ], fluid=True)


def _create_investment_management_tab():
    """Tab 1: Investment Management - Primary workspace for inputting investments"""

    return html.Div([
        dbc.Row([
            dbc.Col([
                html.H4("Investment Management", className="mb-3"),
                html.P("Primary workspace for inputting, managing, and tracking potential investments",
                       className="text-muted mb-4")
            ])
        ]),

        dbc.Row([
            # Left Column: Investment Input Form
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(
                        html.H5("Add New Investment", className="mb-0")),
                    dbc.CardBody([
                        # Investment Basic Information
                        dbc.Row([
                            dbc.Col([
                                html.Label("Investment Name",
                                           className="form-label"),
                                dbc.Input(
                                    id="main-investment-name-input",
                                    placeholder="Enter investment name (max 100 characters)",
                                    maxLength=100,
                                    className="mb-3"
                                )
                            ], width=12)
                        ]),

                        dbc.Row([
                            dbc.Col([
                                html.Label("Investment Type",
                                           className="form-label"),
                                dcc.Dropdown(
                                    id="main-investment-type-dropdown",
                                    options=[
                                        {"label": "Capital Equipment",
                                            "value": "capital"},
                                        {"label": "Process Improvement",
                                            "value": "process"},
                                        {"label": "Human Capital/People",
                                            "value": "people"},
                                        {"label": "Maintenance",
                                            "value": "maintenance"},
                                        {"label": "Quality", "value": "quality"},
                                        {"label": "Digital Transformation",
                                            "value": "digital"},
                                        {"label": "Safety & Environmental",
                                            "value": "safety"},
                                        {"label": "Facility & Infrastructure",
                                            "value": "facility"},
                                        {"label": "Supply Chain & Logistics",
                                            "value": "supply_chain"}
                                    ],
                                    placeholder="Select investment type...",
                                    className="mb-3"
                                )
                            ], width=6),
                            dbc.Col([
                                html.Label("Business Model",
                                           className="form-label"),
                                dcc.Dropdown(
                                    id="biz-business-model-dropdown",
                                    options=[
                                        {"label": "Cost Center (Cost Reduction Focus)",
                                         "value": "cost_center"},
                                        {"label": "Profit Center (Revenue Generation Focus)", "value": "profit_center"}
                                    ],
                                    placeholder="Select business model...",
                                    className="mb-3"
                                )
                            ], width=6)
                        ]),

                        dbc.Row([
                            dbc.Col([
                                html.Label("Production Line",
                                           className="form-label"),
                                dcc.Dropdown(
                                    id="business-production-line-dropdown",
                                    options=[
                                        {"label": "Line 1 - Surface Finish Primary",
                                            "value": "line_1"},
                                        {"label": "Line 2 - Surface Finish Secondary",
                                            "value": "line_2"},
                                        {"label": "Line 3 - Plating Line A",
                                            "value": "line_3"},
                                        {"label": "Line 4 - Plating Line B",
                                            "value": "line_4"},
                                        {"label": "Line 5 - Quality Control",
                                            "value": "line_5"},
                                        {"label": "Line 6 - Packaging/Finishing",
                                            "value": "line_6"},
                                        {"label": "All Lines (Cross-Department)",
                                         "value": "all_lines"}
                                    ],
                                    placeholder="Select production line...",
                                    className="mb-3"
                                )
                            ], width=6),
                            dbc.Col([
                                html.Label("Priority Level",
                                           className="form-label"),
                                dcc.Dropdown(
                                    id="business-priority-level-dropdown",
                                    options=[
                                        {"label": "High Priority", "value": "high"},
                                        {"label": "Medium Priority",
                                            "value": "medium"},
                                        {"label": "Low Priority", "value": "low"}
                                    ],
                                    placeholder="Select priority level...",
                                    className="mb-3"
                                )
                            ], width=6)
                        ]),

                        # Financial Parameters
                        html.Hr(),
                        html.H6("Financial Parameters", className="mb-3"),

                        dbc.Row([
                            dbc.Col([
                                html.Label("Initial Investment Cost ($)",
                                           className="form-label"),
                                dbc.Input(
                                    id="main-investment-cost-input",
                                    type="number",
                                    min=0,
                                    placeholder="Enter investment cost",
                                    className="mb-3"
                                )
                            ], width=6),
                            dbc.Col([
                                html.Label(
                                    "Implementation Timeline (months)", className="form-label"),
                                dbc.Input(
                                    id="business-implementation-timeline-input",
                                    type="number",
                                    min=1,
                                    max=36,
                                    placeholder="1-36 months",
                                    className="mb-3"
                                )
                            ], width=6)
                        ]),

                        dbc.Row([
                            dbc.Col([
                                html.Label("Available Budget ($)",
                                           className="form-label"),
                                dbc.Input(
                                    id="business-available-budget-input",
                                    type="number",
                                    min=0,
                                    placeholder="Enter available budget",
                                    className="mb-3"
                                )
                            ], width=12)
                        ]),

                        # Action Buttons
                        html.Hr(),
                        dbc.Row([
                            dbc.Col([
                                dbc.Button(
                                    "Add Investment",
                                    id="main-add-investment-btn",
                                    color="primary",
                                    className="me-2"
                                ),
                                dbc.Button(
                                    "Clear Form",
                                    id="clear-form-btn",
                                    color="secondary",
                                    outline=True
                                )
                            ])
                        ]),

                        # DEBUG: Add a simple div to verify the layout loads
                        html.Div([
                            html.Small("🔍 DEBUG: Button layout loaded successfully",
                                       className="text-muted",
                                       id="debug-layout-indicator")
                        ], className="mt-2")
                    ])
                ])
            ], width=5),

            # Right Column: Investment Portfolio Table
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H5("Investment Portfolio",
                                className="mb-0 d-inline"),
                        dbc.Badge(
                            "0 Investments",
                            id="main-investment-count-badge",
                            color="info",
                            className="ms-2"
                        )
                    ]),
                    dbc.CardBody([
                        # Investment Table
                        dash_table.DataTable(
                            id="main-investment-portfolio-table",
                            columns=[
                                {"name": "Investment Name", "id": "name"},
                                {"name": "Type", "id": "type"},
                                {"name": "Cost (£)", "id": "cost", "type": "numeric", 
                                 "format": {"specifier": ",.0f"}},
                                {"name": "Status", "id": "status"},
                            ],
                            data=[],
                            editable=False,
                            row_deletable=False,
                            style_cell={
                                'textAlign': 'left',
                                'padding': '12px',
                                'fontFamily': 'Arial'
                            },
                            style_header={
                                'backgroundColor': '#f8f9fa',
                                'fontWeight': 'bold'
                            },
                            style_data_conditional=[
                                {
                                    'if': {'column_id': 'priority', 'filter_query': '{priority} = high'},
                                    'backgroundColor': '#fff3cd',
                                },
                                {
                                    'if': {'column_id': 'priority', 'filter_query': '{priority} = low'},
                                    'backgroundColor': '#f8f9fa',
                                }
                            ],
                            page_size=10,
                            sort_action="native",
                            filter_action="native"
                        ),

                        html.Hr(),

                        # Portfolio Summary Cards
                        dbc.Row([
                            dbc.Col([
                                dbc.Card([
                                    dbc.CardBody([
                                        html.H6("Total Investments",
                                                className="card-title text-muted"),
                                        html.H4(
                                            "0", id="total-investments-count", className="text-primary")
                                    ])
                                ])
                            ], width=3),
                            dbc.Col([
                                dbc.Card([
                                    dbc.CardBody([
                                        html.H6(
                                            "Total Cost", className="card-title text-muted"),
                                        html.H4(
                                            "£0", id="total-investment-cost", className="text-success")
                                    ])
                                ])
                            ], width=3),
                            dbc.Col([
                                dbc.Card([
                                    dbc.CardBody([
                                        html.H6(
                                            "Average ROI", className="card-title text-muted"),
                                        html.H4("0%", id="average-roi",
                                                className="text-info")
                                    ])
                                ])
                            ], width=3),
                            dbc.Col([
                                dbc.Card([
                                    dbc.CardBody([
                                        html.H6(
                                            "Budget Used", className="card-title text-muted"),
                                        html.H4(
                                            "0%", id="budget-utilization", className="text-warning")
                                    ])
                                ])
                            ], width=3)
                        ])
                    ])
                ])
            ], width=7)
        ])
    ], className="p-4")


def _create_data_input_tab():
    """Tab 2: Data Input - Upload investment-type-specific data for calculations"""

    return html.Div([
        dbc.Row([
            dbc.Col([
                html.H4("Data Input", className="mb-3"),
                html.P("Upload investment-type-specific data for calculations",
                       className="text-muted mb-4")
            ])
        ]),

        # Instructions Card
        dbc.Row([
            dbc.Col([
                dbc.Alert([
                    html.H6("📋 Instructions", className="alert-heading"),
                    html.P([
                        "1. First commit investments in the Investment Management tab",
                        html.Br(),
                        "2. Upload forms will appear below based on your committed investment types",
                        html.Br(),
                        "3. Upload CSV/Excel files or enter data manually for each investment type"
                    ], className="mb-0")
                ], color="info", className="mb-4")
            ])
        ]),

        # Dynamic Upload Forms Area
        dbc.Row([
            dbc.Col([
                html.Div([
                    dbc.Card([
                        dbc.CardBody([
                            html.Div([
                                html.H5("No Investments Committed",
                                        className="text-center text-muted"),
                                html.P("Please add investments in the Investment Management tab to see upload forms here.",
                                       className="text-center text-muted mb-0")
                            ], className="py-5")
                        ])
                    ])
                ], id="dynamic-upload-forms")
            ])
        ])
    ], className="p-4")


def _create_financial_dashboard_tab():
    """Tab 3: Financial Dashboard - Display optimal investment strategy and budget allocation"""

    return html.Div([
        dbc.Row([
            dbc.Col([
                html.H4("Financial Dashboard", className="mb-3"),
                html.P("Display optimal investment strategy and budget allocation",
                       className="text-muted mb-4")
            ])
        ]),

        # Budget Allocation Section
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(
                        html.H5("Budget Allocation", className="mb-0")),
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                html.Label("Budget Allocation Slider",
                                           className="form-label"),
                                html.P("Adjust budget allocation across your investment portfolio",
                                       className="text-muted small"),
                                dcc.Slider(
                                    id="budget-allocation-slider",
                                    min=0,
                                    max=100,
                                    step=5,
                                    value=100,
                                    marks={
                                        i: f'{i}%' for i in range(0, 101, 25)},
                                    tooltip={"placement": "bottom",
                                             "always_visible": True}
                                )
                            ], width=12)
                        ])
                    ])
                ])
            ], width=12, className="mb-4")
        ]),

        # Dashboard Content Row
        dbc.Row([
            # Left Column: Investment Schedule
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(
                        html.H5("Optimal Investment Schedule", className="mb-0")),
                    dbc.CardBody([
                        html.Div([
                            html.H6("No Investment Data Available",
                                    className="text-center text-muted"),
                            html.P("Upload investment data to see optimal scheduling recommendations",
                                   className="text-center text-muted mb-0")
                        ], id="investment-schedule-content", className="py-4")
                    ])
                ])
            ], width=6),

            # Right Column: Savings Projections
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(
                        html.H5("Savings Projections", className="mb-0")),
                    dbc.CardBody([
                        html.Div([
                            html.H6("No Calculation Results",
                                    className="text-center text-muted"),
                            html.P("Complete data input to see savings projections and ROI analysis",
                                   className="text-center text-muted mb-0")
                        ], id="savings-projections-content", className="py-4")
                    ])
                ])
            ], width=6)
        ], className="mb-4"),

        # ROI Analysis and Comparison
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(
                        html.H5("ROI Analysis & Investment Comparison", className="mb-0")),
                    dbc.CardBody([
                        html.Div([
                            html.H6("Investment Analysis",
                                    className="text-center text-muted"),
                            html.P("ROI comparisons and priority recommendations will appear here after calculations",
                                   className="text-center text-muted mb-0")
                        ], id="roi-analysis-content", className="py-4")
                    ])
                ])
            ], width=12)
        ])
    ], className="p-4")


def _create_investment_reports_tab():
    """Tab 4: Investment Reports - Generate and download investment strategy reports"""

    return html.Div([
        dbc.Row([
            dbc.Col([
                html.H4("Investment Reports", className="mb-3"),
                html.P("Generate and download investment strategy reports",
                       className="text-muted mb-4")
            ])
        ]),

        dbc.Row([
            # Left Column: Report Configuration
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(
                        html.H5("Report Configuration", className="mb-0")),
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                html.Label("Report Type",
                                           className="form-label"),
                                dcc.Dropdown(
                                    id="report-type-dropdown",
                                    options=[
                                        {"label": "Investment Strategy Summary",
                                            "value": "strategy_summary"},
                                        {"label": "Financial Impact Analysis",
                                            "value": "financial_impact"},
                                        {"label": "Implementation Timeline",
                                            "value": "implementation_timeline"},
                                        {"label": "Stakeholder Summary",
                                            "value": "stakeholder_summary"},
                                        {"label": "Complete Investment Report",
                                            "value": "complete_report"}
                                    ],
                                    placeholder="Select report type...",
                                    className="mb-3"
                                )
                            ], width=12)
                        ]),

                        dbc.Row([
                            dbc.Col([
                                html.Label("Export Format",
                                           className="form-label"),
                                dcc.Dropdown(
                                    id="export-format-dropdown",
                                    options=[
                                        {"label": "PDF Document", "value": "pdf"},
                                        {"label": "Excel Spreadsheet",
                                            "value": "excel"},
                                        {"label": "CSV Data", "value": "csv"}
                                    ],
                                    placeholder="Select export format...",
                                    className="mb-3"
                                )
                            ], width=6),
                            dbc.Col([
                                html.Label("Report Recipient",
                                           className="form-label"),
                                dcc.Dropdown(
                                    id="report-recipient-dropdown",
                                    options=[
                                        {"label": "Executive Summary",
                                            "value": "executive"},
                                        {"label": "Department Manager",
                                            "value": "department"},
                                        {"label": "Financial Team",
                                            "value": "financial"},
                                        {"label": "Implementation Team",
                                            "value": "implementation"},
                                        {"label": "All Stakeholders",
                                            "value": "all_stakeholders"}
                                    ],
                                    placeholder="Select recipient type...",
                                    className="mb-3"
                                )
                            ], width=6)
                        ]),

                        html.Hr(),

                        dbc.Row([
                            dbc.Col([
                                dbc.Button(
                                    "Generate Report",
                                    id="generate-report-btn",
                                    color="primary",
                                    size="lg",
                                    className="w-100",
                                    disabled=True
                                ),
                                html.P("Complete investment analysis to enable report generation",
                                       className="text-muted small text-center mt-2")
                            ])
                        ])
                    ])
                ])
            ], width=4),

            # Right Column: Report Preview
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(
                        html.H5("Report Preview", className="mb-0")),
                    dbc.CardBody([
                        html.Div([
                            html.H6("📄 Report Preview",
                                    className="text-center text-muted"),
                            html.P("Select report type and generate to see preview here",
                                   className="text-center text-muted mb-4"),

                            # Sample Report Structure Preview
                            dbc.Card([
                                dbc.CardBody([
                                    html.H6("Sample Report Structure:",
                                            className="text-muted mb-3"),
                                    html.Ul([
                                        html.Li("Executive Summary"),
                                        html.Li(
                                            "Investment Portfolio Overview"),
                                        html.Li("Financial Impact Analysis"),
                                        html.Li("Implementation Timeline"),
                                        html.Li("ROI Projections"),
                                        html.Li("Recommendations"),
                                        html.Li("Appendices")
                                    ], className="text-muted")
                                ])
                            ], color="light", outline=True)
                        ], id="report-preview-content", className="py-4")
                    ])
                ])
            ], width=8)
        ])
    ], className="p-4")


# Data file path
DATA_FILE = '/workspaces/financial_optimizer/data/investments.json'


def load_investments():
    """Load investments from file"""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                return json.load(f)
        except Exception:
            return []
    return []


def save_investments(investments):
    """Save investments to file"""
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, 'w') as f:
        json.dump(investments, f, indent=2)


# COMMENTED OUT - Using working callback in main app instead
# @callback(
#     [Output("biz-investment-portfolio-table", "data"),
#      Output("investment-count-badge", "children")],
#     [Input("biz-add-investment-btn", "n_clicks")],
#     [State("biz-investment-name-input", "value"),
#      State("biz-investment-type-dropdown", "value"),
#      State("biz-investment-cost-input", "value")],
#     prevent_initial_call=True,
#     suppress_callback_exceptions=True
# )
# def add_biz_investment(n_clicks, name, inv_type, cost):
#     """Business Mode Investment Management callback with UNIQUE IDs"""
#     print(f"🔥🔥🔥 BIZ INVESTMENT CALLBACK TRIGGERED! n_clicks={n_clicks}")
#     print(f"🔥 name='{name}', inv_type='{inv_type}', cost='{cost}'")
#
#     # Load existing investments
#     investments = load_investments()
#
#     # Check if button was clicked and required fields are filled
#     if (n_clicks and n_clicks > 0 and name and name.strip() and
#             inv_type and cost):
#         try:
#             print(f"🔥 CREATING BIZ INVESTMENT: {name}")
#
#             new_investment = {
#                 "name": name,
#                 "type": inv_type,
#                 "cost": float(cost),
#                 "status": "Planning",
#                 "business_mode": True
#             }
#
#             investments.append(new_investment)
#             save_investments(investments)
#
#             print(f"🔥 SUCCESS: Added {name} to business table - "
#                   f"Now {len(investments)} investments")
#
#         except Exception as e:
#             print(f"🔥 ERROR: {e}")
#     else:
#         print("🔥 Button not clicked or missing fields")
#
#     # Return data for DataTable
#     table_data = []
#     for inv in investments:
#         table_data.append({
#             "name": inv["name"],
#             "type": inv["type"],
#             "cost": inv["cost"],
#             "business_model": inv.get("business_model", "N/A"),
#             "timeline": inv.get("timeline", "TBD"),
#             "priority": inv.get("priority", "Medium"),
#             "actions": "Edit | Delete"
#         })
#
#     count_badge = f"{len(investments)} Investments"
#
#     return table_data, count_badge


if __name__ == "__main__":
    # Test the layout creation
    layout = create_business_mode_layout()
    print("✅ Business Mode layout created successfully")
