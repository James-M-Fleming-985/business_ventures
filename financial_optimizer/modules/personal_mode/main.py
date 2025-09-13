#!/usr/bin/env python3
"""
Personal Mode Module - Subscription Add-on for Financial Optimizer
Implements portfolio management functionality for Standard tier subscribers.
"""

from dash import html, dcc, Input, Output, State, callback_context, no_update
import dash_bootstrap_components as dbc
from modules.market_dashboard.layout.market_dashboard import create_market_dashboard_layout
from modules.personal_mode.data_persistence import user_data_manager


def create_allocation_sliders(selected_investment_types):
    """Dynamic allocation sliders based on selected investment types"""
    if not selected_investment_types:
        return html.Div("Select investment types above to configure allocation.", className="text-muted")

    sliders = []
    investment_labels = {
        'stocks': '📈 Stocks',
        'bonds': '🏛️ Bonds',
        'etfs': '📊 ETFs',
        'mutual_funds': '🎯 Mutual Funds',
        'real_estate': '🏠 Real Estate',
        'crypto': '₿ Cryptocurrency',
        'retirement': '🏦 Retirement',
        'savings': '💰 Savings'
    }

    for inv_type in selected_investment_types:
        slider_div = html.Div([
            html.Label(
                f"{investment_labels.get(inv_type, inv_type)} (%):", className="fw-bold mb-2"),
            dcc.Slider(
                id=f"allocation-{inv_type}-slider",
                min=0, max=100, step=1, value=0,
                marks={i: str(i) for i in range(0, 101, 20)},
                tooltip={"placement": "bottom", "always_visible": True}
            )
        ], className="mb-3")
        sliders.append(slider_div)

    return sliders


def create_personal_mode_layout():
    """Comprehensive Personal Mode Layout with all tabs implemented"""
    return dbc.Tabs([
        # Financial Dashboard Tab - Primary Command Center
        dbc.Tab(label="Financial Dashboard", children=[
            create_financial_dashboard_layout()
        ]),

        # Investment Management Tab - Existing Implementation
        dbc.Tab(label="Investment Management", children=[
            create_investment_management_layout()
        ]),

        # Market Dashboard Tab - Real-time Market Monitoring
        dbc.Tab(label="Market Dashboard", children=[
            create_market_dashboard_layout()
        ]),

        # Analysis Tab - Mathematical Modeling Engine
        dbc.Tab(label="Analysis", children=[
            create_analysis_tab_layout()
        ]),

        # Data Input Tab - Document Processing and Cash Flow
        dbc.Tab(label="Data Input", children=[
            create_data_input_tab_layout()
        ]),

        # Data Management Tab - Versioning, Backup, and History
        dbc.Tab(label="Data Management", children=[
            create_data_management_layout()
        ]),

        # Subscription Management - Account and Billing
        dbc.Tab(label="Account", children=[
            create_subscription_management_layout()
        ])
    ])


def create_financial_dashboard_layout():
    """Financial Dashboard - Enhanced 8/4 Layout with Control Panel (✅ COMPLETED August 1, 2025)"""
    return html.Div([
        # Hidden data store for financial data
        dcc.Store(id='financial-data-store', data={}),
        
        # Header with Subscription Status
        dbc.Row([
            dbc.Col([
                html.H3("Financial Overview", className="mb-3"),
                dbc.Alert([
                    html.I(className="fas fa-crown me-2"),
                    "Standard Subscription Active - ",
                    html.Strong("Real-time Financial Modeling")
                ], color="success", className="mb-4")
            ], width=12)
        ]),

        # Enhanced 8/4 Layout: Chart (8 columns) | Control Panel (4 columns)
        dbc.Row([
            # Chart Section (8 columns)
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H5("📈 Financial Projection Chart", className="mb-0 d-inline"),
                        html.Small(" (Assets, Liabilities, Cash Flow, Net Worth)", className="text-muted ms-2"),
                        dbc.ButtonGroup([
                            dbc.Button("1Y", id="range-1y", size="sm", outline=True),
                            dbc.Button("5Y", id="range-5y", size="sm", outline=True, active=True),
                            dbc.Button("10Y", id="range-10y", size="sm", outline=True),
                            dbc.Button("30Y", id="range-30y", size="sm", outline=True)
                        ], className="float-end")
                    ]),
                    dbc.CardBody([
                        dcc.Graph(
                            id="enhanced-financial-projection-chart",
                            config={'displayModeBar': False},
                            style={"height": "500px"}
                        )
                    ])
                ])
            ], width=8),

            # Control Panel Section (4 columns) 
            dbc.Col([
                create_financial_control_panel()
            ], width=4)
        ], className="mb-4"),

        # Summary Stats Row
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("Current Financial Position", className="card-title mb-3"),
                        dbc.Row([
                            dbc.Col([
                                html.Small("Net Worth:", className="text-muted"),
                                html.H4(id="current-net-worth-summary", children="£0", className="text-success mb-0")
                            ], width=3),
                            dbc.Col([
                                html.Small("Monthly Cash Flow:", className="text-muted"),
                                html.H4(id="current-cashflow-summary-main", children="£0", className="text-info mb-0")
                            ], width=3),
                            dbc.Col([
                                html.Small("Total Assets:", className="text-muted"),
                                html.H4(id="current-assets-summary", children="£0", className="text-primary mb-0")
                            ], width=3),
                            dbc.Col([
                                html.Small("Total Liabilities:", className="text-muted"),
                                html.H4(id="current-liabilities-summary", children="£0", className="text-danger mb-0")
                            ], width=3)
                        ])
                    ])
                ])
            ], width=12)
        ])
    ], className="p-3")


