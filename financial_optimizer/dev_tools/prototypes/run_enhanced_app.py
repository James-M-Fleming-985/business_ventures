"""
Test script to run the enhanced original app with use case switching.
This runs the original app.py with integrated use case switching.
"""

if __name__ == "__main__":
    print("🚀 Starting Enhanced Financial Optimizer with Use Case Switching")
    print("📊 This includes all your original functionality plus use case switching")
    print("🔍 Available Use Cases: Business, Personal, Charity, Non-Profit")
    print("🌐 Access the application at: http://localhost:8054")

    # Import and run the enhanced app
    import sys

    sys.path.append(".")

    from app import app

    app.run(debug=True, port=8054)
