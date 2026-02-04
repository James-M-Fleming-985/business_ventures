"""
Dashboard Router for Causal Affect Platform
Provides API endpoints for dashboard visualizations
"""

from fastapi import APIRouter, Request, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from typing import Optional
import numpy as np
from datetime import datetime, timedelta
import math

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])
templates = Jinja2Templates(directory="templates")


@router.get("/stats")
async def get_dashboard_stats():
    """Get quick statistics for dashboard header"""
    # TODO: Replace with real data from database/cache
    return {
        "dataPoints": 1250,
        "strongCorrelations": 18,
        "apiSources": 8,
        "lastUpdated": datetime.now().strftime("%H:%M:%S")
    }


@router.get("/heatmap")
async def get_heatmap_data():
    """Get correlation matrix data for heatmap visualization"""
    # Use clear, descriptive variable names
    labels = [
        "GDP Growth (%)",
        "S&P 500 Index",
        "Global Temp (°C)",
        "Earthquake Count",
        "Published Papers",
        "Clinical Trials"
    ]
    
    # Generate correlation matrix (symmetric)
    n = len(labels)
    matrix = []
    for i in range(n):
        row = []
        for j in range(n):
            if i == j:
                row.append(1.0)
            elif i < j:
                # Generate deterministic correlation based on variable pair
                seed_val = (i * 100 + j * 10) % 89
                np.random.seed(seed_val)
                r = np.random.uniform(-0.8, 0.95)
                row.append(round(r, 3))
            else:
                # Mirror from upper triangle
                row.append(matrix[j][i])
        matrix.append(row)
    
    return {
        "labels": labels,
        "matrix": matrix
    }


@router.get("/timeseries")
async def get_timeseries_data(metric: str = Query("all")):
    """Get time series data for trend visualization"""
    # Generate 90 days of demo data
    dates = []
    today = datetime.now()
    for i in range(90):
        date = today - timedelta(days=89-i)
        dates.append(date.strftime("%Y-%m-%d"))
    
    # Create multiple series with clear names and realistic varied patterns
    series = [
        {
            "name": "GDP Growth (%)",
            "dates": dates,
            "values": [
                2.5 + math.sin(i/10) * 0.5 + np.random.normal(0, 0.15)
                for i in range(90)
            ]
        },
        {
            "name": "S&P 500 Index",
            "dates": dates,
            "values": [
                100 + math.cos(i/8) * 15 - i * 0.2 + np.random.normal(0, 3)
                for i in range(90)
            ]
        },
        {
            "name": "Global Temp (°C)",
            "dates": dates,
            "values": [
                15.5 + math.sin(i/20) * 0.8 + i * 0.01 + np.random.normal(0, 0.2)
                for i in range(90)
            ]
        },
        {
            "name": "Earthquake Count",
            "dates": dates,
            "values": [
                50 + math.sin(i/12) * 15 + np.random.normal(0, 8)
                for i in range(90)
            ]
        },
        {
            "name": "Published Papers",
            "dates": dates,
            "values": [
                1000 + i * 8 + math.cos(i/15) * 50 + np.random.normal(0, 30)
                for i in range(90)
            ]
        },
        {
            "name": "Clinical Trials",
            "dates": dates,
            "values": [
                500 + i * 3 - math.sin(i/10) * 20 + np.random.normal(0, 15)
                for i in range(90)
            ]
        }
    ]
    
    # Filter by metric if specified
    if metric != "all":
        series = [s for s in series if s["name"] == metric]
    
    return {"series": series}


