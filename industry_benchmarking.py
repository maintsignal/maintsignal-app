"""
MaintSignal - Industry Benchmarking Module
Compares client maintenance metrics against industry averages.
Shows where they're better or worse than peers.

Benchmark data sourced from:
- SMRP Best Practices (Society for Maintenance & Reliability Professionals)
- Solomon Associates benchmarks
- Limble CMMS Industry Report 2026
- Plant Engineering maintenance surveys
"""

import pandas as pd
import numpy as np


# Industry benchmark data (averages from published studies)
INDUSTRY_BENCHMARKS = {
    "pharmaceutical": {
        "name": "Pharmaceutical / Life Sciences",
        "metrics": {
            "pm_ratio": {"value": 70, "unit": "%", "label": "Planned Maintenance Ratio", "direction": "higher_better",
                         "world_class": 85, "average": 65, "poor": 45, "source": "ISPE Baseline Guide"},
            "data_completeness": {"value": 80, "unit": "%", "label": "Data Completeness", "direction": "higher_better",
                                   "world_class": 95, "average": 75, "poor": 55, "source": "GxP Data Integrity Guidelines"},
            "failure_code_usage": {"value": 75, "unit": "%", "label": "Failure Code Fill Rate", "direction": "higher_better",
                                    "world_class": 95, "average": 70, "poor": 40, "source": "ISPE Baseline Guide"},
            "mttr_hours": {"value": 4.5, "unit": "hrs", "label": "Mean Time to Repair", "direction": "lower_better",
                           "world_class": 2, "average": 5, "poor": 12, "source": "SMRP Best Practice"},
            "reactive_pct": {"value": 25, "unit": "%", "label": "Reactive Maintenance %", "direction": "lower_better",
                              "world_class": 10, "average": 30, "poor": 55, "source": "SMRP Metric 5.5.6"},
            "cost_per_wo": {"value": 850, "unit": "$", "label": "Avg Cost per Work Order", "direction": "lower_better",
                             "world_class": 400, "average": 900, "poor": 2000, "source": "Industry Average"},
        }
    },
    "food_and_beverage": {
        "name": "Food & Beverage",
        "metrics": {
            "pm_ratio": {"value": 60, "unit": "%", "label": "Planned Maintenance Ratio", "direction": "higher_better",
                         "world_class": 80, "average": 55, "poor": 35, "source": "FSMA Compliance Data"},
            "data_completeness": {"value": 65, "unit": "%", "label": "Data Completeness", "direction": "higher_better",
                                   "world_class": 90, "average": 60, "poor": 40, "source": "Food Industry Survey"},
            "failure_code_usage": {"value": 55, "unit": "%", "label": "Failure Code Fill Rate", "direction": "higher_better",
                                    "world_class": 85, "average": 50, "poor": 25, "source": "FSMA Audit Data"},
            "mttr_hours": {"value": 3.5, "unit": "hrs", "label": "Mean Time to Repair", "direction": "lower_better",
                           "world_class": 1.5, "average": 4, "poor": 10, "source": "SMRP Best Practice"},
            "reactive_pct": {"value": 35, "unit": "%", "label": "Reactive Maintenance %", "direction": "lower_better",
                              "world_class": 15, "average": 40, "poor": 65, "source": "SMRP Metric 5.5.6"},
            "cost_per_wo": {"value": 650, "unit": "$", "label": "Avg Cost per Work Order", "direction": "lower_better",
                             "world_class": 300, "average": 700, "poor": 1500, "source": "Industry Average"},
        }
    },
    "oil_and_gas": {
        "name": "Oil & Gas / Petrochemical",
        "metrics": {
            "pm_ratio": {"value": 65, "unit": "%", "label": "Planned Maintenance Ratio", "direction": "higher_better",
                         "world_class": 85, "average": 60, "poor": 40, "source": "Solomon Associates"},
            "data_completeness": {"value": 75, "unit": "%", "label": "Data Completeness", "direction": "higher_better",
                                   "world_class": 95, "average": 70, "poor": 50, "source": "API 580/581 Requirements"},
            "failure_code_usage": {"value": 70, "unit": "%", "label": "Failure Code Fill Rate", "direction": "higher_better",
                                    "world_class": 90, "average": 65, "poor": 35, "source": "Solomon Associates"},
            "mttr_hours": {"value": 6, "unit": "hrs", "label": "Mean Time to Repair", "direction": "lower_better",
                           "world_class": 3, "average": 7, "poor": 18, "source": "SMRP Best Practice"},
            "reactive_pct": {"value": 30, "unit": "%", "label": "Reactive Maintenance %", "direction": "lower_better",
                              "world_class": 10, "average": 35, "poor": 60, "source": "SMRP Metric 5.5.6"},
            "cost_per_wo": {"value": 1200, "unit": "$", "label": "Avg Cost per Work Order", "direction": "lower_better",
                             "world_class": 600, "average": 1300, "poor": 3500, "source": "Solomon Associates"},
        }
    },
    "automotive_manufacturing": {
        "name": "Automotive Manufacturing",
        "metrics": {
            "pm_ratio": {"value": 75, "unit": "%", "label": "Planned Maintenance Ratio", "direction": "higher_better",
                         "world_class": 90, "average": 70, "poor": 45, "source": "IATF 16949 TPM Targets"},
            "data_completeness": {"value": 80, "unit": "%", "label": "Data Completeness", "direction": "higher_better",
                                   "world_class": 95, "average": 75, "poor": 50, "source": "IATF Audit Requirements"},
            "failure_code_usage": {"value": 75, "unit": "%", "label": "Failure Code Fill Rate", "direction": "higher_better",
                                    "world_class": 95, "average": 70, "poor": 40, "source": "IATF PFMEA Requirements"},
            "mttr_hours": {"value": 3, "unit": "hrs", "label": "Mean Time to Repair", "direction": "lower_better",
                           "world_class": 1, "average": 3.5, "poor": 8, "source": "TPM Best Practice"},
            "reactive_pct": {"value": 20, "unit": "%", "label": "Reactive Maintenance %", "direction": "lower_better",
                              "world_class": 5, "average": 25, "poor": 50, "source": "TPM Pillar Standards"},
            "cost_per_wo": {"value": 750, "unit": "$", "label": "Avg Cost per Work Order", "direction": "lower_better",
                             "world_class": 350, "average": 800, "poor": 1800, "source": "Industry Average"},
        }
    },
    "general_manufacturing": {
        "name": "General Manufacturing",
        "metrics": {
            "pm_ratio": {"value": 60, "unit": "%", "label": "Planned Maintenance Ratio", "direction": "higher_better",
                         "world_class": 80, "average": 55, "poor": 35, "source": "Plant Engineering Survey 2025"},
            "data_completeness": {"value": 65, "unit": "%", "label": "Data Completeness", "direction": "higher_better",
                                   "world_class": 90, "average": 60, "poor": 40, "source": "Limble CMMS Report 2026"},
            "failure_code_usage": {"value": 55, "unit": "%", "label": "Failure Code Fill Rate", "direction": "higher_better",
                                    "world_class": 85, "average": 50, "poor": 25, "source": "Limble CMMS Report 2026"},
            "mttr_hours": {"value": 4, "unit": "hrs", "label": "Mean Time to Repair", "direction": "lower_better",
                           "world_class": 2, "average": 5, "poor": 12, "source": "SMRP Best Practice"},
            "reactive_pct": {"value": 35, "unit": "%", "label": "Reactive Maintenance %", "direction": "lower_better",
                              "world_class": 15, "average": 40, "poor": 65, "source": "SMRP Metric 5.5.6"},
            "cost_per_wo": {"value": 700, "unit": "$", "label": "Avg Cost per Work Order", "direction": "lower_better",
                             "world_class": 300, "average": 750, "poor": 1800, "source": "Industry Average"},
        }
    },
}