def create_financial_control_panel():
    """Enhanced Control Panel with 6 Financial Categories - Dual Sliders (✅ COMPLETED August 1, 2025)"""
    return html.Div([
        # Chart Time Range Control Section
        dbc.Card([
            dbc.CardHeader("📊 Chart Time Range Control"),
            dbc.CardBody([
                html.Label("Time Range:", className="fw-bold mb-2"),
                dcc.Slider(
                    id="chart-time-range-slider",
                    min=6, max=360, step=6, value=60,  # Default 5 years
                    marks={
                        6: '6M', 12: '1Y', 60: '5Y', 
                        120: '10Y', 240: '20Y', 360: '30Y'
                    },
                    tooltip={"placement": "bottom", "always_visible": True}
                )
            ])
        ], className="mb-3"),
        
        # Income Section with Current vs Projected
        dbc.Card([
            dbc.CardHeader("💰 Monthly Income"),
            dbc.CardBody([
                # Current vs Projected Display
                dbc.Row([
                    dbc.Col([
                        html.Small("Current Monthly:", className="text-muted"),
                        html.Div([
                            html.Span(id="current-income-display", children="£0", className="fw-bold text-primary"),
                            html.Small(" (net)", className="text-muted ms-1")
                        ])
                    ], width=6),
                    dbc.Col([
                        html.Small("Projected Monthly:", className="text-muted"),
                        html.Div([
                            html.Span(id="projected-income-display", children="£0", className="fw-bold text-success"),
                            html.Small(" (slider)", className="text-muted ms-1")
                        ])
                    ], width=6)
                ], className="mb-3"),
                # Monthly Income Slider (£1,000 - £8,000)
                html.Label("Monthly Net Income:", className="fw-bold mb-2"),
                dcc.Slider(
                    id="income-slider",
                    min=1000, max=8000, step=100, value=3500,
                    marks={1000: '£1K', 3000: '£3K', 5000: '£5K', 8000: '£8K'},
                    tooltip={"placement": "bottom", "always_visible": True},
                    updatemode='drag'  # REAL-TIME UPDATES WHILE DRAGGING
                ),
                # Annual Change Slider (-5% to +10%)
                html.Label("Annual Growth %:", className="fw-bold mb-2 mt-3"),
                dcc.Slider(
                    id="income-growth-slider",
                    min=-5, max=10, step=0.5, value=3,
                    marks={-5: '-5%', 0: '0%', 5: '5%', 10: '10%'},
                    tooltip={"placement": "bottom", "always_visible": True},
                    updatemode='drag'  # REAL-TIME UPDATES WHILE DRAGGING
                ),
                # Impact Display
                html.Div([
                    html.Small("Impact: ", className="text-muted"),
                    html.Span(id="income-impact-display", children="£0 over time", className="fw-bold text-success")
                ], className="mt-2")
            ])
        ], className="mb-3"),
        
        # Housing Section with Current vs Projected
        dbc.Card([
            dbc.CardHeader("🏠 Housing Costs"),
            dbc.CardBody([
                # Current vs Projected Display
                dbc.Row([
                    dbc.Col([
                        html.Small("Current Monthly:", className="text-muted"),
                        html.Div([
                            html.Span(id="current-housing-display", children="£0", className="fw-bold text-primary"),
                            html.Small(" (rent/mortgage)", className="text-muted ms-1")
                        ])
                    ], width=6),
                    dbc.Col([
                        html.Small("Projected Monthly:", className="text-muted"),
                        html.Div([
                            html.Span(id="projected-housing-display", children="£0", className="fw-bold text-warning"),
                            html.Small(" (slider)", className="text-muted ms-1")
                        ])
                    ], width=6)
                ], className="mb-3"),
                # Monthly Housing Slider
                html.Label("Monthly Payment:", className="fw-bold mb-2"),
                dcc.Slider(
                    id="mortgage-slider",
                    min=500, max=3000, step=50, value=1200,
                    marks={500: '£500', 1500: '£1.5K', 3000: '£3K'},
                    tooltip={"placement": "bottom", "always_visible": True},
                    updatemode='drag'  # REAL-TIME UPDATES WHILE DRAGGING
                ),
                # Interest Rate Change Slider
                html.Label("Interest Rate Change %:", className="fw-bold mb-2 mt-3"),
                dcc.Slider(
                    id="mortgage-rate-slider",
                    min=-2, max=5, step=0.25, value=0,
                    marks={-2: '-2%', 0: '0%', 2: '2%', 5: '5%'},
                    tooltip={"placement": "bottom", "always_visible": True},
                    updatemode='drag'  # REAL-TIME UPDATES WHILE DRAGGING
                ),
                html.Div([
                    html.Small("Impact: ", className="text-muted"),
                    html.Span(id="mortgage-impact-display", children="£0 interest effect", className="fw-bold text-info")
                ], className="mt-2")
            ])
        ], className="mb-3"),

        # Utilities Section
        dbc.Card([
            dbc.CardHeader("⚡ Utilities"),
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        html.Small("Current Monthly:", className="text-muted"),
                        html.Div([
                            html.Span(id="current-utilities-display", children="£0", className="fw-bold text-primary")
                        ])
                    ], width=6),
                    dbc.Col([
                        html.Small("Projected Monthly:", className="text-muted"),
                        html.Div([
                            html.Span(id="projected-utilities-display", children="£0", className="fw-bold text-warning")
                        ])
                    ], width=6)
                ], className="mb-3"),
                html.Label("Monthly Utilities:", className="fw-bold mb-2"),
                dcc.Slider(
                    id="utilities-slider",
                    min=50, max=400, step=10, value=150,
                    marks={50: '£50', 150: '£150', 300: '£300', 400: '£400'},
                    tooltip={"placement": "bottom", "always_visible": True},
                    updatemode='drag'  # REAL-TIME UPDATES WHILE DRAGGING
                ),
                html.Label("Annual Inflation %:", className="fw-bold mb-2 mt-3"),
                dcc.Slider(
                    id="utilities-inflation-slider",
                    min=-5, max=15, step=0.5, value=5,
                    marks={-5: '-5%', 0: '0%', 5: '5%', 15: '15%'},
                    tooltip={"placement": "bottom", "always_visible": True},
                    updatemode='drag'  # REAL-TIME UPDATES WHILE DRAGGING
                ),
                html.Div([
                    html.Small("Impact: ", className="text-muted"),
                    html.Span(id="utilities-impact-display", children="£0 cost increase", className="fw-bold text-warning")
                ], className="mt-2")
            ])
        ], className="mb-3"),
        
        # Transport Section
        dbc.Card([
            dbc.CardHeader("🚗 Transport"),
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        html.Small("Current Monthly:", className="text-muted"),
                        html.Div([
                            html.Span(id="current-transport-display", children="£0", className="fw-bold text-primary")
                        ])
                    ], width=6),
                    dbc.Col([
                        html.Small("Projected Monthly:", className="text-muted"),
                        html.Div([
                            html.Span(id="projected-transport-display", children="£0", className="fw-bold text-warning")
                        ])
                    ], width=6)
                ], className="mb-3"),
                html.Label("Monthly Transport:", className="fw-bold mb-2"),
                dcc.Slider(
                    id="transport-slider",
                    min=50, max=800, step=25, value=200,
                    marks={50: '£50', 200: '£200', 500: '£500', 800: '£800'},
                    tooltip={"placement": "bottom", "always_visible": True}
                ),
                html.Label("Annual Change %:", className="fw-bold mb-2 mt-3"),
                dcc.Slider(
                    id="transport-inflation-slider",
                    min=-10, max=10, step=0.5, value=3,
                    marks={-10: '-10%', 0: '0%', 5: '5%', 10: '10%'},
                    tooltip={"placement": "bottom", "always_visible": True}
                ),
                html.Div([
                    html.Small("Impact: ", className="text-muted"),
                    html.Span(id="transport-impact-display", children="£0 transport costs", className="fw-bold text-warning")
                ], className="mt-2")
            ])
        ], className="mb-3"),
        
        # Food Section
        dbc.Card([
            dbc.CardHeader("🍽️ Food & Groceries"),
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        html.Small("Current Monthly:", className="text-muted"),
                        html.Div([
                            html.Span(id="current-food-display", children="£0", className="fw-bold text-primary")
                        ])
                    ], width=6),
                    dbc.Col([
                        html.Small("Projected Monthly:", className="text-muted"),
                        html.Div([
                            html.Span(id="projected-food-display", children="£0", className="fw-bold text-warning")
                        ])
                    ], width=6)
                ], className="mb-3"),
                html.Label("Monthly Food Budget:", className="fw-bold mb-2"),
                dcc.Slider(
                    id="food-slider",
                    min=100, max=800, step=25, value=300,
                    marks={100: '£100', 300: '£300', 500: '£500', 800: '£800'},
                    tooltip={"placement": "bottom", "always_visible": True}
                ),
                html.Label("Annual Food Inflation %:", className="fw-bold mb-2 mt-3"),
                dcc.Slider(
                    id="food-inflation-slider",
                    min=0, max=12, step=0.5, value=4,
                    marks={0: '0%', 4: '4%', 8: '8%', 12: '12%'},
                    tooltip={"placement": "bottom", "always_visible": True}
                ),
                html.Div([
                    html.Small("Impact: ", className="text-muted"),
                    html.Span(id="food-impact-display", children="£0 food costs", className="fw-bold text-warning")
                ], className="mt-2")
            ])
        ], className="mb-3"),
        
        # Enhanced Savings Section with Investment Type Selection
        dbc.Card([
            dbc.CardHeader("💰 Savings & Investments"),
            dbc.CardBody([
                # Current vs Projected Summary
                dbc.Row([
                    dbc.Col([
                        html.Small("Current Total:", className="text-muted"),
                        html.Div([
                            html.Span(id="current-savings-total-display", children="£0", className="fw-bold text-primary")
                        ])
                    ], width=6),
                    dbc.Col([
                        html.Small("Projected Total:", className="text-muted"),
                        html.Div([
                            html.Span(id="projected-savings-total-display", children="£0", className="fw-bold text-success")
                        ])
                    ], width=6)
                ], className="mb-3"),
                # Investment Type Selector
                html.Label("Investment Type:", className="fw-bold mb-2"),
                dbc.RadioItems(
                    id="investment-type-selector",
                    options=[
                        {"label": "Simple Interest", "value": "simple"},
                        {"label": "Compound Interest", "value": "compound"}
                    ],
                    value="compound",
                    inline=True,
                    className="mb-3"
                ),
                # Dual Savings Categories Implementation
                html.H6("🏦 Savings Accounts", className="fw-bold mb-2"),
                html.Label("Total Monthly Savings:", className="fw-bold mb-2"),
                dcc.Slider(
                    id="total-savings-slider",
                    min=0, max=1500, step=50, value=300,
                    marks={0: '£0', 300: '£300', 750: '£750', 1500: '£1.5K'},
                    tooltip={"placement": "bottom", "always_visible": True}
                ),
                html.Label("Average Savings Rate %:", className="fw-bold mb-2 mt-3"),
                dcc.Slider(
                    id="savings-rate-slider",
                    min=0.5, max=6, step=0.25, value=3,
                    marks={0.5: '0.5%', 2: '2%', 4: '4%', 6: '6%'},
                    tooltip={"placement": "bottom", "always_visible": True}
                ),
                html.Hr(),
                html.H6("📈 Investments (Stocks, ETFs, etc.)", className="fw-bold mb-2"),
                html.Label("Total Monthly Investments:", className="fw-bold mb-2"),
                dcc.Slider(
                    id="total-investments-slider",
                    min=0, max=2000, step=50, value=500,
                    marks={0: '£0', 500: '£500', 1000: '£1K', 2000: '£2K'},
                    tooltip={"placement": "bottom", "always_visible": True}
                ),
                html.Label("Expected Return %:", className="fw-bold mb-2 mt-3"),
                dcc.Slider(
                    id="investment-return-slider",
                    min=3, max=12, step=0.5, value=7,
                    marks={3: '3%', 5: '5%', 7: '7%', 10: '10%', 12: '12%'},
                    tooltip={"placement": "bottom", "always_visible": True}
                ),
                # Combined Impact Display with Weighted Averaging
                html.Div([
                    html.Div([
                        html.Small("Total Monthly: ", className="text-muted"),
                        html.Span(id="total-monthly-savings-display", children="£800", className="fw-bold text-primary")
                    ], className="mb-1"),
                    html.Div([
                        html.Small("Weighted Avg Return: ", className="text-muted"),
                        html.Span(id="weighted-return-display", children="5.8%", className="fw-bold text-info")
                    ], className="mb-1"),
                    html.Div([
                        html.Small("Future Value: ", className="text-muted"),
                        html.Span(id="savings-impact-display", children="£0 projected", className="fw-bold text-success")
                    ])
                ], className="mt-2")
            ])
        ], className="mb-3"),
        
        # Financial Impact Summary Panel
        dbc.Card([
            dbc.CardHeader("📊 Current vs Projected Summary"),
            dbc.CardBody([
                html.Div([
                    html.H6("Monthly Cash Flow Impact", className="fw-bold mb-3"),
                    dbc.Row([
                        dbc.Col([
                            html.Small("Current Net Cash Flow:", className="text-muted"),
                            html.Div([
                                html.Span(id="current-cashflow-summary", children="£0", className="fw-bold text-primary")
                            ])
                        ], width=4),
                        dbc.Col([
                            html.Small("Projected Net Cash Flow:", className="text-muted"),
                            html.Div([
                                html.Span(id="projected-cashflow-summary", children="£0", className="fw-bold text-warning")
                            ])
                        ], width=4),
                        dbc.Col([
                            html.Small("Monthly Difference:", className="text-muted"),
                            html.Div([
                                html.Span(id="cashflow-difference-summary", children="£0", className="fw-bold text-info"),
                                html.Br(),
                                html.Small(id="difference-explanation", children="", className="text-muted")
                            ])
                        ], width=4)
                    ])
                ], className="mb-3"),
                html.Hr(),
                html.Div([
                    html.H6("Key Insights", className="fw-bold mb-3"),
                    html.Ul(id="financial-insights-list", children=[
                        html.Li("Enter your financial data in the Data Input tab to see personalized insights", className="text-muted")
                    ])
                ])
            ])
        ])
    ], style={"maxHeight": "800px", "overflowY": "auto"})


def calculate_uk_net_income(gross_annual_salary):
    """Calculate UK net monthly income after tax and NI"""
    if not gross_annual_salary:
        return 0

    # UK Tax rates for 2024/25
    personal_allowance = 12570
    basic_rate_threshold = 50270
    higher_rate_threshold = 125140

    # Calculate income tax
    taxable_income = max(0, gross_annual_salary - personal_allowance)
    income_tax = 0

    if taxable_income <= (basic_rate_threshold - personal_allowance):
        income_tax = taxable_income * 0.20  # Basic rate 20%
    elif taxable_income <= (higher_rate_threshold - personal_allowance):
        income_tax = (basic_rate_threshold - personal_allowance) * 0.20
        income_tax += (taxable_income - (basic_rate_threshold -
                       personal_allowance)) * 0.40  # Higher rate 40%
    else:
        income_tax = (basic_rate_threshold - personal_allowance) * 0.20
        income_tax += (higher_rate_threshold - basic_rate_threshold) * 0.40
        income_tax += (taxable_income - (higher_rate_threshold -
                       personal_allowance)) * 0.45  # Additional rate 45%

    # Calculate National Insurance (Class 1)
    ni_lower_threshold = 12570
    ni_upper_threshold = 50270
    national_insurance = 0

    if gross_annual_salary > ni_lower_threshold:
        ni_earnings = min(gross_annual_salary,
                          ni_upper_threshold) - ni_lower_threshold
        national_insurance = ni_earnings * 0.12  # 12% on earnings between thresholds

        if gross_annual_salary > ni_upper_threshold:
            # 2% on earnings above upper threshold
            national_insurance += (gross_annual_salary -
                                   ni_upper_threshold) * 0.02

    # Calculate net annual income
    net_annual = gross_annual_salary - income_tax - national_insurance
    net_monthly = net_annual / 12

    return net_monthly


