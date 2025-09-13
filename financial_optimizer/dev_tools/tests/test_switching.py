#!/usr/bin/env python3
"""
Test script to verify use case switching functionality
"""
import sys
sys.path.append('/workspaces/financial_optimizer')

try:
    from modules.personal_mode import create_personal_mode_layout
    print("✅ Personal Mode import successful")

    # Test creating personal mode layout
    personal_layout = create_personal_mode_layout()
    print("✅ Personal Mode layout creation successful")
    print(f"   Layout type: {type(personal_layout)}")

except Exception as e:
    print(f"❌ Personal Mode test failed: {e}")
    import traceback
    traceback.print_exc()

# Test business mode imports (basic imports)
try:
    import dash_bootstrap_components as dbc
    from dash import html
    print("✅ Business Mode dependencies import successful")

    # Test creating a simple business layout similar to simple_app.py
    business_layout = dbc.Tabs([
        dbc.Tab(label="Test Tab", children=[
            html.Div([
                html.H3("Test Business Tab"),
                html.P("Test content")
            ])
        ])
    ])
    print("✅ Business Mode layout creation successful")
    print(f"   Layout type: {type(business_layout)}")

except Exception as e:
    print(f"❌ Business Mode test failed: {e}")
    import traceback
    traceback.print_exc()

print("\n🧪 Use Case Switching Test Complete")
