"""
New application entry point using the proper architecture restructure.
This demonstrates the clean, scalable foundation we discussed.
"""

from core.factory_new import ApplicationFactory
from core.config import DEVELOPMENT_MODE, get_current_use_case

def main():
    """Main application entry point."""
    
    if DEVELOPMENT_MODE:
        print("🔧 Starting in Development Mode")
        print("🔄 Use case switching enabled")
        app = ApplicationFactory.create_development_app()
    else:
        print("🚀 Starting in Production Mode")
        current_use_case = get_current_use_case()
        print(f"📊 Use case: {current_use_case.value}")
        app = ApplicationFactory.create_app(current_use_case)
    
    # Run the application
    app.run(debug=DEVELOPMENT_MODE, port=8056)

if __name__ == "__main__":
    main()
