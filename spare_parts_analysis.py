"""
MaintSignal - Spare Parts & Cost Analysis Module
Analyzes maintenance cost data to find:
- Top cost drivers by asset and failure type
- Cost trends over time
- Emergency vs planned spend ratio
- High-cost repeat repairs (same fix, same asset, multiple times)
- Cost optimization opportunities
"""

import pandas as pd
import numpy as np
from collections import defaultdict


def analyze_spare_parts_costs(df, cost_col="cost", asset_col="asset_id", 
                                desc_col="description", date_col="created_date",
                                order_type_col="order_type", labor_col="labor_hours",
                                category_col=None):
    """
    Analyze maintenance cost patterns and identify savings opportunities.
    """
    results = {
        "cost_by_asset": [],
        "cost_by_category": [],
        "emergency_vs_planned": {},
        "high_cost_repeats": [],
        "cost_trends": {},
        "optimization_opportunities": [],
        "stats": {},
    }

    # Validate cost column exists
    if cost_col not in df.columns:
        results["error"] = "No cost data column found"
        return results

    work = df.copy()
    work[cost_col] = pd.to_numeric(work[cost_col], errors="coerce")
    work = work[work[cost_col].notna() & (work[cost_col] > 0)]

    if len(work) == 0:
        results["error"] = "No valid cost data found"
        return results

    # Basic stats
    results["stats"] = {
        "total_cost": round(float(work[cost_col].sum()), 2),
        "avg_cost_per_wo": round(float(work[cost_col].mean()), 2),
        "median_cost": round(float(work[cost_col].median()), 2),
        "max_single_cost": round(float(work[cost_col].max()), 2),
        "records_with_cost": len(work),
        "total_records": len(df),
        "cost_coverage": round(len(work) / max(len(df), 1) * 100, 1),
    }

    # Labor cost estimate
    if labor_col in work.columns:
        work["_labor"] = pd.to_numeric(work[labor_col], errors="coerce").fillna(0)
        total_labor_hours = work["_labor"].sum()
        avg_labor_rate = 75  # Default estimate
        results["stats"]["total_labor_hours"] = round(float(total_labor_hours), 1)
        results["stats"]["estimated_labor_cost"] = round(total_labor_hours * avg_labor_rate, 2)
        results["stats"]["material_cost_estimate"] = round(results["stats"]["total_cost"] - (total_labor_hours * avg_labor_rate), 2)

    # ============================================================
    # 1. COST BY ASSET - Top spending assets
    # ============================================================
    if asset_col in work.columns:
        asset_costs = work[work[asset_col].astype(str).str.strip() != ""].groupby(asset_col).agg(
            total_cost=(cost_col, "sum"),
            avg_cost=(cost_col, "mean"),
            wo_count=(cost_col, "count"),
            max_single=(cost_col, "max"),
        ).reset_index().sort_values("total_cost", ascending=False)

        total = results["stats"]["total_cost"]
        for _, row in asset_costs.head(15).iterrows():
            pct = round(row["total_cost"] / max(total, 1) * 100, 1)
            results["cost_by_asset"].append({
                "asset_id": str(row[asset_col]),
                "total_cost": round(float(row["total_cost"]), 2),
                "avg_cost": round(float(row["avg_cost"]), 2),
                "wo_count": int(row["wo_count"]),
                "max_single": round(float(row["max_single"]), 2),
                "pct_of_total": pct,
            })

    # ============================================================
    # 2. COST BY FAILURE CATEGORY
    # ============================================================
    cat_col = category_col if category_col and category_col in work.columns else None

    if cat_col:
        cat_costs = work[work[cat_col].astype(str).str.strip().isin(["", "nan", "Unknown"]) == False].groupby(cat_col).agg(
            total_cost=(cost_col, "sum"),
            avg_cost=(cost_col, "mean"),
            wo_count=(cost_col, "count"),
        ).reset_index().sort_values("total_cost", ascending=False)

        total = results["stats"]["total_cost"]
        for _, row in cat_costs.head(10).iterrows():
            pct = round(row["total_cost"] / max(total, 1) * 100, 1)
            results["cost_by_category"].append({
                "category": str(row[cat_col]),
                "total_cost": round(float(row["total_cost"]), 2),
                "avg_cost": round(float(row["avg_cost"]), 2),
                "wo_count": int(row["wo_count"]),
                "pct_of_total": pct,
            })

    # ============================================================
    # 3. EMERGENCY VS PLANNED SPEND
    # ============================================================
    if order_type_col in work.columns:
        types = work[order_type_col].astype(str).str.lower()

        emergency_mask = types.str.contains("pm01|breakdown|corrective|emergency|unplanned", na=False)
        planned_mask = types.str.contains("pm02|preventive|planned|scheduled", na=False)

        emergency_cost = float(work.loc[emergency_mask, cost_col].sum())
        planned_cost = float(work.loc[planned_mask, cost_col].sum())
        other_cost = float(work.loc[~emergency_mask & ~planned_mask, cost_col].sum())
        total = emergency_cost + planned_cost + other_cost

        results["emergency_vs_planned"] = {
            "emergency_cost": round(emergency_cost, 2),
            "planned_cost": round(planned_cost, 2),
            "other_cost": round(other_cost, 2),
            "emergency_pct": round(emergency_cost / max(total, 1) * 100, 1),
            "planned_pct": round(planned_cost / max(total, 1) * 100, 1),
            "emergency_count": int(emergency_mask.sum()),
            "planned_count": int(planned_mask.sum()),
            "ratio_label": "Healthy" if emergency_cost < planned_cost else "Reactive-Heavy",
        }

    # ============================================================
    # 4. HIGH-COST REPEAT REPAIRS
    # ============================================================
    if asset_col in work.columns and desc_col in work.columns:
        work["_desc_clean"] = work[desc_col].astype(str).str.lower().str.strip()
        repeat_costs = work.groupby([asset_col, "_desc_clean"]).agg(
            total_cost=(cost_col, "sum"),
            count=(cost_col, "count"),
            avg_cost=(cost_col, "mean"),
        ).reset_index()

        repeat_costs = repeat_costs[repeat_costs["count"] >= 3].sort_values("total_cost", ascending=False)

        for _, row in repeat_costs.head(10).iterrows():
            results["high_cost_repeats"].append({
                "asset_id": str(row[asset_col]),
                "description": str(row["_desc_clean"])[:80],
                "total_cost": round(float(row["total_cost"]), 2),
                "occurrences": int(row["count"]),
                "avg_cost_each": round(float(row["avg_cost"]), 2),
            })

    # ============================================================
    # 5. COST TRENDS BY MONTH
    # ============================================================
    if date_col in work.columns:
        work["_date"] = pd.to_datetime(work[date_col], errors="coerce")
        monthly = work.dropna(subset=["_date"]).groupby(work["_date"].dt.to_period("M")).agg(
            total_cost=(cost_col, "sum"),
            wo_count=(cost_col, "count"),
            avg_cost=(cost_col, "mean"),
        ).reset_index()

        for _, row in monthly.iterrows():
            results["cost_trends"][str(row["_date"])] = {
                "total_cost": round(float(row["total_cost"]), 2),
                "wo_count": int(row["wo_count"]),
                "avg_cost": round(float(row["avg_cost"]), 2),
            }

    # ============================================================
    # 6. OPTIMIZATION OPPORTUNITIES
    # ============================================================
    # High emergency spend
    if results["emergency_vs_planned"].get("emergency_pct", 0) > 50:
        savings = round(results["emergency_vs_planned"]["emergency_cost"] * 0.25, 2)
        results["optimization_opportunities"].append({
            "priority": "HIGH",
            "title": "Reduce Emergency Maintenance Spend",
            "detail": f"Emergency repairs account for {results['emergency_vs_planned']['emergency_pct']}% of total spend. Industry best practice is below 20%.",
            "potential_savings": savings,
            "action": "Convert top 5 emergency failure modes to planned PM tasks with defined intervals.",
        })

    # Top asset consuming disproportionate spend
    if results["cost_by_asset"] and results["cost_by_asset"][0]["pct_of_total"] > 15:
        top = results["cost_by_asset"][0]
        results["optimization_opportunities"].append({
            "priority": "HIGH",
            "title": f"Investigate High-Cost Asset: {top['asset_id']}",
            "detail": f"This single asset accounts for {top['pct_of_total']}% of total maintenance spend (${top['total_cost']:,.0f}).",
            "potential_savings": round(top["total_cost"] * 0.3, 2),
            "action": "Conduct root cause analysis. Consider replacement if repair costs exceed 50% of replacement value.",
        })

    # Repeat repairs wasting money
    if results["high_cost_repeats"]:
        top_repeat = results["high_cost_repeats"][0]
        results["optimization_opportunities"].append({
            "priority": "HIGH",
            "title": f"Eliminate Repeat Repair: {top_repeat['asset_id']}",
            "detail": f"'{top_repeat['description']}' has been done {top_repeat['occurrences']} times costing ${top_repeat['total_cost']:,.0f} total.",
            "potential_savings": round(top_repeat["total_cost"] * 0.7, 2),
            "action": "This repair keeps recurring because the root cause isn't being addressed. Investigate and implement a permanent fix.",
        })

    return results


