"""
Data Universe Validation Script

Validates that all data sources:
1. Are registered in the data_source_registry
2. Have consistent timestamps (first-of-month grid)
3. Have appropriate fill strategies applied
4. Report any gaps or inconsistencies

Run this after deployments to ensure data quality.
"""

import sys
from datetime import datetime
from typing import Dict, List, Tuple
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def validate_data_universe() -> Dict:
    """
    Comprehensive validation of data universe consistency.
    Returns detailed report with issues found.
    """
    from database import get_db_session
    from models import VariableMetadata, TimeSeriesData
    from data_source_registry import DATA_SOURCES, get_source_config, SignalLayer
    from data_alignment_utils import get_standard_monthly_grid
    from sqlalchemy import func
    
    report = {
        "timestamp": datetime.utcnow().isoformat(),
        "status": "pending",
        "summary": {},
        "sources": {},
        "issues": [],
        "recommendations": []
    }
    
    standard_grid = get_standard_monthly_grid(60)
    valid_days = [d.day for d in standard_grid]  # Should all be 1
    
    with get_db_session() as db:
        # =========================================================================
        # 1. Check all variables are from registered sources
        # =========================================================================
        logger.info("Checking source registration...")
        all_sources = db.query(VariableMetadata.source, func.count(VariableMetadata.id)).group_by(VariableMetadata.source).all()
        
        for source, count in all_sources:
            config = get_source_config(source)
            if not config:
                report["issues"].append({
                    "type": "unregistered_source",
                    "source": source,
                    "variable_count": count,
                    "severity": "high",
                    "message": f"Source '{source}' has {count} variables but is not in data_source_registry"
                })
            else:
                report["sources"][source] = {
                    "variable_count": count,
                    "layer": config.layer.name,
                    "is_active": config.is_active,
                    "fill_strategy": config.fill_strategy.value
                }
        
        # =========================================================================
        # 2. Check timestamp consistency (all should be first-of-month)
        # =========================================================================
        logger.info("Checking timestamp consistency...")
        
        # Get distinct days of month in data
        weird_timestamps = db.query(
            VariableMetadata.source,
            VariableMetadata.name,
            TimeSeriesData.timestamp
        ).join(TimeSeriesData).filter(
            func.extract('day', TimeSeriesData.timestamp) != 1
        ).limit(100).all()
        
        if weird_timestamps:
            by_source = {}
            for source, var_name, ts in weird_timestamps:
                if source not in by_source:
                    by_source[source] = []
                by_source[source].append((var_name, ts))
            
            for source, examples in by_source.items():
                report["issues"].append({
                    "type": "non_standard_timestamp",
                    "source": source,
                    "severity": "medium",
                    "example_count": len(examples),
                    "message": f"Source '{source}' has {len(examples)} data points not on first-of-month",
                    "examples": [str(ts) for _, ts in examples[:3]]
                })
        
        # =========================================================================
        # 3. Check data coverage by layer
        # =========================================================================
        logger.info("Checking layer coverage...")
        
        layer_stats = {}
        for layer in SignalLayer:
            layer_sources = [s for s, c in report["sources"].items() 
                           if get_source_config(s) and get_source_config(s).layer == layer]
            
            total_vars = sum(
                db.query(func.count(VariableMetadata.id)).filter(
                    VariableMetadata.source == s
                ).scalar() or 0
                for s in layer_sources
            )
            
            vars_with_data = sum(
                db.query(func.count(func.distinct(TimeSeriesData.variable_id))).join(
                    VariableMetadata
                ).filter(
                    VariableMetadata.source == s
                ).scalar() or 0
                for s in layer_sources
            )
            
            layer_stats[layer.name] = {
                "sources": layer_sources,
                "total_variables": total_vars,
                "variables_with_data": vars_with_data,
                "coverage": f"{(vars_with_data/total_vars*100):.1f}%" if total_vars > 0 else "N/A"
            }
            
            if layer == SignalLayer.FAST and vars_with_data == 0:
                report["issues"].append({
                    "type": "empty_layer",
                    "layer": "FAST",
                    "severity": "critical",
                    "message": "Layer 1 (FAST) has no data! Run POST /api/admin/setup-layer1-fast-signals"
                })
        
        report["summary"]["layers"] = layer_stats
        
        # =========================================================================
        # 4. Check for variables with no data
        # =========================================================================
        logger.info("Checking for empty variables...")
        
        empty_vars = db.query(VariableMetadata).filter(
            ~VariableMetadata.id.in_(
                db.query(TimeSeriesData.variable_id).distinct()
            ),
            VariableMetadata.is_active == True
        ).all()
        
        if empty_vars:
            by_source = {}
            for var in empty_vars:
                if var.source not in by_source:
                    by_source[var.source] = []
                by_source[var.source].append(var.name)
            
            for source, vars in by_source.items():
                report["issues"].append({
                    "type": "empty_variables",
                    "source": source,
                    "count": len(vars),
                    "severity": "medium",
                    "message": f"Source '{source}' has {len(vars)} active variables with no data",
                    "variables": vars[:5]  # Show first 5
                })
        
        # =========================================================================
        # 5. Generate summary
        # =========================================================================
        total_vars = db.query(func.count(VariableMetadata.id)).filter(
            VariableMetadata.is_active == True
        ).scalar() or 0
        
        vars_with_data = db.query(
            func.count(func.distinct(TimeSeriesData.variable_id))
        ).scalar() or 0
        
        total_points = db.query(func.count(TimeSeriesData.id)).scalar() or 0
        
        report["summary"]["totals"] = {
            "total_variables": total_vars,
            "variables_with_data": vars_with_data,
            "total_data_points": total_points,
            "data_coverage": f"{(vars_with_data/total_vars*100):.1f}%" if total_vars > 0 else "N/A"
        }
        
        # =========================================================================
        # 6. Generate recommendations
        # =========================================================================
        if any(i["type"] == "empty_layer" for i in report["issues"]):
            report["recommendations"].append({
                "priority": 1,
                "action": "Setup Layer 1 Fast Signals",
                "command": "POST /api/admin/setup-layer1-fast-signals",
                "reason": "Layer 1 (FAST) is critical for early signal detection"
            })
        
        if any(i["type"] == "empty_variables" for i in report["issues"]):
            report["recommendations"].append({
                "priority": 2,
                "action": "Run data ingestion",
                "command": "POST /api/admin/fetch-data",
                "reason": "Populate empty variables with data"
            })
        
        if any(i["type"] == "non_standard_timestamp" for i in report["issues"]):
            report["recommendations"].append({
                "priority": 3,
                "action": "Re-run normalization",
                "command": "Check data_alignment_utils.py normalize_to_standard_grid()",
                "reason": "Some data not on standard monthly grid"
            })
        
        # Set overall status
        critical_issues = [i for i in report["issues"] if i.get("severity") == "critical"]
        high_issues = [i for i in report["issues"] if i.get("severity") == "high"]
        
        if critical_issues:
            report["status"] = "critical"
        elif high_issues:
            report["status"] = "warning"
        elif report["issues"]:
            report["status"] = "info"
        else:
            report["status"] = "healthy"
    
    return report


