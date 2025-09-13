#!/usr/bin/env python3
"""
Data Management Callbacks for Personal Mode
Handles versioning, backup, and data persistence UI interactions
"""

from dash import Input, Output, State, callback, no_update, html, dcc
import dash_bootstrap_components as dbc
from datetime import datetime
import json

# Import the data persistence manager
from modules.personal_mode.data_persistence import user_data_manager


def register_data_management_callbacks():
    """Register all data management callbacks"""
    
    @callback(
        Output('data-status-alert', 'children'),
        Output('current-data-summary', 'children'),
        Input('data-management-store', 'data'),
        prevent_initial_call=False
    )
    def update_data_status(store_data):
        """Update data status display"""
        try:
            # Get data summary
            summary = user_data_manager.get_data_summary()
            
            if summary["success"]:
                # Status alert
                if summary["has_saved_data"]:
                    alert = dbc.Alert([
                        html.I(className="fas fa-check-circle me-2"),
                        f"Data loaded successfully - Last updated: {summary['last_updated']}"
                    ], color="success")
                else:
                    alert = dbc.Alert([
                        html.I(className="fas fa-info-circle me-2"),
                        "Using default values - No saved data found"
                    ], color="info")
                
                # Summary display
                summary_content = [
                    html.P([
                        html.Strong("Created: "), 
                        summary.get('created_date', 'Never')
                    ], className="mb-1"),
                    html.P([
                        html.Strong("Last Updated: "), 
                        summary.get('last_updated', 'Never')
                    ], className="mb-1"),
                    html.P([
                        html.Strong("Version: "), 
                        summary.get('version', 'Unknown')
                    ], className="mb-1"),
                    html.P([
                        html.Strong("Backups: "), 
                        f"{summary.get('backup_count', 0)} available"
                    ], className="mb-1"),
                    html.P([
                        html.Strong("Source: "), 
                        summary.get('data_source', 'Unknown')
                    ], className="mb-0")
                ]
                
                return alert, summary_content
            else:
                alert = dbc.Alert([
                    html.I(className="fas fa-exclamation-triangle me-2"),
                    f"Error loading data status: {summary.get('error', 'Unknown error')}"
                ], color="warning")
                
                return alert, "Unable to load data summary"
                
        except Exception as e:
            alert = dbc.Alert([
                html.I(className="fas fa-times-circle me-2"),
                f"Error: {str(e)}"
            ], color="danger")
            
            return alert, "Error loading data status"

    @callback(
        Output('version-history-list', 'children'),
        Output('version-select', 'options'),
        Input('refresh-versions-btn', 'n_clicks'),
        prevent_initial_call=True
    )
    def refresh_version_history(n_clicks):
        """Refresh and display version history"""
        try:
            history = user_data_manager.get_version_history()
            
            if history["success"] and history["versions"]:
                # Create version list display
                version_items = []
                version_options = []
                
                for version in history["versions"][:10]:  # Show last 10 versions
                    # Format timestamp
                    try:
                        dt = datetime.fromisoformat(version["timestamp"])
                        formatted_time = dt.strftime("%m/%d %H:%M")
                    except:
                        formatted_time = version["timestamp"][:16]
                    
                    version_items.append(
                        dbc.ListGroupItem([
                            html.Div([
                                html.Strong(version["version_id"]),
                                html.Small(f" ({formatted_time})", className="text-muted ms-2")
                            ]),
                            html.Small(version["description"], className="text-muted"),
                            html.Small(f"{version['change_count']} changes", className="badge bg-secondary ms-2")
                        ])
                    )
                    
                    # Add to dropdown options
                    version_options.append({
                        "label": f"{version['version_id']} - {version['description'][:30]}...",
                        "value": version["version_id"]
                    })
                
                version_list = dbc.ListGroup(version_items, flush=True, style={"max-height": "300px", "overflow-y": "auto"})
                
                return version_list, version_options
            else:
                no_versions = dbc.Alert("No version history available", color="info", className="text-center")
                return no_versions, []
                
        except Exception as e:
            error_msg = dbc.Alert(f"Error loading versions: {str(e)}", color="danger")
            return error_msg, []

    @callback(
        Output('backup-list', 'children'),
        Input('refresh-backups-btn', 'n_clicks'),
        prevent_initial_call=True
    )
    def refresh_backup_list(n_clicks):
        """Refresh and display backup list"""
        try:
            backups = user_data_manager.list_backups()
            
            if backups["success"] and backups["backups"]:
                backup_items = []
                
                for backup in backups["backups"][:5]:  # Show last 5 backups
                    backup_items.append(
                        dbc.ListGroupItem([
                            html.Div([
                                html.Strong(backup["formatted_date"]),
                                html.Small(f" ({backup['size_kb']} KB)", className="text-muted ms-2")
                            ]),
                            html.Small(backup["filename"], className="text-muted")
                        ])
                    )
                
                backup_list = dbc.ListGroup(backup_items, flush=True)
                return backup_list
            else:
                no_backups = dbc.Alert("No backups available", color="info", className="text-center")
                return no_backups
                
        except Exception as e:
            error_msg = dbc.Alert(f"Error loading backups: {str(e)}", color="danger")
            return error_msg

    @callback(
        Output('recent-changes-list', 'children'),
        Input('view-changes-btn', 'n_clicks'),
        prevent_initial_call=True
    )
    def view_recent_changes(n_clicks):
        """Display recent changes"""
        try:
            changes = user_data_manager.get_change_log(limit=5)
            
            if changes["success"] and changes["changes"]:
                change_items = []
                
                for change in changes["changes"]:
                    # Format timestamp
                    try:
                        dt = datetime.fromisoformat(change["timestamp"])
                        formatted_time = dt.strftime("%m/%d %H:%M")
                    except:
                        formatted_time = change["timestamp"][:16]
                    
                    change_items.append(
                        dbc.ListGroupItem([
                            html.Div([
                                html.Strong(change["description"]),
                                html.Small(f" ({formatted_time})", className="text-muted ms-2")
                            ]),
                            html.Small(f"{change['change_count']} changes", className="badge bg-info")
                        ])
                    )
                
                changes_list = dbc.ListGroup(change_items, flush=True)
                return changes_list
            else:
                no_changes = dbc.Alert("No recent changes", color="info", className="text-center")
                return no_changes
                
        except Exception as e:
            error_msg = dbc.Alert(f"Error loading changes: {str(e)}", color="danger")
            return error_msg

    @callback(
        Output('data-management-messages', 'children'),
        Input('save-data-btn', 'n_clicks'),
        Input('save-with-description-btn', 'n_clicks'),
        Input('export-data-btn', 'n_clicks'),
        Input('reset-data-btn', 'n_clicks'),
        Input('revert-version-btn', 'n_clicks'),
        State('save-description-input', 'value'),
        State('version-select', 'value'),
        State('financial-data-store', 'data'),
        prevent_initial_call=True
    )
    def handle_data_actions(save_clicks, save_desc_clicks, export_clicks, reset_clicks, 
                           revert_clicks, description, selected_version, financial_data):
        """Handle all data management actions"""
        from dash import callback_context
        
        if not callback_context.triggered:
            return no_update
        
        trigger_id = callback_context.triggered[0]['prop_id'].split('.')[0]
        
        try:
            if trigger_id == 'save-data-btn':
                # Quick save
                if financial_data:
                    result = user_data_manager.save_user_data(financial_data, change_description="Quick save from Data Management")
                    if result["success"]:
                        return dbc.Alert([
                            html.I(className="fas fa-check me-2"),
                            f"Data saved successfully! {result.get('changes_detected', 0)} changes detected."
                        ], color="success", dismissable=True)
                    else:
                        return dbc.Alert([
                            html.I(className="fas fa-times me-2"),
                            f"Save failed: {result['message']}"
                        ], color="danger", dismissable=True)
                else:
                    return dbc.Alert("No financial data to save", color="warning", dismissable=True)
            
            elif trigger_id == 'save-with-description-btn':
                # Save with description
                if financial_data and description:
                    result = user_data_manager.save_user_data(financial_data, change_description=description)
                    if result["success"]:
                        return dbc.Alert([
                            html.I(className="fas fa-check me-2"),
                            f"Data saved with description! Version: {result.get('version_id', 'N/A')}"
                        ], color="success", dismissable=True)
                    else:
                        return dbc.Alert([
                            html.I(className="fas fa-times me-2"),
                            f"Save failed: {result['message']}"
                        ], color="danger", dismissable=True)
                else:
                    return dbc.Alert("Please provide a description", color="warning", dismissable=True)
            
            elif trigger_id == 'export-data-btn':
                # Export data
                result = user_data_manager.export_data()
                if result["success"]:
                    return dbc.Alert([
                        html.I(className="fas fa-download me-2"),
                        f"Data exported to: {result['export_path']}"
                    ], color="success", dismissable=True)
                else:
                    return dbc.Alert([
                        html.I(className="fas fa-times me-2"),
                        f"Export failed: {result['message']}"
                    ], color="danger", dismissable=True)
            
            elif trigger_id == 'reset-data-btn':
                # Reset to defaults
                result = user_data_manager.reset_to_defaults()
                if result["success"]:
                    return dbc.Alert([
                        html.I(className="fas fa-undo me-2"),
                        "Data reset to defaults. Previous data backed up."
                    ], color="warning", dismissable=True)
                else:
                    return dbc.Alert([
                        html.I(className="fas fa-times me-2"),
                        f"Reset failed: {result['message']}"
                    ], color="danger", dismissable=True)
            
            elif trigger_id == 'revert-version-btn':
                # Revert to selected version
                if selected_version:
                    result = user_data_manager.revert_to_version(selected_version)
                    if result["success"]:
                        return dbc.Alert([
                            html.I(className="fas fa-undo-alt me-2"),
                            f"Reverted to version {selected_version}. Current data backed up."
                        ], color="info", dismissable=True)
                    else:
                        return dbc.Alert([
                            html.I(className="fas fa-times me-2"),
                            f"Revert failed: {result['message']}"
                        ], color="danger", dismissable=True)
                else:
                    return dbc.Alert("Please select a version to revert to", color="warning", dismissable=True)
            
            return no_update
            
        except Exception as e:
            return dbc.Alert([
                html.I(className="fas fa-exclamation-triangle me-2"),
                f"Error: {str(e)}"
            ], color="danger", dismissable=True)

    @callback(
        Output('advanced-tools-content', 'children'),
        Input('advanced-tools-tabs', 'active_tab'),
        prevent_initial_call=False
    )
    def render_advanced_tools(active_tab):
        """Render content for advanced tools tabs"""
        if active_tab == "change-details":
            return html.Div([
                html.H6("Change Details"),
                html.P("Select a version from the history to see detailed changes.", className="text-muted"),
                dbc.Button("Load Change Details", color="info", disabled=True)
            ])
        elif active_tab == "version-compare":
            return html.Div([
                html.H6("Version Comparison"),
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Version 1:"),
                        dbc.Select(placeholder="Select first version...")
                    ], width=6),
                    dbc.Col([
                        dbc.Label("Version 2:"),
                        dbc.Select(placeholder="Select second version...")
                    ], width=6)
                ]),
                dbc.Button("Compare Versions", color="primary", className="mt-2", disabled=True)
            ])
        elif active_tab == "import-export":
            return html.Div([
                html.H6("Import/Export"),
                dbc.Row([
                    dbc.Col([
                        html.Label("Import Financial Data:"),
                        dcc.Upload(
                            id='upload-data',
                            children=dbc.Button([
                                html.I(className="fas fa-upload me-2"),
                                "Select File to Import"
                            ], color="success"),
                            multiple=False
                        )
                    ], width=6),
                    dbc.Col([
                        html.Label("Export Options:"),
                        dbc.ButtonGroup([
                            dbc.Button("Export JSON", color="info"),
                            dbc.Button("Export CSV", color="secondary")
                        ])
                    ], width=6)
                ])
            ])
        
        return html.Div("Select a tab above", className="text-muted")

    print("✅ Data Management callbacks registered successfully")
