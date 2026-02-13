from datetime import datetime, date
from typing import Optional, List, Dict, Any
from sqlalchemy import select, func, and_, or_, case, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.predictions import PredictionModel, PredictionValidation
from app.models.relationships import CausalRelationship


class PredictionTracker:
    """Service for tracking and analyzing prediction performance."""
    
    def __init__(self, db_session: AsyncSession):
        """Initialize the prediction tracker.
        
        Args:
            db_session: Async SQLAlchemy session
        """
        self.db = db_session
    
    async def get_prediction_accuracy(
        self,
        domain: Optional[str] = None,
        model_type: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """Calculate prediction accuracy metrics.
        
        Args:
            domain: Optional domain filter
            model_type: Optional model type filter
            start_date: Optional start date filter
            end_date: Optional end date filter
            
        Returns:
            Dictionary containing accuracy metrics
        """
        # Build base query with validated predictions
        query = select(
            PredictionValidation.direction_correct,
            PredictionValidation.value_error_pct,
            PredictionValidation.timing_error_days,
            CausalRelationship.domain
        ).select_from(
            PredictionValidation
        ).join(
            PredictionModel,
            PredictionValidation.prediction_id == PredictionModel.id
        ).join(
            CausalRelationship,
            PredictionModel.relationship_id == CausalRelationship.id
        )
        
        # Apply filters
        filters = []
        if domain:
            filters.append(CausalRelationship.domain == domain)
        if model_type:
            filters.append(PredictionModel.model_type == model_type)
        if start_date:
            filters.append(PredictionModel.target_date >= start_date)
        if end_date:
            filters.append(PredictionModel.target_date <= end_date)
            
        if filters:
            query = query.where(and_(*filters))
        
        # Execute query
        result = await self.db.execute(query)
        validations = result.all()
        
        # Calculate metrics
        total_predictions = len(validations)
        
        if total_predictions == 0:
            return {
                "total_predictions": 0,
                "direction_accuracy": 0.0,
                "mape": 0.0,
                "timing_accuracy": 0.0
            }
        
        # Direction accuracy
        direction_correct_count = sum(1 for v in validations if v.direction_correct)
        direction_accuracy = direction_correct_count / total_predictions
        
        # MAPE
        mape = sum(abs(v.value_error_pct) for v in validations) / total_predictions
        
        # Timing accuracy (within 3 days)
        timing_accurate_count = sum(
            1 for v in validations 
            if abs(v.timing_error_days) <= 3
        )
        timing_accuracy = timing_accurate_count / total_predictions
        
        return {
            "total_predictions": total_predictions,
            "direction_accuracy": direction_accuracy,
            "mape": mape,
            "timing_accuracy": timing_accuracy
        }
    
    async def get_prediction_timeseries(
        self,
        cause: str,
        effect: str,
        model_type: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[Dict[str, Any]]:
        """Get prediction timeseries for a specific causal pair.
        
        Args:
            cause: Cause variable
            effect: Effect variable
            model_type: Optional model type filter
            start_date: Optional start date filter
            end_date: Optional end date filter
            
        Returns:
            List of prediction data points ordered by target date
        """
        # Build query
        query = select(
            PredictionModel.target_date,
            PredictionModel.predicted_value,
            PredictionModel.confidence_score,
            PredictionValidation.actual_value,
            PredictionValidation.value_error_pct
        ).select_from(
            PredictionModel
        ).join(
            CausalRelationship,
            PredictionModel.relationship_id == CausalRelationship.id
        ).outerjoin(
            PredictionValidation,
            PredictionModel.id == PredictionValidation.prediction_id
        ).where(
            and_(
                CausalRelationship.cause == cause,
                CausalRelationship.effect == effect
            )
        )
        
        # Apply filters
        if model_type:
            query = query.where(PredictionModel.model_type == model_type)
        if start_date:
            query = query.where(PredictionModel.target_date >= start_date)
        if end_date:
            query = query.where(PredictionModel.target_date <= end_date)
        
        # Order by target date
        query = query.order_by(PredictionModel.target_date)
        
        # Execute query
        result = await self.db.execute(query)
        rows = result.all()
        
        # Format results
        return [
            {
                "target_date": row.target_date,
                "predicted_value": row.predicted_value,
                "confidence_score": row.confidence_score,
                "actual_value": row.actual_value,
                "error_pct": row.value_error_pct
            }
            for row in rows
        ]
    
    async def get_best_performing_pairs(
        self,
        domain: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get best performing causal pairs by direction accuracy.
        
        Args:
            domain: Optional domain filter
            limit: Number of top pairs to return
            
        Returns:
            List of best performing pairs with metrics
        """
        # Subquery for per-pair metrics
        pair_metrics = select(
            CausalRelationship.cause,
            CausalRelationship.effect,
            CausalRelationship.domain,
            func.count(PredictionValidation.id).label('total_predictions'),
            func.sum(
                case(
                    (PredictionValidation.direction_correct == True, 1),
                    else_=0
                )
            ).label('correct_directions'),
            func.avg(func.abs(PredictionValidation.value_error_pct)).label('avg_mape')
        ).select_from(
            CausalRelationship
        ).join(
            PredictionModel,
            CausalRelationship.id == PredictionModel.relationship_id
        ).join(
            PredictionValidation,
            PredictionModel.id == PredictionValidation.prediction_id
        ).group_by(
            CausalRelationship.cause,
            CausalRelationship.effect,
            CausalRelationship.domain
        )
        
        if domain:
            pair_metrics = pair_metrics.where(CausalRelationship.domain == domain)
        
        # Calculate direction accuracy and order
        query = select(
            pair_metrics.c.cause,
            pair_metrics.c.effect,
            pair_metrics.c.domain,
            pair_metrics.c.total_predictions,
            (pair_metrics.c.correct_directions * 1.0 / pair_metrics.c.total_predictions).label('direction_accuracy'),
            pair_metrics.c.avg_mape
        ).select_from(
            pair_metrics
        ).where(
            pair_metrics.c.total_predictions > 0
        ).order_by(
            text('direction_accuracy DESC')
        ).limit(limit)
        
        # Execute query
        result = await self.db.execute(query)
        rows = result.all()
        
        return [
            {
                "cause": row.cause,
                "effect": row.effect,
                "domain": row.domain,
                "predictions_count": row.total_predictions,
                "direction_accuracy": row.direction_accuracy,
                "mape": row.avg_mape
            }
            for row in rows
        ]
    
    async def get_worst_performing_pairs(
        self,
        domain: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get worst performing causal pairs by direction accuracy.
        
        Args:
            domain: Optional domain filter
            limit: Number of bottom pairs to return
            
        Returns:
            List of worst performing pairs with metrics
        """
        # Subquery for per-pair metrics
        pair_metrics = select(
            CausalRelationship.cause,
            CausalRelationship.effect,
            CausalRelationship.domain,
            func.count(PredictionValidation.id).label('total_predictions'),
            func.sum(
                case(
                    (PredictionValidation.direction_correct == True, 1),
                    else_=0
                )
            ).label('correct_directions'),
            func.avg(func.abs(PredictionValidation.value_error_pct)).label('avg_mape')
        ).select_from(
            CausalRelationship
        ).join(
            PredictionModel,
            CausalRelationship.id == PredictionModel.relationship_id
        ).join(
            PredictionValidation,
            PredictionModel.id == PredictionValidation.prediction_id
        ).group_by(
            CausalRelationship.cause,
            CausalRelationship.effect,
            CausalRelationship.domain
        )
        
        if domain:
            pair_metrics = pair_metrics.where(CausalRelationship.domain == domain)
        
        # Calculate direction accuracy and order (ascending for worst)
        query = select(
            pair_metrics.c.cause,
            pair_metrics.c.effect,
            pair_metrics.c.domain,
            pair_metrics.c.total_predictions,
            (pair_metrics.c.correct_directions * 1.0 / pair_metrics.c.total_predictions).label('direction_accuracy'),
            pair_metrics.c.avg_mape
        ).select_from(
            pair_metrics
        ).where(
            pair_metrics.c.total_predictions > 0
        ).order_by(
            text('direction_accuracy ASC')
        ).limit(limit)
        
        # Execute query
        result = await self.db.execute(query)
        rows = result.all()
        
        return [
            {
                "cause": row.cause,
                "effect": row.effect,
                "domain": row.domain,
                "predictions_count": row.total_predictions,
                "direction_accuracy": row.direction_accuracy,
                "mape": row.avg_mape
            }
            for row in rows
        ]
    
    async def compare_model_performance(
        self,
        cause: Optional[str] = None,
        effect: Optional[str] = None,
        domain: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Compare performance across different model versions.
        
        Args:
            cause: Optional cause filter
            effect: Optional effect filter
            domain: Optional domain filter
            
        Returns:
            List of model performance comparisons
        """
        # Build query
        query = select(
            PredictionModel.model_version,
            func.count(PredictionValidation.id).label('total_predictions'),
            func.sum(
                case(
                    (PredictionValidation.direction_correct == True, 1),
                    else_=0
                )
            ).label('correct_directions'),
            func.avg(func.abs(PredictionValidation.value_error_pct)).label('avg_mape'),
            func.sum(
                case(
                    (func.abs(PredictionValidation.timing_error_days) <= 3, 1),
                    else_=0
                )
            ).label('timing_accurate')
        ).select_from(
            PredictionModel
        ).join(
            PredictionValidation,
            PredictionModel.id == PredictionValidation.prediction_id
        ).join(
            CausalRelationship,
            PredictionModel.relationship_id == CausalRelationship.id
        )
        
        # Apply filters
        filters = []
        if cause:
            filters.append(CausalRelationship.cause == cause)
        if effect:
            filters.append(CausalRelationship.effect == effect)
        if domain:
            filters.append(CausalRelationship.domain == domain)
            
        if filters:
            query = query.where(and_(*filters))
        
        # Group by model version
        query = query.group_by(PredictionModel.model_version)
        
        # Execute query
        result = await self.db.execute(query)
        rows = result.all()
        
        # Format results
        comparisons = []
        for row in rows:
            if row.total_predictions > 0:
                direction_accuracy = row.correct_directions / row.total_predictions
                timing_accuracy = row.timing_accurate / row.total_predictions
            else:
                direction_accuracy = 0.0
                timing_accuracy = 0.0
            
            comparisons.append({
                "model_version": row.model_version,
                "predictions_count": row.total_predictions,
                "direction_accuracy": direction_accuracy,
                "mape": row.avg_mape or 0.0,
                "timing_accuracy": timing_accuracy
            })
        
        return comparisons