def create_investment_management_layout():
    """Investment Management Tab - Enhanced with Subscription Features"""
    return html.Div([
        html.H3("Portfolio Management", className="mb-4"),

        # Subscription indicator with upgrade prompt
        dbc.Row([
            dbc.Col([
                dbc.Alert([
                    html.I(className="fas fa-crown me-2"),
                    "Personal Mode - Standard Subscription Active"
                ], color="success", className="mb-4")
            ], width=8),
            dbc.Col([
                dbc.Button([
                    html.I(className="fas fa-arrow-up me-2"),
                    "Upgrade to Premium"
                ], color="warning", className="float-end")
            ], width=4)
        ]),

        # Clean Portfolio Allocation Control Panel
        dbc.Card([
            dbc.CardHeader([
                html.H5("🎯 Portfolio Allocation Control", className="mb-0")
            ]),
            dbc.CardBody([
                # Investment Type Selection
                html.Div([
                    html.Label("Select Investment Types:",
                               className="fw-bold mb-3"),
                    dcc.Checklist(
                        id="personal-investment-types-checklist",
                        options=[
                            {'label': ' 📈 Stocks (Individual Equities)',
                             'value': 'stocks'},
                            {'label': ' 🏛️ Bonds (Government/Corporate)',
                             'value': 'bonds'},
                            {'label': ' 📊 ETFs (Exchange Traded Funds)',
                             'value': 'etfs'},
                            {'label': ' 🎯 Mutual Funds', 'value': 'mutual_funds'},
                            {'label': ' 🏠 Real Estate (REITs/Property)',
                             'value': 'real_estate'},
                            {'label': ' ₿ Cryptocurrency', 'value': 'crypto'},
                            {'label': ' 🏦 Retirement Accounts',
                                'value': 'retirement'},
                            {'label': ' 💰 Savings & CDs', 'value': 'savings'}
                        ],
                        value=['stocks', 'etfs', 'bonds'],
                        className="mb-4",
                        style={
                            'display': 'grid',
                            'gridTemplateColumns': 'repeat(auto-fit, minmax(300px, 1fr))',
                            'gap': '10px'
                        }
                    )
                ]),

                # Dynamic Allocation Sliders Container
                html.Div([
                    html.Label("Portfolio Allocation (%):",
                               className="fw-bold mb-3"),
                    html.Div(id="allocation-sliders-container", children=[
                        # Default sliders for initial selection
                        html.Div([
                            html.Label("📈 Stocks (%):",
                                       className="fw-bold mb-2"),
                            dcc.Slider(
                                id="allocation-stocks-slider",
                                min=0, max=100, step=1, value=40,
                                marks={i: str(i) for i in range(0, 101, 20)},
                                tooltip={"placement": "bottom",
                                         "always_visible": True}
                            )
                        ], className="mb-3"),
                        html.Div([
                            html.Label("📊 ETFs (%):",
                                       className="fw-bold mb-2"),
                            dcc.Slider(
                                id="allocation-etfs-slider",
                                min=0, max=100, step=1, value=35,
                                marks={i: str(i) for i in range(0, 101, 20)},
                                tooltip={"placement": "bottom",
                                         "always_visible": True}
                            )
                        ], className="mb-3"),
                        html.Div([
                            html.Label("🏛️ Bonds (%):",
                                       className="fw-bold mb-2"),
                            dcc.Slider(
                                id="allocation-bonds-slider",
                                min=0, max=100, step=1, value=25,
                                marks={i: str(i) for i in range(0, 101, 20)},
                                tooltip={"placement": "bottom",
                                         "always_visible": True}
                            )
                        ], className="mb-3")
                    ])
                ], className="mb-4"),

                # Risk Tolerance & Control Panel
                dbc.Row([
                    dbc.Col([
                        html.Label("Risk Tolerance (1-10):",
                                   className="fw-bold"),
                        dcc.Slider(
                            id="risk-tolerance-slider",
                            min=1, max=10, step=1, value=5,
                            marks={
                                1: {'label': '1', 'style': {'color': '#28a745'}},
                                5: {'label': '5', 'style': {'color': '#ffc107'}},
                                10: {'label': '10', 'style': {'color': '#dc3545'}}
                            },
                            tooltip={"placement": "bottom",
                                     "always_visible": True}
                        ),
                        html.Div([
                            html.Small("Conservative",
                                       className="text-success"),
                            html.Small(
                                "Aggressive", className="text-danger float-end")
                        ], className="mt-2")
                    ], width=6),
                    dbc.Col([
                        html.Label("Total Allocation:", className="fw-bold"),
                        html.H3(id="total-allocation-display", children="100%",
                                className="text-primary mb-2"),
                        dbc.Button("Apply Allocation", id="apply-allocation-btn",
                                   color="success", size="lg", className="w-100")
                    ], width=3),
                    dbc.Col([
                        html.Label("Portfolio Value:", className="fw-bold"),
                        html.H3("£42,350", className="text-info mb-2"),
                        dbc.Button("Rebalance Now", id="rebalance-btn",
                                   color="primary", size="lg", className="w-100")
                    ], width=3)
                ])
            ])
        ], className="mb-4"),

        # Portfolio Allocation Visualization
        dbc.Card([
            dbc.CardHeader([
                html.H5("📊 Portfolio Allocation Breakdown", className="mb-0")
            ]),
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        dcc.Graph(
                            id="portfolio-allocation-donut",
                            config={'displayModeBar': False},
                            style={'height': '400px'}
                        )
                    ], width=8),
                    dbc.Col([
                        html.H6("Current Allocation", className="text-center mb-3"),
                        html.Div([
                            html.Div([
                                html.Span("📈 Stocks", className="fw-bold"),
                                html.Span("40%", className="float-end text-primary")
                            ], className="d-flex justify-content-between mb-2"),
                            html.Div([
                                html.Span("📊 ETFs", className="fw-bold"),
                                html.Span("35%", className="float-end text-info")
                            ], className="d-flex justify-content-between mb-2"),
                            html.Div([
                                html.Span("🏛️ Bonds", className="fw-bold"),
                                html.Span("25%", className="float-end text-success")
                            ], className="d-flex justify-content-between mb-3"),
                            html.Hr(),
                            html.Div([
                                html.Span("Total Portfolio Value", className="fw-bold"),
                                html.Span("£42,350", className="float-end text-dark fw-bold")
                            ], className="d-flex justify-content-between mb-2"),
                            html.Div([
                                html.Span("Expected Annual Return", className="fw-bold"),
                                html.Span("8.2%", className="float-end text-success fw-bold")
                            ], className="d-flex justify-content-between mb-2"),
                            html.Div([
                                html.Span("Risk Level", className="fw-bold"),
                                html.Span("Moderate", className="float-end text-warning fw-bold")
                            ], className="d-flex justify-content-between")
                        ], className="p-3 bg-light rounded")
                    ], width=4)
                ])
            ])
        ], className="mb-4"),

        # AI Recommendations with Premium Upgrade Prompt
        dbc.Card([
            dbc.CardHeader([
                html.H5("💡 AI Investment Recommendations",
                        className="mb-0 d-inline"),
                dbc.Badge("Premium Feature", color="warning", className="ms-2")
            ]),
            dbc.CardBody([
                dbc.Alert([
                    html.I(className="fas fa-lock me-2"),
                    "Upgrade to Premium for unlimited AI-powered investment recommendations. ",
                    html.A("Upgrade now", href="#", className="alert-link")
                ], color="warning", className="mb-3"),

                # Sample recommendations (limited for Standard tier)
                dbc.Table([
                    html.Thead([
                        html.Tr([
                            html.Th("Investment"),
                            html.Th("Current Price"),
                            html.Th("Target"),
                            html.Th("Expected Return"),
                            html.Th("Risk"),
                            html.Th("Action")
                        ])
                    ]),
                    html.Tbody([
                        html.Tr([
                            html.Td([
                                html.Strong("Apple Inc."),
                                html.Br(),
                                html.Small("AAPL", className="text-muted")
                            ]),
                            html.Td("£145.32"),
                            html.Td("£165.00"),
                            html.Td([dbc.Badge("+13.5%", color="success")]),
                            html.Td([dbc.Badge("Medium", color="warning")]),
                            html.Td(
                                [dbc.Button("BUY", size="sm", color="success")])
                        ]),
                        html.Tr([
                            html.Td([
                                html.Strong("Vanguard S&P 500"),
                                html.Br(),
                                html.Small("VOO", className="text-muted")
                            ]),
                            html.Td("£324.85"),
                            html.Td("£340.00"),
                            html.Td([dbc.Badge("+4.7%", color="success")]),
                            html.Td([dbc.Badge("Low", color="success")]),
                            html.Td(
                                [dbc.Button("BUY", size="sm", color="success")])
                        ])
                    ])
                ], striped=True, hover=True, className="mb-0")
            ])
        ], className="mb-4"),

        # Action Schedule
        dbc.Card([
            dbc.CardHeader([
                html.H5("📅 Action Schedule", className="mb-0 d-inline"),
                html.Small(" (2 of 10 monthly recommendations used)",
                           className="text-muted ms-2")
            ]),
            dbc.CardBody([
                dbc.Table([
                    html.Thead([
                        html.Tr([
                            html.Th("Date"),
                            html.Th("Action"),
                            html.Th("Investment"),
                            html.Th("Amount"),
                            html.Th("Status")
                        ])
                    ]),
                    html.Tbody([
                        html.Tr([
                            html.Td("2025-07-25"),
                            html.Td([dbc.Badge("💰 BUY", color="success")]),
                            html.Td("Apple Inc. (AAPL)"),
                            html.Td("£2,500"),
                            html.Td(
                                [dbc.Button("✓", size="sm", color="outline-success")])
                        ]),
                        html.Tr([
                            html.Td("2025-08-01"),
                            html.Td([dbc.Badge("🔄 REBALANCE", color="info")]),
                            html.Td("Portfolio"),
                            html.Td("£5,000"),
                            html.Td(
                                [dbc.Button("⏸", size="sm", color="outline-warning")])
                        ])
                    ])
                ], striped=True, hover=True, className="mb-0")
            ])
        ])
    ], className="p-3")


def create_analysis_tab_layout():
    """Analysis Tab - Mathematical Modeling and Scenario Analysis"""
    return html.Div([
        # Header
        html.H3("Investment Analysis Engine", className="mb-4"),

        dbc.Alert([
            html.I(className="fas fa-chart-line me-2"),
            "Advanced mathematical modeling and scenario analysis tools"
        ], color="info", className="mb-4"),

        # Model Configuration Panel
        dbc.Card([
            dbc.CardHeader([
                html.H5("⚙️ Model Configuration", className="mb-0")
            ]),
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        html.Label("Risk Model:", className="fw-bold"),
                        dcc.Dropdown(
                            id="risk-model-dropdown",
                            options=[
                                {"label": "Modern Portfolio Theory", "value": "mpt"},
                                {"label": "CAPM", "value": "capm"},
                                {"label": "Fama-French 3-Factor", "value": "ff3"},
                                {"label": "Black-Litterman", "value": "bl"}
                            ],
                            value="mpt",
                            className="mb-3"
                        )
                    ], width=3),
                    dbc.Col([
                        html.Label("Time Frequency:", className="fw-bold"),
                        dcc.Dropdown(
                            id="time-frequency-dropdown",
                            options=[
                                {"label": "Daily", "value": "daily"},
                                {"label": "Weekly", "value": "weekly"},
                                {"label": "Monthly", "value": "monthly"},
                                {"label": "Quarterly", "value": "quarterly"}
                            ],
                            value="monthly",
                            className="mb-3"
                        )
                    ], width=3),
                    dbc.Col([
                        html.Label("Historical Period:", className="fw-bold"),
                        dcc.Dropdown(
                            id="historical-period-dropdown",
                            options=[
                                {"label": "1 Year", "value": 1},
                                {"label": "3 Years", "value": 3},
                                {"label": "5 Years", "value": 5},
                                {"label": "10 Years", "value": 10}
                            ],
                            value=5,
                            className="mb-3"
                        )
                    ], width=3),
                    dbc.Col([
                        html.Label("Confidence Level:", className="fw-bold"),
                        dcc.Dropdown(
                            id="confidence-level-dropdown",
                            options=[
                                {"label": "90%", "value": 0.90},
                                {"label": "95%", "value": 0.95},
                                {"label": "99%", "value": 0.99}
                            ],
                            value=0.95,
                            className="mb-3"
                        )
                    ], width=3)
                ])
            ])
        ], className="mb-4"),

        # Scenario Analysis Tools
        dbc.Card([
            dbc.CardHeader([
                html.H5("📊 Scenario Analysis", className="mb-0 d-inline"),
                dbc.Badge("Premium Feature", color="warning", className="ms-2")
            ]),
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        html.Label("Economic Scenario:", className="fw-bold"),
                        dcc.Dropdown(
                            id="economic-scenario-dropdown",
                            options=[
                                {"label": "📈 Economic Growth", "value": "growth"},
                                {"label": "📉 Recession", "value": "recession"},
                                {"label": "💥 Market Crash", "value": "crash"},
                                {"label": "📊 Stagflation", "value": "stagflation"},
                                {"label": "⚖️ Base Case", "value": "base"}
                            ],
                            value="base",
                            className="mb-3"
                        )
                    ], width=4),
                    dbc.Col([
                        html.Label("Interest Rate Change:",
                                   className="fw-bold"),
                        dcc.Slider(
                            id="interest-rate-slider",
                            min=-3, max=3, step=0.25, value=0,
                            marks={-3: '-3%', -1.5: '-1.5%',
                                   0: '0%', 1.5: '+1.5%', 3: '+3%'},
                            tooltip={"placement": "bottom",
                                     "always_visible": True}
                        )
                    ], width=4),
                    dbc.Col([
                        html.Label("Market Volatility:", className="fw-bold"),
                        dcc.Slider(
                            id="volatility-multiplier-slider",
                            min=0.5, max=2.0, step=0.1, value=1.0,
                            marks={0.5: '0.5x', 1.0: '1.0x',
                                   1.5: '1.5x', 2.0: '2.0x'},
                            tooltip={"placement": "bottom",
                                     "always_visible": True}
                        )
                    ], width=4)
                ], className="mb-3"),
                dbc.Row([
                    dbc.Col([
                        dbc.Button("Run Scenario", color="primary",
                                   className="me-2"),
                        dbc.Button("Compare Scenarios", color="success",
                                   outline=True, className="me-2"),
                        dbc.Button("Export Analysis",
                                   color="info", outline=True)
                    ])
                ])
            ])
        ], className="mb-4"),

        # Results Display Area
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H5("📈 Efficient Frontier", className="mb-0")
                    ]),
                    dbc.CardBody([
                        html.Div(
                            "Efficient Frontier Chart Placeholder",
                            className="text-center p-5 bg-light border rounded",
                            style={"height": "300px", "display": "flex",
                                   "alignItems": "center", "justifyContent": "center"}
                        )
                    ])
                ])
            ], width=6),
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H5("📊 Risk-Return Analysis", className="mb-0")
                    ]),
                    dbc.CardBody([
                        html.Div(
                            "Risk-Return Scatter Plot",
                            className="text-center p-5 bg-light border rounded",
                            style={"height": "300px", "display": "flex",
                                   "alignItems": "center", "justifyContent": "center"}
                        )
                    ])
                ])
            ], width=6)
        ], className="mb-4"),

        # Analysis Results Table
        dbc.Card([
            dbc.CardHeader([
                html.H5("📋 Analysis Results", className="mb-0")
            ]),
            dbc.CardBody([
                dbc.Table([
                    html.Thead([
                        html.Tr([
                            html.Th("Metric"),
                            html.Th("Current Portfolio"),
                            html.Th("Optimal Portfolio"),
                            html.Th("Benchmark"),
                            html.Th("Improvement")
                        ])
                    ]),
                    html.Tbody([
                        html.Tr([
                            html.Td("Expected Return"),
                            html.Td("8.2%"),
                            html.Td("9.1%"),
                            html.Td("7.5%"),
                            html.Td([dbc.Badge("+0.9%", color="success")])
                        ]),
                        html.Tr([
                            html.Td("Volatility"),
                            html.Td("15.3%"),
                            html.Td("14.1%"),
                            html.Td("16.2%"),
                            html.Td([dbc.Badge("-1.2%", color="success")])
                        ]),
                        html.Tr([
                            html.Td("Sharpe Ratio"),
                            html.Td("0.53"),
                            html.Td("0.65"),
                            html.Td("0.46"),
                            html.Td([dbc.Badge("+0.12", color="success")])
                        ]),
                        html.Tr([
                            html.Td("Max Drawdown"),
                            html.Td("-22.1%"),
                            html.Td("-18.5%"),
                            html.Td("-25.3%"),
                            html.Td([dbc.Badge("+3.6%", color="success")])
                        ])
                    ])
                ], striped=True, hover=True)
            ])
        ])
    ], className="p-3")


