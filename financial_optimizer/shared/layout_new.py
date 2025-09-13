from dash import html, dcc
import dash_bootstrap_components as dbc
from dash import dash_table

# Import use case configuration
from core.config import get_current_use_case, get_config_for_use_case


# Create minimal layouts to avoid import issues
def create_minimal_header():
    """Create the original simple header."""
    return html.Div(
        [html.H1("Financial Optimizer", className="text-center py-3"), html.Hr()]
    )


def create_minimal_input_tabs():
    return html.Div(
        [
            # Basic financial input form
            html.Div(
                [
                    html.H4("Quick Financial Data Entry"),
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    html.Label("Monthly Revenue (£):"),
                                    dcc.Input(
                                        id="monthly-revenue",
                                        type="number",
                                        value=150000,
                                        className="form-control",
                                    ),
                                ],
                                width=6,
                            ),
                            dbc.Col(
                                [
                                    html.Label("Monthly Expenses (£):"),
                                    dcc.Input(
                                        id="monthly-expenses",
                                        type="number",
                                        value=120000,
                                        className="form-control",
                                    ),
                                ],
                                width=6,
                            ),
                        ],
                        className="mb-3",
                    ),
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    html.Label("Current Assets (£):"),
                                    dcc.Input(
                                        id="current-assets",
                                        type="number",
                                        value=500000,
                                        className="form-control",
                                    ),
                                ],
                                width=6,
                            ),
                            dbc.Col(
                                [
                                    html.Label("Current Liabilities (£):"),
                                    dcc.Input(
                                        id="current-liabilities",
                                        type="number",
                                        value=200000,
                                        className="form-control",
                                    ),
                                ],
                                width=6,
                            ),
                        ],
                        className="mb-3",
                    ),
                    dbc.Button(
                        "Calculate Projections",
                        id="calculate-button",
                        color="primary",
                        className="mt-3",
                    ),
                ]
            ),
            html.Div(id="data-input-content"),
        ]
    )


def create_minimal_chart_section():
    """Create chart section with use case-aware titles."""
    try:
        current_use_case = get_current_use_case()
        
        # Use case specific chart titles
        chart_titles = {
            "business": "Annual Savings (£)",
            "personal": "Net Worth Projection (5 Years)", 
            "charity": "Donation Impact Over Time",
            "non_profit": "Grant Funding Projection"
        }
        
        chart_title = chart_titles.get(current_use_case.value, "Financial Projection")
        
    except:
        # Fallback if use case system isn't working
        chart_title = "Net Worth Projection (5 Years)"
    return html.Div(
        [
            html.H2("Financial Dashboard"),
            # Key metrics row
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.Div(
                                [
                                    html.H5("Net Worth"),
                                    html.H3(
                                        id="net-worth-metric",
                                        children="£300,000",
                                        className="text-primary",
                                    ),
                                ],
                                className="text-center p-3 border rounded",
                            )
                        ],
                        width=3,
                    ),
                    dbc.Col(
                        [
                            html.Div(
                                [
                                    html.H5("Monthly Cash Flow"),
                                    html.H3(
                                        id="cash-flow-metric",
                                        children="£30,000",
                                        className="text-success",
                                    ),
                                ],
                                className="text-center p-3 border rounded",
                            )
                        ],
                        width=3,
                    ),
                    dbc.Col(
                        [
                            html.Div(
                                [
                                    html.H5("Growth Rate"),
                                    html.H3(
                                        id="growth-rate-metric",
                                        children="4.2%",
                                        className="text-info",
                                    ),
                                ],
                                className="text-center p-3 border rounded",
                            )
                        ],
                        width=3,
                    ),
                    dbc.Col(
                        [
                            html.Div(
                                [
                                    html.H5("Investment ROI"),
                                    html.H3(
                                        id="investment-roi-metric",
                                        children="12.5%",
                                        className="text-warning",
                                    ),
                                ],
                                className="text-center p-3 border rounded",
                            )
                        ],
                        width=3,
                    ),
                ],
                className="mb-4",
            ),
            # Chart placeholders
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.H4("Financial Projections"),
                            dcc.Graph(
                                id="financial-projection-chart",
                                figure={
                                    "data": [
                                        {
                                            "x": ["Jan", "Feb", "Mar", "Apr", "May"],
                                            "y": [10000, 11500, 12200, 13800, 15000],
                                            "type": "scatter",
                                            "mode": "lines+markers",
                                            "name": "Annual Savings" if current_use_case.value == "business" else "Net Worth",
                                            "line": {"color": "#007bff", "width": 3},
                                            "marker": {"size": 8, "color": "#007bff"},
                                            "hovertemplate": "<b>%{fullData.name}</b><br>" +
                                                           "Date: %{x}<br>" +
                                                           "Cash Value: £%{y:,.0f}<br>" +
                                                           "Metrics Used:<br>" +
                                                           "• Revenue Growth: +15%<br>" +
                                                           "• Cost Reduction: -8%<br>" +
                                                           "• Efficiency Gains: +12%<br>" +
                                                           "<extra></extra>",
                                            "hoverlabel": {
                                                "bgcolor": "white",
                                                "bordercolor": "#007bff",
                                                "font": {"size": 12, "color": "#333"}
                                            }
                                        }
                                    ],
                                    "layout": {
                                        "title": {
                                            "text": chart_title,
                                            "font": {"size": 16, "color": "#333"}
                                        },
                                        "xaxis": {
                                            "title": "Date",
                                            "titlefont": {"size": 14, "color": "#333"},
                                            "tickfont": {"size": 12, "color": "#333"}
                                        },
                                        "yaxis": {
                                            "title": "Amount (£)",
                                            "titlefont": {"size": 14, "color": "#333"},
                                            "tickfont": {"size": 12, "color": "#333"},
                                            "tickformat": "£,.0f"
                                        },
                                        "showlegend": True,
                                        "legend": {"x": 0, "y": 1, "font": {"size": 12}},
                                        "margin": {"l": 60, "r": 20, "t": 50, "b": 60},
                                        "plot_bgcolor": "white",
                                        "paper_bgcolor": "white",
                                        "hovermode": "x unified"
                                    },
                                },
                            ),
                        ],
                        width=12,
                    )
                ]
            ),
            html.Div(id="chart-content"),
        ]
    )


