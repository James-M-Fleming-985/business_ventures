import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from enum import Enum
import json


class WebSocketStatus(Enum):
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"


@dataclass
class DimensionScore:
    name: str
    score: float
    weight: float


@dataclass
class ScoreBreakdown:
    overall_score: float
    dimensions: List[DimensionScore]


@dataclass
class Metric:
    name: str
    value: Any
    change: Optional[float] = None
    unit: Optional[str] = None


@dataclass
class EngagementMetrics:
    metrics: List[Metric]


@dataclass
class RevenueMetrics:
    metrics: List[Metric]


@dataclass
class FunnelStage:
    name: str
    value: int
    conversion_rate: Optional[float] = None


@dataclass
class ConversionFunnel:
    stages: List[FunnelStage]


@dataclass
class TrafficSource:
    name: str
    visits: int
    conversions: int
    revenue: float
    roi: float


@dataclass
class TrafficSources:
    sources: List[TrafficSource]


@dataclass
class LiveEvent:
    id: str
    timestamp: datetime
    event_type: str
    description: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DataPoint:
    timestamp: datetime
    value: float
    label: Optional[str] = None


@dataclass
class EngagementTrend:
    data_points: List[DataPoint]


@dataclass
class MVPData:
    mvp_id: str
    name: str
    score_breakdown: ScoreBreakdown
    engagement_metrics: EngagementMetrics
    revenue_metrics: RevenueMetrics
    conversion_funnel: ConversionFunnel
    traffic_sources: TrafficSources
    engagement_trend: EngagementTrend


class WebSocketClient:
    def __init__(self, url: str):
        self.url = url
        self.status = WebSocketStatus.DISCONNECTED
        self._event_handlers = []
        self._connection = None
        
    async def connect(self):
        """Connect to WebSocket server."""
        self.status = WebSocketStatus.CONNECTING
        await asyncio.sleep(0.01)
        self.status = WebSocketStatus.CONNECTED
        self._connection = True
        
    async def disconnect(self):
        """Disconnect from WebSocket server."""
        self.status = WebSocketStatus.DISCONNECTED
        self._connection = None
        
    def on_event(self, handler):
        """Register event handler."""
        self._event_handlers.append(handler)
        
    async def _emit_event(self, event: LiveEvent):
        """Emit event to all registered handlers."""
        for handler in self._event_handlers:
            if asyncio.iscoroutinefunction(handler):
                await handler(event)
            else:
                handler(event)


class ScoreBreakdownCard:
    def __init__(self, score_breakdown: ScoreBreakdown):
        self.score_breakdown = score_breakdown
        self.overall_score = score_breakdown.overall_score
        self.dimensions = score_breakdown.dimensions
        
    def render(self) -> Dict[str, Any]:
        """Render score breakdown card."""
        return {
            "overall_score": self.overall_score,
            "dimensions": [
                {
                    "name": dim.name,
                    "score": dim.score,
                    "weight": dim.weight
                }
                for dim in self.dimensions
            ]
        }


class KeyMetricsGrid:
    def __init__(self, engagement_metrics: EngagementMetrics, revenue_metrics: RevenueMetrics):
        self.engagement_metrics = engagement_metrics.metrics
        self.revenue_metrics = revenue_metrics.metrics
        
    def render(self) -> Dict[str, Any]:
        """Render key metrics grid."""
        return {
            "engagement": [
                {
                    "name": m.name,
                    "value": m.value,
                    "change": m.change,
                    "unit": m.unit
                }
                for m in self.engagement_metrics
            ],
            "revenue": [
                {
                    "name": m.name,
                    "value": m.value,
                    "change": m.change,
                    "unit": m.unit
                }
                for m in self.revenue_metrics
            ]
        }


class ConversionFunnelChart:
    def __init__(self, conversion_funnel: ConversionFunnel):
        self.funnel = conversion_funnel
        self.stages = conversion_funnel.stages
        
    def render(self) -> Dict[str, Any]:
        """Render conversion funnel chart."""
        return {
            "stages": [
                {
                    "name": stage.name,
                    "value": stage.value,
                    "conversion_rate": stage.conversion_rate
                }
                for stage in self.stages
            ]
        }


