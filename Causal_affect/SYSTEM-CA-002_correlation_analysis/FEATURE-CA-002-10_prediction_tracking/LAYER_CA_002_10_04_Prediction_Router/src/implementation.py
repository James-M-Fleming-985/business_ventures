from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mock database and services
class MockDatabase:
    def __init__(self):
        self.predictions = [
            {
                "id": "pred1",
                "variable_pair": "A-B",
                "predicted_direction": "positive",
                "actual_direction": "positive",
                "confidence": 0.85,
                "created_at": datetime.now(),
                "model_id": "model1"
            },
            {
                "id": "pred2",
                "variable_pair": "C-D",
                "predicted_direction": "negative",
                "actual_direction": "negative",
                "confidence": 0.90,
                "created_at": datetime.now(),
                "model_id": "model2"
            },
            {
                "id": "pred3",
                "variable_pair": "A-B",
                "predicted_direction": "positive",
                "actual_direction": "negative",
                "confidence": 0.75,
                "created_at": datetime.now(),
                "model_id": "model1"
            }
        ]
    
    def get_predictions(self, filters: Dict[str, Any], skip: int, limit: int) -> List[Dict]:
        """Get filtered predictions with pagination"""
        filtered = self.predictions.copy()
        
        # Apply filters
        if filters.get("variable_pair"):
            filtered = [p for p in filtered if p["variable_pair"] == filters["variable_pair"]]
        if filters.get("predicted_direction"):
            filtered = [p for p in filtered if p["predicted_direction"] == filters["predicted_direction"]]
        if filters.get("actual_direction"):
            filtered = [p for p in filtered if p["actual_direction"] == filters["actual_direction"]]
        if filters.get("model_id"):
            filtered = [p for p in filtered if p["model_id"] == filters["model_id"]]
        
        # Apply pagination
        total = len(filtered)
        filtered = filtered[skip:skip + limit]
        
        return filtered, total
    
    def get_prediction_by_id(self, prediction_id: str) -> Optional[Dict]:
        """Get prediction by ID"""
        for pred in self.predictions:
            if pred["id"] == prediction_id:
                return pred
        return None
    
    def get_accuracy_metrics(self) -> Dict[str, Any]:
        """Calculate accuracy metrics"""
        total = len(self.predictions)
        correct = sum(1 for p in self.predictions if p["predicted_direction"] == p["actual_direction"])
        
        return {
            "overall_accuracy": correct / total if total > 0 else 0,
            "total_predictions": total,
            "correct_predictions": correct,
            "incorrect_predictions": total - correct,
            "accuracy_by_direction": {
                "positive": 0.5,  # Mock value
                "negative": 1.0,  # Mock value
                "neutral": 0.0   # Mock value
            }
        }
    
    def get_accuracy_timeseries(self, variable_pair: str) -> List[Dict]:
        """Get accuracy timeseries for a variable pair"""
        # Mock timeseries data
        return [
            {
                "date": "2024-02-01",
                "accuracy": 0.85,
                "prediction_count": 10
            },
            {
                "date": "2024-02-02",
                "accuracy": 0.90,
                "prediction_count": 15
            }
        ]
    
    def get_model_comparisons(self) -> List[Dict]:
        """Get model comparison data"""
        return [
            {
                "model_id": "model2",
                "model_name": "Model 2",
                "total_predictions": 1,
                "direction_accuracy": 1.0,
                "confidence_correlation": 0.95
            },
            {
                "model_id": "model1",
                "model_name": "Model 1",
                "total_predictions": 2,
                "direction_accuracy": 0.5,
                "confidence_correlation": 0.80
            }
        ]

class MockActualUpdater:
    def update_actuals(self) -> Dict[str, int]:
        """Mock update actuals operation"""
        return {
            "predictions_updated": 5,
            "failed_updates": 0
        }

# Initialize services
db = MockDatabase()
actual_updater = MockActualUpdater()

# Response models
class SuccessResponse(BaseModel):
    success: bool
    data: Any
    error: Optional[str] = None

@app.get("/")
async def get_predictions(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    variable_pair: Optional[str] = None,
    predicted_direction: Optional[str] = None,
    actual_direction: Optional[str] = None,
    model_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get predictions with pagination and filtering
    
    - **skip**: Number of records to skip
    - **limit**: Maximum number of records to return
    - **variable_pair**: Filter by variable pair
    - **predicted_direction**: Filter by predicted direction
    - **actual_direction**: Filter by actual direction
    - **model_id**: Filter by model ID
    """
    try:
        filters = {
            "variable_pair": variable_pair,
            "predicted_direction": predicted_direction,
            "actual_direction": actual_direction,
            "model_id": model_id
        }
        filters = {k: v for k, v in filters.items() if v is not None}
        
        predictions, total = db.get_predictions(filters, skip, limit)
        
        return {
            "success": True,
            "data": {
                "predictions": predictions,
                "total": total,
                "skip": skip,
                "limit": limit
            },
            "error": None
        }
    except Exception as e:
        logger.error(f"Database error: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error occurred")

@app.get("/{prediction_id}")
async def get_prediction(prediction_id: str) -> Dict[str, Any]:
    """
    Get a specific prediction by ID
    
    - **prediction_id**: The unique identifier of the prediction
    """
    try:
        prediction = db.get_prediction_by_id(prediction_id)
        
        if not prediction:
            return {
                "success": False,
                "data": None,
                "error": f"Prediction with id '{prediction_id}' not found"
            }
        
        return {
            "success": True,
            "data": prediction,
            "error": None
        }
    except Exception as e:
        logger.error(f"Database error: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error occurred")

@app.get("/accuracy")
async def get_accuracy() -> Dict[str, Any]:
    """
    Get overall accuracy metrics for predictions
    """
    try:
        metrics = db.get_accuracy_metrics()
        
        return {
            "success": True,
            "data": metrics,
            "error": None
        }
    except Exception as e:
        logger.error(f"Database error: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error occurred")

@app.get("/accuracy/timeseries")
async def get_accuracy_timeseries(
    variable_pair: Optional[str] = Query(None)
) -> Dict[str, Any]:
    """
    Get accuracy timeseries data for a specific variable pair
    
    - **variable_pair**: The variable pair to get timeseries for (required)
    """
    if not variable_pair:
        raise HTTPException(
            status_code=400,
            detail="variable_pair parameter is required"
        )
    
    try:
        timeseries = db.get_accuracy_timeseries(variable_pair)
        
        return {
            "success": True,
            "data": {
                "variable_pair": variable_pair,
                "timeseries": timeseries
            },
            "error": None
        }
    except Exception as e:
        logger.error(f"Database error: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error occurred")

@app.get("/models/compare")
async def compare_models() -> Dict[str, Any]:
    """
    Get model comparison data sorted by direction accuracy (descending)
    """
    try:
        comparisons = db.get_model_comparisons()
        
        return {
            "success": True,
            "data": {
                "models": comparisons
            },
            "error": None
        }
    except Exception as e:
        logger.error(f"Database error: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error occurred")

@app.post("/update-actuals")
async def update_actuals() -> Dict[str, Any]:
    """
    Trigger update of actual values for predictions
    """
    try:
        result = actual_updater.update_actuals()
        
        return {
            "success": True,
            "data": result,
            "error": None
        }
    except Exception as e:
        logger.error(f"Database error: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error occurred")

# Exception handler for database errors
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    if exc.status_code == 500:
        return {
            "success": False,
            "data": None,
            "error": exc.detail
        }
    raise exc
