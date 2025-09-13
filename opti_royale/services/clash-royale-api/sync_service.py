#!/usr/bin/env python3
"""
Clash Royale API Integration Service

This service handles:
1. Syncing card metadata from Clash Royale API
2. Tracking balance changes
3. Updating ML models when cards change
4. Maintaining card effectiveness data
"""

import os
import asyncio
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import aiohttp
import asyncpg
import aioredis
from dataclasses import dataclass, asdict
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ChangeType(Enum):
    BUFF = "buff"
    NERF = "nerf"
    REWORK = "rework"
    BUG_FIX = "bug_fix"

@dataclass
class CardStats:
    """Card statistics from Clash Royale API"""
    id: int
    name: str
    elixir_cost: int
    type: str
    rarity: str
    arena: int
    hitpoints: Optional[int] = None
    damage: Optional[int] = None
    hit_speed: Optional[float] = None
    targets: Optional[str] = None
    range: Optional[float] = None
    deploy_time: Optional[float] = None
    speed: Optional[str] = None
    count: Optional[int] = None
    lifetime: Optional[float] = None
    radius: Optional[float] = None
    description: Optional[str] = None

@dataclass
class BalanceChange:
    """Balance change information"""
    card_id: int
    change_date: datetime
    change_type: ChangeType
    affected_stats: List[str]
    old_values: Dict[str, Any]
    new_values: Dict[str, Any]
    patch_notes: str