@router.get("/network")
async def get_network_data(threshold: float = Query(0.5, ge=0, le=1)):
    """Get network graph data for correlation network visualization"""
    # Demo network with circular layout - use clear names
    labels = [
        "GDP Growth (%)",
        "S&P 500",
        "Global Temp (°C)",
        "Earthquakes",
        "Papers",
        "Trials"
    ]
    n = len(labels)
    
    # Fixed correlation matrix (deterministic - won't change on reload)
    # Based on realistic relationships
    correlation_matrix = [
        [1.00, 0.85, 0.42, -0.12, 0.58, 0.65],  # GDP
        [0.85, 1.00, 0.38, -0.08, 0.52, 0.72],  # S&P 500
        [0.42, 0.38, 1.00, 0.25, 0.15, 0.22],   # Temp
        [-0.12, -0.08, 0.25, 1.00, 0.31, 0.18],  # Earthquakes
        [0.58, 0.52, 0.15, 0.31, 1.00, 0.88],   # Papers
        [0.65, 0.72, 0.22, 0.18, 0.88, 1.00]    # Trials
    ]
    
    # Calculate circular positions
    angles = [i * 2 * math.pi / n for i in range(n)]
    node_x = [math.cos(a) for a in angles]
    node_y = [math.sin(a) for a in angles]
    
    # Generate edges (connections above threshold)
    edge_x = []
    edge_y = []
    edge_info = []  # Store edge details for hover
    connections = [0] * n  # Count connections for each node
    
    for i in range(n):
        for j in range(i+1, n):
            r = abs(correlation_matrix[i][j])
            if r >= threshold:
                # Add edge
                edge_x.extend([node_x[i], node_x[j], None])
                edge_y.extend([node_y[i], node_y[j], None])
                edge_info.append({
                    "source": labels[i],
                    "target": labels[j],
                    "r": correlation_matrix[i][j],
                    "abs_r": r
                })
                connections[i] += 1
                connections[j] += 1
    
    # Node sizes based on connections
    node_sizes = [15 + c * 5 for c in connections]
    
    # Node colors: blue=positive hub, purple=mixed, gray=isolated
    node_colors = []
    for i, c in enumerate(connections):
        if c >= 4:  # Hub node
            node_colors.append('#3b82f6')  # Blue
        elif c >= 2:  # Medium connections
            node_colors.append('#8b5cf6')  # Purple
        else:  # Isolated
            node_colors.append('#64748b')  # Gray
    
    return {
        "nodes": {
            "x": node_x,
            "y": node_y,
            "labels": labels,
            "sizes": node_sizes,
            "colors": node_colors
        },
        "edges": {
            "x": edge_x,
            "y": edge_y,
            "info": edge_info
        }
    }


@router.get("/leaderboard")
async def get_leaderboard_data(sort: str = Query("strength")):
    """Get top correlations for leaderboard table"""
    # Use clear variable names
    variables = [
        "GDP Growth (%)",
        "S&P 500 Index",
        "Global Temp (°C)",
        "Earthquake Count",
        "Published Papers",
        "Clinical Trials"
    ]
    correlations = []
    
    for i in range(len(variables)):
        for j in range(i+1, len(variables)):
            # Deterministic correlations based on variable pair
            seed_val = (i * 100 + j * 10) % 89
            np.random.seed(seed_val)
            r = np.random.uniform(-0.95, 0.95)
            p = abs(np.random.uniform(0.001, 0.15))
            correlations.append({
                "var1": variables[i],
                "var2": variables[j],
                "r": round(r, 3),
                "p": round(p, 4)
            })
    
    # Sort based on parameter
    if sort == "strength":
        correlations.sort(key=lambda x: abs(x["r"]), reverse=True)
    elif sort == "positive":
        correlations = [c for c in correlations if c["r"] > 0]
        correlations.sort(key=lambda x: x["r"], reverse=True)
    elif sort == "negative":
        correlations = [c for c in correlations if c["r"] < 0]
        correlations.sort(key=lambda x: x["r"])
    
    # Return top 20
    return {"correlations": correlations[:20]}


