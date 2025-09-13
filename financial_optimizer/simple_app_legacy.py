#!/usr/bin/env python3
"""
Simple working version of the financial optimizer app.
"""
from modules.business_mode import create_business_mode_layout
from modules.personal_mode import (
    create_personal_mode_layout,
    register_personal_mode_callbacks
)
from dash import Dash, html, dcc, Input, Output, State, callback, callback_context
from dash import dash_table
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
from core.investment_forms import create_investment_modal
import json
import os

# Simple data persistence
DATA_FILE = '/workspaces/financial_optimizer/data/investments.json'


def load_investments():
    """Load investments from file"""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                return json.load(f)
        except:
            return []
    return []


def save_investments(investments):
    """Save investments to file"""
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, 'w') as f:
        json.dump(investments, f, indent=2)


# Import subscription modules

# Create the app
app = Dash(__name__, external_stylesheets=[
           dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True)

# Simple layout with your main tabs
app.layout = html.Div([
    dbc.Container([
        html.H1("Financial Optimizer", className="text-center mb-4"),

        # Development use case selector (subscription-based in production)
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("Development Controls"),
                        html.P([
                            "Manual switching for development - ",
                            "will be subscription-based in production"
                        ], className="text-muted small"),
                        dbc.Select(
                            id="use-case-selector",
                            options=[
                                {"label": "Business", "value": "business"},
                                {"label": "Personal", "value": "personal"},
                                {"label": "Charity", "value": "charity"},
                                {"label": "Non-Profit", "value": "non_profit"},
                            ],
                            value="business",
                        ),
                    ])
                ])
            ], width=12, className="mb-4")
        ]),

        # Main content with tabs (will be updated based on use case)
        html.Div(id="main-tabs"),

        # Content that changes based on use case
        html.Div(id="use-case-content", className="mt-4"),
    ])
])

# Callback to update tabs based on use case


@app.callback(
    Output("main-tabs", "children"),
    Input("use-case-selector", "value")
)
def update_tabs(use_case):
    if use_case == "business":
        return create_business_mode_layout()
    elif use_case == "personal":
        # Personal Mode - Development Module (Goal-Based Subscription)
        print("DEBUG: Loading Personal Mode...")
        try:
            # Create personal mode layout with error isolation
            print("DEBUG: Calling create_personal_mode_layout()...")
            personal_layout = create_personal_mode_layout()
            print("DEBUG: Personal mode layout created successfully!")
            # Wrap in container to isolate from main app callbacks
            return html.Div([
                personal_layout
            ], id="personal-mode-wrapper")
        except Exception as e:
            # Fallback to simple personal mode if there are any issues
            print(f"DEBUG: Personal Mode fallback activated: {e}")
            import traceback
            traceback.print_exc()
            return dbc.Tabs([
                dbc.Tab(label="Personal Dashboard", children=[
                    html.Div([
                        html.H3("Personal Financial Dashboard"),
                        dbc.Alert("Personal Mode", color="info"),
                        dbc.Alert(
                            "Note: Advanced Personal Mode temporarily unavailable.",
                            color="warning"
                        ),
                        html.P("Basic personal financial management interface."),
                    ], className="p-3")
                ])
            ])

    elif use_case == "charity":
        return dbc.Tabs([
            dbc.Tab(label="Donation Dashboard", children=[
                html.Div([
                    html.H3("Donation Dashboard"),
                    dbc.Alert(
                        "Charity donation tracking dashboard (placeholder)", color="warning"),
                    html.P("Track donations, donors, and fundraising campaigns"),
                ], className="p-3")
            ]),

            dbc.Tab(label="Impact Tracking", children=[
                html.Div([
                    html.H3("Impact Tracking"),
                    dbc.Alert(
                        "Charity impact measurement (placeholder)", color="warning"),
                    html.P("Measure and report on charitable impact"),
                ], className="p-3")
            ]),

            dbc.Tab(label="Grant Management", children=[
                html.Div([
                    html.H3("Grant Management"),
                    dbc.Alert(
                        "Grant application and management (placeholder)", color="warning"),
                    html.P("Manage grant applications and compliance"),
                ], className="p-3")
            ]),
        ])

    elif use_case == "non_profit":
        return dbc.Tabs([
            dbc.Tab(label="Program Dashboard", children=[
                html.Div([
                    html.H3("Program Dashboard"),
                    dbc.Alert(
                        "Non-profit program management dashboard (placeholder)", color="secondary"),
                    html.P("Track program performance and outcomes"),
                ], className="p-3")
            ]),

            dbc.Tab(label="Funding Management", children=[
                html.Div([
                    html.H3("Funding Management"),
                    dbc.Alert(
                        "Non-profit funding management (placeholder)", color="secondary"),
                    html.P("Manage funding sources and allocation"),
                ], className="p-3")
            ]),

            dbc.Tab(label="Compliance", children=[
                html.Div([
                    html.H3("Compliance"),
                    dbc.Alert(
                        "Non-profit compliance tracking (placeholder)", color="secondary"),
                    html.P("Track compliance requirements and reporting"),
                ], className="p-3")
            ]),
        ])

    else:
        return dbc.Alert("Please select a use case to see the available tabs.", color="light")


# Callback to update content based on use case
@app.callback(
    Output("use-case-content", "children"),
    Input("use-case-selector", "value")
)
def update_use_case_content(use_case):
    if use_case == "business":
        return dbc.Alert("🏢 Business Mode: Focus on production and departmental analytics", color="success")
    elif use_case == "personal":
        return dbc.Alert("💰 Personal Mode: Focus on investments and portfolio management", color="info")
    elif use_case == "charity":
        return dbc.Alert("❤️ Charity Mode: Focus on donations and impact tracking", color="warning")
    elif use_case == "non_profit":
        return dbc.Alert("🌟 Non-Profit Mode: Focus on grants and program management", color="secondary")
    else:
        return dbc.Alert("Select a use case to see specialized content.", color="light")


# Investment Management Callbacks

