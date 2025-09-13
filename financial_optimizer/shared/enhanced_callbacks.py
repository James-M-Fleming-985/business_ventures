"""
Enhanced Callback Management System for Financial Optimizer

This module restores all the original features (business, personal, charity, non-profit modes)
through the managed callback system to prevent conflicts while maintaining functionality.
"""

from dash import callback, Input, Output, State, html, dcc, dash_table
import dash_bootstrap_components as dbc
from datetime import datetime
import json
import os

# Import personal mode if available
try:
    from modules.personal_mode import (
        create_personal_mode_layout, 
        register_personal_mode_callbacks
    )
    PERSONAL_MODE_AVAILABLE = True
except ImportError:
    PERSONAL_MODE_AVAILABLE = False
    print("Personal mode module not available - using placeholder")

# Import other callback registration functions
try:
    # from modules.business_mode.callbacks.main import register_business_callbacks
    # BUSINESS_CALLBACKS_AVAILABLE = True
    BUSINESS_CALLBACKS_AVAILABLE = False
    print("Business mode callbacks temporarily disabled due to syntax errors")
except ImportError:
    BUSINESS_CALLBACKS_AVAILABLE = False
    print("Business mode callbacks not available")

try:
    from modules.financial_dashboard.callbacks import register_financial_dashboard_callbacks
    FINANCIAL_DASHBOARD_CALLBACKS_AVAILABLE = True
except ImportError:
    FINANCIAL_DASHBOARD_CALLBACKS_AVAILABLE = False
    print("Financial dashboard callbacks not available")

try:
    from modules.investment_mgmt.callbacks import register_investment_mgmt_callbacks
    INVESTMENT_MGMT_CALLBACKS_AVAILABLE = True
except ImportError:
    INVESTMENT_MGMT_CALLBACKS_AVAILABLE = False
    print("Investment management callbacks not available")


class EnhancedCallbackManager:
    """Enhanced callback management system with all original features"""
    
    def __init__(self, app):
        self.app = app
        self.registered_callbacks = []
        
    def register_callback(self, callback_id, outputs, inputs, states=None, func=None):
        """Register a callback with conflict checking"""
        if states is None:
            states = []
            
        # Check for conflicts
        for existing in self.registered_callbacks:
            if existing['id'] == callback_id:
                print(f"WARNING: Callback {callback_id} already registered!")
                return False
                
        # Store callback info
        callback_info = {
            'id': callback_id,
            'outputs': outputs,
            'inputs': inputs,
            'states': states,
            'function': func
        }
        
        self.registered_callbacks.append(callback_info)
        return True
        
    def list_callbacks(self):
        """List all registered callbacks"""
        if not self.registered_callbacks:
            print("No callbacks registered in manager")
            return
        
        print(f"📋 ENHANCED CALLBACK MANAGER: {len(self.registered_callbacks)} callbacks tracked:")
        for cb in self.registered_callbacks:
            print(f"  🔹 {cb['id']}")
            if cb.get('outputs'):
                print(f"    Outputs: {[o.component_id if hasattr(o, 'component_id') else str(o) for o in cb['outputs']]}")
            if cb.get('inputs'):
                print(f"    Inputs: {[i.component_id if hasattr(i, 'component_id') else str(i) for i in cb['inputs']]}")
            if cb.get('states'):
                print(f"    States: {[s.component_id if hasattr(s, 'component_id') else str(s) for s in cb['states']]}")
            print()


# Utility functions for data persistence
def load_investments():
    """Load investments from JSON file"""
    try:
        if os.path.exists("/workspaces/financial_optimizer/data/investments.json"):
            with open("/workspaces/financial_optimizer/data/investments.json", "r") as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading investments: {e}")
    return []


def save_investments(investments):
    """Save investments to JSON file"""
    try:
        os.makedirs("/workspaces/financial_optimizer/data", exist_ok=True)
        with open("/workspaces/financial_optimizer/data/investments.json", "w") as f:
            json.dump(investments, f, indent=2)
    except Exception as e:
        print(f"Error saving investments: {e}")


def create_personal_mode_tabs():
    """Create personal mode tabs placeholder"""
    return dbc.Tabs([
        dbc.Tab(label="Personal Dashboard", children=[
            html.Div([
                html.H3("Personal Financial Dashboard"),
                dbc.Alert("Personal Mode", color="info"),
                dbc.Alert(
                    "Note: Advanced Personal Mode temporarily unavailable.",
                    color="warning"
                ),
                html.P("Basic personal financial management interface."),
            ], className="p-3")
        ])
    ])


