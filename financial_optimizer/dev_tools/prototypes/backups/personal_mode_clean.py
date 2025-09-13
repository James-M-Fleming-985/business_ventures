#!/usr/bin/env python3
"""
Personal Mode Module - Subscription Add-on for Financial Optimizer
Implements portfolio management functionality for Standard tier subscribers.
"""

from dash import html, dcc
import dash_bootstrap_components as dbc


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

        # Analysis Tab - Mathematical Modeling Engine
        dbc.Tab(label="Analysis", children=[
            create_analysis_tab_layout()
        ]),

        # Data Input Tab - Document Processing and Cash Flow
        dbc.Tab(label="Data Input", children=[
            create_data_input_tab_layout()
        ]),

        # Subscription Management - Account and Billing
        dbc.Tab(label="Account", children=[
            create_subscription_management_layout()
        ])
    ])


def create_financial_dashboard_layout():
    """Financial Dashboard - Primary Command Center with Charts and Advanced Controls"""
    return html.Div([
        # Header with Subscription Status
        dbc.Row([
            dbc.Col([
                html.H3("Personal Financial Dashboard", className="mb-3"),
                dbc.Alert([
                    html.I(className="fas fa-crown me-2"),
                    "Standard Subscription Active - ",
                    html.Strong("Real-time Portfolio Tracking")
                ], color="success", className="mb-4")
            ], width=8),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4("£42,350", className="text-success mb-0"),
                        html.Small("Total Net Worth", className="text-muted"),
                        html.Div([
                            html.I(className="fas fa-arrow-up text-success me-1"),
                            html.Span("+£2,340 (5.8%)",
                                      className="text-success")
                        ], className="mt-1")
                    ], className="text-center")
                ], className="border-success")
            ], width=4)
        ], className="mb-4"),

        # Key Performance Metrics Row
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("Portfolio Value", className="card-title"),
                        html.H3("£38,420", className="text-primary mb-2"),
                        html.Small([
                            html.I(
                                className="fas fa-chart-line text-primary me-1"),
                            "+12.3% YTD"
                        ], className="text-muted")
                    ])
                ])
            ], width=3),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("Cash Flow", className="card-title"),
                        html.H3("£1,850", className="text-info mb-2"),
                        html.Small([
                            html.I(className="fas fa-calendar text-info me-1"),
                            "Monthly Available"
                        ], className="text-muted")
                    ])
                ])
            ], width=3),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("Risk Score", className="card-title"),
                        html.H3("5/10", className="text-warning mb-2"),
                        html.Small([
                            html.I(
                                className="fas fa-shield-alt text-warning me-1"),
                            "Moderate Risk"
                        ], className="text-muted")
                    ])
                ])
            ], width=3),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("Goal Progress", className="card-title"),
                        html.H3("67%", className="text-success mb-2"),
                        html.Small([
                            html.I(className="fas fa-target text-success me-1"),
                            "Retirement Goal"
                        ], className="text-muted")
                    ])
                ])
            ], width=3)
        ], className="mb-4"),

        # Interactive Charts Section
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H5("📈 Portfolio Performance",
                                className="mb-0 d-inline"),
                        dbc.ButtonGroup([
                            dbc.Button("1M", size="sm",
                                       outline=True, active=True),
                            dbc.Button("6M", size="sm", outline=True),
                            dbc.Button("1Y", size="sm", outline=True),
                            dbc.Button("5Y", size="sm", outline=True)
                        ], className="float-end")
                    ]),
                    dbc.CardBody([
                        html.Div([
                            html.Div("Portfolio Performance Chart Placeholder",
                                     className="text-center p-5 bg-light border rounded",
                                     style={"height": "300px", "display": "flex", "align-items": "center", "justify-content": "center"})
                        ])
                    ])
                ])
            ], width=8),
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H5("🍩 Asset Allocation", className="mb-0")
                    ]),
                    dbc.CardBody([
                        html.Div([
                            html.Div("Asset Allocation Donut Chart",
                                     className="text-center p-4 bg-light border rounded",
                                     style={"height": "200px", "display": "flex", "align-items": "center", "justify-content": "center"})
                        ]),
                        html.Hr(),
                        html.Div([
                            html.Div([
                                html.Span(
                                    "●", style={"color": "#007bff", "font-size": "20px"}),
                                " Stocks 40%"
                            ], className="mb-1"),
                            html.Div([
                                html.Span(
                                    "●", style={"color": "#28a745", "font-size": "20px"}),
                                " ETFs 35%"
                            ], className="mb-1"),
                            html.Div([
                                html.Span(
                                    "●", style={"color": "#ffc107", "font-size": "20px"}),
                                " Bonds 25%"
                            ], className="mb-1")
                        ])
                    ])
                ])
            ], width=4)
        ], className="mb-4"),

        # Advanced Modeling Controls
        dbc.Card([
            dbc.CardHeader([
                html.H5("🎛️ Advanced Modeling Controls",
                        className="mb-0 d-inline"),
                dbc.Badge("Premium Feature", color="warning", className="ms-2")
            ]),
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        html.Label("Time Horizon (Years):",
                                   className="fw-bold"),
                        dcc.Slider(
                            id="time-horizon-slider",
                            min=1, max=20, step=1, value=10,
                            marks={1: '1Y', 5: '5Y', 10: '10Y',
                                   15: '15Y', 20: '20Y'},
                            tooltip={"placement": "bottom",
                                     "always_visible": True}
                        )
                    ], width=4),
                    dbc.Col([
                        html.Label("Market Scenario:", className="fw-bold"),
                        dcc.Dropdown(
                            id="market-scenario-dropdown",
                            options=[
                                {"label": "🐂 Bull Market", "value": "bull"},
                                {"label": "🐻 Bear Market", "value": "bear"},
                                {"label": "➡️ Neutral Market", "value": "neutral"},
                                {"label": "📊 Historical Average",
                                    "value": "historical"}
                            ],
                            value="historical",
                            className="mb-3"
                        )
                    ], width=4),
                    dbc.Col([
                        html.Label("Monte Carlo Runs:", className="fw-bold"),
                        dcc.Dropdown(
                            id="monte-carlo-runs",
                            options=[
                                {"label": "1,000 simulations", "value": 1000},
                                {"label": "10,000 simulations", "value": 10000},
                                {"label": "100,000 simulations", "value": 100000}
                            ],
                            value=10000,
                            className="mb-3"
                        )
                    ], width=4)
                ], className="mb-3"),
                dbc.Row([
                    dbc.Col([
                        dbc.Button("Run Analysis", color="primary",
                                   className="me-2"),
                        dbc.Button("Save Scenario", color="success",
                                   outline=True, className="me-2"),
                        dbc.Button("Export Results",
                                   color="info", outline=True)
                    ])
                ])
            ])
        ], className="mb-4"),

        # Goal Tracking Section
        dbc.Card([
            dbc.CardHeader([
                html.H5("🎯 Financial Goals Tracking", className="mb-0")
            ]),
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        html.H6("Retirement Fund"),
                        dbc.Progress(value=67, color="success",
                                     className="mb-2"),
                        html.Small("£134,000 / £200,000 target",
                                   className="text-muted")
                    ], width=4),
                    dbc.Col([
                        html.H6("Emergency Fund"),
                        dbc.Progress(value=85, color="info", className="mb-2"),
                        html.Small("£8,500 / £10,000 target",
                                   className="text-muted")
                    ], width=4),
                    dbc.Col([
                        html.H6("House Deposit"),
                        dbc.Progress(value=42, color="warning",
                                     className="mb-2"),
                        html.Small("£21,000 / £50,000 target",
                                   className="text-muted")
                    ], width=4)
                ])
            ])
        ])
    ], className="p-3")


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
                            'grid-template-columns': 'repeat(auto-fit, minmax(300px, 1fr))',
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
                                   "align-items": "center", "justify-content": "center"}
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
                                   "align-items": "center", "justify-content": "center"}
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
    """Data Input Tab - Document Processing and Cash Flow Analysis"""
    return html.Div([
        # Header
        html.H3("Personal Finance Data Input", className="mb-4"),

        dbc.Alert([
            html.I(className="fas fa-upload me-2"),
            "Upload your financial documents for automated analysis and cash flow calculation"
        ], color="info", className="mb-4"),

        # Document Upload Section
        dbc.Card([
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
                                html.I(
                                    className="fas fa-cloud-upload-alt fa-3x mb-3"),
                                html.Br(),
                                "Drag & Drop or Click to Upload",
                                html.Br(),
                                html.Small("PDF, CSV, Excel files",
                                           className="text-muted")
                            ]),
                            style={
                                'width': '100%', 'height': '120px', 'lineHeight': '120px',
                                'borderWidth': '2px', 'borderStyle': 'dashed', 'borderRadius': '10px',
                                'textAlign': 'center', 'margin': '10px'
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
                                html.Small("JPG, PNG, PDF",
                                           className="text-muted")
                            ]),
                            style={
                                'width': '100%', 'height': '120px', 'lineHeight': '120px',
                                'borderWidth': '2px', 'borderStyle': 'dashed', 'borderRadius': '10px',
                                'textAlign': 'center', 'margin': '10px'
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
                                'borderWidth': '2px', 'borderStyle': 'dashed', 'borderRadius': '10px',
                                'textAlign': 'center', 'margin': '10px'
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
        ], className="mb-4"),

        # Cash Flow Analysis Results
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H5("💰 Income Analysis", className="mb-0")
                    ]),
                    dbc.CardBody([
                        html.H4("£4,250", className="text-success mb-3"),
                        html.Div([
                            html.Div([
                                html.Strong("Salary: "),
                                html.Span("£3,800")
                            ], className="mb-1"),
                            html.Div([
                                html.Strong("Freelance: "),
                                html.Span("£350")
                            ], className="mb-1"),
                            html.Div([
                                html.Strong("Investments: "),
                                html.Span("£100")
                            ], className="mb-1")
                        ])
                    ])
                ])
            ], width=4),
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H5("💳 Expense Analysis", className="mb-0")
                    ]),
                    dbc.CardBody([
                        html.H4("£2,400", className="text-danger mb-3"),
                        html.Div([
                            html.Div([
                                html.Strong("Housing: "),
                                html.Span("£1,200")
                            ], className="mb-1"),
                            html.Div([
                                html.Strong("Food: "),
                                html.Span("£400")
                            ], className="mb-1"),
                            html.Div([
                                html.Strong("Transport: "),
                                html.Span("£300")
                            ], className="mb-1"),
                            html.Div([
                                html.Strong("Other: "),
                                html.Span("£500")
                            ], className="mb-1")
                        ])
                    ])
                ])
            ], width=4),
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H5("📊 Available to Invest", className="mb-0")
                    ]),
                    dbc.CardBody([
                        html.H4("£1,850", className="text-primary mb-3"),
                        html.Small("Monthly surplus after expenses",
                                   className="text-muted mb-3"),
                        html.Br(),
                        html.Label("Invest Percentage:",
                                   className="fw-bold mt-3"),
                        dcc.Slider(
                            id="invest-percentage-slider",
                            min=0, max=100, step=5, value=80,
                            marks={0: '0%', 25: '25%', 50: '50%',
                                   75: '75%', 100: '100%'},
                            tooltip={"placement": "bottom",
                                     "always_visible": True}
                        ),
                        html.H5("£1,480 to invest", className="text-info mt-3")
                    ])
                ])
            ], width=4)
        ], className="mb-4"),

        # Spending Optimization
        dbc.Card([
            dbc.CardHeader([
                html.H5("📈 AI Spending Optimization", className="mb-0")
            ]),
            dbc.CardBody([
                html.P(
                    "AI-powered spending analysis and optimization suggestions:", className="mb-3"),
                dbc.Row([
                    dbc.Col([
                        dbc.Alert([
                            html.I(className="fas fa-lightbulb me-2"),
                            html.Strong("Dining Out: "),
                            "You spent £320 on restaurants this month. Consider reducing to £200 to free up £120 for investments."
                        ], color="warning")
                    ], width=6),
                    dbc.Col([
                        dbc.Alert([
                            html.I(className="fas fa-shopping-cart me-2"),
                            html.Strong("Subscriptions: "),
                            "You have £85 in recurring subscriptions. Cancel unused services to save £25/month."
                        ], color="info")
                    ], width=6)
                ])
            ])
        ])
    ], className="p-3")


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
