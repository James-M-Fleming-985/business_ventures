"""
Feature Integration Module for Automated Prioritization Engine
FEATURE ID: FEATURE-CA-006-04

This module orchestrates all layers of the prioritization engine to provide
a unified interface for automated MVP prioritization, scoring, ranking,
threshold management, decision-making, and explainability.
"""

from pathlib import Path
import sys
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from enum import Enum

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Layer imports
try:
    from LAYER-CA-006-04-01.src.implementation import (
        ScoreBreakdown,
        ScoringAlgorithmEngine
    )
except ImportError:
    from pathlib import Path
    layer_01_path = Path(__file__).parent.parent / "LAYER-CA-006-04-01 Scoring Algorithm Engine" / "src"
    sys.path.insert(0, str(layer_01_path))
    from implementation import ScoreBreakdown, ScoringAlgorithmEngine

try:
    from LAYER-CA-006-04-02.src.implementation import (
        MVP,
        RankingSystem
    )
except ImportError:
    layer_02_path = Path(__file__).parent.parent / "LAYER-CA-006-04-02 Ranking System" / "src"
    sys.path.insert(0, str(layer_02_path))
    from implementation import MVP, RankingSystem

try:
    from LAYER-CA-006-04-03.src.implementation import (
        ThresholdOperator,
        ThresholdRule,
        ThresholdConfiguration,
        ThresholdManager
    )
except ImportError:
    layer_03_path = Path(__file__).parent.parent / "LAYER-CA-006-04-03 Threshold Manager" / "src"
    sys.path.insert(0, str(layer_03_path))
    from implementation import (
        ThresholdOperator,
        ThresholdRule,
        ThresholdConfiguration,
        ThresholdManager
    )

try:
    from LAYER-CA-006-04-04.src.implementation import (
        Action,
        Trend,
        DecisionRationale,
        Decision,
        AuditEntry,
        DecisionEngine
    )
except ImportError:
    layer_04_path = Path(__file__).parent.parent / "LAYER-CA-006-04-04 Decision Engine" / "src"
    sys.path.insert(0, str(layer_04_path))
    from implementation import (
        Action,
        Trend,
        DecisionRationale,
        Decision,
        AuditEntry,
        DecisionEngine
    )

try:
    from LAYER-CA-006-04-05.src.implementation import ExplainabilityModule
except ImportError:
    layer_05_path = Path(__file__).parent.parent / "LAYER-CA-006-04-05 Explainability Module" / "src"
    sys.path.insert(0, str(layer_05_path))
    from implementation import ExplainabilityModule


class PriorityLevel(Enum):
    """Priority level enumeration."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NONE = "none"


class FeatureStatus(Enum):
    """Feature operation status."""
    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    FAILURE = "failure"
    ERROR = "error"


@dataclass
class FeatureConfig:
    """Configuration for the Automated Prioritization Engine feature."""
    
    # Scoring weights
    engagement_weight: float = 0.35
    revenue_weight: float = 0.30
    growth_weight: float = 0.25
    potential_weight: float = 0.10
    
    # Threshold configurations
    high_priority_threshold: float = 75.0
    medium_priority_threshold: float = 50.0
    low_priority_threshold: float = 25.0
    
    # Decision rules
    enable_auto_actions: bool = True
    require_human_approval: bool = False
    
    # Outlier handling
    enable_winsorization: bool = True
    winsorization_limits: Tuple[float, float] = (0.05, 0.95)
    
    # Ranking configuration
    enable_trend_tracking: bool = True
    trend_window_days: int = 30
    
    # Explainability settings
    detailed_explanations: bool = True
    include_recommendations: bool = True
    
    def validate(self) -> Tuple[bool, Optional[str]]:
        """
        Validate configuration parameters.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Validate weights sum to 1.0
        total_weight = (
            self.engagement_weight + 
            self.revenue_weight + 
            self.growth_weight + 
            self.potential_weight
        )
        if abs(total_weight - 1.0) > 0.001:
            return False, f"Weights must sum to 1.0, got {total_weight}"
        
        # Validate thresholds
        if not (0 <= self.low_priority_threshold <= 
                self.medium_priority_threshold <= 
                self.high_priority_threshold <= 100):
            return False, "Invalid threshold configuration"
        
        # Validate winsorization limits
        if self.enable_winsorization:
            lower, upper = self.winsorization_limits
            if not (0 <= lower < upper <= 1):
                return False, "Invalid winsorization limits"
        
        return True, None