def create_data_input_tab_layout():
    """Enhanced Data Input Tab - Document Processing and Manual Entry with Sliders"""
    return html.Div([
        # Header
        html.H3("Personal Finance Data Input", className="mb-4"),

        dbc.Alert([
            html.I(className="fas fa-info-circle me-2"),
            "Upload documents for automated analysis or use manual entry for complete control"
        ], color="info", className="mb-4"),

        # Data Input Methods Selection
        dbc.Card([
            dbc.CardHeader([
                html.H5("� Choose Your Data Input Method", className="mb-0")
            ]),
            dbc.CardBody([
                # Enhanced flexbox layout for better button alignment
                dbc.Row([
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.Div([
                                    html.I(
                                        className="fas fa-edit fa-3x text-primary mb-3"),
                                    html.H5("Manual Entry", className="mb-3"),
                                    html.P("Enter your financial details manually with "
                                           "industry-standard categories and real-time sliders",
                                           className="text-muted mb-3"),
                                    dbc.Button([
                                        html.I(
                                            className="fas fa-keyboard me-2"),
                                        "Open Manual Entry"
                                    ], id="open-manual-entry-btn", color="primary",
                                        className="w-100 mb-2"),
                                    html.Small("Complete financial profile in minutes",
                                               className="text-muted")
                                ], className="text-center h-100 d-flex flex-column justify-content-between")
                            ], className="h-100")
                        ], outline=True, color="primary", className="h-100")
                    ], width=6, className="mb-3 mb-md-0 d-flex"),
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.Div([
                                    html.I(
                                        className="fas fa-cloud-upload-alt fa-3x text-success mb-3"),
                                    html.H5("Document Upload",
                                            className="mb-3"),
                                    html.P("Upload bank statements, receipts, and investment "
                                           "accounts for automated analysis",
                                           className="text-muted mb-3"),
                                    dbc.Button([
                                        html.I(className="fas fa-upload me-2"),
                                        "Upload Documents"
                                    ], id="open-document-upload-btn", color="success",
                                        className="w-100 mb-2"),
                                    html.Small("AI-powered document processing",
                                               className="text-muted")
                                ], className="text-center h-100 d-flex flex-column justify-content-between")
                            ], className="h-100")
                        ], outline=True, color="success", className="h-100")
                    ], width=6, className="d-flex")
                ], className="g-3")
            ])
        ], className="mb-4"),

        # Financial Summary Cards (Updated dynamically)
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.Div([
                            html.I(
                                className="fas fa-money-bill-wave text-success me-2"),
                            html.H5("Monthly Income",
                                    className="mb-0 d-inline")
                        ], className="d-flex align-items-center")
                    ]),
                    dbc.CardBody([
                        html.H4("£0", id="total-income-display",
                                className="text-success mb-2"),
                        html.Div(id="income-breakdown", children=[
                            html.Small("Use manual entry to add income sources",
                                       className="text-muted")
                        ])
                    ], className="text-center")
                ], className="h-100")
            ], width=3),
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.Div([
                            html.I(
                                className="fas fa-shopping-cart text-danger me-2"),
                            html.H5("Monthly Expenses",
                                    className="mb-0 d-inline")
                        ], className="d-flex align-items-center")
                    ]),
                    dbc.CardBody([
                        html.H4("£0", id="total-expenses-display",
                                className="text-danger mb-2"),
                        html.Div(id="expenses-breakdown", children=[
                            html.Small("Use manual entry to add expense categories",
                                       className="text-muted")
                        ])
                    ], className="text-center")
                ], className="h-100")
            ], width=3),
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.Div([
                            html.I(className="fas fa-chart-line text-info me-2"),
                            html.H5("Net Cash Flow", className="mb-0 d-inline")
                        ], className="d-flex align-items-center")
                    ]),
                    dbc.CardBody([
                        html.H4("£0", id="net-cashflow-display",
                                className="text-info mb-2"),
                        html.Small("Income - Expenses", className="text-muted")
                    ], className="text-center")
                ], className="h-100")
            ], width=3),
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.Div([
                            html.I(className="fas fa-gem text-primary me-2"),
                            html.H5("Net Worth", className="mb-0 d-inline")
                        ], className="d-flex align-items-center")
                    ]),
                    dbc.CardBody([
                        html.H4("£0", id="net-worth-display",
                                className="text-primary mb-2"),
                        html.Small("Assets - Liabilities",
                                   className="text-muted")
                    ], className="text-center")
                ], className="h-100")
            ], width=3)
        ], className="mb-4 g-3"),

        # Data Persistence Section
        dbc.Card([
            dbc.CardHeader([
                html.Div([
                    html.I(className="fas fa-save text-primary me-2"),
                    html.H5("Data Persistence & Export",
                            className="mb-0 d-inline")
                ], className="d-flex align-items-center")
            ]),
            dbc.CardBody([
                html.P("Save your financial data locally, export to various formats, or load previously saved profiles.",
                       className="text-muted mb-4"),

                # Save/Load Section
                dbc.Row([
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.Div([
                                    html.I(
                                        className="fas fa-download fa-2x text-success mb-3"),
                                    html.H6("Save Financial Profile",
                                            className="mb-3"),
                                    dbc.InputGroup([
                                        dbc.Input(
                                            id="save-profile-name",
                                            placeholder="Enter profile name...",
                                            value="",
                                            type="text"
                                        ),
                                        dbc.Button([
                                            html.I(
                                                className="fas fa-save me-1"),
                                            "Save"
                                        ], id="save-profile-btn", color="success")
                                    ], className="mb-3"),
                                    html.Small("Save current financial data to browser storage",
                                               className="text-muted")
                                ], className="text-center")
                            ])
                        ], outline=True, color="success", className="h-100")
                    ], width=6),

                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.Div([
                                    html.I(
                                        className="fas fa-upload fa-2x text-info mb-3"),
                                    html.H6("Load Financial Profile",
                                            className="mb-3"),
                                    dbc.Select(
                                        id="load-profile-select",
                                        placeholder="Select saved profile...",
                                        options=[],
                                        className="mb-3"
                                    ),
                                    dbc.Button([
                                        html.I(
                                            className="fas fa-folder-open me-1"),
                                        "Load"
                                    ], id="load-profile-btn", color="info", className="w-100"),
                                    html.Small("Load previously saved financial data",
                                               className="text-muted")
                                ], className="text-center")
                            ])
                        ], outline=True, color="info", className="h-100")
                    ], width=6)
                ], className="mb-4"),

                # Export Section
                dbc.Row([
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.Div([
                                    html.I(
                                        className="fas fa-file-export fa-2x text-warning mb-3"),
                                    html.H6("Export Data", className="mb-3"),
                                    dbc.ButtonGroup([
                                        dbc.Button([
                                            html.I(
                                                className="fas fa-file-csv me-1"),
                                            "CSV"
                                        ], id="export-csv-btn", color="warning", size="sm"),
                                        dbc.Button([
                                            html.I(
                                                className="fas fa-file-code me-1"),
                                            "JSON"
                                        ], id="export-json-btn", color="warning", size="sm"),
                                        dbc.Button([
                                            html.I(
                                                className="fas fa-file-excel me-1"),
                                            "Excel"
                                        ], id="export-excel-btn", color="warning", size="sm")
                                    ], className="w-100 mb-3"),
                                    html.Small("Export your financial data for external analysis",
                                               className="text-muted")
                                ], className="text-center")
                            ])
                        ], outline=True, color="warning", className="h-100")
                    ], width=6),

                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.Div([
                                    html.I(
                                        className="fas fa-file-import fa-2x text-secondary mb-3"),
                                    html.H6("Import Data", className="mb-3"),
                                    dcc.Upload([
                                        dbc.Button([
                                            html.I(
                                                className="fas fa-cloud-upload-alt me-1"),
                                            "Import File"
                                        ], color="secondary", className="w-100")
                                    ], id="import-data-upload", className="mb-3"),
                                    html.Small("Import CSV, JSON, or Excel files",
                                               className="text-muted")
                                ], className="text-center")
                            ])
                        ], outline=True, color="secondary", className="h-100")
                    ], width=6)
                ]),

                # Status Messages
                html.Div(id="persistence-status-message", className="mt-3"),

                # Saved Profiles List
                html.Div([
                    html.Hr(),
                    html.H6("Saved Profiles", className="mb-3"),
                    html.Div(id="saved-profiles-list", children=[
                        dbc.Alert("No saved profiles found. Save your current data to create your first profile.",
                                  color="light", className="text-center")
                    ])
                ], id="saved-profiles-section")
            ])
        ], className="mb-4"),

        # Quick Adjustment Sliders (Visible after data entry)
        html.Div([
            dbc.Card([
                dbc.CardHeader([
                    html.H5("🎛️ Quick Financial Adjustments", className="mb-0")
                ]),
                dbc.CardBody([
                    html.P("Use these sliders to quickly adjust your financial metrics "
                           "and see real-time impact on cash flow and net worth.",
                           className="text-muted mb-4"),
                    html.Div(id="adjustment-sliders-container")
                ])
            ])
        ], id="quick-adjustments-section", style={"display": "none"},
            className="mb-4"),

        # Document Upload Section (Initially Hidden)
        html.Div([
            create_document_upload_section()
        ], id="document-upload-section", style={"display": "none"}),

        # Manual Entry Modals
        create_manual_entry_modals()
    ])


