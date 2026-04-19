"""
MaintSignal - Knowledge Capture Module
Extracts tribal knowledge from historical work order descriptions and generates:
- Recommended failure code taxonomy (customized to the facility)
- Equipment-specific troubleshooting guides
- Common abbreviation dictionary from actual usage
- Technician quick-reference cards
- Job plan templates from repetitive work patterns

This module turns messy free-text into structured organizational knowledge.
"""

import pandas as pd
import numpy as np
import re
import json
from collections import Counter, defaultdict
from knowledge_base import GLOBAL_ABBREVIATIONS, get_failure_taxonomy


def extract_abbreviations(descriptions):
    """
    Detect abbreviations actually used in the data that aren't in the global dictionary.
    Returns discovered abbreviations with frequency and context.
    """
    # Pattern: 2-5 uppercase letters that appear multiple times
    abbrev_pattern = re.compile(r'\b([A-Z]{2,6})\b')
    
    abbrev_counts = Counter()
    abbrev_contexts = defaultdict(list)
    
    for desc in descriptions:
        if not isinstance(desc, str) or not desc.strip():
            continue
        
        matches = abbrev_pattern.findall(desc.upper())
        for match in matches:
            # Skip known words
            if match in {"THE", "AND", "FOR", "NOT", "WAS", "HAS", "HAD", "ARE", "ALL", 
                         "NEW", "OLD", "BAD", "OUT", "OFF", "RAN", "SET", "PUT", "CUT",
                         "HOT", "LOW", "HIGH", "OK", "PM", "AM", "NO", "NA", "NB"}:
                continue
            abbrev_counts[match] += 1
            if len(abbrev_contexts[match]) < 5:
                abbrev_contexts[match].append(desc.strip()[:100])
    
    # Filter to abbreviations used 3+ times
    discovered = []
    for abbrev, count in abbrev_counts.most_common(50):
        if count >= 3:
            known = abbrev in GLOBAL_ABBREVIATIONS
            expansion = GLOBAL_ABBREVIATIONS.get(abbrev, "Unknown - needs manual mapping")
            discovered.append({
                "abbreviation": abbrev,
                "frequency": count,
                "known": known,
                "expansion": expansion,
                "sample_contexts": abbrev_contexts[abbrev],
            })
    
    return discovered


def extract_equipment_patterns(df, desc_col="description", asset_col="asset_id"):
    """
    Identify recurring work patterns per equipment type.
    Groups similar descriptions to find repetitive maintenance tasks.
    """
    if desc_col not in df.columns or asset_col not in df.columns:
        return []
    
    # Clean data
    work_df = df[[asset_col, desc_col]].copy()
    work_df = work_df[work_df[asset_col].astype(str).str.strip() != ""]
    work_df = work_df[work_df[desc_col].astype(str).str.strip() != ""]
    work_df[desc_col] = work_df[desc_col].astype(str).str.lower().str.strip()
    
    # Get equipment prefix groups (P- = pumps, C- = conveyors, etc.)
    work_df["_equip_type"] = work_df[asset_col].astype(str).str.extract(r'^([A-Z]+-?)', expand=False).fillna("OTHER")
    
    patterns = []
    
    for equip_type in work_df["_equip_type"].unique():
        type_df = work_df[work_df["_equip_type"] == equip_type]
        desc_counts = type_df[desc_col].value_counts()
        
        # Find descriptions that repeat 3+ times
        repeating = desc_counts[desc_counts >= 3]
        
        if len(repeating) > 0:
            total_for_type = len(type_df)
            pattern = {
                "equipment_type": equip_type,
                "total_work_orders": total_for_type,
                "unique_descriptions": len(desc_counts),
                "repeating_descriptions": len(repeating),
                "top_tasks": [],
            }
            
            for desc, count in repeating.head(10).items():
                pct = round(count / total_for_type * 100, 1)
                pattern["top_tasks"].append({
                    "description": desc,
                    "count": int(count),
                    "percentage": pct,
                })
            
            patterns.append(pattern)
    
    patterns.sort(key=lambda x: x["total_work_orders"], reverse=True)
    return patterns