def create_minimal_investment_mgmt():
    return html.Div(
        [
            html.H2("Investment Management"),
            # Basic investment input form
            html.Div(
                [
                    html.H4("Add Investment"),
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    html.Label("Investment Name:"),
                                    dcc.Input(
                                        id="investment-name",
                                        type="text",
                                        placeholder="Enter investment name...",
                                        className="form-control",
                                    ),
                                ],
                                width=6,
                            ),
                            dbc.Col(
                                [
                                    html.Label("Investment Type:"),
                                    dcc.Dropdown(
                                        id="investment-type",
                                        options=[
                                            {
                                                "label": "Equipment",
                                                "value": "equipment",
                                            },
                                            {"label": "Software", "value": "software"},
                                            {"label": "Training", "value": "training"},
                                            {"label": "Property", "value": "property"},
                                        ],
                                        placeholder="Select type...",
                                        className="mb-3",
                                    ),
                                ],
                                width=6,
                            ),
                        ],
                        className="mb-3",
                    ),
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    html.Label("Cost (£):"),
                                    dcc.Input(
                                        id="investment-cost",
                                        type="number",
                                        placeholder="Enter cost...",
                                        className="form-control",
                                    ),
                                ],
                                width=6,
                            ),
                            dbc.Col(
                                [
                                    html.Label("Expected Annual Savings (£):"),
                                    dcc.Input(
                                        id="investment-savings",
                                        type="number",
                                        placeholder="Enter savings...",
                                        className="form-control",
                                    ),
                                ],
                                width=6,
                            ),
                        ],
                        className="mb-3",
                    ),
                    dbc.Button(
                        "Add Investment",
                        id="add-investment",
                        color="success",
                        className="mt-3",
                    ),
                ]
            ),
            # Investment metrics display
            html.Div(
                [
                    html.H4("Investment Metrics", className="mt-4"),
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    html.H5("ROI:"),
                                    html.H4(
                                        id="roi-display",
                                        children="0%",
                                        className="text-primary",
                                    ),
                                ],
                                width=4,
                            ),
                            dbc.Col(
                                [
                                    html.H5("Payback Period:"),
                                    html.H4(
                                        id="payback-display",
                                        children="0 years",
                                        className="text-success",
                                    ),
                                ],
                                width=4,
                            ),
                            dbc.Col(
                                [
                                    html.H5("Total Investment:"),
                                    html.H4(
                                        id="total-investment",
                                        children="£0",
                                        className="text-info",
                                    ),
                                ],
                                width=4,
                            ),
                        ]
                    ),
                ]
            ),
            html.Div(id="investment-mgmt-content"),
        ]
    )


def create_minimal_investment_analysis():
    return html.Div(
        [
            html.H2("Investment Analysis & Scenario Planning"),
            html.P("Investment analysis and scenario tools will be displayed here."),
            html.Div(id="investment-analysis-content"),
        ]
    )


def create_financial_statements_layout():
    return html.Div(
        [
            html.H2("Financial Statements"),
            html.P("Financial statements will be displayed here."),
            html.Div(id="financial-statements-content"),
        ]
    )


