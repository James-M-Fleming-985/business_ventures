"""Business Mode Layout - Financial Optimizer

4-tab layout implementation based on Business Mode specifications.
Tab 1: Investment Management
Tab 2: Data Input
Tab 3: Financial Dashboard
Tab 4: Investment Reports
"""

from dash import html, dcc, dash_table
import dash_bootstrap_components as dbc
import logging

# Configure logging
logger = logging.getLogger(__name__)


def create_business_layout():
    """Creates the complete Business Mode 4-tab layout"""

    return dbc.Container([
        # Business Mode Header
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4("🏢 Business Mode",
                                className="text-primary mb-2"),
                        html.P([
                            "Optimize your business investments across ",
                            "cost centers and profit centers. Input potential ",
                            "investments, upload data, and receive optimal ",
                            "investment strategies."
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
                children=_create_investment_management_tab()
            ),

            # Tab 2: Data Input
            dbc.Tab(
                label="Data Input",
                tab_id="business-data-input",
                children=_create_data_input_tab()
            ),

            # Tab 3: Financial Dashboard
            dbc.Tab(
                label="Financial Dashboard",
                tab_id="business-financial-dashboard",
                children=_create_financial_dashboard_tab()
            ),

            # Tab 4: Investment Reports
            dbc.Tab(
                label="Investment Reports",
                tab_id="business-investment-reports",
                children=_create_investment_reports_tab()
            )
        ], id="business-mode-tabs",
            active_tab="business-investment-management")
    ], fluid=True)


