"""Prediction tracking implementation for storing and analyzing predictions."""

from datetime import date, datetime
from typing import List, Optional
from uuid import uuid4

from sqlalchemy import Column, String, Date, DateTime, Float, Boolean, select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class PredictionTracking(Base):
    """SQLAlchemy model for tracking predictions and their outcomes."""
    
    __tablename__ = 'prediction_tracking'
    
    prediction_id = Column(String, primary_key=True)
    ticker = Column(String, nullable=False)
    target_date = Column(Date, nullable=False)
    created_at = Column(DateTime, nullable=False, default=func.now())
    prediction_price = Column(Float, nullable=False)
    prediction_direction = Column(String, nullable=False)
    actual_price = Column(Float, nullable=True)
    actual_direction = Column(String, nullable=True)
    direction_correct = Column(Boolean, nullable=True)
    value_error_pct = Column(Float, nullable=True)


async def store_prediction(
    session: AsyncSession,
    ticker: str,
    target_date: date,
    prediction_price: float,
    prediction_direction: str
) -> str:
    """Store a new prediction in the database.
    
    Args:
        session: AsyncSession instance for database operations
        ticker: Stock ticker symbol
        target_date: Date for which the prediction is made
        prediction_price: Predicted price value
        prediction_direction: Predicted price direction ('up' or 'down')
        
    Returns:
        str: Generated prediction_id
    """
    prediction_id = str(uuid4())
    
    prediction = PredictionTracking(
        prediction_id=prediction_id,
        ticker=ticker,
        target_date=target_date,
        created_at=datetime.utcnow(),
        prediction_price=prediction_price,
        prediction_direction=prediction_direction
    )
    
    session.add(prediction)
    await session.commit()
    
    return prediction_id


async def record_actual(
    session: AsyncSession,
    prediction_id: str,
    actual_price: float,
    actual_direction: str
) -> None:
    """Update a prediction with actual results and calculate accuracy metrics.
    
    Args:
        session: AsyncSession instance for database operations
        prediction_id: ID of the prediction to update
        actual_price: Actual price that occurred
        actual_direction: Actual price direction that occurred ('up' or 'down')
    """
    # Fetch the prediction
    result = await session.execute(
        select(PredictionTracking).where(PredictionTracking.prediction_id == prediction_id)
    )
    prediction = result.scalar_one_or_none()
    
    if prediction is None:
        raise ValueError(f"Prediction with ID {prediction_id} not found")
    
    # Update actual values
    prediction.actual_price = actual_price
    prediction.actual_direction = actual_direction
    
    # Calculate direction_correct
    prediction.direction_correct = prediction.prediction_direction == actual_direction
    
    # Calculate value_error_pct
    if prediction.prediction_price != 0:
        error = abs(prediction.prediction_price - actual_price)
        prediction.value_error_pct = (error / prediction.prediction_price) * 100
    else:
        prediction.value_error_pct = 0
    
    await session.commit()


async def list_predictions(
    session: AsyncSession,
    ticker: Optional[str] = None,
    direction_correct: Optional[bool] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    limit: int = 100,
    offset: int = 0
) -> List[PredictionTracking]:
    """List predictions with optional filters and pagination.
    
    Args:
        session: AsyncSession instance for database operations
        ticker: Optional ticker symbol to filter by
        direction_correct: Optional filter for correct/incorrect predictions
        start_date: Optional start date for target_date range
        end_date: Optional end date for target_date range
        limit: Maximum number of records to return
        offset: Number of records to skip
        
    Returns:
        List[PredictionTracking]: List of matching predictions
    """
    query = select(PredictionTracking)
    
    # Build filter conditions
    conditions = []
    
    if ticker is not None:
        conditions.append(PredictionTracking.ticker == ticker)
    
    if direction_correct is not None:
        conditions.append(PredictionTracking.direction_correct == direction_correct)
    
    if start_date is not None:
        conditions.append(PredictionTracking.target_date >= start_date)
    
    if end_date is not None:
        conditions.append(PredictionTracking.target_date <= end_date)
    
    # Apply filters if any
    if conditions:
        query = query.where(and_(*conditions))
    
    # Apply pagination
    query = query.limit(limit).offset(offset)
    
    # Execute query
    result = await session.execute(query)
    return list(result.scalars().all())


async def get_pending_predictions(
    session: AsyncSession,
    as_of_date: date
) -> List[PredictionTracking]:
    """Get predictions that are pending actual results.
    
    Args:
        session: AsyncSession instance for database operations
        as_of_date: Reference date to check for pending predictions
        
    Returns:
        List[PredictionTracking]: List of pending predictions with target_date <= as_of_date
    """
    query = select(PredictionTracking).where(
        and_(
            PredictionTracking.actual_price.is_(None),
            PredictionTracking.target_date <= as_of_date
        )
    )
    
    result = await session.execute(query)
    return list(result.scalars().all())
