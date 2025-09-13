import plotly.graph_objs as go  # type: ignore
from typing import cast, Any

def create_empty_cumulative_chart():
    """Create an empty cumulative chart when no data is available."""
    fig = go.Figure()
    
    # Use cast to Any to bypass the type checking for all Plotly methods
    fig_any = cast(Any, fig)
    fig_any.update_layout(
        title='Investment Savings Over Time',
        xaxis_title='Date',
        yaxis_title='Savings (£)',
        template='plotly_white'
    )
    
    fig_any.add_annotation(
        x=0.5,
        y=0.5,
        xref="paper",
        yref="paper",
        text="No investment data available",
        showarrow=False,
        font=dict(size=14)
    )
    
    return fig