@dataclass
class FeatureResponse:
    """Unified response structure for feature operations."""
    
    status: FeatureStatus
    timestamp: datetime = field(default_factory=datetime.now)
    
    # Core results
    mvp_scores: Dict[str, float] = field(default_factory=dict)
    mvp_rankings: Dict[str, int] = field(default_factory=dict)
    mvp_priorities: Dict[str, PriorityLevel] = field(default_factory=dict)
    decisions: List[Decision] = field(default_factory=list)
    
    # Detailed breakdowns
    score_breakdowns: Dict[str, ScoreBreakdown] = field(default_factory=dict)
    explanations: Dict[str, str] = field(default_factory=dict)
    
    # Metadata
    total_mvps_processed: int = 0
    high_priority_count: int = 0
    medium_priority_count: int = 0
    low_priority_count: int = 0
    
    # Error tracking
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    def add_error(self, error: str) -> None:
        """Add an error message."""
        self.errors.append(f"[{datetime.now().isoformat()}] {error}")
    
    def add_warning(self, warning: str) -> None:
        """Add a warning message."""
        self.warnings.append(f"[{datetime.now().isoformat()}] {warning}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert response to dictionary format."""
        return {
            "status": self.status.value,
            "timestamp": self.timestamp.isoformat(),
            "results": {
                "scores": self.mvp_scores,
                "rankings": self.mvp_rankings,
                "priorities": {k: v.value for k, v in self.mvp_priorities.items()},
                "total_processed": self.total_mvps_processed,
                "priority_distribution": {
                    "high": self.high_priority_count,
                    "medium": self.medium_priority_count,
                    "low": self.low_priority_count
                }
            },
            "decisions": [
                {
                    "mvp_id": d.mvp_id,
                    "action": d.action.value if hasattr(d.action, 'value') else str(d.action),
                    "rationale": d.rationale.__dict__ if hasattr(d, 'rationale') else {}
                }
                for d in self.decisions
            ],
            "explanations": self.explanations,
            "errors": self.errors,
            "warnings": self.warnings
        }


class FeatureOrchestrator:
    """
    Main orchestrator for the Automated Prioritization Engine feature.
    
    This class coordinates all layers to provide end-to-end prioritization
    functionality including scoring, ranking, threshold management, decision-making,
    and explainability.
    """
    
    def __init__(self, config: Optional[FeatureConfig] = None):
        """
        Initialize the feature orchestrator.
        
        Args:
            config: Optional configuration object. If None, uses defaults.
        
        Raises:
            ValueError: If configuration is invalid
            RuntimeError: If layer initialization fails
        """
        self.config = config or FeatureConfig()
        
        # Validate configuration
        is_valid, error_msg = self.config.validate()
        if not is_valid:
            raise ValueError(f"Invalid configuration: {error_msg}")
        
        # Initialize layers
        self._initialize_layers()
        
        # Track initialization status
        self._initialized = True
        self._last_run_timestamp: Optional[datetime] = None
    
    def _initialize_layers(self) -> None:
        """Initialize all layer components with error handling."""
        try:
            # Layer 1: Scoring Algorithm Engine
            self.scoring_engine = ScoringAlgorithmEngine(
                engagement_weight=self.config.engagement_weight,
                revenue_weight=self.config.revenue_weight,
                growth_weight=self.config.growth_weight,
                potential_weight=self.config.potential_weight
            )
        except Exception as e:
            raise RuntimeError(f"Failed to initialize Scoring Algorithm Engine: {e}")
        
        try:
            # Layer 2: Ranking System
            self.ranking_system = RankingSystem()
        except Exception as e:
            raise RuntimeError(f"Failed to initialize Ranking System: {e}")
        
        try:
            # Layer 3: Threshold Manager
            self.threshold_manager = ThresholdManager()
            self._configure_thresholds()
        except Exception as e:
            raise RuntimeError(f"Failed to initialize Threshold Manager: {e}")
        
        try:
            # Layer 4: Decision Engine
            self.decision_engine = DecisionEngine(
                threshold_manager=self.threshold_manager
            )
        except Exception as e:
            raise RuntimeError(f"Failed to initialize Decision Engine: {e}")
        
        try:
            # Layer 5: Explainability Module
            self.explainability_module = ExplainabilityModule()
        except Exception as e:
            raise RuntimeError(f"Failed to initialize Explainability Module: {e}")
    
    def _configure_thresholds(self) -> None:
        """Configure default thresholds in the threshold manager."""
        # High priority threshold
        high_rule = ThresholdRule(
            name="high_priority",
            threshold=self.config.high_priority_threshold,
            operator=ThresholdOperator.GREATER_EQUAL
        )
        
        # Medium priority threshold
        medium_rule = ThresholdRule(
            name="medium_priority",
            threshold=self.config.medium_priority_threshold,
            operator=ThresholdOperator.GREATER_EQUAL
        )
        
        # Low priority threshold
        low_rule = ThresholdRule(
            name="low_priority",
            threshold=self.config.low_priority_threshold,
            operator=ThresholdOperator.GREATER_EQUAL
        )
        
        # Add configurations
        high_config = ThresholdConfiguration(
            category="priority",
            rules=[high_rule]
        )
        medium_config = ThresholdConfiguration(
            category="priority",
            rules=[medium_rule]
        )
        low_config = ThresholdConfiguration(
            category="priority",
            rules=[low_rule]
        )
        
        self.threshold_manager.add_configuration("high", high_config)
        self.threshold_manager.add_configuration("medium", medium_config)
        self.threshold_manager.add_configuration("low", low_config)
    
    def prioritize_mvps(
        self,
        mvp_data: List[Dict[str, Any]],
        include_explanations: bool = True
    ) -> FeatureResponse:
        """
        Execute end-to-end prioritization for a list of MVPs.
        
        Args:
            mvp_data: List of MVP data dictionaries containing metrics
            include_explanations: Whether to generate detailed explanations
        
        Returns:
            FeatureResponse containing scores, rankings, decisions, and explanations
        """
        response = FeatureResponse(status=FeatureStatus.SUCCESS)
        
        try:
            # Step 1: Calculate scores for all MVPs
            scores_result = self._calculate_scores(mvp_data, response)
            if not scores_result:
                response.status = FeatureStatus.FAILURE
                return response
            
            # Step 2: Rank MVPs based on scores
            rankings_result = self._rank_mvps(scores_result, response)
            if not rankings_result:
                response.status = FeatureStatus.PARTIAL_SUCCESS
            
            # Step 3: Determine priority levels using thresholds
            priorities_result = self._determine_priorities(scores_result, response)
            if not priorities_result:
                response.status = FeatureStatus.PARTIAL_SUCCESS
            
            # Step 4: Generate decisions for each MVP
            decisions_result = self._generate_decisions(
                scores_result,
                priorities_result,
                response
            )
            if not decisions_result:
                response.status = FeatureStatus.PARTIAL_SUCCESS
            
            # Step 5: Generate explanations if requested
            if include_explanations or self.config.detailed_explanations:
                self._generate_explanations(
                    scores_result,
                    priorities_result,
                    decisions_result,
                    response
                )
            
            # Update metadata
            response.total_mvps_processed = len(mvp_data)
            self._update_priority_counts(response)
            
            # Update last run timestamp
            self._last_run_timestamp = datetime.now()
            
        except Exception as e:
            response.add_error(f"Prioritization failed: {str(e)}")
            response.status = FeatureStatus.ERROR
        
        return response
    
    def _calculate_scores(
        self,
        mvp_data: List[Dict[str, Any]],
        response: FeatureResponse
    ) -> Dict[str, Tuple[float, ScoreBreakdown]]:
        """
        Calculate scores for all MVPs using the scoring engine.
        
        Args:
            mvp_data: List of MVP data dictionaries
            response: Response object to populate with results
        
        Returns:
            Dictionary mapping mvp_id to (score, breakdown) tuples
        """
        scores = {}
        
        for mvp in mvp_data:
            try:
                mvp_id = mvp.get('id') or mvp.get('mvp_id')
                if not mvp_id:
                    response.add_warning("MVP missing ID, skipping")
                    continue
                
                # Calculate score
                score, breakdown = self.scoring_engine.calculate_score(mvp)
                
                # Store results
                scores[mvp_id] = (score, breakdown)
                response.mvp_scores[mvp_id] = score
                response.score_breakdowns[mvp_id] = breakdown
                
            except Exception as e:
                response.add_error(f"Failed to score MVP {mvp.get('id', 'unknown')}: {e}")
                continue
        
        return scores
    
    def _rank_mvps(
        self,
        scores: Dict[str, Tuple[float, ScoreBreakdown]],
        response: FeatureResponse
    ) -> Dict[str, int]:
        """
        Rank MVPs based on their scores.
        
        Args:
            scores: Dictionary of MVP scores and breakdowns
            response: Response object to populate with results
        
        Returns:
            Dictionary mapping mvp_id to rank
        """
        rankings = {}
        
        try:
            # Create MVP objects for ranking system
            mvps = []
            for mvp_id, (score, breakdown) in scores.items():
                mvp = MVP(
                    mvp_id=mvp_id,
                    priority_score=score,
                    metadata={"breakdown": breakdown.__dict__ if hasattr(breakdown, '__dict__') else {}}
                )
                mvps.append(mvp)
            
            # Rank MVPs
            ranked_mvps = self.ranking_system.rank_mvps(mvps)
            
            # Extract rankings
            for rank, mvp in enumerate(ranked_mvps, start=1):
                rankings[mvp.mvp_id] = rank
                response.mvp_rankings[mvp.mvp_id] = rank
            
        except Exception as e:
            response.add_error(f"Ranking failed: {e}")
            return {}
        
        return rankings
    
    def _determine_priorities(
        self,
        scores: Dict[str, Tuple[float, ScoreBreakdown]],
        response: FeatureResponse
    ) -> Dict[str, PriorityLevel]:
        """
        Determine priority levels for MVPs using threshold manager.
        
        Args:
            scores: Dictionary of MVP scores and breakdowns
            response: Response object to populate with results
        
        Returns:
            Dictionary mapping mvp_id to priority level
        """
        priorities = {}
        
        try:
            for mvp_id, (score, _) in scores.items():
                # Evaluate against thresholds
                if self.threshold_manager.evaluate("high", score):
                    priority = PriorityLevel.HIGH
                elif self.threshold_manager.evaluate("medium", score):
                    priority = PriorityLevel.MEDIUM
                elif self.threshold_manager.evaluate("low", score):
                    priority = PriorityLevel.LOW
                else:
                    priority = PriorityLevel.NONE
                
                priorities[mvp_id] = priority
                response.mvp_priorities[mvp_id] = priority
                
        except Exception as e:
            response.add_error(f"Priority determination failed: {e}")
            return {}
        
        return priorities
    
    def _generate_decisions(
        self,
        scores: Dict[str, Tuple[float, ScoreBreakdown]],
        priorities: Dict[str, PriorityLevel],
        response: FeatureResponse
    ) -> List[Decision]:
        """
        Generate actionable decisions for each MVP.
        
        Args:
            scores: Dictionary of MVP scores and breakdowns
            priorities: Dictionary of MVP priorities
            response: Response object to populate with results
        
        Returns:
            List of Decision objects
        """
        decisions = []
        
        try:
            for mvp_id in scores.keys():
                score, breakdown = scores[mvp_id]
                priority = priorities.get(mvp_id, PriorityLevel.NONE)
                
                # Generate decision using decision engine
                decision = self.decision_engine.make_decision(
                    mvp_id=mvp_id,
                    priority_score=score,
                    priority_level=priority.value,
                    score_breakdown=breakdown
                )
                
                decisions.append(decision)
            
            response.decisions = decisions
            
        except Exception as e:
            response.add_error(f"Decision generation failed: {e}")
            return []
        
        return decisions
    
    def _generate_explanations(
        self,
        scores: Dict[str, Tuple[float, ScoreBreakdown]],
        priorities: Dict[str, PriorityLevel],
        decisions: List[Decision],
        response: FeatureResponse
    ) -> None:
        """
        Generate human-readable explanations for all results.
        
        Args:
            scores: Dictionary of MVP scores and breakdowns
            priorities: Dictionary of MVP priorities
            decisions: List of decisions
            response: Response object to populate with explanations
        """
        try:
            for mvp_id in scores.keys():
                score, breakdown = scores[mvp_id]
                priority = priorities.get(mvp_id, PriorityLevel.NONE)
                
                # Find corresponding decision
                decision = next((d for d in decisions if d.mvp_id == mvp_id), None)
                
                # Generate explanation
                explanation = self.explainability_module.explain_score(
                    mvp_id=mvp_id,
                    score=score,
                    breakdown=breakdown,
                    priority=priority.value,
                    decision=decision
                )
                
                response.explanations[mvp_id] = explanation
                
        except Exception as e:
            response.add_warning(f"Explanation generation failed: {e}")
    
    def _update_priority_counts(self, response: FeatureResponse) -> None:
        """Update priority distribution counts in response."""
        response.high_priority_count = sum(
            1 for p in response.mvp_priorities.values() 
            if p == PriorityLevel.HIGH
        )
        response.medium_priority_count = sum(
            1 for p in response.mvp_priorities.values() 
            if p == PriorityLevel.MEDIUM
        )
        response.low_priority_count = sum(
            1 for p in response.mvp_priorities.values() 
            if p == PriorityLevel.LOW
        )
    
    def get_mvp_priority(self, mvp_id: str) -> Optional[Dict[str, Any]]:
        """
        Get complete priority information for a specific MVP.
        
        Args:
            mvp_id: ID of the MVP
        
        Returns:
            Dictionary containing score, rank, priority, and explanation
        """
        try:
            # This would typically query stored results
            # Implementation depends on data persistence strategy
            return {
                "mvp_id": mvp_id,
                "status": "not_implemented",
                "message": "Query functionality requires data persistence layer"
            }
        except Exception as e:
            return {
                "mvp_id": mvp_id,
                "error": str(e)
            }
    
    def update_configuration(self, new_config: FeatureConfig) -> bool:
        """
        Update the feature configuration and reinitialize layers.
        
        Args:
            new_config: New configuration object
        
        Returns:
            True if update successful, False otherwise
        """
        try:
            # Validate new configuration
            is_valid, error_msg = new_config.validate()
            if not is_valid:
                raise ValueError(error_msg)
            
            # Update configuration
            self.config = new_config
            
            # Reinitialize layers with new configuration
            self._initialize_layers()
            
            return True
            
        except Exception as e:
            print(f"Configuration update failed: {e}")
            return False
    
    def get_feature_status(self) -> Dict[str, Any]:
        """
        Get current status of the feature and all layers.
        
        Returns:
            Dictionary containing status information
        """
        return {
            "feature_id": "FEATURE-CA-006-04",
            "feature_name": "Automated Prioritization Engine",
            "initialized": self._initialized,
            "last_run": self._last_run_timestamp.isoformat() if self._last_ru