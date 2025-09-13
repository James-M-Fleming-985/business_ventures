"""
Charity use case layout - focused on donations, grants, and impact measurement.
"""

from dash import html, dcc
import dash_bootstrap_components as dbc


def create_charity_layout() -> html.Div:
    """Create the charity-specific layout."""
    return html.Div(
        [
            # Header with charity branding
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.H1(
                                "❤️ Charity Financial Management",
                                id="charity-app-title",
                                className="text-center mb-4",
                                style={"color": "#e74c3c", "fontWeight": "bold"},
                            ),
                            dbc.Alert(
                                "❤️ CHARITY MODE: Donations, Grants & Impact Tracking",
                                color="danger",
                                className="text-center mb-3",
                            ),
                        ]
                    )
                ]
            ),
            # Charity Key Metrics Dashboard
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardBody(
                                        [
                                            html.H4(
                                                "💰 Total Donations",
                                                className="card-title",
                                            ),
                                            html.H2(
                                                "£45,850", className="text-success"
                                            ),
                                            html.P("Monthly Collection"),
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
                                                "🎯 Program Impact",
                                                className="card-title",
                                            ),
                                            html.H2("1,247", className="text-info"),
                                            html.P("People Helped"),
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
                                                "📊 Efficiency Ratio",
                                                className="card-title",
                                            ),
                                            html.H2("87%", className="text-warning"),
                                            html.P("Funds to Programs"),
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
                                                "🏆 Grant Success",
                                                className="card-title",
                                            ),
                                            html.H2("73%", className="text-success"),
                                            html.P("Application Rate"),
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
            # Charity-specific tabs
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Tabs(
                                [
                                    dbc.Tab(
                                        label="💰 Donation Tracking",
                                        tab_id="donation-tracking",
                                    ),
                                    dbc.Tab(
                                        label="📈 Grant Management",
                                        tab_id="grant-management",
                                    ),
                                    dbc.Tab(
                                        label="🎯 Impact Measurement",
                                        tab_id="impact-measurement",
                                    ),
                                    dbc.Tab(
                                        label="📊 Financial Reports",
                                        tab_id="financial-reports",
                                    ),
                                ],
                                id="charity-tabs",
                                active_tab="donation-tracking",
                            )
                        ]
                    )
                ],
                className="mb-4",
            ),
            # Content area
            dbc.Row([dbc.Col([html.Div(id="charity-content")])]),
        ]
    )