# Calculation functions for automated savings
def calculate_capital_equipment_savings(business_data, investment_params):
    """Calculate savings from capital equipment investments"""
    # Extract business data
    current_oee = business_data.get('current_oee', 65) / 100
    daily_target = business_data.get('daily_target', 500)
    unit_value = business_data.get('unit_value', 150)
    operating_days = business_data.get('operating_days', 250)

    # Extract investment parameters
    efficiency_improvement = investment_params.get(
        'efficiency_improvement', 5) / 100

    # Calculate improved OEE
    improved_oee = min(current_oee * (1 + efficiency_improvement), 0.95)

    # Calculate additional units per day
    additional_units_per_day = daily_target * (improved_oee - current_oee)

    # Calculate annual savings
    annual_additional_units = additional_units_per_day * operating_days
    annual_savings = annual_additional_units * unit_value

    return max(0, annual_savings)


def calculate_process_improvement_savings(business_data, investment_params):
    """Calculate savings from process improvement investments"""
    # Extract business data
    daily_target = business_data.get('daily_target', 500)
    unit_value = business_data.get('unit_value', 150)
    operating_days = business_data.get('operating_days', 250)
    defect_rate = business_data.get('defect_rate', 3.5) / 100
    rework_cost = business_data.get('rework_cost', 75)

    # Extract investment parameters
    efficiency_improvement = investment_params.get(
        'efficiency_improvement', 5) / 100

    # Calculate quality improvement (reduced defects)
    improved_defect_rate = max(
        defect_rate * (1 - efficiency_improvement), 0.005)
    defect_reduction = defect_rate - improved_defect_rate

    # Calculate annual savings from reduced defects
    annual_units = daily_target * operating_days
    annual_defect_reduction = annual_units * defect_reduction
    annual_savings = annual_defect_reduction * (unit_value + rework_cost)

    return max(0, annual_savings)


def calculate_people_training_savings(business_data, investment_params):
    """Calculate savings from people/training investments"""
    # Extract business data
    staff_count = business_data.get('staff_count', 12)
    hourly_rate = business_data.get('hourly_rate', 25)
    shift_hours = business_data.get('shift_hours', 8)
    shifts_count = business_data.get('shifts_count', 2)
    operating_days = business_data.get('operating_days', 250)

    # Extract investment parameters
    productivity_increase = investment_params.get(
        'productivity_increase', 15) / 100

    # Calculate annual working hours
    annual_hours = shift_hours * shifts_count * operating_days

    # Calculate productivity savings
    productivity_savings = staff_count * hourly_rate * \
        annual_hours * productivity_increase

    return max(0, productivity_savings)


def calculate_maintenance_savings(business_data, investment_params):
    """Calculate savings from reduced maintenance"""
    # Extract business data
    planned_maintenance = business_data.get('planned_maintenance', 40)
    unplanned_downtime = business_data.get('unplanned_downtime', 15)
    maintenance_cost = business_data.get('maintenance_cost', 120)

    # Extract investment parameters
    maintenance_reduction = investment_params.get(
        'maintenance_reduction', 10) / 100

    # Calculate annual maintenance savings
    monthly_maintenance_hours = planned_maintenance + unplanned_downtime
    annual_maintenance_hours = monthly_maintenance_hours * 12

    # Calculate savings from reduced maintenance
    annual_savings = annual_maintenance_hours * \
        maintenance_reduction * maintenance_cost

    return max(0, annual_savings)


# Callback to automatically calculate savings based on business data and investment parameters
@callback(
    Output('investment-savings-display', 'value'),
    [Input('investment-type-dropdown', 'value'),
     Input('efficiency-input', 'value'),
     Input('current-oee-input', 'value'),
     Input('daily-target-input', 'value'),
     Input('unit-value-input', 'value'),
     Input('operating-days-input', 'value'),
     Input('defect-rate-data-input', 'value'),
     Input('rework-cost-input', 'value'),
     Input('staff-count-data-input', 'value'),
     Input('hourly-rate-input', 'value'),
     Input('shift-hours-input', 'value'),
     Input('shifts-count-input', 'value'),
     Input('planned-maintenance-input', 'value'),
     Input('unplanned-downtime-input', 'value'),
     Input('maintenance-cost-input', 'value')]
)
def calculate_investment_savings(investment_type, efficiency_improvement, current_oee, daily_target,
                                 unit_value, operating_days, defect_rate, rework_cost, staff_count,
                                 hourly_rate, shift_hours, shifts_count, planned_maintenance,
                                 unplanned_downtime, maintenance_cost):
    """Calculate investment savings based on business data and investment type"""

    # Default values if inputs are None
    business_data = {
        'current_oee': current_oee or 65,
        'daily_target': daily_target or 500,
        'unit_value': unit_value or 150,
        'operating_days': operating_days or 250,
        'defect_rate': defect_rate or 3.5,
        'rework_cost': rework_cost or 75,
        'staff_count': staff_count or 12,
        'hourly_rate': hourly_rate or 25,
        'shift_hours': shift_hours or 8,
        'shifts_count': shifts_count or 2,
        'planned_maintenance': planned_maintenance or 40,
        'unplanned_downtime': unplanned_downtime or 15,
        'maintenance_cost': maintenance_cost or 120
    }

    investment_params = {
        'efficiency_improvement': efficiency_improvement or 5,
        'productivity_increase': 15,  # Default for people/training
        'maintenance_reduction': 10   # Default for maintenance reduction
    }

    if not investment_type:
        return None

    # Calculate savings based on investment type
    if investment_type == 'capital':
        savings = calculate_capital_equipment_savings(
            business_data, investment_params)
        # Add maintenance savings for capital equipment
        savings += calculate_maintenance_savings(
            business_data, investment_params)
    elif investment_type == 'process':
        savings = calculate_process_improvement_savings(
            business_data, investment_params)
    elif investment_type == 'people':
        savings = calculate_people_training_savings(
            business_data, investment_params)
    else:
        savings = 0

    return round(savings, 2)


