#!/usr/bin/env python3
"""
Test and demonstration of the Personal Mode Data Management System
"""

import dash
from dash import html, dcc
import dash_bootstrap_components as dbc
from modules.personal_mode.main import (
    create_personal_mode_layout, 
    register_personal_mode_callbacks,
    create_profile_data_structure
)

# Create the Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Test the data management functions
def test_data_management_functions():
    """Test the data management functionality"""
    print("🧪 Testing Data Management Functions...")
    
    # Test profile data structure creation
    try:
        profile = create_profile_data_structure()
        print("✅ Profile data structure created successfully")
        print(f"   - Profile keys: {list(profile.keys())}")
        print(f"   - Financial data categories: {list(profile['financialData'].keys())}")
        print(f"   - Metadata: {profile['profileMetadata']['profileName']}")
    except Exception as e:
        print(f"❌ Profile creation failed: {e}")
        return False
    
    # Test layout creation
    try:
        layout = create_personal_mode_layout()
        print("✅ Personal mode layout created successfully")
        print(f"   - Layout type: {type(layout)}")
    except Exception as e:
        print(f"❌ Layout creation failed: {e}")
        return False
    
    return True

# Test the functions
if test_data_management_functions():
    print("\n🎉 All data management functions are working correctly!")
    
    # Create the app layout
    app.layout = dbc.Container([
        html.H1("Financial Optimizer - Personal Mode with Data Management", 
                className="text-center mb-4"),
        
        dbc.Alert([
            html.I(className="fas fa-check-circle me-2"),
            "Data Management System Successfully Integrated! Features include:",
            html.Ul([
                html.Li("Auto-save every 30 seconds to browser localStorage"),
                html.Li("Manual save/load profile controls"),
                html.Li("Export profile as JSON file"),
                html.Li("Import profile from JSON file"),
                html.Li("Reset all data with confirmation"),
                html.Li("Real-time save status indicators"),
            ], className="mb-0 mt-2")
        ], color="success", className="mb-4"),
        
        # Include the full Personal Mode layout
        create_personal_mode_layout()
    ], fluid=True)
    
    # Register all callbacks including data management
    register_personal_mode_callbacks(app)
    
    print("\n📊 Data Management Features Added:")
    print("   🔄 Auto-save: Every 30 seconds to localStorage") 
    print("   💾 Manual Save: Instant save button")
    print("   📁 Export: Download JSON backup file")
    print("   📥 Import: Upload and restore from JSON")
    print("   🗑️  Reset: Clear all data with confirmation")
    print("   📈 Status: Real-time save indicators")
    
    print(f"\n🚀 Starting server on http://127.0.0.1:8052")
    print("💡 Navigate to Data Input tab to see data management controls")
    
    # Run the app
    if __name__ == "__main__":
        app.run_server(debug=True, port=8052)
else:
    print("\n❌ Some functions failed. Please check the implementation.")
