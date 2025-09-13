"""
Personal use case layout - focused on investments, portfolio, and personal financial planning.
"""

from dash import html, dcc
import dash_bootstrap_components as dbc
from typing import Any


def create_personal_layout() -> html.Div:
    """Create the personal finance-specific layout."""
    return html.Div(
        [
            # Header with personal branding
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.H1(
                                "💰 Personal Financial Optimizer",
                                id="personal-app-title",
                                className="text-center mb-4",
                                style={"color": "#2c3e50", "fontWeight": "bold"},
                            ),
                            dbc.Alert(
                                "🏠 PERSONAL MODE: Investment & Portfolio Management",
                                color="info",
                                className="text-center mb-3",
                            ),
                        ]
                    )
                ]
            ),
            # Personal Finance Key Metrics Dashboard
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardBody(
                                        [
                                            html.H4(
                                                "💎 Net Worth", className="card-title"
                                            ),
                                            html.H2(
                                                "£128,450", className="text-success"
                                            ),
                                            html.P("Total Portfolio Value"),
                                        ]
                                    )
                                ]
                            )
                        ],
                        width=3,
                    ),
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardBody(
                                        [
                                            html.H4(
                                                "💸 Monthly Cash Flow",
                                                className="card-title",
                                            ),
                                            html.H2("£3,850", className="text-primary"),
                                            html.P("Income - Expenses"),
                                        ]
                                    )
                                ]
                            )
                        ],
                        width=3,
                    ),
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardBody(
                                        [
                                            html.H4(
                                                "📈 Investment Returns",
                                                className="card-title",
                                            ),
                                            html.H2("12.4%", className="text-warning"),
                                            html.P("YTD Performance"),
                                        ]
                                    )
                                ]
                            )
                        ],
                        width=3,
                    ),
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardBody(
                                        [
                                            html.H4(
                                                "🎯 Savings Rate",
                                                className="card-title",
                                            ),
                                            html.H2("28%", className="text-success"),
                                            html.P("Monthly Savings %"),
                                        ]
                                    )
                                ]
                            )
                        ],
                        width=3,
                    ),
                ],
                className="mb-4",
            ),
            # Personal finance navigation tabs
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Tabs(
                                [
                                    dbc.Tab(
                                        label="📊 Portfolio Dashboard",
                                        tab_id="portfolio-dashboard",
                                    ),
                                    dbc.Tab(
                                        label="💹 Investment Analysis",
                                        tab_id="investment-analysis",
                                    ),
                                    dbc.Tab(
                                        label="💰 Budget Planning",
                                        tab_id="budget-planning",
                                    ),
                                    dbc.Tab(
                                        label="📈 Market Insights",
                                        tab_id="market-insights",
                                    ),
                                    dbc.Tab(
                                        label="🏖️ Retirement Planning",
                                        tab_id="retirement-planning",
                                    ),
                                ],
                                id="personal-tabs",
                                active_tab="portfolio-dashboard",
                            )
                        ]
                    )
                ],
                className="mb-4",
            ),
            # Content area that changes based on tab
            dbc.Row([dbc.Col([html.Div(id="personal-content")])]),
        ]
    )


def create_portfolio_dashboard() -> html.Div:
    """Create the portfolio dashboard tab content."""
    return html.Div(
        [
            dbc.Row(
                [
                    # Portfolio metrics
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardBody(
                                        [
                                            html.H4(
                                                "Net Worth", className="card-title"
                                            ),
                                            html.H2(
                                                id="net-worth", className="text-success"
                                            ),
                                            html.P("Total Portfolio Value"),
                                        ]
                                    )
                                ]
                            )
                        ],
                        width=3,
                    ),
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardBody(
                                        [
                                            html.H4(
                                                "Monthly Cash Flow",
                                                className="card-title",
                                            ),
                                            html.H2(
                                                id="cash-flow", className="text-primary"
                                            ),
                                            html.P("Income - Expenses"),
                                        ]
                                    )
                                ]
                            )
                        ],
                        width=3,
                    ),
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardBody(
                                        [
                                            html.H4(
                                                "Investment Returns",
                                                className="card-title",
                                            ),
                                            html.H2(
                                                id="investment-returns",
                                                className="text-warning",
                                            ),
                                            html.P("YTD Performance"),
                                        ]
                                    )
                                ]
                            )
                        ],
                        width=3,
                    ),
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardBody(
                                        [
                                            html.H4(
                                                "Savings Rate", className="card-title"
                                            ),
                                            html.H2(
                                                id="savings-rate",
                                                className="text-success",
                                            ),
                                            html.P("Monthly Savings %"),
                                        ]
                                    )
                                ]
                            )
                        ],
                        width=3,
                    ),
                ],
                className="mb-4",
            ),
            # Portfolio allocation and performance
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.H5("Portfolio Performance"),
                            dcc.Graph(id="portfolio-chart"),
                        ],
                        width=8,
                    ),
                    dbc.Col(
                        [
                            html.H5("Asset Allocation"),
                            dcc.Graph(id="allocation-chart"),
                            html.Hr(),
                            html.H6("Rebalancing Suggestions"),
                            html.Div(id="rebalancing-suggestions"),
                        ],
                        width=4,
                    ),
                ]
            ),
        ]
    )
