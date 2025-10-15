import plotly.graph_objects as go
import plotly.express as px
from typing import List, Dict, Any, Optional, Union
import pandas as pd
from enum import Enum


class TrendDirection(Enum):
    UP = "up"
    DOWN = "down"
    NEUTRAL = "neutral"


class ChartVisualizationLibrary:
    """Chart visualization library for creating various chart types."""

    @staticmethod
    def _get_responsive_config() -> Dict[str, Any]:
        """Get responsive configuration for charts."""
        return {
            'responsive': True,
            'displayModeBar': True,
            'displaylogo': False,
        }

    @staticmethod
    def _get_responsive_layout(height: Optional[int] = None) -> Dict[str, Any]:
        """Get responsive layout configuration."""
        layout = {
            'autosize': True,
            'margin': dict(l=50, r=50, t=50, b=50),
            'hovermode': 'closest',
        }
        if height:
            layout['height'] = height
        return layout


class TimeSeriesChart:
    """Renders line chart with multiple series."""

    def __init__(self, title: str = "", x_label: str = "", y_label: str = ""):
        """Initialize TimeSeriesChart.
        
        Args:
            title: Chart title
            x_label: X-axis label
            y_label: Y-axis label
        """
        self.title = title
        self.x_label = x_label
        self.y_label = y_label
        self.series_data: List[Dict[str, Any]] = []

    def add_series(self, name: str, x_data: List[Any], y_data: List[float], color: Optional[str] = None) -> None:
        """Add a data series to the chart.
        
        Args:
            name: Series name
            x_data: X-axis data
            y_data: Y-axis data
            color: Line color (optional)
        """
        series = {
            'name': name,
            'x': x_data,
            'y': y_data,
            'color': color
        }
        self.series_data.append(series)

    def render(self) -> go.Figure:
        """Render the time series chart.
        
        Returns:
            Plotly Figure object
        """
        fig = go.Figure()

        for series in self.series_data:
            trace_kwargs = {
                'x': series['x'],
                'y': series['y'],
                'name': series['name'],
                'mode': 'lines+markers',
                'hovertemplate': f"{series['name']}<br>%{{x}}<br>Value: %{{y:,.2f}}<extra></extra>"
            }
            if series.get('color'):
                trace_kwargs['line'] = dict(color=series['color'])
                trace_kwargs['marker'] = dict(color=series['color'])

            fig.add_trace(go.Scatter(**trace_kwargs))

        layout = ChartVisualizationLibrary._get_responsive_layout()
        layout.update({
            'title': self.title,
            'xaxis_title': self.x_label,
            'yaxis_title': self.y_label,
            'showlegend': True,
        })

        fig.update_layout(**layout)
        return fig

    def get_config(self) -> Dict[str, Any]:
        """Get chart configuration.
        
        Returns:
            Configuration dictionary
        """
        return ChartVisualizationLibrary._get_responsive_config()


class BarChart:
    """Displays bars correctly with data labels."""

    def __init__(self, title: str = "", x_label: str = "", y_label: str = ""):
        """Initialize BarChart.
        
        Args:
            title: Chart title
            x_label: X-axis label
            y_label: Y-axis label
        """
        self.title = title
        self.x_label = x_label
        self.y_label = y_label
        self.x_data: List[Any] = []
        self.y_data: List[float] = []
        self.colors: Optional[List[str]] = None
        self.show_data_labels = True

    def set_data(self, x_data: List[Any], y_data: List[float], colors: Optional[List[str]] = None) -> None:
        """Set chart data.
        
        Args:
            x_data: X-axis data (categories)
            y_data: Y-axis data (values)
            colors: Bar colors (optional)
        """
        self.x_data = x_data
        self.y_data = y_data
        self.colors = colors

    def render(self) -> go.Figure:
        """Render the bar chart.
        
        Returns:
            Plotly Figure object
        """
        trace_kwargs = {
            'x': self.x_data,
            'y': self.y_data,
            'text': [f'{val:,.2f}' for val in self.y_data] if self.show_data_labels else None,
            'textposition': 'outside' if self.show_data_labels else None,
            'hovertemplate': '%{x}<br>Value: %{y:,.2f}<extra></extra>',
        }

        if self.colors:
            trace_kwargs['marker'] = dict(color=self.colors)

        fig = go.Figure(data=[go.Bar(**trace_kwargs)])

        layout = ChartVisualizationLibrary._get_responsive_layout()
        layout.update({
            'title': self.title,
            'xaxis_title': self.x_label,
            'yaxis_title': self.y_label,
        })

        fig.update_layout(**layout)
        return fig

    def get_config(self) -> Dict[str, Any]:
        """Get chart configuration.
        
        Returns:
            Configuration dictionary
        """
        return ChartVisualizationLibrary._get_responsive_config()


