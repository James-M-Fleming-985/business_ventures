# data/sample_data.py

def get_business_sample_data():
    """Generate sample business financial data."""
    return {
        "income": [
            {"name": "Product Sales", "amount": 150000, "growth": 4},
            {"name": "Service Revenue", "amount": 75000, "growth": 6},
            {"name": "Maintenance Contracts", "amount": 35000, "growth": 3}
        ],
        "savings": [
            {"name": "Operating Cash", "balance": 250000, "rate": 1.5, "contribution": 5000}
        ],
        "investments": [
            {"name": "Equipment", "value": 350000, "return": -10, "contribution": 8000},
            {"name": "Property", "value": 1200000, "return": 3, "contribution": 0},
            {"name": "R&D Investment", "value": 180000, "return": 15, "contribution": 15000}
        ],
        "debts": [
            {"name": "Business Loan", "balance": 500000, "rate": 4.5, "payment": 9200},
            {"name": "Equipment Financing", "balance": 120000, "rate": 3.8, "payment": 3600}
        ],
        "spending": [
            {"category": "Payroll", "amount": 85000, "essential": True},
            {"category": "Rent", "amount": 12000, "essential": True},
            {"category": "Utilities", "amount": 5000, "essential": True},
            {"category": "Marketing", "amount": 7500, "essential": False},
            {"category": "Insurance", "amount": 3500, "essential": True},
            {"category": "Supplies", "amount": 18000, "essential": True},
            {"category": "Maintenance", "amount": 4500, "essential": True},
            {"category": "Professional Services", "amount": 2800, "essential": False}
        ]
    }

def get_personal_sample_data():
    """Generate sample personal financial data."""
    return {
        "income": [
            {"name": "Salary", "amount": 5500, "growth": 3},
            {"name": "Side Business", "amount": 1200, "growth": 8},
            {"name": "Investment Income", "amount": 450, "growth": 5}
        ],
        "savings": [
            {"name": "Emergency Fund", "balance": 25000, "rate": 2.0, "contribution": 500},
            {"name": "Cash Savings", "balance": 15000, "rate": 1.5, "contribution": 300}
        ],
        "investments": [
            {"name": "Stock Portfolio", "value": 120000, "return": 7.0, "contribution": 1000},
            {"name": "Real Estate", "value": 350000, "return": 4.5, "contribution": 0},
            {"name": "Retirement Accounts", "value": 180000, "return": 6.5, "contribution": 750},
            {"name": "Cryptocurrency", "value": 15000, "return": 15.0, "contribution": 200}
        ],
        "debts": [
            {"name": "Mortgage", "balance": 320000, "rate": 3.2, "payment": 1500},
            {"name": "Car Loan", "balance": 18000, "rate": 4.5, "payment": 380},
            {"name": "Student Loans", "balance": 25000, "rate": 5.0, "payment": 300},
            {"name": "Credit Card", "balance": 3000, "rate": 18.0, "payment": 200}
        ],
        "spending": [
            {"category": "Housing (excl. mortgage)", "amount": 650, "essential": True},
            {"category": "Groceries", "amount": 600, "essential": True},
            {"category": "Utilities", "amount": 300, "essential": True},
            {"category": "Transportation", "amount": 250, "essential": True},
            {"category": "Healthcare", "amount": 200, "essential": True},
            {"category": "Entertainment", "amount": 350, "essential": False},
            {"category": "Dining Out", "amount": 400, "essential": False},
            {"category": "Travel", "amount": 300, "essential": False},
            {"category": "Subscriptions", "amount": 100, "essential": False},
            {"category": "Shopping", "amount": 250, "essential": False}
        ]
    }

def get_sample_data(mode="business"):
    """Get sample data based on the selected mode."""
    if mode == "business":
        return get_business_sample_data()
    else:
        return get_personal_sample_data()