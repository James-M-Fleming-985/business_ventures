#!/usr/bin/env python3
"""
Dynamic Form Generator
Creates form fields based on investment type and business model configuration.
"""

import dash_bootstrap_components as dbc
from dash import html, dcc

def create_dynamic_form_fields(investment_type, business_model, config):
    """
    Create dynamic form fields based on investment type and business model.
    
    Args:
        investment_type: str - The investment type key
        business_model: str - 'cost_center' or 'profit_center'
        config: dict - The investment configuration
    
    Returns:
        list - List of Dash components for the form
    """
    if investment_type not in config:
        return []
    
    investment_config = config[investment_type]
    
    if business_model not in investment_config:
        return []
    
    model_config = investment_config[business_model]
    
    # Create form fields
    form_fields = []
    
    # Add description
    form_fields.append(
        dbc.Alert(
            model_config.get('description', ''),
            color="info",
            className="mb-3"
        )
    )
    
    # Create fields in rows of 2
    fields = model_config.get('fields', [])
    for i in range(0, len(fields), 2):
        row_fields = fields[i:i+2]
        
        cols = []
        for field in row_fields:
            # Create input component based on field type
            if field['type'] == 'number':
                input_component = dbc.Input(
                    id=f"dynamic-{field['id']}",
                    type="number",
                    min=field.get('min', None),
                    max=field.get('max', None),
                    step=field.get('step', None),
                    value=field.get('value', None),
                    placeholder=field.get('placeholder', ''),
                    className="mb-2"
                )
            else:
                input_component = dbc.Input(
                    id=f"dynamic-{field['id']}",
                    type="text",
                    value=field.get('value', ''),
                    placeholder=field.get('placeholder', ''),
                    className="mb-2"
                )
            
            # Add help text if available
            help_text = field.get('help', '')
            if help_text:
                help_component = html.Small(
                    help_text,
                    className="form-text text-muted"
                )
            else:
                help_component = None
            
            # Create column
            col_content = [
                html.Label(field['label'], className="form-label"),
                input_component
            ]
            if help_component:
                col_content.append(help_component)
            
            cols.append(
                dbc.Col(col_content, width=6)
            )
        
        # Add row
        form_fields.append(
            dbc.Row(cols, className="mb-3")
        )
    
    return form_fields

def get_investment_type_options(config):
    """
    Get investment type options for dropdown.
    
    Args:
        config: dict - The investment configuration
    
    Returns:
        list - List of options for dropdown
    """
    options = []
    for key, value in config.items():
        options.append({
            'label': value.get('label', key),
            'value': key
        })
    return options

def collect_dynamic_form_data(form_state, investment_type, business_model, config):
    """
    Collect data from dynamic form fields.
    
    Args:
        form_state: dict - Current form state from Dash inputs
        investment_type: str - The investment type key
        business_model: str - 'cost_center' or 'profit_center'
        config: dict - The investment configuration
    
    Returns:
        dict - Collected form data
    """
    if investment_type not in config:
        return {}
    
    investment_config = config[investment_type]
    
    if business_model not in investment_config:
        return {}
    
    model_config = investment_config[business_model]
    fields = model_config.get('fields', [])
    
    data = {}
    for field in fields:
        field_id = f"dynamic-{field['id']}"
        if field_id in form_state:
            value = form_state[field_id]
            # Convert to appropriate type
            if field['type'] == 'number' and value is not None:
                data[field['id']] = float(value)
            else:
                data[field['id']] = value
    
    return data

def get_field_ids_for_investment_type(investment_type, business_model, config):
    """
    Get list of field IDs for a specific investment type and business model.
    
    Args:
        investment_type: str - The investment type key
        business_model: str - 'cost_center' or 'profit_center'
        config: dict - The investment configuration
    
    Returns:
        list - List of field IDs
    """
    if investment_type not in config:
        return []
    
    investment_config = config[investment_type]
    
    if business_model not in investment_config:
        return []
    
    model_config = investment_config[business_model]
    fields = model_config.get('fields', [])
    
    return [f"dynamic-{field['id']}" for field in fields]

def create_calculation_summary(investment_type, business_model, data, savings):
    """
    Create a summary of the calculation for display.
    
    Args:
        investment_type: str - The investment type key
        business_model: str - 'cost_center' or 'profit_center'
        data: dict - The input data used for calculations
        savings: float - The calculated savings
    
    Returns:
        html.Div - Summary component
    """
    summary_items = []
    
    # Investment type and business model
    summary_items.append(
        html.P([
            html.Strong("Investment Type: "),
            investment_type.replace('_', ' ').title()
        ])
    )
    
    summary_items.append(
        html.P([
            html.Strong("Business Model: "),
            business_model.replace('_', ' ').title()
        ])
    )
    
    # Key data points (show first 5 most important)
    data_items = []
    for key, value in list(data.items())[:5]:
        if value is not None:
            data_items.append(
                html.Li(f"{key.replace('_', ' ').title()}: {value}")
            )
    
    if data_items:
        summary_items.append(
            html.Div([
                html.Strong("Key Parameters:"),
                html.Ul(data_items)
            ])
        )
    
    # Calculated savings
    summary_items.append(
        html.P([
            html.Strong("Calculated Annual Savings: "),
            f"£{savings:,.2f}"
        ], className="text-success")
    )
    
    return html.Div(summary_items, className="calculation-summary")

def create_validation_alerts(investment_type, business_model, data, config):
    """
    Create validation alerts for the form data.
    
    Args:
        investment_type: str - The investment type key
        business_model: str - 'cost_center' or 'profit_center'
        data: dict - The input data
        config: dict - The investment configuration
    
    Returns:
        list - List of alert components
    """
    alerts = []
    
    if investment_type not in config:
        return alerts
    
    investment_config = config[investment_type]
    
    if business_model not in investment_config:
        return alerts
    
    model_config = investment_config[business_model]
    fields = model_config.get('fields', [])
    
    # Check for missing required fields
    missing_fields = []
    for field in fields:
        field_id = field['id']
        if field_id not in data or data[field_id] is None:
            missing_fields.append(field['label'])
    
    if missing_fields:
        alerts.append(
            dbc.Alert(
                f"Missing required fields: {', '.join(missing_fields)}",
                color="warning",
                className="mb-3"
            )
        )
    
    # Check for logical inconsistencies
    if investment_type == 'capital':
        if 'current_oee' in data and 'target_oee' in data:
            if data['target_oee'] <= data['current_oee']:
                alerts.append(
                    dbc.Alert(
                        "Target OEE should be higher than current OEE",
                        color="warning",
                        className="mb-3"
                    )
                )
    
    if investment_type == 'process':
        if 'improved_cycle_time' in data and 'current_cycle_time' in data:
            if data['improved_cycle_time'] >= data['current_cycle_time']:
                alerts.append(
                    dbc.Alert(
                        "Improved cycle time should be less than current cycle time",
                        color="warning",
                        className="mb-3"
                    )
                )
    
    return alerts
