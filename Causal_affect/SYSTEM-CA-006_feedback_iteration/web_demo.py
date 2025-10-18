#!/usr/bin/env python3
"""
Minimal CA-006 Web Demo
A simplified version that runs without database dependencies
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import uvicorn

app = FastAPI(
    title="CA-006 Feedback Collection & Iteration Orchestrator",
    description="System for collecting feedback and managing MVP iterations",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", response_class=HTMLResponse)
async def root():
    """Landing page with system overview"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>CA-006 Feedback Collection System</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 1200px; margin: 50px auto; padding: 20px; }
            h1 { color: #2563eb; }
            .feature { background: #f1f5f9; padding: 15px; margin: 10px 0; border-radius: 8px; }
            .status { color: #10b981; font-weight: bold; }
            .endpoint { background: #1e293b; color: #fff; padding: 5px 10px; border-radius: 4px; font-family: monospace; }
            a { color: #2563eb; text-decoration: none; }
            a:hover { text-decoration: underline; }
        </style>
    </head>
    <body>
        <h1>🎯 CA-006: Feedback Collection & Iteration Orchestrator</h1>
        <p class="status">✅ System Online</p>
        
        <h2>📊 System Features</h2>
        
        <div class="feature">
            <h3>📈 FEATURE-CA-006-01: Analytics Integration</h3>
            <p>Unified analytics from Google Analytics, Mixpanel, and Amplitude</p>
            <p><a href="/api/v1/analytics/demo"><span class="endpoint">GET /api/v1/analytics/demo</span></a></p>
        </div>
        
        <div class="feature">
            <h3>👥 FEATURE-CA-006-02: Engagement Tracking</h3>
            <p>Real-time user engagement metrics and session tracking</p>
            <p><a href="/api/v1/engagement/demo"><span class="endpoint">GET /api/v1/engagement/demo</span></a></p>
        </div>
        
        <div class="feature">
            <h3>💰 FEATURE-CA-006-03: Revenue Tracking</h3>
            <p>Conversion funnel and financial metrics tracking</p>
            <p><a href="/api/v1/revenue/demo"><span class="endpoint">GET /api/v1/revenue/demo</span></a></p>
        </div>
        
        <div class="feature">
            <h3>🎯 FEATURE-CA-006-04: Prioritization Engine</h3>
            <p>Automated scoring and ranking of feedback items</p>
            <p><a href="/api/v1/prioritization/demo"><span class="endpoint">GET /api/v1/prioritization/demo</span></a></p>
        </div>
        
        <div class="feature">
            <h3>🗄️ FEATURE-CA-006-05: Archive Automation</h3>
            <p>Automatic archiving of completed MVPs</p>
            <p><a href="/api/v1/archive/demo"><span class="endpoint">GET /api/v1/archive/demo</span></a></p>
        </div>
        
        <div class="feature">
            <h3>📊 FEATURE-CA-006-06: Dashboard UI</h3>
            <p>Portfolio overview and MVP detail views</p>
            <p><a href="/api/v1/dashboard/demo"><span class="endpoint">GET /api/v1/dashboard/demo</span></a></p>
        </div>
        
        <h2>📚 API Documentation</h2>
        <p><a href="/docs">📖 Interactive API Docs (Swagger UI)</a></p>
        <p><a href="/redoc">📋 API Documentation (ReDoc)</a></p>
        <p><a href="/health">❤️ Health Check</a></p>
        
        <hr>
        <p><small>Built with FastAPI • 7 Features • 30+ Layers</small></p>
    </body>
    </html>
    """

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy", "system": "CA-006", "features": 7, "layers": 30}

@app.get("/api/v1/analytics/demo")
async def analytics_demo():
    """Demo analytics data"""
    return {
        "mvp_id": "MVP-001",
        "analytics_sources": ["Google Analytics", "Mixpanel", "Amplitude"],
        "metrics": {
            "page_views": 15420,
            "unique_users": 3280,
            "avg_session_duration": "4m 32s",
            "bounce_rate": "38.5%"
        },
        "top_pages": [
            {"path": "/dashboard", "views": 4520},
            {"path": "/features", "views": 3210},
            {"path": "/pricing", "views": 2890}
        ]
    }

@app.get("/api/v1/engagement/demo")
async def engagement_demo():
    """Demo engagement metrics"""
    return {
        "mvp_id": "MVP-001",
        "engagement_score": 8.7,
        "active_users_today": 234,
        "events_tracked": 15420,
        "top_events": [
            {"event": "button_click", "count": 4520},
            {"event": "form_submit", "count": 1230},
            {"event": "page_scroll", "count": 9670}
        ],
        "session_metrics": {
            "avg_duration": "4m 32s",
            "avg_pages_per_session": 5.2,
            "return_user_rate": "62%"
        }
    }

@app.get("/api/v1/revenue/demo")
async def revenue_demo():
    """Demo revenue metrics"""
    return {
        "mvp_id": "MVP-001",
        "total_revenue": 45280.50,
        "conversion_rate": "3.2%",
        "avg_order_value": 127.45,
        "funnel": {
            "visitors": 10000,
            "sign_ups": 1200,
            "trials": 450,
            "paid_conversions": 144
        },
        "revenue_trend": [
            {"month": "Aug", "revenue": 12450},
            {"month": "Sep", "revenue": 18920},
            {"month": "Oct", "revenue": 13910}
        ]
    }

@app.get("/api/v1/prioritization/demo")
async def prioritization_demo():
    """Demo prioritization data"""
    return {
        "mvp_id": "MVP-001",
        "ranked_feedback": [
            {
                "id": "FB-001",
                "title": "Add dark mode",
                "score": 9.2,
                "priority": "HIGH",
                "factors": {
                    "user_demand": 8.5,
                    "revenue_impact": 9.0,
                    "effort": 6.5
                }
            },
            {
                "id": "FB-002",
                "title": "Mobile app version",
                "score": 8.8,
                "priority": "HIGH",
                "factors": {
                    "user_demand": 9.5,
                    "revenue_impact": 8.5,
                    "effort": 4.0
                }
            },
            {
                "id": "FB-003",
                "title": "Export to PDF",
                "score": 7.1,
                "priority": "MEDIUM",
                "factors": {
                    "user_demand": 6.5,
                    "revenue_impact": 7.0,
                    "effort": 8.0
                }
            }
        ]
    }

@app.get("/api/v1/archive/demo")
async def archive_demo():
    """Demo archive status"""
    return {
        "mvp_id": "MVP-001",
        "archive_status": "READY",
        "items_to_archive": {
            "feedback_items": 142,
            "analytics_events": 15420,
            "revenue_records": 144,
            "user_sessions": 3280
        },
        "estimated_storage": "2.4 GB",
        "retention_policy": "2 years"
    }

@app.get("/api/v1/dashboard/demo")
async def dashboard_demo():
    """Demo dashboard data"""
    return {
        "portfolio_overview": {
            "active_mvps": 12,
            "total_users": 45280,
            "total_revenue": 234500,
            "avg_engagement": 7.8
        },
        "mvp_details": {
            "mvp_id": "MVP-001",
            "name": "Analytics Dashboard Pro",
            "status": "ACTIVE",
            "health_score": 8.7,
            "key_metrics": {
                "users": 3280,
                "revenue": 45280,
                "engagement": 8.7,
                "satisfaction": 4.3
            },
            "next_iteration": "Q1 2026"
        }
    }

if __name__ == "__main__":
    print("🚀 Starting CA-006 Web Demo...")
    print("📊 Open http://localhost:8000 in your browser")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
