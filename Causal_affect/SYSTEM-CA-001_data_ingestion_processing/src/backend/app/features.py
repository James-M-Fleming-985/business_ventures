from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any
from datetime import datetime, timedelta
import uuid
from app.models import (
    FeedbackCreate, Feedback, FeedbackUpdate, FeedbackStatus,
    IterationCreate, Iteration, IterationUpdate, IterationStatus,
    AnalysisRequest, AnalysisResult, AnalysisType,
    NotificationConfig, NotificationConfigResponse,
    ExportRequest, ExportResponse, ExportFormat
)
from app.exceptions import FeatureDisabledException, ResourceNotFoundException
from app.config import settings

feedback_storage: Dict[str, Feedback] = {}
iteration_storage: Dict[str, Iteration] = {}
analysis_storage: Dict[str, AnalysisResult] = {}
notification_storage: Dict[str, NotificationConfigResponse] = {}
export_storage: Dict[str, ExportResponse] = {}

def check_feature(feature_name: str, enabled: bool):
    if not enabled:
        raise FeatureDisabledException(feature_name)

feedback_router = APIRouter(prefix="/api/feedback", tags=["feedback"])

@feedback_router.post("", response_model=Feedback)
def create_feedback(feedback: FeedbackCreate):
    check_feature("FEATURE-CA-006-02", settings.feature_ca_006_02_enabled)
    feedback_id = str(uuid.uuid4())
    now = datetime.utcnow()
    new_feedback = Feedback(
        id=feedback_id,
        user_id=feedback.user_id,
        content=feedback.content,
        category=feedback.category,
        priority=feedback.priority,
        status=FeedbackStatus.PENDING,
        metadata=feedback.metadata,
        created_at=now,
        updated_at=now
    )
    feedback_storage[feedback_id] = new_feedback
    return new_feedback

@feedback_router.get("", response_model=List[Feedback])
def list_feedback(status: str = None, priority: str = None):
    check_feature("FEATURE-CA-006-02", settings.feature_ca_006_02_enabled)
    results = list(feedback_storage.values())
    if status:
        results = [f for f in results if f.status == status]
    if priority:
        results = [f for f in results if f.priority == priority]
    return results

@feedback_router.get("/{feedback_id}", response_model=Feedback)
def get_feedback(feedback_id: str):
    check_feature("FEATURE-CA-006-02", settings.feature_ca_006_02_enabled)
    if feedback_id not in feedback_storage:
        raise ResourceNotFoundException("Feedback", feedback_id)
    return feedback_storage[feedback_id]

@feedback_router.patch("/{feedback_id}", response_model=Feedback)
def update_feedback(feedback_id: str, update: FeedbackUpdate):
    check_feature("FEATURE-CA-006-02", settings.feature_ca_006_02_enabled)
    if feedback_id not in feedback_storage:
        raise ResourceNotFoundException("Feedback", feedback_id)
    feedback = feedback_storage[feedback_id]
    if update.status:
        feedback.status = update.status
    if update.priority:
        feedback.priority = update.priority
    if update.content:
        feedback.content = update.content
    feedback.updated_at = datetime.utcnow()
    return feedback

iteration_router = APIRouter(prefix="/api/iterations", tags=["iterations"])

@iteration_router.post("", response_model=Iteration)
def create_iteration(iteration: IterationCreate):
    check_feature("FEATURE-CA-006-03", settings.feature_ca_006_03_enabled)
    iteration_id = str(uuid.uuid4())
    now = datetime.utcnow()
    new_iteration = Iteration(
        id=iteration_id,
        name=iteration.name,
        description=iteration.description,
        feedback_ids=iteration.feedback_ids,
        status=IterationStatus.PLANNED,
        start_date=iteration.start_date,
        end_date=iteration.end_date,
        created_at=now,
        updated_at=now
    )
    iteration_storage[iteration_id] = new_iteration
    return new_iteration

@iteration_router.get("", response_model=List[Iteration])
def list_iterations(status: str = None):
    check_feature("FEATURE-CA-006-03", settings.feature_ca_006_03_enabled)
    results = list(iteration_storage.values())
    if status:
        results = [i for i in results if i.status == status]
    return results

@iteration_router.get("/{iteration_id}", response_model=Iteration)
def get_iteration(iteration_id: str):
    check_feature("FEATURE-CA-006-03", settings.feature_ca_006_03_enabled)
    if iteration_id not in iteration_storage:
        raise ResourceNotFoundException("Iteration", iteration_id)
    return iteration_storage[iteration_id]

