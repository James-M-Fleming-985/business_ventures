```python
import asyncio
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from enum import Enum
import aiohttp
from dataclasses import dataclass, field
from collections import defaultdict


class Period(Enum):
    DAY = "day"
    WEEK = "week"
    MONTH = "month"


@dataclass
class RevenueRecord:
    amount: Decimal
    currency: str
    timestamp: datetime
    transaction_id: str


@dataclass
class ExchangeRate:
    from_currency: str
    to_currency: str
    rate: Decimal
    timestamp: datetime
    ttl: int = 300  # 5 minutes cache


@dataclass
class AggregatedRevenue:
    period: Period
    start_date: datetime
    end_date: datetime
    total_amount: Decimal
    currency: str
    record_count: int = 0
    records: List[RevenueRecord] = field(default_factory=list)


class ExchangeRateCache:
    def __init__(self, ttl: int = 300):
        self.cache: Dict[Tuple[str, str], ExchangeRate] = {}
        self.ttl = ttl

    def get(self, from_currency: str, to_currency: str) -> Optional[ExchangeRate]:
        key = (from_currency, to_currency)
        if key in self.cache:
            rate = self.cache[key]
            if (datetime.now() - rate.timestamp).total_seconds() < self.ttl:
                return rate
            else:
                del self.cache[key]
        return None

    def set(self, from_currency: str, to_currency: str, rate: Decimal):
        key = (from_currency, to_currency)
        self.cache[key] = ExchangeRate(
            from_currency=from_currency,
            to_currency=to_currency,
            rate=rate,
            timestamp=datetime.now(),
            ttl=self.ttl
        )


class CurrencyConverter:
    def __init__(self, api_url: Optional[str] = None, cache_ttl: int = 300):
        self.api_url = api_url or "https://api.exchangerate-api.com/v4/latest/"
        self.cache = ExchangeRateCache(ttl=cache_ttl)
        self._fixed_rates: Dict[Tuple[str, str], Decimal] = {}

    def set_fixed_rate(self, from_currency: str, to_currency: str, rate: Decimal):
        """Set a fixed exchange rate for testing or offline mode."""
        self._fixed_rates[(from_currency, to_currency)] = rate

    async def get_exchange_rate(self, from_currency: str, to_currency: str) -> Decimal:
        """Get exchange rate with caching."""
        if from_currency == to_currency:
            return Decimal("1.0")

        # Check fixed rates first
        if (from_currency, to_currency) in self._fixed_rates:
            return self._fixed_rates[(from_currency, to_currency)]

        # Check cache
        cached_rate = self.cache.get(from_currency, to_currency)
        if cached_rate:
            return cached_rate.rate

        # Fetch from API
        rate = await self._fetch_exchange_rate(from_currency, to_currency)
        self.cache.set(from_currency, to_currency, rate)
        return rate

    async def _fetch_exchange_rate(self, from_currency: str, to_currency: str) -> Decimal:
        """Fetch exchange rate from API."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.api_url}{from_currency}") as response:
                    if response.status == 200:
                        data = await response.json()
                        if "rates" in data and to_currency in data["rates"]:
                            return Decimal(str(data["rates"][to_currency]))
                    raise ValueError(f"Could not fetch rate for {from_currency} to {to_currency}")
        except Exception as e:
            # Fallback to approximate rates if API fails
            return self._get_fallback_rate(from_currency, to_currency)

    def _get_fallback_rate(self, from_currency: str, to_currency: str) -> Decimal:
        """Provide fallback rates for common currency pairs."""
        fallback_rates = {
            ("USD", "EUR"): Decimal("0.85"),
            ("EUR", "USD"): Decimal("1.18"),
            ("USD", "GBP"): Decimal("0.73"),
            ("GBP", "USD"): Decimal("1.37"),
            ("EUR", "GBP"): Decimal("0.86"),
            ("GBP", "EUR"): Decimal("1.16"),
        }
        key = (from_currency, to_currency)
        if key in fallback_rates:
            return fallback_rates[key]
        return Decimal("1.0")

    async def convert(self, amount: Decimal, from_currency: str, to_currency: str) -> Decimal:
        """Convert amount from one currency to another."""
        rate = await self.get_exchange_rate(from_currency, to_currency)
        return amount * rate


class RevenueAggregator:
    def __init__(self, base_currency: str = "USD", cache_ttl: int = 300):
        self.base_currency = base_currency
        self.converter = CurrencyConverter(cache_ttl=cache_ttl)
        self.records: List[RevenueRecord] = []

    def add_record(self, record: RevenueRecord):
        """Add a revenue record."""
        self.records.append(record)

    def add_records(self, records: List[RevenueRecord]):
        """Add multiple revenue records."""
        self.records.extend(records)

    def set_fixed_rate(self, from_currency: str, to_currency: str, rate: Decimal):
        """Set a fixed exchange rate."""
        self.converter.set_fixed_rate(from_currency, to_currency, rate)

    async def aggregate_by_period(
        self,
        period: Period,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        target_currency: Optional[str] = None
    ) -> List[AggregatedRevenue]:
        """Aggregate revenue by specified period."""
        target_currency = target_currency or self.base_currency

        # Filter records by date range
        filtered_records = self._filter_records(start_date, end_date)

        # Group records by period
        grouped = self._group_by_period(filtered_records, period)

        # Aggregate each group
        results = []
        for period_key, period_records in grouped.items():
            period_start, period_end = period_key
            total = Decimal("0")

            for record in period_records:
                converted_amount = await self.converter.convert(
                    record.amount,
                    record.currency,
                    target_currency
                )
                total += converted_amount

            results.append(AggregatedRevenue(
                period=period,
                start_date=period_start,
                end_date=period_end,
                total_amount=total,
                currency=target_currency,
                record_count=len(period_records),
                records=period_records
            ))

        # Sort by start_date
        results.sort(key=lambda x: x.start_date)
        return results

    def _filter_records(
        self,
        start_date: Optional[datetime],
        end_date: Optional[datetime]
    ) -> List[RevenueRecord]:
        """Filter records by date range."""
        filtered = self.records

        if start_date:
            filtered = [r for r in filtered if r.timestamp >= start_date]

        if end_date:
            filtered = [r for r in filtered if r.timestamp <= end_date]

        return filtered

    def _group_by_period(
        self,
        records: List[RevenueRecord],
        period: Period
    ) -> Dict[Tuple[datetime, datetime], List[RevenueRecord]]:
        """Group records by period."""
        groups: Dict[Tuple[datetime, datetime], List[RevenueRecord]] = defaultdict(list)

        for record in records:
            period_key = self._get_period_key(record.timestamp, period)
            groups[period_key].append(record)

        return groups

    def _get_period_key(self, timestamp: datetime, period: Period) -> Tuple[datetime, datetime]:
        """Get the period key (start, end) for a timestamp."""
        if period == Period.DAY:
            start = timestamp.replace(hour=0, minute=0, second=0, microsecond=0)
            end = start + timedelta(days=1) - timedelta(microseconds=1)
        elif period == Period.WEEK:
            # Week starts on Monday
            start = timestamp.replace(hour=0, minute=0, second=0, microsecond=0)
            start = start - timedelta(days=start.weekday())
            end = start + timedelta(days=7) - timedelta(microseconds=1)
        elif period == Period.MONTH:
            start = timestamp.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            if start.month == 12:
                end = start.replace(year=start.year + 1, month=1) - timedelta(microseconds=1)
            else:
                end = start.replace(month=start.month + 1) - timedelta(microseconds=1)
        else:
            raise ValueError(f"Unknown period: {period}")

        return (start, end)

    async def get_total_revenue(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        target_currency: Optional[str] = None
    ) -> Decimal:
        """Get total revenue for a date range."""
        target_currency = target_currency or self.base_currency
        filtered_records = self._filter_records(start_date, end_date)

        total = Decimal("0")
        for record in filtered_records:
            converted_amount = await self.converter.convert(
                record.amount,
                record.currency,
                target_currency
            )
            total += converted_amount

        return total

    async def get_revenue_by_currency(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Decimal]:
        """Get revenue grouped by currency."""
        filtered_records = self._filter_records(start_date, end_date)
        revenue_by_currency: Dict[str, Decimal] = defaultdict(lambda: Decimal("0"))

        for record in filtered_records:
            revenue_by_currency[record.currency] += record.amount

        return dict(revenue_by_currency)
```