import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import pandas as pd


class StatCard:
    """Component for displaying a statistical card with trend information."""
    
    def __init__(self, title, value, trend=None, trend_value=None):
        """
        Initialize StatCard.
        
        Args:
            title: Card title
            value: Current value to display
            trend: Trend direction ('up' or 'down')
            trend_value: Numeric trend value
        """
        self.title = title
        self.value = value
        self.trend = trend
        self.trend_value = trend_value
    
    def get_trend_color(self):
        """
        Get color based on trend direction.
        
        Returns:
            'green' for up trend, 'red' for down trend, None otherwise
        """
        if self.trend == 'up':
            return 'green'
        elif self.trend == 'down':
            return 'red'
        return None
    
    def render(self):
        """Render the stat card."""
        return {
            'title': self.title,
            'value': self.value,
            'trend': self.trend,
            'trend_value': self.trend_value,
            'trend_color': self.get_trend_color()
        }


class TopPerformersTable:
    """Component for displaying top performing MVPs."""
    
    def __init__(self, data, on_row_click=None):
        """
        Initialize TopPerformersTable.
        
        Args:
            data: List of MVP dictionaries with id, name, score
            on_row_click: Callback function for row click events
        """
        self.data = data or []
        self.on_row_click = on_row_click
    
    def get_top_performers(self, limit=25):
        """
        Get top performers sorted by score.
        
        Args:
            limit: Maximum number of performers to return
            
        Returns:
            List of top performers sorted by score descending
        """
        sorted_data = sorted(self.data, key=lambda x: x.get('score', 0), reverse=True)
        return sorted_data[:limit]
    
    def handle_row_click(self, row_id):
        """
        Handle row click event.
        
        Args:
            row_id: ID of the clicked row
        """
        if self.on_row_click:
            self.on_row_click(row_id)
    
    def render(self):
        """Render the top performers table."""
        return {
            'data': self.get_top_performers(),
            'count': len(self.get_top_performers())
        }


class ArchiveCandidatesTable:
    """Component for displaying and managing archive candidates."""
    
    def __init__(self, data, api_client=None):
        """
        Initialize ArchiveCandidatesTable.
        
        Args:
            data: List of MVP dictionaries
            api_client: API client for archive operations
        """
        self.data = data or []
        self.api_client = api_client
    
    def get_archive_candidates(self):
        """
        Get MVPs with score less than 10.
        
        Returns:
            List of MVPs eligible for archiving
        """
        return [mvp for mvp in self.data if mvp.get('score', 0) < 10]
    
    def approve_archive(self, mvp_id):
        """
        Approve archiving of an MVP.
        
        Args:
            mvp_id: ID of the MVP to archive
            
        Returns:
            API response
        """
        if self.api_client:
            return self.api_client.approve_archive(mvp_id)
        return None
    
    def reject_archive(self, mvp_id):
        """
        Reject archiving of an MVP.
        
        Args:
            mvp_id: ID of the MVP to keep active
            
        Returns:
            API response
        """
        if self.api_client:
            return self.api_client.reject_archive(mvp_id)
        return None
    
    def render(self):
        """Render the archive candidates table."""
        return {
            'data': self.get_archive_candidates(),
            'count': len(self.get_archive_candidates())
        }


class PortfolioTrendsChart:
    """Component for displaying portfolio trends over time."""
    
    def __init__(self, data):
        """
        Initialize PortfolioTrendsChart.
        
        Args:
            data: List of data points with date and value
        """
        self.data = data or []
    
    def get_chart_data(self, num_points=30):
        """
        Get chart data limited to specified number of points.
        
        Args:
            num_points: Number of data points to return
            
        Returns:
            List of most recent data points
        """
        if len(self.data) <= num_points:
            return self.data
        return self.data[-num_points:]
    
    def render(self):
        """Render the trends chart."""
        chart_data = self.get_chart_data()
        return {
            'data': chart_data,
            'count': len(chart_data)
        }


class LoadingSkeleton:
    """Component for displaying loading state."""
    
    def __init__(self, visible=True):
        """
        Initialize LoadingSkeleton.
        
        Args:
            visible: Whether skeleton should be visible
        """
        self.visible = visible
    
    def show(self):
        """Show the loading skeleton."""
        self.visible = True
    
    def hide(self):
        """Hide the loading skeleton."""
        self.visible = False
    
    def render(self):
        """Render the loading skeleton."""
        return {'visible': self.visible}


class ResponsiveGrid:
    """Component for responsive grid layout."""
    
    def __init__(self, children=None):
        """
        Initialize ResponsiveGrid.
        
        Args:
            children: Child components to display in grid
        """
        self.children = children or []
        self.breakpoint = 'desktop'
    
    def set_breakpoint(self, breakpoint):
        """
        Set the current breakpoint.
        
        Args:
            breakpoint: One of 'desktop', 'tablet', 'mobile'
        """
        if breakpoint in ['desktop', 'tablet', 'mobile']:
            self.breakpoint = breakpoint
    
    def get_columns(self):
        """
        Get number of columns based on breakpoint.
        
        Returns:
            Number of columns for current breakpoint
        """
        if self.breakpoint == 'desktop':
            return 4
        elif self.breakpoint == 'tablet':
            return 2
        else:  # mobile
            return 1
    
    def render(self):
        """Render the responsive grid."""
        return {
            'children': self.children,
            'columns': self.get_columns(),
            'breakpoint': self.breakpoint
        }


