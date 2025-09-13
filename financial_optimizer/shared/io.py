# data/io.py
import pandas as pd
import json
import os
from datetime import datetime

def load_csv_data(file_path):
    """Load financial data from a CSV file."""
    try:
        # Read the CSV file
        df = pd.read_csv(file_path)
        
        # Convert DataFrame to application data structure
        financial_data = convert_dataframe_to_financial_data(df)
        
        return financial_data
    
    except Exception as e:
        print(f"Error loading CSV data: {e}")
        return None

def convert_dataframe_to_financial_data(df):
    """Convert a DataFrame from CSV to the application's financial data structure."""
    financial_data = {
        "income": [],
        "savings": [],
        "investments": [],
        "debts": [],
        "spending": [],
    }
    
    # Process rows based on category column
    if 'Category' in df.columns:
        for _, row in df.iterrows():
            category = row.get("Category", "").lower()
            
            if category == "income":
                financial_data["income"].append({
                    "name": str(row.get("Name", "")),
                    "amount": float(row.get("Amount", 0)),
                    "growth": float(row.get("Growth", 0))
                })
            elif category == "savings":
                financial_data["savings"].append({
                    "name": str(row.get("Name", "")),
                    "balance": float(row.get("Balance", 0)),
                    "rate": float(row.get("Rate", 0)),
                    "contribution": float(row.get("Contribution", 0))
                })
            elif category == "investments":
                financial_data["investments"].append({
                    "name": str(row.get("Name", "")),
                    "value": float(row.get("Value", 0)),
                    "return": float(row.get("Return", 0)),
                    "contribution": float(row.get("Contribution", 0))
                })
            elif category == "debts":
                financial_data["debts"].append({
                    "name": str(row.get("Name", "")),
                    "balance": float(row.get("Balance", 0)),
                    "rate": float(row.get("Rate", 0)),
                    "payment": float(row.get("Payment", 0))
                })
            elif category == "spending":
                financial_data["spending"].append({
                    "category": str(row.get("Name", "")),
                    "amount": float(row.get("Amount", 0)),
                    "essential": bool(row.get("Essential", True)),
                })
    
    return financial_data

def save_financial_data(financial_data, file_path):
    """Save financial data to a JSON file."""
    try:
        with open(file_path, 'w') as f:
            json.dump(financial_data, f, indent=4)
        return True
    except Exception as e:
        print(f"Error saving financial data: {e}")
        return False

def get_sample_data():
    """Return sample financial data for testing/demo purposes."""
    return {
        "income": [
            {"name": "Salary", "amount": 5000, "growth": 3},
            {"name": "Side Business", "amount": 1000, "growth": 5}
        ],
        "savings": [
            {"name": "Emergency Fund", "balance": 10000, "rate": 1.5, "contribution": 200},
            {"name": "Savings Account", "balance": 5000, "rate": 1.0, "contribution": 100}
        ],
        "investments": [
            {"name": "Stock Portfolio", "value": 50000, "return": 7, "contribution": 500},
            {"name": "Real Estate", "value": 200000, "return": 4, "contribution": 0}
        ],
        "debts": [
            {"name": "Mortgage", "balance": 180000, "rate": 3.5, "payment": 1200},
            {"name": "Car Loan", "balance": 15000, "rate": 4.5, "payment": 300}
        ],
        "spending": [
            {"category": "Housing", "amount": 1500, "essential": True},
            {"category": "Food", "amount": 600, "essential": True},
            {"category": "Transportation", "amount": 400, "essential": True},
            {"category": "Entertainment", "amount": 300, "essential": False}
        ]
    }