# ============================================================
# STANDALONE TEST
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("MaintSignal - Spare Parts & Cost Analysis Demo")
    print("=" * 60)

    import random
    np.random.seed(42)

    n = 1500
    assets = ["P-101", "P-102", "C-301", "M-105", "K-201", "V-501"]
    df = pd.DataFrame({
        "asset_id": [random.choice(assets) for _ in range(n)],
        "description": [random.choice(["seal replacement", "bearing change", "PM inspection", "motor repair", "valve rebuild"]) for _ in range(n)],
        "cost": [round(random.uniform(100, 8000), 2) for _ in range(n)],
        "labor_hours": [round(random.uniform(0.5, 24), 1) for _ in range(n)],
        "order_type": [random.choice(["PM01", "PM01", "PM02", "PM02", "PM03"]) for _ in range(n)],
        "created_date": pd.date_range("2024-01-01", periods=n, freq="6h"),
    })

    results = analyze_spare_parts_costs(df)
    
    print(f"\nTotal Spend: ${results['stats']['total_cost']:,.0f}")
    print(f"Avg per WO: ${results['stats']['avg_cost_per_wo']:,.0f}")
    print(f"Records with cost: {results['stats']['records_with_cost']}")

    print(f"\n--- Top Cost Assets ---")
    for a in results["cost_by_asset"][:5]:
        print(f"  {a['asset_id']}: ${a['total_cost']:,.0f} ({a['pct_of_total']}%) - {a['wo_count']} WOs")

    e = results["emergency_vs_planned"]
    if e:
        print(f"\n--- Emergency vs Planned ---")
        print(f"  Emergency: ${e['emergency_cost']:,.0f} ({e['emergency_pct']}%)")
        print(f"  Planned: ${e['planned_cost']:,.0f} ({e['planned_pct']}%)")
        print(f"  Status: {e['ratio_label']}")

    print(f"\n--- Optimization Opportunities ---")
    for opp in results["optimization_opportunities"]:
        print(f"  [{opp['priority']}] {opp['title']}")
        print(f"    Potential savings: ${opp['potential_savings']:,.0f}")
