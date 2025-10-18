"""Quality Checker Service - Layer: Quality Check

Enforces data quality standards and rules.
"""

from typing import Any, Dict, List
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)


class QualityIssue(BaseModel):
    """Represents a data quality issue."""
    field: str
    issue_type: str
    message: str
    severity: str  # 'error', 'warning', 'info'


class QualityReport(BaseModel):
    """Quality check report."""
    passed: bool
    score: float  # 0.0 to 1.0
    issues: List[QualityIssue] = []


class QualityChecker:
    """Checks data quality against defined rules."""
    
    def __init__(self):
        """Initialize quality checker."""
        self.rules: Dict[str, Any] = {}
        logger.info("QualityChecker initialized")
    
    async def check_completeness(self, data: Dict[str, Any]) -> QualityReport:
        """Check if required fields are present.
        
        Args:
            data: Data to check
            
        Returns:
            Quality report
        """
        issues = []
        required_fields = self.rules.get('required_fields', [])
        
        for field in required_fields:
            if field not in data or data[field] is None:
                issues.append(QualityIssue(
                    field=field,
                    issue_type='missing_field',
                    message=f'Required field {field} is missing or null',
                    severity='error'
                ))
        
        score = 1.0 - (len(issues) / max(len(required_fields), 1))
        return QualityReport(
            passed=len(issues) == 0,
            score=score,
            issues=issues
        )
    
    async def check_ranges(self, data: Dict[str, Any]) -> QualityReport:
        """Check if numeric values are within expected ranges.
        
        Args:
            data: Data to check
            
        Returns:
            Quality report
        """
        issues = []
        range_rules = self.rules.get('ranges', {})
        
        for field, (min_val, max_val) in range_rules.items():
            if field in data:
                value = data[field]
                if not isinstance(value, (int, float)):
                    continue
                if value < min_val or value > max_val:
                    issues.append(QualityIssue(
                        field=field,
                        issue_type='out_of_range',
                        message=f'{field}={value} outside range [{min_val}, {max_val}]',
                        severity='warning'
                    ))
        
        score = 1.0 - (len(issues) / max(len(range_rules), 1))
        return QualityReport(
            passed=len(issues) == 0,
            score=score,
            issues=issues
        )
    
    async def check_quality(self, data: Dict[str, Any]) -> QualityReport:
        """Run all quality checks.
        
        Args:
            data: Data to check
            
        Returns:
            Aggregated quality report
        """
        completeness = await self.check_completeness(data)
        ranges = await self.check_ranges(data)
        
        all_issues = completeness.issues + ranges.issues
        avg_score = (completeness.score + ranges.score) / 2
        
        return QualityReport(
            passed=completeness.passed and ranges.passed,
            score=avg_score,
            issues=all_issues
        )
    
    def set_rules(self, rules: Dict[str, Any]) -> None:
        """Configure quality rules.
        
        Args:
            rules: Dictionary of quality rules
        """
        self.rules = rules
        logger.info(f"Quality rules configured: {list(rules.keys())}")
