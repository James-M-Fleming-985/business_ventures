"""
Complete Data Pipeline Execution
Runs full workflow: Database Init → Data Ingestion → Correlation Analysis
"""

import sys
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Execute complete data pipeline"""
    logger.info("=" * 70)
    logger.info("CORRELATION DISCOVERY ENGINE - COMPLETE DATA PIPELINE")
    logger.info("=" * 70)
    logger.info(f"Started at: {datetime.now().isoformat()}")
    logger.info("")
    
    try:
        # PHASE 1: Initialize Database
        logger.info("PHASE 1: Database Initialization")
        logger.info("-" * 70)
        from init_database import main as init_db
        init_db()
        logger.info("✅ Phase 1 Complete\n")
        
        # PHASE 2A: Data Ingestion
        logger.info("PHASE 2A: Data Ingestion from APIs")
        logger.info("-" * 70)
        from data_ingestion_service import DataIngestionService
        
        ingestion_service = DataIngestionService()
        ingestion_stats = ingestion_service.fetch_and_store_all_variables()
        
        logger.info("Ingestion Summary:")
        for key, value in ingestion_stats.items():
            logger.info(f"  {key}: {value}")
        logger.info("✅ Phase 2A Complete\n")
        
        # PHASE 2B: Correlation Analysis
        logger.info("PHASE 2B: N×N Correlation Analysis")
        logger.info("-" * 70)
        from correlation_analysis_service import CorrelationAnalysisService
        
        correlation_service = CorrelationAnalysisService()
        correlation_stats = correlation_service.calculate_all_correlations(
            method='pearson',
            min_threshold=0.0,  # Store all correlations
            significance_level=0.05
        )
        
        logger.info("Correlation Summary:")
        for key, value in correlation_stats.items():
            logger.info(f"  {key}: {value}")
        logger.info("✅ Phase 2B Complete\n")
        
        # Get top correlations
        logger.info("TOP 10 STRONGEST CORRELATIONS:")
        logger.info("-" * 70)
        top_10 = correlation_service.get_top_correlations(limit=10)
        
        for i, corr in enumerate(top_10, 1):
            logger.info(f"{i:2d}. {corr['variable1_name']:30s} ↔ "
                       f"{corr['variable2_name']:30s} | "
                       f"r={corr['correlation_value']:+.3f} | "
                       f"p={corr['p_value']:.4f} | "
                       f"n={corr['sample_size']}")
        logger.info("")
        
        # Summary
        logger.info("=" * 70)
        logger.info("✅ PIPELINE EXECUTION COMPLETE")
        logger.info("=" * 70)
        logger.info(f"Total Variables: {correlation_stats.get('variables_count', 0)}")
        logger.info(f"Total Correlation Pairs: {correlation_stats.get('total_pairs_calculated', 0)}")
        logger.info(f"Significant Correlations: {correlation_stats.get('significant_correlations', 0)}")
        logger.info(f"Data Points Collected: {ingestion_stats.get('data_points_stored', 0)}")
        logger.info("")
        logger.info("Dashboard is now ready with REAL DATA")
        logger.info("All mock/synthetic data has been replaced")
        logger.info("")
        logger.info(f"Completed at: {datetime.now().isoformat()}")
        logger.info("=" * 70)
        
        return 0
        
    except Exception as e:
        logger.error(f"❌ Pipeline execution failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
