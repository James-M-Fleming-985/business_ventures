#!/usr/bin/env python3
"""
Official Card Data Verification Script
Verifies card database against official Clash Royale API and community sources
"""

import asyncio
import aiohttp
import json
import os
from typing import Dict, List, Optional
from dataclasses import dataclass
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class CardVerification:
    """Card verification result"""
    name: str
    found_in_official: bool = False
    found_in_royaleapi: bool = False
    found_in_wiki: bool = False
    can_evolve: bool = False
    verified_stats: Optional[Dict] = None
    discrepancies: List[str] = None

class CardDataVerifier:
    """Verify card data against multiple official sources"""
    
    def __init__(self):
        self.api_key = os.getenv('CLASH_ROYALE_API_KEY')
        self.official_api_url = "https://api.clashroyale.com/v1/cards"
        self.royaleapi_url = "https://royaleapi.com/api/cards"
        
    async def verify_official_api(self) -> Optional[List[Dict]]:
        """Verify against official Clash Royale API"""
        if not self.api_key:
            logger.warning("No CLASH_ROYALE_API_KEY found. Register at developer.clashroyale.com")
            return None
            
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.official_api_url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        cards = data.get('items', [])
                        logger.info(f"✅ Official API: Found {len(cards)} cards")
                        return cards
                    elif response.status == 403:
                        logger.error("❌ Official API: Invalid or missing API key")
                    else:
                        logger.error(f"❌ Official API: HTTP {response.status}")
        except Exception as e:
            logger.error(f"❌ Official API: {e}")
        
        return None
    
    async def verify_royaleapi(self) -> Optional[List[Dict]]:
        """Verify against RoyaleAPI community database"""
        try:
            async with aiohttp.ClientSession() as session:
                # Note: RoyaleAPI might require different endpoint or headers
                async with session.get(self.royaleapi_url) as response:
                    if response.status == 200:
                        data = await response.json()
                        # RoyaleAPI structure may vary
                        cards = data if isinstance(data, list) else data.get('items', [])
                        logger.info(f"✅ RoyaleAPI: Found {len(cards)} cards")
                        return cards
                    else:
                        logger.warning(f"⚠️ RoyaleAPI: HTTP {response.status}")
        except Exception as e:
            logger.warning(f"⚠️ RoyaleAPI: {e}")
        
        return None
    
    async def get_current_database_cards(self) -> List[Dict]:
        """Get cards from current database for comparison"""
        # This would connect to our SQLite database
        # For now, return empty list - implement database connection
        logger.info("📊 Loading current database cards...")
        return []
    
    async def verify_all_sources(self) -> Dict[str, List[Dict]]:
        """Verify card data from all available sources"""
        results = {}
        
        logger.info("🔍 Starting card data verification...")
        
        # Official API (highest priority)
        official_cards = await self.verify_official_api()
        if official_cards:
            results['official'] = official_cards
        
        # Community sources
        royaleapi_cards = await self.verify_royaleapi()
        if royaleapi_cards:
            results['royaleapi'] = royaleapi_cards
        
        # Current database
        db_cards = await self.get_current_database_cards()
        if db_cards:
            results['database'] = db_cards
        
        return results
    
    def generate_verification_report(self, sources: Dict[str, List[Dict]]) -> Dict:
        """Generate verification report with recommendations"""
        report = {
            'timestamp': '2025-07-26',
            'sources_checked': list(sources.keys()),
            'card_counts': {source: len(cards) for source, cards in sources.items()},
            'status': 'pending_api_key' if 'official' not in sources else 'verified',
            'recommendations': []
        }
        
        if 'official' not in sources:
            report['recommendations'].append({
                'priority': 'HIGH',
                'action': 'Obtain official Clash Royale API key',
                'url': 'https://developer.clashroyale.com/',
                'description': 'Register for official API access to get authoritative card data'
            })
        
        if 'official' in sources:
            official_count = len(sources['official'])
            report['recommendations'].append({
                'priority': 'MEDIUM',
                'action': f'Update database to match official count of {official_count} cards',
                'description': 'Sync local database with official card list'
            })
        
        return report
    
    async def run_verification(self) -> None:
        """Run complete verification process"""
        print("🎮 Clash Royale Card Data Verification")
        print("=====================================")
        
        sources = await self.verify_all_sources()
        report = self.generate_verification_report(sources)
        
        print(f"\n📊 Verification Results:")
        print(f"Sources checked: {', '.join(report['sources_checked'])}")
        print(f"Status: {report['status']}")
        
        print(f"\n📈 Card Counts:")
        for source, count in report['card_counts'].items():
            print(f"  {source}: {count} cards")
        
        print(f"\n🎯 Recommendations:")
        for rec in report['recommendations']:
            print(f"  [{rec['priority']}] {rec['action']}")
            if 'url' in rec:
                print(f"       URL: {rec['url']}")
        
        # Save report
        with open('/workspaces/opti_royale/card-verification-report.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n💾 Report saved to: card-verification-report.json")

async def main():
    """Main entry point"""
    verifier = CardDataVerifier()
    await verifier.run_verification()

if __name__ == "__main__":
    asyncio.run(main())