class TrafficSourcesTable:
    def __init__(self, traffic_sources: TrafficSources):
        self.traffic_sources = traffic_sources
        self.sources = traffic_sources.sources
        
    def render(self) -> Dict[str, Any]:
        """Render traffic sources table."""
        return {
            "sources": [
                {
                    "name": source.name,
                    "visits": source.visits,
                    "conversions": source.conversions,
                    "revenue": source.revenue,
                    "roi": source.roi,
                    "roi_bar_width": min(100, max(0, source.roi))
                }
                for source in self.sources
            ]
        }


class LiveEventFeed:
    def __init__(self, websocket_url: str):
        self.websocket_url = websocket_url
        self.websocket = WebSocketClient(websocket_url)
        self.events: List[LiveEvent] = []
        self._event_handlers = []
        
    async def connect(self):
        """Connect to live event feed."""
        await self.websocket.connect()
        self.websocket.on_event(self._handle_event)
        
    async def disconnect(self):
        """Disconnect from live event feed."""
        await self.websocket.disconnect()
        
    async def _handle_event(self, event: LiveEvent):
        """Handle incoming event."""
        self.events.append(event)
        for handler in self._event_handlers:
            if asyncio.iscoroutinefunction(handler):
                await handler(event)
            else:
                handler(event)
                
    def on_event(self, handler):
        """Register event handler."""
        self._event_handlers.append(handler)
        
    async def emit_test_event(self, event: LiveEvent):
        """Emit test event (for testing purposes)."""
        await self.websocket._emit_event(event)
        
    def get_events(self) -> List[LiveEvent]:
        """Get all events."""
        return self.events
        
    def render(self) -> Dict[str, Any]:
        """Render live event feed."""
        return {
            "events": [
                {
                    "id": event.id,
                    "timestamp": event.timestamp.isoformat(),
                    "event_type": event.event_type,
                    "description": event.description,
                    "metadata": event.metadata
                }
                for event in self.events
            ],
            "status": self.websocket.status.value
        }


class EngagementTrendChart:
    def __init__(self, engagement_trend: EngagementTrend):
        self.engagement_trend = engagement_trend
        self.data_points = engagement_trend.data_points
        
    def render(self) -> Dict[str, Any]:
        """Render engagement trend chart."""
        return {
            "data_points": [
                {
                    "timestamp": dp.timestamp.isoformat(),
                    "value": dp.value,
                    "label": dp.label
                }
                for dp in self.data_points
            ],
            "count": len(self.data_points)
        }


class Breadcrumb:
    def __init__(self, items: List[Dict[str, str]]):
        self.items = items
        
    def render(self) -> Dict[str, Any]:
        """Render breadcrumb."""
        return {
            "items": self.items
        }
        
    def navigate_to(self, index: int) -> Optional[str]:
        """Navigate to breadcrumb item."""
        if 0 <= index < len(self.items):
            return self.items[index].get("path")
        return None