# Callback to update business metrics summary
@callback(
    Output('business-metrics-summary', 'children'),
    [Input('current-oee-input', 'value'),
     Input('daily-target-input', 'value'),
     Input('unit-value-input', 'value'),
     Input('operating-days-input', 'value'),
     Input('defect-rate-data-input', 'value'),
     Input('staff-count-data-input', 'value'),
     Input('hourly-rate-input', 'value')]
)
def update_business_metrics(current_oee, daily_target, unit_value, operating_days,
                            defect_rate, staff_count, hourly_rate):
    """Update the business metrics summary display"""

    # Use default values if inputs are None
    oee = current_oee or 65
    target = daily_target or 500
    value = unit_value or 150
    days = operating_days or 250
    defects = defect_rate or 3.5
    staff = staff_count or 12
    rate = hourly_rate or 25

    # Calculate key metrics
    annual_production_target = target * days
    annual_revenue_potential = annual_production_target * value
    annual_defect_units = annual_production_target * (defects / 100)
    annual_labor_cost = staff * rate * 8 * 2 * \
        days  # 8 hours, 2 shifts, operating days

    return [
        dbc.Row([
            dbc.Col([
                html.H6("Annual Production Target", className="text-muted"),
                html.H4(f"{annual_production_target:,.0f} units",
                        className="text-primary")
            ], width=6),
            dbc.Col([
                html.H6("Annual Revenue Potential", className="text-muted"),
                html.H4(f"£{annual_revenue_potential:,.0f}",
                        className="text-success")
            ], width=6),
        ], className="mb-3"),
        dbc.Row([
            dbc.Col([
                html.H6("Expected Defective Units", className="text-muted"),
                html.H4(f"{annual_defect_units:,.0f} units",
                        className="text-warning")
            ], width=6),
            dbc.Col([
                html.H6("Annual Labor Cost", className="text-muted"),
                html.H4(f"£{annual_labor_cost:,.0f}", className="text-info")
            ], width=6),
        ], className="mb-3"),
        dbc.Row([
            dbc.Col([
                html.H6("Current OEE Impact", className="text-muted"),
                html.H4(f"{oee}% efficiency", className="text-secondary")
            ], width=12),
        ])
    ]


# Callback to show/hide conditional parameters based on investment type
@callback(
    [Output('capital-equipment-params', 'style'),
     Output('process-improvement-params', 'style'),
     Output('people-training-params', 'style')],
    [Input('investment-type-dropdown', 'value')]
)
def toggle_conditional_params(investment_type):
    """Show/hide parameter sections based on investment type"""
    capital_style = {"display": "none"}
    process_style = {"display": "none"}
    people_style = {"display": "none"}

    if investment_type == 'capital':
        capital_style = {"display": "block"}
    elif investment_type == 'process':
        process_style = {"display": "block"}
    elif investment_type == 'people':
        people_style = {"display": "block"}

    return capital_style, process_style, people_style


@callback(
    [Output('investments-store', 'data'),
     Output('investments-table', 'data'),
     Output('investment-name-input', 'value'),
     Output('investment-type-dropdown', 'value'),
     Output('investment-business-model-dropdown', 'value'),
     Output('investment-production-line-dropdown', 'value'),
     Output('investment-cost-input', 'value'),
     Output('implementation-time-input', 'value'),
     Output('efficiency-input', 'value')],
    [Input('add-investment-button', 'n_clicks')],
    [State('investments-store', 'data'),
     State('investment-name-input', 'value'),
     State('investment-type-dropdown', 'value'),
     State('investment-business-model-dropdown', 'value'),
     State('investment-production-line-dropdown', 'value'),
     State('investment-cost-input', 'value'),
     State('investment-savings-display', 'value'),
     State('implementation-time-input', 'value'),
     State('efficiency-input', 'value')]
)
def update_investments_table(n_clicks, current_data, name, inv_type, business_model, production_line, cost, savings, impl_time, efficiency):
    """Add new investment to the table"""
    print(f"DEBUG: n_clicks={n_clicks}, name={name}, inv_type={inv_type}, business_model={business_model}, production_line={production_line}, cost={cost}, savings={savings}")

    # Initialize current_data if it's None
    if current_data is None:
        current_data = []

    # Return early if button hasn't been clicked
    if n_clicks is None or n_clicks == 0:
        return current_data, current_data, None, None, 'cost_center', 'line_1', None, 3, 5

    # Check if all required fields are filled
    if not all([name, inv_type, business_model, production_line, cost is not None, savings is not None]):
        print("DEBUG: Missing required fields")
        return current_data, current_data, None, None, 'cost_center', 'line_1', None, 3, 5

    # Calculate ROI
    roi = (savings / cost) * 100 if cost > 0 else 0

    # Create friendly labels for display
    business_model_label = "Profit Center" if business_model == "profit_center" else "Cost Center"
    production_line_label = {
        'line_1': 'Line 1',
        'line_2': 'Line 2',
        'line_3': 'Line 3',
        'line_4': 'Line 4',
        'line_5': 'Line 5',
        'line_6': 'Line 6',
        'all_lines': 'All Lines'
    }.get(production_line, production_line)

    # Create new investment record
    new_investment = {
        'name': name,
        'type': inv_type.title(),
        'business_model': business_model_label,
        'production_line': production_line_label,
        'cost': cost,
        'savings': savings,
        'roi': roi,
        'implementation_time': impl_time if impl_time is not None else 3,
        'status': 'Planned'
    }

    print(f"DEBUG: Adding investment: {new_investment}")

    # Add to existing data
    updated_data = current_data + [new_investment]

    # Clear form inputs
    return updated_data, updated_data, "", None, 'cost_center', 'line_1', None, 3, 5


@callback(
    [Output('total-investment-cost', 'children'),
     Output('total-annual-savings', 'children'),
     Output('average-roi', 'children')],
    [Input('investments-table', 'data')]
)
def update_investment_summary(data):
    """Update investment summary cards"""
    if not data:
        return "£0", "£0", "0%"

    total_cost = sum(item['cost'] for item in data)
    total_savings = sum(item['savings'] for item in data)
    avg_roi = sum(item['roi'] for item in data) / len(data) if data else 0

    return f"£{total_cost:,.2f}", f"£{total_savings:,.2f}", f"{avg_roi:.1f}%"


@callback(
    Output('investments-store', 'data', allow_duplicate=True),
    Input('investments-table', 'data'),
    prevent_initial_call=True
)
def sync_store_with_table(table_data):
    """Sync store when table is modified (e.g., row deletion)"""
    return table_data


