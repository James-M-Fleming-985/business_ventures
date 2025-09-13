#!/usr/bin/env python3
"""
Investment Calculation Engine
Calculates savings for different investment types and business models.
"""

def calculate_capital_equipment_cost_center(data):
    """Calculate savings for capital equipment in cost center model."""
    # Labor savings from process time reduction
    time_savings = (data.get('process_time_current', 0) - 
                   data.get('process_time_improved', 0)) / 60  # Convert to hours
    labor_savings = (time_savings * data.get('labor_rate', 0) * 
                    data.get('annual_volume', 0))
    
    # Energy savings
    energy_reduction = (data.get('energy_current', 0) - 
                       data.get('energy_improved', 0))
    energy_savings = (energy_reduction * data.get('energy_cost', 0) * 
                     data.get('annual_volume', 0))
    
    # OEE improvement impact on labor efficiency
    oee_improvement = ((data.get('target_oee', 0) - data.get('current_oee', 0)) / 100)
    oee_savings = (oee_improvement * data.get('labor_rate', 0) * 
                  data.get('operating_days', 0) * 8)  # 8 hours/day
    
    total_savings = labor_savings + energy_savings + oee_savings
    return max(0, total_savings)

def calculate_capital_equipment_profit_center(data):
    """Calculate savings for capital equipment in profit center model."""
    # Additional capacity from OEE improvement
    oee_improvement = ((data.get('target_oee', 0) - data.get('current_oee', 0)) / 100)
    additional_capacity = (oee_improvement * data.get('production_rate', 0) * 
                          data.get('operating_hours', 0))
    
    # Market demand constraint
    market_demand = data.get('market_demand', 0)
    realizable_capacity = min(additional_capacity, market_demand)
    
    # Revenue from additional capacity
    competitive_factor = data.get('competitive_advantage', 1.0)
    additional_revenue = (realizable_capacity * data.get('unit_margin', 0) * 
                         competitive_factor)
    
    return max(0, additional_revenue)

def calculate_process_improvement_cost_center(data):
    """Calculate savings for process improvement in cost center model."""
    # Cycle time reduction savings
    time_savings = (data.get('current_cycle_time', 0) - 
                   data.get('improved_cycle_time', 0)) / 60  # Convert to hours
    cycle_time_savings = (time_savings * data.get('labor_rate', 0) * 
                         data.get('annual_volume', 0))
    
    # Waste elimination savings
    waste_reduction = ((data.get('current_waste_rate', 0) - 
                       data.get('improved_waste_rate', 0)) / 100)
    waste_savings = (waste_reduction * data.get('waste_cost', 0) * 
                    data.get('annual_volume', 0))
    
    # Quality improvement savings
    defect_reduction = ((data.get('current_defect_rate', 0) - 
                        data.get('improved_defect_rate', 0)) / 100)
    quality_savings = (defect_reduction * data.get('rework_cost', 0) * 
                      data.get('annual_volume', 0))
    
    total_savings = cycle_time_savings + waste_savings + quality_savings
    return max(0, total_savings)

def calculate_process_improvement_profit_center(data):
    """Calculate savings for process improvement in profit center model."""
    # Additional throughput revenue
    throughput_increase = (data.get('improved_throughput', 0) - 
                          data.get('current_throughput', 0))
    # Assume 2000 operating hours per year
    additional_revenue = (throughput_increase * 2000 * data.get('unit_margin', 0))
    
    # Customer satisfaction impact
    satisfaction_improvement = ((data.get('customer_satisfaction_improved', 0) - 
                               data.get('customer_satisfaction_current', 0)) / 100)
    retention_improvement = satisfaction_improvement * 0.5  # 50% correlation
    customer_value = (retention_improvement * data.get('customer_lifetime_value', 0) * 
                     data.get('retention_rate', 0) / 100)
    
    total_savings = additional_revenue + customer_value
    return max(0, total_savings)

def calculate_human_capital_cost_center(data):
    """Calculate savings for human capital in cost center model."""
    # Productivity improvement
    productivity_increase = (data.get('improved_productivity', 0) - 
                           data.get('current_productivity', 0))
    # Assume 2000 working hours per year
    productivity_savings = (productivity_increase * 2000 * data.get('labor_rate', 0) * 
                           data.get('employee_count', 0))
    
    # Error reduction savings
    error_reduction = ((data.get('current_error_rate', 0) - 
                       data.get('improved_error_rate', 0)) / 100)
    # Assume each employee generates 1000 opportunities for errors per year
    error_savings = (error_reduction * 1000 * data.get('error_cost', 0) * 
                    data.get('employee_count', 0))
    
    # Cross-training benefits
    cross_training_value = (data.get('cross_training_benefit', 0) * 
                           data.get('employee_count', 0))
    
    total_savings = productivity_savings + error_savings + cross_training_value
    return max(0, total_savings)

def calculate_human_capital_profit_center(data):
    """Calculate savings for human capital in profit center model."""
    # Productivity revenue
    productivity_increase = (data.get('improved_productivity', 0) - 
                           data.get('current_productivity', 0))
    # Assume 2000 working hours per year
    productivity_revenue = (productivity_increase * 2000 * data.get('unit_margin', 0) * 
                           data.get('employee_count', 0))
    
    # Innovation value
    innovation_value = (data.get('innovation_rate', 0) * 
                       data.get('innovation_value', 0) * 
                       data.get('employee_count', 0))
    
    # Retention savings
    turnover_reduction = data.get('turnover_reduction', 0) / 100
    retention_savings = (turnover_reduction * data.get('recruitment_cost', 0) * 
                        data.get('employee_count', 0))
    
    total_savings = productivity_revenue + innovation_value + retention_savings
    return max(0, total_savings)

