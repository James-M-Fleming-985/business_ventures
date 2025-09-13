
# Initialize callbacks when module is loaded
def register_personal_mode_callbacks():
    """Register all Personal Mode callbacks"""
    try:
        from .callbacks.dashboard_callbacks import register_dashboard_callbacks
        register_dashboard_callbacks()
        print("✅ Personal Mode dashboard callbacks registered successfully")
    except ImportError as e:
        print(f"⚠️ Warning: Could not register dashboard callbacks: {e}")
    except Exception as e:
        print(f"❌ Error registering dashboard callbacks: {e}")
    
    try:
        from .callbacks.data_management_callbacks import register_data_management_callbacks
        register_data_management_callbacks()
        print("✅ Personal Mode data management callbacks registered successfully")
    except ImportError as e:
        print(f"⚠️ Warning: Could not register data management callbacks: {e}")
    except Exception as e:
        print(f"❌ Error registering data management callbacks: {e}")
