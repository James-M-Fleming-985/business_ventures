```python
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from uuid import uuid4


class Action(Enum):
    ARCHIVE = "archive"
    ESCALATE = "escalate"
    MONITOR = "monitor"
    REVIEW = "review"
    NO_ACTION = "no_action"


class Trend(Enum):
    INCREASING = "increasing"
    DECREASING = "decreasing"
    STABLE = "stable"
    UNKNOWN = "unknown"


@dataclass
class DecisionRationale:
    score: float
    trend: Trend
    threshold_met: bool
    override_applied: bool
    factors: List[str]
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Decision:
    decision_id: str
    action: Action
    rationale: DecisionRationale
    manual_override: bool = False
    override_reason: Optional[str] = None
    override_by: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class AuditEntry:
    entry_id: str
    decision_id: str
    action: Action
    original_action: Optional[Action]
    override_by: str
    override_reason: str
    timestamp: datetime
    context: Dict[str, Any]


class DecisionEngine:
    def __init__(self, archive_threshold: float = 5.0, escalate_threshold: float = 70.0):
        self.archive_threshold = archive_threshold
        self.escalate_threshold = escalate_threshold
        self.decisions: List[Decision] = []
        self.audit_trail: List[AuditEntry] = []
        self.logger = logging.getLogger(__name__)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

    def make_decision(
        self,
        score: float,
        trend: Trend,
        context: Optional[Dict[str, Any]] = None
    ) -> Decision:
        """
        Make a decision based on score and trend.
        
        Args:
            score: The numerical score (0-100)
            trend: The trend direction
            context: Additional context for decision making
            
        Returns:
            Decision object with action and rationale
        """
        context = context or {}
        factors = []
        
        # Determine action based on score and trend
        if score < self.archive_threshold:
            action = Action.ARCHIVE
            threshold_met = True
            factors.append(f"Score {score} below archive threshold {self.archive_threshold}")
            
            # Apply false positive detection
            if trend == Trend.INCREASING:
                factors.append("Increasing trend detected - potential false positive")
                # Check if increase is significant
                if context.get("recent_increase", 0) > 2.0:
                    action = Action.MONITOR
                    threshold_met = False
                    factors.append("Recent increase significant - switching to MONITOR")
                    
        elif score >= self.escalate_threshold:
            action = Action.ESCALATE
            threshold_met = True
            factors.append(f"Score {score} above escalation threshold {self.escalate_threshold}")
            
        elif self.archive_threshold <= score < self.escalate_threshold:
            if trend == Trend.INCREASING:
                action = Action.MONITOR
                factors.append("Score in mid-range with increasing trend")
            elif trend == Trend.DECREASING:
                action = Action.REVIEW
                factors.append("Score in mid-range with decreasing trend")
            else:
                action = Action.MONITOR
                factors.append("Score in mid-range with stable/unknown trend")
            threshold_met = False
        else:
            action = Action.NO_ACTION
            threshold_met = False
            factors.append("No action criteria met")

        rationale = DecisionRationale(
            score=score,
            trend=trend,
            threshold_met=threshold_met,
            override_applied=False,
            factors=factors
        )

        decision = Decision(
            decision_id=str(uuid4()),
            action=action,
            rationale=rationale,
            manual_override=False
        )

        self.decisions.append(decision)
        self._log_decision(decision)

        return decision

    def apply_manual_override(
        self,
        decision_id: str,
        new_action: Action,
        override_by: str,
        override_reason: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Decision:
        """
        Apply manual override to an existing decision.
        
        Args:
            decision_id: ID of the decision to override
            new_action: New action to apply
            override_by: User/system applying the override
            override_reason: Reason for override
            context: Additional context
            
        Returns:
            Updated decision with override applied
        """
        context = context or {}
        
        # Find the decision
        decision = None
        for d in self.decisions:
            if d.decision_id == decision_id:
                decision = d
                break
        
        if not decision:
            raise ValueError(f"Decision {decision_id} not found")

        original_action = decision.action
        
        # Update decision
        decision.action = new_action
        decision.manual_override = True
        decision.override_reason = override_reason
        decision.override_by = override_by
        decision.rationale.override_applied = True
        decision.rationale.factors.append(
            f"Manual override applied by {override_by}: {override_reason}"
        )

        # Create audit entry
        audit_entry = AuditEntry(
            entry_id=str(uuid4()),
            decision_id=decision_id,
            action=new_action,
            original_action=original_action,
            override_by=override_by,
            override_reason=override_reason,
            timestamp=datetime.utcnow(),
            context=context
        )
        
        self.audit_trail.append(audit_entry)
        self._log_override(audit_entry, decision)

        return decision

    def get_decision(self, decision_id: str) -> Optional[Decision]:
        """Get a decision by ID."""
        for decision in self.decisions:
            if decision.decision_id == decision_id:
                return decision
        return None

    def get_audit_trail(self, decision_id: Optional[str] = None) -> List[AuditEntry]:
        """
        Get audit trail entries.
        
        Args:
            decision_id: Optional filter by decision ID
            
        Returns:
            List of audit entries
        """
        if decision_id:
            return [entry for entry in self.audit_trail if entry.decision_id == decision_id]
        return self.audit_trail.copy()

    def calculate_false_positive_rate(self) -> float:
        """
        Calculate false positive rate for archive decisions.
        
        Returns:
            False positive rate as percentage
        """
        archive_decisions = [
            d for d in self.decisions 
            if d.action == Action.ARCHIVE or (
                d.manual_override and 
                any(e.original_action == Action.ARCHIVE 
                    for e in self.audit_trail 
                    if e.decision_id == d.decision_id)
            )
        ]
        
        if not archive_decisions:
            return 0.0

        # Count false positives (archive decisions that were overridden)
        false_positives = sum(
            1 for d in archive_decisions
            if d.manual_override and d.action != Action.ARCHIVE
        )

        return (false_positives / len(archive_decisions)) * 100

    def _log_decision(self, decision: Decision) -> None:
        """Log decision with complete rationale."""
        self.logger.info(
            f"Decision made: {decision.decision_id} | "
            f"Action: {decision.action.value} | "
            f"Score: {decision.rationale.score} | "
            f"Trend: {decision.rationale.trend.value} | "
            f"Threshold met: {decision.rationale.threshold_met} | "
            f"Factors: {', '.join(decision.rationale.factors)}"
        )

    def _log_override(self, audit_entry: AuditEntry, decision: Decision) -> None:
        """Log override with audit information."""
        self.logger.info(
            f"Override applied: {audit_entry.entry_id} | "
            f"Decision: {decision.decision_id} | "
            f"Original action: {audit_entry.original_action.value if audit_entry.original_action else 'None'} | "
            f"New action: {audit_entry.action.value} | "
            f"By: {audit_entry.override_by} | "
            f"Reason: {audit_entry.override_reason}"
        )

    def get_all_decisions(self) -> List[Decision]:
        """Get all decisions."""
        return self.decisions.copy()

    def reset(self) -> None:
        """Reset engine state (useful for testing)."""
        self.decisions.clear()
        self.audit_trail.clear()
```