# Callback for business model dynamic content
@app.callback(
    Output("business-model-content", "children"),
    Input("business-model-selector", "value")
)
def update_business_model_content(business_model):
    if not business_model:
        return []

    # Investment types based on your specification
    investment_types = [
        {
            "id": "capital",
            "title": "Capital Equipment & Assets",
            "description": "Equipment, machinery, and physical assets",
            "icon": "🏭"
        },
        {
            "id": "process",
            "title": "Process Improvement & Optimization",
            "description": "Workflow optimization and process enhancement",
            "icon": "⚙️"
        },
        {
            "id": "people",
            "title": "Human Capital & Training",
            "description": "Training programs and workforce development",
            "icon": "👥"
        },
        {
            "id": "maintenance",
            "title": "Maintenance & Asset Reliability",
            "description": "Preventive maintenance and asset optimization",
            "icon": "🔧"
        },
        {
            "id": "quality",
            "title": "Quality Systems & Compliance",
            "description": "Quality improvement and compliance systems",
            "icon": "✅"
        },
        {
            "id": "digital",
            "title": "Digital Transformation & Industry 4.0",
            "description": "Automation, IoT, and digital systems",
            "icon": "🤖"
        },
        {
            "id": "safety",
            "title": "Safety & Environmental Systems",
            "description": "Safety improvements and environmental compliance",
            "icon": "🛡️"
        },
        {
            "id": "facility",
            "title": "Facility & Infrastructure",
            "description": "Building improvements and infrastructure",
            "icon": "🏢"
        },
        {
            "id": "supply_chain",
            "title": "Supply Chain & Logistics",
            "description": "Supply chain optimization and logistics",
            "icon": "🚚"
        }
    ]

    model_name = "Profit Center" if business_model == "profit_center" else "Cost Center"

    return [
        dbc.Alert([
            html.H5(f"{model_name} Investment Types",
                    className="alert-heading"),
            html.P(f"Select investment types to upload data for {model_name.lower()} calculations. "
                   f"Click any box to open the detailed form with upload and mapping features."),
        ], color="info", className="mb-4"),

        # Investment type boxes grid
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5([
                            html.Span(inv_type["icon"], className="me-2"),
                            inv_type["title"]
                        ], className="card-title"),
                        html.P(inv_type["description"], className="card-text"),
                        dbc.Button(
                            "Configure & Upload Data",
                            id=f"open-{inv_type['id']}-form",
                            color="primary",
                            size="sm",
                            className="w-100"
                        )
                    ])
                ], className="h-100 shadow-sm hover-shadow",
                    style={"cursor": "pointer", "transition": "all 0.2s"})
            ], width=6, lg=4, className="mb-3")
            for inv_type in investment_types
        ]),

        # Store the selected business model for forms
        dcc.Store(id="selected-business-model", data=business_model),

        # Modal container for investment forms
        html.Div(id="investment-form-modal"),

        # Summary of configured investment types
        html.Div(id="configured-investments-summary", className="mt-4")
    ]

# Callback to update organizational unit label and options based on business model


@app.callback(
    [Output("organizational-unit-label", "children"),
     Output("investment-organizational-unit-dropdown", "options"),
     Output("investment-organizational-unit-dropdown", "value")],
    Input("investment-business-model-dropdown", "value")
)
def update_organizational_unit_field(business_model):
    """Update the organizational unit field based on business model selection."""
    if business_model == "cost_center":
        label = "Cost Center:"
        options = [
            {'label': 'Surface Finish Department', 'value': 'surface_finish'},
            {'label': 'Machining Department', 'value': 'machining'},
            {'label': 'Quality Control Department', 'value': 'quality_control'},
            {'label': 'Maintenance Department', 'value': 'maintenance'},
            {'label': 'Packaging Department', 'value': 'packaging'},
            {'label': 'Warehouse Operations', 'value': 'warehouse'}
        ]
        default_value = 'surface_finish'
    else:  # profit_center
        label = "Production Line:"
        options = [
            {'label': 'Line 1 - Surface Finish Primary', 'value': 'line_1'},
            {'label': 'Line 2 - Surface Finish Secondary', 'value': 'line_2'},
            {'label': 'Line 3 - Plating Line A', 'value': 'line_3'},
            {'label': 'Line 4 - Plating Line B', 'value': 'line_4'},
            {'label': 'Line 5 - Quality Control', 'value': 'line_5'},
            {'label': 'Line 6 - Packaging/Finishing', 'value': 'line_6'}
        ]
        default_value = 'line_1'

    return label, options, default_value

# Callback for business metrics summary


