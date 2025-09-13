#!/usr/bin/env python3
"""
Game Mechanics Update Monitor
Continuously monitors and updates enhanced card database when balance changes occur
"""

import json
import asyncio
import aiohttp
import os
import datetime
import hashlib
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, asdict
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class BalanceChange:
    """Represents a detected balance change"""
    card_name: str
    change_type: str  # "stats", "mechanics", "new_card", "evolution"
    old_value: any
    new_value: any
    change_date: str
    impact_level: str  # "low", "medium", "high", "critical"

@dataclass
class UpdateReport:
    """Report of all detected changes"""
    scan_date: str
    total_changes: int
    critical_changes: int
    balance_changes: List[BalanceChange]
    requires_mechanics_update: bool
    api_version_changed: bool

class GameMechanicsMonitor:
    """Monitors game mechanics and triggers updates when changes detected"""
    
    def __init__(self):
        self.api_key = os.getenv('CLASH_ROYALE_API_KEY')
        self.last_scan_file = '/workspaces/opti_royale/data/last_mechanics_scan.json'
        self.change_log_file = '/workspaces/opti_royale/data/mechanics_change_log.json'
        self.enhanced_db_file = '/workspaces/opti_royale/enhanced_card_database.json'
        
        # Critical stats that affect mechanics
        self.critical_stats = {
            'hitpoints', 'damage', 'attackSpeed', 'range', 'sight', 
            'speed', 'targeting', 'evolutionLevels', 'canEvolve'
        }
        
        # Initialize data directory
        os.makedirs('/workspaces/opti_royale/data', exist_ok=True)
    
    async def check_for_updates(self) -> UpdateReport:
        """Main update checking function"""
        logger.info("🔍 Starting mechanics update scan...")
        
        try:
            # Fetch current official data
            current_cards = await self.fetch_official_cards()
            if not current_cards:
                logger.error("Failed to fetch official cards")
                return self._create_empty_report()
            
            # Load previous scan data
            previous_data = self.load_previous_scan()
            
            # Detect changes
            changes = await self.detect_changes(previous_data, current_cards)
            
            # Analyze impact
            report = self.analyze_changes(changes)
            
            # Save current state
            self.save_current_scan(current_cards)
            
            # Log changes
            if changes:
                self.log_changes(changes)
                logger.info(f"✅ Scan complete: {len(changes)} changes detected")
            else:
                logger.info("✅ Scan complete: No changes detected")
            
            return report
            
        except Exception as e:
            logger.error(f"❌ Update scan failed: {e}")
            return self._create_empty_report()
    
    async def fetch_official_cards(self) -> Optional[List[Dict]]:
        """Fetch latest card data from official API"""
        if not self.api_key:
            logger.error("No API key found")
            return None
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get("https://api.clashroyale.com/v1/cards", headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('items', [])
                    else:
                        logger.error(f"API request failed: {response.status}")
                        return None
        except Exception as e:
            logger.error(f"API request error: {e}")
            return None
    
    async def detect_changes(self, previous_data: Dict, current_cards: List[Dict]) -> List[BalanceChange]:
        """Detect changes between previous and current data"""
        changes = []
        
        if not previous_data:
            logger.info("No previous data - this is initial scan")
            return changes
        
        previous_cards = {card['name']: card for card in previous_data.get('cards', [])}
        current_cards_dict = {card['name']: card for card in current_cards}
        
        # Check for new cards
        new_cards = set(current_cards_dict.keys()) - set(previous_cards.keys())
        for card_name in new_cards:
            changes.append(BalanceChange(
                card_name=card_name,
                change_type="new_card",
                old_value=None,
                new_value=current_cards_dict[card_name],
                change_date=datetime.datetime.now().isoformat(),
                impact_level="high"
            ))
        
        # Check for removed cards (rare but possible)
        removed_cards = set(previous_cards.keys()) - set(current_cards_dict.keys())
        for card_name in removed_cards:
            changes.append(BalanceChange(
                card_name=card_name,
                change_type="removed_card",
                old_value=previous_cards[card_name],
                new_value=None,
                change_date=datetime.datetime.now().isoformat(),
                impact_level="critical"
            ))
        
        # Check for stat changes in existing cards
        for card_name in current_cards_dict.keys():
            if card_name in previous_cards:
                card_changes = self.compare_card_stats(
                    previous_cards[card_name], 
                    current_cards_dict[card_name]
                )
                changes.extend(card_changes)
        
        return changes
    
    def compare_card_stats(self, old_card: Dict, new_card: Dict) -> List[BalanceChange]:
        """Compare individual card stats and detect changes"""
        changes = []
        card_name = new_card['name']
        
        for stat in self.critical_stats:
            old_value = old_card.get(stat)
            new_value = new_card.get(stat)
            
            if old_value != new_value:
                # Determine impact level
                impact = self.assess_stat_change_impact(stat, old_value, new_value)
                
                changes.append(BalanceChange(
                    card_name=card_name,
                    change_type="stats",
                    old_value=old_value,
                    new_value=new_value,
                    change_date=datetime.datetime.now().isoformat(),
                    impact_level=impact
                ))
        
        return changes
    
    def assess_stat_change_impact(self, stat: str, old_value: any, new_value: any) -> str:
        """Assess the impact level of a stat change"""
        if stat in ['targeting', 'canEvolve', 'evolutionLevels']:
            return "critical"  # These changes affect core mechanics
        
        if stat in ['hitpoints', 'damage']:
            try:
                old_val = float(old_value) if old_value else 0
                new_val = float(new_value) if new_value else 0
                change_percent = abs(new_val - old_val) / old_val if old_val > 0 else 0
                
                if change_percent > 0.15:  # >15% change
                    return "high"
                elif change_percent > 0.05:  # >5% change
                    return "medium"
                else:
                    return "low"
            except (ValueError, TypeError):
                return "medium"
        
        return "medium"  # Default for other stats
    
    def analyze_changes(self, changes: List[BalanceChange]) -> UpdateReport:
        """Analyze detected changes and create report"""
        critical_changes = sum(1 for change in changes if change.impact_level == "critical")
        
        # Determine if mechanics update is required
        requires_mechanics_update = any(
            change.change_type in ["new_card", "removed_card"] or
            change.impact_level in ["critical", "high"]
            for change in changes
        )
        
        return UpdateReport(
            scan_date=datetime.datetime.now().isoformat(),
            total_changes=len(changes),
            critical_changes=critical_changes,
            balance_changes=changes,
            requires_mechanics_update=requires_mechanics_update,
            api_version_changed=False  # We can enhance this later
        )
    
    async def trigger_mechanics_update(self, report: UpdateReport):
        """Trigger enhanced database regeneration when needed"""
        if not report.requires_mechanics_update:
            logger.info("No mechanics update required")
            return
        
        logger.info("🔄 Triggering mechanics database update...")
        
        try:
            # Run the enhanced database generator
            import subprocess
            result = subprocess.run([
                'python', '/workspaces/opti_royale/scripts/generate-enhanced-database.py'
            ], capture_output=True, text=True, cwd='/workspaces/opti_royale')
            
            if result.returncode == 0:
                logger.info("✅ Enhanced database updated successfully")
                
                # Update last update timestamp
                await self.update_database_metadata(report)
                
                # Send notification (if configured)
                await self.notify_team(report)
            else:
                logger.error(f"❌ Database update failed: {result.stderr}")
                
        except Exception as e:
            logger.error(f"❌ Failed to trigger database update: {e}")
    
    async def update_database_metadata(self, report: UpdateReport):
        """Update enhanced database with change tracking metadata"""
        try:
            with open(self.enhanced_db_file, 'r') as f:
                db_data = json.load(f)
            
            # Add update tracking to metadata
            db_data['metadata']['lastBalanceCheck'] = report.scan_date
            db_data['metadata']['totalChangesDetected'] = report.total_changes
            db_data['metadata']['criticalChanges'] = report.critical_changes
            db_data['metadata']['autoUpdateEnabled'] = True
            
            with open(self.enhanced_db_file, 'w') as f:
                json.dump(db_data, f, indent=2)
                
            logger.info("📊 Database metadata updated with change tracking")
            
        except Exception as e:
            logger.error(f"Failed to update database metadata: {e}")
    
    async def notify_team(self, report: UpdateReport):
        """Send notifications about critical changes"""
        if report.critical_changes > 0:
            logger.warning(f"🚨 CRITICAL: {report.critical_changes} critical changes detected!")
            
            # Log critical changes
            critical_changes = [c for c in report.balance_changes if c.impact_level == "critical"]
            for change in critical_changes:
                logger.warning(f"   - {change.card_name}: {change.change_type} ({change.old_value} → {change.new_value})")
    
    def load_previous_scan(self) -> Dict:
        """Load previous scan data"""
        try:
            with open(self.last_scan_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.info("No previous scan data found")
            return {}
        except Exception as e:
            logger.error(f"Failed to load previous scan: {e}")
            return {}
    
    def save_current_scan(self, cards: List[Dict]):
        """Save current scan data for next comparison"""
        try:
            scan_data = {
                'scan_date': datetime.datetime.now().isoformat(),
                'cards': cards,
                'card_count': len(cards)
            }
            
            with open(self.last_scan_file, 'w') as f:
                json.dump(scan_data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save scan data: {e}")
    
    def log_changes(self, changes: List[BalanceChange]):
        """Log detected changes to change log file"""
        try:
            # Load existing log
            try:
                with open(self.change_log_file, 'r') as f:
                    log_data = json.load(f)
            except FileNotFoundError:
                log_data = {'changes': []}
            
            # Add new changes
            for change in changes:
                log_data['changes'].append(asdict(change))
            
            # Save updated log
            with open(self.change_log_file, 'w') as f:
                json.dump(log_data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to log changes: {e}")
    
    def _create_empty_report(self) -> UpdateReport:
        """Create empty report for error cases"""
        return UpdateReport(
            scan_date=datetime.datetime.now().isoformat(),
            total_changes=0,
            critical_changes=0,
            balance_changes=[],
            requires_mechanics_update=False,
            api_version_changed=False
        )

async def main():
    """Main monitoring function"""
    monitor = GameMechanicsMonitor()
    
    # Run update check
    report = await monitor.check_for_updates()
    
    # Print summary
    print(f"🔍 Mechanics Update Scan Complete")
    print(f"📊 Total Changes: {report.total_changes}")
    print(f"🚨 Critical Changes: {report.critical_changes}")
    print(f"🔄 Mechanics Update Required: {report.requires_mechanics_update}")
    
    if report.total_changes > 0:
        print("\n📋 Changes Detected:")
        for change in report.balance_changes[:5]:  # Show first 5
            print(f"   - {change.card_name}: {change.change_type} ({change.impact_level})")
        
        if len(report.balance_changes) > 5:
            print(f"   ... and {len(report.balance_changes) - 5} more changes")
    
    # Trigger update if needed
    if report.requires_mechanics_update:
        await monitor.trigger_mechanics_update(report)
    
    return report

if __name__ == "__main__":
    report = asyncio.run(main())