def _create_investment_management_tab():
    """Tab 1: Investment Management - Original Layout"""

    return html.Div([
        html.H3("Investment Management"),
        html.P("Manage and analyze your investments using uploaded data."),

        # Investment Summary Cards
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4("3", id="total-investments-count"),
                        html.P("Total Investments", className="text-muted")
                    ])
                ], color="primary", outline=True)
            ], width=3),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4("£305,000", id="total-potential-savings"),
                        html.P("Total Potential Savings",
                               className="text-muted")
                    ])
                ], color="success", outline=True)
            ], width=3),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4("£155,000", id="total-investment-cost"),
                        html.P("Total Investment Cost", className="text-muted")
                    ])
                ], color="warning", outline=True)
            ], width=3),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4("1.97:1", id="average-roi-ratio"),
                        html.P("Average ROI Ratio", className="text-muted")
                    ])
                ], color="info", outline=True)
            ], width=3)
        ], className="mb-4"),

        # Business Model Selection
        dbc.Card([
            dbc.CardBody([
                html.H5("Step 1: Business Model Configuration"),
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Business Model:"),
                        dcc.Dropdown(
                            id='investment-business-model-dropdown',
                            options=[
                                {'label': 'Profit Center (Revenue Generation)',
                                 'value': 'profit_center'},
                                {'label': 'Cost Center (Cost Reduction)',
                                 'value': 'cost_center'}
                            ],
                            placeholder="Select business model...",
                            clearable=False,
                            value='cost_center'
                        )
                    ], width=6),
                    dbc.Col([
                        html.Label(id="organizational-unit-label", children="Cost Centers:"),
                        dbc.InputGroup([
                            dcc.Dropdown(
                                id='investment-organizational-unit-dropdown',
                                options=[
                                    {'label': 'Production Department', 'value': 'production'},
                                    {'label': 'Quality Control', 'value': 'quality'},
                                    {'label': 'Maintenance', 'value': 'maintenance'},
                                    {'label': 'Logistics', 'value': 'logistics'}
                                ],
                                placeholder="Select organizational unit...",
                                clearable=False,
                                style={'flex': '1'}
                            ),
                            dbc.Button("Add New", id="add-organizational-unit-btn",
                                       color="outline-secondary", size="sm")
                        ])
                    ], width=6),
                ], className="mb-3"),
                dbc.Alert(
                    id="business-model-description",
                    color="info",
                    children="Cost Center focuses on operational efficiency and cost reduction."
                )
            ])
        ], className="mb-4"),

        # Investment Creation Form
        dbc.Card([
            dbc.CardBody([
                html.H5("Step 2: Create New Investment"),
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
                            options=[
                                {"label": "Capital Equipment", "value": "capital"},
                                {"label": "Process Improvement", "value": "process"},
                                {"label": "Human Capital/People", "value": "people"},
                                {"label": "Maintenance", "value": "maintenance"},
                                {"label": "Quality", "value": "quality"},
                                {"label": "Digital Transformation",
                                    "value": "digital"},
                                {"label": "Safety & Environmental",
                                    "value": "safety"},
                                {"label": "Facility & Infrastructure",
                                    "value": "facility"},
                                {"label": "Supply Chain & Logistics",
                                    "value": "supply_chain"}
                            ]
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
                    ], width=3),
                    dbc.Col([
                        dbc.Label("Priority Level"),
                        dcc.Dropdown(
                            id="new-investment-priority",
                            options=[
                                {'label': 'High - Critical', 'value': 'high'},
                                {'label': 'Medium - Important', 'value': 'medium'},
                                {'label': 'Low - Nice to Have', 'value': 'low'}
                            ],
                            placeholder="Select priority...",
                            value='medium'
                        )
                    ], width=3),
                    dbc.Col([
                        dbc.Label("Implementation Time (months)"),
                        dbc.Input(id="new-investment-timeline", type="number",
                                  value=3, min=1, max=36)
                    ], width=3),
                    dbc.Col([
                        dbc.Button("Create Investment", id="create-investment-btn",
                                   color="primary", className="mt-4 w-100")
                    ], width=3)
                ])
            ])
        ], className="mb-4"),

        # Business Model Context Display
        dbc.Alert(id="business-model-context", color="info", className="mb-3"),

        # Investment Table
        dbc.Card([
            dbc.CardBody([
                html.H5("Investment Portfolio"),
                html.Div([
                    # Sample investments display (will be replaced with dynamic data)
                    html.Div([
                        dash_table.DataTable(
                            id="investment-portfolio-table",
                            columns=[
                                {"name": "Investment Name", "id": "name"},
                                {"name": "Type", "id": "type"},
                                {"name": "Business Model", "id": "business_model"},
                                {"name": "Cost Center", "id": "cost_center"},
                                {"name": "Production Line", "id": "production_line"},
                                {"name": "Priority", "id": "priority"},
                                {"name": "Cost (£)", "id": "cost", "type": "numeric",
                                 "format": {"specifier": ",.0f"}},
                                {"name": "Timeline (months)", "id": "timeline"},
                                {"name": "Expected Savings (£)", "id": "expected_savings", "type": "numeric",
                                 "format": {"specifier": ",.0f"}},
                                {"name": "ROI", "id": "roi"},
                                {"name": "Status", "id": "status"},
                                {"name": "Actions", "id": "actions", "presentation": "markdown"}
                            ],
                            data=[
                                {
                                    "name": "Automated Quality Control System",
                                    "type": "Capital Equipment",
                                    "business_model": "Cost Center",
                                    "cost_center": "Quality Control",
                                    "production_line": "Line 5 - Quality Control",
                                    "priority": "High",
                                    "cost": 75000,
                                    "timeline": 6,
                                    "expected_savings": 125000,
                                    "roi": "1.67:1",
                                    "status": "Ready for Analysis",
                                    "actions": "[Edit](edit) | [Delete](delete) | [Analyze](analyze)"
                                },
                                {
                                    "name": "Process Optimization Software",
                                    "type": "Digital Transformation",
                                    "business_model": "Cost Center", 
                                    "cost_center": "Production",
                                    "production_line": "All Lines",
                                    "priority": "Medium",
                                    "cost": 45000,
                                    "timeline": 4,
                                    "expected_savings": 95000,
                                    "roi": "2.11:1",
                                    "status": "Data Required",
                                    "actions": "[Edit](edit) | [Delete](delete) | [Upload Data](upload)"
                                },
                                {
                                    "name": "Preventive Maintenance System",
                                    "type": "Maintenance",
                                    "business_model": "Cost Center",
                                    "cost_center": "Maintenance", 
                                    "production_line": "All Lines",
                                    "priority": "High",
                                    "cost": 35000,
                                    "timeline": 3,
                                    "expected_savings": 85000,
                                    "roi": "2.43:1",
                                    "status": "Analysis Complete",
                                    "actions": "[Edit](edit) | [Delete](delete) | [View Report](report)"
                                }
                            ],
                            editable=False,
                            row_deletable=False,
                            style_cell={
                                'textAlign': 'left',
                                'padding': '12px',
                                'fontFamily': 'Arial',
                                'minWidth': '120px'
                            },
                            style_header={
                                'backgroundColor': '#f8f9fa',
                                'fontWeight': 'bold'
                            },
                            style_data_conditional=[
                                {
                                    'if': {'filter_query': '{status} = "Ready for Analysis"'},
                                    'backgroundColor': '#d4edda',
                                    'color': 'black',
                                },
                                {
                                    'if': {'filter_query': '{status} = "Data Required"'},
                                    'backgroundColor': '#fff3cd',
                                    'color': 'black',
                                },
                                {
                                    'if': {'filter_query': '{status} = "Analysis Complete"'},
                                    'backgroundColor': '#d1ecf1',
                                    'color': 'black',
                                }
                            ],
                            page_size=10,
                            sort_action="native",
                            filter_action="native"
                        )
                    ], id="investment-table-container", style={"display": "block"})
                ]),

                # Updated summary cards
                dbc.Row([
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.H4("£255,000", id="total-potential-savings"),
                                html.P("Total Expected Savings", className="text-muted")
                            ])
                        ], color="success", outline=True)
                    ], width=3),
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.H4("£155,000", id="total-investment-cost"),
                                html.P("Total Investment Cost", className="text-muted")
                            ])
                        ], color="warning", outline=True)
                    ], width=3),
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.H4("1.65:1", id="average-roi-ratio"),
                                html.P("Average ROI Ratio", className="text-muted")
                            ])
                        ], color="info", outline=True)
                    ], width=3),
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.H4("13 months", id="average-payback"),
                                html.P("Average Payback Period", className="text-muted")
                            ])
                        ], color="secondary", outline=True)
                    ], width=3)
                ], className="mt-3")
                ]),

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


