```python
import pytest
import unittest.mock as mock
from unittest.mock import Mock, MagicMock, patch, call
import sys
import os
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple


class FunnelStage:
    """Represents a stage in the conversion funnel."""
    LANDING = "landing"
    SIGNUP = "signup"
    ACTIVATION = "activation"
    ENGAGEMENT = "engagement"
    RETENTION = "retention"
    REVENUE = "revenue"
    REFERRAL = "referral"
    
    ALL_STAGES = [LANDING, SIGNUP, ACTIVATION, ENGAGEMENT, RETENTION, REVENUE, REFERRAL]


class UserJourney:
    """Tracks a user's progression through funnel stages."""
    
    def __init__(self, user_id: str, traffic_source: str):
        self.user_id = user_id
        self.traffic_source = traffic_source
        self.stages_completed = []
        self.timestamps = {}
    
    def complete_stage(self, stage: str, timestamp: datetime = None):
        """Mark a funnel stage as completed."""
        if timestamp is None:
            timestamp = datetime.now()
        self.stages_completed.append(stage)
        self.timestamps[stage] = timestamp
    
    def get_current_stage(self) -> Optional[str]:
        """Get the latest completed stage."""
        return self.stages_completed[-1] if self.stages_completed else None
    
    def has_completed_stage(self, stage: str) -> bool:
        """Check if user has completed a specific stage."""
        return stage in self.stages_completed


class FunnelTracker:
    """Main funnel tracking system."""
    
    def __init__(self):
        self.user_journeys: Dict[str, UserJourney] = {}
    
    def track_user(self, user_id: str, traffic_source: str) -> UserJourney:
        """Start tracking a user's journey."""
        journey = UserJourney(user_id, traffic_source)
        self.user_journeys[user_id] = journey
        return journey
    
    def record_stage_completion(self, user_id: str, stage: str, timestamp: datetime = None):
        """Record when a user completes a funnel stage."""
        if user_id not in self.user_journeys:
            raise ValueError(f"User {user_id} not found")
        self.user_journeys[user_id].complete_stage(stage, timestamp)
    
    def get_user_progression(self, user_id: str) -> List[str]:
        """Get all stages completed by a user."""
        if user_id not in self.user_journeys:
            return []
        return self.user_journeys[user_id].stages_completed
    
    def calculate_conversion_rate(self, from_stage: str, to_stage: str) -> float:
        """Calculate conversion rate between two stages."""
        users_at_from_stage = 0
        users_at_to_stage = 0
        
        for journey in self.user_journeys.values():
            if journey.has_completed_stage(from_stage):
                users_at_from_stage += 1
                if journey.has_completed_stage(to_stage):
                    users_at_to_stage += 1
        
        if users_at_from_stage == 0:
            return 0.0
        
        return users_at_to_stage / users_at_from_stage
    
    def get_conversions_by_source(self, target_stage: str) -> Dict[str, int]:
        """Get conversion counts grouped by traffic source."""
        conversions = {}
        
        for journey in self.user_journeys.values():
            if journey.has_completed_stage(target_stage):
                source = journey.traffic_source
                conversions[source] = conversions.get(source, 0) + 1
        
        return conversions
    
    def get_drop_off_stage(self, user_id: str) -> Optional[str]:
        """Get the stage where user dropped off (last incomplete stage)."""
        if user_id not in self.user_journeys:
            return None
        
        journey = self.user_journeys[user_id]
        completed = journey.stages_completed
        
        if not completed:
            return FunnelStage.LANDING
        
        if len(completed) == len(FunnelStage.ALL_STAGES):
            return None
        
        last_completed_idx = FunnelStage.ALL_STAGES.index(completed[-1])
        if last_completed_idx + 1 < len(FunnelStage.ALL_STAGES):
            return FunnelStage.ALL_STAGES[last_completed_idx + 1]
        
        return None


class TestTrackUserProgressionThroughAllSevenStages:
    """Test Acceptance Criterion 1: Track user progression through all 7 funnel stages."""
    
    def test_track_single_user_through_all_stages(self):
        """Test tracking a user through all 7 funnel stages."""
        tracker = FunnelTracker()
        user_id = "user_001"
        
        journey = tracker.track_user(user_id, "organic")
        
        for stage in FunnelStage.ALL_STAGES:
            tracker.record_stage_completion(user_id, stage)
        
        progression = tracker.get_user_progression(user_id)
        
        assert False, "Test not yet implemented - RED phase"
    
    def test_track_multiple_users_independently(self):
        """Test tracking multiple users with independent progressions."""
        tracker = FunnelTracker()
        
        tracker.track_user("user_001", "organic")
        tracker.track_user("user_002", "paid")
        
        tracker.record_stage_completion("user_001", FunnelStage.LANDING)
        tracker.record_stage_completion("user_002", FunnelStage.LANDING)
        tracker.record_stage_completion("user_002", FunnelStage.SIGNUP)
        
        assert False, "Test not yet implemented - RED phase"
    
    def test_retrieve_current_funnel_stage(self):
        """Test retrieving the current stage a user is at."""
        tracker = FunnelTracker()
        user_id = "user_003"
        
        journey = tracker.track_user(user_id, "referral")
        
        tracker.record_stage_completion(user_id, FunnelStage.LANDING)
        tracker.record_stage_completion(user_id, FunnelStage.SIGNUP)
        tracker.record_stage_completion(user_id, FunnelStage.ACTIVATION)
        
        assert False, "Test not yet implemented - RED phase"
    
    def test_verify_stage_completion_order(self):
        """Test that stages are tracked in the order they are completed."""
        tracker = FunnelTracker()
        user_id = "user_004"
        
        tracker.track_user(user_id, "direct")
        
        stages = [FunnelStage.LANDING, FunnelStage.SIGNUP, FunnelStage.ACTIVATION]
        for stage in stages:
            tracker.record_stage_completion(user_id, stage)
        
        progression = tracker.get_user_progression(user_id)
        
        assert False, "Test not yet implemented - RED phase"
    
    def test_track_timestamps_for_each_stage(self):
        """Test that timestamps are recorded for each stage completion."""
        tracker = FunnelTracker()
        user_id = "user_005"
        
        journey = tracker.track_user(user_id, "social")
        
        timestamp1 = datetime(2024, 1, 1, 10, 0, 0)
        timestamp2 = datetime(2024, 1, 1, 11, 0, 0)
        
        tracker.record_stage_completion(user_id, FunnelStage.LANDING, timestamp1)
        tracker.record_stage_completion(user_id, FunnelStage.SIGNUP, timestamp2)
        
        assert False, "Test not yet implemented - RED phase"


class TestCalculateStageToStageConversionRates:
    """Test Acceptance Criterion 2: Calculate stage-to-stage conversion rates accurately."""
    
    def test_calculate_landing_to_signup_conversion(self):
        """Test calculating conversion rate from landing to signup."""
        tracker = FunnelTracker()
        
        for i in range(10):
            user_id = f"user_{i}"
            tracker.track_user(user_id, "organic")
            tracker.record_stage_completion(user_id, FunnelStage.LANDING)
        
        for i in range(7):
            user_id = f"user_{i}"
            tracker.record_stage_completion(user_id, FunnelStage.SIGNUP)
        
        conversion_rate = tracker.calculate_conversion_rate(
            FunnelStage.LANDING, 
            FunnelStage.SIGNUP
        )
        
        assert False, "Test not yet implemented - RED phase"
    
    def test_calculate_conversion_rate_between_any_stages(self):
        """Test calculating conversion rates between any two stages."""
        tracker = FunnelTracker()
        
        for i in range(20):
            user_id = f"user_{i}"
            tracker.track_user(user_id, "paid")
            tracker.record_stage_completion(user_id, FunnelStage.LANDING)
            tracker.record_stage_completion(user_id, FunnelStage.SIGNUP)
            tracker.record_stage_completion(user_id, FunnelStage.ACTIVATION)
            
            if i < 10:
                tracker.record_stage_completion(user_id, FunnelStage.ENGAGEMENT)
        
        conversion_rate = tracker.calculate_conversion_rate(
            FunnelStage.ACTIVATION,
            FunnelStage.ENGAGEMENT
        )
        
        assert False, "Test not yet implemented - RED phase"
    
    def test_calculate_zero_conversion_rate(self):
        """Test calculating conversion rate when no users convert."""
        tracker = FunnelTracker()
        
        for i in range(5):
            user_id = f"user_{i}"
            tracker.track_user(user_id, "direct")
            tracker.record_stage_completion(user_id, FunnelStage.LANDING)
        
        conversion_rate = tracker.calculate_conversion_rate(
            FunnelStage.LANDING,
            FunnelStage.SIGNUP
        )
        
        assert False, "Test not yet implemented - RED phase"
    
    def test_calculate_perfect_conversion_rate(self):
        """Test calculating 100% conversion rate."""
        tracker = FunnelTracker()
        
        for i in range(5):
            user_id = f"user_{i}"
            tracker.track_user(user_id, "referral")
            tracker.record_stage_completion(user_id, FunnelStage.LANDING)
            tracker.record_stage_completion(user_id, FunnelStage.SIGNUP)
        
        conversion_rate = tracker.calculate_conversion_rate(
            FunnelStage.LANDING,
            FunnelStage.SIGNUP
        )
        
        assert False, "Test not yet implemented - RED phase"
    
    def test_calculate_all_stage_conversion_rates(self):
        """Test calculating conversion rates for all stage pairs."""
        tracker = FunnelTracker()
        
        for i in range(100):
            user_id = f"user_{i}"
            tracker.track_user(user_id, "organic")
            
            for j, stage in enumerate(FunnelStage.ALL_STAGES):
                if i >= (j * 10):
                    tracker.record_stage_completion(user_id, stage)
        
        assert False, "Test not yet implemented - RED phase"


class TestAttributeConversionsToTrafficSources:
    """Test Acceptance Criterion 3: Attribute conversions to traffic sources correctly."""
    
    def test_track_conversion_source_for_single_user(self):
        """Test tracking traffic source for a single user conversion."""
        tracker = FunnelTracker()
        
        user_id = "user_001"
        tracker.track_user(user_id, "google_ads")
        
        for stage in FunnelStage.ALL_STAGES:
            tracker.record_stage_completion(user_id, stage)
        
        conversions = tracker.get_conversions_by_source(FunnelStage.REVENUE)
        
        assert False, "Test not yet implemented - RED phase"
    
    def test_attribute_conversions_across_multiple_sources(self):
        """Test attribution across multiple traffic sources."""
        tracker = FunnelTracker()
        
        sources = ["organic", "paid", "referral", "direct", "social"]
        
        for i, source in enumerate(sources):
            for j in range(i + 1):
                user_id = f"user_{source}_{j}"
                tracker.track_user(user_id, source)
                
                for stage in FunnelStage.ALL_STAGES:
                    tracker.record_stage_completion(user_id, stage)
        
        conversions = tracker.get_conversions_by_source(FunnelStage.REVENUE)
        
        assert False, "Test not yet implemented - RED phase"
    
    def test_source_attribution_for_partial_conversion(self):
        """Test source attribution for users who partially converted."""
        tracker = FunnelTracker()
        
        tracker.track_user("user_001", "organic")
        tracker.record_stage_completion("user_001", FunnelStage.LANDING)
        tracker.record_stage_completion("user_001", FunnelStage.SIGNUP)
        
        tracker.track_user("user_002", "paid")
        tracker.record_stage_completion("user_002", FunnelStage.LANDING)
        tracker.record_stage_completion("user_002", FunnelStage.SIGNUP)
        tracker.record_stage_completion("user_002", FunnelStage.ACTIVATION)
        
        conversions_signup = tracker.get_conversions_by_source(FunnelStage.SIGNUP)
        conversions_activation = tracker.get_conversions_by_source(FunnelStage.ACTIVATION)
        
        assert False, "Test not yet implemented - RED phase"
    
    def test_source_with_no_conversions(self):
        """Test handling traffic source with no conversions."""
        tracker = FunnelTracker()
        
        tracker.track_user("user_001", "email")
        tracker.record_stage_completion("user_001", FunnelStage.LANDING)
        
        conversions = tracker.get_conversions_by_source(FunnelStage.REVENUE)
        
        assert False, "Test not yet implemented - RED phase"
    
    def test_compare_conversion_rates_by_source(self):
        """Test comparing conversion rates across different sources."""
        tracker = FunnelTracker()
        
        for i in range(10):
            tracker.track_user(f"organic_{i}", "organic")
            tracker.record_stage_completion(f"organic_{i}", FunnelStage.LANDING)
            
            if i < 8:
                tracker.record_stage_completion(f"organic_{i}", FunnelStage.SIGNUP)
        
        for i in range(10):
            tracker.track_user(f"paid_{i}", "paid")
            tracker.record_stage_completion(f"paid_{i}", FunnelStage.LANDING)
            
            if i < 5:
                tracker.record_stage_completion(f"paid_{i}", Funn