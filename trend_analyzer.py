"""
MaintSignal - Trend Analysis Module
Analyzes maintenance data across time periods to detect:
- Seasonal failure patterns
- Deteriorating vs improving assets
- PM effectiveness trends
- Data quality improvement tracking
- Monthly/quarterly KPI trending

Works with single-period data (splits into months) or multi-period uploads.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from collections import defaultdict


def analyze_trends(df, date_col="created_date", period="monthly"):
    """
    Analyze maintenance data trends over time.
    
    Args:
        df: DataFrame with normalized maintenance data
        date_col: Column containing dates
        period: 'monthly', 'quarterly', or 'weekly'
    
    Returns:
        Dictionary with trend analysis results
    """
    results = {
        "period_type": period,
        "failure_trends": {},
        "asset_trends": {},
        "kpi_trends": {},
        "seasonal_patterns": {},
        "data_quality_trends": {},
        "alerts": [],
        "insights": [],
    }
    
    if date_col not in df.columns:
        results["error"] = f"Date column '{date_col}' not found"
        return results
    
    # Ensure dates are datetime
    df = df.copy()
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    df = df.dropna(subset=[date_col])
    
    if len(df) == 0:
        results["error"] = "No valid dates found"
        return results
    
    # Create period column
    if period == "monthly":
        df["_period"] = df[date_col].dt.to_period("M").astype(str)
    elif period == "quarterly":
        df["_period"] = df[date_col].dt.to_period("Q").astype(str)
    elif period == "weekly":
        df["_period"] = df[date_col].dt.to_period("W").astype(str)
    
    periods = sorted(df["_period"].unique())
    results["periods"] = periods
    results["date_range"] = {
        "start": df[date_col].min().strftime("%Y-%m-%d"),
        "end": df[date_col].max().strftime("%Y-%m-%d"),
        "span_days": (df[date_col].max() - df[date_col].min()).days,
        "num_periods": len(periods),
    }
    
    # 1. FAILURE VOLUME TRENDS
    volume_by_period = df.groupby("_period").size().to_dict()
    results["failure_trends"]["volume"] = volume_by_period
    
    # Breakdown vs planned ratio by period
    if "order_type" in df.columns:
        breakdown_by_period = {}
        planned_by_period = {}
        ratio_by_period = {}
        
        for p in periods:
            period_df = df[df["_period"] == p]
            types = period_df["order_type"].astype(str).str.lower()
            breakdowns = types.str.contains("pm01|breakdown|corrective|emergency|unplanned", na=False).sum()
            planned = types.str.contains("pm02|preventive|planned|scheduled", na=False).sum()
            total = breakdowns + planned
            
            breakdown_by_period[p] = int(breakdowns)
            planned_by_period[p] = int(planned)
            ratio_by_period[p] = round(planned / total * 100, 1) if total > 0 else 0
        
        results["failure_trends"]["breakdowns"] = breakdown_by_period
        results["failure_trends"]["planned"] = planned_by_period
        results["failure_trends"]["pm_ratio"] = ratio_by_period
        
        # Check if PM ratio is improving
        if len(periods) >= 3:
            ratios = [ratio_by_period[p] for p in periods]
            first_half = np.mean(ratios[:len(ratios)//2])
            second_half = np.mean(ratios[len(ratios)//2:])
            if second_half > first_half + 5:
                results["insights"].append({
                    "type": "positive",
                    "title": "PM Ratio Improving",
                    "detail": f"Planned maintenance ratio increased from {first_half:.0f}% to {second_half:.0f}% over the analysis period",
                })
            elif second_half < first_half - 5:
                results["alerts"].append({
                    "type": "negative",
                    "title": "PM Ratio Declining",
                    "detail": f"Planned maintenance ratio decreased from {first_half:.0f}% to {second_half:.0f}% - reactive maintenance is increasing",
                    "severity": "warning",
                })
    
    # 2. ASSET-LEVEL TRENDS
    if "asset_id" in df.columns:
        asset_df = df[df["asset_id"].astype(str).str.strip() != ""]
        
        asset_period_counts = asset_df.groupby(["asset_id", "_period"]).size().reset_index(name="count")
        
        # Find assets with increasing failure rates
        deteriorating_assets = []
        improving_assets = []
        
        for asset_id in asset_df["asset_id"].unique():
            asset_data = asset_period_counts[asset_period_counts["asset_id"] == asset_id]
            if len(asset_data) >= 3:
                counts = asset_data.sort_values("_period")["count"].values
                first_half = np.mean(counts[:len(counts)//2])
                second_half = np.mean(counts[len(counts)//2:])
                
                change_pct = ((second_half - first_half) / max(first_half, 1)) * 100
                
                if change_pct > 30 and second_half >= 3:
                    deteriorating_assets.append({
                        "asset_id": asset_id,
                        "change_pct": round(change_pct, 1),
                        "early_avg": round(first_half, 1),
                        "recent_avg": round(second_half, 1),
                        "total_failures": int(counts.sum()),
                    })
                elif change_pct < -30 and first_half >= 3:
                    improving_assets.append({
                        "asset_id": asset_id,
                        "change_pct": round(change_pct, 1),
                        "early_avg": round(first_half, 1),
                        "recent_avg": round(second_half, 1),
                        "total_failures": int(counts.sum()),
                    })
        
        deteriorating_assets.sort(key=lambda x: x["change_pct"], reverse=True)
        improving_assets.sort(key=lambda x: x["change_pct"])
        
        results["asset_trends"]["deteriorating"] = deteriorating_assets[:10]
        results["asset_trends"]["improving"] = improving_assets[:10]
        
        if deteriorating_assets:
            worst = deteriorating_assets[0]
            results["alerts"].append({
                "type": "negative",
                "title": f"Asset {worst['asset_id']} Failure Rate Increasing",
                "detail": f"Failures increased {worst['change_pct']:.0f}% (from {worst['early_avg']:.1f} to {worst['recent_avg']:.1f} per period). Investigate for systemic issue.",
                "severity": "critical",
            })
    
    # 3. KPI TRENDS
    kpi_by_period = {}
    for p in periods:
        period_df = df[df["_period"] == p]
        kpi = {"period": p, "total_orders": len(period_df)}
        
        # MTTR
        if "labor_hours" in period_df.columns:
            kpi["avg_labor_hours"] = round(period_df["labor_hours"].mean(), 1)
        
        # Average cost
        if "cost" in period_df.columns:
            kpi["avg_cost"] = round(period_df["cost"].mean(), 2)
            kpi["total_cost"] = round(period_df["cost"].sum(), 2)
        
        # Downtime
        if "downtime_start" in period_df.columns and "downtime_end" in period_df.columns:
            dt_hours = 0
            for _, row in period_df.iterrows():
                try:
                    if pd.notna(row["downtime_start"]) and pd.notna(row["downtime_end"]):
                        diff = (row["downtime_end"] - row["downtime_start"]).total_seconds() / 3600
                        if 0 < diff < 720:
                            dt_hours += diff
                except:
                    pass
            kpi["total_downtime_hours"] = round(dt_hours, 1)
        
        kpi_by_period[p] = kpi
    
    results["kpi_trends"] = kpi_by_period
    
    # 4. SEASONAL PATTERNS
    if len(df) >= 100:
        df["_month"] = df[date_col].dt.month
        month_counts = df.groupby("_month").size()
        avg_monthly = month_counts.mean()
        
        seasonal = {}
        for month in range(1, 13):
            count = month_counts.get(month, 0)
            seasonal[month] = {
                "count": int(count),
                "vs_average": round((count / avg_monthly - 1) * 100, 1) if avg_monthly > 0 else 0,
                "month_name": datetime(2024, month, 1).strftime("%B"),
            }
        
        results["seasonal_patterns"] = seasonal
        
        # Find peak failure months
        peak_month = max(seasonal.items(), key=lambda x: x[1]["count"])
        low_month = min(seasonal.items(), key=lambda x: x[1]["count"])
        
        if peak_month[1]["vs_average"] > 25:
            results["insights"].append({
                "type": "pattern",
                "title": f"Peak Failures in {peak_month[1]['month_name']}",
                "detail": f"{peak_month[1]['month_name']} has {peak_month[1]['vs_average']:.0f}% more failures than average. Consider scheduling additional PM coverage.",
            })
    
    # 5. DATA QUALITY TRENDS
    quality_fields = ["failure_code", "cause_code", "asset_id", "description"]
    dq_by_period = {}
    
    for p in periods:
        period_df = df[df["_period"] == p]
        total = len(period_df)
        dq = {"period": p, "total": total}
        
        for field in quality_fields:
            if field in period_df.columns:
                if period_df[field].dtype == 'datetime64[ns]':
                    filled = period_df[field].notna().sum()
                else:
                    filled = period_df[field].astype(str).str.strip().replace("", np.nan).notna().sum()
                dq[f"{field}_pct"] = round(filled / total * 100, 1) if total > 0 else 0
        
        dq_by_period[p] = dq
    
    results["data_quality_trends"] = dq_by_period
    
    # Check if data quality is improving
    if len(periods) >= 3 and "failure_code" in df.columns:
        fc_trends = [dq_by_period[p].get("failure_code_pct", 0) for p in periods]
        first_half = np.mean(fc_trends[:len(fc_trends)//2])
        second_half = np.mean(fc_trends[len(fc_trends)//2:])
        
        if second_half > first_half + 5:
            results["insights"].append({
                "type": "positive",
                "title": "Failure Code Completeness Improving",
                "detail": f"Failure code fill rate improved from {first_half:.0f}% to {second_half:.0f}% - data quality initiatives are working",
            })
        elif second_half < first_half - 5:
            results["alerts"].append({
                "type": "negative",
                "title": "Failure Code Completeness Declining",
                "detail": f"Failure code fill rate dropped from {first_half:.0f}% to {second_half:.0f}% - technician compliance may need reinforcement",
                "severity": "warning",
            })
    
    return results


def generate_trend_summary(results):
    """Generate a concise summary of trend analysis findings."""
    summary = {
        "date_range": results.get("date_range", {}),
        "num_periods": results.get("date_range", {}).get("num_periods", 0),
        "total_alerts": len(results.get("alerts", [])),
        "total_insights": len(results.get("insights", [])),
        "deteriorating_assets": len(results.get("asset_trends", {}).get("deteriorating", [])),
        "improving_assets": len(results.get("asset_trends", {}).get("improving", [])),
        "key_findings": [],
    }
    
    # Add top alerts as key findings
    for alert in results.get("alerts", [])[:3]:
        summary["key_findings"].append({
            "type": "alert",
            "title": alert["title"],
            "detail": alert["detail"],
        })
    
    for insight in results.get("insights", [])[:3]:
        summary["key_findings"].append({
            "type": "insight",
            "title": insight["title"],
            "detail": insight["detail"],
        })
    
    return summary


# ============================================================
# STANDALONE TEST
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("MaintSignal - Trend Analysis Demo")
    print("=" * 60)
    
    import random
    np.random.seed(42)
    
    # Generate 18 months of data with realistic patterns
    n = 3000
    dates = pd.date_range("2024-01-01", "2025-06-30", periods=n)
    
    data = {
        "created_date": dates,
        "asset_id": [random.choice(["P-101", "P-102", "C-301", "C-302", "M-105", "M-106", "K-201"]) 
                     if random.random() > 0.1 else "" for _ in range(n)],
        "order_type": [random.choice(["PM01", "PM01", "PM02", "PM02", "PM03"]) for _ in range(n)],
        "failure_code": [random.choice(["MECH", "ELEC", "INST", "", "", ""]) for _ in range(n)],
        "cause_code": [random.choice(["WEAR", "OVERLOAD", "", "", "", ""]) for _ in range(n)],
        "labor_hours": [round(random.uniform(0.5, 16), 1) for _ in range(n)],
        "cost": [round(random.uniform(100, 5000), 2) for _ in range(n)],
        "description": [random.choice(["pump seal leak", "bearing noise", "PM inspection", "motor trip"]) for _ in range(n)],
    }
    df = pd.DataFrame(data)
    
    results = analyze_trends(df, period="monthly")
    summary = generate_trend_summary(results)
    
    print(f"\nDate Range: {results['date_range']['start']} to {results['date_range']['end']}")
    print(f"Periods Analyzed: {summary['num_periods']}")
    print(f"Alerts: {summary['total_alerts']}")
    print(f"Insights: {summary['total_insights']}")
    print(f"Deteriorating Assets: {summary['deteriorating_assets']}")
    print(f"Improving Assets: {summary['improving_assets']}")
    
    print("\n--- Key Findings ---")
    for finding in summary["key_findings"]:
        icon = "!" if finding["type"] == "alert" else ">"
        print(f"  {icon} {finding['title']}")
        print(f"    {finding['detail']}")
    
    print("\n--- Volume by Period (first 6 months) ---")
    for p in results["periods"][:6]:
        vol = results["failure_trends"]["volume"].get(p, 0)
        print(f"  {p}: {vol} work orders")
    
    if results.get("asset_trends", {}).get("deteriorating"):
        print("\n--- Deteriorating Assets ---")
        for asset in results["asset_trends"]["deteriorating"][:3]:
            print(f"  {asset['asset_id']}: +{asset['change_pct']}% increase ({asset['early_avg']} -> {asset['recent_avg']} per period)")