@router.get("/relationship/{var1}/{var2}")
async def get_relationship_details(var1: str, var2: str):
    """Get detailed relationship analysis for modal"""
    # Generate correlation value (deterministic based on variable names)
    seed_value = sum(ord(c) for c in var1 + var2) % 100
    np.random.seed(seed_value)
    
    r = np.random.uniform(0.5, 0.95) * (1 if seed_value % 2 == 0 else -1)
    p_value = np.random.uniform(0.0001, 0.05)
    
    # Generate realistic scatter data with correlation
    n_points = 50
    x_data = np.random.uniform(50, 150, n_points)
    noise = np.random.normal(0, 15, n_points)
    y_data = r * x_data + (1 - abs(r)) * 50 + noise
    
    # Generate time series data (30 days historical + 30 days forecast)
    dates_hist = [(datetime.now() - timedelta(days=30-i)).strftime("%Y-%m-%d") for i in range(30)]
    dates_fore = [(datetime.now() + timedelta(days=i+1)).strftime("%Y-%m-%d") for i in range(30)]
    
    # Historical time series with correlation
    base1 = np.linspace(80, 110, 30) + np.random.normal(0, 5, 30)
    base2 = r * base1 + (1 - abs(r)) * 20 + np.random.normal(0, 5, 30)
    
    # Forecast with trend continuation
    trend1 = (base1[-1] - base1[-10]) / 10
    trend2 = (base2[-1] - base2[-10]) / 10
    forecast1 = [base1[-1] + trend1 * (i+1) + np.random.normal(0, 2) for i in range(30)]
    forecast2 = [base2[-1] + trend2 * (i+1) + np.random.normal(0, 2) for i in range(30)]
    
    # Calculate stability (how consistent correlation is over time windows)
    window_corrs = []
    for i in range(0, 20, 5):
        window_r = np.corrcoef(base1[i:i+10], base2[i:i+10])[0, 1]
        window_corrs.append(window_r)
    stability = (1 - np.std(window_corrs)) * 100
    
    # Generate natural language explanation
    abs_r = abs(r)
    strength = "strong" if abs_r >= 0.7 else "moderate" if abs_r >= 0.4 else "weak"
    direction = "positive" if r > 0 else "negative"
    sig_level = "highly significant" if p_value < 0.001 else "significant" if p_value < 0.01 else "marginally significant"
    
    explanation = (
        f"There is a {strength} {direction} correlation between {var1} and {var2} "
        f"(r = {r:.3f}, p = {p_value:.4f}). This relationship is {sig_level}, "
        f"indicating it is unlikely to be due to random chance. "
        f"When {var1} {'increases' if r > 0 else 'decreases'}, {var2} tends to "
        f"{'increase' if r > 0 else 'decrease'} as well. The correlation has been "
        f"stable over time (stability: {stability:.1f}%), suggesting a consistent "
        f"relationship between these variables."
    )
    
    return {
        "var1": var1,
        "var2": var2,
        "correlation": round(r, 3),
        "p_value": p_value,
        "strength": strength,
        "direction": direction,
        "stability": f"{stability:.1f}%",
        "explanation": explanation,
        "scatter_data": {
            "x": x_data.tolist(),
            "y": y_data.tolist()
        },
        "timeseries": {
            "historical": {
                "dates": dates_hist,
                "var1": base1.tolist(),
                "var2": base2.tolist()
            },
            "forecast": {
                "dates": dates_fore,
                "var1": forecast1,
                "var2": forecast2
            }
        },
        "metrics": {
            "n_points": n_points,
            "mean_x": float(np.mean(x_data)),
            "mean_y": float(np.mean(y_data)),
            "std_x": float(np.std(x_data)),
            "std_y": float(np.std(y_data))
        }
    }

