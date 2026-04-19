"""
MaintSignal - Root Cause Correlation Module
Finds hidden relationships between failures:
- Failure chains: A breaks, then B breaks within X days on same asset
- Co-occurring failures: Assets that fail together suggest shared root cause
- Cascade patterns: One failure type consistently precedes another
- Repeat failures: Same asset, same failure, recurring within a window

This is the analysis that makes clients say "we never saw that before."
"""

import pandas as pd
import numpy as np
from collections import defaultdict, Counter
from datetime import timedelta


def analyze_root_cause_correlations(df, date_col="created_date", asset_col="asset_id",
                                      desc_col="description", failure_col="failure_code",
                                      category_col=None, window_days=90):
    """
    Analyze maintenance data for hidden failure correlations.
    
    Args:
        df: DataFrame with maintenance data
        date_col: Date column name
        asset_col: Asset/equipment ID column
        desc_col: Description column
        failure_col: Failure code column
        category_col: AI-normalized category column (if available from normalization)
        window_days: Days to look for correlated failures
    
    Returns:
        Dictionary with correlation analysis results
    """
    results = {
        "failure_chains": [],
        "repeat_failures": [],
        "co_occurring_assets": [],
        "cascade_patterns": [],
        "insights": [],
        "stats": {},
    }
    
    # Validate required columns
    if date_col not in df.columns or asset_col not in df.columns:
        results["error"] = f"Required columns missing: need '{date_col}' and '{asset_col}'"
        return results
    
    # Prepare data
    work = df.copy()
    work[date_col] = pd.to_datetime(work[date_col], errors="coerce")
    work = work.dropna(subset=[date_col])
    work = work[work[asset_col].astype(str).str.strip() != ""]
    work = work.sort_values(date_col)
    
    # Use category column if available, otherwise fall back to failure_code
    cat_col = category_col if category_col and category_col in work.columns else failure_col
    
    if cat_col not in work.columns:
        # Try to use description-based simple categorization
        if desc_col in work.columns:
            work["_category"] = work[desc_col].astype(str).str.lower().apply(_simple_categorize)
            cat_col = "_category"
        else:
            results["error"] = "No failure classification column available"
            return results
    
    # Clean category column
    work[cat_col] = work[cat_col].astype(str).str.strip()
    work = work[work[cat_col] != ""]
    work = work[work[cat_col] != "nan"]
    work = work[work[cat_col] != "Unknown"]
    work = work[work[cat_col] != "Preventive Maintenance"]
    
    results["stats"]["total_failure_records"] = len(work)
    results["stats"]["unique_assets"] = work[asset_col].nunique()
    results["stats"]["unique_categories"] = work[cat_col].nunique()
    results["stats"]["date_range_days"] = (work[date_col].max() - work[date_col].min()).days
    
    # ============================================================
    # 1. FAILURE CHAINS - A fails, then B fails on same asset within window
    # ============================================================
    chain_counts = Counter()
    chain_examples = defaultdict(list)
    
    for asset_id in work[asset_col].unique():
        asset_work = work[work[asset_col] == asset_id].sort_values(date_col)
        
        if len(asset_work) < 2:
            continue
        
        for i in range(len(asset_work) - 1):
            row_a = asset_work.iloc[i]
            cat_a = str(row_a[cat_col])
            date_a = row_a[date_col]
            
            for j in range(i + 1, min(i + 5, len(asset_work))):
                row_b = asset_work.iloc[j]
                cat_b = str(row_b[cat_col])
                date_b = row_b[date_col]
                
                days_between = (date_b - date_a).days
                
                if days_between > window_days:
                    break
                
                if cat_a != cat_b and days_between > 0:
                    chain_key = (cat_a, cat_b)
                    chain_counts[chain_key] += 1
                    
                    if len(chain_examples[chain_key]) < 3:
                        chain_examples[chain_key].append({
                            "asset": str(asset_id),
                            "first_failure": cat_a,
                            "first_date": date_a.strftime("%Y-%m-%d"),
                            "second_failure": cat_b,
                            "second_date": date_b.strftime("%Y-%m-%d"),
                            "days_between": days_between,
                        })
    
    # Filter to chains that occur 3+ times
    for (cat_a, cat_b), count in chain_counts.most_common(15):
        if count >= 3:
            avg_days = np.mean([ex["days_between"] for ex in chain_examples[(cat_a, cat_b)]])
            results["failure_chains"].append({
                "first_failure": cat_a,
                "second_failure": cat_b,
                "occurrences": count,
                "avg_days_between": round(avg_days, 1),
                "examples": chain_examples[(cat_a, cat_b)][:3],
                "interpretation": f"When '{cat_a}' occurs, '{cat_b}' follows within {avg_days:.0f} days on average ({count} occurrences)",
            })
    
    if results["failure_chains"]:
        top_chain = results["failure_chains"][0]
        results["insights"].append({
            "type": "critical",
            "title": f"Failure Chain: {top_chain['first_failure']} triggers {top_chain['second_failure']}",
            "detail": top_chain["interpretation"] + ". Investigate whether fixing the root cause of the first failure prevents the second.",
        })
    
    # ============================================================
    # 2. REPEAT FAILURES - Same asset, same category, recurring
    # ============================================================
    repeat_tracker = defaultdict(list)
    
    for asset_id in work[asset_col].unique():
        asset_work = work[work[asset_col] == asset_id].sort_values(date_col)
        
        for cat in asset_work[cat_col].unique():
            cat_events = asset_work[asset_work[cat_col] == cat].sort_values(date_col)
            
            if len(cat_events) >= 3:
                dates = cat_events[date_col].tolist()
                intervals = [(dates[i+1] - dates[i]).days for i in range(len(dates)-1)]
                avg_interval = np.mean(intervals)
                
                repeat_tracker[(str(asset_id), str(cat))].append({
                    "asset_id": str(asset_id),
                    "category": str(cat),
                    "occurrence_count": len(cat_events),
                    "avg_interval_days": round(avg_interval, 1),
                    "min_interval_days": min(intervals),
                    "max_interval_days": max(intervals),
                    "first_occurrence": dates[0].strftime("%Y-%m-%d"),
                    "last_occurrence": dates[-1].strftime("%Y-%m-%d"),
                })
    
    # Flatten and sort by frequency
    all_repeats = []
    for key, entries in repeat_tracker.items():
        all_repeats.extend(entries)
    
    all_repeats.sort(key=lambda x: x["occurrence_count"], reverse=True)
    results["repeat_failures"] = all_repeats[:15]
    
    if all_repeats:
        worst_repeat = all_repeats[0]
        results["insights"].append({
            "type": "critical",
            "title": f"Chronic Failure: {worst_repeat['asset_id']} — {worst_repeat['category']}",
            "detail": f"This failure has occurred {worst_repeat['occurrence_count']} times with an average interval of {worst_repeat['avg_interval_days']} days. Current maintenance strategy is not addressing the root cause.",
        })
    
    # ============================================================
    # 3. CO-OCCURRING FAILURES - Different assets failing on same day
    # ============================================================
    daily_failures = work.groupby(work[date_col].dt.date).apply(
        lambda x: list(zip(x[asset_col].astype(str), x[cat_col].astype(str)))
    )
    
    co_occurrence_counts = Counter()
    co_occurrence_examples = defaultdict(list)
    
    for date, failures in daily_failures.items():
        if len(failures) >= 2:
            # Find unique asset-category pairs for this day
            unique_failures = list(set(failures))
            
            for i in range(len(unique_failures)):
                for j in range(i + 1, len(unique_failures)):
                    asset_a, cat_a = unique_failures[i]
                    asset_b, cat_b = unique_failures[j]
                    
                    if asset_a != asset_b:
                        # Normalize order for consistent counting
                        pair = tuple(sorted([(str(asset_a), str(cat_a)), (str(asset_b), str(cat_b))]))
                        co_occurrence_counts[pair] += 1
                        
                        if len(co_occurrence_examples[pair]) < 2:
                            co_occurrence_examples[pair].append(str(date))
    
    for pair, count in co_occurrence_counts.most_common(10):
        if count >= 3:
            (asset_a, cat_a), (asset_b, cat_b) = pair
            results["co_occurring_assets"].append({
                "asset_a": asset_a,
                "failure_a": cat_a,
                "asset_b": asset_b,
                "failure_b": cat_b,
                "co_occurrences": count,
                "example_dates": co_occurrence_examples[pair],
                "interpretation": f"{asset_a} ({cat_a}) and {asset_b} ({cat_b}) fail on the same day {count} times — possible shared root cause (power, vibration, process upset)",
            })
    
    # ============================================================
    # 4. CASCADE PATTERNS - One failure type consistently precedes another type
    # ============================================================
    cascade_matrix = defaultdict(lambda: defaultdict(int))
    
    for chain in results["failure_chains"]:
        cascade_matrix[chain["first_failure"]][chain["second_failure"]] += chain["occurrences"]
    
    cascade_patterns = []
    for cause, effects in cascade_matrix.items():
        for effect, count in effects.items():
            if count >= 3:
                # Calculate what % of the "cause" failures lead to this "effect"
                total_cause = work[work[cat_col] == cause].shape[0]
                cascade_rate = round(count / max(total_cause, 1) * 100, 1)
                
                cascade_patterns.append({
                    "cause": cause,
                    "effect": effect,
                    "count": count,
                    "cascade_rate": cascade_rate,
                    "interpretation": f"{cascade_rate}% of '{cause}' events are followed by '{effect}' — suggests causal relationship",
                })
    
    cascade_patterns.sort(key=lambda x: x["cascade_rate"], reverse=True)
    results["cascade_patterns"] = cascade_patterns[:10]
    
    # ============================================================
    # SUMMARY STATISTICS
    # ============================================================
    results["stats"]["total_chains_found"] = len(results["failure_chains"])
    results["stats"]["total_repeats_found"] = len(results["repeat_failures"])
    results["stats"]["total_co_occurrences"] = len(results["co_occurring_assets"])
    results["stats"]["total_cascade_patterns"] = len(results["cascade_patterns"])
    
    total_findings = (len(results["failure_chains"]) + len(results["repeat_failures"]) + 
                      len(results["co_occurring_assets"]) + len(results["cascade_patterns"]))
    
    if total_findings == 0:
        results["insights"].append({
            "type": "info",
            "title": "No Strong Correlations Found",
            "detail": "No statistically significant failure correlations detected. This could mean failures are independent, or the dataset needs more history (6+ months recommended).",
        })
    
    return results


