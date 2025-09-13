#!/usr/bin/env python3
"""
Data Input Workflow Implementation
Based on user's proposed workflow: Business Model → Investment Type Boxes → Detailed Forms
"""

from dash import Dash, html, dcc, Input, Output, State, callback
import dash_bootstrap_components as dbc
from investment_config import INVESTMENT_CONFIGS

def create_data_input_tab():
    """Create the data input tab with business model selection and investment type boxes."""
    return html.Div([
        html.H3("Data Input"),
        html.P("Select your business model and upload data for each investment type."),
        
        # Business Model Selection
        dbc.Card([
            dbc.CardBody([
                html.H5("Step 1: Select Business Model", className="card-title"),
                dbc.RadioItems(
                    id="business-model-selection",
                    options=[
                        {"label": "Cost Center - Focus on cost reduction and operational efficiency", 
                         "value": "cost_center"},
                        {"label": "Profit Center - Focus on revenue generation and market opportunity", 
                         "value": "profit_center"}
                    ],
                    value="cost_center",
                    inline=False,
                    className="mb-3"
                ),
                dbc.Alert(
                    id="business-model-description",
                    color="info",
                    className="mb-0"
                )
            ])
        ], className="mb-4"),
        
        # Investment Type Upload Boxes
        html.Div([
            html.H5("Step 2: Upload Data for Investment Types"),
            html.P("Click on each investment type to open detailed data upload forms."),
            html.Div(id="investment-type-boxes", className="row")
        ], id="investment-upload-section", style={"display": "none"})
    ])

def create_investment_type_box(investment_type, investment_config, business_model):
    """Create a clickable box for each investment type."""
    config = investment_config[business_model]
    
    # Count required fields
    field_count = len(config.get('fields', []))
    
    # Check if data is uploaded (placeholder logic)
    data_uploaded = False  # This would be checked against actual data store
    
    status_color = "success" if data_uploaded else "light"
    status_icon = "✓" if data_uploaded else "📁"
    
    return dbc.Col([
        dbc.Card([
            dbc.CardBody([
                html.H6(f"{status_icon} {investment_config['label']}", className="card-title"),
                html.P(config['description'], className="card-text small"),
                html.P(f"Required fields: {field_count}", className="text-muted small"),
                html.Hr(),
                dbc.Button(
                    "Upload Data" if not data_uploaded else "View/Edit Data",
                    id=f"open-{investment_type}-form",
                    color="primary" if not data_uploaded else "success",
                    size="sm",
                    className="w-100"
                )
            ])
        ], color=status_color, outline=True, className="h-100")
    ], width=4, className="mb-3")

def create_detailed_investment_form(investment_type, investment_config, business_model):
    """Create detailed form for specific investment type."""
    config = investment_config[business_model]
    fields = config.get('fields', [])
    
    # Create form fields
    form_fields = []
    for field in fields:
        form_fields.append(
            dbc.Row([
                dbc.Col([
                    dbc.Label(field['label']),
                    dbc.Input(
                        id=f"detailed-{investment_type}-{field['id']}",
                        type=field['type'],
                        placeholder=field.get('help', ''),
                        value=field.get('value', ''),
                        min=field.get('min', None),
                        max=field.get('max', None),
                        step=field.get('step', None)
                    ),
                    dbc.FormText(field.get('help', ''))
                ], width=6)
            ], className="mb-3")
        )
    
    return dbc.Modal([
        dbc.ModalHeader([
            dbc.ModalTitle(f"Data Upload: {investment_config['label']}")
        ]),
        dbc.ModalBody([
            # Upload Section
            dbc.Card([
                dbc.CardBody([
                    html.H6("Option 1: Upload File"),
                    dcc.Upload(
                        id=f"upload-{investment_type}",
                        children=html.Div([
                            'Drag and Drop or ',
                            html.A('Select Files')
                        ]),
                        style={
                            'width': '100%',
                            'height': '60px',
                            'lineHeight': '60px',
                            'borderWidth': '1px',
                            'borderStyle': 'dashed',
                            'borderRadius': '5px',
                            'textAlign': 'center',
                            'margin': '10px'
                        },
                        multiple=False
                    ),
                    html.Div(id=f"upload-status-{investment_type}")
                ])
            ], className="mb-3"),
            
            # Column Mapping Section
            dbc.Card([
                dbc.CardBody([
                    html.H6("Column Mapping"),
                    html.P("Map your file columns to required fields:"),
                    html.Div(id=f"column-mapping-{investment_type}")
                ])
            ], className="mb-3"),
            
            # Manual Entry Section
            dbc.Card([
                dbc.CardBody([
                    html.H6("Option 2: Manual Entry"),
                    html.P(config['description']),
                    html.Hr(),
                    *form_fields
                ])
            ])
        ]),
        dbc.ModalFooter([
            dbc.Button("Cancel", id=f"cancel-{investment_type}", color="secondary"),
            dbc.Button("Save Data", id=f"save-{investment_type}", color="primary")
        ])
    ], id=f"modal-{investment_type}", size="lg", is_open=False)

# Example callback structure
@callback(
    Output("business-model-description", "children"),
    Input("business-model-selection", "value")
)
def update_business_model_description(business_model):
    """Update description based on business model selection."""
    if business_model == "cost_center":
        return "Cost Center: Focus on reducing operational costs through efficiency improvements, waste reduction, and process optimization."
    else:
        return "Profit Center: Focus on generating additional revenue through increased capacity, market opportunities, and customer value creation."

@callback(
    [Output("investment-upload-section", "style"),
     Output("investment-type-boxes", "children")],
    Input("business-model-selection", "value")
)
def update_investment_boxes(business_model):
    """Show investment type boxes based on business model selection."""
    if not business_model:
        return {"display": "none"}, []
    
    boxes = []
    for investment_type, investment_config in INVESTMENT_CONFIGS.items():
        if business_model in investment_config:
            box = create_investment_type_box(investment_type, investment_config, business_model)
            boxes.append(box)
    
    return {"display": "block"}, boxes

# Modal open/close callbacks for each investment type
for investment_type in INVESTMENT_CONFIGS.keys():
    @callback(
        Output(f"modal-{investment_type}", "is_open"),
        [Input(f"open-{investment_type}-form", "n_clicks"),
         Input(f"cancel-{investment_type}", "n_clicks"),
         Input(f"save-{investment_type}", "n_clicks")],
        State(f"modal-{investment_type}", "is_open")
    )
    def toggle_modal(open_clicks, cancel_clicks, save_clicks, is_open):
        """Toggle modal for investment type."""
        if open_clicks or cancel_clicks or save_clicks:
            return not is_open
        return is_open
