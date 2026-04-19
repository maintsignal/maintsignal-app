"""
MaintSignal - Compliance Gap Detection Module
Analyzes maintenance data against industry-specific regulatory requirements.
Supports: FDA 21 CFR Part 11, ISO 55001, IATF 16949, FSMA, OSHA PSM, API 580/581

This module checks what an auditor would check - before the auditor arrives.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta


# Regulatory frameworks and their data requirements
COMPLIANCE_FRAMEWORKS = {
    "fda_21cfr11": {
        "name": "FDA 21 CFR Part 11",
        "industries": ["pharmaceutical", "medical_device", "biotech"],
        "description": "Electronic records and signatures for pharmaceutical manufacturing",
        "required_fields": {
            "asset_id": {"label": "Equipment Identification", "weight": 10, "reason": "Every maintenance action must be traceable to specific equipment"},
            "description": {"label": "Work Description", "weight": 10, "reason": "Complete description of maintenance performed is required for audit trail"},
            "created_date": {"label": "Date/Time Stamp", "weight": 10, "reason": "Accurate timestamps required for electronic record compliance"},
            "completed_date": {"label": "Completion Date", "weight": 9, "reason": "Duration tracking required for GMP compliance"},
            "failure_code": {"label": "Failure Classification", "weight": 8, "reason": "Standardized failure coding required for CAPA investigations"},
            "cause_code": {"label": "Root Cause Code", "weight": 9, "reason": "Root cause documentation required for deviation reports"},
            "labor_hours": {"label": "Labor Documentation", "weight": 6, "reason": "Resource tracking for validation activities"},
            "status": {"label": "Work Order Status", "weight": 7, "reason": "Lifecycle tracking required for electronic records"},
        },
        "checks": [
            {"name": "Audit Trail Completeness", "description": "All records must have creator, timestamp, and completion data"},
            {"name": "Electronic Signature Traceability", "description": "Work orders must be closeable to a specific person"},
            {"name": "Change Control Documentation", "description": "Equipment modifications must be documented with before/after states"},
            {"name": "Calibration Records", "description": "Calibration activities must include standards used and results"},
            {"name": "Deviation Documentation", "description": "Unplanned maintenance must link to deviation/CAPA records"},
        ]
    },
    "iso_55001": {
        "name": "ISO 55001 Asset Management",
        "industries": ["general_manufacturing", "utilities", "oil_and_gas", "mining"],
        "description": "International standard for asset management systems",
        "required_fields": {
            "asset_id": {"label": "Asset Identification", "weight": 10, "reason": "Complete asset register is foundational to ISO 55001"},
            "location": {"label": "Asset Location", "weight": 8, "reason": "Physical location tracking required for asset management plans"},
            "description": {"label": "Activity Description", "weight": 8, "reason": "Work performed must be documented for lifecycle management"},
            "created_date": {"label": "Activity Date", "weight": 7, "reason": "Timeline tracking for asset lifecycle decisions"},
            "completed_date": {"label": "Completion Date", "weight": 7, "reason": "Duration data needed for performance measurement"},
            "failure_code": {"label": "Failure Mode", "weight": 9, "reason": "Failure mode data drives risk-based decision making"},
            "cost": {"label": "Cost Recording", "weight": 8, "reason": "Lifecycle costing is core to asset management planning"},
            "order_type": {"label": "Activity Classification", "weight": 7, "reason": "Planned vs unplanned ratio is a key ISO 55001 KPI"},
        },
        "checks": [
            {"name": "Asset Register Completeness", "description": "All physical assets must be identified and tracked"},
            {"name": "Lifecycle Cost Tracking", "description": "Maintenance costs must be attributable to specific assets"},
            {"name": "Risk-Based Prioritization", "description": "Failure data must support criticality assessment"},
            {"name": "Performance Measurement", "description": "KPIs (MTBF, MTTR, availability) must be calculable from data"},
            {"name": "Continuous Improvement Evidence", "description": "Trend data must demonstrate improvement over time"},
        ]
    },
    "iatf_16949": {
        "name": "IATF 16949 Automotive Quality",
        "industries": ["automotive_manufacturing", "auto_parts"],
        "description": "Quality management system for automotive production",
        "required_fields": {
            "asset_id": {"label": "Equipment ID", "weight": 10, "reason": "TPM requires equipment-level tracking"},
            "description": {"label": "Maintenance Description", "weight": 9, "reason": "Detailed records required for FMEA updates"},
            "failure_code": {"label": "Failure Mode Code", "weight": 10, "reason": "PFMEA requires systematic failure mode documentation"},
            "cause_code": {"label": "Root Cause", "weight": 10, "reason": "8D/root cause analysis requires cause documentation"},
            "created_date": {"label": "Event Date", "weight": 8, "reason": "Timeline required for OEE calculation"},
            "completed_date": {"label": "Resolution Date", "weight": 8, "reason": "MTTR tracking for customer scorecards"},
            "downtime_start": {"label": "Downtime Start", "weight": 9, "reason": "OEE availability calculation requires precise downtime"},
            "downtime_end": {"label": "Downtime End", "weight": 9, "reason": "OEE availability calculation requires precise downtime"},
            "labor_hours": {"label": "Labor Hours", "weight": 6, "reason": "Resource planning for TPM activities"},
        },
        "checks": [
            {"name": "TPM Documentation", "description": "Total Productive Maintenance activities must be fully recorded"},
            {"name": "OEE Data Availability", "description": "Downtime, quality, and performance data must support OEE calculation"},
            {"name": "PFMEA Linkage", "description": "Failure modes must map to Process FMEA for continuous updates"},
            {"name": "Preventive Maintenance Compliance", "description": "PM schedule adherence must be measurable"},
            {"name": "Corrective Action Traceability", "description": "Every breakdown must link to corrective/preventive action"},
        ]
    },
    "fsma": {
        "name": "FSMA Food Safety",
        "industries": ["food_and_beverage", "food_processing"],
        "description": "FDA Food Safety Modernization Act requirements",
        "required_fields": {
            "asset_id": {"label": "Equipment ID", "weight": 10, "reason": "Food contact equipment must be individually tracked"},
            "description": {"label": "Maintenance Description", "weight": 9, "reason": "Sanitary maintenance activities require documentation"},
            "created_date": {"label": "Activity Date", "weight": 9, "reason": "Pre-operational inspections require date tracking"},
            "completed_date": {"label": "Completion Date", "weight": 8, "reason": "Turnaround time for food safety equipment"},
            "failure_code": {"label": "Failure Type", "weight": 8, "reason": "Contamination-related failures require classification"},
            "order_type": {"label": "Activity Type", "weight": 7, "reason": "Sanitation vs maintenance must be distinguishable"},
            "status": {"label": "Completion Status", "weight": 8, "reason": "Open work orders on food contact equipment are audit findings"},
        },
        "checks": [
            {"name": "Sanitary Equipment Records", "description": "Food contact surfaces maintenance must be separately trackable"},
            {"name": "Allergen Control Documentation", "description": "Equipment changeover and cleaning records must be complete"},
            {"name": "Preventive Controls Verification", "description": "Environmental monitoring and equipment verification records"},
            {"name": "Supplier Equipment Records", "description": "Third-party maintenance must be documented to same standard"},
            {"name": "Recall Readiness", "description": "Equipment-to-product traceability must be possible"},
        ]
    },
    "osha_psm": {
        "name": "OSHA PSM (Process Safety)",
        "industries": ["oil_and_gas", "chemical", "refining"],
        "description": "Process Safety Management for hazardous chemicals",
        "required_fields": {
            "asset_id": {"label": "Equipment Tag", "weight": 10, "reason": "PSM-covered equipment must have individual records"},
            "description": {"label": "Work Description", "weight": 10, "reason": "Mechanical integrity requires detailed work documentation"},
            "failure_code": {"label": "Failure Classification", "weight": 9, "reason": "Process safety incidents require failure categorization"},
            "cause_code": {"label": "Root Cause", "weight": 9, "reason": "PSM incident investigation requires root cause"},
            "created_date": {"label": "Event Date", "weight": 8, "reason": "Incident timeline reconstruction for investigations"},
            "completed_date": {"label": "Resolution Date", "weight": 8, "reason": "Time-to-repair for safety-critical equipment"},
            "order_type": {"label": "Work Type", "weight": 8, "reason": "Distinguish inspection, repair, replacement for MI program"},
            "labor_hours": {"label": "Labor Documentation", "weight": 6, "reason": "Qualified personnel tracking for PSM work"},
        },
        "checks": [
            {"name": "Mechanical Integrity Program", "description": "Inspection and testing records for pressure vessels, piping, relief devices"},
            {"name": "Management of Change", "description": "Equipment modifications must trigger MOC review"},
            {"name": "Pre-Startup Safety Review", "description": "Post-maintenance safety checks before restart"},
            {"name": "Hot Work Documentation", "description": "Hot work permits linked to maintenance activities"},
            {"name": "Incident Investigation Records", "description": "Near-miss and incident data must be analyzable"},
        ]
    }
}


def detect_industry_frameworks(industry):
    """Return applicable compliance frameworks for an industry."""
    applicable = []
    for fw_id, fw in COMPLIANCE_FRAMEWORKS.items():
        if industry in fw["industries"] or industry == "general_manufacturing":
            applicable.append(fw_id)
    
    # Always include ISO 55001 as it applies broadly
    if "iso_55001" not in applicable:
        applicable.append("iso_55001")
    
    return applicable


def analyze_compliance_gaps(df, industry="general_manufacturing", frameworks=None):
    """
    Analyze maintenance data against regulatory compliance requirements.
    
    Returns a comprehensive compliance report with:
    - Overall compliance score per framework
    - Field-level gap analysis
    - Specific audit risk items
    - Prioritized remediation actions
    """
    if frameworks is None:
        frameworks = detect_industry_frameworks(industry)
    
    total_records = len(df)
    results = {
        "industry": industry,
        "total_records": total_records,
        "frameworks_checked": [],
        "overall_compliance_score": 0,
        "critical_gaps": [],
        "remediation_actions": [],
    }
    
    framework_scores = []
    
    for fw_id in frameworks:
        if fw_id not in COMPLIANCE_FRAMEWORKS:
            continue
            
        fw = COMPLIANCE_FRAMEWORKS[fw_id]
        fw_result = {
            "id": fw_id,
            "name": fw["name"],
            "description": fw["description"],
            "field_scores": {},
            "check_results": [],
            "score": 0,
            "risk_level": "low",
        }
        
        # Check field completeness against requirements
        total_weight = 0
        weighted_score = 0
        
        for field, req in fw["required_fields"].items():
            weight = req["weight"]
            total_weight += weight
            
            if field in df.columns:
                if df[field].dtype == 'datetime64[ns]':
                    filled_pct = round(df[field].notna().sum() / total_records * 100, 1)
                else:
                    filled_pct = round(
                        df[field].astype(str).str.strip().replace("", np.nan).notna().sum() 
                        / total_records * 100, 1
                    )
            else:
                filled_pct = 0
            
            field_score = min(filled_pct, 100)
            weighted_score += (field_score / 100) * weight
            
            status = "pass" if filled_pct >= 90 else "warning" if filled_pct >= 70 else "fail"
            
            fw_result["field_scores"][field] = {
                "label": req["label"],
                "completeness": filled_pct,
                "weight": weight,
                "status": status,
                "reason": req["reason"],
            }
            
            if status == "fail":
                results["critical_gaps"].append({
                    "framework": fw["name"],
                    "field": req["label"],
                    "completeness": filled_pct,
                    "reason": req["reason"],
                    "severity": "critical" if weight >= 9 else "major",
                })
        
        fw_score = round((weighted_score / total_weight) * 100, 1) if total_weight > 0 else 0
        fw_result["score"] = fw_score
        fw_result["risk_level"] = "low" if fw_score >= 85 else "medium" if fw_score >= 65 else "high"
        
        # Run framework-specific checks
        for check in fw["checks"]:
            # Determine check result based on available data
            check_result = _run_compliance_check(df, fw_id, check, industry)
            fw_result["check_results"].append(check_result)
        
        framework_scores.append(fw_score)
        results["frameworks_checked"].append(fw_result)
    
    # Overall score
    results["overall_compliance_score"] = round(np.mean(framework_scores), 1) if framework_scores else 0
    
    # Generate remediation actions
    results["remediation_actions"] = _generate_remediation_actions(results)
    
    return results


def _run_compliance_check(df, framework_id, check, industry):
    """Run a specific compliance check against the data."""
    check_name = check["name"]
    result = {
        "name": check_name,
        "description": check["description"],
        "status": "unknown",
        "finding": "",
        "risk": "medium",
    }
    
    # Asset Register Completeness
    if "Asset Register" in check_name or "Asset Identification" in check_name:
        if "asset_id" in df.columns:
            missing = df["asset_id"].astype(str).str.strip().isin(["", "nan"]).sum()
            pct_complete = round((1 - missing / len(df)) * 100, 1)
            if pct_complete >= 95:
                result["status"] = "pass"
                result["finding"] = f"{pct_complete}% of records have equipment identification"
            elif pct_complete >= 80:
                result["status"] = "warning"
                result["finding"] = f"{missing} records ({100-pct_complete}%) missing equipment ID - audit risk"
                result["risk"] = "medium"
            else:
                result["status"] = "fail"
                result["finding"] = f"{missing} records ({100-pct_complete}%) missing equipment ID - critical audit finding"
                result["risk"] = "high"
        else:
            result["status"] = "fail"
            result["finding"] = "No equipment identification field found in data"
            result["risk"] = "critical"
    
    # Audit Trail / Electronic Records
    elif "Audit Trail" in check_name or "Electronic" in check_name:
        has_dates = "created_date" in df.columns and "completed_date" in df.columns
        has_status = "status" in df.columns
        if has_dates and has_status:
            date_complete = df["created_date"].notna().sum() / len(df) * 100
            if date_complete >= 95:
                result["status"] = "pass"
                result["finding"] = f"Timestamp coverage at {date_complete:.1f}%"
            else:
                result["status"] = "warning"
                result["finding"] = f"Timestamp coverage at {date_complete:.1f}% - gaps in audit trail"
                result["risk"] = "medium"
        else:
            result["status"] = "fail"
            result["finding"] = "Missing date or status fields - cannot demonstrate audit trail"
            result["risk"] = "high"
    
    # OEE Data
    elif "OEE" in check_name:
        has_downtime = "downtime_start" in df.columns and "downtime_end" in df.columns
        if has_downtime:
            dt_complete = df["downtime_start"].notna().sum() / len(df) * 100
            if dt_complete >= 80:
                result["status"] = "pass"
                result["finding"] = f"Downtime timestamps available on {dt_complete:.1f}% of records"
            else:
                result["status"] = "warning"
                result["finding"] = f"Only {dt_complete:.1f}% have downtime timestamps - OEE calculation will be inaccurate"
                result["risk"] = "medium"
        else:
            result["status"] = "fail"
            result["finding"] = "No downtime start/end fields - OEE cannot be calculated from this data"
            result["risk"] = "high"
    
    # Lifecycle Cost Tracking
    elif "Cost" in check_name or "Lifecycle" in check_name:
        if "cost" in df.columns and "asset_id" in df.columns:
            has_cost = df["cost"].notna().sum() / len(df) * 100
            has_asset = df["asset_id"].astype(str).str.strip().replace("", np.nan).notna().sum() / len(df) * 100
            if has_cost >= 80 and has_asset >= 80:
                result["status"] = "pass"
                result["finding"] = f"Cost data ({has_cost:.0f}%) and asset linkage ({has_asset:.0f}%) support lifecycle costing"
            else:
                result["status"] = "warning"
                result["finding"] = f"Cost coverage {has_cost:.0f}%, asset linkage {has_asset:.0f}% - lifecycle costing gaps exist"
                result["risk"] = "medium"
        else:
            result["status"] = "fail"
            result["finding"] = "Cannot track maintenance costs to individual assets"
            result["risk"] = "high"
    
    # Performance Measurement (MTBF/MTTR)
    elif "Performance" in check_name or "KPI" in check_name:
        can_calc_mttr = "created_date" in df.columns and "completed_date" in df.columns and "asset_id" in df.columns
        can_calc_failures = "failure_code" in df.columns or "order_type" in df.columns
        if can_calc_mttr and can_calc_failures:
            result["status"] = "pass"
            result["finding"] = "Sufficient data to calculate MTBF, MTTR, and availability KPIs"
        elif can_calc_mttr:
            result["status"] = "warning"
            result["finding"] = "Can calculate MTTR but failure classification gaps limit MTBF accuracy"
            result["risk"] = "medium"
        else:
            result["status"] = "fail"
            result["finding"] = "Cannot calculate standard maintenance KPIs from available data"
            result["risk"] = "high"
    
    # Preventive Maintenance Compliance
    elif "Preventive" in check_name or "PM" in check_name or "TPM" in check_name:
        if "order_type" in df.columns:
            order_types = df["order_type"].astype(str).str.lower()
            pm_count = order_types.str.contains("pm02|preventive|planned|scheduled", na=False).sum()
            cm_count = order_types.str.contains("pm01|breakdown|corrective|emergency|unplanned", na=False).sum()
            total_typed = pm_count + cm_count
            if total_typed > 0:
                pm_ratio = pm_count / total_typed * 100
                if pm_ratio >= 60:
                    result["status"] = "pass"
                    result["finding"] = f"PM ratio at {pm_ratio:.0f}% ({pm_count} planned vs {cm_count} unplanned)"
                elif pm_ratio >= 40:
                    result["status"] = "warning"
                    result["finding"] = f"PM ratio at {pm_ratio:.0f}% - below best practice target of 80%"
                    result["risk"] = "medium"
                else:
                    result["status"] = "fail"
                    result["finding"] = f"PM ratio at only {pm_ratio:.0f}% - reactive maintenance dominates"
                    result["risk"] = "high"
            else:
                result["status"] = "warning"
                result["finding"] = "Cannot distinguish planned vs unplanned work from order type coding"
                result["risk"] = "medium"
        else:
            result["status"] = "fail"
            result["finding"] = "No order type classification - cannot measure PM compliance"
            result["risk"] = "high"
    
    # Root Cause / Corrective Action
    elif "Root Cause" in check_name or "Corrective" in check_name or "CAPA" in check_name or "Deviation" in check_name:
        if "cause_code" in df.columns:
            cause_filled = df["cause_code"].astype(str).str.strip().replace("", np.nan).notna().sum()
            cause_pct = cause_filled / len(df) * 100
            if cause_pct >= 80:
                result["status"] = "pass"
                result["finding"] = f"Root cause documented on {cause_pct:.0f}% of records"
            elif cause_pct >= 50:
                result["status"] = "warning"
                result["finding"] = f"Root cause only documented on {cause_pct:.0f}% of records - investigation gaps"
                result["risk"] = "medium"
            else:
                result["status"] = "fail"
                result["finding"] = f"Root cause documented on only {cause_pct:.0f}% - major CAPA/investigation gap"
                result["risk"] = "high"
        else:
            result["status"] = "fail"
            result["finding"] = "No root cause field found - cannot demonstrate systematic investigation"
            result["risk"] = "critical"
    
    # Continuous Improvement
    elif "Improvement" in check_name or "Trend" in check_name:
        if "created_date" in df.columns:
            try:
                dates = pd.to_datetime(df["created_date"], errors="coerce")
                date_range = (dates.max() - dates.min()).days
                if date_range >= 180:
                    result["status"] = "pass"
                    result["finding"] = f"Data spans {date_range} days - sufficient for trend analysis"
                else:
                    result["status"] = "warning"
                    result["finding"] = f"Data only spans {date_range} days - need 6+ months for meaningful trends"
                    result["risk"] = "low"
            except:
                result["status"] = "warning"
                result["finding"] = "Date parsing issues prevent trend analysis"
                result["risk"] = "medium"
        else:
            result["status"] = "fail"
            result["finding"] = "No date field - cannot demonstrate continuous improvement"
            result["risk"] = "medium"
    
    # Default for unmatched checks
    elif result["status"] == "unknown":
        result["status"] = "info"
        result["finding"] = "Manual review recommended for this compliance requirement"
        result["risk"] = "medium"
    
    return result


def _generate_remediation_actions(results):
    """Generate prioritized remediation actions from compliance gaps."""
    actions = []
    
    # Sort critical gaps by severity
    for gap in sorted(results["critical_gaps"], key=lambda x: x.get("severity", "minor") == "critical", reverse=True):
        priority = "HIGH" if gap["severity"] == "critical" else "MEDIUM"
        actions.append({
            "priority": priority,
            "framework": gap["framework"],
            "action": f"Improve {gap['field']} data entry to {90 if priority == 'HIGH' else 80}%+ completeness",
            "current": f"{gap['completeness']}%",
            "target": "90%+" if priority == "HIGH" else "80%+",
            "reason": gap["reason"],
            "effort": "Process change" if gap["completeness"] > 50 else "System configuration + training",
        })
    
    # Add framework-specific actions
    for fw in results["frameworks_checked"]:
        for check in fw["check_results"]:
            if check["status"] == "fail":
                actions.append({
                    "priority": "HIGH" if check["risk"] in ["high", "critical"] else "MEDIUM",
                    "framework": fw["name"],
                    "action": f"Address: {check['name']}",
                    "current": check["finding"],
                    "target": "Full compliance",
                    "reason": check["description"],
                    "effort": "Process + system review",
                })
    
    # Deduplicate and limit
    seen = set()
    unique_actions = []
    for action in actions:
        key = action["action"]
        if key not in seen:
            seen.add(key)
            unique_actions.append(action)
    
    return unique_actions[:15]  # Top 15 most important


def generate_compliance_summary(results):
    """Generate a human-readable compliance summary."""
    score = results["overall_compliance_score"]
    
    if score >= 85:
        risk_label = "LOW RISK"
        summary = "Your maintenance data substantially meets regulatory requirements. Minor gaps exist but are unlikely to trigger audit findings."
    elif score >= 65:
        risk_label = "MODERATE RISK"
        summary = "Your maintenance data has significant gaps that could result in audit observations. Targeted improvements needed before next inspection."
    else:
        risk_label = "HIGH RISK"
        summary = "Your maintenance data has critical compliance gaps. An auditor would likely issue major findings. Immediate remediation recommended."
    
    return {
        "score": score,
        "risk_label": risk_label,
        "summary": summary,
        "frameworks_count": len(results["frameworks_checked"]),
        "critical_gaps_count": len([g for g in results["critical_gaps"] if g["severity"] == "critical"]),
        "total_gaps_count": len(results["critical_gaps"]),
        "actions_count": len(results["remediation_actions"]),
    }


# ============================================================
# STANDALONE TEST
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("MaintSignal - Compliance Gap Detection Demo")
    print("=" * 60)
    
    # Create sample data with typical gaps
    np.random.seed(42)
    import random
    
    n = 500
    data = {
        "asset_id": [f"P-{random.randint(100,110)}" if random.random() > 0.15 else "" for _ in range(n)],
        "description": [random.choice(["pump leak", "bearing noise", "PM inspection", "motor trip", ""]) for _ in range(n)],
        "created_date": pd.date_range("2024-01-01", periods=n, freq="12h"),
        "completed_date": pd.date_range("2024-01-02", periods=n, freq="12h"),
        "failure_code": [random.choice(["MECH", "ELEC", "INST", "", "", ""]) for _ in range(n)],
        "cause_code": [random.choice(["WEAR", "OVERLOAD", "", "", "", ""]) for _ in range(n)],
        "order_type": [random.choice(["PM01", "PM01", "PM02", "PM02", "PM03"]) for _ in range(n)],
        "cost": [round(random.uniform(100, 5000), 2) if random.random() > 0.2 else np.nan for _ in range(n)],
        "labor_hours": [round(random.uniform(0.5, 16), 1) if random.random() > 0.1 else np.nan for _ in range(n)],
        "status": ["COMPLETED"] * n,
        "location": [f"PLANT1-AREA-{random.randint(1,5)}" if random.random() > 0.1 else "" for _ in range(n)],
    }
    df = pd.DataFrame(data)
    
    # Test pharmaceutical compliance
    print("\n--- Pharmaceutical (FDA 21 CFR Part 11) ---")
    results = analyze_compliance_gaps(df, industry="pharmaceutical")
    summary = generate_compliance_summary(results)
    
    print(f"Overall Score: {summary['score']}%")
    print(f"Risk Level: {summary['risk_label']}")
    print(f"Frameworks Checked: {summary['frameworks_count']}")
    print(f"Critical Gaps: {summary['critical_gaps_count']}")
    print(f"Total Gaps: {summary['total_gaps_count']}")
    print(f"\nSummary: {summary['summary']}")
    
    print("\n--- Framework Details ---")
    for fw in results["frameworks_checked"]:
        print(f"\n  {fw['name']}: {fw['score']}% ({fw['risk_level']} risk)")
        for field, score in fw["field_scores"].items():
            status_icon = "PASS" if score["status"] == "pass" else "WARN" if score["status"] == "warning" else "FAIL"
            print(f"    [{status_icon}] {score['label']}: {score['completeness']}%")
        for check in fw["check_results"]:
            status_icon = "PASS" if check["status"] == "pass" else "WARN" if check["status"] == "warning" else "FAIL"
            print(f"    [{status_icon}] {check['name']}: {check['finding']}")
    
    print("\n--- Top Remediation Actions ---")
    for i, action in enumerate(results["remediation_actions"][:5], 1):
        print(f"  {i}. [{action['priority']}] {action['action']}")
        print(f"     Current: {action['current']} | Target: {action['target']}")
        print(f"     Why: {action['reason']}")
