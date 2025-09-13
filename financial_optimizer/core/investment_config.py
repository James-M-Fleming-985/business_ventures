#!/usr/bin/env python3
"""
Investment Type Configuration
Defines the dynamic form fields for each investment type and business model combination.
"""

# Investment type configurations
INVESTMENT_CONFIGS = {
    "capital": {
        "label": "Capital Equipment & Assets",
        "cost_center": {
            "description": "Cost reduction through improved efficiency and reduced operational costs",
            "fields": [
                {"id": "current_oee", "label": "Current OEE (%)", "type": "number", "min": 0, "max": 100,
                 "step": 0.1, "value": 65, "help": "Current Overall Equipment Effectiveness"},
                {"id": "target_oee", "label": "Target OEE (%)", "type": "number", "min": 0,
                 "max": 100, "step": 0.1, "value": 85, "help": "Target OEE after investment"},
                {"id": "process_time_current", "label": "Current Process Time (min/unit)", "type": "number",
                 "min": 0, "step": 0.1, "value": 5.0, "help": "Current time per unit processed"},
                {"id": "process_time_improved", "label": "Improved Process Time (min/unit)", "type": "number",
                 "min": 0, "step": 0.1, "value": 4.0, "help": "Expected time per unit after improvement"},
                {"id": "labor_rate", "label": "Labor Rate (£/hour)", "type": "number", "min": 0,
                 "step": 1, "value": 25, "help": "Fully loaded labor cost per hour"},
                {"id": "energy_current", "label": "Current Energy (kWh/unit)", "type": "number",
                 "min": 0, "step": 0.01, "value": 2.5, "help": "Current energy consumption per unit"},
                {"id": "energy_improved", "label": "Improved Energy (kWh/unit)", "type": "number",
                 "min": 0, "step": 0.01, "value": 2.0, "help": "Expected energy consumption per unit"},
                {"id": "energy_cost", "label": "Energy Cost (£/kWh)", "type": "number", "min": 0,
                 "step": 0.01, "value": 0.15, "help": "Energy cost per kilowatt hour"},
                {"id": "annual_volume", "label": "Annual Volume (units)", "type": "number",
                 "min": 0, "step": 1000, "value": 50000, "help": "Annual production volume"},
                {"id": "operating_days", "label": "Operating Days/Year", "type": "number",
                    "min": 0, "max": 365, "step": 1, "value": 250, "help": "Annual operating days"}
            ],
            "calculation_formula": "labor_savings + energy_savings + maintenance_savings + quality_savings"
        },
        "profit_center": {
            "description": "Revenue generation through increased capacity and market opportunity",
            "fields": [
                {"id": "current_oee", "label": "Current OEE (%)", "type": "number", "min": 0, "max": 100,
                 "step": 0.1, "value": 65, "help": "Current Overall Equipment Effectiveness"},
                {"id": "target_oee", "label": "Target OEE (%)", "type": "number", "min": 0,
                 "max": 100, "step": 0.1, "value": 85, "help": "Target OEE after investment"},
                {"id": "production_rate", "label": "Production Rate (units/hour)", "type": "number",
                 "min": 0, "step": 1, "value": 100, "help": "Maximum production rate per hour"},
                {"id": "unit_margin", "label": "Unit Margin (£/unit)", "type": "number", "min": 0,
                 "step": 0.01, "value": 15.50, "help": "Contribution margin per unit"},
                {"id": "market_demand", "label": "Market Demand (units/year)", "type": "number",
                 "min": 0, "step": 1000, "value": 75000, "help": "Annual market demand available"},
                {"id": "operating_hours", "label": "Operating Hours/Year", "type": "number",
                    "min": 0, "step": 100, "value": 2000, "help": "Annual operating hours"},
                {"id": "competitive_advantage", "label": "Competitive Advantage Factor", "type": "number",
                    "min": 0, "max": 1, "step": 0.1, "value": 0.8, "help": "Market capture probability (0-1)"}
            ],
            "calculation_formula": "additional_revenue + cost_reduction + market_share_value"
        }
    },

    "process": {
        "label": "Process Improvement & Optimization",
        "cost_center": {
            "description": "Cost reduction through cycle time reduction and waste elimination",
            "fields": [
                {"id": "current_cycle_time", "label": "Current Cycle Time (min)", "type": "number",
                 "min": 0, "step": 0.1, "value": 8.0, "help": "Current process cycle time"},
                {"id": "improved_cycle_time", "label": "Improved Cycle Time (min)", "type": "number",
                 "min": 0, "step": 0.1, "value": 6.0, "help": "Expected cycle time after improvement"},
                {"id": "current_waste_rate", "label": "Current Waste Rate (%)", "type": "number",
                 "min": 0, "max": 100, "step": 0.1, "value": 5.0, "help": "Current waste percentage"},
                {"id": "improved_waste_rate", "label": "Improved Waste Rate (%)", "type": "number",
                 "min": 0, "max": 100, "step": 0.1, "value": 2.0, "help": "Expected waste percentage"},
                {"id": "current_defect_rate", "label": "Current Defect Rate (%)", "type": "number",
                 "min": 0, "max": 100, "step": 0.1, "value": 3.0, "help": "Current defect rate"},
                {"id": "improved_defect_rate", "label": "Improved Defect Rate (%)", "type": "number",
                 "min": 0, "max": 100, "step": 0.1, "value": 1.0, "help": "Expected defect rate"},
                {"id": "labor_rate", "label": "Labor Rate (£/hour)", "type": "number", "min": 0,
                 "step": 1, "value": 25, "help": "Fully loaded labor cost per hour"},
                {"id": "waste_cost", "label": "Waste Cost (£/unit)", "type": "number",
                 "min": 0, "step": 0.01, "value": 2.50, "help": "Cost per unit of waste"},
                {"id": "rework_cost", "label": "Rework Cost (£/unit)", "type": "number",
                 "min": 0, "step": 0.01, "value": 8.00, "help": "Cost per unit of rework"},
                {"id": "annual_volume", "label": "Annual Volume (units)", "type": "number",
                 "min": 0, "step": 1000, "value": 50000, "help": "Annual production volume"}
            ],
            "calculation_formula": "cycle_time_savings + waste_elimination + quality_improvement"
        },
        "profit_center": {
            "description": "Revenue generation through improved throughput and customer satisfaction",
            "fields": [
                {"id": "current_throughput", "label": "Current Throughput (units/hour)", "type": "number",
                 "min": 0, "step": 1, "value": 100, "help": "Current throughput rate"},
                {"id": "improved_throughput", "label": "Improved Throughput (units/hour)", "type": "number",
                 "min": 0, "step": 1, "value": 130, "help": "Expected throughput after improvement"},
                {"id": "unit_margin", "label": "Unit Margin (£/unit)", "type": "number", "min": 0,
                 "step": 0.01, "value": 15.50, "help": "Contribution margin per unit"},
                {"id": "customer_satisfaction_current",
                    "label": "Current Customer Satisfaction (%)", "type": "number", "min": 0, "max": 100, "step": 1, "value": 85, "help": "Current customer satisfaction score"},
                {"id": "customer_satisfaction_improved",
                    "label": "Improved Customer Satisfaction (%)", "type": "number", "min": 0, "max": 100, "step": 1, "value": 95, "help": "Expected customer satisfaction"},
                {"id": "customer_lifetime_value",
                    "label": "Customer Lifetime Value (£)", "type": "number", "min": 0, "step": 100, "value": 25000, "help": "Average customer lifetime value"},
                {"id": "retention_rate", "label": "Retention Rate (%)", "type": "number", "min": 0,
                 "max": 100, "step": 1, "value": 90, "help": "Customer retention rate"}
            ],
            "calculation_formula": "throughput_revenue + cost_reduction + customer_value"
        }
    },

    "people": {
        "label": "Human Capital & Training",
        "cost_center": {
            "description": "Cost reduction through productivity improvement and error reduction",
            "fields": [
                {"id": "current_productivity", "label": "Current Productivity (units/hour)", "type": "number",
                 "min": 0, "step": 1, "value": 25, "help": "Current productivity per person"},
                {"id": "improved_productivity", "label": "Improved Productivity (units/hour)", "type": "number",
                 "min": 0, "step": 1, "value": 30, "help": "Expected productivity after training"},
                {"id": "training_hours", "label": "Training Hours per Employee", "type": "number",
                    "min": 0, "step": 1, "value": 40, "help": "Total training hours per employee"},
                {"id": "employee_count", "label": "Number of Employees", "type": "number",
                    "min": 1, "step": 1, "value": 8, "help": "Number of employees to be trained"},
                {"id": "labor_rate", "label": "Labor Rate (£/hour)", "type": "number", "min": 0,
                 "step": 1, "value": 25, "help": "Fully loaded labor cost per hour"},
                {"id": "current_error_rate", "label": "Current Error Rate (%)", "type": "number",
                 "min": 0, "max": 100, "step": 0.1, "value": 3.5, "help": "Current error rate"},
                {"id": "improved_error_rate", "label": "Improved Error Rate (%)", "type": "number", "min": 0,
                 "max": 100, "step": 0.1, "value": 1.5, "help": "Expected error rate after training"},
                {"id": "error_cost", "label": "Error Cost (£/error)", "type": "number",
                 "min": 0, "step": 1, "value": 50, "help": "Average cost per error"},
                {"id": "cross_training_benefit", "label": "Cross-Training Benefit (£/employee)", "type": "number",
                 "min": 0, "step": 100, "value": 2000, "help": "Annual benefit from cross-training"}
            ],
            "calculation_formula": "productivity_improvement + error_reduction + versatility_value"
        },
        "profit_center": {
            "description": "Revenue generation through productivity and innovation",
            "fields": [
                {"id": "current_productivity", "label": "Current Productivity (units/hour)", "type": "number",
                 "min": 0, "step": 1, "value": 25, "help": "Current productivity per person"},
                {"id": "improved_productivity", "label": "Improved Productivity (units/hour)", "type": "number",
                 "min": 0, "step": 1, "value": 30, "help": "Expected productivity after training"},
                {"id": "unit_margin", "label": "Unit Margin (£/unit)", "type": "number", "min": 0,
                 "step": 0.01, "value": 15.50, "help": "Contribution margin per unit"},
                {"id": "innovation_rate", "label": "Innovation Rate (suggestions/employee/year)", "type": "number",
                 "min": 0, "step": 1, "value": 5, "help": "Innovation suggestions per employee per year"},
                {"id": "innovation_value", "label": "Average Innovation Value (£/suggestion)", "type": "number",
                 "min": 0, "step": 100, "value": 2500, "help": "Average value per innovation"},
                {"id": "turnover_reduction", "label": "Turnover Reduction (%)", "type": "number", "min": 0,
                 "max": 100, "step": 1, "value": 25, "help": "Reduction in employee turnover"},
                {"id": "recruitment_cost", "label": "Recruitment Cost (£/employee)", "type": "number",
                 "min": 0, "step": 100, "value": 8000, "help": "Cost to recruit and train new employee"}
            ],
            "calculation_formula": "productivity_revenue + innovation_value + retention_savings"
        }
    },

    "maintenance": {
        "label": "Maintenance & Asset Reliability",
        "cost_center": {
            "description": "Cost reduction through predictive maintenance and downtime reduction",
            "fields": [
                {"id": "current_mtbf", "label": "Current MTBF (hours)", "type": "number",
                 "min": 0, "step": 10, "value": 200, "help": "Mean Time Between Failures"},
                {"id": "improved_mtbf", "label": "Improved MTBF (hours)", "type": "number",
                 "min": 0, "step": 10, "value": 350, "help": "Expected MTBF after improvement"},
                {"id": "current_mttr", "label": "Current MTTR (hours)", "type": "number",
                 "min": 0, "step": 0.5, "value": 4.0, "help": "Mean Time To Repair"},
                {"id": "improved_mttr", "label": "Improved MTTR (hours)", "type": "number",
                 "min": 0, "step": 0.5, "value": 2.0, "help": "Expected MTTR after improvement"},
                {"id": "maintenance_cost_hour",
                    "label": "Maintenance Cost (£/hour)", "type": "number", "min": 0, "step": 5, "value": 75, "help": "Cost per maintenance hour"},
                {"id": "lost_production_cost", "label": "Lost Production Cost (£/hour)", "type": "number",
                 "min": 0, "step": 10, "value": 500, "help": "Cost of lost production per hour"},
                {"id": "operating_hours", "label": "Operating Hours/Year", "type": "number",
                    "min": 0, "step": 100, "value": 2000, "help": "Annual operating hours"},
                {"id": "emergency_premium", "label": "Emergency Maintenance Premium (%)", "type": "number", "min": 0,
                 "max": 500, "step": 10, "value": 150, "help": "Additional cost for emergency maintenance"}
            ],
            "calculation_formula": "reduced_maintenance_costs + downtime_reduction + parts_inventory_optimization"
        },
        "profit_center": {
            "description": "Revenue protection through reliability and quality consistency",
            "fields": [
                {"id": "current_oee", "label": "Current OEE (%)", "type": "number", "min": 0, "max": 100,
                 "step": 0.1, "value": 65, "help": "Current Overall Equipment Effectiveness"},
                {"id": "improved_oee", "label": "Improved OEE (%)", "type": "number", "min": 0, "max": 100,
                 "step": 0.1, "value": 85, "help": "Expected OEE with improved maintenance"},
                {"id": "production_rate", "label": "Production Rate (units/hour)", "type": "number",
                 "min": 0, "step": 1, "value": 100, "help": "Maximum production rate per hour"},
                {"id": "unit_margin", "label": "Unit Margin (£/unit)", "type": "number", "min": 0,
                 "step": 0.01, "value": 15.50, "help": "Contribution margin per unit"},
                {"id": "quality_consistency", "label": "Quality Consistency Improvement (%)", "type": "number",
                 "min": 0, "max": 100, "step": 1, "value": 15, "help": "Improvement in quality consistency"},
                {"id": "customer_delivery_impact",
                    "label": "Customer Delivery Impact (£/incident)", "type": "number", "min": 0, "step": 100, "value": 5000, "help": "Cost per delivery failure"},
                {"id": "incidents_per_year", "label": "Current Incidents/Year", "type": "number",
                    "min": 0, "step": 1, "value": 12, "help": "Current delivery incidents per year"}
            ],
            "calculation_formula": "avoided_lost_production + emergency_maintenance_savings + quality_improvements"
        }
    },

    "quality": {
        "label": "Quality Systems & Compliance",
        "cost_center": {
            "description": "Cost reduction through improved quality and compliance efficiency",
            "fields": [
                {"id": "current_fpy", "label": "Current First Pass Yield (%)", "type": "number", "min": 0,
                 "max": 100, "step": 0.1, "value": 92.0, "help": "Current first pass yield"},
                {"id": "improved_fpy", "label": "Improved First Pass Yield (%)", "type": "number",
                 "min": 0, "max": 100, "step": 0.1, "value": 97.0, "help": "Expected first pass yield"},
                {"id": "inspection_time", "label": "Inspection Time (min/unit)", "type": "number",
                 "min": 0, "step": 0.1, "value": 2.0, "help": "Time spent on inspection per unit"},
                {"id": "inspection_reduction", "label": "Inspection Time Reduction (%)", "type": "number",
                 "min": 0, "max": 100, "step": 1, "value": 30, "help": "Reduction in inspection time"},
                {"id": "rework_cost", "label": "Rework Cost (£/unit)", "type": "number",
                 "min": 0, "step": 0.01, "value": 8.00, "help": "Cost per unit of rework"},
                {"id": "scrap_cost", "label": "Scrap Cost (£/unit)", "type": "number",
                 "min": 0, "step": 0.01, "value": 15.00, "help": "Cost per unit of scrap"},
                {"id": "labor_rate", "label": "Labor Rate (£/hour)", "type": "number", "min": 0,
                 "step": 1, "value": 25, "help": "Fully loaded labor cost per hour"},
                {"id": "annual_volume", "label": "Annual Volume (units)", "type": "number",
                 "min": 0, "step": 1000, "value": 50000, "help": "Annual production volume"}
            ],
            "calculation_formula": "reduced_inspection_costs + rework_reduction + waste_reduction + compliance_efficiency"
        },
        "profit_center": {
            "description": "Revenue generation through premium pricing and market access",
            "fields": [
                {"id": "current_fpy", "label": "Current First Pass Yield (%)", "type": "number", "min": 0,
                 "max": 100, "step": 0.1, "value": 92.0, "help": "Current first pass yield"},
                {"id": "improved_fpy", "label": "Improved First Pass Yield (%)", "type": "number",
                 "min": 0, "max": 100, "step": 0.1, "value": 97.0, "help": "Expected first pass yield"},
                {"id": "quality_premium", "label": "Quality Premium (%)", "type": "number", "min": 0,
                 "max": 100, "step": 1, "value": 8, "help": "Premium pricing for quality"},
                {"id": "customer_retention", "label": "Customer Retention Improvement (%)", "type": "number",
                 "min": 0, "max": 100, "step": 1, "value": 15, "help": "Improvement in customer retention"},
                {"id": "customer_lifetime_value",
                    "label": "Customer Lifetime Value (£)", "type": "number", "min": 0, "step": 100, "value": 25000, "help": "Average customer lifetime value"},
                {"id": "market_access", "label": "New Market Access (£/year)", "type": "number", "min": 0,
                 "step": 1000, "value": 50000, "help": "New market revenue from certifications"},
                {"id": "avoided_recalls", "label": "Avoided Recall Cost (£/year)", "type": "number", "min": 0,
                 "step": 1000, "value": 25000, "help": "Cost avoided through quality improvements"}
            ],
            "calculation_formula": "premium_pricing + customer_retention + market_access + avoided_costs"
        }
    }
}

# Additional investment types can be added here...
# "digital": {...},
# "safety": {...},
# "facility": {...},
# "supply_chain": {...}