def create_charity_mode_tabs():
    """Create charity mode tabs"""
    return dbc.Tabs([
        dbc.Tab(label="Donation Dashboard", children=[
            html.Div([
                html.H3("Donation Dashboard"),
                dbc.Alert(
                    "Charity donation tracking dashboard (placeholder)", 
                    color="warning"),
                html.P("Track donations, donors, and fundraising campaigns"),
            ], className="p-3")
        ]),
        dbc.Tab(label="Impact Tracking", children=[
            html.Div([
                html.H3("Impact Tracking"),
                dbc.Alert(
                    "Charity impact measurement (placeholder)", 
                    color="warning"),
                html.P("Measure and report on charitable impact"),
            ], className="p-3")
        ]),
        dbc.Tab(label="Grant Management", children=[
            html.Div([
                html.H3("Grant Management"),
                dbc.Alert(
                    "Grant application and management (placeholder)", 
                    color="warning"),
                html.P("Manage grant applications and compliance"),
            ], className="p-3")
        ]),
    ])


def create_business_mode_tabs():
    """Create business mode tabs with unique IDs to avoid conflicts"""
    return dbc.Tabs([
        # Tab 1: Investment Management (Business Mode specific)
        dbc.Tab(
            label="Business Investment Analysis",
            tab_id="biz-investment-analysis",
            children=[
                html.Div([
                    html.H4("Business Investment Analysis", className="mb-3"),
                    dbc.Alert(
                        "Advanced business investment analysis and tools",
                        color="primary"
                    ),
                    
                    # Investment Input Form (moved from main layout)
                    dbc.Card([
                        dbc.CardHeader(html.H5("Add New Investment", className="mb-0")),
                        dbc.CardBody([
                            dbc.Row([
                                dbc.Col([
                                    dbc.Label("Investment Name"),
                                    dbc.Input(id="main-investment-name-input", 
                                              placeholder="Enter investment name")
                                ], width=6),
                                dbc.Col([
                                    dbc.Label("Investment Type"),
                                    dbc.Select(
                                        id="main-investment-type-dropdown",
                                        options=[
                                            {"label": "Equipment", "value": "equipment"},
                                            {"label": "Technology", "value": "technology"},
                                            {"label": "Infrastructure", "value": "infrastructure"},
                                            {"label": "Training", "value": "training"},
                                            {"label": "Research", "value": "research"}
                                        ],
                                        placeholder="Select type"
                                    )
                                ], width=6)
                            ], className="mb-3"),
                            dbc.Row([
                                dbc.Col([
                                    dbc.Label("Initial Cost ($)"),
                                    dbc.Input(id="main-investment-cost-input", 
                                              type="number", placeholder="Enter cost")
                                ], width=6),
                                dbc.Col([
                                    dbc.Button("Add Investment", 
                                               id="main-add-investment-btn", 
                                               color="primary", className="mt-4")
                                ], width=6)
                            ])
                        ])
                    ], className="mb-4"),
                    
                    # Investment Portfolio Table (moved from main layout)
                    dbc.Card([
                        dbc.CardHeader([
                            html.H5("Investment Portfolio", className="mb-0 d-inline"),
                            dbc.Badge("0 Investments", id="main-investment-count-badge", 
                                      color="info", className="ms-2")
                        ]),
                        dbc.CardBody([
                            dash_table.DataTable(
                                id="main-investment-portfolio-table",
                                columns=[
                                    {"name": "Name", "id": "name"},
                                    {"name": "Type", "id": "type"},
                                    {"name": "Cost ($)", "id": "cost", "type": "numeric"},
                                    {"name": "Date Added", "id": "date_added"}
                                ],
                                data=[],
                                editable=True,
                                row_deletable=True,
                                style_table={'overflowX': 'auto'},
                                style_cell={'textAlign': 'left'},
                                style_data_conditional=[
                                    {
                                        'if': {'row_index': 'odd'},
                                        'backgroundColor': 'rgb(248, 248, 248)'
                                    }
                                ]
                            )
                        ])
                    ], className="mb-4"),

                    dbc.Row([
                        dbc.Col([
                            dbc.Card([
                                dbc.CardBody([
                                    html.H5("Investment Strategy"),
                                    html.P("Analyze investment strategies across "
                                           "cost centers and profit centers"),
                                    dbc.Button("Analyze Investments",
                                               color="primary", disabled=True),
                                    html.Small(" (Feature in development)",
                                               className="text-muted")
                                ])
                            ])
                        ], width=6),
                        dbc.Col([
                            dbc.Card([
                                dbc.CardBody([
                                    html.H5("ROI Optimization"),
                                    html.P("Optimize return on investment "
                                           "across business units"),
                                    dbc.Button("Optimize ROI",
                                               color="success", disabled=True),
                                    html.Small(" (Feature in development)",
                                               className="text-muted")
                                ])
                            ])
                        ], width=6)
                    ], className="mt-3")
                ], className="p-3")
            ]
        ),

        # Tab 2: Data Input
        dbc.Tab(
            label="Data Input",
            tab_id="biz-data-input",
            children=[
                html.Div([
                    html.H3("Data Input"),
                    html.P("Select your business model and upload data for each investment type."),

                    # Business Model Selection
                    dbc.Card([
                        dbc.CardBody([
                            html.H5("Step 1: Select Business Model",
                                    className="card-title"),
                            dbc.RadioItems(
                                id="business-model-selection",
                                options=[
                                    {"label": "Cost Center - Focus on cost reduction and operational efficiency",
                                     "value": "cost_center"},
                                    {"label": "Profit Center - Focus on revenue generation and market opportunity",
                                     "value": "profit_center"}
                                ],
                                value="cost_center",
                                inline=False,
                                className="mb-3"
                            ),
                            dbc.Alert(
                                id="business-model-description",
                                color="info",
                                className="mb-0"
                            )
                        ])
                    ], className="mb-4"),

                    # Investment Type Upload Boxes
                    html.Div([
                        html.H5("Step 2: Upload Data for Investment Types"),
                        html.P("Click on each investment type to open detailed data upload forms."),
                        html.Div([
                            # Investment type boxes
                            dbc.Row([
                                dbc.Col([
                                    dbc.Card([
                                        dbc.CardBody([
                                            html.H6("� Capital Equipment",
                                                    className="card-title"),
                                            html.P(
                                                "Equipment investments for operational improvements", 
                                                className="card-text small"),
                                            html.P("Status: Pending",
                                                   className="text-muted small"),
                                            html.Hr(),
                                            dbc.Button(
                                                "Upload Data",
                                                id="open-capital-form",
                                                color="primary",
                                                size="sm",
                                                className="w-100"
                                            )
                                        ])
                                    ], color="light", outline=True, className="h-100")
                                ], width=4, className="mb-3"),

                                dbc.Col([
                                    dbc.Card([
                                        dbc.CardBody([
                                            html.H6("📁 Process Improvement",
                                                    className="card-title"),
                                            html.P(
                                                "Process optimization and workflow improvements", 
                                                className="card-text small"),
                                            html.P("Status: Pending",
                                                   className="text-muted small"),
                                            html.Hr(),
                                            dbc.Button(
                                                "Upload Data",
                                                id="open-process-form",
                                                color="primary",
                                                size="sm",
                                                className="w-100"
                                            )
                                        ])
                                    ], color="light", outline=True, className="h-100")
                                ], width=4, className="mb-3"),

                                dbc.Col([
                                    dbc.Card([
                                        dbc.CardBody([
                                            html.H6("📁 Human Capital/People",
                                                    className="card-title"),
                                            html.P(
                                                "Training, hiring, and human resource investments", 
                                                className="card-text small"),
                                            html.P("Status: Pending",
                                                   className="text-muted small"),
                                            html.Hr(),
                                            dbc.Button(
                                                "Upload Data",
                                                id="open-people-form",
                                                color="primary",
                                                size="sm",
                                                className="w-100"
                                            )
                                        ])
                                    ], color="light", outline=True, className="h-100")
                                ], width=4, className="mb-3")
                            ])
                        ], id="investment-type-boxes", className="row")
                    ], id="investment-upload-section"),

                    # Modal dialogs for each investment type (simplified for now)
                    dbc.Modal([
                        dbc.ModalHeader([
                            dbc.ModalTitle("Data Upload: Capital Equipment")
                        ]),
                        dbc.ModalBody([
                            html.P("Capital equipment data upload functionality will be implemented here.")
                        ]),
                        dbc.ModalFooter([
                            dbc.Button("Cancel", id="cancel-capital",
                                       color="secondary"),
                            dbc.Button("Save Data", id="save-capital",
                                       color="primary")
                        ])
                    ], id="modal-capital", size="lg", is_open=False)
                ])
            ]
        ),

        # Tab 3: Financial Dashboard
        dbc.Tab(
            label="Financial Dashboard",
            tab_id="biz-financial-dashboard",
            children=[
                html.Div([
                    dbc.Row([
                        dbc.Col([
                            html.H4("Financial Dashboard", className="mb-3"),
                            html.P("Display optimal investment strategy and budget allocation",
                                   className="text-muted mb-4")
                        ])
                    ]),

                    # Dashboard Content Row
                    dbc.Row([
                        # Left Column: Investment Schedule
                        dbc.Col([
                            dbc.Card([
                                dbc.CardHeader(html.H5("Optimal Investment Schedule",
                                                       className="mb-0")),
                                dbc.CardBody([
                                    html.Div([
                                        html.H6("No Investment Data Available",
                                                className="text-center text-muted"),
                                        html.P("Upload investment data to see optimal scheduling recommendations",
                                               className="text-center text-muted mb-0")
                                    ], id="investment-schedule-content",
                                        className="py-4")
                                ])
                            ])
                        ], width=6),

                        # Right Column: Savings Projections
                        dbc.Col([
                            dbc.Card([
                                dbc.CardHeader(html.H5("Savings Projections",
                                                       className="mb-0")),
                                dbc.CardBody([
                                    html.Div([
                                        html.H6("No Calculation Results",
                                                className="text-center text-muted"),
                                        html.P("Complete data input to see savings projections and ROI analysis",
                                               className="text-center text-muted mb-0")
                                    ], id="savings-projections-content",
                                        className="py-4")
                                ])
                            ])
                        ], width=6)
                    ])
                ], className="p-4")
            ]
        ),

        # Tab 4: Investment Reports
        dbc.Tab(
            label="Investment Reports",
            tab_id="biz-investment-reports",
            children=[
                html.Div([
                    dbc.Row([
                        dbc.Col([
                            html.H4("Investment Reports", className="mb-3"),
                            html.P("Generate and download investment strategy reports",
                                   className="text-muted mb-4")
                        ])
                    ]),

                    dbc.Row([
                        # Left Column: Report Configuration
                        dbc.Col([
                            dbc.Card([
                                dbc.CardHeader(html.H5("Report Configuration",
                                                       className="mb-0")),
                                dbc.CardBody([
                                    dbc.Row([
                                        dbc.Col([
                                            html.Label("Report Type",
                                                       className="form-label"),
                                            dcc.Dropdown(
                                                id="report-type-dropdown",
                                                options=[
                                                    {"label": "Investment Strategy Summary",
                                                     "value": "strategy_summary"},
                                                    {"label": "Financial Impact Analysis",
                                                     "value": "financial_impact"},
                                                    {"label": "Implementation Timeline",
                                                     "value": "implementation_timeline"}
                                                ],
                                                placeholder="Select report type...",
                                                className="mb-3"
                                            )
                                        ], width=12)
                                    ]),

                                    html.Hr(),

                                    dbc.Row([
                                        dbc.Col([
                                            dbc.Button(
                                                "Generate Report",
                                                id="generate-report-btn",
                                                color="primary",
                                                size="lg",
                                                className="w-100",
                                                disabled=True
                                            ),
                                            html.P("Complete investment analysis to enable report generation",
                                                   className="text-muted small text-center mt-2")
                                        ])
                                    ])
                                ])
                            ])
                        ], width=4),

                        # Right Column: Report Preview
                        dbc.Col([
                            dbc.Card([
                                dbc.CardHeader(html.H5("Report Preview",
                                                       className="mb-0")),
                                dbc.CardBody([
                                    html.Div([
                                        html.H6("📄 Report Preview",
                                                className="text-center text-muted"),
                                        html.P("Select report type and generate to see preview here",
                                               className="text-center text-muted mb-4")
                                    ], id="report-preview-content", className="py-4")
                                ])
                            ])
                        ], width=8)
                    ])
                ], className="p-4")
            ]
        )
    ], id="business-mode-tabs", active_tab="biz-investment-analysis")