def calculate_client_metrics(df, quality_results=None, downtime_results=None):
    """
    Calculate the client's actual metrics from their data.
    Returns dict of metric_name -> value.
    """
    metrics = {}
    total = len(df)

    # PM Ratio
    if "order_type" in df.columns:
        types = df["order_type"].astype(str).str.lower()
        planned = types.str.contains("pm02|preventive|planned|scheduled", na=False).sum()
        reactive = types.str.contains("pm01|breakdown|corrective|emergency|unplanned", na=False).sum()
        total_typed = planned + reactive
        if total_typed > 0:
            metrics["pm_ratio"] = round(planned / total_typed * 100, 1)
            metrics["reactive_pct"] = round(reactive / total_typed * 100, 1)

    # Data Completeness
    if quality_results and "avg_completeness" in quality_results:
        metrics["data_completeness"] = quality_results["avg_completeness"]

    # Failure Code Usage
    if "failure_code" in df.columns:
        filled = df["failure_code"].astype(str).str.strip().replace("", np.nan).notna().sum()
        metrics["failure_code_usage"] = round(filled / total * 100, 1)

    # MTTR
    if "labor_hours" in df.columns:
        breakdown_mask = pd.Series([True] * total)
        if "order_type" in df.columns:
            breakdown_mask = df["order_type"].astype(str).str.lower().str.contains("pm01|breakdown|corrective|emergency", na=False)
        breakdown_hours = df.loc[breakdown_mask, "labor_hours"]
        if len(breakdown_hours) > 0:
            metrics["mttr_hours"] = round(breakdown_hours.mean(), 1)

    # Cost per WO
    if "cost" in df.columns:
        avg_cost = df["cost"].mean()
        if pd.notna(avg_cost):
            metrics["cost_per_wo"] = round(avg_cost, 0)

    return metrics


