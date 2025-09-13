import sys
import traceback
from datetime import datetime
from typing import List, Dict, Any, Optional, Union, Callable
from dash import html, Input, Output, State, dash, Dash

# shared list to store errors
error_collection: List[Dict[str, Any]] = []

def collect_error(callback_name: str = "Unknown"):
    """Collect error information when an exception occurs."""
    exc_type, exc_value, _ = sys.exc_info()
    error_details = {
        'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'callback': callback_name,
        'type': str(exc_type.__name__) if exc_type else "Unknown",
        'message': str(exc_value),
        'traceback': traceback.format_exc()
    }
    error_collection.append(error_details)
    return error_details

def get_all_errors():
    """Return all collected errors as formatted text for copying."""
    if not error_collection:
        return "No errors collected."
    
    error_text = "=== COLLECTED APPLICATION ERRORS ===\n\n"
    
    for i, error in enumerate(error_collection):
        error_text += f"ERROR #{i+1}\n"
        error_text += f"Time: {error['time']}\n"
        error_text += f"Callback: {error['callback']}\n"
        error_text += f"Type: {error['type']}\n"
        error_text += f"Message: {error['message']}\n"
        error_text += f"Traceback:\n{error['traceback']}\n"
        error_text += "-" * 50 + "\n\n"
    
    return error_text

def get_all_errors_list():
    """Return all collected errors as a list for display."""
    return error_collection.copy()

def clear_errors():
    """Clear the error collection."""
    global error_collection
    error_collection = []

def register_error_handling_callbacks(app: Dash) -> Dict[str, Callable]:
    """Register error handling callbacks for the app and return the callback functions."""
    
    @app.callback(
        Output("error-collection-display", "children"),
        Input("show-errors-btn", "n_clicks"),
        prevent_initial_call=True
    )
    def display_all_errors(n_clicks: Optional[int]) -> Union[str, html.Pre]:
        """Display all collected errors when button is clicked."""
        if not n_clicks:
            return ""
        
        errors = get_all_errors()
        return html.Pre(errors, style={
            "backgroundColor": "#f8f9fa",
            "padding": "15px",
            "border": "1px solid #dee2e6",
            "borderRadius": "5px",
            "maxHeight": "500px",
            "overflowY": "auto"
        })

    @app.callback(
        Output("error-collection-display", "children", allow_duplicate=True),
        Input("clear-errors-btn", "n_clicks"),
        prevent_initial_call=True
    )
    def clear_all_errors(n_clicks: Optional[int]) -> Union[str, Any]:
        """Clear all collected errors when button is clicked."""
        if not n_clicks:
            return dash.no_update
        
        clear_errors()
        return "Errors cleared."
    
    # Return callback functions to make them "used"
    return {
        "display_all_errors": display_all_errors,
        "clear_all_errors": clear_all_errors
    }