@app.callback(
    Output("business-metrics-summary", "children"),
    [Input("business-model-selector", "value")] +
    [Input(f"{input_id}-input", "value") for input_id in [
        "current-oee", "daily-target", "unit-value", "operating-days",
        "shift-hours", "shifts-count", "planned-maintenance", "unplanned-downtime",
        "maintenance-cost", "staff-count-data", "hourly-rate", "staff-utilization",
        "defect-rate-data", "rework-cost", "scrap-cost",
        # Cost center inputs
        "dept-oee", "daily-throughput", "processing-cost", "cost-center-days",
        "cost-center-hours", "capacity-utilization", "cc-planned-maintenance",
        "cc-unplanned-downtime", "cc-maintenance-cost", "cc-staff-count",
        "cc-hourly-rate", "cc-labor-efficiency", "cc-defect-rate",
        "cc-rework-cost", "cc-waste-cost", "cc-energy-usage",
        "cc-energy-cost", "cc-utility-cost"
    ]],
    prevent_initial_call=True
)
def update_business_metrics(business_model, *input_values):
    # Get input values, handling None values
    inputs = list(input_values)
    for i in range(len(inputs)):
        if inputs[i] is None:
            inputs[i] = 0

    if business_model == "profit_center":
        # Use first 15 values for profit center
        current_oee, daily_target, unit_value, operating_days, shift_hours, shifts_count, \
            planned_maintenance, unplanned_downtime, maintenance_cost, staff_count, \
            hourly_rate, staff_utilization, defect_rate, rework_cost, scrap_cost = inputs[
                :15]

        # Calculate profit center metrics
        annual_production = daily_target * operating_days
        annual_revenue = annual_production * unit_value
        total_downtime = (planned_maintenance + unplanned_downtime) * 12
        annual_maintenance_cost = total_downtime * maintenance_cost
        annual_labor_cost = staff_count * hourly_rate * \
            shift_hours * shifts_count * operating_days
        annual_quality_cost = annual_production * \
            (defect_rate / 100) * (rework_cost + scrap_cost)

        return [
            dbc.Row([
                dbc.Col([
                    html.H6("Annual Production:", className="fw-bold"),
                    html.P(f"{annual_production:,.0f} units")
                ], width=4),
                dbc.Col([
                    html.H6("Annual Revenue:", className="fw-bold"),
                    html.P(f"£{annual_revenue:,.0f}")
                ], width=4),
                dbc.Col([
                    html.H6("Current OEE:", className="fw-bold"),
                    html.P(f"{current_oee}%")
                ], width=4),
            ], className="mb-3"),
            dbc.Row([
                dbc.Col([
                    html.H6("Annual Maintenance Cost:", className="fw-bold"),
                    html.P(f"£{annual_maintenance_cost:,.0f}")
                ], width=4),
                dbc.Col([
                    html.H6("Annual Labor Cost:", className="fw-bold"),
                    html.P(f"£{annual_labor_cost:,.0f}")
                ], width=4),
                dbc.Col([
                    html.H6("Annual Quality Cost:", className="fw-bold"),
                    html.P(f"£{annual_quality_cost:,.0f}")
                ], width=4),
            ], className="mb-3"),
        ]
    else:  # cost_center
        # Use values from index 15 onwards for cost center
        dept_oee, daily_throughput, processing_cost, cost_center_days, \
            cost_center_hours, capacity_utilization, cc_planned_maintenance, \
            cc_unplanned_downtime, cc_maintenance_cost, cc_staff_count, \
            cc_hourly_rate, cc_labor_efficiency, cc_defect_rate, \
            cc_rework_cost, cc_waste_cost, cc_energy_usage, \
            cc_energy_cost, cc_utility_cost = inputs[15:]

        # Calculate cost center metrics
        annual_throughput = daily_throughput * cost_center_days
        annual_processing_cost = annual_throughput * processing_cost
        total_downtime = (cc_planned_maintenance + cc_unplanned_downtime) * 12
        annual_maintenance_cost = total_downtime * cc_maintenance_cost
        annual_labor_cost = cc_staff_count * cc_hourly_rate * \
            cost_center_hours * cost_center_days
        annual_quality_cost = annual_throughput * \
            (cc_defect_rate / 100) * (cc_rework_cost + cc_waste_cost)
        annual_energy_cost = annual_throughput * cc_energy_usage * cc_energy_cost
        annual_utility_cost = cc_utility_cost * 12

        return [
            dbc.Row([
                dbc.Col([
                    html.H6("Annual Throughput:", className="fw-bold"),
                    html.P(f"{annual_throughput:,.0f} units")
                ], width=4),
                dbc.Col([
                    html.H6("Annual Processing Cost:", className="fw-bold"),
                    html.P(f"£{annual_processing_cost:,.0f}")
                ], width=4),
                dbc.Col([
                    html.H6("Department OEE:", className="fw-bold"),
                    html.P(f"{dept_oee}%")
                ], width=4),
            ], className="mb-3"),
            dbc.Row([
                dbc.Col([
                    html.H6("Annual Maintenance Cost:", className="fw-bold"),
                    html.P(f"£{annual_maintenance_cost:,.0f}")
                ], width=4),
                dbc.Col([
                    html.H6("Annual Labor Cost:", className="fw-bold"),
                    html.P(f"£{annual_labor_cost:,.0f}")
                ], width=4),
                dbc.Col([
                    html.H6("Annual Quality Cost:", className="fw-bold"),
                    html.P(f"£{annual_quality_cost:,.0f}")
                ], width=4),
            ], className="mb-3"),
            dbc.Row([
                dbc.Col([
                    html.H6("Annual Energy Cost:", className="fw-bold"),
                    html.P(f"£{annual_energy_cost:,.0f}")
                ], width=4),
                dbc.Col([
                    html.H6("Annual Utility Cost:", className="fw-bold"),
                    html.P(f"£{annual_utility_cost:,.0f}")
                ], width=4),
                dbc.Col([
                    html.H6("Capacity Utilization:", className="fw-bold"),
                    html.P(f"{capacity_utilization}%")
                ], width=4),
            ], className="mb-3"),
        ]


# ========================= PERSONAL INVESTMENT MANAGEMENT CALLBACKS =========================

# Real-time personal investment calculations
@app.callback(
    [Output('personal-total-value-display', 'value'),
     Output('personal-gain-loss-display', 'value'),
     Output('personal-gain-loss-percent-display', 'value'),
     Output('personal-yield-display', 'value')],
    [Input('personal-investment-shares-input', 'value'),
     Input('personal-investment-price-input', 'value'),
     Input('personal-current-price-input', 'value'),
     Input('personal-dividend-input', 'value')]
)
def calculate_personal_investment_metrics(shares, purchase_price, current_price, annual_dividend):
    if not all([shares, purchase_price, current_price]):
        return "£0.00", "£0.00", "0.0%", "0.0%"

    try:
        shares = float(shares)
        purchase_price = float(purchase_price)
        current_price = float(current_price)
        annual_dividend = float(annual_dividend or 0)

        # Calculate total values
        total_investment = shares * purchase_price
        total_current_value = shares * current_price

        # Calculate gain/loss
        gain_loss = total_current_value - total_investment
        gain_loss_percent = (gain_loss / total_investment *
                             100) if total_investment > 0 else 0

        # Calculate dividend yield
        total_dividend = shares * annual_dividend
        yield_percent = (total_dividend / total_investment *
                         100) if total_investment > 0 else 0

        return (
            f"£{total_current_value:,.2f}",
            f"£{gain_loss:,.2f}",
            f"{gain_loss_percent:.1f}%",
            f"{yield_percent:.2f}%"
        )
    except (ValueError, TypeError):
        return "£0.00", "£0.00", "0.0%", "0.0%"

# Add personal investment to portfolio


