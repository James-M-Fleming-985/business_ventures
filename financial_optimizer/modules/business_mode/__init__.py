"""
Business Mode Module - Financial Optimizer

This module implements the Business Mode functionality for the Financial
Optimizer platform, providing business-specific financial management and
optimization features.

Module Structure:
- main.py: Main Business Mode implementation and layout
- callbacks/: Business Mode callback functions
- layout/: UI layout components
- logic/: Business logic and calculations
- models/: Data models and structures
- utils.py: Utility functions

The Business Mode module supports business financial optimization including
cash flow management, capital equipment planning, and business investment
strategies.
"""

from .layout.main import create_business_layout, create_business_mode_layout

__all__ = [
    'create_business_layout',
    'create_business_mode_layout'
]
