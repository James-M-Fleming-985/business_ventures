```python
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Union
from enum import Enum


class AttributionModel(Enum):
    FIRST_TOUCH = "first_touch"
    LAST_TOUCH = "last_touch"
    LINEAR = "linear"


class FinancialMetricsCalculator:
    """Calculator for financial metrics including CAC, LTV, MRR, and ARR."""
    
    def __init__(self):
        self.cohort_data = {}
        self.subscription_data = {}
        
    def calculate_cac(
        self,
        marketing_spend: float,
        sales_spend: float,
        customers_acquired: int,
        attribution_model: str = "linear",
        touchpoint_data: Optional[List[Dict]] = None
    ) -> Dict[str, float]:
        """
        Calculate Customer Acquisition Cost with different attribution models.
        
        Args:
            marketing_spend: Total marketing spend
            sales_spend: Total sales spend
            customers_acquired: Number of customers acquired
            attribution_model: Attribution model to use (first_touch, last_touch, linear)
            touchpoint_data: Optional touchpoint data for attribution
            
        Returns:
            Dictionary with CAC calculations
        """
        if customers_acquired == 0:
            return {
                "cac": 0.0,
                "marketing_cac": 0.0,
                "sales_cac": 0.0,
                "attribution_model": attribution_model
            }
        
        total_spend = marketing_spend + sales_spend
        base_cac = total_spend / customers_acquired
        
        result = {
            "cac": round(base_cac, 2),
            "marketing_cac": round(marketing_spend / customers_acquired, 2),
            "sales_cac": round(sales_spend / customers_acquired, 2),
            "attribution_model": attribution_model
        }
        
        if touchpoint_data:
            attributed_cac = self._apply_attribution_model(
                touchpoint_data, attribution_model, total_spend, customers_acquired
            )
            result["attributed_cac"] = round(attributed_cac, 2)
        
        return result
    
    def _apply_attribution_model(
        self,
        touchpoint_data: List[Dict],
        model: str,
        total_spend: float,
        customers_acquired: int
    ) -> float:
        """Apply attribution model to touchpoint data."""
        if model == "first_touch":
            return self._first_touch_attribution(touchpoint_data, total_spend, customers_acquired)
        elif model == "last_touch":
            return self._last_touch_attribution(touchpoint_data, total_spend, customers_acquired)
        elif model == "linear":
            return self._linear_attribution(touchpoint_data, total_spend, customers_acquired)
        else:
            return total_spend / customers_acquired if customers_acquired > 0 else 0.0
    
    def _first_touch_attribution(
        self, touchpoint_data: List[Dict], total_spend: float, customers_acquired: int
    ) -> float:
        """Calculate CAC using first touch attribution."""
        first_touch_spend = sum(
            tp.get("spend", 0) for tp in touchpoint_data if tp.get("position") == "first"
        )
        return first_touch_spend / customers_acquired if customers_acquired > 0 else 0.0
    
    def _last_touch_attribution(
        self, touchpoint_data: List[Dict], total_spend: float, customers_acquired: int
    ) -> float:
        """Calculate CAC using last touch attribution."""
        last_touch_spend = sum(
            tp.get("spend", 0) for tp in touchpoint_data if tp.get("position") == "last"
        )
        return last_touch_spend / customers_acquired if customers_acquired > 0 else 0.0
    
    def _linear_attribution(
        self, touchpoint_data: List[Dict], total_spend: float, customers_acquired: int
    ) -> float:
        """Calculate CAC using linear attribution."""
        if not touchpoint_data or customers_acquired == 0:
            return 0.0
        
        # Group touchpoints by customer
        customer_touchpoints = {}
        for tp in touchpoint_data:
            customer_id = tp.get("customer_id")
            if customer_id not in customer_touchpoints:
                customer_touchpoints[customer_id] = []
            customer_touchpoints[customer_id].append(tp)
        
        total_attributed_spend = 0.0
        for customer_id, touchpoints in customer_touchpoints.items():
            num_touchpoints = len(touchpoints)
            if num_touchpoints > 0:
                customer_spend = sum(tp.get("spend", 0) for tp in touchpoints)
                total_attributed_spend += customer_spend / num_touchpoints * num_touchpoints
        
        if total_attributed_spend == 0:
            return total_spend / customers_acquired
        
        return total_attributed_spend / customers_acquired
    
    def estimate_ltv(
        self,
        cohort_data: pd.DataFrame,
        cohort_period: str = "monthly",
        discount_rate: float = 0.0,
        min_days: int = 90
    ) -> Dict[str, float]:
        """
        Estimate Lifetime Value using cohort analysis.
        
        Args:
            cohort_data: DataFrame with cohort revenue data
            cohort_period: Period for cohort analysis (monthly, quarterly)
            discount_rate: Discount rate for future cash flows
            min_days: Minimum days of data required (default 90)
            
        Returns:
            Dictionary with LTV estimates
        """
        if cohort_data.empty:
            return {
                "ltv": 0.0,
                "average_revenue_per_customer": 0.0,
                "cohort_period": cohort_period,
                "min_days": min_days
            }
        
        # Ensure required columns exist
        required_cols = ["cohort", "period", "revenue", "customers"]
        for col in required_cols:
            if col not in cohort_data.columns:
                cohort_data[col] = 0
        
        # Calculate average revenue per customer per period
        cohort_data["arpc"] = cohort_data.apply(
            lambda row: row["revenue"] / row["customers"] if row["customers"] > 0 else 0,
            axis=1
        )
        
        # Group by cohort and calculate total LTV
        cohort_ltv = {}
        for cohort in cohort_data["cohort"].unique():
            cohort_df = cohort_data[cohort_data["cohort"] == cohort].sort_values("period")
            
            ltv = 0.0
            for idx, row in cohort_df.iterrows():
                period = row["period"]
                arpc = row["arpc"]
                
                if discount_rate > 0:
                    discounted_arpc = arpc / ((1 + discount_rate) ** period)
                    ltv += discounted_arpc
                else:
                    ltv += arpc
            
            cohort_ltv[cohort] = ltv
        
        # Calculate overall average LTV
        avg_ltv = np.mean(list(cohort_ltv.values())) if cohort_ltv else 0.0
        
        # Calculate average revenue per customer
        total_revenue = cohort_data["revenue"].sum()
        total_customers = cohort_data.groupby("cohort")["customers"].first().sum()
        avg_revenue_per_customer = total_revenue / total_customers if total_customers > 0 else 0.0
        
        return {
            "ltv": round(avg_ltv, 2),
            "average_revenue_per_customer": round(avg_revenue_per_customer, 2),
            "cohort_ltv": {k: round(v, 2) for k, v in cohort_ltv.items()},
            "cohort_period": cohort_period,
            "min_days": min_days
        }
    
    def calculate_mrr(
        self,
        subscription_data: pd.DataFrame,
        as_of_date: Optional[datetime] = None
    ) -> Dict[str, float]:
        """
        Calculate Monthly Recurring Revenue.
        
        Args:
            subscription_data: DataFrame with subscription information
            as_of_date: Date to calculate MRR as of (default: current date)
            
        Returns:
            Dictionary with MRR metrics
        """
        if subscription_data.empty:
            return {
                "mrr": 0.0,
                "new_mrr": 0.0,
                "expansion_mrr": 0.0,
                "contraction_mrr": 0.0,
                "churn_mrr": 0.0,
                "net_new_mrr": 0.0
            }
        
        if as_of_date is None:
            as_of_date = datetime.now()
        
        # Filter active subscriptions
        active_subs = subscription_data.copy()
        
        # Calculate MRR based on subscription frequency
        def calculate_monthly_value(row):
            amount = row.get("amount", 0)
            frequency = row.get("frequency", "monthly").lower()
            
            if frequency == "monthly":
                return amount
            elif frequency == "annual" or frequency == "yearly":
                return amount / 12
            elif frequency == "quarterly":
                return amount / 3
            elif frequency == "weekly":
                return amount * 52 / 12
            else:
                return amount
        
        active_subs["mrr_amount"] = active_subs.apply(calculate_monthly_value, axis=1)
        
        total_mrr = active_subs["mrr_amount"].sum()
        
        # Calculate MRR components
        new_mrr = active_subs[active_subs.get("status") == "new"]["mrr_amount"].sum() if "status" in active_subs.columns else 0.0
        expansion_mrr = active_subs[active_subs.get("status") == "expansion"]["mrr_amount"].sum() if "status" in active_subs.columns else 0.0
        contraction_mrr = active_subs[active_subs.get("status") == "contraction"]["mrr_amount"].sum() if "status" in active_subs.columns else 0.0
        churn_mrr = active_subs[active_subs.get("status") == "churned"]["mrr_amount"].sum() if "status" in active_subs.columns else 0.0
        
        net_new_mrr = new_mrr + expansion_mrr - contraction_mrr - churn_mrr
        
        return {
            "mrr": round(total_mrr, 2),
            "new_mrr": round(new_mrr, 2),
            "expansion_mrr": round(expansion_mrr, 2),
            "contraction_mrr": round(contraction_mrr, 2),
            "churn_mrr": round(churn_mrr, 2),
            "net_new_mrr": round(net_new_mrr, 2)
        }
    
    def calculate_arr(
        self,
        subscription_data: pd.DataFrame,
        as_of_date: Optional[datetime] = None
    ) -> Dict[str, float]:
        """
        Calculate Annual Recurring Revenue.
        
        Args:
            subscription_data: DataFrame with subscription information
            as_of_date: Date to calculate ARR as of (default: current date)
            
        Returns:
            Dictionary with ARR metrics
        """
        mrr_data = self.calculate_mrr(subscription_data, as_of_date)
        
        arr = mrr_data["mrr"] * 12
        new_arr = mrr_data["new_mrr"] * 12
        expansion_arr = mrr_data["expansion_mrr"] * 12
        contraction_arr = mrr_data["contraction_mrr"] * 12
        churn_arr = mrr_data["churn_mrr"] * 12
        net_new_arr = mrr_data["net_new_mrr"] * 12
        
        return {
            "arr": round(arr, 2),
            "new_arr": round(new_arr, 2),
            "expansion_arr": round(expansion_arr, 2),
            "contraction_arr": round(contraction_arr, 2),
            "churn_arr": round(churn_arr, 2),
            "net_new_arr": round(net_new_arr, 2)
        }
    
    def generate_cohort_retention_curve(
        self,
        cohort_data: pd.DataFrame,
        cohort_column: str = "cohort",
        period_column: str = "period",
        customers_column: str = "customers"
    ) -> Dict[str, List[float]]:
        """
        Generate cohort retention curves.
        
        Args:
            cohort_data: DataFrame with cohort data
            cohort_column: Name of cohort column
            period_column: Name of period column
            customers_column: Name of customers column
            
        Returns:
            Dictionary with retention curves for each cohort
        """
        if cohort_data.empty:
            return {}
        
        retention_curves = {}
        
        for cohort in cohort_data[cohort_column].unique():
            cohort_df = cohort_data[cohort_data[cohort_column] == cohort].sort_values(period_column)
            
            if cohort_df.empty:
                continue
            
            # Get initial customer count (period 0)
            initial_customers = cohort_df[cohort_df[period_column] == 0][customers_column].values
            if len(initial_customers) == 0:
                initial_customers = cohort_df[customers_column].iloc[0]
            else:
                initial_customers = initial_customers[0]
            
            if initial_customers == 0:
                continue
            
            # Calculate retention rate for each period
            retention_rates = []
            for _, row in cohort_df.iterrows():
                retention_rate = (row[customers_column] / initial_customers) * 100
                retention_rates.append(round(retention_rate, 2))
            
            retention_curves[str(cohort)] = retention_rates
        
        return retention_curves
    
    def calculate_cohort_metrics(
        self,
        cohort_data: pd.DataFrame,
        include_retention: bool = True,
        include_revenue: bool = True
    ) -> Dict:
        """
        Calculate comprehensive cohort metrics.
        
        Args:
            cohort_data: DataFrame with cohort data
            include_retention: Whether to include retention curves
            include_revenue: Whether to include revenue metrics
            
        Returns:
            Dictionary with cohort metrics
        """
        metrics = {}
        
        if include_retention:
            retention_curves = self.generate_cohort_retention_curve(cohort_data)
            metrics["retention_curves"] = retention_curves
        
        if include_revenue and "revenue" in cohort_data.columns:
            ltv_data = self.estimate_ltv(cohort_data)
            metrics["ltv_data"] = ltv_data
        
        return metrics


def calculate_cac(
    marketing_spend: float,
    sales_spend: float,
    customers_acquired: int,
    attribution_model: str = "linear",
    touchpoint_data: Optional[List[Dict]] = None
) -> Dict[str, float]:
    """Convenience function to calculate CAC."""
    calculator = FinancialMetricsCalculator()
    return calculator.calculate_cac(