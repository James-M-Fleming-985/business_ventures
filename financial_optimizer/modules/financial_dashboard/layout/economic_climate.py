"""
Component for economic climate analysis UI.
"""
from dash import html, dcc, dash_table
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
import json

def create_economic_climate_section():
    """
    Create the economic climate analysis section for the application.
    
    Returns:
        html.Div: The economic climate component
    """
    print("Creating economic climate section")  # Debug statement
    
    return html.Div([
        html.H4("Economic Climate Analysis", className="mb-3"),
        
        html.Div([
            html.Label("Select Economic Region:"),
            dcc.Dropdown(
                id="economic-region-dropdown",
                options=[
                    {"label": "United Kingdom", "value": "UK"},
                    {"label": "European Union", "value": "EU"},
                    {"label": "United States", "value": "US"},
                    {"label": "Asia", "value": "ASIA"},
                    {"label": "India", "value": "IN"},
                ],
                value="UK",
                clearable=False,
                className="mb-3"
            ),
            
            # Button to fetch and analyze economic data
            dbc.Button(
                "Analyze Economic Climate", 
                id="analyze-climate-button", 
                color="primary", 
                className="mb-3"
            ),
            
            # Loading spinner for when data is being fetched
            dbc.Spinner(
                html.Div(id="economic-indicators-container", children=[])
            ),
            
            # Hidden div to store economic analysis results
            html.Div(id="economic-analysis-store", style={"display": "none"})
        ], className="border p-3 rounded mb-3")
    ], className="mt-4")


# Define callbacks as top-level functions instead of nesting them
def update_economic_indicators(n_clicks, region, mode):
    """
    Update economic indicators based on selected region.
    
    Args:
        n_clicks: Button click count
        region: Selected economic region
        mode: App mode (business/personal)
        
    Returns:
        tuple: (economic indicators display, analysis JSON)
    """
    from modules.financial_dashboard.models.economic_climate import get_economic_data, analyze_economic_climate
    
    if not n_clicks:
        return html.Div(), ""
    
    if mode == "business" and region != "UK":
        # For business mode, only UK data is relevant
        region = "UK"
    
    # Fetch economic data and analyze
    print(f"Fetching economic data for {region}")  # Debug statement
    economic_data = get_economic_data(region)
    print(f"Analyzing economic data: {economic_data}")  # Debug statement
    analysis = analyze_economic_climate(economic_data)
    
    # Create indicators display
    region_name = {
        "UK": "United Kingdom",
        "EU": "European Union",
        "US": "United States",
        "ASIA": "Asia",
        "IN": "India"
    }.get(region, region)
    
    indicators_display = html.Div([
        html.H5(f"Economic Indicators for {region_name}", className="mt-2"),
        
        # Display key indicators in a table
        dash_table.DataTable(
            columns=[
                {"name": "Indicator", "id": "indicator"},
                {"name": "Value", "id": "value"},
                {"name": "Year", "id": "year"}
            ],
            data=[
                {"indicator": "GDP Growth (%)", 
                 "value": economic_data.get("gdp_growth", {}).get("value", "N/A"),
                 "year": economic_data.get("gdp_growth", {}).get("year", "N/A")},
                {"indicator": "Inflation Rate (%)", 
                 "value": economic_data.get("inflation", {}).get("value", "N/A"),
                 "year": economic_data.get("inflation", {}).get("year", "N/A")},
                {"indicator": "Unemployment Rate (%)", 
                 "value": economic_data.get("unemployment", {}).get("value", "N/A"),
                 "year": economic_data.get("unemployment", {}).get("year", "N/A")},
                {"indicator": "Interest Rate (%)", 
                 "value": economic_data.get("interest_rate", {}).get("value", "N/A"),
                 "year": economic_data.get("interest_rate", {}).get("year", "N/A")},
                {"indicator": "Business Confidence", 
                 "value": economic_data.get("business_confidence", {}).get("value", "N/A"),
                 "year": economic_data.get("business_confidence", {}).get("year", "N/A")}
            ],
            style_cell={'textAlign': 'left', 'padding': '10px'},
            style_header={
                'backgroundColor': 'rgb(230, 230, 230)',
                'fontWeight': 'bold'
            },
            style_table={'overflowX': 'auto'},
        ),
        
        # Recommendation section
        html.Div([
            html.H5("Economic Analysis", className="mt-3"),
            html.P([
                f"Economic Health Score: ",
                html.Strong(f"{analysis['economic_score']}/10")
            ]),
            html.P(analysis["description"]),
            html.Div([
                html.Strong("Recommended Scenario:"),
                html.Div(
                    html.Span(
                        analysis["recommended_scenario"].title(),
                        className="badge bg-primary ms-2"
                    )
                )
            ], className="mb-3"),
            html.P("Select this scenario in the 'Select Scenarios to Compare' dropdown to apply this economic climate to your financial projections."),
        ], className="mt-3 border-top pt-3")
    ])
    
    return indicators_display, json.dumps(analysis)

def update_scenario_selection(analysis_json, current_selection):
    """
    Update the scenario selector based on economic analysis.
    
    Args:
        analysis_json: JSON string with analysis results
        current_selection: Currently selected scenarios
        
    Returns:
        list: Updated scenario selection
    """
    if not analysis_json:
        return current_selection
        
    try:
        analysis = json.loads(analysis_json)
        # Change this to return a list with the recommended scenario
        # since your dropdown accepts a list (multi=True)
        return [analysis["recommended_scenario"]]
    except:
        return current_selection

def register_economic_climate_callbacks(app):
    """
    Register callbacks for the economic climate component.
    
    Args:
        app: The Dash application instance
    """
    print("Registering economic climate callbacks")  # Debug statement
    
    # Use the top-level functions we defined earlier
    app.callback(
        Output("economic-indicators-container", "children"),
        Output("economic-analysis-store", "children"),
        Input("analyze-climate-button", "n_clicks"),
        State("economic-region-dropdown", "value"),
        State("app-mode", "value"),
        prevent_initial_call=True
    )(update_economic_indicators)
    
    app.callback(
        Output("scenario-selector", "value"),
        Input("economic-analysis-store", "children"),
        State("scenario-selector", "value"),
        prevent_initial_call=True
    )(update_scenario_selection)
    
    print("Economic climate callbacks registered successfully")  # Debug statement