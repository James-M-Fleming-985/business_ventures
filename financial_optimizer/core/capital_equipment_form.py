#!/usr/bin/env python3
"""
Capital Equipment Investment Form - Cost Center Focus
Phase 1 implementation focusing on accurate cost center savings calculations
"""

import dash_bootstrap_components as dbc
from dash import html, dcc, Input, Output, State, callback


def create_capital_equipment_form():
    """Create focused form for Capital Equipment investments - Cost Center model."""
    return html.Div([
        dbc.Alert([
            html.H6("Capital Equipment Investment - Cost Center Model",
                    className="alert-heading"),
            html.P(
                "Focus on cost reduction through improved OEE, reduced labor time, and energy savings."),
            html.P(
                "This calculation follows ISO 55000:2024 asset management principles.")
        ], color="info", className="mb-4"),

        # Current State (Baseline) Section
        dbc.Card([
            dbc.CardBody([
                html.H5("Current State (Baseline)", className="card-title"),
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Current OEE (%)"),
                        dbc.Input(
                            id="capital-current-oee",
                            type="number",
                            min=0, max=100, step=0.1,
                            value=65,
                            placeholder="Current Overall Equipment Effectiveness"
                        ),
                        html.Small("Typical range: 60-80%",
                                   className="text-muted")
                    ], width=6),
                    dbc.Col([
                        dbc.Label("Current Process Time (min/unit)"),
                        dbc.Input(
                            id="capital-current-process-time",
                            type="number",
                            min=0, step=0.1,
                            value=5.0,
                            placeholder="Time to process one unit"
                        ),
                        html.Small("Include setup and processing time",
                                   className="text-muted")
                    ], width=6)
                ], className="mb-3"),

                dbc.Row([
                    dbc.Col([
                        dbc.Label("Current Energy Usage (kWh/unit)"),
                        dbc.Input(
                            id="capital-current-energy",
                            type="number",
                            min=0, step=0.01,
                            value=2.5,
                            placeholder="Energy consumption per unit"
                        ),
                        html.Small("Include all equipment energy",
                                   className="text-muted")
                    ], width=6),
                    dbc.Col([
                        dbc.Label("Current Maintenance Hours/Month"),
                        dbc.Input(
                            id="capital-current-maintenance",
                            type="number",
                            min=0, step=1,
                            value=40,
                            placeholder="Monthly maintenance hours"
                        ),
                        html.Small("Include planned and unplanned",
                                   className="text-muted")
                    ], width=6)
                ], className="mb-3")
            ])
        ], className="mb-4"),

        # Target State (After Investment) Section
        dbc.Card([
            dbc.CardBody([
                html.H5("Target State (After Investment)",
                        className="card-title"),
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Target OEE (%)"),
                        dbc.Input(
                            id="capital-target-oee",
                            type="number",
                            min=0, max=100, step=0.1,
                            value=85,
                            placeholder="Target Overall Equipment Effectiveness"
                        ),
                        html.Small("World class: 85%+", className="text-muted")
                    ], width=6),
                    dbc.Col([
                        dbc.Label("Target Process Time (min/unit)"),
                        dbc.Input(
                            id="capital-target-process-time",
                            type="number",
                            min=0, step=0.1,
                            value=4.0,
                            placeholder="Improved time per unit"
                        ),
                        html.Small("Should be less than current",
                                   className="text-muted")
                    ], width=6)
                ], className="mb-3"),

                dbc.Row([
                    dbc.Col([
                        dbc.Label("Target Energy Usage (kWh/unit)"),
                        dbc.Input(
                            id="capital-target-energy",
                            type="number",
                            min=0, step=0.01,
                            value=2.0,
                            placeholder="Improved energy consumption"
                        ),
                        html.Small("10-25% improvement typical",
                                   className="text-muted")
                    ], width=6),
                    dbc.Col([
                        dbc.Label("Target Maintenance Hours/Month"),
                        dbc.Input(
                            id="capital-target-maintenance",
                            type="number",
                            min=0, step=1,
                            value=30,
                            placeholder="Reduced maintenance hours"
                        ),
                        html.Small("15-25% reduction typical",
                                   className="text-muted")
                    ], width=6)
                ], className="mb-3")
            ])
        ], className="mb-4"),

        # Operational Parameters Section
        dbc.Card([
            dbc.CardBody([
                html.H5("Operational Parameters", className="card-title"),
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Annual Volume (units)"),
                        dbc.Input(
                            id="capital-annual-volume",
                            type="number",
                            min=0, step=1000,
                            value=50000,
                            placeholder="Annual production volume"
                        ),
                        html.Small("Units processed per year",
                                   className="text-muted")
                    ], width=6),
                    dbc.Col([
                        dbc.Label("Operating Days per Year"),
                        dbc.Input(
                            id="capital-operating-days",
                            type="number",
                            min=0, max=365, step=1,
                            value=250,
                            placeholder="Annual operating days"
                        ),
                        html.Small("Typical: 250-300 days",
                                   className="text-muted")
                    ], width=6)
                ], className="mb-3"),

                dbc.Row([
                    dbc.Col([
                        dbc.Label("Labor Rate (£/hour)"),
                        dbc.Input(
                            id="capital-labor-rate",
                            type="number",
                            min=0, step=1,
                            value=25,
                            placeholder="Fully loaded labor cost"
                        ),
                        html.Small("Include overheads and benefits",
                                   className="text-muted")
                    ], width=6),
                    dbc.Col([
                        dbc.Label("Energy Cost (£/kWh)"),
                        dbc.Input(
                            id="capital-energy-cost",
                            type="number",
                            min=0, step=0.01,
                            value=0.15,
                            placeholder="Energy cost per kWh"
                        ),
                        html.Small("Check current energy rates",
                                   className="text-muted")
                    ], width=6)
                ], className="mb-3"),

                dbc.Row([
                    dbc.Col([
                        dbc.Label("Maintenance Cost (£/hour)"),
                        dbc.Input(
                            id="capital-maintenance-cost",
                            type="number",
                            min=0, step=5,
                            value=75,
                            placeholder="Maintenance labor + parts cost"
                        ),
                        html.Small("Include labor and parts",
                                   className="text-muted")
                    ], width=6),
                    dbc.Col([
                        dbc.Label("Quality Cost per Defect (£)"),
                        dbc.Input(
                            id="capital-quality-cost",
                            type="number",
                            min=0, step=1,
                            value=15,
                            placeholder="Cost per quality defect"
                        ),
                        html.Small("Rework + scrap + handling",
                                   className="text-muted")
                    ], width=6)
                ], className="mb-3")
            ])
        ], className="mb-4"),

        # Real-time calculation display
        dbc.Card([
            dbc.CardBody([
                html.H5("Calculated Annual Savings",
                        className="card-title text-success"),
                html.Div(id="capital-savings-breakdown", className="mb-3"),
                html.Hr(),
                html.Div([
                    html.H4(id="capital-total-savings",
                            className="text-success"),
                    html.P("Total Annual Cost Reduction",
                           className="text-muted")
                ])
            ])
        ], color="success", outline=True)
    ])