def generate_failure_code_library(df, industry="general_manufacturing", desc_col="description", 
                                   failure_col="failure_code", norm_results=None):
    """
    Generate a recommended failure code taxonomy based on actual data patterns.
    
    This is the core knowledge capture feature - it reads all historical descriptions
    and creates a standardized, simplified failure code set that matches how work
    actually happens at this specific facility.
    """
    taxonomy = get_failure_taxonomy(industry)
    
    # Count existing failure codes
    existing_codes = {}
    if failure_col in df.columns:
        fc = df[failure_col].astype(str).str.strip().replace("", np.nan).dropna()
        existing_codes = fc.value_counts().to_dict()
    
    # Get AI-normalized categories if available
    ai_categories = {}
    if norm_results is not None and isinstance(norm_results, pd.DataFrame) and "category" in norm_results.columns:
        ai_categories = norm_results["category"].value_counts().to_dict()
    
    # Analyze descriptions for common themes
    descriptions = df[desc_col].astype(str).str.lower().tolist() if desc_col in df.columns else []
    
    # Theme detection keywords
    themes = {
        "Seal Failure": ["seal", "leaking", "leak", "packing", "o-ring"],
        "Bearing Failure": ["bearing", "brng", "brg", "seized", "grinding"],
        "Motor Failure": ["motor", "mtr", "winding", "overheating", "overload", "burnt", "rewound"],
        "Pump Failure": ["pump", "pmp", "cavitation", "impeller", "suction"],
        "Valve Failure": ["valve", "vlv", "actuator", "stuck", "stem"],
        "Electrical Fault": ["electrical", "circuit", "breaker", "fuse", "short", "wiring", "ckt"],
        "Instrumentation": ["transmitter", "xmtr", "sensor", "calibration", "plc", "dcs"],
        "Lubrication": ["lubrication", "lube", "grease", "oil", "lub"],
        "Alignment": ["alignment", "misalign", "coupling", "vibration"],
        "Corrosion": ["corrosion", "corroded", "rust", "erosion", "pitting"],
        "Belt/Chain": ["belt", "chain", "tension", "tracking", "sprocket"],
        "Hydraulic": ["hydraulic", "hyd", "cylinder", "hose", "fitting"],
        "Pneumatic": ["pneumatic", "air", "compressor", "regulator", "solenoid"],
        "Structural": ["structural", "crack", "weld", "frame", "support", "foundation"],
        "Preventive Maintenance": ["pm", "inspection", "routine", "preventive", "scheduled", "annual"],
        "Cleaning": ["clean", "flush", "wash", "sanit", "decontam"],
    }
    
    theme_counts = {}
    for theme, keywords in themes.items():
        count = sum(1 for d in descriptions if any(kw in d for kw in keywords))
        if count > 0:
            theme_counts[theme] = count
    
    # Build recommended code library
    recommended_codes = []
    code_num = 1
    
    for theme, count in sorted(theme_counts.items(), key=lambda x: x[1], reverse=True):
        if count >= 5 or (count >= 2 and theme in (ai_categories or {})):
            pct = round(count / len(descriptions) * 100, 1) if descriptions else 0
            
            # Generate a short code
            code_prefix = {
                "Seal Failure": "MECH-SEAL",
                "Bearing Failure": "MECH-BRG",
                "Motor Failure": "ELEC-MTR",
                "Pump Failure": "MECH-PMP",
                "Valve Failure": "MECH-VLV",
                "Electrical Fault": "ELEC-GEN",
                "Instrumentation": "INST-GEN",
                "Lubrication": "MECH-LUB",
                "Alignment": "MECH-ALN",
                "Corrosion": "MECH-COR",
                "Belt/Chain": "MECH-BLT",
                "Hydraulic": "MECH-HYD",
                "Pneumatic": "MECH-PNE",
                "Structural": "MECH-STR",
                "Preventive Maintenance": "PM-GEN",
                "Cleaning": "PM-CLN",
            }.get(theme, f"GEN-{code_num:02d}")
            
            recommended_codes.append({
                "code": code_prefix,
                "category": theme,
                "description": f"{theme} - based on {count} historical work orders",
                "frequency": count,
                "percentage": pct,
                "in_taxonomy": theme in taxonomy,
                "keywords": themes.get(theme, []),
            })
            code_num += 1
    
    # Add "Other" category
    categorized = sum(c["frequency"] for c in recommended_codes)
    uncategorized = len(descriptions) - categorized
    if uncategorized > 0:
        recommended_codes.append({
            "code": "GEN-OTH",
            "category": "Other / Unclassified",
            "description": f"Work orders not matching any standard category ({uncategorized} records)",
            "frequency": uncategorized,
            "percentage": round(uncategorized / len(descriptions) * 100, 1) if descriptions else 0,
            "in_taxonomy": False,
            "keywords": [],
        })
    
    return {
        "total_descriptions_analyzed": len(descriptions),
        "recommended_codes": recommended_codes,
        "total_codes": len(recommended_codes),
        "existing_codes": existing_codes,
        "coverage": round(categorized / len(descriptions) * 100, 1) if descriptions else 0,
        "recommendation": _generate_taxonomy_recommendation(recommended_codes, existing_codes, descriptions),
    }


