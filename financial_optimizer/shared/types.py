# Type definitions for the financial optimizer application

from typing import Dict, List, Any, TypedDict

class PlotlyLayout(TypedDict, total=False):
    """Type definition for Plotly layout configurations"""
    title: str
    xaxis_title: str
    yaxis_title: str
    yaxis_range: List[float]
    template: str
    showlegend: bool
    margin: Dict[str, int]
    hovermode: str
    xaxis: Dict[str, Any]
    yaxis: Dict[str, Any]
    transition_duration: int

class InvestmentMetrics(TypedDict):
    """Type definition for investment metrics"""
    roi: float
    irr: float
    payback_period: float
    npv: float
