#!/usr/bin/env python3
"""
Automated Mechanics Update Scheduler
Runs periodic checks for balance changes and updates enhanced database
"""

import asyncio
import schedule
import time
import logging
from datetime import datetime
import sys
import os

# Add scripts directory to path
sys.path.append('/workspaces/opti_royale/scripts')
from mechanics_update_monitor import GameMechanicsMonitor

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/workspaces/opti_royale/logs/mechanics-scheduler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class MechanicsUpdateScheduler:
    """Handles scheduled monitoring and updates"""
    
    def __init__(self):
        self.monitor = GameMechanicsMonitor()
        self.last_check = None
        self.check_interval_hours = 6  # Check every 6 hours
        
        # Ensure logs directory exists
        os.makedirs('/workspaces/opti_royale/logs', exist_ok=True)
    
    async def run_scheduled_check(self):
        """Run a scheduled mechanics check"""
        try:
            logger.info("🕐 Starting scheduled mechanics check...")
            
            # Run the monitor
            report = await self.monitor.check_for_updates()
            
            # Log results
            logger.info(f"✅ Scheduled check complete: {report.total_changes} changes detected")
            
            if report.critical_changes > 0:
                logger.warning(f"🚨 CRITICAL: {report.critical_changes} critical changes detected!")
            
            # Trigger update if needed
            if report.requires_mechanics_update:
                logger.info("🔄 Triggering mechanics database update...")
                await self.monitor.trigger_mechanics_update(report)
            
            self.last_check = datetime.now()
            
        except Exception as e:
            logger.error(f"❌ Scheduled check failed: {e}")
    
    def run_manual_check(self):
        """Run manual check (synchronous wrapper)"""
        asyncio.run(self.run_scheduled_check())
    
    def start_scheduler(self):
        """Start the automated scheduler"""
        logger.info("🚀 Starting Mechanics Update Scheduler...")
        logger.info(f"📅 Scheduled checks every {self.check_interval_hours} hours")
        
        # Schedule regular checks
        schedule.every(self.check_interval_hours).hours.do(self.run_manual_check)
        
        # Schedule daily comprehensive check
        schedule.every().day.at("06:00").do(self.run_manual_check)
        
        # Schedule post-balance change check (monthly around balance change dates)
        schedule.every().month.do(self.run_manual_check)
        
        logger.info("✅ Scheduler started successfully")
        
        # Run initial check
        logger.info("🔍 Running initial check...")
        self.run_manual_check()
        
        # Keep running
        while True:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute for scheduled jobs
            except KeyboardInterrupt:
                logger.info("🛑 Scheduler stopped by user")
                break
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                time.sleep(300)  # Wait 5 minutes before retrying

def main():
    """Main scheduler function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Clash Royale Mechanics Update Scheduler')
    parser.add_argument('--mode', choices=['schedule', 'manual'], default='manual',
                       help='Run mode: schedule for continuous monitoring, manual for one-time check')
    parser.add_argument('--interval', type=int, default=6,
                       help='Check interval in hours (for schedule mode)')
    
    args = parser.parse_args()
    
    scheduler = MechanicsUpdateScheduler()
    scheduler.check_interval_hours = args.interval
    
    if args.mode == 'schedule':
        logger.info("🤖 Starting in scheduled mode...")
        scheduler.start_scheduler()
    else:
        logger.info("🔍 Running single manual check...")
        scheduler.run_manual_check()
        logger.info("✅ Manual check complete")

if __name__ == "__main__":
    main()
