# components/financial_inputs.py
from dash import html, dcc, dash_table
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State

def create_input_tabs():
    """Create tabs for financial data input."""
    return html.Div([
        html.H2("Financial Data Input"),
        
        dbc.Tabs([
            dbc.Tab(label="Revenue Streams", id="revenue-streams-tab", children=[
                create_income_input_form()
            ]),
            dbc.Tab(label="Capital Assets", id="capital-assets-tab", children=[
                create_assets_input_form()
            ]),
            dbc.Tab(label="Debt Obligations", id="debt-obligations-tab", children=[
                create_liabilities_input_form()
            ]),
            dbc.Tab(label="Operating Expenses", id="operating-expenses-tab", children=[
                create_expenses_input_form()
            ]),
        ], id="input-tabs"),
        
        html.Div([
            dbc.Button("Import CSV", id="import-csv-button", color="secondary", className="me-2"),
            dbc.Button("Save Data", id="save-data-button", color="secondary", className="me-2"),
            dbc.Button("Calculate Projections", id="calculate-button", color="primary"),
        ], className="mt-4")
    ])

def create_income_input_form():
    """Create input form for revenue streams."""
    return html.Div([
        html.H3(id="income-form-title", children="Revenue Streams"),
        html.Button("+ Add Stream", id="add-income-row", className="mb-3"),
        
        dash_table.DataTable(
            id='income-table',
            columns=[
                {"name": "Revenue Source", "id": "name"},
                {"name": "Monthly Amount (£)", "id": "amount", "type": "numeric"},
                {"name": "Growth Rate (%/year)", "id": "growth", "type": "numeric"}
            ],
            data=[
                {"name": "Product Sales", "amount": 150000, "growth": 4},
                {"name": "Service Revenue", "amount": 75000, "growth": 6}
            ],
            editable=True,
            row_deletable=True,
            style_cell={'textAlign': 'left', 'padding': '10px'},
            style_header={
                'backgroundColor': 'rgb(230, 230, 230)',
                'fontWeight': 'bold'
            }
        )
    ], className="py-3")

def create_assets_input_form():
    """Create input form for capital assets."""
    return html.Div([
        html.H3(id="assets-form-title", children="Capital Assets"),
        html.Button("+ Add Asset", id="add-asset-row", className="mb-3"),
        
        dash_table.DataTable(
            id='assets-table',
            columns=[
                {"name": "Asset Name", "id": "name"},
                {"name": "Current Value (£)", "id": "value", "type": "numeric"},
                {"name": "Return/Growth Rate (%/year)", "id": "return", "type": "numeric"},
                {"name": "Monthly Investment (£)", "id": "contribution", "type": "numeric"}
            ],
            data=[
                {"name": "Cash Reserves", "value": 250000, "return": 1.5, "contribution": 5000},
                {"name": "Equipment", "value": 350000, "return": -10, "contribution": 8000},
                {"name": "Property", "value": 1200000, "return": 3, "contribution": 0}
            ],
            editable=True,
            row_deletable=True,
            style_cell={'textAlign': 'left', 'padding': '10px'},
            style_header={
                'backgroundColor': 'rgb(230, 230, 230)',
                'fontWeight': 'bold'
            }
        )
    ], className="py-3")

def create_liabilities_input_form():
    """Create input form for debt obligations."""
    return html.Div([
        html.H3(id="liabilities-form-title", children="Debt Obligations"),
        html.Button("+ Add Debt", id="add-liability-row", className="mb-3"),
        
        dash_table.DataTable(
            id='liabilities-table',
            columns=[
                {"name": "Obligation Name", "id": "name"},
                {"name": "Current Balance (£)", "id": "balance", "type": "numeric"},
                {"name": "Interest Rate (%)", "id": "rate", "type": "numeric"},
                {"name": "Monthly Payment (£)", "id": "payment", "type": "numeric"}
            ],
            data=[
                {"name": "Business Loan", "balance": 500000, "rate": 4.5, "payment": 9200},
                {"name": "Equipment Financing", "balance": 120000, "rate": 3.8, "payment": 3600}
            ],
            editable=True,
            row_deletable=True,
            style_cell={'textAlign': 'left', 'padding': '10px'},
            style_header={
                'backgroundColor': 'rgb(230, 230, 230)',
                'fontWeight': 'bold'
            }
        )
    ], className="py-3")

def create_expenses_input_form():
    """Create input form for operating expenses."""
    return html.Div([
        html.H3(id="expenses-form-title", children="Operating Expenses"),
        html.Button("+ Add Expense", id="add-expense-row", className="mb-3"),
        
        dash_table.DataTable(
            id='expenses-table',
            columns=[
                {"name": "Category", "id": "category"},
                {"name": "Monthly Amount (£)", "id": "amount", "type": "numeric"},
                {"name": "Essential", "id": "essential"}  # Removed type: boolean to fix error
            ],
            data=[
                {"category": "Payroll", "amount": 85000, "essential": True},
                {"category": "Rent", "amount": 12000, "essential": True},
                {"category": "Utilities", "amount": 5000, "essential": True},
                {"category": "Marketing", "amount": 7500, "essential": False}
            ],
            editable=True,
            row_deletable=True,
            style_cell={'textAlign': 'left', 'padding': '10px'},
            style_header={
                'backgroundColor': 'rgb(230, 230, 230)',
                'fontWeight': 'bold'
            }
        )
    ], className="py-3")

