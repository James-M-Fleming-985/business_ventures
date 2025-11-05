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
    
    # Calculate circular positions
    angles = [i * 2 * math.pi / n for i in range(n)]
    node_x = [math.cos(a) for a in angles]
    node_y = [math.sin(a) for a in angles]
    
    # Generate edges (connections above threshold)
    edge_x = []
    edge_y = []
    connections = [0] * n  # Count connections for each node
    
    for i in range(n):
        for j in range(i+1, n):
            # Random correlation
            r = abs(np.random.uniform(-1, 1))
            if r >= threshold:
                # Add edge
                edge_x.extend([node_x[i], node_x[j], None])
                edge_y.extend([node_y[i], node_y[j], None])
                connections[i] += 1
                connections[j] += 1
    
    # Node sizes based on connections
    node_sizes = [15 + c * 5 for c in connections]
    
    # Node colors based on connection count
    max_conn = max(connections) if connections else 1
    node_colors = [f'rgba({int(59 + (c/max_conn)*100)}, {int(130 - (c/max_conn)*50)}, {int(246 - (c/max_conn)*100)}, 0.8)' 
                   for c in connections]
    
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
            "y": edge_y
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