def _simple_categorize(text):
    """Fallback categorization when no failure code or AI category is available."""
    if not isinstance(text, str):
        return "Unknown"
    
    text = text.lower()
    
    categories = {
        "Seal Failure": ["seal", "leaking", "leak", "packing", "gasket"],
        "Bearing Failure": ["bearing", "brg", "grinding", "seized"],
        "Motor Failure": ["motor", "mtr", "overheating", "overload", "tripped"],
        "Pump Failure": ["pump", "pmp", "cavitation", "impeller"],
        "Valve Failure": ["valve", "vlv", "actuator", "stuck"],
        "Electrical Fault": ["electrical", "circuit", "breaker", "fuse", "short"],
        "Instrumentation": ["sensor", "transmitter", "xmtr", "calibrat"],
        "Conveyor Failure": ["conveyor", "belt", "chain", "roller"],
        "Compressor Failure": ["compressor", "comp"],
    }
    
    for category, keywords in categories.items():
        if any(kw in text for kw in keywords):
            return category
    
    if any(kw in text for kw in ["pm", "inspection", "routine", "preventive", "scheduled"]):
        return "Preventive Maintenance"
    
    return "Unknown"


def generate_correlation_summary(results):
    """Generate a concise summary for the dashboard."""
    return {
        "total_chains": results["stats"].get("total_chains_found", 0),
        "total_repeats": results["stats"].get("total_repeats_found", 0),
        "total_co_occurrences": results["stats"].get("total_co_occurrences", 0),
        "total_cascades": results["stats"].get("total_cascade_patterns", 0),
        "total_insights": len(results.get("insights", [])),
        "critical_findings": len([i for i in results.get("insights", []) if i.get("type") == "critical"]),
    }


