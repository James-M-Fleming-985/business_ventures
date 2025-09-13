#!/usr/bin/env python3
"""
Market Dashboard Layout for Personal Mode
Real-time market monitoring and analysis tools
"""

from dash import html, dcc
import dash_bootstrap_components as dbc


def create_market_dashboard_layout():
    """Market Dashboard - Real-time market monitoring and analysis"""
    return html.Div([
        # Header
        html.H3("Market Dashboard", className="mb-4"),

        dbc.Alert([
            html.I(className="fas fa-chart-area me-2"),
            "Real-time market monitoring and advanced market analysis tools"
        ], color="info", className="mb-4"),

        # Market Overview Cards
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("S&P 500", className="card-title"),
                        html.H3("4,185.47", className="text-success mb-2"),
                        html.Small([
                            html.I(className="fas fa-arrow-up text-success me-1"),
                            "+24.32 (+0.58%)"
                        ], className="text-muted")
                    ])
                ])
            ], width=3),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("FTSE 100", className="card-title"),
                        html.H3("7,234.15", className="text-success mb-2"),
                        html.Small([
                            html.I(className="fas fa-arrow-up text-success me-1"),
                            "+12.45 (+0.17%)"
                        ], className="text-muted")
                    ])
                ])
            ], width=3),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("NASDAQ", className="card-title"),
                        html.H3("12,967.83", className="text-danger mb-2"),
                        html.Small([
                            html.I(className="fas fa-arrow-down text-danger me-1"),
                            "-45.67 (-0.35%)"
                        ], className="text-muted")
                    ])
                ])
            ], width=3),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("VIX", className="card-title"),
                        html.H3("18.45", className="text-warning mb-2"),
                        html.Small([
                            html.I(
                                className="fas fa-exclamation-triangle text-warning me-1"),
                            "Moderate Volatility"
                        ], className="text-muted")
                    ])
                ])
            ], width=3)
        ], className="mb-4"),

        # Market Analysis Tools
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H5("📈 Market Trends", className="mb-0 d-inline"),
                        dbc.ButtonGroup([
                            dbc.Button("1D", size="sm",
                                       outline=True, active=True),
                            dbc.Button("5D", size="sm", outline=True),
                            dbc.Button("1M", size="sm", outline=True),
                            dbc.Button("YTD", size="sm", outline=True)
                        ], className="float-end")
                    ]),
                    dbc.CardBody([
                        html.Div([
                            html.Div("Market Trends Chart Placeholder",
                                     className="text-center p-5 bg-light border rounded",
                                     style={"height": "300px", "display": "flex",
                                            "align-items": "center", "justify-content": "center"})
                        ])
                    ])
                ])
            ], width=8),
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H5("🔥 Market Movers", className="mb-0")
                    ]),
                    dbc.CardBody([
                        html.H6("Top Gainers", className="text-success mb-3"),
                        html.Div([
                            html.Div([
                                html.Strong("NVDA"),
                                html.Span(
                                    " +5.67%", className="text-success float-end")
                            ], className="mb-2"),
                            html.Div([
                                html.Strong("TSLA"),
                                html.Span(
                                    " +4.23%", className="text-success float-end")
                            ], className="mb-2"),
                            html.Div([
                                html.Strong("AAPL"),
                                html.Span(
                                    " +3.45%", className="text-success float-end")
                            ], className="mb-3")
                        ]),
                        html.Hr(),
                        html.H6("Top Losers", className="text-danger mb-3"),
                        html.Div([
                            html.Div([
                                html.Strong("META"),
                                html.Span(
                                    " -3.21%", className="text-danger float-end")
                            ], className="mb-2"),
                            html.Div([
                                html.Strong("NFLX"),
                                html.Span(
                                    " -2.87%", className="text-danger float-end")
                            ], className="mb-2"),
                            html.Div([
                                html.Strong("AMZN"),
                                html.Span(
                                    " -2.34%", className="text-danger float-end")
                            ])
                        ])
                    ])
                ])
            ], width=4)
        ], className="mb-4"),

        # Market Analysis and Alerts
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H5("🚨 Market Alerts", className="mb-0 d-inline"),
                        dbc.Badge("2 Active", color="warning",
                                  className="ms-2")
                    ]),
                    dbc.CardBody([
                        dbc.Alert([
                            html.I(className="fas fa-exclamation-triangle me-2"),
                            html.Strong("Price Alert: "),
                            "Apple Inc. (AAPL) reached your target price of £145.00"
                        ], color="success", dismissable=True),
                        dbc.Alert([
                            html.I(className="fas fa-trending-down me-2"),
                            html.Strong("Market Alert: "),
                            "Technology sector down 2.1% - Consider rebalancing opportunities"
                        ], color="warning", dismissable=True)
                    ])
                ])
            ], width=6),
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H5("📊 Sector Performance", className="mb-0")
                    ]),
                    dbc.CardBody([
                        html.Div([
                            html.Div([
                                html.Span("Technology"),
                                html.Span(
                                    "+1.23%", className="text-success float-end")
                            ], className="mb-2"),
                            dbc.Progress(value=75, color="success",
                                         className="mb-3"),

                            html.Div([
                                html.Span("Healthcare"),
                                html.Span(
                                    "+0.87%", className="text-success float-end")
                            ], className="mb-2"),
                            dbc.Progress(value=65, color="success",
                                         className="mb-3"),

                            html.Div([
                                html.Span("Finance"),
                                html.Span(
                                    "-0.34%", className="text-danger float-end")
                            ], className="mb-2"),
                            dbc.Progress(value=45, color="danger",
                                         className="mb-3")
                        ])
                    ])
                ])
            ], width=6)
        ], className="mb-4"),

        # Advanced Market Tools (Premium Features)
        dbc.Card([
            dbc.CardHeader([
                html.H5("🔬 Advanced Market Analysis",
                        className="mb-0 d-inline"),
                dbc.Badge("Premium Feature", color="warning", className="ms-2")
            ]),
            dbc.CardBody([
                dbc.Alert([
                    html.I(className="fas fa-lock me-2"),
                    "Upgrade to Premium for advanced market scanning, correlation analysis, and institutional-grade market insights. ",
                    html.A("Upgrade now", href="#", className="alert-link")
                ], color="warning", className="mb-3"),

                dbc.Row([
                    dbc.Col([
                        html.H6("Market Correlation Matrix"),
                        html.Div(
                            "Correlation Heatmap Placeholder",
                            className="text-center p-4 bg-light border rounded",
                            style={"height": "200px", "display": "flex",
                                   "align-items": "center", "justify-content": "center"}
                        )
                    ], width=6),
                    dbc.Col([
                        html.H6("Economic Indicators"),
                        dbc.Table([
                            html.Thead([
                                html.Tr([
                                    html.Th("Indicator"),
                                    html.Th("Value"),
                                    html.Th("Change")
                                ])
                            ]),
                            html.Tbody([
                                html.Tr([
                                    html.Td("GDP Growth"),
                                    html.Td("2.4%"),
                                    html.Td(
                                        [dbc.Badge("+0.1%", color="success")])
                                ]),
                                html.Tr([
                                    html.Td("Unemployment"),
                                    html.Td("3.7%"),
                                    html.Td(
                                        [dbc.Badge("-0.2%", color="success")])
                                ]),
                                html.Tr([
                                    html.Td("Inflation (CPI)"),
                                    html.Td("3.1%"),
                                    html.Td(
                                        [dbc.Badge("+0.1%", color="warning")])
                                ])
                            ])
                        ], size="sm")
                    ], width=6)
                ])
            ])
        ], className="mb-4"),

        # Watchlist and Portfolio Impact
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H5("👀 Your Watchlist", className="mb-0 d-inline"),
                        dbc.Button("+ Add Stock", size="sm",
                                   color="outline-primary", className="float-end")
                    ]),
                    dbc.CardBody([
                        dbc.Table([
                            html.Thead([
                                html.Tr([
                                    html.Th("Symbol"),
                                    html.Th("Price"),
                                    html.Th("Change"),
                                    html.Th("Action")
                                ])
                            ]),
                            html.Tbody([
                                html.Tr([
                                    html.Td([
                                        html.Strong("AAPL"),
                                        html.Br(),
                                        html.Small(
                                            "Apple Inc.", className="text-muted")
                                    ]),
                                    html.Td("£145.32"),
                                    html.Td(
                                        [dbc.Badge("+2.1%", color="success")]),
                                    html.Td([
                                        dbc.ButtonGroup([
                                            dbc.Button(
                                                "BUY", size="sm", color="success"),
                                            dbc.Button(
                                                "ALERT", size="sm", color="outline-primary")
                                        ])
                                    ])
                                ]),
                                html.Tr([
                                    html.Td([
                                        html.Strong("MSFT"),
                                        html.Br(),
                                        html.Small("Microsoft Corp.",
                                                   className="text-muted")
                                    ]),
                                    html.Td("£267.89"),
                                    html.Td(
                                        [dbc.Badge("+1.4%", color="success")]),
                                    html.Td([
                                        dbc.ButtonGroup([
                                            dbc.Button(
                                                "BUY", size="sm", color="success"),
                                            dbc.Button(
                                                "ALERT", size="sm", color="outline-primary")
                                        ])
                                    ])
                                ])
                            ])
                        ])
                    ])
                ])
            ], width=12)
        ])
    ], className="p-3")