class PortfolioView:
    """Main portfolio view component."""
    
    def __init__(self, data=None, api_client=None, is_loading=False):
        """
        Initialize PortfolioView.
        
        Args:
            data: Portfolio data dictionary
            api_client: API client for data operations
            is_loading: Whether data is currently loading
        """
        self.data = data or {}
        self.api_client = api_client
        self.is_loading = is_loading
        self.stat_cards = []
        self.top_performers_table = None
        self.archive_candidates_table = None
        self.trends_chart = None
        self.loading_skeleton = LoadingSkeleton(visible=is_loading)
        self.grid = ResponsiveGrid()
        
        if not is_loading and data:
            self._initialize_components()
    
    def _initialize_components(self):
        """Initialize all child components with data."""
        self._create_stat_cards()
        self._create_top_performers_table()
        self._create_archive_candidates_table()
        self._create_trends_chart()
    
    def _create_stat_cards(self):
        """Create the 5 statistical cards."""
        stats = self.data.get('stats', {})
        
        self.stat_cards = [
            StatCard(
                title='Total MVPs',
                value=stats.get('total_mvps', 0),
                trend=stats.get('total_mvps_trend'),
                trend_value=stats.get('total_mvps_trend_value')
            ),
            StatCard(
                title='Active Projects',
                value=stats.get('active_projects', 0),
                trend=stats.get('active_projects_trend'),
                trend_value=stats.get('active_projects_trend_value')
            ),
            StatCard(
                title='Avg Score',
                value=stats.get('avg_score', 0),
                trend=stats.get('avg_score_trend'),
                trend_value=stats.get('avg_score_trend_value')
            ),
            StatCard(
                title='Success Rate',
                value=stats.get('success_rate', 0),
                trend=stats.get('success_rate_trend'),
                trend_value=stats.get('success_rate_trend_value')
            ),
            StatCard(
                title='Archive Candidates',
                value=stats.get('archive_candidates', 0),
                trend=stats.get('archive_candidates_trend'),
                trend_value=stats.get('archive_candidates_trend_value')
            )
        ]
    
    def _create_top_performers_table(self):
        """Create the top performers table."""
        mvps = self.data.get('mvps', [])
        self.top_performers_table = TopPerformersTable(
            data=mvps,
            on_row_click=self._handle_mvp_navigation
        )
    
    def _create_archive_candidates_table(self):
        """Create the archive candidates table."""
        mvps = self.data.get('mvps', [])
        self.archive_candidates_table = ArchiveCandidatesTable(
            data=mvps,
            api_client=self.api_client
        )
    
    def _create_trends_chart(self):
        """Create the portfolio trends chart."""
        trends = self.data.get('trends', [])
        self.trends_chart = PortfolioTrendsChart(data=trends)
    
    def _handle_mvp_navigation(self, mvp_id):
        """
        Handle navigation to MVP detail.
        
        Args:
            mvp_id: ID of the MVP to navigate to
        """
        pass  # Navigation logic would be implemented here
    
    def set_loading(self, is_loading):
        """
        Set loading state.
        
        Args:
            is_loading: Whether view is loading
        """
        self.is_loading = is_loading
        if is_loading:
            self.loading_skeleton.show()
        else:
            self.loading_skeleton.hide()
    
    def set_breakpoint(self, breakpoint):
        """
        Set responsive breakpoint.
        
        Args:
            breakpoint: One of 'desktop', 'tablet', 'mobile'
        """
        self.grid.set_breakpoint(breakpoint)
    
    def get_stat_cards(self):
        """
        Get all stat cards.
        
        Returns:
            List of StatCard instances
        """
        return self.stat_cards
    
    def render(self):
        """
        Render the portfolio view.
        
        Returns:
            Dictionary containing rendered components
        """
        if self.is_loading:
            return {
                'loading': self.loading_skeleton.render()
            }
        
        return {
            'stat_cards': [card.render() for card in self.stat_cards],
            'top_performers': self.top_performers_table.render() if self.top_performers_table else None,
            'archive_candidates': self.archive_candidates_table.render() if self.archive_candidates_table else None,
            'trends_chart': self.trends_chart.render() if self.trends_chart else None,
            'grid': self.grid.render(),
            'loading': self.loading_skeleton.render()
        }


class APIClient:
    """Mock API client for testing."""
    
    def approve_archive(self, mvp_id):
        """
        Approve archiving of an MVP.
        
        Args:
            mvp_id: ID of the MVP to archive
            
        Returns:
            Response dictionary
        """
        return {'status': 'success', 'mvp_id': mvp_id, 'action': 'approved'}
    
    def reject_archive(self, mvp_id):
        """
        Reject archiving of an MVP.
        
        Args:
            mvp_id: ID of the MVP to keep active
            
        Returns:
            Response dictionary
        """
        return {'status': 'success', 'mvp_id': mvp_id, 'action': 'rejected'}