@iteration_router.patch("/{iteration_id}", response_model=Iteration)
def update_iteration(iteration_id: str, update: IterationUpdate):
    check_feature("FEATURE-CA-006-03", settings.feature_ca_006_03_enabled)
    if iteration_id not in iteration_storage:
        raise ResourceNotFoundException("Iteration", iteration_id)
    iteration = iteration_storage[iteration_id]
    if update.status:
        iteration.status = update.status
    if update.name:
        iteration.name = update.name
    if update.description:
        iteration.description = update.description
    iteration.updated_at = datetime.utcnow()
    return iteration

analysis_router = APIRouter(prefix="/api/analysis", tags=["analysis"])

@analysis_router.post("", response_model=AnalysisResult)
def create_analysis(request: AnalysisRequest):
    check_feature("FEATURE-CA-006-04", settings.feature_ca_006_04_enabled)
    analysis_id = str(uuid.uuid4())
    
    results: Dict[str, Any] = {}
    if request.analysis_type == AnalysisType.SENTIMENT:
        results = {"positive": 45, "neutral": 35, "negative": 20}
    elif request.analysis_type == AnalysisType.TREND:
        results = {"trending_up": ["feature-x"], "trending_down": ["feature-y"]}
    elif request.analysis_type == AnalysisType.PRIORITY:
        results = {"high": 10, "medium": 25, "low": 15}
    
    analysis = AnalysisResult(
        id=analysis_id,
        analysis_type=request.analysis_type,
        results=results,
        created_at=datetime.utcnow()
    )
    analysis_storage[analysis_id] = analysis
    return analysis

@analysis_router.get("", response_model=List[AnalysisResult])
def list_analyses():
    check_feature("FEATURE-CA-006-04", settings.feature_ca_006_04_enabled)
    return list(analysis_storage.values())

@analysis_router.get("/{analysis_id}", response_model=AnalysisResult)
def get_analysis(analysis_id: str):
    check_feature("FEATURE-CA-006-04", settings.feature_ca_006_04_enabled)
    if analysis_id not in analysis_storage:
        raise ResourceNotFoundException("Analysis", analysis_id)
    return analysis_storage[analysis_id]

notification_router = APIRouter(prefix="/api/notifications", tags=["notifications"])

@notification_router.post("", response_model=NotificationConfigResponse)
def create_notification_config(config: NotificationConfig):
    check_feature("FEATURE-CA-006-05", settings.feature_ca_006_05_enabled)
    config_id = str(uuid.uuid4())
    response = NotificationConfigResponse(
        id=config_id,
        notification_type=config.notification_type,
        recipient=config.recipient,
        events=config.events,
        enabled=config.enabled,
        created_at=datetime.utcnow()
    )
    notification_storage[config_id] = response
    return response

@notification_router.get("", response_model=List[NotificationConfigResponse])
def list_notification_configs():
    check_feature("FEATURE-CA-006-05", settings.feature_ca_006_05_enabled)
    return list(notification_storage.values())

@notification_router.delete("/{config_id}")
def delete_notification_config(config_id: str):
    check_feature("FEATURE-CA-006-05", settings.feature_ca_006_05_enabled)
    if config_id not in notification_storage:
        raise ResourceNotFoundException("NotificationConfig", config_id)
    del notification_storage[config_id]
    return {"message": "deleted"}

export_router = APIRouter(prefix="/api/exports", tags=["exports"])

@export_router.post("", response_model=ExportResponse)
def create_export(request: ExportRequest):
    check_feature("FEATURE-CA-006-06", settings.feature_ca_006_06_enabled)
    export_id = str(uuid.uuid4())
    now = datetime.utcnow()
    export = ExportResponse(
        id=export_id,
        format=request.format,
        url=f"https://exports.example.com/{export_id}.{request.format.value}",
        created_at=now,
        expires_at=now + timedelta(hours=24)
    )
    export_storage[export_id] = export
    return export

@export_router.get("", response_model=List[ExportResponse])
def list_exports():
    check_feature("FEATURE-CA-006-06", settings.feature_ca_006_06_enabled)
    return list(export_storage.values())

@export_router.get("/{export_id}", response_model=ExportResponse)
def get_export(export_id: str):
    check_feature("FEATURE-CA-006-06", settings.feature_ca_006_06_enabled)
    if export_id not in export_storage:
        raise ResourceNotFoundException("Export", export_id)
    return export_storage[export_id]