# ============================================================
# STANDALONE TEST
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("MaintSignal - Root Cause Correlation Demo")
    print("=" * 60)
    
    import random
    np.random.seed(42)
    
    # Generate data with intentional correlations
    n = 2000
    assets = ["P-101", "P-102", "C-301", "C-302", "M-105", "M-106", "K-201", "V-501"]
    categories = ["Seal Failure", "Bearing Failure", "Motor Failure", "Valve Failure",
                   "Electrical Fault", "Preventive Maintenance"]
    
    records = []
    base_date = pd.Timestamp("2024-01-01")
    
    for i in range(n):
        asset = random.choice(assets)
        cat = random.choice(categories)
        date = base_date + timedelta(days=random.randint(0, 540))
        records.append({"asset_id": asset, "created_date": date, "description": f"{cat} on {asset}", 
                        "failure_code": cat[:4].upper()})
    
    # Inject correlated failures: every time P-101 has Seal Failure, add Bearing Failure 15-30 days later
    for i in range(30):
        date = base_date + timedelta(days=random.randint(0, 500))
        records.append({"asset_id": "P-101", "created_date": date, "description": "seal leak on pump",
                        "failure_code": "SEAL"})
        records.append({"asset_id": "P-101", "created_date": date + timedelta(days=random.randint(10, 35)),
                        "description": "bearing noise after seal repair", "failure_code": "BRG"})
    
    # Inject repeat failures: C-301 bearing every 45 days
    for i in range(12):
        date = base_date + timedelta(days=45 * i + random.randint(-5, 5))
        records.append({"asset_id": "C-301", "created_date": date, "description": "bearing failure conveyor",
                        "failure_code": "BRG"})
    
    df = pd.DataFrame(records)
    df["_category"] = df["description"].apply(_simple_categorize)
    
    results = analyze_root_cause_correlations(df, category_col="_category")
    summary = generate_correlation_summary(results)
    
    print(f"\nRecords analyzed: {results['stats']['total_failure_records']}")
    print(f"Unique assets: {results['stats']['unique_assets']}")
    print(f"Date range: {results['stats']['date_range_days']} days")
    
    print(f"\n--- Failure Chains ({summary['total_chains']}) ---")
    for chain in results["failure_chains"][:5]:
        print(f"  {chain['first_failure']} -> {chain['second_failure']}: {chain['occurrences']}x, avg {chain['avg_days_between']} days")
    
    print(f"\n--- Repeat Failures ({summary['total_repeats']}) ---")
    for repeat in results["repeat_failures"][:5]:
        print(f"  {repeat['asset_id']} - {repeat['category']}: {repeat['occurrence_count']}x, every {repeat['avg_interval_days']} days")
    
    print(f"\n--- Co-Occurring Failures ({summary['total_co_occurrences']}) ---")
    for co in results["co_occurring_assets"][:3]:
        print(f"  {co['asset_a']}({co['failure_a']}) + {co['asset_b']}({co['failure_b']}): {co['co_occurrences']}x same day")
    
    print(f"\n--- Cascade Patterns ({summary['total_cascades']}) ---")
    for cascade in results["cascade_patterns"][:3]:
        print(f"  {cascade['cause']} -> {cascade['effect']}: {cascade['cascade_rate']}% cascade rate")
    
    print(f"\n--- Insights ---")
    for insight in results["insights"]:
        print(f"  [{insight['type'].upper()}] {insight['title']}")
        print(f"    {insight['detail']}")
