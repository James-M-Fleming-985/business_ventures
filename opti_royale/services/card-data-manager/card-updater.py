#!/usr/bin/env python3
"""
Card Data Manager - Automated Card Statistics Updater
Handles fetching, parsing, and updating Clash Royale card statistics
"""

import json
import asyncio
import aiohttp
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class CardStats:
    """Data class for card statistics"""
    card_id: str
    name: str
    type: str
    rarity: str
    cost: int
    hitpoints: Optional[int] = None
    damage: Optional[int] = None
    dps: Optional[float] = None
    attack_speed: Optional[float] = None
    range: Optional[float] = None
    speed: Optional[str] = None
    deploy_time: Optional[float] = None
    target_type: Optional[str] = None
    splash_radius: Optional[float] = None
    splash_damage: Optional[int] = None
    spell_radius: Optional[float] = None
    spell_duration: Optional[float] = None
    count: Optional[int] = None
    lifetime: Optional[float] = None
    production_speed: Optional[float] = None
    spawned_unit: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    game_version: str = "current"

class CardDataUpdater:
    """Manages card data updates from multiple sources"""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.engine = create_engine(database_url)
        self.Session = sessionmaker(bind=self.engine)
        
        # Data sources for card information
        self.data_sources = {
            "royaleapi": "https://royaleapi.com/api/cards",
            "clashroyale_official": "https://api.clashroyale.com/v1/cards",
            "deckshop": "https://www.deckshop.pro/api/cards",
            "statsroyale": "https://statsroyale.com/api/cards"
        }
        
        # Manual card data for critical stats (tournament standard)
        self.manual_card_data = self._load_manual_card_data()
    
    def _load_manual_card_data(self) -> Dict[str, CardStats]:
        """Load manually curated card data for accuracy"""
        return {
            "knight": CardStats(
                card_id="knight",
                name="Knight",
                type="TROOP",
                rarity="COMMON",
                cost=3,
                hitpoints=1568,
                damage=176,
                dps=125,
                attack_speed=1.4,
                range=1.0,
                speed="Medium",
                deploy_time=1.0,
                target_type="Ground",
                description="A tough melee fighter. The Barbarian's handsome, cultured cousin.",
                category="Tank",
                archetype="Cycle"
            ),
            "fireball": CardStats(
                card_id="fireball",
                name="Fireball",
                type="SPELL",
                rarity="RARE",
                cost=4,
                damage=572,
                spell_radius=2.5,
                description="Annihilates a small area with a big explosion.",
                category="Damage Spell",
                archetype="Control"
            ),
            "hog-rider": CardStats(
                card_id="hog-rider",
                name="Hog Rider",
                type="TROOP",
                rarity="RARE",
                cost=4,
                hitpoints=1408,
                damage=318,
                dps=159,
                attack_speed=2.0,
                range=1.0,
                speed="Very Fast",
                deploy_time=1.0,
                target_type="Buildings",
                description="Fast melee troop that targets buildings and ignores enemy units.",
                category="Win Condition",
                archetype="Cycle"
            ),
            # Add more cards as needed...
        }
    
    async def fetch_official_api_data(self) -> Optional[List[Dict]]:
        """Fetch card data from Clash Royale official API"""
        try:
            headers = {
                "Authorization": f"Bearer {os.getenv('CLASH_ROYALE_API_KEY')}",
                "Accept": "application/json"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "https://api.clashroyale.com/v1/cards",
                    headers=headers
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("items", [])
                    else:
                        logger.error(f"Official API error: {response.status}")
                        return None
        except Exception as e:
            logger.error(f"Error fetching official API data: {e}")
            return None
    
    async def fetch_community_api_data(self, source: str, url: str) -> Optional[List[Dict]]:
        """Fetch card data from community APIs"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"Fetched data from {source}")
                        return data
                    else:
                        logger.warning(f"{source} API returned {response.status}")
                        return None
        except Exception as e:
            logger.error(f"Error fetching from {source}: {e}")
            return None
    
    def parse_card_data(self, raw_data: Dict, source: str) -> Optional[CardStats]:
        """Parse raw card data into standardized format"""
        try:
            # Different APIs have different data structures
            if source == "clashroyale_official":
                return self._parse_official_api(raw_data)
            elif source == "royaleapi":
                return self._parse_royaleapi(raw_data)
            elif source == "deckshop":
                return self._parse_deckshop(raw_data)
            else:
                return self._parse_generic(raw_data)
        except Exception as e:
            logger.error(f"Error parsing card data from {source}: {e}")
            return None
    
    def _parse_official_api(self, data: Dict) -> CardStats:
        """Parse official Clash Royale API data"""
        return CardStats(
            card_id=data.get("id", "").lower().replace(" ", "-"),
            name=data.get("name", ""),
            type=data.get("type", "").upper(),
            rarity=data.get("rarity", "").upper(),
            cost=data.get("elixirCost", 0),
            description=data.get("description", ""),
            image_url=data.get("iconUrls", {}).get("medium", "")
        )
    
    def _parse_royaleapi(self, data: Dict) -> CardStats:
        """Parse RoyaleAPI data with detailed stats"""
        stats = data.get("stats", {})
        return CardStats(
            card_id=data.get("id", ""),
            name=data.get("name", ""),
            type=data.get("type", "").upper(),
            rarity=data.get("rarity", "").upper(),
            cost=data.get("cost", 0),
            hitpoints=stats.get("hitpoints"),
            damage=stats.get("damage"),
            dps=stats.get("dps"),
            attack_speed=stats.get("attackSpeed"),
            range=stats.get("range"),
            speed=stats.get("speed"),
            target_type=stats.get("targetType"),
            description=data.get("description", "")
        )
    
    def _parse_deckshop(self, data: Dict) -> CardStats:
        """Parse DeckShop Pro data"""
        return CardStats(
            card_id=data.get("id", ""),
            name=data.get("name", ""),
            type=data.get("type", "").upper(),
            rarity=data.get("rarity", "").upper(),
            cost=data.get("cost", 0),
            description=data.get("description", "")
        )
    
    def _parse_generic(self, data: Dict) -> CardStats:
        """Generic parser for unknown data sources"""
        return CardStats(
            card_id=data.get("id", data.get("name", "")).lower().replace(" ", "-"),
            name=data.get("name", ""),
            type=data.get("type", "TROOP").upper(),
            rarity=data.get("rarity", "COMMON").upper(),
            cost=data.get("cost", data.get("elixir", 0))
        )
    
    async def detect_balance_changes(self, new_version: str) -> List[Dict]:
        """Detect balance changes between versions"""
        changes = []
        
        with self.Session() as session:
            # Get current active cards
            current_cards = session.execute(
                text("""
                    SELECT c.id, c.name, cs.* 
                    FROM cards c 
                    LEFT JOIN card_stats cs ON c.id = cs.card_id 
                    WHERE cs.is_active = true
                """)
            ).fetchall()
            
            for card in current_cards:
                # Compare with new data (implement comparison logic)
                # This would check if stats have changed
                pass
        
        return changes
    
    async def update_card_database(self, cards_data: List[CardStats], game_version: str) -> None:
        """Update database with new card data"""
        with self.Session() as session:
            try:
                for card_data in cards_data:
                    # Update main card record
                    session.execute(text("""
                        INSERT INTO cards (
                            id, name, type, rarity, cost, category, description, 
                            image_url, game_version, updated_at
                        ) VALUES (
                            :id, :name, :type, :rarity, :cost, :category, :description,
                            :image_url, :game_version, NOW()
                        ) ON CONFLICT (id) DO UPDATE SET
                            name = EXCLUDED.name,
                            type = EXCLUDED.type,
                            rarity = EXCLUDED.rarity,
                            cost = EXCLUDED.cost,
                            description = EXCLUDED.description,
                            image_url = EXCLUDED.image_url,
                            game_version = EXCLUDED.game_version,
                            updated_at = NOW()
                    """), {
                        "id": card_data.card_id,
                        "name": card_data.name,
                        "type": card_data.type,
                        "rarity": card_data.rarity,
                        "cost": card_data.cost,
                        "category": getattr(card_data, 'category', 'Unknown'),
                        "description": card_data.description,
                        "image_url": card_data.image_url,
                        "game_version": game_version
                    })
                    
                    # Deactivate old card stats
                    session.execute(text("""
                        UPDATE card_stats 
                        SET is_active = false 
                        WHERE card_id = :card_id AND is_active = true
                    """), {"card_id": card_data.card_id})
                    
                    # Insert new card stats
                    session.execute(text("""
                        INSERT INTO card_stats (
                            card_id, game_version, hitpoints, damage, dps, attack_speed,
                            range, splash_radius, splash_damage, deploy_time, lifetime,
                            spell_duration, cost, is_active, release_date
                        ) VALUES (
                            :card_id, :game_version, :hitpoints, :damage, :dps, :attack_speed,
                            :range, :splash_radius, :splash_damage, :deploy_time, :lifetime,
                            :spell_duration, :cost, true, NOW()
                        )
                    """), {
                        "card_id": card_data.card_id,
                        "game_version": game_version,
                        "hitpoints": card_data.hitpoints,
                        "damage": card_data.damage,
                        "dps": card_data.dps,
                        "attack_speed": card_data.attack_speed,
                        "range": card_data.range,
                        "splash_radius": card_data.splash_radius,
                        "splash_damage": card_data.splash_damage,
                        "deploy_time": card_data.deploy_time,
                        "lifetime": card_data.lifetime,
                        "spell_duration": card_data.spell_duration,
                        "cost": card_data.cost
                    })
                
                session.commit()
                logger.info(f"Successfully updated {len(cards_data)} cards for version {game_version}")
                
            except Exception as e:
                session.rollback()
                logger.error(f"Error updating database: {e}")
                raise
    
    async def run_update_cycle(self, game_version: Optional[str] = None) -> None:
        """Run complete update cycle"""
        if not game_version:
            game_version = datetime.now().strftime("%Y.%m.%d")
        
        logger.info(f"Starting card data update for version {game_version}")
        
        all_cards_data = []
        
        # Start with manual data for accuracy
        all_cards_data.extend(self.manual_card_data.values())
        
        # Fetch from official API first
        official_data = await self.fetch_official_api_data()
        if official_data:
            for card_raw in official_data:
                parsed = self.parse_card_data(card_raw, "clashroyale_official")
                if parsed:
                    all_cards_data.append(parsed)
        
        # Fetch from community APIs for additional stats
        for source, url in self.data_sources.items():
            if source != "clashroyale_official":  # Already fetched
                community_data = await self.fetch_community_api_data(source, url)
                if community_data:
                    for card_raw in community_data:
                        parsed = self.parse_card_data(card_raw, source)
                        if parsed:
                            # Merge with existing data if card already exists
                            existing = next((c for c in all_cards_data if c.card_id == parsed.card_id), None)
                            if existing:
                                # Merge stats (prefer non-None values)
                                self._merge_card_stats(existing, parsed)
                            else:
                                all_cards_data.append(parsed)
        
        # Update database
        await self.update_card_database(all_cards_data, game_version)
        
        # Detect and log balance changes
        changes = await self.detect_balance_changes(game_version)
        if changes:
            logger.info(f"Detected {len(changes)} balance changes")
            for change in changes:
                logger.info(f"  {change}")
    
    def _merge_card_stats(self, existing: CardStats, new: CardStats) -> None:
        """Merge card stats, preferring non-None values"""
        for field in existing.__dataclass_fields__:
            existing_val = getattr(existing, field)
            new_val = getattr(new, field)
            if existing_val is None and new_val is not None:
                setattr(existing, field, new_val)

async def main():
    """Main entry point"""
    database_url = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/opti_royale")
    updater = CardDataUpdater(database_url)
    
    # Run update cycle
    await updater.run_update_cycle()

if __name__ == "__main__":
    asyncio.run(main())