@router.get("/fast-signals")
async def get_fast_signals():
    """
    Get Layer 1 Fast Signals with momentum indicators.
    These are behavioral signals (Wikipedia pageviews, Reddit activity, etc.)
    that move faster than market/economic data.
    """
    from database import get_db_session
    from models import VariableMetadata, TimeSeriesData
    from sqlalchemy import func, desc
    
    signals = []
    
    try:
        with get_db_session() as db:
            # Get all Layer 1 (Wikipedia) variables
            layer1_vars = db.query(VariableMetadata).filter(
                VariableMetadata.source == 'wikipedia',
                VariableMetadata.is_active == True
            ).all()
            
            for var in layer1_vars:
                # Get recent data points to calculate momentum
                recent_data = db.query(TimeSeriesData).filter(
                    TimeSeriesData.variable_id == var.id
                ).order_by(desc(TimeSeriesData.timestamp)).limit(6).all()
                
                if len(recent_data) >= 2:
                    # Calculate month-over-month momentum
                    current = recent_data[0].value
                    previous = recent_data[1].value
                    momentum = ((current - previous) / max(previous, 1)) * 100
                else:
                    momentum = 0
                
                signals.append({
                    'name': var.name,
                    'display_name': var.display_name,
                    'momentum': round(momentum, 1),
                    'layer': 1,
                    'source': var.source,
                    'has_data': len(recent_data) > 0
                })
            
            # Sort by absolute momentum (most active first)
            signals.sort(key=lambda x: abs(x['momentum']), reverse=True)
            
            # Generate top insight
            top_insight = None
            if signals:
                top_signal = signals[0]
                direction = 'surging' if top_signal['momentum'] > 10 else 'rising' if top_signal['momentum'] > 0 else 'declining'
                top_insight = {
                    'title': f"Top Signal: {top_signal['display_name']}",
                    'description': f"{top_signal['display_name']} is {direction} with {abs(top_signal['momentum']):.1f}% momentum. "
                                   f"This Layer 1 behavioral signal may predict upcoming Layer 2 market movements."
                }
            
            return {
                'signals': signals[:10],  # Top 10 most active
                'total_layer1_variables': len(layer1_vars),
                'top_insight': top_insight
            }
            
    except Exception as e:
        import logging
        logging.error(f"Failed to load fast signals: {e}")
        
        # Return placeholder if database query fails
        return {
            'signals': [],
            'total_layer1_variables': 0,
            'top_insight': {
                'title': 'Layer 1 Setup Required',
                'description': 'Run POST /api/admin/setup-layer1-fast-signals to add Wikipedia pageview variables for early signal detection.'
            }
        }


@router.get("/cascade-predictions/{signal_name}")
async def get_cascade_predictions(signal_name: str):
    """
    Get Layer 2/3 variables that the selected Layer 1 signal predicts.
    Uses Granger causality results to find predictive relationships.
    """
    from database import get_db_session
    from models import VariableMetadata, CorrelationResult
    from sqlalchemy import or_, and_, desc
    
    predictions = []
    
    try:
        with get_db_session() as db:
            # Find the Layer 1 variable
            layer1_var = db.query(VariableMetadata).filter(
                VariableMetadata.name == signal_name
            ).first()
            
            if not layer1_var:
                return {'predictions': [], 'top_prediction': None, 'optimal_lag': None}
            
            # Find correlations where this variable has Granger causality
            # (meaning Layer 1 signal → Layer 2/3 outcome)
            causality_results = db.query(CorrelationResult).filter(
                or_(
                    and_(
                        CorrelationResult.variable1_id == layer1_var.id,
                        CorrelationResult.granger_p_value_xy != None,
                        CorrelationResult.granger_p_value_xy < 0.05
                    ),
                    and_(
                        CorrelationResult.variable2_id == layer1_var.id,
                        CorrelationResult.granger_p_value_yx != None,
                        CorrelationResult.granger_p_value_yx < 0.05
                    )
                ),
                CorrelationResult.is_significant == True
            ).order_by(desc(CorrelationResult.abs_correlation)).limit(5).all()
            
            for result in causality_results:
                # Determine which variable is the outcome
                if result.variable1_id == layer1_var.id:
                    outcome_var = result.variable2
                    p_value = result.granger_p_value_xy
                else:
                    outcome_var = result.variable1
                    p_value = result.granger_p_value_yx
                
                # Skip if outcome is also Layer 1
                if outcome_var.source == 'wikipedia':
                    continue
                
                predictions.append({
                    'name': outcome_var.name,
                    'display_name': outcome_var.display_name,
                    'direction': 'up' if result.correlation_value > 0 else 'down',
                    'p_value': f"{p_value:.4f}",
                    'lag': result.granger_lags or 14,
                    'correlation': result.correlation_value
                })
            
            # Generate top prediction summary
            top_prediction = None
            optimal_lag = None
            if predictions:
                top = predictions[0]
                top_prediction = f"{layer1_var.display_name} → {top['display_name']} ({top['direction'].upper()})"
                optimal_lag = top['lag']
            
            return {
                'predictions': predictions,
                'top_prediction': top_prediction,
                'optimal_lag': optimal_lag
            }
            
    except Exception as e:
        import logging
        logging.error(f"Failed to load cascade predictions: {e}")
        return {'predictions': [], 'top_prediction': None, 'optimal_lag': None}