class FunnelChart:
    """Visualizes funnel with correct proportions."""

    def __init__(self, title: str = ""):
        """Initialize FunnelChart.
        
        Args:
            title: Chart title
        """
        self.title = title
        self.stages: List[str] = []
        self.values: List[float] = []
        self.colors: Optional[List[str]] = None

    def set_data(self, stages: List[str], values: List[float], colors: Optional[List[str]] = None) -> None:
        """Set funnel data.
        
        Args:
            stages: Stage names
            values: Stage values
            colors: Stage colors (optional)
        """
        self.stages = stages
        self.values = values
        self.colors = colors

    def render(self) -> go.Figure:
        """Render the funnel chart.
        
        Returns:
            Plotly Figure object
        """
        trace_kwargs = {
            'y': self.stages,
            'x': self.values,
            'textinfo': 'value+percent initial',
            'hovertemplate': '%{y}<br>Value: %{x:,.0f}<br>Percent: %{percentInitial}<extra></extra>',
        }

        if self.colors:
            trace_kwargs['marker'] = dict(color=self.colors)

        fig = go.Figure(data=[go.Funnel(**trace_kwargs)])

        layout = ChartVisualizationLibrary._get_responsive_layout()
        layout.update({
            'title': self.title,
        })

        fig.update_layout(**layout)
        return fig

    def get_proportions(self) -> List[float]:
        """Get proportions of each stage relative to the first.
        
        Returns:
            List of proportions
        """
        if not self.values or self.values[0] == 0:
            return []
        return [val / self.values[0] for val in self.values]

    def get_config(self) -> Dict[str, Any]:
        """Get chart configuration.
        
        Returns:
            Configuration dictionary
        """
        return ChartVisualizationLibrary._get_responsive_config()


class ProgressBar:
    """Animates smoothly from 0 to target value."""

    def __init__(self, target_value: float, max_value: float = 100, label: str = ""):
        """Initialize ProgressBar.
        
        Args:
            target_value: Target progress value
            max_value: Maximum value (default 100)
            label: Progress bar label
        """
        self.target_value = target_value
        self.max_value = max_value
        self.label = label
        self.current_value = 0
        self.color = "#4CAF50"

    def get_percentage(self) -> float:
        """Get current percentage.
        
        Returns:
            Percentage value
        """
        return (self.target_value / self.max_value) * 100 if self.max_value > 0 else 0

    def animate_to_target(self, steps: int = 20) -> List[float]:
        """Generate animation frames from 0 to target.
        
        Args:
            steps: Number of animation steps
            
        Returns:
            List of intermediate values
        """
        if steps <= 0:
            return [self.target_value]
        
        step_size = self.target_value / steps
        return [step_size * i for i in range(steps + 1)]

    def render(self) -> Dict[str, Any]:
        """Render progress bar data.
        
        Returns:
            Dictionary with progress bar data
        """
        percentage = self.get_percentage()
        return {
            'current_value': self.target_value,
            'max_value': self.max_value,
            'percentage': percentage,
            'label': self.label,
            'color': self.color,
            'animation_frames': self.animate_to_target()
        }

    def set_color(self, color: str) -> None:
        """Set progress bar color.
        
        Args:
            color: Color value (hex or CSS color name)
        """
        self.color = color


