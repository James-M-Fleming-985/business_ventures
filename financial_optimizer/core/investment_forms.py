#!/usr/bin/env python3
"""
Investment Forms Modal System
Creates modal forms for each investment type with upload and mapping features
"""

import dash_bootstrap_components as dbc
from dash import html, dcc, Input, Output, State, callback
import json


def create_investment_modal(investment_type, business_model):
    """Create modal form for specific investment type."""

    # Investment type configurations from your spec
    investment_configs = {
        "capital": {
            "title": "Capital Equipment & Assets",
            "description": "Equipment, machinery, and physical assets",
            "cost_center_fields": [
                "Current OEE (%)", "Target OEE (%)", "Process Time (min/unit)",
                "Energy Usage (kWh/unit)", "Maintenance Hours/Month",
                "Annual Volume (units)", "Labor Rate (£/hour)", "Energy Cost (£/kWh)"
            ],
            "profit_center_fields": [
                "Unit Selling Price (£)", "Unit Variable Cost (£)",
                "Market Demand (units)", "Current OEE (%)", "Target OEE (%)",
                "Production Rate (units/hour)", "Operating Hours/Year"
            ]
        },
        "process": {
            "title": "Process Improvement & Optimization",
            "description": "Workflow optimization and process enhancement",
            "cost_center_fields": [
                "Current Cycle Time (min)", "Target Cycle Time (min)",
                "Current Defect Rate (%)", "Target Defect Rate (%)",
                "Labor Hours/Unit", "Annual Volume (units)", "Labor Rate (£/hour)"
            ],
            "profit_center_fields": [
                "Current Yield (%)", "Target Yield (%)", "Unit Selling Price (£)",
                "Annual Volume (units)", "Customer Satisfaction Score"
            ]
        },
        "people": {
            "title": "Human Capital & Training",
            "description": "Training programs and workforce development",
            "cost_center_fields": [
                "Number of Staff", "Training Hours/Person", "Current Productivity (units/hour)",
                "Expected Productivity Improvement (%)", "Labor Rate (£/hour)"
            ],
            "profit_center_fields": [
                "Number of Staff", "Training Cost/Person (£)", "Expected Revenue Impact (%)",
                "Customer Satisfaction Improvement (%)", "Innovation Rate Increase (%)"
            ]
        },
        "maintenance": {
            "title": "Maintenance & Asset Reliability",
            "description": "Preventive maintenance and asset optimization",
            "cost_center_fields": [
                "Current Maintenance Hours/Month", "Target Maintenance Hours/Month",
                "Current Downtime Hours/Month", "Target Downtime Hours/Month",
                "Maintenance Cost (£/hour)", "Production Rate (units/hour)"
            ],
            "profit_center_fields": [
                "Current MTBF (hours)", "Target MTBF (hours)", "Revenue Loss/Hour (£)",
                "Emergency Maintenance Cost (£/hour)", "Planned Maintenance Cost (£/hour)"
            ]
        },
        "quality": {
            "title": "Quality Systems & Compliance",
            "description": "Quality improvement and compliance systems",
            "cost_center_fields": [
                "Current Defect Rate (%)", "Target Defect Rate (%)",
                "Rework Cost (£/unit)", "Scrap Cost (£/unit)", "Annual Volume (units)"
            ],
            "profit_center_fields": [
                "Current First Pass Yield (%)", "Target First Pass Yield (%)",
                "Customer Complaint Rate", "Warranty Cost (£/unit)", "Premium Pricing Potential (%)"
            ]
        },
        "digital": {
            "title": "Digital Transformation & Industry 4.0",
            "description": "Automation, IoT, and digital systems",
            "cost_center_fields": [
                "Manual Hours/Day", "Automation Savings (%)", "Data Entry Time (hours/day)",
                "Error Rate Reduction (%)", "Labor Rate (£/hour)"
            ],
            "profit_center_fields": [
                "Time-to-Market Reduction (%)", "Customization Premium (%)",
                "Service Revenue Potential (£)", "Market Responsiveness Improvement (%)"
            ]
        },
        "safety": {
            "title": "Safety & Environmental Systems",
            "description": "Safety improvements and environmental compliance",
            "cost_center_fields": [
                "Current Incident Rate", "Target Incident Rate", "Incident Cost (£/incident)",
                "Insurance Premium (£/year)", "Compliance Cost (£/year)"
            ],
            "profit_center_fields": [
                "Brand Value Impact (£)", "Regulatory Benefits (£)",
                "Insurance Savings (£)", "Production Shutdown Risk Reduction (%)"
            ]
        },
        "facility": {
            "title": "Facility & Infrastructure",
            "description": "Building improvements and infrastructure",
            "cost_center_fields": [
                "Energy Consumption (kWh/month)", "Energy Cost (£/kWh)",
                "Maintenance Cost (£/month)", "Space Utilization (%)", "Utility Costs (£/month)"
            ],
            "profit_center_fields": [
                "Additional Capacity (units)", "Capacity Utilization (%)",
                "Quality Premium (%)", "Customer Impression Value (£)"
            ]
        },
        "supply_chain": {
            "title": "Supply Chain & Logistics",
            "description": "Supply chain optimization and logistics",
            "cost_center_fields": [
                "Inventory Carrying Cost (%)", "Current Inventory Value (£)",
                "Logistics Cost (£/unit)", "Transaction Cost (£/transaction)"
            ],
            "profit_center_fields": [
                "Service Premium (%)", "Lead Time Reduction (days)",
                "Customer Retention Impact (%)", "Market Responsiveness (%)"
            ]
        }
    }

    config = investment_configs.get(investment_type, {})
    model_type = "cost_center" if business_model == "cost_center" else "profit_center"
    fields = config.get(f"{model_type}_fields", [])

    return dbc.Modal([
        dbc.ModalHeader([
            dbc.ModalTitle(config.get("title", "Investment Form")),
            dbc.Button(
                "×", id=f"close-{investment_type}-modal", className="btn-close")
        ]),
        dbc.ModalBody([
            html.P(config.get("description", "")),
            html.Hr(),

            # Business Model Info
            dbc.Alert([
                html.H6(
                    f"Business Model: {business_model.replace('_', ' ').title()}", className="alert-heading"),
                html.P(
                    f"Required fields for {model_type.replace('_', ' ')} calculations:")
            ], color="info", className="mb-3"),

            # File Upload Section
            dbc.Card([
                dbc.CardBody([
                    html.H5("Data Upload", className="card-title"),
                    dcc.Upload(
                        id=f"upload-{investment_type}-data",
                        children=html.Div([
                            html.I(className="fas fa-cloud-upload-alt fa-2x mb-2"),
                            html.P("Drag and drop or click to select files"),
                            html.P("Supports: CSV, Excel (.xlsx, .xls)",
                                   className="text-muted small")
                        ]),
                        style={
                            'width': '100%',
                            'height': '120px',
                            'lineHeight': '120px',
                            'borderWidth': '2px',
                            'borderStyle': 'dashed',
                            'borderRadius': '10px',
                            'textAlign': 'center',
                            'margin': '10px',
                            'borderColor': '#007bff'
                        },
                        multiple=False
                    ),
                    html.Div(
                        id=f"upload-{investment_type}-status", className="mt-2")
                ])
            ], className="mb-3"),

            # Column Mapping Section
            dbc.Card([
                dbc.CardBody([
                    html.H5("Column Mapping", className="card-title"),
                    html.P("Map your data columns to required fields:",
                           className="text-muted"),
                    html.Div(id=f"mapping-{investment_type}-fields", children=[
                        dbc.Row([
                            dbc.Col([
                                html.Label(field, className="fw-bold"),
                                dcc.Dropdown(
                                    id=f"map-{investment_type}-{field.lower().replace(' ', '-').replace('(', '').replace(')', '').replace('/', '-')}",
                                    placeholder="Select column...",
                                    options=[],  # Will be populated after file upload
                                    clearable=True
                                )
                            ], width=6)
                            for field in fields[i:i+2]  # Two columns per row
                        ], className="mb-2")
                        for i in range(0, len(fields), 2)
                    ])
                ])
            ], className="mb-3"),

            # Preview Section
            dbc.Card([
                dbc.CardBody([
                    html.H5("Data Preview", className="card-title"),
                    html.Div(id=f"preview-{investment_type}-data", children=[
                        html.P("Upload a file to see data preview...",
                               className="text-muted")
                    ])
                ])
            ], className="mb-3"),

            # Manual Entry Option
            dbc.Card([
                dbc.CardBody([
                    html.H5("Manual Entry (Optional)", className="card-title"),
                    html.P(
                        "Enter values manually if you don't have a file to upload:", className="text-muted"),
                    html.Div([
                        dbc.Row([
                            dbc.Col([
                                html.Label(field),
                                dbc.Input(
                                    id=f"manual-{investment_type}-{field.lower().replace(' ', '-').replace('(', '').replace(')', '').replace('/', '-')}",
                                    type="number",
                                    placeholder=f"Enter {field.lower()}..."
                                )
                            ], width=6)
                            for field in fields[i:i+2]
                        ], className="mb-2")
                        for i in range(0, len(fields), 2)
                    ])
                ])
            ], className="mb-3")
        ]),
        dbc.ModalFooter([
            dbc.Button(
                "Cancel", id=f"cancel-{investment_type}-form", color="secondary", className="me-2"),
            dbc.Button("Calculate Savings",
                       id=f"calculate-{investment_type}-savings", color="primary")
        ])
    ], id=f"{investment_type}-investment-modal", is_open=False, size="xl")