def benchmark_against_industry(client_metrics, industry="general_manufacturing"):
    """
    Compare client metrics against industry benchmarks.
    Returns detailed comparison with ratings.
    """
    benchmarks = INDUSTRY_BENCHMARKS.get(industry, INDUSTRY_BENCHMARKS["general_manufacturing"])
    
    results = {
        "industry": benchmarks["name"],
        "comparisons": [],
        "overall_rating": "",
        "strengths": [],
        "weaknesses": [],
        "summary_score": 0,
    }

    scores = []

    for metric_key, benchmark in benchmarks["metrics"].items():
        if metric_key not in client_metrics:
            continue

        client_value = client_metrics[metric_key]
        
        comparison = {
            "metric": benchmark["label"],
            "client_value": client_value,
            "unit": benchmark["unit"],
            "industry_average": benchmark["average"],
            "world_class": benchmark["world_class"],
            "poor": benchmark["poor"],
            "source": benchmark["source"],
            "direction": benchmark["direction"],
        }

        # Rate performance
        if benchmark["direction"] == "higher_better":
            if client_value >= benchmark["world_class"]:
                comparison["rating"] = "world_class"
                comparison["rating_label"] = "World Class"
                comparison["vs_average"] = round(client_value - benchmark["average"], 1)
                scores.append(100)
            elif client_value >= benchmark["average"]:
                comparison["rating"] = "above_average"
                comparison["rating_label"] = "Above Average"
                comparison["vs_average"] = round(client_value - benchmark["average"], 1)
                scores.append(75)
            elif client_value >= benchmark["poor"]:
                comparison["rating"] = "below_average"
                comparison["rating_label"] = "Below Average"
                comparison["vs_average"] = round(client_value - benchmark["average"], 1)
                scores.append(40)
            else:
                comparison["rating"] = "critical"
                comparison["rating_label"] = "Critical Gap"
                comparison["vs_average"] = round(client_value - benchmark["average"], 1)
                scores.append(15)
        else:  # lower_better
            if client_value <= benchmark["world_class"]:
                comparison["rating"] = "world_class"
                comparison["rating_label"] = "World Class"
                comparison["vs_average"] = round(benchmark["average"] - client_value, 1)
                scores.append(100)
            elif client_value <= benchmark["average"]:
                comparison["rating"] = "above_average"
                comparison["rating_label"] = "Above Average"
                comparison["vs_average"] = round(benchmark["average"] - client_value, 1)
                scores.append(75)
            elif client_value <= benchmark["poor"]:
                comparison["rating"] = "below_average"
                comparison["rating_label"] = "Below Average"
                comparison["vs_average"] = round(benchmark["average"] - client_value, 1)
                scores.append(40)
            else:
                comparison["rating"] = "critical"
                comparison["rating_label"] = "Critical Gap"
                comparison["vs_average"] = round(benchmark["average"] - client_value, 1)
                scores.append(15)

        results["comparisons"].append(comparison)

        # Track strengths and weaknesses
        if comparison["rating"] in ["world_class", "above_average"]:
            results["strengths"].append(f"{benchmark['label']}: {client_value}{benchmark['unit']} ({comparison['rating_label']})")
        elif comparison["rating"] in ["below_average", "critical"]:
            gap_text = f"{abs(comparison['vs_average'])}{benchmark['unit']} {'below' if benchmark['direction'] == 'higher_better' else 'above'} average"
            results["weaknesses"].append(f"{benchmark['label']}: {client_value}{benchmark['unit']} — {gap_text}")

    # Overall score
    results["summary_score"] = round(np.mean(scores), 1) if scores else 0
    
    if results["summary_score"] >= 80:
        results["overall_rating"] = "Leading"
    elif results["summary_score"] >= 60:
        results["overall_rating"] = "Competitive"
    elif results["summary_score"] >= 40:
        results["overall_rating"] = "Below Average"
    else:
        results["overall_rating"] = "Needs Improvement"

    return results


# ============================================================
# STANDALONE TEST
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("MaintSignal - Industry Benchmarking Demo")
    print("=" * 60)

    # Simulate client metrics
    client = {
        "pm_ratio": 48,
        "data_completeness": 61,
        "failure_code_usage": 42,
        "mttr_hours": 6.2,
        "reactive_pct": 52,
        "cost_per_wo": 1150,
    }

    for industry in ["pharmaceutical", "general_manufacturing", "oil_and_gas"]:
        results = benchmark_against_industry(client, industry)
        print(f"\n--- {results['industry']} ---")
        print(f"Overall: {results['summary_score']}% ({results['overall_rating']})")
        
        for comp in results["comparisons"]:
            rating_icon = {"world_class": "★", "above_average": "✓", "below_average": "!", "critical": "✗"}.get(comp["rating"], "?")
            print(f"  [{rating_icon}] {comp['metric']}: {comp['client_value']}{comp['unit']} vs {comp['industry_average']}{comp['unit']} avg ({comp['rating_label']})")
        
        if results["strengths"]:
            print(f"  Strengths: {', '.join(results['strengths'][:2])}")
        if results["weaknesses"]:
            print(f"  Weaknesses: {', '.join(results['weaknesses'][:2])}")