@app.callback(
    Output('personal-investments-store', 'data'),
    Input('add-personal-investment-button', 'n_clicks'),
    State('personal-investments-store', 'data'),
    State('personal-investment-name-input', 'value'),
    State('personal-investment-type-dropdown', 'value'),
    State('personal-investment-symbol-input', 'value'),
    State('personal-investment-category-dropdown', 'value'),
    State('personal-account-type-dropdown', 'value'),
    State('personal-investment-shares-input', 'value'),
    State('personal-investment-price-input', 'value'),
    State('personal-current-price-input', 'value'),
    State('personal-dividend-input', 'value'),
    State('personal-purchase-date-input', 'value'),
    State('personal-target-allocation-input', 'value')
)
def add_personal_investment(n_clicks, current_data, name, inv_type, symbol, category, account,
                            shares, purchase_price, current_price, dividend, purchase_date, allocation):
    if n_clicks == 0 or not all([name, inv_type, shares, purchase_price, current_price]):
        return current_data or []

    try:
        shares = float(shares)
        purchase_price = float(purchase_price)
        current_price = float(current_price)
        dividend = float(dividend or 0)
        allocation = float(allocation or 0)

        # Calculate metrics
        total_investment = shares * purchase_price
        total_current_value = shares * current_price
        gain_loss = total_current_value - total_investment
        gain_loss_percent = (gain_loss / total_investment *
                             100) if total_investment > 0 else 0
        total_dividend = shares * dividend
        yield_percent = (total_dividend / total_investment *
                         100) if total_investment > 0 else 0

        # Get display labels for dropdowns
        type_labels = {
            'stocks': '📈 Stocks',
            'bonds': '🏛️ Bonds',
            'etfs': '📊 ETFs',
            'mutual_funds': '🎯 Mutual Funds',
            'real_estate': '🏠 Real Estate',
            'crypto': '₿ Crypto',
            'retirement': '🏦 Retirement',
            'savings': '💰 Savings',
            'international': '🌍 International',
            'other': '📋 Other'
        }

        category_labels = {
            'growth': 'Growth',
            'income': 'Income',
            'balanced': 'Balanced',
            'speculative': 'Speculative',
            'conservative': 'Conservative',
            'retirement': 'Retirement'
        }

        account_labels = {
            'taxable': 'Taxable Brokerage',
            '401k': '401(k)',
            'trad_ira': 'Traditional IRA',
            'roth_ira': 'Roth IRA',
            'hsa': 'HSA',
            'savings': 'Savings',
            'other': 'Other'
        }

        new_investment = {
            'id': len(current_data or []) + 1,
            'name': name,
            'type': type_labels.get(inv_type, inv_type),
            'symbol': symbol or '-',
            'category': category_labels.get(category, category),
            'account': account_labels.get(account, account),
            'shares': shares,
            'purchase_price': purchase_price,
            'current_price': current_price,
            'total_value': total_current_value,
            'gain_loss': gain_loss,
            'gain_loss_percent': gain_loss_percent,
            'dividend': dividend,
            'yield': yield_percent,
            'purchase_date': purchase_date or '',
            'allocation': allocation
        }

        updated_data = (current_data or []) + [new_investment]
        return updated_data

    except (ValueError, TypeError):
        return current_data or []

# Update personal investments table and portfolio metrics


@app.callback(
    [Output('personal-investments-table', 'data'),
     Output('personal-total-portfolio-value', 'children'),
     Output('personal-total-gain-loss', 'children'),
     Output('personal-portfolio-return', 'children'),
     Output('personal-dividend-income', 'children')],
    [Input('personal-investments-store', 'data'),
     Input('personal-investments-table', 'data_previous'),
     Input('personal-investments-table', 'data')]
)
def update_personal_investments_display(stored_data, prev_table_data, current_table_data):
    ctx = callback_context

    # Handle row deletions
    if ctx.triggered and 'personal-investments-table' in ctx.triggered[0]['prop_id']:
        # Update stored data when table is modified
        if current_table_data is not None:
            return current_table_data, *calculate_personal_portfolio_totals(current_table_data)

    # Use stored data
    investments_data = stored_data or []

    if not investments_data:
        return [], "£0.00", "£0.00", "0.0%", "£0.00"

    # Calculate portfolio totals
    totals = calculate_personal_portfolio_totals(investments_data)

    return investments_data, *totals


def calculate_personal_portfolio_totals(investments_data):
    """Calculate portfolio summary metrics"""
    if not investments_data:
        return "£0.00", "£0.00", "0.0%", "£0.00"

    total_value = sum(inv.get('total_value', 0) for inv in investments_data)
    total_cost = sum(inv.get('shares', 0) * inv.get('purchase_price', 0)
                     for inv in investments_data)
    total_gain_loss = total_value - total_cost
    portfolio_return = (total_gain_loss / total_cost *
                        100) if total_cost > 0 else 0
    total_dividend = sum(inv.get('shares', 0) * inv.get('dividend', 0)
                         for inv in investments_data)

    # Format return color
    return_class = "text-success" if total_gain_loss >= 0 else "text-danger"

    return (
        f"£{total_value:,.2f}",
        f"£{total_gain_loss:,.2f}",
        f"{portfolio_return:.1f}%",
        f"£{total_dividend:,.2f}"
    )

# Clear personal investment form after adding


@app.callback(
    [Output('personal-investment-name-input', 'value'),
     Output('personal-investment-type-dropdown', 'value'),
     Output('personal-investment-symbol-input', 'value'),
     Output('personal-investment-category-dropdown', 'value'),
     Output('personal-account-type-dropdown', 'value'),
     Output('personal-investment-shares-input', 'value'),
     Output('personal-investment-price-input', 'value'),
     Output('personal-current-price-input', 'value'),
     Output('personal-dividend-input', 'value'),
     Output('personal-purchase-date-input', 'value'),
     Output('personal-target-allocation-input', 'value')],
    Input('add-personal-investment-button', 'n_clicks'),
    prevent_initial_call=True
)
def clear_personal_investment_form(n_clicks):
    if n_clicks > 0:
        return '', None, '', 'balanced', 'taxable', None, None, None, 0, '', None
    return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update


# Business Mode Modal Callbacks
@callback(
    Output("modal-capital", "is_open"),
    [Input("open-capital-form", "n_clicks"), Input("cancel-capital",
                                                   "n_clicks"), Input("save-capital", "n_clicks")],
    [State("modal-capital", "is_open")],
    prevent_initial_call=True
)
def toggle_capital_modal(open_clicks, cancel_clicks, save_clicks, is_open):
    """Toggle capital equipment modal."""
    if open_clicks or cancel_clicks or save_clicks:
        return not is_open
    return is_open


@callback(
    Output("modal-process", "is_open"),
    [Input("open-process-form", "n_clicks"), Input("cancel-process",
                                                   "n_clicks"), Input("save-process", "n_clicks")],
    [State("modal-process", "is_open")],
    prevent_initial_call=True
)
def toggle_process_modal(open_clicks, cancel_clicks, save_clicks, is_open):
    """Toggle process improvement modal."""
    if open_clicks or cancel_clicks or save_clicks:
        return not is_open
    return is_open


