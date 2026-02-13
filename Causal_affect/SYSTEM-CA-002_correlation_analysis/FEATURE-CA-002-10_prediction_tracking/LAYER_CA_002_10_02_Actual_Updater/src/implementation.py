from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Tuple
import logging

logger = logging.getLogger(__name__)


class ActualUpdater:
    """Updates pending predictions with actual values from time series data."""
    
    def __init__(self, db_session: AsyncSession):
        """
        Initialize the ActualUpdater with a database session.
        
        Args:
            db_session: SQLAlchemy async session for database operations
        """
        self.db_session = db_session
    
    async def update_all_pending(self) -> Dict[str, int]:
        """
        Find and update all pending predictions with past target dates.
        
        Returns:
            Dictionary with summary counts:
            - updated: Number of predictions updated with actuals
            - expired: Number of predictions marked as expired (no data after 30 days)
            - still_pending: Number of predictions still awaiting data
            - errors: Number of predictions that encountered errors
        """
        summary = {
            'updated': 0,
            'expired': 0,
            'still_pending': 0,
            'errors': 0
        }
        
        try:
            # Import models here to avoid circular imports
            from models import Prediction, TimeSeriesData
            
            # Find all pending predictions with past target dates
            now = datetime.utcnow()
            stmt = select(Prediction).where(
                and_(
                    Prediction.status == 'pending',
                    Prediction.target_date <= now
                )
            )
            
            result = await self.db_session.execute(stmt)
            pending_predictions = result.scalars().all()
            
            for prediction in pending_predictions:
                try:
                    # Check if more than 30 days have passed
                    days_past = (now - prediction.target_date).days
                    
                    if days_past > 30:
                        # Mark as expired
                        prediction.status = 'expired'
                        summary['expired'] += 1
                        continue
                    
                    # Try to find actual data for the target date
                    actual_data = await self._get_actual_data(
                        prediction.variable_1_id,
                        prediction.variable_2_id,
                        prediction.target_date,
                        TimeSeriesData
                    )
                    
                    if actual_data is None:
                        # No data available yet
                        summary['still_pending'] += 1
                        continue
                    
                    # Update prediction with actual values
                    await self._update_prediction_with_actuals(
                        prediction,
                        actual_data
                    )
                    summary['updated'] += 1
                    
                except Exception as e:
                    logger.error(f"Error updating prediction {prediction.id}: {str(e)}")
                    summary['errors'] += 1
            
            # Commit all changes
            await self.db_session.commit()
            
        except Exception as e:
            logger.error(f"Error in update_all_pending: {str(e)}")
            await self.db_session.rollback()
            raise
        
        return summary
    
    async def _get_actual_data(
        self,
        variable_1_id: int,
        variable_2_id: int,
        target_date: datetime,
        TimeSeriesData
    ) -> Optional[Dict[str, float]]:
        """
        Fetch actual values from time_series_data for the target date.
        
        Args:
            variable_1_id: ID of the first variable
            variable_2_id: ID of the second variable
            target_date: Date to fetch data for
            TimeSeriesData: TimeSeriesData model class
            
        Returns:
            Dictionary with actual values or None if data not found
        """
        try:
            # Query for both variables on the target date
            stmt = select(TimeSeriesData).where(
                and_(
                    TimeSeriesData.variable_id.in_([variable_1_id, variable_2_id]),
                    func.date(TimeSeriesData.timestamp) == target_date.date()
                )
            )
            
            result = await self.db_session.execute(stmt)
            data_points = result.scalars().all()
            
            if len(data_points) < 2:
                # Need data for both variables
                return None
            
            # Organize data by variable ID
            actual_values = {}
            for data_point in data_points:
                if data_point.variable_id == variable_1_id:
                    actual_values['variable_1'] = data_point.value
                elif data_point.variable_id == variable_2_id:
                    actual_values['variable_2'] = data_point.value
            
            # Ensure we have both values
            if 'variable_1' not in actual_values or 'variable_2' not in actual_values:
                return None
            
            return actual_values
            
        except Exception as e:
            logger.error(f"Error fetching actual data: {str(e)}")
            return None
    
    async def _update_prediction_with_actuals(
        self,
        prediction,
        actual_data: Dict[str, float]
    ) -> None:
        """
        Update prediction record with actual values and calculated metrics.
        
        Args:
            prediction: Prediction object to update
            actual_data: Dictionary with actual values for both variables
        """
        # Update actual values
        prediction.actual_value_1 = actual_data['variable_1']
        prediction.actual_value_2 = actual_data['variable_2']
        
        # Calculate direction correctness
        predicted_direction = self._get_direction(
            prediction.predicted_value_1,
            prediction.predicted_value_2
        )
        actual_direction = self._get_direction(
            actual_data['variable_1'],
            actual_data['variable_2']
        )
        prediction.direction_correct = (predicted_direction == actual_direction)
        
        # Calculate value error percentage
        # Using variable_1 as the primary variable for error calculation
        if prediction.predicted_value_1 != 0:
            error = actual_data['variable_1'] - prediction.predicted_value_1
            prediction.value_error_pct = (error / prediction.predicted_value_1) * 100
        else:
            prediction.value_error_pct = None
        
        # Update status
        prediction.status = 'completed'
        prediction.updated_at = datetime.utcnow()
    
    def _get_direction(self, value1: float, value2: float) -> str:
        """
        Determine the direction of change between two values.
        
        Args:
            value1: First value
            value2: Second value
            
        Returns:
            'up' if value2 > value1, 'down' if value2 < value1, 'flat' if equal
        """
        if value2 > value1:
            return 'up'
        elif value2 < value1:
            return 'down'
        else:
            return 'flat'