def print_report(report: Dict):
    """Pretty print the validation report"""
    print("\n" + "=" * 70)
    print("DATA UNIVERSE VALIDATION REPORT")
    print("=" * 70)
    print(f"Timestamp: {report['timestamp']}")
    
    status_emoji = {
        "healthy": "✅",
        "info": "ℹ️ ",
        "warning": "⚠️ ",
        "critical": "🚨"
    }
    print(f"Status: {status_emoji.get(report['status'], '?')} {report['status'].upper()}")
    
    # Summary
    print("\n📊 SUMMARY")
    print("-" * 40)
    totals = report["summary"].get("totals", {})
    print(f"  Total Variables: {totals.get('total_variables', 0)}")
    print(f"  Variables with Data: {totals.get('variables_with_data', 0)}")
    print(f"  Total Data Points: {totals.get('total_data_points', 0)}")
    print(f"  Coverage: {totals.get('data_coverage', 'N/A')}")
    
    # Layer breakdown
    print("\n📶 LAYER COVERAGE")
    print("-" * 40)
    for layer_name, stats in report["summary"].get("layers", {}).items():
        emoji = "🚀" if layer_name == "PROTO_FAST" else "⚡" if layer_name == "FAST" else "📈" if layer_name == "MEDIUM" else "🏛️"
        print(f"  {emoji} {layer_name}:")
        print(f"      Sources: {', '.join(stats['sources']) or 'None'}")
        print(f"      Variables: {stats['variables_with_data']}/{stats['total_variables']} ({stats['coverage']})")
    
    # Issues
    if report["issues"]:
        print("\n⚠️  ISSUES FOUND")
        print("-" * 40)
        for issue in report["issues"]:
            severity_emoji = {"critical": "🚨", "high": "🔴", "medium": "🟡", "low": "🟢"}.get(issue.get("severity"), "⚪")
            print(f"  {severity_emoji} [{issue['type']}] {issue['message']}")
    else:
        print("\n✅ No issues found!")
    
    # Recommendations
    if report["recommendations"]:
        print("\n💡 RECOMMENDATIONS")
        print("-" * 40)
        for rec in sorted(report["recommendations"], key=lambda x: x["priority"]):
            print(f"  {rec['priority']}. {rec['action']}")
            print(f"     Command: {rec['command']}")
            print(f"     Reason: {rec['reason']}")
    
    print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    try:
        report = validate_data_universe()
        print_report(report)
        
        # Exit with code based on status
        if report["status"] == "critical":
            sys.exit(2)
        elif report["status"] == "warning":
            sys.exit(1)
        else:
            sys.exit(0)
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(3)