@callback(
    Output("modal-people", "is_open"),
    [Input("open-people-form", "n_clicks"), Input("cancel-people",
                                                  "n_clicks"), Input("save-people", "n_clicks")],
    [State("modal-people", "is_open")],
    prevent_initial_call=True
)
def toggle_people_modal(open_clicks, cancel_clicks, save_clicks, is_open):
    """Toggle human capital modal."""
    if open_clicks or cancel_clicks or save_clicks:
        return not is_open
    return is_open


# Investment Management Callbacks
@callback(
    [Output("investment-portfolio-table", "data"),
     Output("empty-investments-message", "style"),
     Output("investment-table-container", "style"),
     Output("total-investments-count", "children"),
     Output("total-investment-cost", "children"),
     Output("new-investment-name", "value"),
     Output("new-investment-type", "value"),
     Output("new-investment-cost", "value"),
     Output("new-investment-line", "value"),
     Output("new-investment-timeline", "value")],
    [Input("create-investment-btn", "n_clicks")],
    [State("new-investment-name", "value"),
     State("new-investment-type", "value"),
     State("new-investment-cost", "value"),
     State("new-investment-line", "value"),
     State("new-investment-timeline", "value")]
)
def manage_investments(n_clicks, name, inv_type, cost, line, timeline):
    """Handle investment creation and display"""

    # Load existing investments
    investments = load_investments()

    # Add new investment if form submitted
    if n_clicks and n_clicks > 0 and name and inv_type and cost:
        try:
            new_investment = {
                "name": name,
                "type": inv_type,
                "production_line": line or "All Lines",
                "cost": float(cost),
                "timeline": int(timeline) if timeline else 3,
                "status": "Planning",
                "actions": "[Edit](edit) | [Delete](delete)"
            }
            investments.append(new_investment)
            save_investments(investments)
            print(f"Investment created: {new_investment['name']}")

            # Clear form
            name, inv_type, cost, line, timeline = "", None, "", None, 3
        except Exception as e:
            print(f"Error creating investment: {e}")

    # Calculate summary statistics
    total_count = len(investments)
    total_cost = sum(inv['cost'] for inv in investments)

    # Show/hide table based on data
    if investments:
        table_style = {"display": "block"}
        message_style = {"display": "none"}
    else:
        table_style = {"display": "none"}
        message_style = {"display": "block"}

    print(f"Returning: {total_count} investments, total cost: £{total_cost}")

    return (investments, message_style, table_style,
            str(total_count), f"£{total_cost:,.0f}",
            name, inv_type, cost, line, timeline)


# Initial load callback to populate table on page load
@callback(
    [Output("investment-portfolio-table", "data", allow_duplicate=True),
     Output("empty-investments-message", "style", allow_duplicate=True),
     Output("investment-table-container", "style", allow_duplicate=True),
     Output("total-investments-count", "children", allow_duplicate=True),
     Output("total-investment-cost", "children", allow_duplicate=True)],
    [Input("business-mode-tabs", "active_tab")],
    prevent_initial_call='initial_duplicate'
)
def load_initial_investments(active_tab):
    """Load investments when Investment Management tab is accessed"""
    if active_tab == "business-investment-management":
        # Load existing investments
        investments = load_investments()

        # Calculate summary statistics
        total_count = len(investments)
        total_cost = sum(inv['cost'] for inv in investments)

        # Show/hide table based on data
        if investments:
            table_style = {"display": "block"}
            message_style = {"display": "none"}
        else:
            table_style = {"display": "none"}
            message_style = {"display": "block"}

        print(f"Initial load: {total_count} investments, "
              f"total cost: £{total_cost}")

        return (investments, message_style, table_style,
                str(total_count), f"£{total_cost:,.0f}")

    # Return empty state for other tabs
    return [], {"display": "block"}, {"display": "none"}, "0", "£0"


# Personal Mode Data Input Callbacks
@callback(
    Output("manual-entry-modal", "is_open"),
    [Input("open-manual-entry-btn", "n_clicks"),
     Input("cancel-manual-entry", "n_clicks"),
     Input("save-manual-entry", "n_clicks")],
    [State("manual-entry-modal", "is_open")],
    prevent_initial_call=False,  # Changed to False to allow initial calls
    suppress_callback_exceptions=True
)
def toggle_manual_entry_modal(open_clicks, cancel_clicks, save_clicks, is_open):
    """Toggle the manual entry modal for Personal Mode"""
    print(f"DEBUG: Modal callback triggered!")
    print(f"  - open_clicks: {open_clicks}")
    print(f"  - cancel_clicks: {cancel_clicks}")
    print(f"  - save_clicks: {save_clicks}")
    print(f"  - is_open: {is_open}")

    ctx = callback_context
    print(f"  - ctx.triggered: {ctx.triggered}")

    if ctx.triggered:
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        print(f"  - Button clicked: {button_id}")

        if button_id == "open-manual-entry-btn":
            print("  - Opening modal!")
            return True
        elif button_id in ["cancel-manual-entry", "save-manual-entry"]:
            print("  - Closing modal!")
            return False

    return is_open or False


@callback(
    Output("document-upload-section", "style"),
    [Input("open-document-upload-btn", "n_clicks")]
)
def toggle_document_upload_section(n_clicks):
    """Toggle document upload section visibility"""
    if n_clicks and n_clicks > 0:
        return {"display": "block"}
    return {"display": "none"}