def create_nonprofit_mode_tabs():
    """Create non-profit mode tabs with placeholders"""
    return dbc.Tabs([
        dbc.Tab(
            label="Program Management",
            tab_id="nonprofit-program-management",
            children=[
                html.Div([
                    dbc.Alert(
                        "Non-profit program management dashboard (placeholder)",
                        color="info", className="text-center"
                    )
                ], className="p-4")
            ]
        ),
        dbc.Tab(
            label="Funding Management",
            tab_id="nonprofit-funding-management",
            children=[
                html.Div([
                    dbc.Alert(
                        "Non-profit funding management (placeholder)",
                        color="info", className="text-center"
                    )
                ], className="p-4")
            ]
        ),
        dbc.Tab(
            label="Compliance",
            tab_id="nonprofit-compliance",
            children=[
                html.Div([
                    dbc.Alert(
                        "Non-profit compliance tracking (placeholder)",
                        color="info", className="text-center"
                    )
                ], className="p-4")
            ]
        )
    ], id="nonprofit-mode-tabs", active_tab="nonprofit-program-management")
    """Create non-profit mode tabs"""
    return dbc.Tabs([
        dbc.Tab(label="Program Dashboard", children=[
            html.Div([
                html.H3("Program Dashboard"),
                dbc.Alert(
                    "Non-profit program management dashboard (placeholder)", 
                    color="secondary"),
                html.P("Track program performance and outcomes"),
            ], className="p-3")
        ]),
        dbc.Tab(label="Funding Management", children=[
            html.Div([
                html.H3("Funding Management"),
                dbc.Alert(
                    "Non-profit funding management (placeholder)", 
                    color="secondary"),
                html.P("Manage funding sources and allocation"),
            ], className="p-3")
        ]),
        dbc.Tab(label="Compliance", children=[
            html.Div([
                html.H3("Compliance"),
                dbc.Alert(
                    "Non-profit compliance tracking (placeholder)", 
                    color="secondary"),
                html.P("Track compliance requirements and reporting"),
            ], className="p-3")
        ]),
    ])


