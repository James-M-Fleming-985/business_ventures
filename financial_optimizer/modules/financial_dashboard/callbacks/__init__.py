from typing import Any, Dict, List, Optional, Tuple, Union, cast
from dash import Dash, html, dcc, Input, Output, State, callback_context
from dash._callback import NoUpdate
from dash.development.base_component import Component
import dash
import uuid
import json

def register_financial_dashboard_callbacks(app: Dash) -> None:
    """Register all callbacks related to dashboard layout management."""
    
    @app.callback(
        [Output('financial-dashboard-grid', 'children', allow_duplicate=True),
         Output('financial-dashboard-grid', 'layouts', allow_duplicate=True)],
        Input('add-chart-btn', 'n_clicks'),
        [State('financial-dashboard-grid', 'children'),
         State('financial-dashboard-grid', 'layouts')],
        prevent_initial_call=True
    )
    def add_new_chart(
        n_clicks: Optional[int], 
        current_children: List[html.Div], 
        current_layouts: Dict[str, List[Dict[str, Any]]]
    ) -> Tuple[Union[List[html.Div], NoUpdate], Union[Dict[str, List[Dict[str, Any]]], NoUpdate]]:
        """Add a new chart to the dashboard"""
        if not n_clicks:
            return dash.no_update, dash.no_update
    
        # Generate a unique ID for the new chart
        chart_id = f'new-chart-{str(uuid.uuid4())[:8]}'
        
        # Create new chart
        new_chart = html.Div([
                html.H5("New Chart", className="chart-title"),
                html.Button("×", className="close-btn", id={'type': 'close-btn', 'id': f"close-{chart_id}"}),
                html.Button("×", className="close-btn", id=f"close-{chart_id}"),
                dcc.Dropdown(
                    id=f'chart-type-{chart_id}',
                    options=[
                        {'label': 'Line Chart', 'value': 'line'},
                        {'label': 'Bar Chart', 'value': 'bar'},
                        {'label': 'Pie Chart', 'value': 'pie'}
                    ],  # type: ignore[arg-type]
                    value='line',
                    clearable=False,
                    className="mb-2"
                ),
                dcc.Graph(
                    id=f'chart-{chart_id}',
                    figure={
                        'data': [{'x': [1, 2, 3], 'y': [4, 1, 2], 'type': 'bar'}],
                        'layout': {
                            'title': 'New Chart',
                            'margin': {'l': 40, 'r': 20, 't': 40, 'b': 30}
                        }
                    },
                    config={'displayModeBar': False},
                    style={"height": "100%", "width": "100%"}
                )
            ], key=chart_id, className="grid-item")
        
        # Add new chart to children
        new_children = current_children + [new_chart]
        
        # Add new chart to layouts
        new_layouts = {}
        for breakpoint, layout in current_layouts.items():
            # Find the maximum y position
            max_y = 0
            for item in layout:
                item_bottom = item['y'] + item['h']
                if item_bottom > max_y:
                    max_y = item_bottom
            
            # Add the new chart at the bottom
            new_layouts[breakpoint] = layout + [{
                'i': chart_id, 
                'x': 0, 
                'y': max_y, 
                'w': min(6, current_layouts[breakpoint][0]['w']), 
                'h': 6, 
                'minW': 3, 
                'minH': 3
            }]
        
        return new_children, new_layouts

    # Only save layout changes - no circular dependency
    app.clientside_callback(
        """
        function(current_layout) {
            if (current_layout && Object.keys(current_layout).length > 0) {
                return current_layout;
            }
            return window.dash_clientside.no_update;
        }
        """,
        Output('dashboard-layout-store', 'data'),
        Input('financial-dashboard-grid', 'layouts'),
        prevent_initial_call=True
    )

    @app.callback(
        Output('dashboard-layout-store', 'data', allow_duplicate=True),
        Input('reset-layout-btn', 'n_clicks'),
        prevent_initial_call=True
    )
    def reset_layout(n_clicks: Optional[int]) -> Union[Dict[str, Any], NoUpdate]:
        """Reset the layout to default when button is clicked"""
        if n_clicks:
            return {
                'lg': [
                    {'i': 'budget-allocation', 'x': 0, 'y': 0, 'w': 6, 'h': 6, 'minW': 4, 'minH': 4},
                    {'i': 'savings-over-time', 'x': 6, 'y': 0, 'w': 6, 'h': 6, 'minW': 4, 'minH': 4},
                    {'i': 'metrics-panel', 'x': 0, 'y': 6, 'w': 12, 'h': 3, 'minW': 6, 'minH': 3},
                    {'i': 'overview-chart', 'x': 0, 'y': 9, 'w': 12, 'h': 6, 'minW': 6, 'minH': 4},
                ],
                'md': [
                    {'i': 'budget-allocation', 'x': 0, 'y': 0, 'w': 5, 'h': 6},
                    {'i': 'savings-over-time', 'x': 5, 'y': 0, 'w': 5, 'h': 6},
                    {'i': 'metrics-panel', 'x': 0, 'y': 6, 'w': 10, 'h': 3},
                    {'i': 'overview-chart', 'x': 0, 'y': 9, 'w': 10, 'h': 6},
                ],
                'sm': [
                    {'i': 'budget-allocation', 'x': 0, 'y': 0, 'w': 6, 'h': 6},
                    {'i': 'savings-over-time', 'x': 0, 'y': 6, 'w': 6, 'h': 6},
                    {'i': 'metrics-panel', 'x': 0, 'y': 12, 'w': 6, 'h': 3},
                    {'i': 'overview-chart', 'x': 0, 'y': 15, 'w': 6, 'h': 6},
                ]
            }
        return dash.no_update
    @app.callback(
        [Output('financial-dashboard-grid', 'children', allow_duplicate=True),
         Output('financial-dashboard-grid', 'layouts', allow_duplicate=True)],
        [Input('close-budget-allocation', 'n_clicks'),
         Input('close-savings-chart', 'n_clicks'),
         Input('close-metrics-panel', 'n_clicks'),
         Input('close-overview-chart', 'n_clicks')],
        [State('financial-dashboard-grid', 'children'),
         State('financial-dashboard-grid', 'layouts')],
        prevent_initial_call=True
    )
    def remove_static_chart(
        close_budget: Optional[int], 
        close_savings: Optional[int], 
        close_metrics: Optional[int], 
        close_overview: Optional[int],
        current_children: List[html.Div], 
        current_layouts: Dict[str, List[Dict[str, Any]]]
    ) -> Tuple[Union[List[html.Div], NoUpdate], Union[Dict[str, List[Dict[str, Any]]], NoUpdate]]:
        """Remove a static chart when its close button is clicked"""
        ctx = callback_context
        if not ctx.triggered:
            return dash.no_update, dash.no_update
            
        triggered_id = cast(str, ctx.triggered[0]['prop_id'].split('.')[0])
        
        # Map close button IDs to chart IDs
        chart_map = {
            'close-budget-allocation': 'budget-allocation',
            'close-savings-chart': 'savings-over-time',
            'close-metrics-panel': 'metrics-panel',
            'close-overview-chart': 'overview-chart'
        }
        
        chart_id = chart_map.get(triggered_id)
        if not chart_id:
            return dash.no_update, dash.no_update
        
        # Remove the chart from children
        new_children = [child for child in current_children if child['props']['key'] != chart_id]
        
        # Remove the chart from layouts
        new_layouts = {}
        for breakpoint, layout in current_layouts.items():
            new_layouts[breakpoint] = [item for item in layout if item['i'] != chart_id]
        
        return new_children, new_layouts
    
    @app.callback(
        [Output('financial-dashboard-grid', 'children', allow_duplicate=True),
         Output('financial-dashboard-grid', 'layouts', allow_duplicate=True)],
        Input({'type': 'close-btn', 'id': dash.ALL}, 'n_clicks'),
        [State('financial-dashboard-grid', 'children'),
         State('financial-dashboard-grid', 'layouts')],
        prevent_initial_call=True
    )
    def remove_dynamic_chart(
        n_clicks: List[Optional[int]],
        current_children: List[html.Div], 
        current_layouts: Dict[str, List[Dict[str, Any]]]
    ) -> Tuple[Union[List[html.Div], NoUpdate], Union[Dict[str, List[Dict[str, Any]]], NoUpdate]]:
        """Remove a dynamically added chart when its close button is clicked"""
        ctx = callback_context
        if not ctx.triggered or not any(n_clicks):
            return dash.no_update, dash.no_update
            
        triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
        # Extract the chart ID from the close button ID (e.g., 'close-new-chart-12345678')
        if not triggered_id.startswith('{'):
            return dash.no_update, dash.no_update
            
        button_id = json.loads(triggered_id)
        chart_id = button_id['id'].replace('close-', '')
        
        # Remove the chart from children
        new_children = [child for child in current_children if child['props']['key'] != chart_id]
        
        # Remove the chart from layouts
        new_layouts = {}
        for breakpoint, layout in current_layouts.items():
            new_layouts[breakpoint] = [item for item in layout if item['i'] != chart_id]
        
        return new_children, new_layouts
