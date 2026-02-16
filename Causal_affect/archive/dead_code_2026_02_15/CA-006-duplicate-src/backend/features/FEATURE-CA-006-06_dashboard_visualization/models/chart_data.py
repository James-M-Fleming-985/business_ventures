"""Chart data models for visualization."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, validator


class ChartType(str, Enum):
    """Supported chart types."""
    
    LINE = "line"
    BAR = "bar"
    PIE = "pie"
    AREA = "area"
    SCATTER = "scatter"
    HEATMAP = "heatmap"
    GAUGE = "gauge"
    

class ChartDataPoint(BaseModel):
    """Single data point for charts."""
    
    x: Union[str, int, float, datetime]
    y: Union[int, float, None]
    
    # Optional additional dimensions
    z: Optional[Union[int, float]] = None  # For 3D charts
    size: Optional[Union[int, float]] = None  # For bubble charts
    color: Optional[str] = None
    label: Optional[str] = None
    
    # Additional metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @validator("x", pre=True)
    def parse_x_value(cls, v: Any) -> Union[str, int, float, datetime]:
        if isinstance(v, str):
            # Try to parse as datetime
            try:
                return datetime.fromisoformat(v.replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                pass
        return v
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ChartSeries(BaseModel):
    """Data series for multi-series charts."""
    
    name: str = Field(..., description="Series name for legend")
    data: List[ChartDataPoint]
    
    # Series styling
    color: Optional[str] = None
    type: Optional[ChartType] = None  # For mixed charts
    visible: bool = True
    
    # Series-specific options
    stack: Optional[str] = None  # Stack group for stacked charts
    y_axis_id: Optional[str] = None  # For multiple y-axes
    
    @validator("data")
    def validate_non_empty(cls, v: List[ChartDataPoint]) -> List[ChartDataPoint]:
        if not v:
            raise ValueError("Series data cannot be empty")
        return v


class ChartData(BaseModel):
    """Complete chart data structure."""
    
    chart_type: ChartType
    series: List[ChartSeries]
    
    # Metadata
    title: Optional[str] = None
    subtitle: Optional[str] = None
    
    # Axes configuration
    x_axis: Dict[str, Any] = Field(default_factory=dict)
    y_axis: Dict[str, Any] = Field(default_factory=dict)
    
    # Data summary
    total_points: Optional[int] = None
    date_range: Optional[Dict[str, datetime]] = None
    
    @validator("series")
    def validate_series(cls, series: List[ChartSeries], values: Dict[str, Any]) -> List[ChartSeries]:
        if not series:
            raise ValueError("Chart must have at least one series")
        
        chart_type = values.get("chart_type")
        
        # Validate pie charts have only one series
        if chart_type == ChartType.PIE and len(series) > 1:
            raise ValueError("Pie charts can only have one data series")
        
        return series
    
    @validator("total_points", always=True)
    def calculate_total_points(cls, v: Optional[int], values: Dict[str, Any]) -> int:
        if v is not None:
            return v
        
        series = values.get("series", [])
        return sum(len(s.data) for s in series)
    
    def to_plotly_format(self) -> Dict[str, Any]:
        """Convert to Plotly.js compatible format."""
        traces = []
        
        for series in self.series:
            trace = {
                "name": series.name,
                "type": (series.type or self.chart_type).value,
                "x": [point.x for point in series.data],
                "y": [point.y for point in series.data],
            }
            
            if series.color:
                trace["marker"] = {"color": series.color}
            
            if series.stack:
                trace["stackgroup"] = series.stack
            
            if series.y_axis_id:
                trace["yaxis"] = series.y_axis_id
            
            traces.append(trace)
        
        layout = {
            "title": {"text": self.title} if self.title else {},
            "xaxis": self.x_axis,
            "yaxis": self.y_axis,
        }
        
        return {"data": traces, "layout": layout}
    
    def to_echarts_format(self) -> Dict[str, Any]:
        """Convert to ECharts compatible format."""
        option = {
            "title": {
                "text": self.title,
                "subtext": self.subtitle,
            } if self.title else {},
            "legend": {
                "data": [s.name for s in self.series]
            },
            "series": []
        }
        
        if self.chart_type == ChartType.PIE:
            option["series"] = [{
                "name": self.series[0].name,
                "type": "pie",
                "data": [
                    {"name": point.label or str(point.x), "value": point.y}
                    for point in self.series[0].data
                ]
            }]
        else:
            # Extract unique x values for category axis
            x_values = sorted(set(
                point.x for series in self.series for point in series.data
            ))
            
            option.update({
                "xAxis": {"type": "category", "data": x_values, **self.x_axis},
                "yAxis": {"type": "value", **self.y_axis},
                "series": [
                    {
                        "name": series.name,
                        "type": series.type.value if series.type else self.chart_type.value,
                        "data": [point.y for point in series.data],
                        "stack": series.stack,
                    }
                    for series in self.series
                ]
            })
        
        return option


class TimeSeriesData(ChartData):
    """Specialized model for time series data."""
    
    time_interval: str = Field(..., description="Time interval: minute, hour, day, week, month")
    timezone: str = Field(default="UTC")
    
    # Aggregation info
    aggregation_method: Optional[str] = Field(None, description="sum, avg, min, max, count")
    
    @validator("series")
    def validate_time_series(cls, series: List[ChartSeries]) -> List[ChartSeries]:
        """Ensure all x values are datetime objects."""
        for s in series:
            for point in s.data:
                if not isinstance(point.x, datetime):
                    raise ValueError(f"Time series requires datetime x values, got {type(point.x)}")
        
        return series
    
    @validator("date_range", always=True)
    def calculate_date_range(cls, v: Optional[Dict[str, datetime]], values: Dict[str, Any]) -> Dict[str, datetime]:
        if v is not None:
            return v
        
        series = values.get("series", [])
        if not series:
            return {"start": datetime.utcnow(), "end": datetime.utcnow()}
        
        all_dates = [
            point.x for s in series for point in s.data 
            if isinstance(point.x, datetime)
        ]
        
        return {
            "start": min(all_dates),
            "end": max(all_dates)
        } if all_dates else {"start": datetime.utcnow(), "end": datetime.utcnow()}