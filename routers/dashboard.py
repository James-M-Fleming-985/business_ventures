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
    # TODO: Replace with real correlation analysis
    # For now, return demo data
    labels = [
        "GDP Growth",
        "Stock Market",
        "Global Temp",
        "Earthquakes",
        "Research Papers",
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
                # Generate random correlation for demo
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
    
    # Create multiple series
    series = [
        {
            "name": "GDP Growth",
            "dates": dates,
            "values": [2.5 + math.sin(i/10) + np.random.normal(0, 0.2) for i in range(90)]
        },
        {
            "name": "Stock Index",
            "dates": dates,
            "values": [3.0 + math.cos(i/8) + np.random.normal(0, 0.3) for i in range(90)]
        },
        {
            "name": "Temperature Anomaly",
            "dates": dates,
            "values": [0.8 + math.sin(i/15) + np.random.normal(0, 0.15) for i in range(90)]
        }
    ]
    
    # Filter by metric if specified
    if metric != "all":
        series = [s for s in series if s["name"] == metric]
    
    return {"series": series}


@router.get("/network")
async def get_network_data(threshold: float = Query(0.5, ge=0, le=1)):
    """Get network graph data for correlation network visualization"""
    # Demo network with circular layout
    labels = ["GDP", "Stocks", "Temp", "Quakes", "Papers", "Trials"]
    n = len(labels)
    
    # Fixed correlation matrix (deterministic - won't change on reload)
    # Based on realistic relationships
    correlation_matrix = [
        [1.00, 0.85, 0.42, -0.12, 0.58, 0.65],  # GDP
        [0.85, 1.00, 0.38, -0.08, 0.52, 0.72],  # Stocks
        [0.42, 0.38, 1.00, 0.25, 0.15, 0.22],   # Temp
        [-0.12, -0.08, 0.25, 1.00, 0.31, 0.18], # Quakes
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
    # Generate demo correlations
    variables = ["GDP", "Stock Market", "Temperature", "Earthquakes", "Research Papers", "Clinical Trials"]
    correlations = []
    
    for i in range(len(variables)):
        for j in range(i+1, len(variables)):
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