def create_document_upload_section():
    """Original document upload functionality"""
    return dbc.Card([
        dbc.CardHeader([
            html.H5("📁 Document Upload Center", className="mb-0")
        ]),
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    html.H6("Bank Statements", className="mb-3"),
                    dcc.Upload(
                        id="bank-statements-upload",
                        children=html.Div([
                            html.I(className="fas fa-cloud-upload-alt fa-3x mb-3"),
                            html.Br(),
                            "Drag & Drop or Click to Upload",
                            html.Br(),
                            html.Small("PDF, CSV, Excel files",
                                       className="text-muted")
                        ]),
                        style={
                            'width': '100%', 'height': '120px', 'lineHeight': '120px',
                            'borderWidth': '2px', 'borderStyle': 'dashed',
                            'borderRadius': '10px', 'textAlign': 'center', 'margin': '10px'
                        },
                        multiple=True,
                        className="mb-3"
                    ),
                    html.Div(id="bank-statements-output",
                             className="text-muted")
                ], width=4),
                dbc.Col([
                    html.H6("Receipts & Expenses", className="mb-3"),
                    dcc.Upload(
                        id="receipts-upload",
                        children=html.Div([
                            html.I(className="fas fa-receipt fa-3x mb-3"),
                            html.Br(),
                            "Upload Receipt Images",
                            html.Br(),
                            html.Small("JPG, PNG, PDF", className="text-muted")
                        ]),
                        style={
                            'width': '100%', 'height': '120px', 'lineHeight': '120px',
                            'borderWidth': '2px', 'borderStyle': 'dashed',
                            'borderRadius': '10px', 'textAlign': 'center', 'margin': '10px'
                        },
                        multiple=True,
                        className="mb-3"
                    ),
                    html.Div(id="receipts-output", className="text-muted")
                ], width=4),
                dbc.Col([
                    html.H6("Investment Accounts", className="mb-3"),
                    dcc.Upload(
                        id="investment-statements-upload",
                        children=html.Div([
                            html.I(className="fas fa-chart-line fa-3x mb-3"),
                            html.Br(),
                            "Investment Statements",
                            html.Br(),
                            html.Small("PDF, CSV files",
                                       className="text-muted")
                        ]),
                        style={
                            'width': '100%', 'height': '120px', 'lineHeight': '120px',
                            'borderWidth': '2px', 'borderStyle': 'dashed',
                            'borderRadius': '10px', 'textAlign': 'center', 'margin': '10px'
                        },
                        multiple=True,
                        className="mb-3"
                    ),
                    html.Div(id="investment-statements-output",
                             className="text-muted")
                ], width=4)
            ]),
            dbc.Row([
                dbc.Col([
                    dbc.Button([
                        html.I(className="fas fa-cogs me-2"),
                        "Process Documents"
                    ], color="primary", size="lg", className="w-100")
                ])
            ])
        ])
    ], className="mb-4")


def create_manual_entry_modals():
    """Create comprehensive manual entry modals for financial data"""
    return html.Div([
        # Main Financial Data Entry Modal
        dbc.Modal([
            dbc.ModalHeader([
                dbc.ModalTitle("📊 Complete Financial Profile Entry")
            ]),
            dbc.ModalBody([
                dbc.Tabs([
                    # Income Tab
                    dbc.Tab(label="💰 Income", children=[
                        create_income_entry_form()
                    ]),
                    # Expenses Tab
                    dbc.Tab(label="💳 Expenses", children=[
                        create_expenses_entry_form()
                    ]),
                    # Assets Tab
                    dbc.Tab(label="🏠 Assets", children=[
                        create_assets_entry_form()
                    ]),
                    # Liabilities Tab
                    dbc.Tab(label="📋 Debts & Loans", children=[
                        create_liabilities_entry_form()
                    ])
                ])
            ]),
            dbc.ModalFooter([
                dbc.Button("Load Sample Data", id="load-sample-data-btn",
                           color="info", className="me-auto"),
                dbc.Button("Cancel", id="cancel-manual-entry",
                           color="secondary"),
                dbc.Button("Save Financial Profile", id="save-manual-entry",
                           color="primary")
            ])
        ], id="manual-entry-modal", size="xl", is_open=False, backdrop="static")
    ])


def create_income_entry_form():
    """Industry-standard income categories with input fields"""
    return html.Div([
        html.H5("Monthly Income Sources", className="mb-4"),
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Primary Income"),
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                dbc.Label("Gross Salary/Wage"),
                                dbc.InputGroup([
                                    dbc.InputGroupText("£"),
                                    dbc.Input(id="gross-salary", type="number",
                                              placeholder="0", value=0)
                                ], className="mb-3")
                            ], width=6),
                            dbc.Col([
                                dbc.Label("Net Take-Home"),
                                dbc.InputGroup([
                                    dbc.InputGroupText("£"),
                                    dbc.Input(id="net-salary", type="number",
                                              placeholder="0", value=0)
                                ], className="mb-3")
                            ], width=6)
                        ])
                    ])
                ])
            ], width=12, className="mb-3"),

            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Additional Income"),
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                dbc.Label("Bonuses/Commission"),
                                dbc.InputGroup([
                                    dbc.InputGroupText("£"),
                                    dbc.Input(id="bonuses", type="number",
                                              placeholder="0", value=0)
                                ], className="mb-2")
                            ], width=6),
                            dbc.Col([
                                dbc.Label("Freelance/Side Hustle"),
                                dbc.InputGroup([
                                    dbc.InputGroupText("£"),
                                    dbc.Input(id="freelance", type="number",
                                              placeholder="0", value=0)
                                ], className="mb-2")
                            ], width=6)
                        ]),
                        dbc.Row([
                            dbc.Col([
                                dbc.Label("Rental Income"),
                                dbc.InputGroup([
                                    dbc.InputGroupText("£"),
                                    dbc.Input(id="rental-income", type="number",
                                              placeholder="0", value=0)
                                ], className="mb-2")
                            ], width=6),
                            dbc.Col([
                                dbc.Label("Investment Dividends"),
                                dbc.InputGroup([
                                    dbc.InputGroupText("£"),
                                    dbc.Input(id="dividends", type="number",
                                              placeholder="0", value=0)
                                ], className="mb-2")
                            ], width=6)
                        ]),
                        dbc.Row([
                            dbc.Col([
                                dbc.Label("Pension/Benefits"),
                                dbc.InputGroup([
                                    dbc.InputGroupText("£"),
                                    dbc.Input(id="pension-benefits", type="number",
                                              placeholder="0", value=0)
                                ], className="mb-2")
                            ], width=6),
                            dbc.Col([
                                dbc.Label("Other Income"),
                                dbc.InputGroup([
                                    dbc.InputGroupText("£"),
                                    dbc.Input(id="other-income", type="number",
                                              placeholder="0", value=0)
                                ], className="mb-2")
                            ], width=6)
                        ])
                    ])
                ])
            ], width=12)
        ])
    ], className="p-3")


def create_expenses_entry_form():
    """Industry-standard expense categories with input fields"""
    return html.Div([
        html.H5("Monthly Expenses", className="mb-4"),
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Housing & Utilities"),
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                dbc.Label("Rent/Mortgage"),
                                dbc.InputGroup([
                                    dbc.InputGroupText("£"),
                                    dbc.Input(id="rent-mortgage", type="number",
                                              placeholder="0", value=0)
                                ], className="mb-2")
                            ], width=6),
                            dbc.Col([
                                dbc.Label("Utilities (Gas, Electric)"),
                                dbc.InputGroup([
                                    dbc.InputGroupText("£"),
                                    dbc.Input(id="utilities", type="number",
                                              placeholder="0", value=0)
                                ], className="mb-2")
                            ], width=6)
                        ]),
                        dbc.Row([
                            dbc.Col([
                                dbc.Label("Council Tax"),
                                dbc.InputGroup([
                                    dbc.InputGroupText("£"),
                                    dbc.Input(id="council-tax", type="number",
                                              placeholder="0", value=0)
                                ], className="mb-2")
                            ], width=6),
                            dbc.Col([
                                dbc.Label("Home Insurance"),
                                dbc.InputGroup([
                                    dbc.InputGroupText("£"),
                                    dbc.Input(id="home-insurance", type="number",
                                              placeholder="0", value=0)
                                ], className="mb-2")
                            ], width=6)
                        ])
                    ])
                ])
            ], width=12, className="mb-3"),

            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Living Expenses"),
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                dbc.Label("Groceries & Food"),
                                dbc.InputGroup([
                                    dbc.InputGroupText("£"),
                                    dbc.Input(id="groceries", type="number",
                                              placeholder="0", value=0)
                                ], className="mb-2")
                            ], width=6),
                            dbc.Col([
                                dbc.Label("Transport (Car/Public)"),
                                dbc.InputGroup([
                                    dbc.InputGroupText("£"),
                                    dbc.Input(id="transport", type="number",
                                              placeholder="0", value=0)
                                ], className="mb-2")
                            ], width=6)
                        ]),
                        dbc.Row([
                            dbc.Col([
                                dbc.Label("Healthcare"),
                                dbc.InputGroup([
                                    dbc.InputGroupText("£"),
                                    dbc.Input(id="healthcare", type="number",
                                              placeholder="0", value=0)
                                ], className="mb-2")
                            ], width=6),
                            dbc.Col([
                                dbc.Label("Entertainment"),
                                dbc.InputGroup([
                                    dbc.InputGroupText("£"),
                                    dbc.Input(id="entertainment", type="number",
                                              placeholder="0", value=0)
                                ], className="mb-2")
                            ], width=6)
                        ])
                    ])
                ])
            ], width=12)
        ])
    ], className="p-3")


def create_assets_entry_form():
    """Assets entry form with current values"""
    return html.Div([
        html.H5("Current Assets", className="mb-4"),
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Property & Real Estate"),
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                dbc.Label("Primary Residence Value"),
                                dbc.InputGroup([
                                    dbc.InputGroupText("£"),
                                    dbc.Input(id="home-value", type="number",
                                              placeholder="0", value=0)
                                ], className="mb-2")
                            ], width=6),
                            dbc.Col([
                                dbc.Label("Investment Properties"),
                                dbc.InputGroup([
                                    dbc.InputGroupText("£"),
                                    dbc.Input(id="investment-properties", type="number",
                                              placeholder="0", value=0)
                                ], className="mb-2")
                            ], width=6)
                        ])
                    ])
                ])
            ], width=12, className="mb-3"),

            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Financial Assets"),
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                dbc.Label("Savings Accounts"),
                                dbc.InputGroup([
                                    dbc.InputGroupText("£"),
                                    dbc.Input(id="savings", type="number",
                                              placeholder="0", value=0)
                                ], className="mb-2")
                            ], width=6),
                            dbc.Col([
                                dbc.Label("Investment Accounts"),
                                dbc.InputGroup([
                                    dbc.InputGroupText("£"),
                                    dbc.Input(id="investments", type="number",
                                              placeholder="0", value=0)
                                ], className="mb-2")
                            ], width=6)
                        ]),
                        dbc.Row([
                            dbc.Col([
                                dbc.Label("Pension Value"),
                                dbc.InputGroup([
                                    dbc.InputGroupText("£"),
                                    dbc.Input(id="pension-value", type="number",
                                              placeholder="0", value=0)
                                ], className="mb-2")
                            ], width=6),
                            dbc.Col([
                                dbc.Label("Other Assets (Car, etc.)"),
                                dbc.InputGroup([
                                    dbc.InputGroupText("£"),
                                    dbc.Input(id="other-assets", type="number",
                                              placeholder="0", value=0)
                                ], className="mb-2")
                            ], width=6)
                        ])
                    ])
                ])
            ], width=12)
        ])
    ], className="p-3")