def register_input_callbacks(app):
    """Register callbacks for input components."""
    
    # Callback to add a new row to income table
    @app.callback(
        Output('income-table', 'data'),
        Input('add-income-row', 'n_clicks'),
        State('income-table', 'data'),
        prevent_initial_call=True
    )
    def add_income_row(n_clicks, rows):
        if n_clicks is None:
            return rows
        rows.append({"name": "", "amount": 0, "growth": 0})
        return rows
    
    # Callback to add a new row to assets table
    @app.callback(
        Output('assets-table', 'data'),
        Input('add-asset-row', 'n_clicks'),
        State('assets-table', 'data'),
        prevent_initial_call=True
    )
    def add_asset_row(n_clicks, rows):
        if n_clicks is None:
            return rows
        rows.append({"name": "", "value": 0, "return": 0, "contribution": 0})
        return rows
    
    # Callback to add a new row to liabilities table
    @app.callback(
        Output('liabilities-table', 'data'),
        Input('add-liability-row', 'n_clicks'),
        State('liabilities-table', 'data'),
        prevent_initial_call=True
    )
    def add_liability_row(n_clicks, rows):
        if n_clicks is None:
            return rows
        rows.append({"name": "", "balance": 0, "rate": 0, "payment": 0})
        return rows
    
    # Callback to add a new row to expenses table
    @app.callback(
        Output('expenses-table', 'data'),
        Input('add-expense-row', 'n_clicks'),
        State('expenses-table', 'data'),
        prevent_initial_call=True
    )
    def add_expense_row(n_clicks, rows):
        if n_clicks is None:
            return rows
        rows.append({"category": "", "amount": 0, "essential": False})
        return rows

    # Callback to update investment field options based on app mode
    @app.callback(
        Output('investment-type-input', 'options'),
        Input('app-mode', 'value')
    )
    def update_investment_options(mode):
        if mode == 'business':
            # Business investment options
            return [
                {'label': 'Cash/Working Capital', 'value': 'cash'},
                {'label': 'Equipment/Machinery', 'value': 'equipment'},
                {'label': 'Property/Facilities', 'value': 'property'},
                {'label': 'Research & Development', 'value': 'rd'},
                {'label': 'Marketing/Brand', 'value': 'marketing'},
                {'label': 'IT/Software', 'value': 'it'},
                {'label': 'Training/Human Capital', 'value': 'training'},
                {'label': 'New Staff Onboarding', 'value': 'staffing'}
            ]
        else:
            # Personal investment options
            return [
                {'label': 'Cash/Savings', 'value': 'cash'},
                {'label': 'Stocks/Equities', 'value': 'stocks'},
                {'label': 'Bonds/Fixed Income', 'value': 'bonds'},
                {'label': 'Real Estate', 'value': 'property'},
                {'label': 'Education/Skills', 'value': 'education'},
                {'label': 'Business Venture', 'value': 'business'}
            ]
    
    # Callback to update form labels based on app mode
    @app.callback(
        [Output('income-form-title', 'children'),
         Output('assets-form-title', 'children'),
         Output('liabilities-form-title', 'children'),
         Output('expenses-form-title', 'children'),
         Output('revenue-streams-tab', 'label'),
         Output('capital-assets-tab', 'label'),
         Output('debt-obligations-tab', 'label'),
         Output('operating-expenses-tab', 'label')],
        [Input('app-mode', 'value')]
    )
    def update_form_labels(mode):
        if mode == 'business':
            return (
                "Revenue Streams", 
                "Capital Assets", 
                "Debt Obligations", 
                "Operating Expenses",
                "Revenue Streams",
                "Capital Assets",
                "Debt Obligations",
                "Operating Expenses"
            )
        else:
            return (
                "Income Sources", 
                "Assets", 
                "Liabilities", 
                "Expenses",
                "Income Sources",
                "Assets",
                "Liabilities",
                "Expenses"
            )
        
# Update the existing investment slider to a budget slider

def create_budget_control():
    """Create budget allocation controls."""
    return html.Div([
        # Add the budget label with ID
        html.Label(id="budget-label", children="Investment Budget (£):"),
        
        dcc.Slider(
            id='budget-slider',
            min=0,
            max=1000000,
            step=10000,
            value=250000,
            marks={i: f"£{i/1000}k" for i in range(0, 1100000, 100000)},
            updatemode='drag'  # Add this line
        ),
        
        # Time horizon slider
        html.Div([
            html.Label("Time Horizon (years):"),
            dcc.Slider(
                id='budget-timeframe',
                min=1,
                max=10,
                step=1,
                value=5,
                marks={i: str(i) for i in range(1, 11)},
            )
        ], className="mt-3"),
        
        # Projected savings
        html.Div([
            html.Label("Projected 5-Year Savings:"),
            html.H4(id="projected-savings", children="£0")
        ], className="mt-3"),
        
    ], className="mb-4")

# We can leave the existing create_input_tabs function, but update your main input function
def create_input_section():
    """Create the main input section based on application mode."""
    return html.Div([
        html.Div(id='mode-specific-inputs', children=[
            # This will be populated via callback based on mode
        ])
    ])