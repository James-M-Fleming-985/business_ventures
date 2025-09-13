from dash import html, dcc, dash_table
import dash_bootstrap_components as dbc #type: ignore
from datetime import datetime

def create_investment_mgmt_layout():
    """Create the layout for the Investment Management tab"""
    return html.Div([
        html.H2("Department Investments"),
        html.P("Add and manage potential investments for optimization."),
    
        # Investment input form
        html.Div(className="control-panel", children=[
            dbc.Row([
                dbc.Col([
                    html.Div([
                        html.Label("Investment Name:"),
                        dbc.Input(id="investment-mgmt-name-input", type="text", placeholder="Enter investment name...")
                    ])
                ], width=6),
                    
                dbc.Col([
                    html.Label("Investment Type:"),
                    dcc.Dropdown(
                        id='investment-mgmt-type-input',
                        options=[
                            {'label': 'Capital Equipment', 'value': 'capital'},
                            {'label': 'Process Improvement', 'value': 'process'},
                            {'label': 'People/Training', 'value': 'people'},
                            {'label': 'Software/IT', 'value': 'software'},
                            {'label': 'Facility', 'value': 'facility'}
                        ],
                        placeholder="Select type...",
                        clearable=False
                    )
                ], width=6),
            ], className="mb-3"),
                
            dbc.Row([
                dbc.Col([
                    html.Label("Initial Cost (£):"),
                    dbc.Input(
                        id="investment-cost-input", 
                        type="number", 
                        placeholder="Enter cost...", 
                        min=0,
                        pattern=r"[0-9]*",
                        required=True  # Add this to mark it as required
                    ),
                    # Add validation message div here
                    html.Div(id="cost-validation-output", style={"color": "red", "fontSize": "small"})
                ], width=4),
                dbc.Col([
                    html.Label(id="investment-rate-label", children="Annual Savings (£):"),
                    dbc.Input(id="investment-savings-input", type="number", placeholder="Enter projected savings...", min=0)
                ], width=4),
                    
                dbc.Col([
                    html.Label("Implementation Time (months):"),
                    dbc.Input(id="implementation-time-input", type="number", placeholder="Months...", min=1, max=36, value=3)
                ], width=4)
            ], className="mb-3"),

            # Scope of Investment-scope-container radio buttons
            html.Div([
                dbc.Row([
                    dbc.Col([
                        html.Label("Scope of Investment:", className="form-label"),
                    ], width=12),
                    dbc.Col([
                        dbc.RadioItems(
                            id="investment-scope-input",
                            options=[
                                {"label": "Department-wide", "value": "department"},
                                {"label": "Specific Production Line(s)", "value": "line"}
                            ],
                            value="department",
                            inline=True,
                            className="mb-2"
                        )
                    ], width=12),
                    dbc.Col([
                        html.Div([
                            html.Label("Select Production Line(s):", className="form-label mt-2"),
                            dcc.Dropdown(
                                id="production-line-selector",
                                options=[
                                    {"label": "Line 1", "value": "line_1"},
                                    {"label": "Line 2", "value": "line_2"},
                                    {"label": "Line 3", "value": "line_3"},
                                    {"label": "Line 4", "value": "line_4"},
                                    {"label": "Line 5", "value": "line_5"},
                                    {"label": "Line 6", "value": "line_6"}
                                ],
                                multi=True,
                                placeholder="Select affected production line(s)"
                            )
                        ], id="production-line-container", style={"display": "none"})
                    ], width=12)
                ], className="mb-3")
            ], id="investment-scope-container"),

            # Implementation Timeline Fields
            dbc.Row([
                dbc.Col([
                    html.H5("Implementation Timeline", className="mt-3"),
                ], width=12, className="mb-2"),
                dbc.Col([
                    html.Label("Start Date:"),
                    dcc.DatePickerSingle(
                        id="implementation-start-date",
                        min_date_allowed=datetime(2020, 1, 1),
                        max_date_allowed=datetime(2030, 12, 31),
                        initial_visible_month=datetime.today(),
                        placeholder="Select start date",
                        className="w-100"
                    )
                ], width=4),
                dbc.Col([
                    html.Label("End Date:"),
                    dcc.DatePickerSingle(
                        id="implementation-end-date",
                        min_date_allowed=datetime(2020, 1, 1),
                        max_date_allowed=datetime(2030, 12, 31),
                        initial_visible_month=datetime.today(),
                        placeholder="Select end date",
                        className="w-100"
                    )
                ], width=4),
                dbc.Col([
                    html.Label("Status:"),
                    dcc.Dropdown(
                        id="implementation-status",
                        options=[
                            {"label": "Planned", "value": "planned"},
                            {"label": "In Progress", "value": "in_progress"},
                            {"label": "Completed", "value": "completed"},
                            {"label": "Cancelled", "value": "cancelled"}
                        ],
                        placeholder="Select status",
                        value="planned"
                    )
                ], width=4)
            ], className="mb-3"),

            # Capital Equipment Parameters
            html.Div([
                html.H5("Capital Equipment Parameters", className="mt-3"),
                dbc.Row([
                    dbc.Col([
                        html.Label("Current OEE Baseline:"),
                        html.Div([
                            dbc.Row([
                                dbc.Col([
                                    html.Label("Current Availability (%):"),
                                    dbc.Input(id="oee-current-availability-input", type="number", min=0, max=100, step=0.1, value=75)
                                ], width=4),
                                dbc.Col([
                                    html.Label("Current Performance (%):"),
                                    dbc.Input(id="oee-current-performance-input", type="number", min=0, max=100, step=0.1, value=70)
                                ], width=4),
                                dbc.Col([
                                    html.Label("Current Quality (%):"),
                                    dbc.Input(id="oee-current-quality-input", type="number", min=0, max=100, step=0.1, value=90)
                                ], width=4),
                            ]),
                        ], id="oee-current-container")
                    ], width=12),
                ], className="mb-3"),
                dbc.Row([
                    dbc.Col([
                        html.Label("Expected OEE Improvements:"),
                        html.Div([
                            dbc.Row([
                                dbc.Col([
                                    html.Label("Availability Increase (%):"),
                                    dbc.Input(id="oee-availability-improvement-input", type="number", min=0, max=50, step=0.1, value=5)
                                ], width=4),
                                dbc.Col([
                                    html.Label("Performance Increase (%):"),
                                    dbc.Input(id="oee-performance-improvement-input", type="number", min=0, max=50, step=0.1, value=5)
                                ], width=4),
                                dbc.Col([
                                    html.Label("Quality Increase (%):"),
                                    dbc.Input(id="oee-quality-improvement-input", type="number", min=0, max=50, step=0.1, value=2)
                                ], width=4),
                            ]),
                        ], id="oee-improvement-container")
                    ], width=12),
                ], className="mb-3"),
                dbc.Row([
                    dbc.Col([
                        html.Label("Financial Impact Factors:"),
                    ], width=12, className="mb-2"),
                    dbc.Col([
                        html.Div([
                            html.Label("Equipment Hourly Rate (£): "),
                            html.I(
                                id="equipment-rate-help-icon",
                                className="fas fa-question-circle",
                                style={"cursor": "pointer", "margin-left": "5px", "color": "#007bff"}
                            ),
                        ], className="d-flex align-items-center"),
                        dbc.Tooltip(
                            [
                                html.H6("How to Calculate Equipment Hourly Rate:", className="mb-2"),
                                html.P("For Equipment Replacement:", className="mb-1 font-weight-bold"),
                                html.Ul([
                                    html.Li("Energy savings: Annual savings ÷ operating hours"),
                                    html.Li("Maintenance savings: Annual maintenance reduction ÷ operating hours"),
                                    html.Li("Downtime impact: Line hourly value × downtime reduction")
                                ], className="mb-2 pl-3"),
                                html.P("For Production Equipment:", className="mb-1 font-weight-bold"),
                                html.Ul([
                                    html.Li("Production method: Units/hour × value/unit"),
                                    html.Li("Revenue method: Annual revenue ÷ annual hours")
                                ], className="pl-3"),
                                html.Hr(),
                                html.P("Example: £200/hour for equipment generating £200k annually over 1,000 hours", className="mb-0 font-italic")
                            ],
                            target="equipment-rate-help-icon",
                            placement="right",
                            className="equipment-rate-tooltip"
                        ),
                        dbc.Input(id="equipment-hourly-rate-input", type="number", min=0, step=10, value=250)
                    ], width=4),
                    dbc.Col([
                        html.Label("Operating Hours per Year:"),
                        dbc.Input(id="operating-hours-input", type="number", min=0, step=100, value=2000)
                    ], width=4),
                    dbc.Col([
                        html.Label("Maintenance Reduction (%):"),
                        dbc.Input(id="maintenance-reduction-input", type="number", min=0, max=100, step=1, value=10)
                    ], width=4),
                ], className="mb-3"),
            ], id="capital-equipment-params", style={"display": "none"}),

            # Process Improvement specific parameters
            html.Div([
                html.H5("Process Improvement Parameters", className="mt-3"),
                dbc.Row([
                    dbc.Col([
                        html.Label("Current Process Metrics:"),
                    ], width=12, className="mb-2"),
                    dbc.Col([
                        html.Label("Current Cycle Time (min):"),
                        dbc.Input(id="current-cycle-time-input", type="number", min=0, step=0.1, value=5)
                    ], width=4),
                    dbc.Col([
                        html.Label("Current Downtime (%):"),
                        dbc.Input(id="current-downtime-input", type="number", min=0, max=100, step=0.1, value=15)
                    ], width=4),
                    dbc.Col([
                        html.Label("Current Defect Rate (%):"),
                        dbc.Input(id="current-defect-rate-input", type="number", min=0, max=100, step=0.1, value=3)
                    ], width=4),
                ], className="mb-3"),
                dbc.Row([
                    dbc.Col([
                        html.Label("Expected Process Improvements:"),
                    ], width=12, className="mb-2"),
                    dbc.Col([
                        html.Label("Cycle Time Reduction (%):"),
                        dbc.Input(id="cycle-time-reduction-input", type="number", min=0, max=50, step=0.1, value=10)
                    ], width=4),
                    dbc.Col([
                        html.Label("Downtime Reduction (%):"),
                        dbc.Input(id="downtime-reduction-input", type="number", min=0, max=50, step=0.1, value=20)
                    ], width=4),
                    dbc.Col([
                        html.Label("Defect Reduction (%):"),
                        dbc.Input(id="defect-reduction-input", type="number", min=0, max=50, step=0.1, value=30)
                    ], width=4),
                ], className="mb-3"),
                dbc.Row([
                    dbc.Col([
                        html.Label("Financial Impact Factors:"),
                    ], width=12, className="mb-2"),
                    dbc.Col([
                        html.Label("Production Value (£/unit):"),
                        dbc.Input(id="product-value-input", type="number", min=0, step=1, value=100)
                    ], width=4),
                    dbc.Col([
                        html.Label("Annual Production Volume:"),
                        dbc.Input(id="production-volume-input", type="number", min=0, step=100, value=10000)
                    ], width=4),
                    dbc.Col([
                        html.Label("Material Cost per Unit (£):"),
                        dbc.Input(id="material-cost-input", type="number", min=0, step=1, value=20)
                    ], width=4),
                ], className="mb-3"),
            ], id="process-improvement-params", style={"display": "none"}),

            # People/Training Parameters
            html.Div([
                html.H5("People/Training Parameters", className="mt-3"),
                dbc.Row([
                    dbc.Col([
                        html.Label("Current OLE Baseline:"),
                        html.Div([
                            dbc.Row([
                                dbc.Col([
                                    html.Label("Current Labor Efficiency (%):"),
                                    dbc.Input(id="ole-current-efficiency-input", type="number", min=0, max=100, step=0.1, value=70)
                                ], width=6),
                                dbc.Col([
                                    html.Label("Current Process Quality (%):"),
                                    dbc.Input(id="ole-current-quality-input", type="number", min=0, max=100, step=0.1, value=85)
                                ], width=6),
                            ]),
                        ], id="ole-current-container")
                    ], width=12),
                ], className="mb-3"),
                dbc.Row([
                    dbc.Col([
                        html.Label("Expected OLE Improvements:"),
                        html.Div([
                            dbc.Row([
                                dbc.Col([
                                    html.Label("Efficiency Increase (%):"),
                                    dbc.Input(id="ole-efficiency-improvement-input", type="number", min=0, max=50, step=0.1, value=8)
                                ], width=6),
                                dbc.Col([
                                    html.Label("Quality Increase (%):"),
                                    dbc.Input(id="ole-quality-improvement-input", type="number", min=0, max=50, step=0.1, value=5)
                                ], width=6),
                            ]),
                        ], id="ole-improvement-container")
                    ], width=12),
                ], className="mb-3"),
                dbc.Row([
                    dbc.Col([
                        html.Label("Financial Impact Factors:"),
                    ], width=12, className="mb-2"),
                    dbc.Col([
                        html.Label("Average Labor Cost (£/hour):"),
                        dbc.Input(id="labor-hourly-rate-input", type="number", min=0, step=1, value=25)
                    ], width=4),
                    dbc.Col([
                        html.Label("Total Staff Hours per Year:"),
                        dbc.Input(id="staff-hours-input", type="number", min=0, step=100, value=2000)
                    ], width=4),
                    dbc.Col([
                        html.Label("Staff Count:"),
                        dbc.Input(id="staff-count-input", type="number", min=1, step=1, value=10)
                    ], width=4),
                ], className="mb-3"),
            ], id="people-training-params", style={"display": "none"}),
            
            # Efficiency Improvement and buttons
            dbc.Row([
                dbc.Col([
                    # Wrap the existing efficiency input in its container
                    html.Div([
                        html.Label("Efficiency Improvement (%):"),
                        dbc.Input(
                            id="investment-efficiency-input", 
                            type="number", 
                            placeholder="% improvement...", 
                            min=0, 
                            max=100, 
                            value=5
                        )
                    ], id="investment-efficiency-container"),
                ], width=4),
                
                dbc.Col([
                    # Add the new investment lifespan container
                    html.Div([
                        html.Label("Investment Lifespan (years):"),
                        dbc.Input(
                            id="investment-lifespan-input",
                            type="number",
                            min=1,
                            max=30,
                            step=1,
                            value=5
                        )
                    ], id="investment-lifespan-container", style={"display": "none"}),
                ], width=4),
                
                dbc.Col([
                    html.Label("Risk Level:"),
                    dcc.Slider(
                        id='risk-slider',
                        min=1,
                        max=5,
                        step=1,
                        value=3,
                        marks={i: str(i) for i in range(1, 6)},
                    )
                ], width=4),
                
                dbc.Col([
                    html.Button("Add Investment", id="add-investment-button", className="btn btn-primary w-100 mt-4")
                ], width=4)
            ], className="mb-4"),
        ]),
        
        # Table of investments
        html.Div([
            dash_table.DataTable(
                id='investments-table',
                columns=[
                    {'name': 'Name', 'id': 'name'},
                    {'name': 'Type', 'id': 'type'},
                    {'name': 'Cost (£)', 'id': 'cost', 'type': 'numeric', 'format': {'specifier': ',.2f'}},
                    {'name': 'Annual Savings (£)', 'id': 'savings', 'type': 'numeric', 'format': {'specifier': ',.2f'}},
                    {'name': 'ROI', 'id': 'roi', 'type': 'numeric', 'format': {'specifier': '.2%'}},
                    {'name': 'Scope', 'id': 'scope'},
                    {'name': 'Start Date', 'id': 'implementation_start'},
                    {'name': 'End Date', 'id': 'implementation_end'},
                    {'name': 'Status', 'id': 'status'}
                ],
                data=[],
                style_table={'overflowX': 'auto'},
                row_deletable=True,
                style_cell={
                    'textAlign': 'right',
                    'padding': '8px',
                },
                style_header={
                    'background_color': 'rgb(230, 230, 230)',
                    'fontWeight': 'bold'
                },
                style_data_conditional=[
                    {
                        'if': {'row_index': 'odd'},
                        'backgroundColor': 'rgb(248, 248, 248)'
                    }
                ],
                sort_action="native",
            )
        ], className="mb-4"),
        
        # Investment summary metrics
        dbc.Row([
            dbc.Col([
                html.Div([
                    html.H5("Total Investment:"),
                    html.H4(id="total-investment-cost", children="£0")
                ], className="metric-card")
            ], width=4),
            
            dbc.Col([
                html.Div([
                    html.H5("Total Annual Savings:"),
                    html.H4(id="total-annual-savings", children="£0")
                ], className="metric-card")
            ], width=4),
            
            dbc.Col([
                html.Div([
                    html.H5("Average ROI:"),
                    html.H4(id="average-roi", children="0%")
                ], className="metric-card")
            ], width=4)
        ])
    ]),  # End of Investment Management tab
