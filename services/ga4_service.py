"""
GA4 (Google Analytics 4) Service (Track G — M1)

Pulls engagement metrics from GA4 and populates ProductMetrics rows
for each active ProductDeployment.

Requires environment variables:
  GA4_PROPERTY_ID        — GA4 property ID (e.g. "properties/123456789")
  GA4_CREDENTIALS_JSON   — path to service-account JSON or inline JSON

When credentials are not configured, the service logs a warning and
returns stub data so the rest of the platform continues to function.
"""

import json
import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from models import ProductDeployment, ProductMetrics

logger = logging.getLogger(__name__)

GA4_PROPERTY_ID = os.getenv("GA4_PROPERTY_ID")
GA4_CREDENTIALS_JSON = os.getenv("GA4_CREDENTIALS_JSON")

_analytics_client = None


def _get_analytics_client():
    """Lazily initialise the GA4 Data API client."""
    global _analytics_client
    if _analytics_client is not None:
        return _analytics_client

    if not GA4_PROPERTY_ID or not GA4_CREDENTIALS_JSON:
        logger.info("GA4 not configured (GA4_PROPERTY_ID / GA4_CREDENTIALS_JSON missing)")
        return None

    try:
        from google.analytics.data_v1beta import BetaAnalyticsDataClient
        from google.oauth2 import service_account

        # Support both file path and inline JSON
        if os.path.isfile(GA4_CREDENTIALS_JSON):
            credentials = service_account.Credentials.from_service_account_file(
                GA4_CREDENTIALS_JSON,
                scopes=["https://www.googleapis.com/auth/analytics.readonly"],
            )
        else:
            info = json.loads(GA4_CREDENTIALS_JSON)
            credentials = service_account.Credentials.from_service_account_info(
                info,
                scopes=["https://www.googleapis.com/auth/analytics.readonly"],
            )

        _analytics_client = BetaAnalyticsDataClient(credentials=credentials)
        logger.info("GA4 BetaAnalyticsDataClient initialised for %s", GA4_PROPERTY_ID)
        return _analytics_client
    except Exception as exc:
        logger.warning("Could not initialise GA4 client: %s", exc)
        return None


def fetch_engagement_metrics(
    hostname: str,
    days: int = 30,
) -> Dict[str, Any]:
    """Fetch page views, unique users, avg session duration from GA4
    for a specific hostname (the deployed MVP's domain).

    Returns a dict with keys: page_views, unique_visitors, avg_session_seconds.
    Returns zeros if GA4 is not configured.
    """
    client = _get_analytics_client()
    if client is None:
        return {"page_views": 0, "unique_visitors": 0, "avg_session_seconds": 0.0}

    try:
        from google.analytics.data_v1beta.types import (
            DateRange,
            Dimension,
            FilterExpression,
            Filter,
            Metric,
            RunReportRequest,
        )

        request = RunReportRequest(
            property=GA4_PROPERTY_ID,
            date_ranges=[DateRange(
                start_date=f"{days}daysAgo",
                end_date="today",
            )],
            dimensions=[Dimension(name="hostName")],
            metrics=[
                Metric(name="screenPageViews"),
                Metric(name="activeUsers"),
                Metric(name="averageSessionDuration"),
            ],
            dimension_filter=FilterExpression(
                filter=Filter(
                    field_name="hostName",
                    string_filter=Filter.StringFilter(
                        value=hostname,
                        match_type=Filter.StringFilter.MatchType.EXACT,
                    ),
                )
            ),
        )

        response = client.run_report(request)

        page_views = 0
        unique_visitors = 0
        avg_session = 0.0

        for row in response.rows:
            page_views += int(row.metric_values[0].value or 0)
            unique_visitors += int(row.metric_values[1].value or 0)
            avg_session = float(row.metric_values[2].value or 0)

        return {
            "page_views": page_views,
            "unique_visitors": unique_visitors,
            "avg_session_seconds": round(avg_session, 2),
        }

    except Exception as exc:
        logger.warning("GA4 fetch failed for %s: %s", hostname, exc)
        return {"page_views": 0, "unique_visitors": 0, "avg_session_seconds": 0.0}


def pull_engagement_for_all_deployments(db: Session) -> Dict[str, int]:
    """Iterate all active ProductDeployments and pull GA4 engagement data
    into ProductMetrics rows.

    Designed to be called periodically (e.g. daily via a scheduled job).

    Returns {"updated": N, "skipped": M, "total": T}.
    """
    deployments = (
        db.query(ProductDeployment)
        .filter(ProductDeployment.status == "active")
        .all()
    )

    updated = 0
    skipped = 0

    for dep in deployments:
        # Determine hostname from railway_url or domain
        hostname = dep.domain
        if not hostname and dep.railway_url:
            # Extract hostname from URL
            from urllib.parse import urlparse
            parsed = urlparse(dep.railway_url)
            hostname = parsed.hostname

        if not hostname:
            skipped += 1
            continue

        data = fetch_engagement_metrics(hostname, days=30)
        if data["page_views"] == 0 and data["unique_visitors"] == 0:
            skipped += 1
            continue

        now = datetime.utcnow()
        period_start = now - timedelta(days=30)

        # Upsert
        existing = (
            db.query(ProductMetrics)
            .filter(
                ProductMetrics.deployment_id == dep.id,
                ProductMetrics.source == "ga4",
                ProductMetrics.period_start >= period_start - timedelta(days=1),
            )
            .first()
        )

        if existing:
            existing.page_views = data["page_views"]
            existing.unique_visitors = data["unique_visitors"]
            existing.avg_session_seconds = data["avg_session_seconds"]
            existing.period_end = now
        else:
            pm = ProductMetrics(
                deployment_id=dep.id,
                period_start=period_start,
                period_end=now,
                page_views=data["page_views"],
                unique_visitors=data["unique_visitors"],
                avg_session_seconds=data["avg_session_seconds"],
                source="ga4",
            )
            db.add(pm)

        updated += 1

    if updated > 0:
        db.commit()

    logger.info("GA4 pull complete: %d updated, %d skipped, %d total", updated, skipped, len(deployments))
    return {"updated": updated, "skipped": skipped, "total": len(deployments)}
