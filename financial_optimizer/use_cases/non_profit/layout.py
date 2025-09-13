"""
Non-profit use case layout - focused on budget management and program tracking.
"""

from dash import html, dcc
import dash_bootstrap_components as dbc


def create_nonprofit_layout() -> html.Div:
    """Create the non-profit-specific layout."""
    return html.Div(
        [
            # Header with non-profit branding
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.H1(
                                "🏛️ Non-Profit Financial Manager",
                                id="nonprofit-app-title",
                                className="text-center mb-4",
                                style={"color": "#8e44ad", "fontWeight": "bold"},
                            ),
                            dbc.Alert(
                                "🏛️ NON-PROFIT MODE: Budget Management & Program Tracking",
                                color="secondary",
                                className="text-center mb-3",
                            ),
                        ]
                    )
                ]
            ),
            # Non-Profit Key Metrics Dashboard
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardBody(
                                        [
                                            html.H4(
                                                "💼 Operating Budget",
                                                className="card-title",
                                            ),
                                            html.H2(
                                                "£125,000", className="text-primary"
                                            ),
                                            html.P("Annual Allocation"),
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
                                                "📊 Program Efficiency",
                                                className="card-title",
                                            ),
                                            html.H2("92%", className="text-success"),
                                            html.P("Budget Utilization"),
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
                                                "🎯 Mission Impact",
                                                className="card-title",
                                            ),
                                            html.H2("2,156", className="text-info"),
                                            html.P("Beneficiaries Served"),
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
                                                "📈 Funding Status",
                                                className="card-title",
                                            ),
                                            html.H2("68%", className="text-warning"),
                                            html.P("YTD Secured"),
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
            # Non-profit specific tabs
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Tabs(
                                [
                                    dbc.Tab(
                                        label="💼 Budget Planning",
                                        tab_id="budget-planning",
                                    ),
                                    dbc.Tab(
                                        label="🎯 Program Tracking",
                                        tab_id="program-tracking",
                                    ),
                                    dbc.Tab(
                                        label="📊 Impact Analysis",
                                        tab_id="impact-analysis",
                                    ),
                                    dbc.Tab(
                                        label="💰 Funding Pipeline",
                                        tab_id="funding-pipeline",
                                    ),
                                ],
                                id="nonprofit-tabs",
                                active_tab="budget-planning",
                            )
                        ]
                    )
                ],
                className="mb-4",
            ),
            # Content area
            dbc.Row([dbc.Col([html.Div(id="nonprofit-content")])]),
        ]
    )
