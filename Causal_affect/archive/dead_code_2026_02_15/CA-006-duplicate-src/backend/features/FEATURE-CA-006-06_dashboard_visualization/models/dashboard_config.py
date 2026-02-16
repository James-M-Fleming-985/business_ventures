"""Dashboard configuration models."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, validator


class WidgetType(str, Enum):
    """Available widget types."""
    
    LINE_CHART = "line_chart"
    BAR_CHART = "bar_chart"
    PIE_CHART = "pie_chart"
    AREA_CHART = "area_chart"
    SCATTER_PLOT = "scatter_plot"
    HEATMAP = "heatmap"
    TABLE = "table"
    METRIC_CARD = "metric_card"
    GAUGE = "gauge"
    MAP = "map"


class FilterConfig(BaseModel):
    """Configuration for dashboard filters."""
    
    id: str = Field(..., description="Unique filter identifier")
    field: str = Field(..., description="Field to filter on")
    label: str = Field(..., description="Display label")
    type: str = Field(..., description="Filter type: select, range, date, etc.")
    options: Optional[List[Dict[str, Any]]] = None
    default_value: Optional[Any] = None
    required: bool = False
    
    @validator("type")
    def validate_type(cls, v: str) -> str:
        allowed_types = {"select", "multi_select", "range", "date_range", "text", "boolean"}
        if v not in allowed_types:
            raise ValueError(f"Invalid filter type. Must be one of: {allowed_types}")
        return v


class ChartConfig(BaseModel):
    """Configuration for chart visualization."""
    
    title: str
    subtitle: Optional[str] = None
    x_axis_label: Optional[str] = None
    y_axis_label: Optional[str] = None
    show_legend: bool = True
    show_grid: bool = True
    enable_zoom: bool = True
    enable_export: bool = True
    color_scheme: Optional[List[str]] = None
    height: Optional[int] = Field(None, ge=100, le=1000)
    
    # Chart-specific options
    stacked: Optional[bool] = None  # For bar/area charts
    show_data_labels: bool = False
    animation_duration: int = Field(default=300, ge=0, le=2000)
    
    # Data configuration
    data_source: str = Field(..., description="Endpoint or query for data")
    refresh_interval: Optional[int] = Field(None, ge=0, description="Auto-refresh in seconds")
    
    class Config:
        schema_extra = {
            "example": {
                "title": "Monthly Revenue",
                "subtitle": "Last 12 months",
                "x_axis_label": "Month",
                "y_axis_label": "Revenue ($)",
                "show_legend": True,
                "data_source": "/api/v1/analytics/revenue/monthly"
            }
        }


class WidgetConfig(BaseModel):
    """Configuration for a dashboard widget."""
    
    id: str = Field(..., description="Unique widget identifier")
    type: WidgetType
    chart_config: Optional[ChartConfig] = None
    filters: List[str] = Field(default_factory=list, description="Applied filter IDs")
    
    # Widget-specific settings
    settings: Dict[str, Any] = Field(default_factory=dict)
    
    @validator("chart_config")
    def validate_chart_config(cls, v: Optional[ChartConfig], values: Dict[str, Any]) -> Optional[ChartConfig]:
        widget_type = values.get("type")
        chart_types = {
            WidgetType.LINE_CHART, WidgetType.BAR_CHART, WidgetType.PIE_CHART,
            WidgetType.AREA_CHART, WidgetType.SCATTER_PLOT, WidgetType.HEATMAP
        }
        
        if widget_type in chart_types and v is None:
            raise ValueError(f"chart_config is required for widget type {widget_type}")
        
        return v


class LayoutItem(BaseModel):
    """Layout configuration for a widget."""
    
    widget_id: str
    x: int = Field(..., ge=0, le=11, description="Grid column (0-11)")
    y: int = Field(..., ge=0, description="Grid row")
    width: int = Field(..., ge=1, le=12, description="Width in grid columns")
    height: int = Field(..., ge=1, description="Height in grid rows")
    min_width: Optional[int] = Field(None, ge=1, le=12)
    min_height: Optional[int] = Field(None, ge=1)
    max_width: Optional[int] = Field(None, ge=1, le=12)
    max_height: Optional[int] = Field(None, ge=1)
    
    @validator("x")
    def validate_x_position(cls, v: int, values: Dict[str, Any]) -> int:
        width = values.get("width", 1)
        if v + width > 12:
            raise ValueError("Widget extends beyond grid boundary (x + width > 12)")
        return v


class DashboardLayout(BaseModel):
    """Layout configuration for the dashboard."""
    
    items: List[LayoutItem]
    row_height: int = Field(default=60, ge=30, le=200, description="Height of each grid row in pixels")
    margin: int = Field(default=10, ge=0, le=50, description="Margin between widgets")
    container_padding: int = Field(default=20, ge=0, le=100)
    
    @validator("items")
    def validate_no_overlaps(cls, items: List[LayoutItem]) -> List[LayoutItem]:
        """Ensure no widgets overlap in the grid."""
        occupied = set()
        
        for item in items:
            for x in range(item.x, item.x + item.width):
                for y in range(item.y, item.y + item.height):
                    coord = (x, y)
                    if coord in occupied:
                        raise ValueError(f"Widget overlap detected at position {coord}")
                    occupied.add(coord)
        
        return items


class DashboardConfig(BaseModel):
    """Complete dashboard configuration."""
    
    id: UUID
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    
    # Components
    widgets: List[WidgetConfig]
    filters: List[FilterConfig] = Field(default_factory=list)
    layout: DashboardLayout
    
    # Metadata
    tags: List[str] = Field(default_factory=list)
    is_public: bool = False
    owner_id: UUID
    
    # Timestamps
    created_at: datetime
    updated_at: datetime
    
    # Dashboard settings
    theme: str = Field(default="light", pattern="^(light|dark|auto)$")
    refresh_interval: Optional[int] = Field(None, ge=0, description="Global refresh in seconds")
    
    @validator("widgets")
    def validate_unique_widget_ids(cls, widgets: List[WidgetConfig]) -> List[WidgetConfig]:
        ids = [w.id for w in widgets]
        if len(ids) != len(set(ids)):
            raise ValueError("Widget IDs must be unique")
        return widgets
    
    @validator("layout")
    def validate_layout_references(cls, layout: DashboardLayout, values: Dict[str, Any]) -> DashboardLayout:
        widgets = values.get("widgets", [])
        widget_ids = {w.id for w in widgets}
        layout_widget_ids = {item.widget_id for item in layout.items}
        
        missing = layout_widget_ids - widget_ids
        if missing:
            raise ValueError(f"Layout references non-existent widgets: {missing}")
        
        orphaned = widget_ids - layout_widget_ids
        if orphaned:
            raise ValueError(f"Widgets not included in layout: {orphaned}")
        
        return layout
    
    class Config:
        schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "Sales Dashboard",
                "description": "Overview of sales performance",
                "widgets": [
                    {
                        "id": "widget-1",
                        "type": "line_chart",
                        "chart_config": {
                            "title": "Revenue Trend",
                            "data_source": "/api/v1/analytics/revenue/daily"
                        }
                    }
                ],
                "layout": {
                    "items": [
                        {
                            "widget_id": "widget-1",
                            "x": 0,
                            "y": 0,
                            "width": 6,
                            "height": 4
                        }
                    ]
                },
                "owner_id": "550e8400-e29b-41d4-a716-446655440001",
                "created_at": "2023-12-01T00:00:00Z",
                "updated_at": "2023-12-01T00:00:00Z"
            }
        }