def create_use_case_aware_tabs():
    """Create tabs based on current use case configuration."""
    # Get current use case and configuration
    current_use_case = get_current_use_case()
    config = get_config_for_use_case(current_use_case)
    
    # Define all available tabs that match your existing modules
    all_tabs = {
        "data_input": {
            "label": "Data Input",
            "content": create_minimal_input_tabs(),
            "id": "data-input-tab"
        },
        "dashboard": {  # This matches the config
            "label": "Financial Dashboard", 
            "content": create_minimal_chart_section(),
            "id": "financial-dashboard-tab"
        },
        "financial_dashboard": {  # Alternative mapping
            "label": "Financial Dashboard", 
            "content": create_minimal_chart_section(),
            "id": "financial-dashboard-tab"
        },
        "investment_mgmt": {
            "label": "Investment Management",
            "content": create_minimal_investment_mgmt(),
            "id": "investment-mgmt-tab"
        },
        "investment_analysis": {
            "label": "Investment Analysis",
            "content": create_minimal_investment_analysis(),
            "id": "investment-analysis-tab"
        },
        "financial_statements": {
            "label": "Financial Statements",
            "content": create_financial_statements_layout(),
            "id": "financial-statements-tab"
        },
        "market_dashboard": {
            "label": "Market Dashboard",
            "content": html.Div([
                html.H2("Market Analysis"),
                html.P(f"Market data and analysis tools for {current_use_case.value} use case."),
                html.Div([
                    html.H5("Current Configuration:"),
                    html.Ul([
                        html.Li(f"Use Case: {current_use_case.value.title()}"),
                        html.Li(f"Features: {', '.join(config.enabled_features)}"),
                        html.Li(f"Data Sources: {', '.join(config.data_sources)}"),
                    ])
                ])
            ]),
            "id": "market-dashboard-tab"
        },
        "market_analysis": {  # Alternative mapping
            "label": "Market Analysis",
            "content": html.Div([
                html.H2("Market Analysis"),
                html.P(f"Market analysis for {current_use_case.value} use case."),
            ]),
            "id": "market-analysis-tab"
        },
        "reports": {
            "label": "Reports",
            "content": html.Div([
                html.H2("Reports"),
                html.P(f"Report generation for {current_use_case.value} use case."),
            ]),
            "id": "reports-tab"
        },
        "planning": {
            "label": "Planning",
            "content": html.Div([
                html.H2("Planning"),
                html.P(f"Planning tools for {current_use_case.value} use case."),
            ]),
            "id": "planning-tab"
        }
    }
    
    print(f"🔍 Creating tabs for use case: {current_use_case.value}")
    print(f"🔍 Tab layout from config: {config.tab_layout}")
    
    # Create tabs based on the current use case configuration
    tabs = []
    for tab_id in config.tab_layout:
        if tab_id in all_tabs:
            tab_config = all_tabs[tab_id]
            tabs.append(
                dbc.Tab(
                    label=tab_config["label"],
                    children=[tab_config["content"]],
                    id=tab_config["id"],
                )
            )
            print(f"✅ Added tab: {tab_config['label']}")
        else:
            print(f"❌ Tab not found: {tab_id}")
    
    return tabs


def create_layout():
    """Create the main application layout aligned with modular structure."""
    return html.Div(
        [
            # External stylesheets
            html.Link(rel="stylesheet", href="/assets/css/style.css"),
            # Application header
            create_minimal_header(),
            # Main content
            dbc.Container(
                [
                    dbc.Tabs(
                        create_use_case_aware_tabs(),
                        id="main-tabs",
                        className="mb-4",
                    ),
                    # Error collection and data stores
                    html.Div(
                        [
                            html.H4("Application Status"),
                            dbc.Row(
                                [
                                    dbc.Col(
                                        [
                                            html.Button(
                                                "Show All Errors",
                                                id="show-errors-btn",
                                                className="btn btn-danger me-2",
                                            ),
                                            html.Button(
                                                "Clear Errors",
                                                id="clear-errors-btn",
                                                className="btn btn-warning me-2",
                                            ),
                                            html.Button(
                                                "Export Data",
                                                id="export-data-btn",
                                                className="btn btn-success",
                                            ),
                                        ],
                                        width=12,
                                    ),
                                ]
                            ),
                            html.Div(
                                id="error-collection-display",
                                className="mt-3",
                                style={
                                    "backgroundColor": "#f8f9fa",
                                    "padding": "15px",
                                    "border": "1px solid #dee2e6",
                                    "borderRadius": "5px",
                                    "maxHeight": "300px",
                                    "overflowY": "auto",
                                },
                            ),
                        ],
                        className="mt-4",
                    ),
                ],
                fluid=True,
            ),
            # Data stores - keep all existing stores for compatibility
            dcc.Store(id="financial-data-store"),
            dcc.Store(id="projection-results-store"),
            dcc.Store(id="investments-store"),
            dcc.Store(id="dashboard-layout-store"),
            dcc.Store(id="portfolio-data-store"),
            dcc.Store(id="app-mode-store"),
            # Interval for updates
            dcc.Interval(id="interval-component", interval=30000, n_intervals=0),
        ]
    )
