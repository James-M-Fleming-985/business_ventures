"""
Personal Mode Module - Financial Optimizer

This module implements the Personal Mode functionality for the Financial
Optimizer platform, providing tier-appropriate investment management and
portfolio optimization features.

Module Structure:
- main.py: Main Personal Mode implementation and layout
- callbacks/: Personal Mode callback functions
- layout/: UI layout components
- logic/: Business logic and calculations
- models/: Data models and structures
- utils.py: Utility functions

The Personal Mode module supports the goal-based subscription model with
features appropriate for personal finance management and investment planning.
"""

from .main import (
    create_allocation_sliders,
    create_personal_mode_layout,
    create_investment_management_layout,
    create_financial_dashboard_layout,
    create_analysis_tab_layout,
    create_data_input_tab_layout,
    create_subscription_management_layout,
    register_personal_mode_callbacks
)

__all__ = [
    'create_allocation_sliders',
    'create_personal_mode_layout',
    'create_investment_management_layout',
    'create_financial_dashboard_layout',
    'create_analysis_tab_layout',
    'create_data_input_tab_layout',
    'create_subscription_management_layout',
    'register_personal_mode_callbacks'
]
