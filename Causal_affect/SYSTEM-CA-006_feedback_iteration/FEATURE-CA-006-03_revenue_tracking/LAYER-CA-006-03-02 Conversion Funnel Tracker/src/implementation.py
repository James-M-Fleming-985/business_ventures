```python
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from collections import defaultdict


class ConversionFunnelTracker:
    """
    Tracks user progression through a 7-stage conversion funnel with source attribution.
    
    Stages:
    1. Landing
    2. Browse
    3. View Product
    4. Add to Cart
    5. Checkout
    6. Payment
    7. Confirmation
    """
    
    STAGES = [
        "landing",
        "browse",
        "view_product",
        "add_to_cart",
        "checkout",
        "payment",
        "confirmation"
    ]
    
    def __init__(self):
        """Initialize the conversion funnel tracker."""
        self.user_sessions: Dict[str, Dict[str, Any]] = {}
        self.stage_counts: Dict[str, int] = {stage: 0 for stage in self.STAGES}
        self.source_conversions: Dict[str, int] = defaultdict(int)
        self.source_starts: Dict[str, int] = defaultdict(int)
        self.dropoffs: Dict[str, int] = {stage: 0 for stage in self.STAGES}
    
    def track_event(self, user_id: str, stage: str, source: Optional[str] = None, 
                   timestamp: Optional[str] = None) -> bool:
        """
        Track a user's progress through a funnel stage.
        
        Args:
            user_id: Unique identifier for the user
            stage: Current funnel stage
            source: Traffic source (required for first stage)
            timestamp: Event timestamp (ISO format)
            
        Returns:
            bool: True if event was tracked successfully
            
        Raises:
            ValueError: If stage is invalid or source is missing for first stage
        """
        if stage not in self.STAGES:
            raise ValueError(f"Invalid stage: {stage}")
        
        stage_index = self.STAGES.index(stage)
        
        # Initialize user session if not exists
        if user_id not in self.user_sessions:
            if stage_index != 0:
                # User must start at landing stage
                return False
            
            if source is None:
                raise ValueError("Source is required for the first stage")
            
            self.user_sessions[user_id] = {
                "source": source,
                "current_stage": stage,
                "current_stage_index": stage_index,
                "stages_completed": [stage],
                "timestamp": timestamp or datetime.utcnow().isoformat()
            }
            self.stage_counts[stage] += 1
            self.source_starts[source] += 1
            return True
        
        # Get user session
        session = self.user_sessions[user_id]
        current_index = session["current_stage_index"]
        
        # Check if user is progressing forward
        if stage_index <= current_index:
            # User is revisiting a stage or at same stage
            return False
        
        # Check if user is skipping stages (only allow sequential progression)
        if stage_index != current_index + 1:
            return False
        
        # Update session
        session["current_stage"] = stage
        session["current_stage_index"] = stage_index
        session["stages_completed"].append(stage)
        
        # Update stage counts
        self.stage_counts[stage] += 1
        
        # Track conversion if reached final stage
        if stage == "confirmation":
            self.source_conversions[session["source"]] += 1
        
        return True
    
    def get_conversion_rate(self, from_stage: str, to_stage: str) -> float:
        """
        Calculate conversion rate between two stages.
        
        Args:
            from_stage: Starting stage
            to_stage: Ending stage
            
        Returns:
            float: Conversion rate (0.0 to 1.0)
            
        Raises:
            ValueError: If stages are invalid or out of order
        """
        if from_stage not in self.STAGES:
            raise ValueError(f"Invalid from_stage: {from_stage}")
        if to_stage not in self.STAGES:
            raise ValueError(f"Invalid to_stage: {to_stage}")
        
        from_index = self.STAGES.index(from_stage)
        to_index = self.STAGES.index(to_stage)
        
        if to_index <= from_index:
            raise ValueError("to_stage must come after from_stage")
        
        from_count = self.stage_counts[from_stage]
        to_count = self.stage_counts[to_stage]
        
        if from_count == 0:
            return 0.0
        
        return to_count / from_count
    
    def get_overall_conversion_rate(self) -> float:
        """
        Calculate overall conversion rate from landing to confirmation.
        
        Returns:
            float: Overall conversion rate (0.0 to 1.0)
        """
        return self.get_conversion_rate("landing", "confirmation")
    
    def get_source_attribution(self) -> Dict[str, Dict[str, Any]]:
        """
        Get conversion attribution by traffic source.
        
        Returns:
            dict: Dictionary mapping sources to their conversion metrics
        """
        attribution = {}
        
        for source in self.source_starts:
            starts = self.source_starts[source]
            conversions = self.source_conversions.get(source, 0)
            conversion_rate = conversions / starts if starts > 0 else 0.0
            
            attribution[source] = {
                "starts": starts,
                "conversions": conversions,
                "conversion_rate": conversion_rate
            }
        
        return attribution
    
    def get_dropoff_analysis(self) -> Dict[str, Dict[str, Any]]:
        """
        Analyze drop-offs at each funnel stage.
        
        Returns:
            dict: Dictionary with drop-off metrics for each stage
        """
        analysis = {}
        
        for i, stage in enumerate(self.STAGES[:-1]):
            current_count = self.stage_counts[stage]
            next_stage = self.STAGES[i + 1]
            next_count = self.stage_counts[next_stage]
            
            dropoffs = current_count - next_count
            dropoff_rate = dropoffs / current_count if current_count > 0 else 0.0
            
            analysis[stage] = {
                "users_at_stage": current_count,
                "users_dropped": dropoffs,
                "dropoff_rate": dropoff_rate,
                "users_continued": next_count
            }
        
        # Add final stage
        confirmation_count = self.stage_counts["confirmation"]
        analysis["confirmation"] = {
            "users_at_stage": confirmation_count,
            "users_dropped": 0,
            "dropoff_rate": 0.0,
            "users_continued": confirmation_count
        }
        
        return analysis
    
    def get_stage_counts(self) -> Dict[str, int]:
        """
        Get the count of users at each stage.
        
        Returns:
            dict: Dictionary mapping stages to user counts
        """
        return self.stage_counts.copy()
    
    def get_user_journey(self, user_id: str) -> Optional[List[str]]:
        """
        Get the journey of a specific user through the funnel.
        
        Args:
            user_id: User identifier
            
        Returns:
            list: List of stages completed by user, or None if user not found
        """
        if user_id not in self.user_sessions:
            return None
        
        return self.user_sessions[user_id]["stages_completed"].copy()
    
    def reset(self):
        """Reset all tracking data."""
        self.user_sessions.clear()
        self.stage_counts = {stage: 0 for stage in self.STAGES}
        self.source_conversions.clear()
        self.source_starts.clear()
        self.dropoffs = {stage: 0 for stage in self.STAGES}
    
    def export_data(self) -> str:
        """
        Export all tracking data as JSON.
        
        Returns:
            str: JSON string with all tracking data
        """
        data = {
            "user_sessions": self.user_sessions,
            "stage_counts": self.stage_counts,
            "source_conversions": dict(self.source_conversions),
            "source_starts": dict(self.source_starts),
            "dropoffs": self.dropoffs
        }
        return json.dumps(data, indent=2)
    
    def import_data(self, json_data: str):
        """
        Import tracking data from JSON.
        
        Args:
            json_data: JSON string with tracking data
        """
        data = json.loads(json_data)
        
        self.user_sessions = data.get("user_sessions", {})
        self.stage_counts = data.get("stage_counts", {stage: 0 for stage in self.STAGES})
        self.source_conversions = defaultdict(int, data.get("source_conversions", {}))
        self.source_starts = defaultdict(int, data.get("source_starts", {}))
        self.dropoffs = data.get("dropoffs", {stage: 0 for stage in self.STAGES})
```