@callback(
    [Output("total-income-display", "children"),
     Output("total-expenses-display", "children"),
     Output("net-cashflow-display", "children"),
     Output("net-worth-display", "children"),
     Output("income-breakdown", "children"),
     Output("expenses-breakdown", "children"),
     Output("quick-adjustments-section", "style"),
     Output("adjustment-sliders-container", "children")],
    [Input("save-manual-entry", "n_clicks")],
    [State("gross-salary", "value"),
     State("net-salary", "value"),
     State("bonuses", "value"),
     State("freelance", "value"),
     State("rental-income", "value"),
     State("dividends", "value"),
     State("pension-benefits", "value"),
     State("other-income", "value"),
     State("rent-mortgage", "value"),
     State("utilities", "value"),
     State("council-tax", "value"),
     State("home-insurance", "value"),
     State("groceries", "value"),
     State("transport", "value"),
     State("healthcare", "value"),
     State("entertainment", "value"),
     State("home-value", "value"),
     State("investment-properties", "value"),
     State("savings", "value"),
     State("investments", "value"),
     State("pension-value", "value"),
     State("other-assets", "value"),
     State("mortgage-balance", "value"),
     State("credit-cards", "value"),
     State("personal-loans", "value"),
     State("student-loans", "value"),
     State("other-debts", "value")],
    prevent_initial_call=True
)
def calculate_financial_summary(n_clicks, gross_salary, net_salary, bonuses,
                                freelance, rental_income, dividends,
                                pension_benefits, other_income, rent_mortgage,
                                utilities, council_tax, home_insurance,
                                groceries, transport, healthcare, entertainment,
                                home_value, investment_properties, savings,
                                investments, pension_value, other_assets,
                                mortgage_balance, credit_cards, personal_loans,
                                student_loans, other_debts):
    """Calculate and display financial summary from manual entry"""

    if not n_clicks:
        raise PreventUpdate

    # Calculate totals (handle None values)
    def safe_float(val):
        return float(val) if val is not None else 0.0

    # Income calculation
    total_income = (safe_float(net_salary) + safe_float(bonuses) +
                    safe_float(freelance) + safe_float(rental_income) +
                    safe_float(dividends) + safe_float(pension_benefits) +
                    safe_float(other_income))

    # Expenses calculation
    total_expenses = (safe_float(rent_mortgage) + safe_float(utilities) +
                      safe_float(council_tax) + safe_float(home_insurance) +
                      safe_float(groceries) + safe_float(transport) +
                      safe_float(healthcare) + safe_float(entertainment))

    # Assets calculation
    total_assets = (safe_float(home_value) + safe_float(investment_properties) +
                    safe_float(savings) + safe_float(investments) +
                    safe_float(pension_value) + safe_float(other_assets))

    # Liabilities calculation
    total_liabilities = (safe_float(mortgage_balance) + safe_float(credit_cards) +
                         safe_float(personal_loans) + safe_float(student_loans) +
                         safe_float(other_debts))

    # Net calculations
    net_cashflow = total_income - total_expenses
    net_worth = total_assets - total_liabilities

    # Create income breakdown
    income_items = []
    if safe_float(net_salary) > 0:
        income_items.append(
            html.Div([html.Strong("Net Salary: "), f"£{net_salary:,.0f}"]))
    if safe_float(bonuses) > 0:
        income_items.append(
            html.Div([html.Strong("Bonuses: "), f"£{bonuses:,.0f}"]))
    if safe_float(freelance) > 0:
        income_items.append(
            html.Div([html.Strong("Freelance: "), f"£{freelance:,.0f}"]))
    if safe_float(rental_income) > 0:
        income_items.append(
            html.Div([html.Strong("Rental: "), f"£{rental_income:,.0f}"]))

    # Create expenses breakdown
    expense_items = []
    if safe_float(rent_mortgage) > 0:
        expense_items.append(
            html.Div([html.Strong("Housing: "), f"£{rent_mortgage:,.0f}"]))
    if safe_float(groceries) > 0:
        expense_items.append(
            html.Div([html.Strong("Groceries: "), f"£{groceries:,.0f}"]))
    if safe_float(transport) > 0:
        expense_items.append(
            html.Div([html.Strong("Transport: "), f"£{transport:,.0f}"]))
    if safe_float(utilities) > 0:
        expense_items.append(
            html.Div([html.Strong("Utilities: "), f"£{utilities:,.0f}"]))

    # Create adjustment sliders
    adjustment_sliders = create_adjustment_sliders()

    return (
        f"£{total_income:,.0f}",
        f"£{total_expenses:,.0f}",
        f"£{net_cashflow:,.0f}",
        f"£{net_worth:,.0f}",
        income_items if income_items else [html.Small(
            "No income data entered", className="text-muted")],
        expense_items if expense_items else [html.Small(
            "No expense data entered", className="text-muted")],
        {"display": "block"},
        adjustment_sliders
    )


def create_adjustment_sliders():
    """Create dynamic adjustment sliders for key financial metrics"""
    return html.Div([
        dbc.Row([
            dbc.Col([
                html.Label("Reduce Dining Out (%)", className="fw-bold mb-2"),
                dcc.Slider(
                    id="dining-reduction-slider",
                    min=0, max=50, step=5, value=0,
                    marks={0: '0%', 10: '10%', 25: '25%', 50: '50%'},
                    tooltip={"placement": "bottom", "always_visible": True}
                )
            ], width=3),
            dbc.Col([
                html.Label("Reduce Entertainment (%)",
                           className="fw-bold mb-2"),
                dcc.Slider(
                    id="entertainment-reduction-slider",
                    min=0, max=50, step=5, value=0,
                    marks={0: '0%', 10: '10%', 25: '25%', 50: '50%'},
                    tooltip={"placement": "bottom", "always_visible": True}
                )
            ], width=3),
            dbc.Col([
                html.Label("Increase Income (%)", className="fw-bold mb-2"),
                dcc.Slider(
                    id="income-increase-slider",
                    min=0, max=30, step=5, value=0,
                    marks={0: '0%', 10: '10%', 20: '20%', 30: '30%'},
                    tooltip={"placement": "bottom", "always_visible": True}
                )
            ], width=3),
            dbc.Col([
                html.Label("Investment Percentage (%)",
                           className="fw-bold mb-2"),
                dcc.Slider(
                    id="investment-percentage-slider",
                    min=0, max=100, step=5, value=20,
                    marks={0: '0%', 25: '25%', 50: '50%', 100: '100%'},
                    tooltip={"placement": "bottom", "always_visible": True}
                )
            ], width=3)
        ], className="mb-4"),

        # Impact display
        dbc.Row([
            dbc.Col([
                dbc.Alert([
                    html.I(className="fas fa-chart-line me-2"),
                    html.Span("Adjust sliders above to see real-time impact on your financial metrics",
                              id="slider-impact-text")
                ], color="info")
            ])
        ])
    ])


if __name__ == "__main__":
    print("Starting Simple Financial Optimizer...")
    
    # Register personal mode callbacks for modal functionality
    register_personal_mode_callbacks(app)
    
    app.run_server(debug=True, port=8050)