def _create_data_input_tab():
    """Tab 2: Data Input - Original Layout with Modal Dialogs"""

    return html.Div([
        html.H3("Data Input"),
        html.P("Select your business model and upload data for each investment type."),

        # Business Model Selection
        dbc.Card([
            dbc.CardBody([
                html.H5("Step 1: Select Business Model",
                        className="card-title"),
                dbc.RadioItems(
                    id="business-model-selection",
                    options=[
                        {"label": "Cost Center - Focus on cost reduction and operational efficiency",
                         "value": "cost_center"},
                        {"label": "Profit Center - Focus on revenue generation and market opportunity",
                         "value": "profit_center"}
                    ],
                    value="cost_center",
                    inline=False,
                    className="mb-3"
                ),
                dbc.Alert(
                    id="business-model-description",
                    color="info",
                    className="mb-0"
                )
            ])
        ], className="mb-4"),

        # Investment Type Upload Boxes
        html.Div([
            html.H5("Step 2: Upload Data for Investment Types"),
            html.P("Click on each investment type to open detailed data upload forms."),
            html.Div([
            html.Div([
                # Row 1: Capital Equipment, Process Improvement, Human Capital
                dbc.Row([
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.H6("📁 Capital Equipment",
                                        className="card-title"),
                                html.P(
                                    "Equipment investments for operational improvements", className="card-text small"),
                                html.P("Required fields: 8", className="text-muted small"),
                                html.P("Status: Data Required",
                                       className="text-warning small"),
                                html.Hr(),
                                dbc.Button(
                                    "Upload Data",
                                    id="open-capital-form",
                                    color="primary",
                                    size="sm",
                                    className="w-100"
                                )
                            ])
                        ], color="light", outline=True, className="h-100")
                    ], width=4, className="mb-3"),

                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.H6("📁 Process Improvement",
                                        className="card-title"),
                                html.P(
                                    "Process optimization and workflow improvements", className="card-text small"),
                                html.P("Required fields: 6", className="text-muted small"),
                                html.P("Status: Data Required",
                                       className="text-warning small"),
                                html.Hr(),
                                dbc.Button(
                                    "Upload Data",
                                    id="open-process-form",
                                    color="primary",
                                    size="sm",
                                    className="w-100"
                                )
                            ])
                        ], color="light", outline=True, className="h-100")
                    ], width=4, className="mb-3"),

                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.H6("📁 Human Capital/People",
                                        className="card-title"),
                                html.P(
                                    "Training, hiring, and human resource investments", className="card-text small"),
                                html.P("Required fields: 5", className="text-muted small"),
                                html.P("Status: Data Required",
                                       className="text-warning small"),
                                html.Hr(),
                                dbc.Button(
                                    "Upload Data",
                                    id="open-people-form",
                                    color="primary",
                                    size="sm",
                                    className="w-100"
                                )
                            ])
                        ], color="light", outline=True, className="h-100")
                    ], width=4, className="mb-3")
                ]),

                # Row 2: Maintenance, Quality, Digital Transformation
                dbc.Row([
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.H6("📁 Maintenance",
                                        className="card-title"),
                                html.P(
                                    "Equipment maintenance and reliability improvements", className="card-text small"),
                                html.P("Required fields: 7", className="text-muted small"),
                                html.P("Status: Data Required",
                                       className="text-warning small"),
                                html.Hr(),
                                dbc.Button(
                                    "Upload Data",
                                    id="open-maintenance-form",
                                    color="primary",
                                    size="sm",
                                    className="w-100"
                                )
                            ])
                        ], color="light", outline=True, className="h-100")
                    ], width=4, className="mb-3"),

                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.H6("📁 Quality",
                                        className="card-title"),
                                html.P(
                                    "Quality control and assurance investments", className="card-text small"),
                                html.P("Required fields: 6", className="text-muted small"),
                                html.P("Status: Data Required",
                                       className="text-warning small"),
                                html.Hr(),
                                dbc.Button(
                                    "Upload Data",
                                    id="open-quality-form",
                                    color="primary",
                                    size="sm",
                                    className="w-100"
                                )
                            ])
                        ], color="light", outline=True, className="h-100")
                    ], width=4, className="mb-3"),

                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.H6("📁 Digital Transformation",
                                        className="card-title"),
                                html.P(
                                    "Technology and digitalization investments", className="card-text small"),
                                html.P("Required fields: 9", className="text-muted small"),
                                html.P("Status: Data Required",
                                       className="text-warning small"),
                                html.Hr(),
                                dbc.Button(
                                    "Upload Data",
                                    id="open-digital-form",
                                    color="primary",
                                    size="sm",
                                    className="w-100"
                                )
                            ])
                        ], color="light", outline=True, className="h-100")
                    ], width=4, className="mb-3")
                ]),

                # Row 3: Safety & Environmental, Facility & Infrastructure, Supply Chain
                dbc.Row([
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.H6("📁 Safety & Environmental",
                                        className="card-title"),
                                html.P(
                                    "Safety improvements and environmental compliance", className="card-text small"),
                                html.P("Required fields: 5", className="text-muted small"),
                                html.P("Status: Data Required",
                                       className="text-warning small"),
                                html.Hr(),
                                dbc.Button(
                                    "Upload Data",
                                    id="open-safety-form",
                                    color="primary",
                                    size="sm",
                                    className="w-100"
                                )
                            ])
                        ], color="light", outline=True, className="h-100")
                    ], width=4, className="mb-3"),

                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.H6("📁 Facility & Infrastructure",
                                        className="card-title"),
                                html.P(
                                    "Building, infrastructure, and facility improvements", className="card-text small"),
                                html.P("Required fields: 6", className="text-muted small"),
                                html.P("Status: Data Required",
                                       className="text-warning small"),
                                html.Hr(),
                                dbc.Button(
                                    "Upload Data",
                                    id="open-facility-form",
                                    color="primary",
                                    size="sm",
                                    className="w-100"
                                )
                            ])
                        ], color="light", outline=True, className="h-100")
                    ], width=4, className="mb-3"),

                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.H6("📁 Supply Chain & Logistics",
                                        className="card-title"),
                                html.P(
                                    "Supply chain optimization and logistics improvements", className="card-text small"),
                                html.P("Required fields: 7", className="text-muted small"),
                                html.P("Status: Data Required",
                                       className="text-warning small"),
                                html.Hr(),
                                dbc.Button(
                                    "Upload Data",
                                    id="open-supply-chain-form",
                                    color="primary",
                                    size="sm",
                                    className="w-100"
                                )
                            ])
                        ], color="light", outline=True, className="h-100")
                    ], width=4, className="mb-3")
                ])
            ], id="investment-type-boxes", className="row")
        ], id="investment-upload-section"),

        # Modal dialogs for each investment type
        *_create_investment_modals()
    ])