# Callback for real-time Capital Equipment savings calculation


@callback(
    [Output("capital-savings-breakdown", "children"),
     Output("capital-total-savings", "children")],
    [Input("capital-current-oee", "value"),
     Input("capital-target-oee", "value"),
     Input("capital-current-process-time", "value"),
     Input("capital-target-process-time", "value"),
     Input("capital-current-energy", "value"),
     Input("capital-target-energy", "value"),
     Input("capital-current-maintenance", "value"),
     Input("capital-target-maintenance", "value"),
     Input("capital-annual-volume", "value"),
     Input("capital-operating-days", "value"),
     Input("capital-labor-rate", "value"),
     Input("capital-energy-cost", "value"),
     Input("capital-maintenance-cost", "value"),
     Input("capital-quality-cost", "value")]
)
def calculate_capital_equipment_savings(
    current_oee, target_oee, current_process_time, target_process_time,
    current_energy, target_energy, current_maintenance, target_maintenance,
    annual_volume, operating_days, labor_rate, energy_cost,
    maintenance_cost, quality_cost
):
    """Calculate Capital Equipment savings using Cost Center methodology."""

    # Handle None values
    inputs = [current_oee, target_oee, current_process_time, target_process_time,
              current_energy, target_energy, current_maintenance, target_maintenance,
              annual_volume, operating_days, labor_rate, energy_cost,
              maintenance_cost, quality_cost]

    if any(x is None for x in inputs):
        return html.P("Enter all values to see calculation", className="text-muted"), "£0"

    # Labor savings from process time reduction
    process_time_savings = (current_process_time -
                            target_process_time) / 60  # Convert to hours
    labor_savings = process_time_savings * labor_rate * annual_volume

    # Energy savings
    energy_reduction = current_energy - target_energy
    energy_savings = energy_reduction * energy_cost * annual_volume

    # Maintenance savings
    maintenance_reduction = (current_maintenance -
                             target_maintenance) * 12  # Annual
    maintenance_savings = maintenance_reduction * maintenance_cost

    # OEE improvement benefits (additional throughput capacity)
    oee_improvement = (target_oee - current_oee) / 100
    # Assume 8 hours/day operation
    oee_labor_savings = oee_improvement * labor_rate * 8 * operating_days

    # Quality improvement (assume 2% defect rate improvement with OEE increase)
    quality_improvement = oee_improvement * 0.02  # 2% improvement
    quality_savings = quality_improvement * annual_volume * quality_cost

    # Total savings
    total_savings = labor_savings + energy_savings + \
        maintenance_savings + oee_labor_savings + quality_savings

    # Create breakdown display
    breakdown = [
        html.H6("Savings Breakdown:", className="mb-3"),
        html.Div([
            html.P([html.Strong("Labor Savings: "), f"£{labor_savings:,.0f}"]),
            html.P([html.Strong("Energy Savings: "),
                   f"£{energy_savings:,.0f}"]),
            html.P([html.Strong("Maintenance Savings: "),
                   f"£{maintenance_savings:,.0f}"]),
            html.P([html.Strong("OEE Improvement: "),
                   f"£{oee_labor_savings:,.0f}"]),
            html.P([html.Strong("Quality Improvement: "),
                   f"£{quality_savings:,.0f}"])
        ])
    ]

    return breakdown, f"£{total_savings:,.0f}"
