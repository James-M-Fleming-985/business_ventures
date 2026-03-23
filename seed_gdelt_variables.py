"""
Seed GDELT Variables — Create VariableMetadata for GDELT sentiment themes.

Run once:  python seed_gdelt_variables.py
Idempotent: skips any variable whose name already exists.
"""

import json
import logging
from datetime import datetime

from database import get_db_session
from models import VariableMetadata

logger = logging.getLogger(__name__)

# Each entry: (name, display_name, theme, unit)
# GDELT themes: https://blog.gdeltproject.org/gdelt-2-0-our-global-world-in-realtime/
GDELT_VARIABLES = [
    # --- Economic Themes ---
    ("gdelt_econ_bankruptcy", "Global Bankruptcy Sentiment", "ECON_BANKRUPTCY", "tone"),
    ("gdelt_econ_debt", "Global Debt Sentiment", "ECON_DEBT", "tone"),
    ("gdelt_econ_inflation", "Global Inflation Sentiment", "ECON_INFLATION", "tone"),
    ("gdelt_econ_unemployment", "Global Unemployment Sentiment", "ECON_UNEMPLOYMENT", "tone"),
    ("gdelt_econ_trade", "Global Trade Sentiment", "ECON_TRADE", "tone"),
    ("gdelt_econ_housing", "Global Housing Market Sentiment", "ECON_HOUSING", "tone"),
    ("gdelt_econ_energy", "Global Energy Market Sentiment", "ECON_ENERGYPRICE", "tone"),
    ("gdelt_econ_stockmarket", "Global Stock Market Sentiment", "ECON_STOCKMARKET", "tone"),
    ("gdelt_econ_interest_rate", "Global Interest Rate Sentiment", "ECON_INTERESTRATE", "tone"),

    # --- Technology & Innovation ---
    ("gdelt_tech_ai", "AI Technology Sentiment", "TECH_AI", "tone"),
    ("gdelt_tech_cyber", "Cybersecurity Sentiment", "SECURITY_CYBER", "tone"),
    ("gdelt_tech_blockchain", "Blockchain Sentiment", "TECH_BLOCKCHAIN", "tone"),

    # --- Geopolitical Risk ---
    ("gdelt_conflict_armed", "Armed Conflict Sentiment", "CONFLICT_ARMED", "tone"),
    ("gdelt_protest", "Global Protest Sentiment", "PROTEST", "tone"),
    ("gdelt_terror", "Terrorism Sentiment", "TERROR", "tone"),
    ("gdelt_sanctions", "Sanctions Sentiment", "SANCTIONS", "tone"),

    # --- Health ---
    ("gdelt_health_pandemic", "Pandemic Sentiment", "HEALTH_PANDEMIC", "tone"),
    ("gdelt_health_general", "Global Health Sentiment", "HEALTH_GENERAL", "tone"),

    # --- Environment ---
    ("gdelt_env_climate", "Climate Change Sentiment", "ENV_CLIMATECHANGE", "tone"),
    ("gdelt_env_disaster", "Natural Disaster Sentiment", "ENV_NATURALDISASTER", "tone"),
]


def seed_gdelt_variables():
    """Insert GDELT variables into VariableMetadata (idempotent)."""
    created = 0
    skipped = 0

    with get_db_session() as session:
        existing_names = {
            v.name for v in session.query(VariableMetadata.name).filter(
                VariableMetadata.source == 'gdelt'
            ).all()
        }

        for name, display_name, theme, unit in GDELT_VARIABLES:
            if name in existing_names:
                skipped += 1
                continue

            var = VariableMetadata(
                name=name,
                display_name=display_name,
                unit=unit,
                data_type='time_series',
                source='gdelt',
                api_endpoint=f'https://api.gdeltproject.org/api/v2/doc/doc?query={theme}&mode=timelinetone',
                update_frequency='daily',
                parameters=json.dumps({"theme": theme}),
                is_active=True,
            )
            session.add(var)
            created += 1

        session.commit()

    msg = f"GDELT seed complete: {created} created, {skipped} already existed (total catalogue: {len(GDELT_VARIABLES)})"
    print(msg)
    logger.info(msg)
    return {"created": created, "skipped": skipped, "total": len(GDELT_VARIABLES)}


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    seed_gdelt_variables()