def _generate_taxonomy_recommendation(recommended_codes, existing_codes, descriptions):
    """Generate a human-readable recommendation about the failure code taxonomy."""
    num_recommended = len(recommended_codes)
    num_existing = len(existing_codes)
    
    if num_existing == 0:
        return (f"No existing failure code taxonomy detected. We recommend implementing "
                f"a {num_recommended}-code standardized library based on your actual failure patterns. "
                f"This will immediately enable failure trending and root cause analysis.")
    elif num_existing > 50:
        return (f"Your current taxonomy has {num_existing} codes, which is too granular for consistent use. "
                f"Technicians skip codes when there are too many options. We recommend simplifying to "
                f"{min(num_recommended, 20)} codes based on actual usage patterns.")
    elif num_existing < 5:
        return (f"Your current taxonomy has only {num_existing} codes, which is too broad for meaningful analysis. "
                f"We recommend expanding to {num_recommended} codes to capture the failure modes "
                f"actually occurring in your facility.")
    else:
        return (f"Your current {num_existing}-code taxonomy partially covers your failure patterns. "
                f"Based on analysis of {len(descriptions)} work orders, we recommend a revised "
                f"{num_recommended}-code library aligned to your actual equipment and failure modes.")


def generate_quick_reference_card(failure_library, abbreviations):
    """
    Generate a technician quick-reference card combining:
    - Simplified failure codes with descriptions
    - Common abbreviation expansions
    - Data entry reminders
    """
    card = {
        "title": "Technician Quick-Reference Card",
        "subtitle": "Use these codes and descriptions when closing work orders",
        "failure_codes": [],
        "abbreviations": [],
        "reminders": [
            "Always select an equipment ID before closing the work order",
            "Choose the failure code that best matches what you found - not what you did",
            "If none of the codes fit, use 'Other' and write a detailed description",
            "Include the specific component that failed in your description",
            "Record actual time spent, not estimated time",
        ],
    }
    
    # Top failure codes
    for code in failure_library.get("recommended_codes", [])[:15]:
        if code["category"] != "Other / Unclassified":
            card["failure_codes"].append({
                "code": code["code"],
                "name": code["category"],
                "when_to_use": f"Use when: {', '.join(code['keywords'][:4])}",
            })
    
    # Top abbreviations
    for abbrev in abbreviations[:20]:
        if abbrev.get("known"):
            card["abbreviations"].append({
                "abbrev": abbrev["abbreviation"],
                "meaning": abbrev["expansion"],
                "frequency": abbrev["frequency"],
            })
    
    return card


def analyze_knowledge_gaps(df, desc_col="description"):
    """
    Identify areas where maintenance knowledge is being lost:
    - Vague descriptions that don't capture useful information
    - Single-word or very short descriptions
    - Descriptions that can't be classified
    - Equipment with no failure history (shadow maintenance)
    """
    gaps = {
        "vague_descriptions": [],
        "too_short": 0,
        "generic_actions": 0,
        "no_root_cause": 0,
        "total_analyzed": 0,
    }
    
    if desc_col not in df.columns:
        return gaps
    
    descriptions = df[desc_col].astype(str).tolist()
    gaps["total_analyzed"] = len(descriptions)
    
    vague_patterns = [
        "fixed it", "repaired", "done", "completed", "ok", "working", 
        "good", "fine", "no issue", "resolved", "taken care of",
        "same as before", "as discussed", "per request", "see notes",
    ]
    
    for desc in descriptions:
        desc_lower = desc.lower().strip()
        
        # Too short (under 10 characters)
        if len(desc_lower) < 10:
            gaps["too_short"] += 1
        
        # Vague / generic
        if any(v in desc_lower for v in vague_patterns):
            gaps["generic_actions"] += 1
            if len(gaps["vague_descriptions"]) < 20:
                gaps["vague_descriptions"].append(desc.strip()[:100])
        
        # No root cause indication (just action, no "because" or "due to" or cause)
        cause_indicators = ["because", "due to", "caused by", "found", "discovered", 
                           "root cause", "failure mode", "worn", "broken", "cracked",
                           "corroded", "leaked", "seized", "tripped"]
        if not any(ci in desc_lower for ci in cause_indicators):
            gaps["no_root_cause"] += 1
    
    gaps["vague_percentage"] = round(gaps["generic_actions"] / max(len(descriptions), 1) * 100, 1)
    gaps["short_percentage"] = round(gaps["too_short"] / max(len(descriptions), 1) * 100, 1)
    gaps["no_cause_percentage"] = round(gaps["no_root_cause"] / max(len(descriptions), 1) * 100, 1)
    
    return gaps