def create_liabilities_entry_form():
    """Comprehensive liabilities entry with loan details"""
    return html.Div([
        html.H5("Debts & Liabilities", className="mb-4"),
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Mortgage Details"),
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                dbc.Label("Outstanding Mortgage"),
                                dbc.InputGroup([
                                    dbc.InputGroupText("£"),
                                    dbc.Input(id="mortgage-balance", type="number",
                                              placeholder="0", value=0)
                                ], className="mb-2")
                            ], width=4),
                            dbc.Col([
                                dbc.Label("Interest Rate (%)"),
                                dbc.InputGroup([
                                    dbc.Input(id="mortgage-rate", type="number",
                                              placeholder="0", value=0, step=0.01),
                                    dbc.InputGroupText("%")
                                ], className="mb-2")
                            ], width=4),
                            dbc.Col([
                                dbc.Label("Years Remaining"),
                                dbc.Input(id="mortgage-years", type="number",
                                          placeholder="0", value=0, className="mb-2")
                            ], width=4)
                        ])
                    ])
                ])
            ], width=12, className="mb-3"),

            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Credit Card Debts"),
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                dbc.Label("Credit Card Balance"),
                                dbc.InputGroup([
                                    dbc.InputGroupText("£"),
                                    dbc.Input(
                                        id="credit-cards",
                                        type="number",
                                        placeholder="0",
                                        value=0
                                    )
                                ], className="mb-2")
                            ], width=4),
                            dbc.Col([
                                dbc.Label("Interest Rate (%)"),
                                dbc.InputGroup([
                                    dbc.Input(
                                        id="credit-cards-rate",
                                        type="number",
                                        placeholder="0",
                                        value=0,
                                        step=0.01
                                    ),
                                    dbc.InputGroupText("%")
                                ], className="mb-2")
                            ], width=4),
                            dbc.Col([
                                dbc.Label("Monthly Payment"),
                                dbc.InputGroup([
                                    dbc.InputGroupText("£"),
                                    dbc.Input(
                                        id="credit-cards-payment",
                                        type="number",
                                        placeholder="0",
                                        value=0
                                    )
                                ], className="mb-2")
                            ], width=4)
                        ])
                    ])
                ])
            ], width=12, className="mb-3"),

            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Personal Loans"),
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                dbc.Label("Personal Loan Balance"),
                                dbc.InputGroup([
                                    dbc.InputGroupText("£"),
                                    dbc.Input(
                                        id="personal-loans",
                                        type="number",
                                        placeholder="0",
                                        value=0
                                    )
                                ], className="mb-2")
                            ], width=4),
                            dbc.Col([
                                dbc.Label("Interest Rate (%)"),
                                dbc.InputGroup([
                                    dbc.Input(
                                        id="personal-loans-rate",
                                        type="number",
                                        placeholder="0",
                                        value=0,
                                        step=0.01
                                    ),
                                    dbc.InputGroupText("%")
                                ], className="mb-2")
                            ], width=4),
                            dbc.Col([
                                dbc.Label("Years Remaining"),
                                dbc.Input(
                                    id="personal-loans-years",
                                    type="number",
                                    placeholder="0",
                                    value=0,
                                    className="mb-2"
                                )
                            ], width=4)
                        ])
                    ])
                ])
            ], width=12, className="mb-3"),

            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Student Loans"),
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                dbc.Label("Student Loan Balance"),
                                dbc.InputGroup([
                                    dbc.InputGroupText("£"),
                                    dbc.Input(
                                        id="student-loans",
                                        type="number",
                                        placeholder="0",
                                        value=0
                                    )
                                ], className="mb-2")
                            ], width=4),
                            dbc.Col([
                                dbc.Label("Interest Rate (%)"),
                                dbc.InputGroup([
                                    dbc.Input(
                                        id="student-loans-rate",
                                        type="number",
                                        placeholder="0",
                                        value=0,
                                        step=0.01
                                    ),
                                    dbc.InputGroupText("%")
                                ], className="mb-2")
                            ], width=4),
                            dbc.Col([
                                dbc.Label("Monthly Payment"),
                                dbc.InputGroup([
                                    dbc.InputGroupText("£"),
                                    dbc.Input(
                                        id="student-loans-payment",
                                        type="number",
                                        placeholder="0",
                                        value=0
                                    )
                                ], className="mb-2")
                            ], width=4)
                        ])
                    ])
                ])
            ], width=12, className="mb-3"),

            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Other Debts"),
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                dbc.Label("Other Debt Balance"),
                                dbc.InputGroup([
                                    dbc.InputGroupText("£"),
                                    dbc.Input(
                                        id="other-debts",
                                        type="number",
                                        placeholder="0",
                                        value=0
                                    )
                                ], className="mb-2")
                            ], width=4),
                            dbc.Col([
                                dbc.Label("Interest Rate (%)"),
                                dbc.InputGroup([
                                    dbc.Input(
                                        id="other-debts-rate",
                                        type="number",
                                        placeholder="0",
                                        value=0,
                                        step=0.01
                                    ),
                                    dbc.InputGroupText("%")
                                ], className="mb-2")
                            ], width=4),
                            dbc.Col([
                                dbc.Label("Monthly Payment"),
                                dbc.InputGroup([
                                    dbc.InputGroupText("£"),
                                    dbc.Input(
                                        id="other-debts-payment",
                                        type="number",
                                        placeholder="0",
                                        value=0
                                    )
                                ], className="mb-2")
                            ], width=4)
                        ])
                    ])
                ])
            ], width=12)
        ])
    ], className="p-3")


def create_data_management_layout():
    """Data Management Tab - Versioning, Backup, and Data Persistence Features"""
    return html.Div([
        # Hidden stores for data management functionality
        dcc.Store(id='data-management-store', data={}),
        dcc.Store(id='version-history-store', data={}),
        dcc.Store(id='backup-list-store', data={}),
        
        # Header with Status
        dbc.Row([
            dbc.Col([
                html.H3([
                    html.I(className="fas fa-database me-2"),
                    "Data Management & Versioning"
                ], className="mb-3"),
                html.Div(id="data-status-alert")
            ], width=12)
        ]),

        # Main Layout: 3 Columns
        dbc.Row([
            # Column 1: Current Data Status & Quick Actions (4 columns)
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H5([
                            html.I(className="fas fa-info-circle me-2"),
                            "Data Status"
                        ], className="mb-0")
                    ]),
                    dbc.CardBody([
                        html.Div(id="current-data-summary"),
                        html.Hr(),
                        html.H6("Quick Actions"),
                        dbc.ButtonGroup([
                            dbc.Button([
                                html.I(className="fas fa-save me-2"),
                                "Save Now"
                            ], id="save-data-btn", color="primary", size="sm"),
                            dbc.Button([
                                html.I(className="fas fa-download me-2"),
                                "Export"
                            ], id="export-data-btn", color="success", size="sm"),
                            dbc.Button([
                                html.I(className="fas fa-undo me-2"),
                                "Reset"
                            ], id="reset-data-btn", color="warning", size="sm")
                        ], className="d-grid gap-2 mb-3"),
                        
                        # Save with Description
                        html.Hr(),
                        html.H6("Save with Description"),
                        dbc.InputGroup([
                            dbc.Input(
                                id="save-description-input",
                                placeholder="Describe your changes...",
                                type="text"
                            ),
                            dbc.Button([
                                html.I(className="fas fa-save me-1"),
                                "Save"
                            ], id="save-with-description-btn", color="primary")
                        ], className="mb-2")
                    ])
                ])
            ], width=4),

            # Column 2: Version History & Management (4 columns)
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H5([
                            html.I(className="fas fa-history me-2"),
                            "Version History"
                        ], className="mb-0")
                    ]),
                    dbc.CardBody([
                        dbc.Button([
                            html.I(className="fas fa-sync me-2"),
                            "Refresh History"
                        ], id="refresh-versions-btn", color="info", size="sm", className="mb-3"),
                        
                        html.Div(id="version-history-list"),
                        
                        html.Hr(),
                        html.H6("Version Actions"),
                        dbc.Row([
                            dbc.Col([
                                dbc.Select(
                                    id="version-select",
                                    placeholder="Select version...",
                                    options=[]
                                )
                            ], width=8),
                            dbc.Col([
                                dbc.Button([
                                    html.I(className="fas fa-undo-alt me-1"),
                                    "Revert"
                                ], id="revert-version-btn", color="warning", size="sm")
                            ], width=4)
                        ])
                    ])
                ])
            ], width=4),

            # Column 3: Backup Management & Change Log (4 columns)
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H5([
                            html.I(className="fas fa-shield-alt me-2"),
                            "Backups & Changes"
                        ], className="mb-0")
                    ]),
                    dbc.CardBody([
                        # Backup Section
                        html.H6("Backup Management"),
                        dbc.Button([
                            html.I(className="fas fa-sync me-2"),
                            "Refresh Backups"
                        ], id="refresh-backups-btn", color="info", size="sm", className="mb-2"),
                        
                        html.Div(id="backup-list"),
                        
                        html.Hr(),
                        html.H6("Recent Changes"),
                        dbc.Button([
                            html.I(className="fas fa-list me-2"),
                            "View Change Log"
                        ], id="view-changes-btn", color="secondary", size="sm", className="mb-2"),
                        
                        html.Div(id="recent-changes-list")
                    ])
                ])
            ], width=4)
        ], className="mb-4"),

        # Bottom Section: Detailed Views & Comparison Tools
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H5([
                            html.I(className="fas fa-tools me-2"),
                            "Advanced Tools"
                        ], className="mb-0")
                    ]),
                    dbc.CardBody([
                        dbc.Tabs([
                            dbc.Tab(label="Change Details", tab_id="change-details"),
                            dbc.Tab(label="Version Comparison", tab_id="version-compare"),
                            dbc.Tab(label="Import/Export", tab_id="import-export")
                        ], id="advanced-tools-tabs", active_tab="change-details"),
                        
                        html.Div(id="advanced-tools-content", className="mt-3")
                    ])
                ])
            ], width=12)
        ]),

        # Status Messages
        html.Div(id="data-management-messages", className="mt-3")
    ], className="p-3")


# Original remaining functions continue below...