def _create_financial_dashboard_tab():
    """Tab 3: Financial Dashboard"""

    return html.Div([
        dbc.Row([
            dbc.Col([
                html.H4("Financial Dashboard", className="mb-3"),
                html.P("Display optimal investment strategy " +
                       "and budget allocation",
                       className="text-muted mb-4")
            ])
        ]),

        # Dashboard Content Row
        dbc.Row([
            # Left Column: Investment Schedule
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H5("Optimal Investment Schedule",
                                           className="mb-0")),
                    dbc.CardBody([
                        html.Div([
                            html.H6("No Investment Data Available",
                                    className="text-center text-muted"),
                            html.P("Upload investment data to see optimal " +
                                   "scheduling recommendations",
                                   className="text-center text-muted mb-0")
                        ], id="investment-schedule-content",
                            className="py-4")
                    ])
                ])
            ], width=6),

            # Right Column: Savings Projections
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H5("Savings Projections",
                                           className="mb-0")),
                    dbc.CardBody([
                        html.Div([
                            html.H6("No Calculation Results",
                                    className="text-center text-muted"),
                            html.P("Complete data input to see savings " +
                                   "projections and ROI analysis",
                                   className="text-center text-muted mb-0")
                        ], id="savings-projections-content",
                            className="py-4")
                    ])
                ])
            ], width=6)
        ])
    ], className="p-4")


