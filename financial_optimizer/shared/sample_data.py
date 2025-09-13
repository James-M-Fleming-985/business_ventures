"""
Sample data for development and demonstrations.
"""
from typing import Dict, Any, List

def get_sample_data() -> Dict[str, Any]:
    """
    Return sample financial data for testing.
    """
    return {
        "income": [
            {"name": "Salary", "amount": 5000, "frequency": "monthly"},
            {"name": "Bonus", "amount": 10000, "frequency": "annual"},
            {"name": "Dividends", "amount": 2000, "frequency": "quarterly"}
        ],
        "expenses": [
            {"name": "Rent", "amount": 1500, "frequency": "monthly"},
            {"name": "Utilities", "amount": 300, "frequency": "monthly"},
            {"name": "Insurance", "amount": 200, "frequency": "monthly"}
        ],
        "assets": [
            {"name": "Cash", "value": 15000, "liquid": True},
            {"name": "Stocks", "value": 50000, "liquid": True},
            {"name": "Property", "value": 300000, "liquid": False}
        ],
        "liabilities": [
            {"name": "Credit Card", "balance": 2000, "rate": 0.189},
            {"name": "Mortgage", "balance": 250000, "rate": 0.035}
        ]
    }