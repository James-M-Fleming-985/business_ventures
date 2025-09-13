#!/usr/bin/env python3
"""
Financial Dashboard Callbacks - Real-time Control Panel Integration

Implements the comprehensive callback system connecting:
1. Control Panel Sliders (16 inputs) → Financial Chart Updates 
2. Data Input Modal (27 fields) → Chart & Control Panel Updates
3. Time Range Controls → Chart Time Scaling
4. Current vs Projected Real-time Displays

Based on Personal Mode Implementation Roadmap - Phase 2.5 Requirements
"""

from dash import callback, Input, Output, State, no_update, callback_context
import plotly.graph_objects as go
from typing import Dict, List, Tuple, Any
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Import professional financial calculation utilities
from ..logic.financial_calculations import (
    calculate_uk_net_income,
    calculate_financial_projections,
    calculate_compound_interest,
    calculate_debt_amortization,
    calculate_weighted_investment_return,
    validate_financial_inputs
)


class FinancialDashboardCallbacks:
    """
    Comprehensive callback management for Financial Dashboard
    
    Handles real-time updates between:
    - Control panel sliders and financial chart
    - Data input modal and dashboard displays  
    - Time range controls and projection scaling
    - Current vs projected value comparisons
    """
    
    def __init__(self, app=None):
        self.app = app
        self.register_all_callbacks()
    
    def register_all_callbacks(self):
        """Register all dashboard callbacks with organized groups"""
        self.register_control_panel_callbacks()
        self.register_data_input_callbacks()
        self.register_time_range_callbacks()
        self.register_impact_display_callbacks()
    
    def register_control_panel_callbacks(self):
        """
        Real-time chart updates from 16 control panel sliders
        
        Slider Groups:
        - Income: monthly amount + annual growth %
        - Housing: monthly payment + interest rate change %  
        - Utilities: monthly cost + inflation %
        - Transport: monthly cost + annual change %
        - Food: monthly budget + food inflation %
        - Savings: monthly amount + savings rate %
        - Investments: monthly amount + expected return %
        - Time Range: chart time range slider
        - Investment Type: simple vs compound toggle
        """
        
        @self.app.callback(
            [
                Output('enhanced-financial-projection-chart', 'figure'),
                Output('current-net-worth-summary', 'children'),
                Output('current-cashflow-summary-main', 'children'),
                Output('current-assets-summary', 'children'),
                Output('current-liabilities-summary', 'children')
            ],
            [
                # Income Controls (2 inputs)
                Input('income-slider', 'value'),
                Input('income-growth-slider', 'value'),
                
                # Housing Controls (2 inputs)  
                Input('mortgage-slider', 'value'),
                Input('mortgage-rate-slider', 'value'),
                
                # Utilities Controls (2 inputs)
                Input('utilities-slider', 'value'),
                Input('utilities-inflation-slider', 'value'),
                
                # Transport Controls (2 inputs)
                Input('transport-slider', 'value'),
                Input('transport-inflation-slider', 'value'),
                
                # Food Controls (2 inputs)
                Input('food-slider', 'value'),
                Input('food-inflation-slider', 'value'),
                
                # Savings Controls (2 inputs)
                Input('total-savings-slider', 'value'),
                Input('savings-rate-slider', 'value'),
                
                # Investment Controls (2 inputs)
                Input('total-investments-slider', 'value'),
                Input('investment-return-slider', 'value'),
                
                # Time Range & Type (2 inputs)
                Input('chart-time-range-slider', 'value'),
                Input('investment-type-selector', 'value')
            ],
            [
                # Data Input State for baseline values
                State('financial-data-store', 'data')
            ]
        )
        def update_financial_chart_from_control_panel(
            # Income inputs
            income_monthly, income_growth,
            # Housing inputs  
            housing_monthly, housing_rate_change,
            # Utilities inputs
            utilities_monthly, utilities_inflation,
            # Transport inputs
            transport_monthly, transport_change,
            # Food inputs
            food_monthly, food_inflation,
            # Savings inputs
            savings_monthly, savings_rate,
            # Investment inputs
            investments_monthly, investment_return,
            # Time & type inputs
            time_range_months, investment_type,
            # Current user data state
            financial_data
        ):
            """
            Real-time financial chart updates from control panel sliders
            
            Performance Target: <100ms update time per roadmap requirements
            """
            
            # DEBUG: Print callback trigger
            print(f"🔧 DEBUG: Chart callback triggered!")
            print(f"   Income: £{income_monthly}, Housing: £{housing_monthly}")
            print(f"   Time Range: {time_range_months} months")
            
            # Prepare financial inputs from control panel values
            control_panel_inputs = {
                'monthly_income': income_monthly,
                'income_growth': income_growth / 100,  # Convert % to decimal
                'monthly_housing': housing_monthly,
                'housing_rate_change': housing_rate_change / 100,
                'monthly_utilities': utilities_monthly,
                'utilities_inflation': utilities_inflation / 100,
                'monthly_transport': transport_monthly,
                'transport_inflation': transport_change / 100,
                'monthly_food': food_monthly,
                'food_inflation': food_inflation / 100,
                'monthly_savings': savings_monthly,
                'savings_rate': savings_rate / 100,
                'monthly_investments': investments_monthly,
                'investment_return': investment_return / 100,
                'time_range_months': time_range_months,
                'investment_type': investment_type
            }
            
            # Add baseline user data if available
            baseline_data = financial_data or {}
            
            # Validate inputs before processing
            validated_inputs = validate_financial_inputs(control_panel_inputs)
            
            # Calculate enhanced financial projections
            projections = calculate_financial_projections(
                validated_inputs, 
                baseline_data,
                time_range_months
            )
            
            print(f"🔧 DEBUG: Projections calculated - Net worth range: £{projections['net_worth'][0]:,.0f} to £{projections['net_worth'][-1]:,.0f}")
            
            # Create interactive chart with 4 traces
            chart_figure = self.create_enhanced_financial_chart(
                projections, 
                time_range_months
            )
            
            print(f"🔧 DEBUG: Chart figure created with {len(chart_figure.data)} traces")
            
            # Calculate current summary values
            current_net_worth = f"£{projections['net_worth'][-1]:,.0f}"
            current_cashflow = f"£{projections['monthly_cash_flow'][-1]:,.0f}"
            current_assets = f"£{projections['total_assets'][-1]:,.0f}"
            current_liabilities = f"£{projections['total_liabilities'][-1]:,.0f}"
            
            print(f"🔧 DEBUG: Returning chart update")
            
            return (
                chart_figure,
                current_net_worth,
                current_cashflow, 
                current_assets,
                current_liabilities
            )
    
    def register_data_input_callbacks(self):
        """
        Connect 27-field data input modal to chart and control panel displays
        
        Data Input Fields:
        - Income: gross_salary, bonus, freelance, rental, dividends, other_income
        - Expenses: housing, utilities, transport, groceries, healthcare, entertainment  
        - Assets: home_value, savings, investments, pension, other_assets
        - Liabilities: mortgage, credit_cards, personal_loans, student_loans, other_debts
        """
        
        @self.app.callback(
            [
                # Update Current Value Displays in Control Panel
                Output('current-income-display', 'children'),
                Output('current-housing-display', 'children'),
                Output('current-utilities-display', 'children'),
                Output('current-transport-display', 'children'),
                Output('current-food-display', 'children'),
                Output('current-savings-total-display', 'children'),
                
                # Update Chart with User Data
                Output('enhanced-financial-projection-chart', 'figure', allow_duplicate=True),
                
                # Update Summary Cards
                Output('current-net-worth-summary', 'children', allow_duplicate=True),
                Output('current-cashflow-summary-main', 'children', allow_duplicate=True),
                Output('current-assets-summary', 'children', allow_duplicate=True),
                Output('current-liabilities-summary', 'children', allow_duplicate=True)
            ],
            [
                Input('financial-data-store', 'data')
            ],
            [
                # Control panel slider states for projection comparison
                State('income-slider', 'value'),
                State('mortgage-slider', 'value'),
                State('utilities-slider', 'value'),
                State('transport-slider', 'value'),
                State('food-slider', 'value'),
                State('total-savings-slider', 'value'),
                State('chart-time-range-slider', 'value')
            ],
            prevent_initial_call=True
        )
        def update_from_data_input(
            financial_data,
            # Control panel states for comparison
            income_slider, housing_slider, utilities_slider,
            transport_slider, food_slider, savings_slider,
            time_range_months
        ):
            """
            Update all displays when user enters financial data
            
            Shows user's actual data vs control panel projections
            """
            
            if not financial_data:
                return [no_update] * 11
            
            # Calculate monthly values from user data
            monthly_net_income = calculate_uk_net_income(
                financial_data.get('gross_salary', 0)
            )
            monthly_housing = financial_data.get('housing_costs', 0) / 12
            monthly_utilities = financial_data.get('utilities', 0) / 12  
            monthly_transport = financial_data.get('transport', 0) / 12
            monthly_food = financial_data.get('groceries', 0) / 12
            
            # Calculate current savings/investments
            current_savings = financial_data.get('savings', 0)
            current_investments = financial_data.get('investments', 0)
            total_savings = current_savings + current_investments
            
            # Format current value displays
            current_income_display = f"£{monthly_net_income:,.0f}"
            current_housing_display = f"£{monthly_housing:,.0f}"
            current_utilities_display = f"£{monthly_utilities:,.0f}"
            current_transport_display = f"£{monthly_transport:,.0f}"
            current_food_display = f"£{monthly_food:,.0f}"
            current_savings_display = f"£{total_savings:,.0f}"
            
            # Create updated chart with user data baseline
            user_financial_inputs = {
                'monthly_income': monthly_net_income,
                'monthly_housing': monthly_housing,
                'monthly_utilities': monthly_utilities,
                'monthly_transport': monthly_transport,
                'monthly_food': monthly_food,
                'starting_assets': (
                    financial_data.get('home_value', 0) +
                    financial_data.get('savings', 0) +
                    financial_data.get('investments', 0) +
                    financial_data.get('pension', 0) +
                    financial_data.get('other_assets', 0)
                ),
                'starting_liabilities': (
                    financial_data.get('mortgage', 0) +
                    financial_data.get('credit_cards', 0) +
                    financial_data.get('personal_loans', 0) +
                    financial_data.get('student_loans', 0) +
                    financial_data.get('other_debts', 0)
                )
            }
            
            # Calculate projections with user data
            projections = calculate_financial_projections(
                user_financial_inputs,
                {},
                time_range_months or 60
            )
            
            # Create updated chart
            updated_chart = self.create_enhanced_financial_chart(
                projections,
                time_range_months or 60
            )
            
            # Calculate updated summary values
            current_net_worth = f"£{projections['net_worth'][-1]:,.0f}"
            current_cashflow = f"£{projections['monthly_cash_flow'][-1]:,.0f}"
            current_assets = f"£{projections['total_assets'][-1]:,.0f}"
            current_liabilities = f"£{projections['total_liabilities'][-1]:,.0f}"
            
            return (
                current_income_display,
                current_housing_display,
                current_utilities_display,
                current_transport_display,
                current_food_display,
                current_savings_display,
                updated_chart,
                current_net_worth,
                current_cashflow,
                current_assets,
                current_liabilities
            )
    
    def register_time_range_callbacks(self):
        """
        Handle time range slider and preset buttons (1Y, 5Y, 10Y, 30Y)
        
        Updates chart scaling and data point granularity
        """
        
        @self.app.callback(
            Output('chart-time-range-slider', 'value'),
            [
                Input('range-1y', 'n_clicks'),
                Input('range-5y', 'n_clicks'), 
                Input('range-10y', 'n_clicks'),
                Input('range-30y', 'n_clicks')
            ],
            prevent_initial_call=True
        )
        def update_time_range_from_buttons(n1y, n5y, n10y, n30y):
            """Update time range slider when preset buttons are clicked"""
            
            ctx = callback_context
            if not ctx.triggered:
                return no_update
            
            button_id = ctx.triggered[0]['prop_id'].split('.')[0]
            
            time_range_map = {
                'range-1y': 12,   # 1 year = 12 months
                'range-5y': 60,   # 5 years = 60 months  
                'range-10y': 120, # 10 years = 120 months
                'range-30y': 360  # 30 years = 360 months
            }
            
            return time_range_map.get(button_id, 60)
    
    def register_impact_display_callbacks(self):
        """
        Real-time impact calculations and explanations
        
        Updates impact displays showing financial effects of slider changes
        """
        
        @self.app.callback(
            [
                # Impact Display Updates
                Output('income-impact-display', 'children'),
                Output('mortgage-impact-display', 'children'),
                Output('utilities-impact-display', 'children'),
                Output('transport-impact-display', 'children'),
                Output('food-impact-display', 'children'),
                Output('savings-impact-display', 'children'),
                
                # Current vs Projected Comparisons
                Output('projected-income-display', 'children'),
                Output('projected-housing-display', 'children'),
                Output('projected-utilities-display', 'children'),
                Output('projected-transport-display', 'children'),
                Output('projected-food-display', 'children'),
                Output('projected-savings-total-display', 'children'),
                
                # Cash Flow Summary Updates
                Output('current-cashflow-summary', 'children'),
                Output('projected-cashflow-summary', 'children'),
                Output('cashflow-difference-summary', 'children'),
                Output('difference-explanation', 'children'),
                
                # Weighted Investment Return Display
                Output('total-monthly-savings-display', 'children'),
                Output('weighted-return-display', 'children')
            ],
            [
                Input('income-slider', 'value'),
                Input('income-growth-slider', 'value'),
                Input('mortgage-slider', 'value'),
                Input('mortgage-rate-slider', 'value'),
                Input('utilities-slider', 'value'),
                Input('utilities-inflation-slider', 'value'),
                Input('transport-slider', 'value'),
                Input('transport-inflation-slider', 'value'),
                Input('food-slider', 'value'),
                Input('food-inflation-slider', 'value'),
                Input('total-savings-slider', 'value'),
                Input('savings-rate-slider', 'value'),
                Input('total-investments-slider', 'value'),
                Input('investment-return-slider', 'value'),
                Input('chart-time-range-slider', 'value'),
                Input('investment-type-selector', 'value')
            ],
            [
                State('financial-data-store', 'data')
            ]
        )
        def update_impact_displays(
            income_monthly, income_growth,
            housing_monthly, housing_rate,
            utilities_monthly, utilities_inflation,
            transport_monthly, transport_change,
            food_monthly, food_inflation,
            savings_monthly, savings_rate,
            investments_monthly, investment_return,
            time_range_months, investment_type,
            financial_data
        ):
            """
            Calculate and display real-time financial impact of slider changes
            
            Shows immediate feedback on 30-year financial effects
            """
            
            # Calculate 30-year impacts for each category
            years = time_range_months / 12
            
            # Income Impact Calculation
            base_income = 3500  # Default baseline
            income_difference = income_monthly - base_income
            annual_growth_effect = calculate_compound_interest(
                income_difference * 12, income_growth/100, years
            )
            income_impact = f"£{annual_growth_effect:,.0f} over {years:.0f} years"
            
            # Housing Impact Calculation  
            base_housing = 1200  # Default baseline
            housing_difference = housing_monthly - base_housing
            housing_total_impact = housing_difference * time_range_months
            interest_savings = calculate_debt_amortization(
                housing_difference, housing_rate/100, years
            )
            housing_impact = f"£{interest_savings:,.0f} interest effect"
            
            # Utilities Impact Calculation
            base_utilities = 150  # Default baseline
            utilities_difference = utilities_monthly - base_utilities
            utilities_inflation_effect = calculate_compound_interest(
                utilities_difference * 12, utilities_inflation/100, years
            )
            utilities_impact = f"£{utilities_inflation_effect:,.0f} cost increase"
            
            # Transport Impact Calculation
            base_transport = 200  # Default baseline
            transport_difference = transport_monthly - base_transport
            transport_change_effect = calculate_compound_interest(
                transport_difference * 12, transport_change/100, years
            )
            transport_impact = f"£{transport_change_effect:,.0f} transport costs"
            
            # Food Impact Calculation
            base_food = 300  # Default baseline
            food_difference = food_monthly - base_food
            food_inflation_effect = calculate_compound_interest(
                food_difference * 12, food_inflation/100, years
            )
            food_impact = f"£{food_inflation_effect:,.0f} food costs"
            
            # Savings & Investment Impact Calculation
            total_monthly_combined = savings_monthly + investments_monthly
            weighted_return = calculate_weighted_investment_return(
                savings_monthly, savings_rate/100,
                investments_monthly, investment_return/100
            )
            
            if investment_type == 'compound':
                future_value = calculate_compound_interest(
                    total_monthly_combined * 12, weighted_return, years
                )
            else:
                future_value = total_monthly_combined * time_range_months * (
                    1 + weighted_return * years
                )
            
            savings_impact = f"£{future_value:,.0f} projected"
            
            # Projected Value Displays
            projected_income = f"£{income_monthly:,.0f}"
            projected_housing = f"£{housing_monthly:,.0f}"
            projected_utilities = f"£{utilities_monthly:,.0f}"
            projected_transport = f"£{transport_monthly:,.0f}"
            projected_food = f"£{food_monthly:,.0f}"
            projected_savings_total = f"£{total_monthly_combined:,.0f}"
            
            # Cash Flow Calculations
            user_data = financial_data or {}
            current_net_income = calculate_uk_net_income(
                user_data.get('gross_salary', 0)
            ) if user_data else 0
            current_expenses = (
                user_data.get('housing_costs', 0) +
                user_data.get('utilities', 0) +
                user_data.get('transport', 0) +
                user_data.get('groceries', 0)
            ) / 12 if user_data else 0
            
            current_cashflow = current_net_income - current_expenses
            projected_cashflow = income_monthly - (
                housing_monthly + utilities_monthly + 
                transport_monthly + food_monthly +
                total_monthly_combined
            )
            cashflow_difference = projected_cashflow - current_cashflow
            
            # Format displays
            current_cashflow_display = f"£{current_cashflow:,.0f}"
            projected_cashflow_display = f"£{projected_cashflow:,.0f}"
            difference_display = f"£{cashflow_difference:,.0f}"
            
            if cashflow_difference > 0:
                difference_explanation = "Better cash flow position"
            elif cashflow_difference < 0:
                difference_explanation = "Reduced cash flow"
            else:
                difference_explanation = "No change"
            
            # Weighted return display
            total_monthly_display = f"£{total_monthly_combined:,.0f}"
            weighted_return_display = f"{weighted_return*100:.1f}%"
            
            return (
                income_impact,
                housing_impact,
                utilities_impact,
                transport_impact,
                food_impact,
                savings_impact,
                projected_income,
                projected_housing,
                projected_utilities,
                projected_transport,
                projected_food,
                projected_savings_total,
                current_cashflow_display,
                projected_cashflow_display,
                difference_display,
                difference_explanation,
                total_monthly_display,
                weighted_return_display
            )
    
    def create_enhanced_financial_chart(
        self, 
        projections: Dict[str, List[float]], 
        time_range_months: int
    ) -> go.Figure:
        """
        Create interactive financial projection chart with 4 key metrics
        
        Traces:
        1. Net Worth (green) - Assets minus Liabilities
        2. Total Assets (blue) - Everything you own
        3. Total Liabilities (red) - Everything you owe  
        4. Cumulative Cash Flow (teal) - Monthly surplus accumulation
        """
        
        # Prepare time axis
        months = list(range(1, time_range_months + 1))
        years = [month / 12 for month in months]
        
        # Create figure with secondary y-axis for percentages if needed
        fig = go.Figure()
        
        # Net Worth Trace (primary metric)
        fig.add_trace(go.Scatter(
            x=years,
            y=projections['net_worth'],
            mode='lines',
            name='Net Worth',
            line=dict(color='#28a745', width=3),
            hovertemplate='<b>Net Worth</b><br>' +
                         'Year: %{x:.1f}<br>' +
                         'Value: £%{y:,.0f}<extra></extra>'
        ))
        
        # Total Assets Trace
        fig.add_trace(go.Scatter(
            x=years,
            y=projections['total_assets'],
            mode='lines',
            name='Total Assets',
            line=dict(color='#007bff', width=2),
            hovertemplate='<b>Total Assets</b><br>' +
                         'Year: %{x:.1f}<br>' +
                         'Value: £%{y:,.0f}<extra></extra>'
        ))
        
        # Total Liabilities Trace
        fig.add_trace(go.Scatter(
            x=years,
            y=projections['total_liabilities'],
            mode='lines',
            name='Total Liabilities',
            line=dict(color='#dc3545', width=2),
            hovertemplate='<b>Total Liabilities</b><br>' +
                         'Year: %{x:.1f}<br>' +
                         'Value: £%{y:,.0f}<extra></extra>'
        ))
        
        # Cumulative Cash Flow Trace
        fig.add_trace(go.Scatter(
            x=years,
            y=projections['cumulative_cash_flow'],
            mode='lines',
            name='Cash Flow',
            line=dict(color='#20c997', width=2),
            hovertemplate='<b>Cumulative Cash Flow</b><br>' +
                         'Year: %{x:.1f}<br>' +
                         'Value: £%{y:,.0f}<extra></extra>'
        ))
        
        # Update layout for professional appearance
        fig.update_layout(
            title=dict(
                text=f"Financial Projection ({time_range_months//12}-Year Outlook)",
                x=0.5,
                font=dict(size=16, family="Arial")
            ),
            xaxis=dict(
                title="Years",
                showgrid=True,
                gridcolor='rgba(0,0,0,0.1)',
                zeroline=False
            ),
            yaxis=dict(
                title="Value (£)",
                showgrid=True,
                gridcolor='rgba(0,0,0,0.1)',
                zeroline=True,
                zerolinecolor='rgba(0,0,0,0.3)',
                tickformat=',.0f',
                tickprefix='£'
            ),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            hovermode='x unified',
            plot_bgcolor='white',
            paper_bgcolor='white',
            margin=dict(l=50, r=50, t=50, b=50),
            height=500
        )
        
        return fig


# Initialize callback system
def register_dashboard_callbacks(app=None):
    """Register all financial dashboard callbacks"""
    return FinancialDashboardCallbacks(app)