def create_modal_callbacks(investment_type):
    """Create callbacks for modal open/close and data processing."""

    # Callback to open modal
    @callback(
        Output(f"{investment_type}-investment-modal", "is_open"),
        [Input(f"open-{investment_type}-form", "n_clicks"),
         Input(f"close-{investment_type}-modal", "n_clicks"),
         Input(f"cancel-{investment_type}-form", "n_clicks")],
        [State(f"{investment_type}-investment-modal", "is_open")],
        prevent_initial_call=True
    )
    def toggle_modal(open_clicks, close_clicks, cancel_clicks, is_open):
        return not is_open if any([open_clicks, close_clicks, cancel_clicks]) else is_open

    # Callback to handle file upload
    @callback(
        [Output(f"upload-{investment_type}-status", "children"),
         Output(f"preview-{investment_type}-data", "children")],
        Input(f"upload-{investment_type}-data", "contents"),
        State(f"upload-{investment_type}-data", "filename"),
        prevent_initial_call=True
    )
    def process_uploaded_file(contents, filename):
        if contents is not None:
            # Here you would process the uploaded file
            # For now, return a placeholder
            status = dbc.Alert([
                html.I(className="fas fa-check-circle me-2"),
                f"File uploaded: {filename}"
            ], color="success")

            preview = html.Div([
                html.H6("File Preview:"),
                html.P(f"Filename: {filename}"),
                html.P("Column mapping will be enabled after file processing...")
            ])

            return status, preview

        return "", html.P("Upload a file to see data preview...", className="text-muted")