def create_subscription_management_layout():
    """Subscription Management Tab - Account Settings and Billing"""
    return html.Div([
        # Header
        html.H3("Account & Subscription Management", className="mb-4"),

        # Current Subscription Status
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.I(
                                className="fas fa-crown fa-3x text-warning mb-3"),
                            html.H4("Standard Plan", className="text-primary"),
                            html.P("£9.99/month", className="text-muted mb-3"),
                            html.Small("Next billing: August 19, 2025",
                                       className="text-muted")
                        ], className="text-center")
                    ])
                ], className="border-warning")
            ], width=3),
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("This Month's Usage"),
                    dbc.CardBody([
                        html.Div([
                            html.H5("2 of 10", className="text-primary"),
                            html.Small("Recommendations Used"),
                            dbc.Progress(value=20, className="mt-2 mb-3"),
                            html.Small("8 recommendations remaining",
                                       className="text-muted")
                        ])
                    ])
                ])
            ], width=4),
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Account Value"),
                    dbc.CardBody([
                        html.H4("£42,350", className="text-success mb-2"),
                        html.Small([
                            html.I(className="fas fa-arrow-up text-success me-1"),
                            "+£2,340 this month"
                        ], className="text-muted")
                    ])
                ])
            ], width=5)
        ], className="mb-4"),

        # Subscription Tiers Comparison
        dbc.Card([
            dbc.CardHeader([
                html.H5("📊 Subscription Plans Comparison", className="mb-0")
            ]),
            dbc.CardBody([
                dbc.Row([
                    # Standard Tier (Current)
                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader([
                                html.H6(
                                    "Standard", className="mb-0 text-center"),
                                dbc.Badge("CURRENT", color="success",
                                          className="ms-2")
                            ]),
                            dbc.CardBody([
                                html.H4("£9.99", className="text-center mb-1"),
                                html.Small(
                                    "/month", className="text-center d-block mb-3"),
                                html.Ul([
                                    html.Li("5-10 monthly recommendations"),
                                    html.Li("Automated rebalancing"),
                                    html.Li("Real-time price alerts"),
                                    html.Li("Email support (48hr)")
                                ], className="text-sm"),
                                dbc.Button("Current Plan", disabled=True,
                                           color="success", className="w-100 mt-3")
                            ])
                        ], className="h-100 border-success")
                    ], width=4),

                    # Premium Tier
                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader([
                                html.H6(
                                    "Premium", className="mb-0 text-center"),
                                dbc.Badge("POPULAR", color="warning",
                                          className="ms-2")
                            ]),
                            dbc.CardBody([
                                html.H4("£29.99", className="text-center mb-1"),
                                html.Small(
                                    "/month", className="text-center d-block mb-3"),
                                html.Ul([
                                    html.Li("Unlimited recommendations"),
                                    html.Li("Advanced opportunity scanning"),
                                    html.Li("Tax optimization"),
                                    html.Li("Priority support (24hr)")
                                ], className="text-sm"),
                                dbc.Button(
                                    "Upgrade to Premium", color="warning", className="w-100 mt-3")
                            ])
                        ], className="h-100 border-warning")
                    ], width=4),

                    # Enterprise Tier
                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader([
                                html.H6("Enterprise",
                                        className="mb-0 text-center")
                            ]),
                            dbc.CardBody([
                                html.H4("Custom", className="text-center mb-3"),
                                html.Ul([
                                    html.Li("Multiple portfolios"),
                                    html.Li("Family accounts"),
                                    html.Li("Dedicated support"),
                                    html.Li("API access")
                                ], className="text-sm"),
                                dbc.Button("Contact Sales",
                                           color="info", className="w-100 mt-3")
                            ])
                        ], className="h-100")
                    ], width=4)
                ])
            ])
        ], className="mb-4"),

        # Payment Information
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H5("💳 Payment Method", className="mb-0")
                    ]),
                    dbc.CardBody([
                        html.Div([
                            html.I(className="fab fa-cc-visa fa-2x me-3"),
                            html.Div([
                                html.Strong("Visa ending in 4242"),
                                html.Br(),
                                html.Small("Expires 12/2026",
                                           className="text-muted")
                            ], className="d-inline-block")
                        ], className="mb-3"),
                        dbc.Button("Update Payment Method",
                                   color="outline-primary", size="sm")
                    ])
                ])
            ], width=6),
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H5("📄 Recent Billing", className="mb-0")
                    ]),
                    dbc.CardBody([
                        html.Div([
                            html.Div([
                                html.Strong("July 19, 2025"),
                                html.Span(" - £9.99", className="float-end")
                            ], className="mb-1"),
                            html.Div([
                                html.Strong("June 19, 2025"),
                                html.Span(" - £9.99", className="float-end")
                            ], className="mb-1"),
                            html.Div([
                                html.Strong("May 19, 2025"),
                                html.Span(" - £9.99", className="float-end")
                            ], className="mb-3")
                        ]),
                        dbc.Button("View All Invoices",
                                   color="outline-info", size="sm")
                    ])
                ])
            ], width=6)
        ], className="mb-4"),

        # Upgrade Promotion
        dbc.Card([
            dbc.CardHeader([
                html.H5("🚀 Unlock Premium Features", className="mb-0")
            ]),
            dbc.CardBody([
                html.P(
                    "You're missing out on advanced features that could boost your returns:", className="mb-3"),
                dbc.Alert([
                    html.I(className="fas fa-gift me-2"),
                    html.Strong("Special Offer: "),
                    "Upgrade to Premium now and get your first month for just £19.99 (33% off)"
                ], color="success", className="mb-3"),
                dbc.Button("Upgrade to Premium Now",
                           color="warning", size="lg")
            ])
        ])
    ], className="p-3")


def calculate_monthly_debt_payments(mortgage_balance, mortgage_rate, mortgage_years,
                                    credit_cards, credit_cards_rate, credit_cards_payment,
                                    personal_loans, personal_loans_rate, personal_loans_years,
                                    student_loans, student_loans_rate, student_loans_payment,
                                    other_debts, other_debts_rate, other_debts_payment):
    """Calculate total monthly debt payments including interest calculations"""

    total_payments = 0

    # Calculate mortgage payment using standard loan formula
    if mortgage_balance and mortgage_rate and mortgage_years:
        monthly_rate = (mortgage_rate / 100) / 12
        num_payments = mortgage_years * 12
        if monthly_rate > 0:
            mortgage_payment = mortgage_balance * \
                (monthly_rate * (1 + monthly_rate)**num_payments) / \
                ((1 + monthly_rate)**num_payments - 1)
            total_payments += mortgage_payment

    # Add credit card payments (user-specified)
    if credit_cards_payment:
        total_payments += credit_cards_payment

    # Calculate personal loan payment using standard loan formula
    if personal_loans and personal_loans_rate and personal_loans_years:
        monthly_rate = (personal_loans_rate / 100) / 12
        num_payments = personal_loans_years * 12
        if monthly_rate > 0:
            personal_loan_payment = personal_loans * \
                (monthly_rate * (1 + monthly_rate)**num_payments) / \
                ((1 + monthly_rate)**num_payments - 1)
            total_payments += personal_loan_payment

    # Add student loan payments (user-specified)
    if student_loans_payment:
        total_payments += student_loans_payment

    # Add other debt payments (user-specified)
    if other_debts_payment:
        total_payments += other_debts_payment

    return total_payments


def create_breakdown_display(items):
    """Create a breakdown display for income or expenses"""
    breakdown = []
    for name, amount in items:
        if amount > 0:
            breakdown.append(
                html.Div([
                    html.Span(name, className="me-auto"),
                    html.Span(f"£{amount:,.0f}", className="text-end")
                ], className="d-flex justify-content-between mb-1")
            )

    if not breakdown:
        breakdown = [html.Small("No data entered yet", className="text-muted")]

    return breakdown


