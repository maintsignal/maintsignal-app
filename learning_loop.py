"""
MaintSignal - Learning Loop Module
Stores every AI classification result and client correction.
Uses accumulated knowledge to improve future analyses.

How it works:
1. After each analysis, results are saved to a local JSON database
2. When a client corrects a classification, the correction is stored
3. Future analyses load corrections as few-shot examples for the AI
4. Over time, the system gets more accurate for each industry/client

Storage: Local JSON files in ~/.maintsignal/learning/
"""

import json
import os
import hashlib
from datetime import datetime
from collections import Counter, defaultdict


# Storage directory
LEARNING_DIR = os.path.expanduser("~/.maintsignal/learning")


def _ensure_dir():
    """Create learning directory if it doesn't exist."""
    os.makedirs(LEARNING_DIR, exist_ok=True)


def _get_db_path(db_name="classifications"):
    """Get path to a learning database file."""
    _ensure_dir()
    return os.path.join(LEARNING_DIR, f"{db_name}.json")


def _load_db(db_name="classifications"):
    """Load a learning database."""
    path = _get_db_path(db_name)
    if os.path.exists(path):
        try:
            with open(path, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {"entries": [], "corrections": [], "stats": {}}
    return {"entries": [], "corrections": [], "stats": {}}


def _save_db(data, db_name="classifications"):
    """Save a learning database."""
    path = _get_db_path(db_name)
    with open(path, "w") as f:
        json.dump(data, f, indent=2, default=str)


def save_classification_results(results_df, industry, client_name="", source_file=""):
    """
    Save classification results from an analysis run.
    
    Args:
        results_df: DataFrame with columns: original, interpretation, category, component, confidence, method
        industry: Industry key
        client_name: Optional client identifier
        source_file: Original filename
    """
    db = _load_db()
    
    run_id = hashlib.md5(f"{datetime.now().isoformat()}{client_name}".encode()).hexdigest()[:12]
    
    run_entry = {
        "run_id": run_id,
        "timestamp": datetime.now().isoformat(),
        "industry": industry,
        "client_name": client_name,
        "source_file": source_file,
        "total_classified": len(results_df),
        "categories_found": int(results_df["category"].nunique()) if "category" in results_df.columns else 0,
        "confidence_dist": {},
        "category_dist": {},
    }
    
    # Store confidence distribution
    if "confidence" in results_df.columns:
        conf_counts = results_df["confidence"].value_counts().to_dict()
        run_entry["confidence_dist"] = {str(k): int(v) for k, v in conf_counts.items()}
    
    # Store category distribution
    if "category" in results_df.columns:
        cat_counts = results_df["category"].value_counts().head(20).to_dict()
        run_entry["category_dist"] = {str(k): int(v) for k, v in cat_counts.items()}
    
    # Store sample classifications (not all — just unique patterns)
    samples = []
    if "original" in results_df.columns and "category" in results_df.columns:
        # Get unique original descriptions and their classifications
        unique = results_df.drop_duplicates(subset=["original"]).head(200)
        for _, row in unique.iterrows():
            samples.append({
                "original": str(row.get("original", ""))[:100],
                "category": str(row.get("category", "Unknown")),
                "component": str(row.get("component", "unknown")),
                "confidence": str(row.get("confidence", "low")),
                "method": str(row.get("method", "unknown")),
            })
    
    run_entry["samples"] = samples
    db["entries"].append(run_entry)
    
    # Update global stats
    db["stats"]["total_runs"] = len(db["entries"])
    db["stats"]["total_classified"] = sum(e.get("total_classified", 0) for e in db["entries"])
    db["stats"]["last_run"] = datetime.now().isoformat()
    db["stats"]["industries_seen"] = list(set(e.get("industry", "") for e in db["entries"]))
    
    _save_db(db)
    return run_id


def save_correction(original_text, wrong_category, correct_category, correct_component="",
                     industry="", client_name="", notes=""):
    """
    Save a client correction to a classification.
    These corrections become few-shot examples for future analyses.
    
    Args:
        original_text: The original technician description
        wrong_category: What the AI classified it as
        correct_category: What it should have been
        correct_component: The correct component
        industry: Industry context
        client_name: Who made the correction
        notes: Additional context
    """
    db = _load_db()
    
    correction = {
        "id": hashlib.md5(f"{original_text}{datetime.now().isoformat()}".encode()).hexdigest()[:10],
        "timestamp": datetime.now().isoformat(),
        "original_text": str(original_text)[:150],
        "wrong_category": wrong_category,
        "correct_category": correct_category,
        "correct_component": correct_component,
        "industry": industry,
        "client_name": client_name,
        "notes": notes,
    }
    
    db["corrections"].append(correction)
    _save_db(db)
    return correction["id"]


def get_corrections_for_industry(industry):
    """
    Get all corrections for a specific industry.
    Returns list of corrections that can be used as few-shot examples.
    """
    db = _load_db()
    
    corrections = [c for c in db.get("corrections", [])
                   if c.get("industry", "") == industry or c.get("industry", "") == ""]
    
    return corrections


def get_few_shot_examples_from_corrections(industry, max_examples=10):
    """
    Convert stored corrections into few-shot examples for the LLM prompt.
    These teach the AI from past mistakes.
    """
    corrections = get_corrections_for_industry(industry)
    
    if not corrections:
        return []
    
    # Deduplicate by original text
    seen = set()
    unique = []
    for c in corrections:
        text = c["original_text"].lower().strip()
        if text not in seen:
            seen.add(text)
            unique.append(c)
    
    # Return as few-shot format
    examples = []
    for c in unique[:max_examples]:
        examples.append({
            "original": c["original_text"],
            "category": c["correct_category"],
            "component": c.get("correct_component", "unknown"),
            "confidence": "high",
            "source": "client_correction",
        })
    
    return examples


def get_learning_stats():
    """Get overall learning statistics."""
    db = _load_db()
    
    stats = db.get("stats", {})
    stats["total_corrections"] = len(db.get("corrections", []))
    stats["total_runs"] = len(db.get("entries", []))
    
    # Corrections by industry
    industry_corrections = Counter()
    for c in db.get("corrections", []):
        industry_corrections[c.get("industry", "unknown")] += 1
    stats["corrections_by_industry"] = dict(industry_corrections)
    
    # Most common wrong classifications
    wrong_cats = Counter()
    for c in db.get("corrections", []):
        wrong_cats[f"{c.get('wrong_category', '?')} -> {c.get('correct_category', '?')}"] += 1
    stats["common_mistakes"] = dict(wrong_cats.most_common(10))
    
    # Accumulated knowledge
    all_samples = []
    for entry in db.get("entries", []):
        all_samples.extend(entry.get("samples", []))
    stats["total_unique_patterns"] = len(set(s.get("original", "") for s in all_samples))
    
    return stats


def get_industry_knowledge(industry, top_n=50):
    """
    Get accumulated knowledge for an industry.
    Returns the most common description-to-category mappings learned from past analyses.
    """
    db = _load_db()
    
    # Collect all samples from this industry
    mappings = defaultdict(Counter)
    
    for entry in db.get("entries", []):
        if entry.get("industry", "") == industry:
            for sample in entry.get("samples", []):
                desc = sample.get("original", "").lower().strip()
                cat = sample.get("category", "Unknown")
                if desc and cat != "Unknown":
                    mappings[desc][cat] += 1
    
    # Also include corrections (override)
    for c in db.get("corrections", []):
        if c.get("industry", "") == industry:
            desc = c["original_text"].lower().strip()
            cat = c["correct_category"]
            mappings[desc][cat] += 100  # Corrections have highest weight
    
    # Build knowledge base
    knowledge = []
    for desc, cat_counts in mappings.items():
        best_cat = cat_counts.most_common(1)[0]
        knowledge.append({
            "description": desc,
            "category": best_cat[0],
            "confidence_count": best_cat[1],
        })
    
    knowledge.sort(key=lambda x: x["confidence_count"], reverse=True)
    return knowledge[:top_n]


def export_learning_data():
    """Export all learning data as a dictionary (for backup or transfer)."""
    return _load_db()


def import_learning_data(data):
    """Import learning data from a backup."""
    _save_db(data)


# ============================================================
# STANDALONE TEST
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("MaintSignal - Learning Loop Demo")
    print("=" * 60)
    
    import pandas as pd
    
    # Simulate saving results from an analysis
    sample_results = pd.DataFrame({
        "original": ["pump seal leak", "bearing noise", "motor trip", "PM inspection", "fixed it"] * 20,
        "interpretation": ["pump seal leaking", "bearing noise detected", "motor tripped", "PM done", "unknown"] * 20,
        "category": ["Seal Failure", "Bearing Failure", "Motor Failure", "Preventive Maintenance", "Unknown"] * 20,
        "component": ["seal", "bearing", "motor", "N/A", "unknown"] * 20,
        "confidence": ["high", "high", "high", "high", "low"] * 20,
        "method": ["keyword", "keyword", "keyword", "keyword", "keyword"] * 20,
    })
    
    # Save results
    run_id = save_classification_results(sample_results, industry="pharmaceutical", client_name="Test Client")
    print(f"\nSaved analysis run: {run_id}")
    
    # Save some corrections
    save_correction(
        original_text="replaced internals on feed pump",
        wrong_category="Unknown",
        correct_category="Pump Failure",
        correct_component="pump internals",
        industry="pharmaceutical",
        client_name="Test Client",
        notes="Common pump repair pattern"
    )
    
    save_correction(
        original_text="CIP valve stuck closed",
        wrong_category="Unknown",
        correct_category="Valve Failure",
        correct_component="CIP valve",
        industry="pharmaceutical",
        client_name="Test Client"
    )
    
    print("Saved 2 corrections")
    
    # Get learning stats
    stats = get_learning_stats()
    print(f"\n--- Learning Stats ---")
    print(f"  Total runs: {stats['total_runs']}")
    print(f"  Total classified: {stats.get('total_classified', 0)}")
    print(f"  Total corrections: {stats['total_corrections']}")
    print(f"  Unique patterns: {stats['total_unique_patterns']}")
    
    # Get few-shot examples from corrections
    examples = get_few_shot_examples_from_corrections("pharmaceutical")
    print(f"\n--- Few-Shot Examples from Corrections ({len(examples)}) ---")
    for ex in examples:
        print(f"  '{ex['original']}' -> {ex['category']} ({ex['component']})")
    
    # Get industry knowledge
    knowledge = get_industry_knowledge("pharmaceutical")
    print(f"\n--- Accumulated Knowledge ({len(knowledge)} patterns) ---")
    for k in knowledge[:5]:
        print(f"  '{k['description']}' -> {k['category']} (seen {k['confidence_count']}x)")
    
    print(f"\nLearning data stored at: {LEARNING_DIR}")