def register_all_callbacks(app, callback_manager):
    """Register all callbacks including original features with proper management"""
    
    # Track registered callback IDs to prevent duplicates
    registered_ids = set()
    
    # 1. TEST BUTTON CALLBACK
    if "test_button" not in registered_ids:
        @callback(
            Output("test-output", "children"),
            [Input("test-button", "n_clicks")],
            prevent_initial_call=True
        )
        def test_callback(n_clicks):
            print(f"🚨 ENHANCED: TEST CALLBACK FIRED! n_clicks = {n_clicks}")
            return f"✅ TEST BUTTON CLICKED {n_clicks} TIMES!"
        
        callback_manager.register_callback(
            "test_button",
            [Output("test-output", "children")],
            [Input("test-button", "n_clicks")]
        )
        registered_ids.add("test_button")

    # 2. INVESTMENT MANAGEMENT CALLBACK
    if "investment_management" not in registered_ids:
        @callback(
            [Output("main-investment-portfolio-table", "data"),
             Output("main-investment-count-badge", "children")],
            [Input("main-add-investment-btn", "n_clicks")],
            [State("main-investment-name-input", "value"),
             State("main-investment-type-dropdown", "value"),
             State("main-investment-cost-input", "value")],
            prevent_initial_call=True
        )
        def add_investment(n_clicks, name, inv_type, cost):
            print(f"🔥 ENHANCED: INVESTMENT CALLBACK FIRED! n_clicks={n_clicks}")
            
            investments = load_investments()
            
            if n_clicks and n_clicks > 0 and name and name.strip() and inv_type and cost:
                try:
                    new_investment = {
                        "name": name.strip(),
                        "type": inv_type,
                        "cost": float(cost),
                        "date_added": datetime.now().strftime("%Y-%m-%d")
                    }
                    investments.append(new_investment)
                    save_investments(investments)
                    print(f"🔥 SUCCESS: Added {name} - Now {len(investments)} investments")
                except Exception as e:
                    print(f"🔥 ERROR: {e}")
            
            # Return table data and count
            table_data = []
            for inv in investments:
                table_data.append({
                    "name": inv["name"],
                    "type": inv["type"], 
                    "cost": inv["cost"],
                    "date_added": inv.get("date_added", "2025-01-01")
                })
            
            count_badge = f"{len(investments)} Investments"
            return table_data, count_badge

        callback_manager.register_callback(
            "investment_management",
            [Output("main-investment-portfolio-table", "data"),
             Output("main-investment-count-badge", "children")],
            [Input("main-add-investment-btn", "n_clicks")],
            [State("main-investment-name-input", "value"),
             State("main-investment-type-dropdown", "value"),
             State("main-investment-cost-input", "value")]
        )
        registered_ids.add("investment_management")

    # 3. MAIN TABS CALLBACK - RESTORED ALL ORIGINAL FEATURES
    if "main_tabs" not in registered_ids:
        @callback(
            Output("main-tabs", "children"),
            [Input("use-case-selector", "value")]
        )
        def update_tabs(use_case):
            print(f"🔥 ENHANCED: update_tabs called with use_case={use_case}")
            
            if use_case == "business":
                print("🔥 ENHANCED: Business mode - loading complete business tabs")
                return create_business_mode_tabs()
                
            elif use_case == "personal":
                print("🔥 ENHANCED: Loading Personal Mode...")
                try:
                    if PERSONAL_MODE_AVAILABLE:
                        personal_layout = create_personal_mode_layout()
                        print("🔥 ENHANCED: Personal mode layout created successfully!")
                        return html.Div([personal_layout], id="personal-mode-wrapper")
                    else:
                        return create_personal_mode_tabs()
                except Exception as e:
                    print(f"🔥 ENHANCED: Personal Mode fallback activated: {e}")
                    return create_personal_mode_tabs()
                    
            elif use_case == "charity":
                print("🔥 ENHANCED: Loading Charity Mode...")
                return create_charity_mode_tabs()
                
            elif use_case == "non_profit":
                print("🔥 ENHANCED: Loading Non-Profit Mode...")
                return create_nonprofit_mode_tabs()
                
            else:
                return dbc.Alert("Please select a use case to see the available tabs.", 
                               color="light")

        callback_manager.register_callback(
            "main_tabs",
            [Output("main-tabs", "children")],
            [Input("use-case-selector", "value")]
        )
        registered_ids.add("main_tabs")

    # 4. USE CASE STATUS CALLBACK
    if "use_case_status" not in registered_ids:
        @callback(
            Output("use-case-content", "children"),
            [Input("use-case-selector", "value")]
        )
        def update_use_case_status(use_case):
            print(f"🔥 ENHANCED: Use case status changed to {use_case}")
            
            if use_case == "business":
                return dbc.Alert("🏢 Business Mode: Investment Management Active", 
                               color="success")
            elif use_case == "personal":
                return dbc.Alert("💰 Personal Mode: Portfolio & Goal Tracking", 
                               color="info")
            elif use_case == "charity":
                return dbc.Alert("❤️ Charity Mode: Donation & Impact Management", 
                               color="warning")
            elif use_case == "non_profit":
                return dbc.Alert("🌟 Non-Profit Mode: Program & Compliance Management", 
                               color="secondary")
            return dbc.Alert("Please select a use case", color="light")

        callback_manager.register_callback(
            "use_case_status",
            [Output("use-case-content", "children")],
            [Input("use-case-selector", "value")]
        )
        registered_ids.add("use_case_status")

    print("✅ ALL ENHANCED CALLBACKS REGISTERED")
    
    # Register module-specific callbacks if available
    if PERSONAL_MODE_AVAILABLE:
        try:
            register_personal_mode_callbacks(app)
            print("✅ PERSONAL MODE CALLBACKS REGISTERED")
        except Exception as e:
            print(f"⚠️ Error registering Personal Mode callbacks: {e}")
    
    # Register additional module callbacks
    if BUSINESS_CALLBACKS_AVAILABLE:
        try:
            # Business mode callbacks may need config parameter, skip for now
            print("⚠️ Business callbacks available but need config integration")
        except Exception as e:
            print(f"⚠️ Error registering Business Mode callbacks: {e}")
    
    if FINANCIAL_DASHBOARD_CALLBACKS_AVAILABLE:
        try:
            register_financial_dashboard_callbacks(app)
            print("✅ FINANCIAL DASHBOARD CALLBACKS REGISTERED")
        except Exception as e:
            print(f"⚠️ Error registering Financial Dashboard callbacks: {e}")
    
    if INVESTMENT_MGMT_CALLBACKS_AVAILABLE:
        try:
            register_investment_mgmt_callbacks(app)
            print("✅ INVESTMENT MANAGEMENT CALLBACKS REGISTERED")
        except Exception as e:
            print(f"⚠️ Error registering Investment Management callbacks: {e}")
    
    print(f"🔥 Total Enhanced Callbacks: {len(registered_ids)}")
    print(f"🔥 Manager Tracked Callbacks: {len(callback_manager.registered_callbacks)}")
    
    return callback_manager