class ClashRoyaleAPIService:
    """
    Service for integrating with Clash Royale API
    """
    
    def __init__(self):
        self.api_token = os.getenv('CLASH_ROYALE_API_TOKEN')
        self.api_base_url = os.getenv('CLASH_ROYALE_API_BASE_URL', 'https://api.clashroyale.com/v1')
        self.db_url = os.getenv('DATABASE_URL')
        self.redis_url = os.getenv('REDIS_URL')
        
        # Rate limiting
        self.rate_limit_per_second = 10
        self.last_request_time = 0
        
        if not self.api_token:
            raise ValueError("CLASH_ROYALE_API_TOKEN environment variable is required")
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            headers={'Authorization': f'Bearer {self.api_token}'},
            timeout=aiohttp.ClientTimeout(total=30)
        )
        self.db_pool = await asyncpg.create_pool(self.db_url)
        self.redis = aioredis.from_url(self.redis_url)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.session.close()
        await self.db_pool.close()
        await self.redis.close()
    
    async def _rate_limited_request(self, url: str) -> Dict[str, Any]:
        """Make rate-limited request to Clash Royale API"""
        # Simple rate limiting
        current_time = asyncio.get_event_loop().time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < (1.0 / self.rate_limit_per_second):
            await asyncio.sleep((1.0 / self.rate_limit_per_second) - time_since_last)
        
        async with self.session.get(f"{self.api_base_url}{url}") as response:
            self.last_request_time = asyncio.get_event_loop().time()
            
            if response.status == 200:
                return await response.json()
            elif response.status == 429:
                # Rate limited, wait and retry
                retry_after = int(response.headers.get('Retry-After', 60))
                logger.warning(f"Rate limited, waiting {retry_after} seconds")
                await asyncio.sleep(retry_after)
                return await self._rate_limited_request(url)
            else:
                logger.error(f"API request failed: {response.status} - {await response.text()}")
                response.raise_for_status()
    
    async def fetch_all_cards(self) -> List[CardStats]:
        """Fetch all cards from Clash Royale API"""
        logger.info("Fetching all cards from Clash Royale API...")
        
        try:
            data = await self._rate_limited_request('/cards')
            cards = []
            
            for item in data.get('items', []):
                card = CardStats(
                    id=item['id'],
                    name=item['name'],
                    elixir_cost=item.get('elixirCost', 0),
                    type=item.get('type', 'unknown'),
                    rarity=item.get('rarity', 'common'),
                    arena=item.get('arena', 0),
                    hitpoints=item.get('hitpoints'),
                    damage=item.get('damage'),
                    hit_speed=item.get('hitSpeed'),
                    targets=item.get('targets'),
                    range=item.get('range'),
                    deploy_time=item.get('deployTime'),
                    speed=item.get('speed'),
                    count=item.get('count'),
                    lifetime=item.get('lifetime'),
                    radius=item.get('radius'),
                    description=item.get('description')
                )
                cards.append(card)
            
            logger.info(f"Successfully fetched {len(cards)} cards")
            return cards
            
        except Exception as e:
            logger.error(f"Failed to fetch cards: {str(e)}")
            raise
    
    async def sync_cards_to_database(self, cards: List[CardStats]) -> None:
        """Sync card data to database and detect changes"""
        logger.info("Syncing cards to database...")
        
        async with self.db_pool.acquire() as conn:
            for card in cards:
                # Check if card exists and get current data
                existing_card = await conn.fetchrow(
                    "SELECT * FROM card_metadata WHERE card_id = $1", card.id
                )
                
                if existing_card:
                    # Check for changes
                    changes = await self._detect_card_changes(existing_card, card)
                    if changes:
                        await self._record_balance_change(conn, card.id, changes)
                        await self._update_card_metadata(conn, card)
                        logger.info(f"Updated card: {card.name} with changes: {list(changes.keys())}")
                else:
                    # New card
                    await self._insert_card_metadata(conn, card)
                    logger.info(f"Added new card: {card.name}")
    
    async def _detect_card_changes(self, existing: dict, new_card: CardStats) -> Dict[str, Dict[str, Any]]:
        """Detect changes between existing and new card data"""
        changes = {}
        
        # Compare relevant stats
        comparable_fields = [
            'elixir_cost', 'hitpoints', 'damage', 'hit_speed', 'targets',
            'range', 'deploy_time', 'speed', 'count', 'lifetime', 'radius'
        ]
        
        for field in comparable_fields:
            old_value = existing.get(field)
            new_value = getattr(new_card, field, None)
            
            if old_value != new_value and new_value is not None:
                changes[field] = {
                    'old': old_value,
                    'new': new_value
                }
        
        return changes
    
    async def _record_balance_change(self, conn, card_id: int, changes: Dict[str, Dict[str, Any]]) -> None:
        """Record balance change in database"""
        change_type = self._determine_change_type(changes)
        affected_stats = list(changes.keys())
        
        await conn.execute("""
            INSERT INTO balance_changes 
            (card_id, change_date, change_type, affected_stats, changes_data, model_retrain_triggered)
            VALUES ($1, $2, $3, $4, $5, $6)
        """, card_id, datetime.now().date(), change_type.value, affected_stats, json.dumps(changes), True)
        
        # Trigger ML model retrain
        await self.redis.publish('model_retrain', json.dumps({
            'reason': 'balance_change',
            'card_id': card_id,
            'changes': changes
        }))
    
    def _determine_change_type(self, changes: Dict[str, Dict[str, Any]]) -> ChangeType:
        """Determine if changes are buff, nerf, or rework"""
        # Simplified logic - could be more sophisticated
        stat_changes = []
        
        for field, change in changes.items():
            old_val = change['old']
            new_val = change['new']
            
            if field in ['hitpoints', 'damage', 'range'] and isinstance(old_val, (int, float)) and isinstance(new_val, (int, float)):
                if new_val > old_val:
                    stat_changes.append('buff')
                elif new_val < old_val:
                    stat_changes.append('nerf')
            elif field == 'hit_speed' and isinstance(old_val, (int, float)) and isinstance(new_val, (int, float)):
                # Lower hit speed = faster attacks = buff
                if new_val < old_val:
                    stat_changes.append('buff')
                elif new_val > old_val:
                    stat_changes.append('nerf')
        
        if len(set(stat_changes)) > 1:
            return ChangeType.REWORK
        elif 'buff' in stat_changes:
            return ChangeType.BUFF
        elif 'nerf' in stat_changes:
            return ChangeType.NERF
        else:
            return ChangeType.REWORK
    
    async def _update_card_metadata(self, conn, card: CardStats) -> None:
        """Update existing card metadata"""
        await conn.execute("""
            UPDATE card_metadata SET
                name = $2,
                elixir_cost = $3,
                type = $4,
                rarity = $5,
                arena = $6,
                hitpoints = $7,
                damage = $8,
                hit_speed = $9,
                targets = $10,
                range = $11,
                deploy_time = $12,
                speed = $13,
                count = $14,
                lifetime = $15,
                radius = $16,
                description = $17,
                last_api_sync = $18,
                updated_at = $19
            WHERE card_id = $1
        """, card.id, card.name, card.elixir_cost, card.type, card.rarity, card.arena,
             card.hitpoints, card.damage, card.hit_speed, card.targets, card.range,
             card.deploy_time, card.speed, card.count, card.lifetime, card.radius,
             card.description, datetime.now(), datetime.now())
    
    async def _insert_card_metadata(self, conn, card: CardStats) -> None:
        """Insert new card metadata"""
        await conn.execute("""
            INSERT INTO card_metadata 
            (card_id, name, elixir_cost, type, rarity, arena, hitpoints, damage, 
             hit_speed, targets, range, deploy_time, speed, count, lifetime, 
             radius, description, last_api_sync, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20)
        """, card.id, card.name, card.elixir_cost, card.type, card.rarity, card.arena,
             card.hitpoints, card.damage, card.hit_speed, card.targets, card.range,
             card.deploy_time, card.speed, card.count, card.lifetime, card.radius,
             card.description, datetime.now(), datetime.now(), datetime.now())
    
    async def fetch_current_meta_data(self) -> Dict[str, Any]:
        """Fetch current meta statistics from top ladder"""
        logger.info("Fetching current meta data...")
        
        try:
            # Get top players
            data = await self._rate_limited_request('/locations/global/rankings/players?limit=200')
            
            # Analyze their decks for meta trends
            card_usage = {}
            total_decks = 0
            
            for player in data.get('items', []):
                if 'currentDeck' in player:
                    total_decks += 1
                    for card in player['currentDeck']:
                        card_name = card['name']
                        card_usage[card_name] = card_usage.get(card_name, 0) + 1
            
            # Calculate usage rates
            meta_data = {}
            for card_name, usage_count in card_usage.items():
                usage_rate = usage_count / total_decks if total_decks > 0 else 0
                meta_data[card_name] = {
                    'usage_rate': usage_rate,
                    'usage_count': usage_count,
                    'meta_strength': min(usage_rate * 10, 10)  # 0-10 scale
                }
            
            logger.info(f"Analyzed meta data from {total_decks} top player decks")
            return meta_data
            
        except Exception as e:
            logger.error(f"Failed to fetch meta data: {str(e)}")
            return {}
    
    async def update_meta_ratings(self, meta_data: Dict[str, Any]) -> None:
        """Update card meta ratings in database"""
        logger.info("Updating meta ratings...")
        
        async with self.db_pool.acquire() as conn:
            for card_name, data in meta_data.items():
                await conn.execute("""
                    UPDATE card_metadata 
                    SET 
                        current_meta_rating = $2,
                        usage_rate = $3,
                        updated_at = $4
                    WHERE name = $1
                """, card_name, data['meta_strength'], data['usage_rate'], datetime.now())
    
    async def run_sync_cycle(self) -> None:
        """Run complete synchronization cycle"""
        logger.info("Starting Clash Royale API sync cycle...")
        
        try:
            # Fetch and sync cards
            cards = await self.fetch_all_cards()
            await self.sync_cards_to_database(cards)
            
            # Fetch and update meta data
            meta_data = await self.fetch_current_meta_data()
            if meta_data:
                await self.update_meta_ratings(meta_data)
            
            # Cache sync timestamp
            await self.redis.set('last_cr_api_sync', datetime.now().isoformat())
            
            logger.info("Clash Royale API sync completed successfully")
            
        except Exception as e:
            logger.error(f"Sync cycle failed: {str(e)}")
            raise

async def main():
    """Main entry point for sync service"""
    async with ClashRoyaleAPIService() as service:
        await service.run_sync_cycle()

if __name__ == "__main__":
    asyncio.run(main())
