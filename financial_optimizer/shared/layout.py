from dash import html, dcc
import dash_bootstrap_components as dbc
from dash import dash_table
from dash.dash_table.Format import Format, Scheme
from dash.dash_table import FormatTemplate
from dash_draggable import ResponsiveGridLayout # type: ignore

from shared.components.header import create_header
from modules.data_input.layout.financial_inputs import create_input_tabs
from modules.financial_dashboard.layout.charts import create_chart_section
from modules.financial_dashboard.layout.economic_climate import create_economic_climate_section
from modules.investment_analysis.layout.investment_optimizer import create_investment_optimizer_section
from modules.data_input.layout.financial_inputs import create_budget_control

from datetime import date, datetime  # Add this import at the top of the file

def create_layout():
    """Create the main application layout."""
    return html.Div([
        # External stylesheets
        html.Link(
            rel='stylesheet',
            href='/assets/css/style.css'
        ),
        
        # Application header
        create_header(),
        
        # Main content
        dbc.Container([
            dbc.Tabs([
                # Scenario Analysis tab - no changes needed
                dbc.Tab(label="Scenario Analysis", children=[
                    html.H2("Financial Scenario Analysis"),
                    
                    # ...existing scenario analysis content...
                    dbc.Row([
                        dbc.Col([
                            html.Label("Select Scenarios to Compare:"),
                            dcc.Dropdown(
                                id='scenario-selector',
                                options=[],  # Will be populated based on mode
                                value=['baseline', 'optimistic', 'pessimistic'],
                                multi=True
                            ),
                        ], width=12, className="mb-3"),
                        
                        dbc.Col([
                            html.Button("Run Scenario Analysis", id="run-scenario-button", className="btn btn-primary"),
                        ], width=12, className="mb-3"),
                    ]),
                    
                    # Scenario results section
                    html.Div([
                        html.H4("Scenario Comparison", className="mt-4"),
                        
                        # Tabs for different projection charts
                        dbc.Tabs([
                            dbc.Tab(label="Net Worth/Equity", children=[
                                dcc.Graph(id='scenario-net-worth-chart')
                            ]),
                            dbc.Tab(label="Cash Flow", children=[
                                dcc.Graph(id='scenario-cash-flow-chart')
                            ]),
                            dbc.Tab(label="Revenue", children=[
                                dcc.Graph(id='scenario-revenue-chart')
                            ]),
                            dbc.Tab(label="EBITDA/Profit", children=[
                                dcc.Graph(id='scenario-ebitda-chart')
                            ])
                        ]),
                        
                        # Scenario summary table
                        html.H4("Scenario Summary", className="mt-4"),
                        dash_table.DataTable(
                            id='scenario-summary-table',
                            columns=[
                                {"name": "Scenario", "id": "name"},
                                {"name": "Final Value", "id": "final_net_worth", "type": "numeric", "format": {"specifier": ",.2f"}},
                                {"name": "Final Cash Flow", "id": "final_cash_flow", "type": "numeric", "format": {"specifier": ",.2f"}},
                                {"name": "Avg Growth", "id": "avg_growth_rate", "type": "numeric", "format": {"specifier": ".2%"}},
                                {"name": "Min Cash Flow", "id": "min_cash_flow", "type": "numeric", "format": {"specifier": ",.2f"}},
                                {"name": "Max Cash Flow", "id": "max_cash_flow", "type": "numeric", "format": {"specifier": ",.2f"}}
                            ],
                            data=[],
                            style_cell={'textAlign': 'right'},
                            sort_action='native'
                        ),
                        
                        # Description of selected scenario
                        html.Div(id="scenario-description", className="mt-3")
                        
                    ], id='scenario-results', style={'display': 'none'})
                ], id='scenario-analysis-tab'),

                # Financial Overview tab with draggable components
                dbc.Tab(label="Financial Overview", children=[
                    html.Div([
                        # Control panel at the top
                        html.Div([
                            html.H4("Budget Allocation", className="mb-3"),
                            create_budget_control(),
                            html.Div(id='mode-specific-metrics', className="mt-4"),
                        ], className="control-panel mb-4"),
                        
                        # Draggable dashboard layout
                        html.Div([
                            html.H4("Financial Dashboard", className="mb-3"),
                            html.Button("Add New Chart", id="add-chart-btn", className="btn btn-primary mb-3 me-2"),
                            html.Button("Reset Layout", id="reset-layout-btn", className="btn btn-outline-secondary mb-3"),
                            
                            # Responsive grid layout for draggable components
                            ResponsiveGridLayout(
                                id='financial-dashboard-grid',
                                layouts={
                                    'lg': [
                                        {'i': 'budget-allocation', 'x': 0, 'y': 0, 'w': 8, 'h': 6},
                                        {'i': 'savings-over-time', 'x': 8, 'y': 0, 'w': 4, 'h': 6},
                                        {'i': 'metrics-panel', 'x': 0, 'y': 6, 'w': 12, 'h': 2},
                                        {'i': 'overview-chart', 'x': 0, 'y': 8, 'w': 12, 'h': 6},
                                    ]
                                },
                                gridCols={'lg': 12, 'md': 10, 'sm': 6, 'xs': 4, 'xxs': 2},
                                # Fix margin to be an array of [x, y] instead of a single number
                                margin=[10, 10],
                                # Fix containerPadding to be an array of [x, y] instead of a single number
                                containerPadding=[10, 10],
                                isDraggable=True,
                                isResizable=True,
                                children=[
                                    # Budget allocation chart
                                    html.Div([
                                        html.Div([
                                            html.H5([
                                                html.Span("Budget Allocation"),
                                                html.I(className="fas fa-times close-btn", id="close-budget-allocation")
                                            ], className="d-flex justify-content-between align-items-center"),
                                            dbc.Row([
                                                dbc.Col([
                                                    dcc.Graph(id='budget-allocation-chart', style={"height": "350px"})
                                                ], width=9),
                                                dbc.Col([
                                                    html.H6("Prioritization Criteria", className="mb-2"),
                                                    dbc.Checklist(
                                                        id="prioritization-criteria",
                                                        options=[
                                                            {"label": "Return on Investment (ROI)", "value": "roi"},
                                                            {"label": "Risk Level (Lower Better)", "value": "risk"},
                                                            {"label": "Implementation Time", "value": "time"},
                                                            {"label": "Efficiency Improvement", "value": "efficiency"},
                                                            {"label": "Annual Savings", "value": "savings"}
                                                        ],
                                                        value=["roi", "risk"],
                                                        inline=False,
                                                        switch=True,
                                                    ),
                                                    html.Hr(),
                                                    html.H6("Display Options", className="mb-2 mt-3"),
                                                    dbc.Checklist(
                                                        id="display-options",
                                                        options=[
                                                            {"label": "Show Budget Line", "value": "budget_line"},
                                                            {"label": "Show Cumulative Total", "value": "cumulative"},
                                                            {"label": "Show Unselected Investments", "value": "unselected"}
                                                        ],
                                                        value=["budget_line", "cumulative"],
                                                        inline=False,
                                                        switch=True,
                                                    ),
                                                    html.Div(id="budget-utilization-display", className="mt-3")
                                                ], width=3),
                                            ])
                                        ], className="dashboard-card h-100")
                                    ], key='budget-allocation'),
                                    
                                    # Savings over time chart
                                    html.Div([
                                        html.Div([
                                            html.H5([
                                                html.Span("Investment Savings Over Time"),
                                                html.I(className="fas fa-times close-btn", id="close-savings-chart")
                                            ], className="d-flex justify-content-between align-items-center"),
                                            dcc.Graph(id="cumulative-savings-chart", style={"height": "350px"})
                                        ], className="dashboard-card h-100")
                                    ], key='savings-over-time'),
                                    
                                    # Metrics panel
                                    html.Div([
                                        html.Div([
                                            dbc.Row([
                                                dbc.Col([
                                                    html.Div([
                                                        html.H6(id='worth-metric-title', children="Department Contribution"),
                                                        html.Div([
                                                            html.Small("Current:"),
                                                            html.H5(id='current-net-worth', children="£0.00")
                                                        ], className="d-flex justify-content-between"),
                                                        html.Div([
                                                            html.Small("Projected:"),
                                                            html.H5(id='projected-net-worth', children="£0.00")
                                                        ], className="d-flex justify-content-between"),
                                                    ], className="dashboard-metric")
                                                ], width=4),
                                                
                                                dbc.Col([
                                                    html.Div([
                                                        html.H6(id='flow-metric-title', children="Departmental Savings"),
                                                        html.Div([
                                                            html.Small("Current Annual:"),
                                                            html.H5(id='current-cash-flow', children="£0.00")
                                                        ], className="d-flex justify-content-between"),
                                                        html.Div([
                                                            html.Small("Projected Annual:"),
                                                            html.H5(id='projected-cash-flow', children="£0.00")
                                                        ], className="d-flex justify-content-between"),
                                                    ], className="dashboard-metric")
                                                ], width=4),
                                                
                                                dbc.Col([
                                                    html.Div([
                                                        html.H6(id='spend-metric-title', children="Departmental Spending"),
                                                        html.Div([
                                                            html.Small("Current:"),
                                                            html.H5(id='current-spending', children="£0.00")
                                                        ], className="d-flex justify-content-between"),
                                                        html.Div([
                                                            html.Small("Projected:"),
                                                            html.H5(id='projected-spending', children="£0.00")
                                                        ], className="d-flex justify-content-between"),
                                                        html.Div([
                                                            html.Small("Optimization:"),
                                                            html.H5(id='spending-optimization', children="£0.00")
                                                        ], className="d-flex justify-content-between"),
                                                    ], className="dashboard-metric")
                                                ], width=4),
                                            ])
                                        ], className="dashboard-card h-100")
                                    ], key='metrics-panel'),
                                    
                                    # Overview chart
                                    html.Div([
                                        html.Div([
                                            html.H5([
                                                html.Span("Financial Overview"),
                                                html.I(className="fas fa-times close-btn", id="close-overview-chart")
                                            ], className="d-flex justify-content-between align-items-center"),
                                            dcc.Graph(id='overview-chart', style={"height": "350px"})
                                        ], className="dashboard-card h-100")
                                    ], key='overview-chart'),
                                ]
                            ),
                            
                            # Store for saving dashboard layout configuration
                            dcc.Store(id='dashboard-layout-store', storage_type='local')
                        ], className="dashboard-container"),
                    ])
                ]),
                
                # Investment Management tab
                dbc.Tab(label="Investment Management", children=[
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
                
                # Projection Charts tab
                dbc.Tab(label="Projection Charts", children=[
                    create_chart_section()
                ]),
                
                # Financial Statements tab
                dbc.Tab(label="Financial Statements", children=[
                    html.H2("Financial Statements"),
                    html.P("Select a statement to view:"),
                    dbc.RadioItems(
                        id='statement-selector',
                        options=[
                            {'label': 'Income Statement', 'value': 'income'},
                            {'label': 'Balance Sheet', 'value': 'balance'},
                            {'label': 'Cash Flow Statement', 'value': 'cash'}
                        ],
                        value='income',
                        inline=True,
                        className="mb-3"
                    ),
                    html.Div(id='financial-statement-container')
                ]),
                
                # Data Input tab
                dbc.Tab(label="Data Input", children=[
                    create_input_tabs()
                ]),

                # Investment Optimizer tab
                dbc.Tab(label="Investment Optimizer", children=[
                    create_investment_optimizer_section()
                ], id='investment-optimizer-tab'),
                
                # Investment Analysis tab
                dbc.Tab(label="Investment Analysis", children=[
                    html.H2("Investment Analysis"),
                    
                    # Investment performance metrics
                    dbc.Row([
                        dbc.Col([
                            html.Div([
                                html.H4("Return on Investment (ROI)"),
                                html.Div([
                                    html.P("5-Year ROI:"),
                                    html.H3(id='roi-metric', children="0.0%")
                                ]),
                            ], className="metric-card")
                        ], width=4),
                        
                        dbc.Col([
                            html.Div([
                                html.H4("Internal Rate of Return (IRR)"),
                                html.Div([
                                    html.P("5-Year IRR:"),
                                    html.H3(id='irr-metric', children="0.0%")
                                ]),
                            ], className="metric-card")
                        ], width=4),
                        
                        dbc.Col([
                            html.Div([
                                html.H4("Payback Period"),
                                html.Div([
                                    html.P("Months to recover investment:"),
                                    html.H3(id='payback-metric', children="N/A")
                                ]),
                            ], className="metric-card")
                        ], width=4),
                    ]),
                
                    # Investment comparison
                    html.Div([
                        html.H4("Investment Comparison", className="mt-4"),
                        
                        dbc.Row([
                            dbc.Col([
                                html.Label("Compare with:"),
                                dcc.Dropdown(
                                    id='alternative-investment-type',
                                    options=[
                                        {'label': 'No Investment (Baseline)', 'value': 'none'},
                                        {'label': 'Cash/Working Capital', 'value': 'cash'},
                                        {'label': 'Equipment/Machinery', 'value': 'equipment'},
                                        {'label': 'Property/Facilities', 'value': 'property'},
                                        {'label': 'Research & Development', 'value': 'rd'},
                                        {'label': 'Marketing/Brand', 'value': 'marketing'},
                                        {'label': 'IT/Software', 'value': 'it'},
                                        {'label': 'Training/Human Capital', 'value': 'training'},
                                        {'label': 'New Staff Onboarding', 'value': 'staffing'}
                                    ],
                                    value='none',
                                    clearable=False
                                )
                            ], width=6),
                        
                            dbc.Col([
                                html.Label("Alternative Rate (%):"),
                                dbc.Input(
                                    id='alternative-rate-input',
                                    type='number',
                                    min=0,
                                    max=100,
                                    step=0.1,
                                    value=3.0,
                                    placeholder="Enter rate..."
                                )
                            ], width=6),
                        ]),
                    
                        html.Div(id='investment-comparison-chart-container', className="mt-4", children=[
                            dcc.Graph(id='investment-comparison-chart')
                        ])
                    ], className="control-panel mt-4")
                ])
            ], id="main-tabs", className="mt-4"),  # End of tabs
            
            # Store components
            dcc.Store(id='financial-data-store', storage_type='local'),
            dcc.Store(id='projection-results-store', storage_type='local'),
            dcc.Store(id='alternative-projection-store', storage_type='local'),
            dcc.Store(id='investments-store', data=[], storage_type='local'),  # For investment list
            dcc.Store(id='mode-specific-data', storage_type='local'),
            
            # Error management section
            html.Div([
                html.H5("Error Management", className="mt-4"),
                html.Button("Show All Errors", id="show-errors-btn", className="btn btn-danger me-2"),
                html.Button("Clear Errors", id="clear-errors-btn", className="btn btn-secondary"),
                html.Div(id="error-collection-display", className="mt-3", style={
                    "whiteSpace": "pre-wrap", 
                    "fontFamily": "monospace"
                })
            ], className="mt-5 mb-3", style={"borderTop": "1px solid #dee2e6", "paddingTop": "20px"})
        ], fluid=True),  # Add fluid=True parameter here
    ])  # End of main Div