class TrendIndicator:
    """Shows correct arrow and color based on trend direction."""

    def __init__(self, value: float, previous_value: float, label: str = ""):
        """Initialize TrendIndicator.
        
        Args:
            value: Current value
            previous_value: Previous value for comparison
            label: Indicator label
        """
        self.value = value
        self.previous_value = previous_value
        self.label = label

    def get_direction(self) -> TrendDirection:
        """Get trend direction.
        
        Returns:
            TrendDirection enum value
        """
        if self.value > self.previous_value:
            return TrendDirection.UP
        elif self.value < self.previous_value:
            return TrendDirection.DOWN
        else:
            return TrendDirection.NEUTRAL

    def get_change(self) -> float:
        """Get absolute change.
        
        Returns:
            Change value
        """
        return self.value - self.previous_value

    def get_percentage_change(self) -> float:
        """Get percentage change.
        
        Returns:
            Percentage change
        """
        if self.previous_value == 0:
            return 0.0
        return ((self.value - self.previous_value) / abs(self.previous_value)) * 100

    def get_arrow(self) -> str:
        """Get arrow symbol based on direction.
        
        Returns:
            Arrow symbol (↑, ↓, or →)
        """
        direction = self.get_direction()
        if direction == TrendDirection.UP:
            return "↑"
        elif direction == TrendDirection.DOWN:
            return "↓"
        else:
            return "→"

    def get_color(self) -> str:
        """Get color based on direction.
        
        Returns:
            Color value (green for up, red for down, gray for neutral)
        """
        direction = self.get_direction()
        if direction == TrendDirection.UP:
            return "#4CAF50"  # Green
        elif direction == TrendDirection.DOWN:
            return "#F44336"  # Red
        else:
            return "#9E9E9E"  # Gray

    def render(self) -> Dict[str, Any]:
        """Render trend indicator data.
        
        Returns:
            Dictionary with trend indicator data
        """
        return {
            'value': self.value,
            'previous_value': self.previous_value,
            'label': self.label,
            'direction': self.get_direction().value,
            'change': self.get_change(),
            'percentage_change': self.get_percentage_change(),
            'arrow': self.get_arrow(),
            'color': self.get_color()
        }


class ResponsiveChartMixin:
    """Mixin for responsive chart behavior."""

    @staticmethod
    def get_breakpoints() -> Dict[str, int]:
        """Get responsive breakpoints.
        
        Returns:
            Dictionary with breakpoint definitions
        """
        return {
            'mobile': 768,
            'tablet': 1024,
            'desktop': 1920
        }

    @staticmethod
    def get_dimensions_for_device(device: str) -> Dict[str, int]:
        """Get chart dimensions for a device type.
        
        Args:
            device: Device type (mobile, tablet, or desktop)
            
        Returns:
            Dictionary with width and height
        """
        dimensions = {
            'mobile': {'width': 360, 'height': 300},
            'tablet': {'width': 768, 'height': 400},
            'desktop': {'width': 1200, 'height': 500}
        }
        return dimensions.get(device, dimensions['desktop'])

    @staticmethod
    def is_responsive(chart: Union[TimeSeriesChart, BarChart, FunnelChart]) -> bool:
        """Check if chart is responsive.
        
        Args:
            chart: Chart instance
            
        Returns:
            True if chart configuration is responsive
        """
        config = chart.get_config()
        return config.get('responsive', False)


def format_tooltip_value(value: float, format_type: str = "default") -> str:
    """Format value for tooltip display.
    
    Args:
        value: Value to format
        format_type: Format type (default, currency, percentage)
        
    Returns:
        Formatted string
    """
    if format_type == "currency":
        return f"${value:,.2f}"
    elif format_type == "percentage":
        return f"{value:.2f}%"
    else:
        return f"{value:,.2f}"
