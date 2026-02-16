from typing import Dict, List, Any, Optional
from datetime import datetime
import json

from ..models.schemas import (
    ChartType,
    ChartConfig,
    ChartData,
    MetricValue,
    AggregatedData,
    TrendData,
    ComparisonData
)
from ..exceptions import ChartGenerationError


class ChartGenerator:
    """Service for generating chart configurations and data."""

    def generate_chart_data(
        self,
        chart_type: ChartType,
        data: Any,
        config: Optional[ChartConfig] = None
    ) -> ChartData:
        """Generate chart data based on type and input data."""
        try:
            if chart_type == ChartType.LINE:
                return self._generate_line_chart(data, config)
            elif chart_type == ChartType.BAR:
                return self._generate_bar_chart(data, config)
            elif chart_type == ChartType.PIE:
                return self._generate_pie_chart(data, config)
            elif chart_type == ChartType.AREA:
                return self._generate_area_chart(data, config)
            elif chart_type == ChartType.SCATTER:
                return self._generate_scatter_chart(data, config)
            elif chart_type == ChartType.HEATMAP:
                return self._generate_heatmap(data, config)
            elif chart_type == ChartType.GAUGE:
                return self._generate_gauge_chart(data, config)
            else:
                raise ChartGenerationError(f"Unsupported chart type: {chart_type}")
        except Exception as e:
            raise ChartGenerationError(f"Failed to generate chart: {str(e)}")

    def _generate_line_chart(
        self,
        data: AggregatedData,
        config: Optional[ChartConfig]
    ) -> ChartData:
        """Generate line chart data."""
        chart_config = config or ChartConfig()
        
        series = [{
            "name": chart_config.title or "Metric",
            "data": [
                {
                    "x": value.timestamp.isoformat(),
                    "y": value.value
                }
                for value in data.values
            ]
        }]

        options = self._get_base_options(chart_config)
        options.update({
            "chart": {
                "type": "line",
                "height": chart_config.height or 350,
                "zoom": {"enabled": True}
            },
            "stroke": {
                "curve": "smooth",
                "width": 2
            },
            "xaxis": {
                "type": "datetime",
                "labels": {"datetimeUTC": False}
            },
            "yaxis": {
                "title": {"text": chart_config.y_axis_label or "Value"},
                "labels": {
                    "formatter": "function (val) { return val.toFixed(2); }"
                }
            }
        })

        return ChartData(
            type=ChartType.LINE,
            series=series,
            options=options,
            metadata={"total_points": len(data.values)}
        )

    def _generate_bar_chart(
        self,
        data: AggregatedData,
        config: Optional[ChartConfig]
    ) -> ChartData:
        """Generate bar chart data."""
        chart_config = config or ChartConfig()
        
        categories = []
        values = []
        
        for value in data.values[-30:]:  # Last 30 data points
            categories.append(value.timestamp.strftime("%m/%d %H:%M"))
            values.append(value.value)

        series = [{
            "name": chart_config.title or "Metric",
            "data": values
        }]

        options = self._get_base_options(chart_config)
        options.update({
            "chart": {
                "type": "bar",
                "height": chart_config.height or 350
            },
            "plotOptions": {
                "bar": {
                    "horizontal": False,
                    "columnWidth": "55%",
                    "endingShape": "rounded"
                }
            },
            "xaxis": {
                "categories": categories,
                "labels": {"rotate": -45}
            },
            "yaxis": {
                "title": {"text": chart_config.y_axis_label or "Value"}
            }
        })

        return ChartData(
            type=ChartType.BAR,
            series=series,
            options=options,
            metadata={"categories_count": len(categories)}
        )

    def _generate_pie_chart(
        self,
        data: Dict[str, float],
        config: Optional[ChartConfig]
    ) -> ChartData:
        """Generate pie chart data."""
        chart_config = config or ChartConfig()
        
        labels = list(data.keys())
        series = list(data.values())

        options = self._get_base_options(chart_config)
        options.update({
            "chart": {
                "type": "pie",
                "height": chart_config.height or 350
            },
            "labels": labels,
            "responsive": [{
                "breakpoint": 480,
                "options": {
                    "chart": {"width": 200},
                    "legend": {"position": "bottom"}
                }
            }],
            "legend": {
                "position": "right",
                "offsetY": 0,
                "height": 230
            }
        })

        return ChartData(
            type=ChartType.PIE,
            series=series,
            options=options,
            metadata={"total_value": sum(series)}
        )

    def _generate_area_chart(
        self,
        data: AggregatedData,
        config: Optional[ChartConfig]
    ) -> ChartData:
        """Generate area chart data."""
        chart_config = config or ChartConfig()
        
        series = [{
            "name": chart_config.title or "Metric",
            "data": [
                {
                    "x": value.timestamp.isoformat(),
                    "y": value.value
                }
                for value in data.values
            ]
        }]

        options = self._get_base_options(chart_config)
        options.update({
            "chart": {
                "type": "area",
                "height": chart_config.height or 350,
                "zoom": {"enabled": True}
            },
            "dataLabels": {"enabled": False},
            "stroke": {"curve": "smooth"},
            "fill": {
                "type": "gradient",
                "gradient": {
                    "shadeIntensity": 1,
                    "opacityFrom": 0.7,
                    "opacityTo": 0.9,
                    "stops": [0, 90, 100]
                }
            },
            "xaxis": {
                "type": "datetime",
                "labels": {"datetimeUTC": False}
            },
            "yaxis": {
                "title": {"text": chart_config.y_axis_label or "Value"}
            }
        })

        return ChartData(
            type=ChartType.AREA,
            series=series,
            options=options,
            metadata={"total_points": len(data.values)}
        )

    def _generate_scatter_chart(
        self,
        data: List[Dict[str, Any]],
        config: Optional[ChartConfig]
    ) -> ChartData:
        """Generate scatter chart data."""
        chart_config = config or ChartConfig()
        
        series = [{
            "name": "Data Points",
            "data": [
                [point.get("x", 0), point.get("y", 0)]
                for point in data
            ]
        }]

        options = self._get_base_options(chart_config)
        options.update({
            "chart": {
                "type": "scatter",
                "height": chart_config.height or 350,
                "zoom": {
                    "enabled": True,
                    "type": "xy"
                }
            },
            "xaxis": {
                "title": {"text": chart_config.x_axis_label or "X Axis"},
                "tickAmount": 10
            },
            "yaxis": {
                "title": {"text": chart_config.y_axis_label or "Y Axis"},
                "tickAmount": 7
            }
        })

        return ChartData(
            type=ChartType.SCATTER,
            series=series,
            options=options,
            metadata={"point_count": len(data)}
        )

    def _generate_heatmap(
        self,
        data: List[List[float]],
        config: Optional[ChartConfig]
    ) -> ChartData:
        """Generate heatmap chart data."""
        chart_config = config or ChartConfig()
        
        series = []
        for i, row in enumerate(data):
            series.append({
                "name": f"Series {i+1}",
                "data": [
                    {"x": f"W{j+1}", "y": value}
                    for j, value in enumerate(row)
                ]
            })

        options = self._get_base_options(chart_config)
        options.update({
            "chart": {
                "type": "heatmap",
                "height": chart_config.height or 350
            },
            "dataLabels": {"enabled": False},
            "colors": ["#008FFB"],
            "xaxis": {
                "title": {"text": chart_config.x_axis_label or "Categories"}
            },
            "plotOptions": {
                "heatmap": {
                    "colorScale": {
                        "ranges": [
                            {"from": -30, "to": 5, "color": "#00A100"},
                            {"from": 6, "to": 20, "color": "#FFB200"},
                            {"from": 21, "to": 45, "color": "#FF0000"}
                        ]
                    }
                }
            }
        })

        return ChartData(
            type=ChartType.HEATMAP,
            series=series,
            options=options,
            metadata={"grid_size": f"{len(data)}x{len(data[0]) if data else 0}"}
        )

    def _generate_gauge_chart(
        self,
        value: float,
        config: Optional[ChartConfig]
    ) -> ChartData:
        """Generate gauge chart data."""
        chart_config = config or ChartConfig()
        
        max_value = chart_config.max_value or 100
        series = [min(value / max_value * 100, 100)]

        options = self._get_base_options(chart_config)
        options.update({
            "chart": {
                "type": "radialBar",
                "height": chart_config.height or 350,
                "offsetY": -20
            },
            "plotOptions": {
                "radialBar": {
                    "startAngle": -135,
                    "endAngle": 135,
                    "hollow": {
                        "margin": 0,
                        "size": "70%",
                        "background": "transparent"
                    },
                    "track": {
                        "background": "#e7e7e7",
                        "strokeWidth": "97%",
                        "margin": 5
                    },
                    "dataLabels": {
                        "show": True,
                        "value": {
                            "formatter": f"function (val) {{ return '{value:.1f}'; }}",
                            "color": "#111",
                            "fontSize": "36px",
                            "show": True
                        }
                    }
                }
            },
            "fill": {
                "type": "gradient",
                "gradient": {
                    "shade": "dark",
                    "type": "horizontal",
                    "shadeIntensity": 0.5,
                    "gradientToColors": ["#ABE5A1"],
                    "inverseColors": True,
                    "opacityFrom": 1,
                    "opacityTo": 1,
                    "stops": [0, 100]
                }
            },
            "stroke": {"lineCap": "round"},
            "labels": [chart_config.title or "Gauge"]
        })

        return ChartData(
            type=ChartType.GAUGE,
            series=series,
            options=options,
            metadata={"actual_value": value, "max_value": max_value}
        )

    def _get_base_options(self, config: ChartConfig) -> Dict[str, Any]:
        """Get base chart options."""
        return {
            "title": {
                "text": config.title or "",
                "align": "left"
            },
            "colors": config.colors or ["#008FFB", "#00E396", "#FEB019"],
            "theme": {
                "mode": config.theme or "light",
                "palette": "palette1"
            },
            "tooltip": {
                "enabled": True,
                "theme": config.theme or "light"
            },
            "grid": {
                "borderColor": "#e7e7e7",
                "strokeDashArray": 4
            }
        }

    def generate_comparison_chart(
        self,
        comparison_data: ComparisonData,
        chart_type: ChartType,
        config: Optional[ChartConfig] = None
    ) -> ChartData:
        """Generate chart for metric comparison."""
        if chart_type == ChartType.BAR:
            return self._generate_comparison_bar_chart(comparison_data, config)
        elif chart_type == ChartType.LINE:
            return self._generate_comparison_line_chart(comparison_data, config)
        else:
            raise ChartGenerationError(f"Unsupported comparison chart type: {chart_type}")

    def _generate_comparison_bar_chart(
        self,
        data: ComparisonData,
        config: Optional[ChartConfig]
    ) -> ChartData:
        """Generate comparison bar chart."""
        chart_config = config or ChartConfig()
        
        categories = [metric["name"] for metric in data.metrics]
        series = [{
            "name": "Current",
            "data": [metric["statistics"]["average"] for metric in data.metrics]
        }]

        options = self._get_base_options(chart_config)
        options.update({
            "chart": {
                "type": "bar",
                "height": chart_config.height or 350
            },
            "plotOptions": {
                "bar": {"horizontal": True}
            },
            "xaxis": {
                "categories": categories
            },
            "yaxis": {
                "title": {"text": "Metrics"}
            }
        })

        return ChartData(
            type=ChartType.BAR,
            series=series,
            options=options,
            metadata={"metric_count": len(data.metrics)}
        )

    def _generate_comparison_line_chart(
        self,
        data: ComparisonData,
        config: Optional[ChartConfig]
    ) -> ChartData:
        """Generate comparison line chart."""
        chart_config = config or ChartConfig()
        
        series = []
        for metric in data.metrics:
            series.append({
                "name": metric["name"],
                "data": [
                    {
                        "x": "Min",
                        "y": metric["statistics"]["minimum"]
                    },
                    {
                        "x": "Avg",
                        "y": metric["statistics"]["average"]
                    },
                    {
                        "x": "Max",
                        "y": metric["statistics"]["maximum"]
                    }
                ]
            })

        options = self._get_base_options(chart_config)
        options.update({
            "chart": {
                "type": "line",
                "height": chart_config.height or 350
            },
            "xaxis": {
                "categories": ["Min", "Avg", "Max"]
            },
            "yaxis": {
                "title": {"text": "Value"}
            }
        })

        return ChartData(
            type=ChartType.LINE,
            series=series,
            options=options,
            metadata={"metric_count": len(data.metrics)}
        )

    def generate_trend_chart(
        self,
        trend_data: TrendData,
        config: Optional[ChartConfig] = None
    ) -> ChartData:
        """Generate trend visualization chart."""
        chart_config = config or ChartConfig()
        
        series = [{
            "name": "Trend",
            "data": [
                {
                    "x": point.timestamp.isoformat(),
                    "y": point.value
                }
                for point in trend_data.data_points
            ]
        }]

        # Add trend annotation
        annotations = {
            "yaxis": [{
                "y": trend_data.current_value,
                "borderColor": "#00E396",
                "label": {
                    "borderColor": "#00E396",
                    "style": {
                        "color": "#fff",
                        "background": "#00E396"
                    },
                    "text": f"Current: {trend_data.current_value:.2f}"
                }
            }]
        }

        options = self._get_base_options(chart_config)
        options.update({
            "chart": {
                "type": "area",
                "height": chart_config.height or 350
            },
            "annotations": annotations,
            "xaxis": {
                "type": "datetime"
            },
            "yaxis": {
                "title": {"text": "Value"}
            },
            "subtitle": {
                "text": f"Change: {trend_data.change_percent:+.1f}% ({trend_data.trend})",
                "align": "left"
            }
        })

        return ChartData(
            type=ChartType.AREA,
            series=series,
            options=options,
            metadata={
                "trend": trend_data.trend,
                "change_percent": trend_data.change_percent
            }
        )
