# components/header.py
from dash import html, dcc
import dash_bootstrap_components as dbc

def create_header():
    """Create the application header component."""
    return html.Div([
        dbc.Container([
            dbc.Row([
                dbc.Col([
                    html.H1(id="app-title", children="SLS Surface Finish Finance", className="app-title"),
                ], width=8),
                dbc.Col([
                    html.Div([
                        html.Label(" "),
                        dbc.RadioItems(
                            id='app-mode',
                            options=[
                                {'label': 'Mode 1', 'value': 'business'},
                                {'label': 'Mode 2', 'value': 'personal'}
                            ],
                            value='business',  # Default to business mode
                            inline=True
                        )
                    ], className="mode-toggle")
                ], width=4)
            ])
        ], fluid=True)
    ], className="header")