class MVPDetailView:
    def __init__(self, route_params: Dict[str, Any], data_service: Optional[Any] = None):
        self.route_params = route_params
        self.mvp_id = route_params.get("mvpId")
        self.data_service = data_service
        self.mvp_data: Optional[MVPData] = None
        self.score_breakdown_card: Optional[ScoreBreakdownCard] = None
        self.key_metrics_grid: Optional[KeyMetricsGrid] = None
        self.conversion_funnel_chart: Optional[ConversionFunnelChart] = None
        self.traffic_sources_table: Optional[TrafficSourcesTable] = None
        self.live_event_feed: Optional[LiveEventFeed] = None
        self.engagement_trend_chart: Optional[EngagementTrendChart] = None
        self.breadcrumb: Optional[Breadcrumb] = None
        
    async def fetch_data(self):
        """Fetch MVP data using mvpId from route params."""
        if not self.mvp_id:
            raise ValueError("mvpId is required")
            
        if self.data_service:
            self.mvp_data = await self.data_service.get_mvp_data(self.mvp_id)
        else:
            self.mvp_data = await self._fetch_mvp_data(self.mvp_id)
            
        self._initialize_components()
        
    async def _fetch_mvp_data(self, mvp_id: str) -> MVPData:
        """Fetch MVP data from API."""
        await asyncio.sleep(0.01)
        
        score_breakdown = ScoreBreakdown(
            overall_score=85.5,
            dimensions=[
                DimensionScore("User Experience", 90.0, 0.25),
                DimensionScore("Performance", 85.0, 0.25),
                DimensionScore("Reliability", 80.0, 0.25),
                DimensionScore("Innovation", 87.0, 0.25),
            ]
        )
        
        engagement_metrics = EngagementMetrics(
            metrics=[
                Metric("Daily Active Users", 15000, 5.2, "users"),
                Metric("Session Duration", 12.5, 3.1, "minutes"),
                Metric("Bounce Rate", 35.2, -2.1, "%"),
                Metric("Pages per Session", 4.8, 1.5, "pages"),
                Metric("Returning Users", 8500, 4.3, "users"),
            ]
        )
        
        revenue_metrics = RevenueMetrics(
            metrics=[
                Metric("Total Revenue", 125000, 8.5, "$"),
                Metric("ARPU", 8.33, 2.1, "$"),
                Metric("Conversion Rate", 3.5, 0.5, "%"),
                Metric("Average Order Value", 95.50, 5.2, "$"),
                Metric("Customer Lifetime Value", 450.00, 7.8, "$"),
            ]
        )
        
        conversion_funnel = ConversionFunnel(
            stages=[
                FunnelStage("Awareness", 100000, 100.0),
                FunnelStage("Interest", 50000, 50.0),
                FunnelStage("Consideration", 25000, 50.0),
                FunnelStage("Intent", 10000, 40.0),
                FunnelStage("Evaluation", 5000, 50.0),
                FunnelStage("Purchase", 3500, 70.0),
                FunnelStage("Retention", 2800, 80.0),
            ]
        )
        
        traffic_sources = TrafficSources(
            sources=[
                TrafficSource("Organic Search", 45000, 1575, 150000, 85.5),
                TrafficSource("Direct", 25000, 1000, 95000, 72.3),
                TrafficSource("Social Media", 15000, 525, 50000, 65.2),
                TrafficSource("Paid Search", 10000, 450, 42750, 58.9),
                TrafficSource("Referral", 5000, 200, 19000, 45.6),
            ]
        )
        
        now = datetime.now()
        engagement_trend = EngagementTrend(
            data_points=[
                DataPoint(now - timedelta(days=29-i), 1000 + i * 100 + (i % 3) * 50)
                for i in range(30)
            ]
        )
        
        return MVPData(
            mvp_id=mvp_id,
            name=f"MVP {mvp_id}",
            score_breakdown=score_breakdown,
            engagement_metrics=engagement_metrics,
            revenue_metrics=revenue_metrics,
            conversion_funnel=conversion_funnel,
            traffic_sources=traffic_sources,
            engagement_trend=engagement_trend
        )
        
    def _initialize_components(self):
        """Initialize all view components."""
        if not self.mvp_data:
            return
            
        self.score_breakdown_card = ScoreBreakdownCard(self.mvp_data.score_breakdown)
        self.key_metrics_grid = KeyMetricsGrid(
            self.mvp_data.engagement_metrics,
            self.mvp_data.revenue_metrics
        )
        self.conversion_funnel_chart = ConversionFunnelChart(self.mvp_data.conversion_funnel)
        self.traffic_sources_table = TrafficSourcesTable(self.mvp_data.traffic_sources)
        self.engagement_trend_chart = EngagementTrendChart(self.mvp_data.engagement_trend)
        
        websocket_url = f"ws://localhost:8000/live-events/{self.mvp_id}"
        self.live_event_feed = LiveEventFeed(websocket_url)
        
        self.breadcrumb = Breadcrumb([
            {"label": "Home", "path": "/"},
            {"label": "Portfolio", "path": "/portfolio"},
            {"label": self.mvp_data.name, "path": f"/mvp/{self.mvp_id}"}
        ])
        
    async def connect_live_feed(self):
        """Connect to live event feed."""
        if self.live_event_feed:
            await self.live_event_feed.connect()
            
    async def disconnect_live_feed(self):
        """Disconnect from live event feed."""
        if self.live_event_feed:
            await self.live_event_feed.disconnect()
            
    def navigate_back_to_portfolio(self) -> str:
        """Navigate back to portfolio from breadcrumb."""
        if self.breadcrumb:
            return self.breadcrumb.navigate_to(1)