# ============================================================
# STANDALONE TEST
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("MaintSignal - Knowledge Capture Demo")
    print("=" * 60)
    
    import random
    np.random.seed(42)
    
    # Generate realistic data
    descriptions = [
        "pump leaking from seal area", "replaced mech seal on pump", "seal failure replaced seal",
        "pump p101 leaking bad need new seal", "bearing noise on conveyor", "replaced bearing on main conveyor",
        "motor overheating", "motor tripped on overload", "valve stuck open", "replaced valve actuator",
        "PM inspection all ok", "routine maintenance completed", "lubrication and inspection",
        "fixed it", "done", "repaired pump", "replaced seal", "BRG noise conv DE side",
        "MTR tripped on O/L", "CKT BKR tripped MCC reset", "XMTR reading erratic recal",
        "belt tracking off adjusted", "cleaned and inspected", "general maintenance",
    ] * 50
    
    random.shuffle(descriptions)
    
    n = len(descriptions)
    df = pd.DataFrame({
        "description": descriptions[:n],
        "asset_id": [random.choice(["P-101", "P-102", "C-301", "M-105", "V-501", "K-201"]) for _ in range(n)],
        "failure_code": [random.choice(["MECH", "ELEC", "", "", ""]) for _ in range(n)],
    })
    
    # Test abbreviation extraction
    print("\n--- Abbreviation Discovery ---")
    abbrevs = extract_abbreviations(df["description"].tolist())
    for a in abbrevs[:10]:
        status = "Known" if a["known"] else "NEW"
        print(f"  [{status}] {a['abbreviation']} = {a['expansion']} (used {a['frequency']}x)")
    
    # Test equipment patterns
    print("\n--- Equipment Work Patterns ---")
    patterns = extract_equipment_patterns(df)
    for p in patterns[:3]:
        print(f"\n  Equipment Type: {p['equipment_type']}")
        print(f"  Total WOs: {p['total_work_orders']}, Unique: {p['unique_descriptions']}")
        for task in p["top_tasks"][:3]:
            print(f"    - '{task['description']}' x{task['count']} ({task['percentage']}%)")
    
    # Test failure code library
    print("\n--- Recommended Failure Code Library ---")
    library = generate_failure_code_library(df, industry="general_manufacturing")
    print(f"  Codes recommended: {library['total_codes']}")
    print(f"  Coverage: {library['coverage']}%")
    print(f"  Recommendation: {library['recommendation']}")
    for code in library["recommended_codes"][:8]:
        print(f"    {code['code']}: {code['category']} ({code['frequency']} WOs, {code['percentage']}%)")
    
    # Test knowledge gaps
    print("\n--- Knowledge Gaps ---")
    gaps = analyze_knowledge_gaps(df)
    print(f"  Vague descriptions: {gaps['generic_actions']} ({gaps['vague_percentage']}%)")
    print(f"  Too short (<10 chars): {gaps['too_short']} ({gaps['short_percentage']}%)")
    print(f"  No root cause: {gaps['no_root_cause']} ({gaps['no_cause_percentage']}%)")
    
    # Test quick reference card
    print("\n--- Quick Reference Card ---")
    card = generate_quick_reference_card(library, abbrevs)
    print(f"  Failure codes: {len(card['failure_codes'])}")
    print(f"  Abbreviations: {len(card['abbreviations'])}")
    print(f"  Reminders: {len(card['reminders'])}")
