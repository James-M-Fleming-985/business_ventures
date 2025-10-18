```python
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Union, Any
from datetime import datetime
import logging
from dataclasses import dataclass
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class QualityMetric(Enum):
    """Enumeration of quality metrics."""
    COMPLETENESS = "completeness"
    ACCURACY = "accuracy"
    CONSISTENCY = "consistency"
    VALIDITY = "validity"
    UNIQUENESS = "uniqueness"
    TIMELINESS = "timeliness"


@dataclass
class QualityScore:
    """Data class for quality scores."""
    metric: str
    score: float
    details: Optional[Dict[str, Any]] = None
    timestamp: Optional[datetime] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class DataQualityChecker:
    """
    A comprehensive data quality checker that calculates various quality metrics
    for ingested data.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the DataQualityChecker.

        Args:
            config: Optional configuration dictionary for quality thresholds and rules
        """
        self.config = config or {}
        self.quality_scores: List[QualityScore] = []
        self.thresholds = {
            QualityMetric.COMPLETENESS: self.config.get('completeness_threshold', 0.9),
            QualityMetric.ACCURACY: self.config.get('accuracy_threshold', 0.95),
            QualityMetric.CONSISTENCY: self.config.get('consistency_threshold', 0.9),
            QualityMetric.VALIDITY: self.config.get('validity_threshold', 0.95),
            QualityMetric.UNIQUENESS: self.config.get('uniqueness_threshold', 0.99),
            QualityMetric.TIMELINESS: self.config.get('timeliness_threshold', 0.95)
        }

    def check_data_quality(self, data: Union[pd.DataFrame, Dict, List]) -> Dict[str, float]:
        """
        Calculate quality scores for all ingested data.

        Args:
            data: The data to check quality for (DataFrame, dict, or list)

        Returns:
            Dictionary containing quality scores for each metric

        Raises:
            ValueError: If data format is not supported
            TypeError: If data type is invalid
        """
        if data is None:
            raise ValueError("Data cannot be None")

        # Convert data to DataFrame for uniform processing
        df = self._convert_to_dataframe(data)

        # Calculate all quality metrics
        quality_results = {
            QualityMetric.COMPLETENESS.value: self._calculate_completeness(df),
            QualityMetric.ACCURACY.value: self._calculate_accuracy(df),
            QualityMetric.CONSISTENCY.value: self._calculate_consistency(df),
            QualityMetric.VALIDITY.value: self._calculate_validity(df),
            QualityMetric.UNIQUENESS.value: self._calculate_uniqueness(df),
            QualityMetric.TIMELINESS.value: self._calculate_timeliness(df)
        }

        # Store quality scores
        for metric, score in quality_results.items():
            self.quality_scores.append(
                QualityScore(metric=metric, score=score)
            )

        logger.info(f"Quality check completed. Overall scores: {quality_results}")

        return quality_results

    def _convert_to_dataframe(self, data: Union[pd.DataFrame, Dict, List]) -> pd.DataFrame:
        """
        Convert various data types to pandas DataFrame.

        Args:
            data: Input data in various formats

        Returns:
            pandas DataFrame

        Raises:
            TypeError: If data type is not supported
        """
        if isinstance(data, pd.DataFrame):
            return data
        elif isinstance(data, dict):
            # Handle nested dictionaries
            if all(isinstance(v, dict) for v in data.values()):
                return pd.DataFrame(data).T
            else:
                return pd.DataFrame([data])
        elif isinstance(data, list):
            if not data:
                return pd.DataFrame()
            elif isinstance(data[0], dict):
                return pd.DataFrame(data)
            else:
                return pd.DataFrame(data, columns=['value'])
        else:
            raise TypeError(f"Unsupported data type: {type(data)}")

    def _calculate_completeness(self, df: pd.DataFrame) -> float:
        """
        Calculate completeness score (percentage of non-null values).

        Args:
            df: DataFrame to check

        Returns:
            Completeness score between 0 and 1
        """
        if df.empty:
            return 1.0

        total_cells = df.size
        non_null_cells = df.count().sum()

        completeness = non_null_cells / total_cells if total_cells > 0 else 1.0

        logger.debug(f"Completeness: {completeness:.4f} ({non_null_cells}/{total_cells})")

        return completeness

    def _calculate_accuracy(self, df: pd.DataFrame) -> float:
        """
        Calculate accuracy score based on data type validation and range checks.

        Args:
            df: DataFrame to check

        Returns:
            Accuracy score between 0 and 1
        """
        if df.empty:
            return 1.0

        accuracy_scores = []

        for column in df.columns:
            col_data = df[column].dropna()
            if col_data.empty:
                accuracy_scores.append(1.0)
                continue

            # Check numeric columns for outliers
            if pd.api.types.is_numeric_dtype(col_data):
                # Use IQR method for outlier detection
                Q1 = col_data.quantile(0.25)
                Q3 = col_data.quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR

                outliers = ((col_data < lower_bound) | (col_data > upper_bound)).sum()
                accuracy = 1 - (outliers / len(col_data))
                accuracy_scores.append(accuracy)

            # Check string columns for validity
            elif pd.api.types.is_string_dtype(col_data):
                # Check for empty strings or suspicious patterns
                invalid = col_data.str.strip().eq('').sum()
                accuracy = 1 - (invalid / len(col_data))
                accuracy_scores.append(accuracy)

            else:
                accuracy_scores.append(1.0)

        return np.mean(accuracy_scores) if accuracy_scores else 1.0

    def _calculate_consistency(self, df: pd.DataFrame) -> float:
        """
        Calculate consistency score by checking data format and patterns.

        Args:
            df: DataFrame to check

        Returns:
            Consistency score between 0 and 1
        """
        if df.empty:
            return 1.0

        consistency_scores = []

        for column in df.columns:
            col_data = df[column].dropna()
            if col_data.empty:
                consistency_scores.append(1.0)
                continue

            # Check string columns for consistent patterns
            if pd.api.types.is_string_dtype(col_data):
                # Check for consistent case
                unique_values = col_data.nunique()
                unique_lower = col_data.str.lower().nunique()
                case_consistency = unique_lower / unique_values if unique_values > 0 else 1.0

                # Check for consistent length patterns
                lengths = col_data.str.len()
                length_cv = lengths.std() / lengths.mean() if lengths.mean() > 0 else 0
                length_consistency = 1 - min(length_cv, 1)

                consistency = (case_consistency + length_consistency) / 2
                consistency_scores.append(consistency)

            # Check numeric columns for consistent scale
            elif pd.api.types.is_numeric_dtype(col_data):
                if len(col_data) > 1:
                    # Check for consistent magnitude
                    magnitude_range = np.log10(col_data.abs().max() + 1) - np.log10(col_data.abs().min() + 1)
                    consistency = 1 / (1 + magnitude_range / 10)  # Normalize to 0-1
                    consistency_scores.append(consistency)
                else:
                    consistency_scores.append(1.0)

            else:
                consistency_scores.append(1.0)

        return np.mean(consistency_scores) if consistency_scores else 1.0

    def _calculate_validity(self, df: pd.DataFrame) -> float:
        """
        Calculate validity score by checking data against expected formats and rules.

        Args:
            df: DataFrame to check

        Returns:
            Validity score between 0 and 1
        """
        if df.empty:
            return 1.0

        validity_scores = []

        for column in df.columns:
            col_data = df[column].dropna()
            if col_data.empty:
                validity_scores.append(1.0)
                continue

            # Apply validity rules based on column name patterns
            column_lower = column.lower()

            if 'email' in column_lower:
                # Simple email validation
                valid_emails = col_data.astype(str).str.contains(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', regex=True)
                validity = valid_emails.sum() / len(col_data)
                validity_scores.append(validity)

            elif 'phone' in column_lower:
                # Simple phone validation (digits and common separators)
                valid_phones = col_data.astype(str).str.contains(r'^[\d\s\-\(\)\+]+$', regex=True)
                validity = valid_phones.sum() / len(col_data)
                validity_scores.append(validity)

            elif 'date' in column_lower or 'time' in column_lower:
                # Try to parse as datetime
                try:
                    pd.to_datetime(col_data)
                    validity_scores.append(1.0)
                except:
                    validity_scores.append(0.5)

            elif pd.api.types.is_numeric_dtype(col_data):
                # Check for valid numeric values (no inf or extreme values)
                valid_nums = ~(np.isinf(col_data) | (np.abs(col_data) > 1e15))
                validity = valid_nums.sum() / len(col_data)
                validity_scores.append(validity)

            else:
                # Default validity check
                validity_scores.append(0.95)

        return np.mean(validity_scores) if validity_scores else 1.0

    def _calculate_uniqueness(self, df: pd.DataFrame) -> float:
        """
        Calculate uniqueness score by checking for duplicate records.

        Args:
            df: DataFrame to check

        Returns:
            Uniqueness score between 0 and 1
        """
        if df.empty or len(df) <= 1:
            return 1.0

        # Check for duplicate rows
        unique_rows = len(df.drop_duplicates())
        total_rows = len(df)

        uniqueness = unique_rows / total_rows if total_rows > 0 else 1.0

        logger.debug(f"Uniqueness: {uniqueness:.4f} ({unique_rows}/{total_rows} unique rows)")

        return uniqueness

    def _calculate_timeliness(self, df: pd.DataFrame) -> float:
        """
        Calculate timeliness score based on data freshness.

        Args:
            df: DataFrame to check

        Returns:
            Timeliness score between 0 and 1
        """
        if df.empty:
            return 1.0

        # Look for date/time columns
        date_columns = []
        for column in df.columns:
            column_lower = column.lower()
            if any(term in column_lower for term in ['date', 'time', 'created', 'updated', 'timestamp']):
                try:
                    df[column] = pd.to_datetime(df[column])
                    date_columns.append(column)
                except:
                    pass

        if not date_columns:
            # If no date columns found, assume data is current
            return 0.95

        # Calculate freshness for each date column
        timeliness_scores = []
        current_time = pd.Timestamp.now()

        for column in date_columns:
            col_data = df[column].dropna()
            if col_data.empty:
                continue

            # Calculate age of data in days
            ages = (current_time - col_data).dt.total_seconds() / 86400  # Convert to days

            # Define freshness thresholds (customize based on requirements)
            fresh_threshold = 7  # days
            stale_threshold = 30  # days

            # Calculate timeliness score
            fresh_data = (ages <= fresh_threshold).sum()
            moderate_data = ((ages > fresh_threshold) & (ages <= stale_threshold)).sum()
            stale_data = (ages > stale_threshold).sum()

            timeliness = (
                fresh_data * 1.0 +
                moderate_data * 0.7 +
                stale_data * 0.3
            ) / len(col_data)

            timeliness_scores.append(timeliness)

        return np.mean(timeliness_scores) if timeliness_scores else 0.95

    def get_quality_report(self) -> Dict[str, Any]:
        """
        Generate a comprehensive quality report.

        Returns:
            Dictionary containing quality report with scores and recommendations
        """
        if not self.quality_scores:
            return {
                "status": "No quality checks performed",
                "scores": {},
                "recommendations": []
            }

        # Group scores by metric
        metric_scores = {}
        for score in self.quality_scores:
            if score.metric not in metric_scores:
                metric_scores[score.metric] = []
            metric_scores[score.metric].append(score.score)

        # Calculate average scores
        avg_scores = {
            metric: np.mean(scores)
            for metric, scores in metric_scores.items()
        }

        # Generate recommendations
        recommendations = []
        for metric, avg_score in avg_scores.items():
            threshold = self.thresholds.get(QualityMetric(metric), 0.9)
            if avg_score < threshold:
                recommendations.append({
                    "metric": metric,
                    "score": avg_score,
                    "threshold": threshold,
                    "recommendation": f"Improve {metric} - current score {avg_score:.2f} is below threshold {threshold:.2f}"
                })

        # Calculate overall quality score
        overall_score = np.mean(list(avg_scores.values()))

        return {
            "status": "Quality check completed",
            "overall_score": overall_score,
            "scores": avg_scores,
            "recommendations": recommendations,
            "total_checks": len(self.quality_scores),
            "timestamp": datetime.now().isoformat()
        }

    def reset(self):
        """Reset the quality checker, clearing all stored scores."""
        self.quality_scores = []
        logger.info("Quality checker reset")
```