def register_personal_mode_callbacks(app):
    """Register all Personal Mode callbacks for modal functionality"""

    # Modal toggle callback for manual entry
    @app.callback(
        Output("manual-entry-modal", "is_open"),
        [Input("open-manual-entry-btn", "n_clicks"),
         Input("cancel-manual-entry", "n_clicks"),
         Input("save-manual-entry", "n_clicks")],
        [State("manual-entry-modal", "is_open")]
    )
    def toggle_manual_entry_modal(open_clicks, cancel_clicks, save_clicks, is_open):
        """Toggle the manual entry modal"""
        ctx = callback_context
        if not ctx.triggered:
            return False

        button_id = ctx.triggered[0]["prop_id"].split(".")[0]

        if button_id == "open-manual-entry-btn" and open_clicks:
            return True
        elif button_id in ["cancel-manual-entry", "save-manual-entry"]:
            return False

        return is_open

    # Sample data loading callback
    @app.callback(
        [Output("gross-salary", "value"),
         Output("bonuses", "value"),
         Output("freelance", "value"),
         Output("rental-income", "value"),
         Output("dividends", "value"),
         Output("other-income", "value"),
         Output("rent-mortgage", "value"),
         Output("transport", "value"),
         Output("groceries", "value"),
         Output("utilities", "value"),
         Output("home-insurance", "value"),
         Output("entertainment", "value"),
         Output("home-value", "value"),
         Output("savings", "value"),
         Output("investments", "value"),
         Output("other-assets", "value"),
         Output("mortgage-balance", "value"),
         Output("mortgage-rate", "value"),
         Output("mortgage-years", "value"),
         Output("credit-cards", "value"),
         Output("credit-cards-rate", "value"),
         Output("personal-loans", "value"),
         Output("personal-loans-rate", "value"),
         Output("student-loans", "value"),
         Output("student-loans-rate", "value"),
         Output("other-debts", "value"),
         Output("other-debts-rate", "value")],
        Input("load-sample-data-btn", "n_clicks"),
        prevent_initial_call=True
    )
    def load_sample_data(n_clicks):
        """Load realistic sample financial data for demonstration"""
        if n_clicks:
            return (
                # Income values
                45000,  # gross-salary
                3000,   # bonuses
                800,    # freelance
                0,      # rental-income
                150,    # dividends
                200,    # other-income
                # Expense values
                1100,   # rent-mortgage
                280,    # transport
                350,    # groceries
                120,    # utilities
                85,     # home-insurance
                180,    # entertainment
                # Asset values
                220000,  # home-value
                8500,   # savings
                12000,  # investments
                3000,   # other-assets
                # Debt values
                180000,  # mortgage-balance
                3.2,    # mortgage-rate
                23,     # mortgage-years
                3200,   # credit-cards
                19.9,   # credit-cards-rate
                8500,   # personal-loans
                7.5,    # personal-loans-rate
                12000,  # student-loans
                4.2,    # student-loans-rate
                1500,   # other-debts
                11.5    # other-debts-rate
            )
        return [no_update] * 27

    # Financial calculation callbacks
    @app.callback(
        [Output("total-income-display", "children"),
         Output("total-expenses-display", "children"),
         Output("net-cashflow-display", "children"),
         Output("net-worth-display", "children"),
         Output("income-breakdown", "children"),
         Output("expenses-breakdown", "children")],
        [Input("save-manual-entry", "n_clicks")],
        [State("gross-salary", "value"),
         State("bonuses", "value"),
         State("freelance", "value"),
         State("rental-income", "value"),
         State("dividends", "value"),
         State("other-income", "value"),
         State("rent-mortgage", "value"),
         State("transport", "value"),
         State("groceries", "value"),
         State("utilities", "value"),
         State("home-insurance", "value"),
         State("entertainment", "value"),
         State("home-value", "value"),
         State("savings", "value"),
         State("investments", "value"),
         State("other-assets", "value"),
         State("mortgage-balance", "value"),
         State("mortgage-rate", "value"),
         State("mortgage-years", "value"),
         State("credit-cards", "value"),
         State("credit-cards-rate", "value"),
         State("credit-cards-payment", "value"),
         State("personal-loans", "value"),
         State("personal-loans-rate", "value"),
         State("personal-loans-years", "value"),
         State("student-loans", "value"),
         State("student-loans-rate", "value"),
         State("student-loans-payment", "value"),
         State("other-debts", "value"),
         State("other-debts-rate", "value"),
         State("other-debts-payment", "value")]
    )
    def update_financial_displays(n_clicks,
                                  gross_salary, bonuses, freelance, rental_income, dividends, other_income,
                                  rent_mortgage, transport, groceries, utilities, home_insurance,
                                  entertainment,
                                  home_value, savings, investments, other_assets,
                                  mortgage_balance, mortgage_rate, mortgage_years,
                                  credit_cards, credit_cards_rate, credit_cards_payment,
                                  personal_loans, personal_loans_rate, personal_loans_years,
                                  student_loans, student_loans_rate, student_loans_payment,
                                  other_debts, other_debts_rate, other_debts_payment):
        """Calculate and update financial displays with real financial calculations"""

        if not n_clicks:
            # Return default values if no data entered yet
            return "£0", "£0", "£0", "£0", [], []

        # Calculate total monthly income (convert annual values to monthly, apply UK tax)
        net_monthly_salary = calculate_uk_net_income(gross_salary or 0)
        monthly_bonuses = (bonuses or 0) / 12
        monthly_dividends = (dividends or 0) / 12
        total_income = sum([
            net_monthly_salary, monthly_bonuses, freelance or 0,
            rental_income or 0, monthly_dividends, other_income or 0
        ])

        # Calculate total monthly expenses (including calculated debt payments)
        calculated_debt_payments = calculate_monthly_debt_payments(
            mortgage_balance, mortgage_rate, mortgage_years,
            credit_cards, credit_cards_rate, credit_cards_payment,
            personal_loans, personal_loans_rate, personal_loans_years,
            student_loans, student_loans_rate, student_loans_payment,
            other_debts, other_debts_rate, other_debts_payment
        )

        total_expenses = sum([
            rent_mortgage or 0, transport or 0, groceries or 0,
            utilities or 0, home_insurance or 0, calculated_debt_payments,
            entertainment or 0
        ])

        # Calculate net cash flow
        net_cashflow = total_income - total_expenses

        # Calculate total assets
        total_assets = sum([
            home_value or 0, savings or 0,
            investments or 0, other_assets or 0
        ])        # Calculate total liabilities
        total_liabilities = sum([
            mortgage_balance or 0, credit_cards or 0,
            personal_loans or 0, student_loans or 0, other_debts or 0
        ])

        # Calculate net worth
        net_worth = total_assets - total_liabilities

        # Create income breakdown
        income_breakdown = create_breakdown_display([
            ("Gross Salary", gross_salary or 0),
            ("Bonuses", bonuses or 0),
            ("Freelance", freelance or 0),
            ("Rental Income", rental_income or 0),
            ("Dividends", dividends or 0),
            ("Other Income", other_income or 0)
        ])

        # Create expenses breakdown
        expenses_breakdown = create_breakdown_display([
            ("Rent/Mortgage", rent_mortgage or 0),
            ("Transport", transport or 0),
            ("Groceries", groceries or 0),
            ("Utilities", utilities or 0),
            ("Home Insurance", home_insurance or 0),
            ("Debt Payments", calculated_debt_payments),
            ("Entertainment", entertainment or 0)
        ])

        return (
            f"£{total_income:,.0f}",
            f"£{total_expenses:,.0f}",
            f"£{net_cashflow:,.0f}",
            f"£{net_worth:,.0f}",
            income_breakdown,
            expenses_breakdown
        )

    # CRITICAL FIX: Update financial data store for other callbacks to use
    @app.callback(
        Output("financial-data-store", "data"),
        [Input("save-manual-entry", "n_clicks")],
        [State("gross-salary", "value"),
         State("bonuses", "value"),
         State("freelance", "value"),
         State("rental-income", "value"),
         State("dividends", "value"),
         State("other-income", "value"),
         State("rent-mortgage", "value"),
         State("transport", "value"),
         State("groceries", "value"),
         State("utilities", "value"),
         State("home-insurance", "value"),
         State("entertainment", "value"),
         State("home-value", "value"),
         State("savings", "value"),
         State("investments", "value"),
         State("other-assets", "value"),
         State("mortgage-balance", "value"),
         State("credit-cards", "value"),
         State("personal-loans", "value"),
         State("student-loans", "value"),
         State("other-debts", "value")]
    )
    def update_financial_data_store(n_clicks, gross_salary, bonuses, freelance, rental_income, 
                                  dividends, other_income, rent_mortgage, transport, groceries, 
                                  utilities, home_insurance, entertainment, home_value, savings, 
                                  investments, other_assets, mortgage_balance, credit_cards, 
                                  personal_loans, student_loans, other_debts):
        """Store financial data for use by dashboard callbacks and save to persistence system"""
        if not n_clicks:
            return {}
        
        # Create financial data dictionary for the dashboard
        dashboard_data = {
            'gross_salary': gross_salary or 0,
            'bonuses': bonuses or 0,
            'freelance': freelance or 0,
            'rental_income': rental_income or 0,
            'dividends': dividends or 0,
            'other_income': other_income or 0,
            'housing_costs': (rent_mortgage or 0) * 12,  # Convert to annual
            'transport': (transport or 0) * 12,  # Convert to annual
            'groceries': (groceries or 0) * 12,  # Convert to annual
            'utilities': (utilities or 0) * 12,  # Convert to annual
            'home_insurance': (home_insurance or 0) * 12,  # Convert to annual
            'entertainment': (entertainment or 0) * 12,  # Convert to annual
            'home_value': home_value or 0,
            'savings': savings or 0,
            'investments': investments or 0,
            'other_assets': other_assets or 0,
            'mortgage': mortgage_balance or 0,
            'credit_cards': credit_cards or 0,
            'personal_loans': personal_loans or 0,
            'student_loans': student_loans or 0,
            'other_debts': other_debts or 0
        }
        
        # Create persistence data dictionary (using the structure expected by UserDataManager)
        persistence_data = {
            "personal_info": {
                "name": "",
                "age": 30,
                "location": "UK",
                "currency": "GBP"
            },
            "income": {
                "gross_salary": gross_salary or 0,
                "bonuses": bonuses or 0,
                "freelance": freelance or 0,
                "benefits": 0,  # Not captured in this form
                "other_income": (rental_income or 0) + (dividends or 0) + (other_income or 0)
            },
            "housing": {
                "mortgage_rent": rent_mortgage or 0,
                "insurance": home_insurance or 0,
                "utilities": utilities or 0,
                "maintenance": 0,  # Not captured in this form
                "council_tax": 0   # Not captured in this form
            },
            "transport": {
                "car_payment": transport or 0,
                "fuel": 0,
                "insurance": 0,
                "maintenance": 0,
                "public_transport": 0
            },
            "lifestyle": {
                "food_groceries": groceries or 0,
                "dining_out": 0,
                "entertainment": entertainment or 0,
                "subscriptions": 0,
                "clothing": 0,
                "healthcare": 0,
                "personal_care": 0,
                "miscellaneous": 0
            },
            "financial": {
                "savings_account": savings or 0,
                "checking_account": 0,
                "investments": investments or 0,
                "retirement": 0,
                "emergency_fund": 0
            },
            "debts": {
                "mortgage_balance": mortgage_balance or 0,
                "car_loan": 0,
                "student_loans": student_loans or 0,
                "credit_cards": credit_cards or 0,
                "other_debt": (personal_loans or 0) + (other_debts or 0)
            },
            "goals": {
                "retirement_age": 65,
                "target_retirement_income": 3000,
                "house_deposit_target": 50000,
                "emergency_fund_months": 6
            },
            "metadata": {
                "created_date": None,
                "last_updated": None,
                "version": "1.0",
                "data_source": "manual_entry"
            }
        }
        
        # Save to persistence system
        try:
            result = user_data_manager.save_user_data(
                persistence_data, 
                create_backup=True, 
                change_description="Financial profile saved from Data Input"
            )
            if result["success"]:
                print(f"✅ Financial data saved successfully: {result['message']}")
            else:
                print(f"❌ Failed to save financial data: {result['message']}")
        except Exception as e:
            print(f"❌ Error saving financial data: {str(e)}")
        
        return dashboard_data

    # Portfolio Allocation Donut Chart Callback
    @app.callback(
        Output("portfolio-allocation-donut", "figure"),
        [Input("allocation-stocks-slider", "value"),
         Input("allocation-etfs-slider", "value"),
         Input("allocation-bonds-slider", "value")]
    )
    def update_portfolio_allocation_donut(stocks_pct, etfs_pct, bonds_pct):
        """Update portfolio allocation donut chart"""
        import plotly.graph_objs as go

        # Default values if None
        stocks_pct = stocks_pct or 40
        etfs_pct = etfs_pct or 35
        bonds_pct = bonds_pct or 25

        # Calculate total to normalize if needed
        total_allocation = stocks_pct + etfs_pct + bonds_pct
        if total_allocation != 100:
            # Normalize to 100%
            stocks_pct = (stocks_pct / total_allocation) * 100
            etfs_pct = (etfs_pct / total_allocation) * 100
            bonds_pct = (bonds_pct / total_allocation) * 100

        # Create donut chart
        fig = go.Figure(data=[go.Pie(
            labels=['📈 Stocks', '📊 ETFs', '🏛️ Bonds'],
            values=[stocks_pct, etfs_pct, bonds_pct],
            hole=0.4,
            marker_colors=['#007bff', '#17a2b8', '#28a745'],
            textinfo='label+percent',
            textfont={'size': 14},
            hovertemplate='<b>%{label}</b><br>Allocation: %{percent}<br>Value: £%{value:,.0f}<extra></extra>',
            showlegend=True
        )])

        fig.update_layout(
            title={
                'text': 'Portfolio Allocation Breakdown',
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 16}
            },
            height=400,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            legend={
                'orientation': 'h',
                'yanchor': 'bottom',
                'y': -0.2,
                'xanchor': 'center',
                'x': 0.5
            },
            margin={'l': 20, 'r': 20, 't': 60, 'b': 80}
        )

        return fig

    # Total Allocation Display Callback
    @app.callback(
        Output("total-allocation-display", "children"),
        [Input("allocation-stocks-slider", "value"),
         Input("allocation-etfs-slider", "value"),
         Input("allocation-bonds-slider", "value")]
    )
    def update_total_allocation_display(stocks_pct, etfs_pct, bonds_pct):
        """Update total allocation percentage display"""
        stocks_pct = stocks_pct or 40
        etfs_pct = etfs_pct or 35
        bonds_pct = bonds_pct or 25
        
        total = stocks_pct + etfs_pct + bonds_pct
        
        if total == 100:
            return f"{total}%"
        elif total < 100:
            return f"{total}% (Under-allocated)"
        else:
            return f"{total}% (Over-allocated)"


# Initialize the Dash app (outside __main__ block for imports)
import dash
from dash import Dash, dcc, html
import dash_bootstrap_components as dbc

app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "Financial Optimizer - Personal Mode"

if __name__ == "__main__":
    # Set up the layout
    app.layout = create_personal_mode_layout()
    
    # Register all Personal Mode callbacks (data input modal, sample data, financial calculations)
    register_personal_mode_callbacks(app)
    
    # Register dashboard callbacks (control panel sliders → chart connections)
    try:
        from modules.personal_mode.callbacks.dashboard_callbacks import register_dashboard_callbacks
        register_dashboard_callbacks(app)
        print("✅ FINANCIAL DASHBOARD CALLBACKS REGISTERED")
        print("✅ CONTROL PANEL → CHART CONNECTIONS ACTIVE")
        print("✅ DATA INPUT MODAL → CHART CONNECTIONS ACTIVE")
        print("✅ REAL-TIME IMPACT DISPLAYS ACTIVE")
    except ImportError as e:
        print(f"⚠️ Warning: Could not register dashboard callbacks: {e}")
    except Exception as e:
        print(f"❌ Error registering dashboard callbacks: {e}")
    
    # Register data management callbacks (Data Management tab functionality)
    try:
        from modules.personal_mode.callbacks.data_management_callbacks import register_data_management_callbacks
        register_data_management_callbacks(app)
        print("✅ DATA MANAGEMENT CALLBACKS REGISTERED")
        print("✅ VERSION HISTORY → UI CONNECTIONS ACTIVE")
        print("✅ BACKUP MANAGEMENT → UI CONNECTIONS ACTIVE") 
        print("✅ CHANGE LOG → UI CONNECTIONS ACTIVE")
    except ImportError as e:
        print(f"⚠️ Warning: Could not register data management callbacks: {e}")
    except Exception as e:
        print(f"❌ Error registering data management callbacks: {e}")
    
    print("🚀 Starting Financial Optimizer Personal Mode...")
    print("📊 Enhanced Financial Control Panel - Phase 2.5 Implementation")
    print("🔗 16 Control Panel Sliders → Financial Chart Updates")
    print("📝 27 Data Input Fields → Chart & Control Panel Updates")
    print("⏱️ Real-time Time Range Controls")
    print("💡 Current vs Projected Impact Displays")
    print("")
    print("🌐 App running at: http://127.0.0.1:8050/")
    print("=" * 60)
    
    # Run the app
    app.run_server(debug=True, host='0.0.0.0', port=8050)
