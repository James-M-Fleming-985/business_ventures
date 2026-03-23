"""
Seed FRED Variables — Expand VariableMetadata to 50+ FRED series.

Run once:  python seed_fred_variables.py
Idempotent: skips any variable whose name already exists.
"""

import json
import logging
from datetime import datetime

from database import get_db_session
from models import VariableMetadata

logger = logging.getLogger(__name__)

# Each entry: (name, display_name, indicator_code, unit, update_frequency)
FRED_VARIABLES = [
    # --- GDP & Output ---
    ("fred_gdp", "US GDP", "GDP", "billions_usd", "quarterly"),
    ("fred_gdp_per_capita", "US GDP Per Capita", "A939RX0Q048SBEA", "usd", "quarterly"),
    ("fred_real_gdp", "US Real GDP", "GDPC1", "billions_usd_2017", "quarterly"),
    ("fred_industrial_production", "Industrial Production Index", "INDPRO", "index_2017", "monthly"),
    ("fred_capacity_utilization", "Capacity Utilization", "TCU", "percent", "monthly"),

    # --- Labour Market ---
    ("fred_unemployment_rate", "Unemployment Rate", "UNRATE", "percent", "monthly"),
    ("fred_nonfarm_payrolls", "Nonfarm Payrolls", "PAYEMS", "thousands", "monthly"),
    ("fred_initial_claims", "Initial Jobless Claims", "ICSA", "claims", "weekly"),
    ("fred_continued_claims", "Continued Jobless Claims", "CCSA", "claims", "weekly"),
    ("fred_labor_force_participation", "Labor Force Participation Rate", "CIVPART", "percent", "monthly"),
    ("fred_avg_hourly_earnings", "Average Hourly Earnings", "CES0500000003", "usd", "monthly"),

    # --- Inflation & Prices ---
    ("fred_cpi", "Consumer Price Index (All Urban)", "CPIAUCSL", "index_1982", "monthly"),
    ("fred_core_cpi", "Core CPI (Less Food & Energy)", "CPILFESL", "index_1982", "monthly"),
    ("fred_pce_price_index", "PCE Price Index", "PCEPI", "index_2017", "monthly"),
    ("fred_core_pce", "Core PCE Price Index", "PCEPILFE", "index_2017", "monthly"),
    ("fred_ppi_finished_goods", "PPI: Finished Goods", "WPSFD49207", "index_1982", "monthly"),
    ("fred_breakeven_inflation_5y", "5-Year Breakeven Inflation", "T5YIE", "percent", "daily"),
    ("fred_breakeven_inflation_10y", "10-Year Breakeven Inflation", "T10YIE", "percent", "daily"),

    # --- Interest Rates & Monetary Policy ---
    ("fred_fed_funds_rate", "Federal Funds Rate", "FEDFUNDS", "percent", "monthly"),
    ("fred_treasury_3m", "3-Month Treasury Bill", "DTB3", "percent", "daily"),
    ("fred_treasury_2y", "2-Year Treasury Yield", "DGS2", "percent", "daily"),
    ("fred_treasury_10y", "10-Year Treasury Yield", "DGS10", "percent", "daily"),
    ("fred_treasury_30y", "30-Year Treasury Yield", "DGS30", "percent", "daily"),
    ("fred_yield_spread_10y_2y", "10Y-2Y Treasury Spread", "T10Y2Y", "percent", "daily"),
    ("fred_yield_spread_10y_3m", "10Y-3M Treasury Spread", "T10Y3M", "percent", "daily"),
    ("fred_m2_money_supply", "M2 Money Supply", "M2SL", "billions_usd", "monthly"),

    # --- Housing ---
    ("fred_housing_starts", "Housing Starts", "HOUST", "thousands_annual", "monthly"),
    ("fred_building_permits", "Building Permits", "PERMIT", "thousands_annual", "monthly"),
    ("fred_existing_home_sales", "Existing Home Sales", "EXHOSLUSM495S", "thousands", "monthly"),
    ("fred_new_home_sales", "New Home Sales", "HSN1F", "thousands_annual", "monthly"),
    ("fred_case_shiller_national", "Case-Shiller National Home Price Index", "CSUSHPINSA", "index_2000", "monthly"),
    ("fred_mortgage_rate_30y", "30-Year Fixed Mortgage Rate", "MORTGAGE30US", "percent", "weekly"),

    # --- Consumer Sentiment & Spending ---
    ("fred_umich_consumer_sentiment", "U of Michigan Consumer Sentiment", "UMCSENT", "index_1966", "monthly"),
    ("fred_retail_sales", "Advance Retail Sales", "RSAFS", "millions_usd", "monthly"),
    ("fred_personal_income", "Personal Income", "PI", "billions_usd", "monthly"),
    ("fred_personal_saving_rate", "Personal Saving Rate", "PSAVERT", "percent", "monthly"),
    ("fred_consumer_credit", "Total Consumer Credit", "TOTALSL", "billions_usd", "monthly"),

    # --- Business & Manufacturing ---
    ("fred_ism_manufacturing", "ISM Manufacturing PMI", "MANEMP", "thousands", "monthly"),
    ("fred_durable_goods_orders", "Durable Goods Orders", "DGORDER", "millions_usd", "monthly"),
    ("fred_business_inventories", "Business Inventories", "BUSINV", "millions_usd", "monthly"),
    ("fred_nfib_small_business", "NFIB Small Business Optimism", "EVANQ", "index", "quarterly"),

    # --- International & Trade ---
    ("fred_trade_balance", "Trade Balance", "BOPGSTB", "millions_usd", "monthly"),
    ("fred_usd_index", "Trade-Weighted USD Index (Broad)", "DTWEXBGS", "index_2006", "daily"),
    ("fred_wti_crude", "WTI Crude Oil Price", "DCOILWTICO", "usd_per_barrel", "daily"),

    # --- Financial Conditions ---
    ("fred_sp500", "S&P 500 Index", "SP500", "index", "daily"),
    ("fred_vix_proxy", "CBOE Volatility Index (Proxy)", "VIXCLS", "index", "daily"),
    ("fred_corporate_baa_spread", "Baa Corporate Bond Spread", "BAAFFM", "percent", "monthly"),
    ("fred_ted_spread", "TED Spread", "TEDRATE", "percent", "daily"),
    ("fred_financial_stress", "St. Louis Financial Stress Index", "STLFSI2", "index", "weekly"),

    # --- Government & Fiscal ---
    ("fred_federal_debt_gdp", "Federal Debt as % of GDP", "GFDEGDQ188S", "percent", "quarterly"),
    ("fred_federal_surplus_deficit", "Federal Surplus/Deficit", "MTSDS133FMS", "millions_usd", "monthly"),
]


def seed_fred_variables():
    """Insert FRED variables into VariableMetadata (idempotent)."""
    created = 0
    skipped = 0

    with get_db_session() as session:
        existing_names = {
            v.name for v in session.query(VariableMetadata.name).filter(
                VariableMetadata.source == 'fred'
            ).all()
        }

        for name, display_name, code, unit, freq in FRED_VARIABLES:
            if name in existing_names:
                skipped += 1
                continue

            var = VariableMetadata(
                name=name,
                display_name=display_name,
                unit=unit,
                data_type='time_series',
                source='fred',
                api_endpoint=f'https://api.stlouisfed.org/fred/series/observations?series_id={code}',
                update_frequency=freq,
                parameters=json.dumps({"indicator_code": code}),
                is_active=True,
            )
            session.add(var)
            created += 1

        session.commit()

    msg = f"FRED seed complete: {created} created, {skipped} already existed (total catalogue: {len(FRED_VARIABLES)})"
    print(msg)
    logger.info(msg)
    return {"created": created, "skipped": skipped, "total": len(FRED_VARIABLES)}


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    seed_fred_variables()