def _create_investment_reports_tab():
    """Tab 4: Investment Reports"""

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
                    dbc.CardHeader(html.H5("Report Configuration",
                                           className="mb-0")),
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
                                         "value": "implementation_timeline"}
                                    ],
                                    placeholder="Select report type...",
                                    className="mb-3"
                                )
                            ], width=12)
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
                                html.P("Complete investment analysis to " +
                                       "enable report generation",
                                       className="text-muted small " +
                                       "text-center mt-2")
                            ])
                        ])
                    ])
                ])
            ], width=4),

            # Right Column: Report Preview
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H5("Report Preview",
                                           className="mb-0")),
                    dbc.CardBody([
                        html.Div([
                            html.H6("📄 Report Preview",
                                    className="text-center text-muted"),
                            html.P("Select report type and generate to " +
                                   "see preview here",
                                   className="text-center text-muted mb-4")
                        ], id="report-preview-content", className="py-4")
                    ])
                ])
            ], width=8)
        ])
    ], className="p-4")


# Maintain compatibility with existing imports
create_business_mode_layout = create_business_layout


def _create_investment_modals():
    """Create modal dialogs for each investment type"""

    # Investment type configurations (simplified version)
    investment_configs = {
        "capital": {
            "label": "Capital Equipment & Assets",
            "description": "Equipment investments for operational improvements"
        },
        "process": {
            "label": "Process Improvement",
            "description": "Process optimization and workflow improvements"
        },
        "people": {
            "label": "Human Capital/People",
            "description": "Training, hiring, and human resource investments"
        },
        "maintenance": {
            "label": "Maintenance",
            "description": "Equipment maintenance and reliability improvements"
        },
        "quality": {
            "label": "Quality",
            "description": "Quality control and assurance investments"
        },
        "digital": {
            "label": "Digital Transformation",
            "description": "Technology and digitalization investments"
        },
        "safety": {
            "label": "Safety & Environmental",
            "description": "Safety improvements and environmental compliance"
        },
        "facility": {
            "label": "Facility & Infrastructure",
            "description": "Building, infrastructure, and facility improvements"
        },
        "supply_chain": {
            "label": "Supply Chain & Logistics",
            "description": "Supply chain optimization and logistics improvements"
        }
    }

    modals = []

    for investment_type, config in investment_configs.items():
        modal = dbc.Modal([
            dbc.ModalHeader([
                dbc.ModalTitle(f"Data Upload: {config['label']}")
            ]),
            dbc.ModalBody([
                # Upload Section
                dbc.Card([
                    dbc.CardBody([
                        html.H6("Option 1: Upload File"),
                        dcc.Upload(
                            id=f"upload-{investment_type}",
                            children=html.Div([
                                'Drag and Drop or ',
                                html.A('Select Files')
                            ]),
                            style={
                                'width': '100%',
                                'height': '60px',
                                'lineHeight': '60px',
                                'borderWidth': '1px',
                                'borderStyle': 'dashed',
                                'borderRadius': '5px',
                                'textAlign': 'center',
                                'margin': '10px'
                            },
                            multiple=False
                        ),
                        html.Div(id=f"upload-status-{investment_type}")
                    ])
                ], className="mb-3"),

                # Column Mapping Section
                dbc.Card([
                    dbc.CardBody([
                        html.H6("Column Mapping"),
                        html.P("Map your file columns to required fields:"),
                        html.Div(id=f"column-mapping-{investment_type}")
                    ])
                ], className="mb-3"),

                # Manual Entry Section
                dbc.Card([
                    dbc.CardBody([
                        html.H6("Option 2: Manual Entry"),
                        html.P(config['description']),
                        html.Hr(),

                        # Sample form fields (can be expanded based on investment type)
                        dbc.Row([
                            dbc.Col([
                                dbc.Label("Current Performance Metric"),
                                dbc.Input(
                                    id=f"current-performance-{investment_type}",
                                    type="number",
                                    placeholder="Enter current value..."
                                )
                            ], width=6),
                            dbc.Col([
                                dbc.Label("Target Performance Metric"),
                                dbc.Input(
                                    id=f"target-performance-{investment_type}",
                                    type="number",
                                    placeholder="Enter target value..."
                                )
                            ], width=6)
                        ], className="mb-3"),

                        dbc.Row([
                            dbc.Col([
                                dbc.Label("Annual Volume/Usage"),
                                dbc.Input(
                                    id=f"annual-volume-{investment_type}",
                                    type="number",
                                    placeholder="Enter annual volume..."
                                )
                            ], width=6),
                            dbc.Col([
                                dbc.Label("Cost Per Unit (£)"),
                                dbc.Input(
                                    id=f"unit-cost-{investment_type}",
                                    type="number",
                                    placeholder="Enter unit cost..."
                                )
                            ], width=6)
                        ], className="mb-3")
                    ])
                ])
            ]),
            dbc.ModalFooter([
                dbc.Button("Cancel", id=f"cancel-{investment_type}",
                           color="secondary"),
                dbc.Button("Save Data", id=f"save-{investment_type}",
                           color="primary")
            ])
        ], id=f"modal-{investment_type}", size="xl", is_open=False)

        modals.append(modal)

    return modals
        ], id=f"modal-{investment_type}", size="lg", is_open=False)

        modals.append(modal)

    return modals


def create_investment_type_box(investment_type, investment_config, business_model):
    """Create a clickable box for each investment type."""

    # Check if data is uploaded (placeholder logic)
    data_uploaded = False  # This would be checked against actual data store

    status_color = "success" if data_uploaded else "light"
    status_icon = "✓" if data_uploaded else "📁"

    return dbc.Col([
        dbc.Card([
            dbc.CardBody([
                html.H6(f"{status_icon} {investment_config['label']}",
                        className="card-title"),
                html.P(investment_config['description'],
                       className="card-text small"),
                html.P(f"Status: {'Complete' if data_uploaded else 'Pending'}",
                       className="text-muted small"),
                html.Hr(),
                dbc.Button(
                    "Upload Data" if not data_uploaded else "View/Edit Data",
                    id=f"open-{investment_type}-form",
                    color="primary" if not data_uploaded else "success",
                    size="sm",
                    className="w-100"
                )
            ])
        ], color=status_color, outline=True, className="h-100")
    ], width=4, className="mb-3")