def calculate_maintenance_cost_center(data):
    """Calculate savings for maintenance in cost center model."""
    # MTBF improvement reduces maintenance frequency
    current_failures = data.get('operating_hours', 0) / data.get('current_mtbf', 1)
    improved_failures = data.get('operating_hours', 0) / data.get('improved_mtbf', 1)
    failure_reduction = current_failures - improved_failures
    
    # Maintenance cost savings
    maintenance_savings = (failure_reduction * data.get('current_mttr', 0) * 
                          data.get('maintenance_cost_hour', 0))
    
    # Downtime reduction savings
    downtime_reduction = failure_reduction * (data.get('current_mttr', 0) - 
                                             data.get('improved_mttr', 0))
    downtime_savings = (downtime_reduction * data.get('lost_production_cost', 0))
    
    # Emergency maintenance premium reduction
    emergency_savings = (failure_reduction * data.get('maintenance_cost_hour', 0) * 
                        data.get('emergency_premium', 0) / 100)
    
    total_savings = maintenance_savings + downtime_savings + emergency_savings
    return max(0, total_savings)

def calculate_maintenance_profit_center(data):
    """Calculate savings for maintenance in profit center model."""
    # OEE improvement from better maintenance
    oee_improvement = ((data.get('improved_oee', 0) - data.get('current_oee', 0)) / 100)
    
    # Additional production capacity
    additional_capacity = (oee_improvement * data.get('production_rate', 0) * 
                          data.get('operating_hours', 0))
    
    # Revenue from additional capacity
    additional_revenue = additional_capacity * data.get('unit_margin', 0)
    
    # Quality consistency improvement
    quality_improvement = data.get('quality_consistency', 0) / 100
    quality_value = (quality_improvement * data.get('unit_margin', 0) * 
                    data.get('production_rate', 0) * data.get('operating_hours', 0))
    
    # Avoided customer delivery incidents
    incident_reduction = data.get('incidents_per_year', 0) * 0.5  # 50% reduction
    incident_savings = (incident_reduction * data.get('customer_delivery_impact', 0))
    
    total_savings = additional_revenue + quality_value + incident_savings
    return max(0, total_savings)

def calculate_quality_cost_center(data):
    """Calculate savings for quality in cost center model."""
    # First pass yield improvement
    fpy_improvement = ((data.get('improved_fpy', 0) - data.get('current_fpy', 0)) / 100)
    
    # Reduced rework costs
    rework_reduction = (fpy_improvement * data.get('annual_volume', 0) * 
                       data.get('rework_cost', 0))
    
    # Reduced scrap costs
    scrap_reduction = (fpy_improvement * data.get('annual_volume', 0) * 
                      data.get('scrap_cost', 0))
    
    # Inspection time reduction
    inspection_reduction = data.get('inspection_reduction', 0) / 100
    inspection_savings = (inspection_reduction * data.get('inspection_time', 0) / 60 * 
                         data.get('labor_rate', 0) * data.get('annual_volume', 0))
    
    total_savings = rework_reduction + scrap_reduction + inspection_savings
    return max(0, total_savings)

def calculate_quality_profit_center(data):
    """Calculate savings for quality in profit center model."""
    # Premium pricing from quality improvement
    fpy_improvement = ((data.get('improved_fpy', 0) - data.get('current_fpy', 0)) / 100)
    quality_premium = (fpy_improvement * data.get('quality_premium', 0) / 100 * 
                      data.get('annual_volume', 0) * data.get('unit_margin', 0))
    
    # Customer retention improvement
    retention_improvement = data.get('customer_retention', 0) / 100
    retention_value = (retention_improvement * data.get('customer_lifetime_value', 0))
    
    # New market access
    market_access = data.get('market_access', 0)
    
    # Avoided recall costs
    avoided_costs = data.get('avoided_recalls', 0)
    
    total_savings = quality_premium + retention_value + market_access + avoided_costs
    return max(0, total_savings)

# Main calculation dispatcher
CALCULATION_FUNCTIONS = {
    'capital': {
        'cost_center': calculate_capital_equipment_cost_center,
        'profit_center': calculate_capital_equipment_profit_center
    },
    'process': {
        'cost_center': calculate_process_improvement_cost_center,
        'profit_center': calculate_process_improvement_profit_center
    },
    'people': {
        'cost_center': calculate_human_capital_cost_center,
        'profit_center': calculate_human_capital_profit_center
    },
    'maintenance': {
        'cost_center': calculate_maintenance_cost_center,
        'profit_center': calculate_maintenance_profit_center
    },
    'quality': {
        'cost_center': calculate_quality_cost_center,
        'profit_center': calculate_quality_profit_center
    }
}

def calculate_investment_savings(investment_type, business_model, data):
    """
    Calculate savings for a specific investment type and business model.
    
    Args:
        investment_type: str - The type of investment (e.g., 'capital', 'process')
        business_model: str - The business model ('cost_center' or 'profit_center')
        data: dict - The input data for calculations
    
    Returns:
        float - The calculated annual savings
    """
    if investment_type in CALCULATION_FUNCTIONS:
        if business_model in CALCULATION_FUNCTIONS[investment_type]:
            calculation_func = CALCULATION_FUNCTIONS[investment_type][business_model]
            return calculation_func(data)
    
    # Default fallback calculation if specific function not found
    return 0.0
