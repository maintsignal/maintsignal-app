"""
MaintSignal — Smart LLM Normalization Engine
Handles abbreviations, industry jargon, and multi-language technician notes.

Three modes:
1. OFFLINE — Fast keyword matching using knowledge base (free, no API)
2. ONLINE  — Claude API with industry-specific prompting (best quality)
3. HYBRID  — Keyword first, LLM for uncertain cases (cost-optimized)

Usage:
    from smart_normalizer import SmartNormalizer
    
    # Offline (free, good for demos)
    norm = SmartNormalizer(mode="offline", industry="oil_and_gas")
    results = norm.normalize(df["description"].tolist())
    
    # Online (best quality, requires API key)
    norm = SmartNormalizer(mode="online", industry="pharmaceutical", api_key="sk-ant-xxx")
    results = norm.normalize(df["description"].tolist())
    
    # Hybrid (cost-optimized)
    norm = SmartNormalizer(mode="hybrid", industry="food_and_beverage", api_key="sk-ant-xxx")
    results = norm.normalize(df["description"].tolist())
"""

import re
import json
import time
import pandas as pd
from typing import Optional
from knowledge_base import (
    GLOBAL_ABBREVIATIONS,
    INDUSTRY_TAXONOMIES,
    get_all_abbreviations,
    get_failure_taxonomy,
    build_normalization_prompt,
)


class NormalizationResult:
    """Single normalized description result."""
    def __init__(self, original="", interpretation="", category="Unknown",
                 component="unknown", confidence="low", method=""):
        self.original = original
        self.interpretation = interpretation  # Expanded plain-English version
        self.category = category
        self.component = component
        self.confidence = confidence
        self.method = method  # "keyword", "llm", or "hybrid"


class SmartNormalizer:
    """
    Multi-mode failure description normalizer.
    Combines industry knowledge base with LLM intelligence.
    """

    def __init__(self, mode="offline", industry=None, api_key=None,
                 client_abbreviations=None):
        """
        Args:
            mode: "offline" (keyword), "online" (LLM), or "hybrid" (both)
            industry: Industry key from knowledge_base.INDUSTRY_TAXONOMIES
            api_key: Anthropic API key (required for online/hybrid mode)
            client_abbreviations: Dict of client-specific abbreviations
        """
        self.mode = mode
        self.industry = industry or "general_manufacturing"
        self.api_key = api_key
        self.client_abbreviations = client_abbreviations or {}

        # Load knowledge base
        self.abbreviations = get_all_abbreviations(industry)
        if client_abbreviations:
            self.abbreviations.update(client_abbreviations)

        self.taxonomy = get_failure_taxonomy(industry)
        self.batch_size = 40  # Descriptions per LLM call

        # Build keyword matcher from taxonomy
        self.keyword_rules = self._build_keyword_rules()

        # Setup LLM client if needed
        self.llm_client = None
        if mode in ["online", "hybrid"] and api_key:
            try:
                import anthropic
                self.llm_client = anthropic.Anthropic(api_key=api_key)
            except ImportError:
                print("WARNING: anthropic package not installed. Falling back to offline mode.")
                self.mode = "offline"

    def _build_keyword_rules(self):
        """
        Build keyword matching rules from the taxonomy.
        Each category gets a set of weighted keywords.
        """
        rules = {}

        # Universal keyword patterns (work across all industries)
        base_patterns = {
            "Seal Failure": {
                "primary": ["seal", "packing", "gasket", "o-ring", "oring"],
                "secondary": ["leak", "leaking", "drip", "weep"],
                "components": ["mechanical seal", "shaft seal", "lip seal"],
            },
            "Bearing Failure": {
                "primary": ["bearing", "brg", "brng"],
                "secondary": ["grinding", "seized", "hot bearing", "metal shavings",
                              "bearing temp", "bearing noise"],
                "components": ["DE bearing", "NDE bearing", "thrust bearing",
                               "journal bearing", "roller bearing"],
            },
            "Motor / Drive Failure": {
                "primary": ["motor", "mtr", "mot", "vfd", "drive"],
                "secondary": ["overheating", "overheat", "overload", "tripped",
                              "high amps", "vibration", "winding", "rewound",
                              "burnt", "burned"],
                "components": ["motor", "drive motor", "servo", "gearbox"],
            },
            "Valve Failure": {
                "primary": ["valve", "vlv", "actuator", "positioner"],
                "secondary": ["stuck", "not responding", "erratic", "passing",
                              "leaking thru", "cavitation", "trim"],
                "components": ["control valve", "safety valve", "isolation valve",
                               "globe valve", "butterfly valve", "ball valve"],
            },
            "Electrical Fault": {
                "primary": ["breaker", "contactor", "wiring", "electrical"],
                "secondary": ["short", "ground fault", "tripped", "loose wire",
                              "power supply", "cable", "fuse"],
                "components": ["breaker", "contactor", "relay", "power supply",
                               "cable", "junction box"],
            },
            "Instrumentation Fault": {
                "primary": ["sensor", "transmitter", "xmtr", "xmitter", "plc",
                            "instrument"],
                "secondary": ["reading", "erratic", "drift", "calibrat", "fault",
                              "out of range", "signal"],
                "components": ["sensor", "transmitter", "thermocouple", "RTD",
                               "level switch", "pressure gauge"],
            },
            "Corrosion / Erosion": {
                "primary": ["corrosion", "corroded", "rust", "erosion", "pitting"],
                "secondary": ["material loss", "thinning", "CUI", "coating"],
                "components": ["pipe", "vessel", "tank", "flange", "bolts"],
            },
            "Pump Failure": {
                "primary": ["pump", "pmp", "pp"],
                "secondary": ["cavitation", "impeller", "no flow", "low pressure",
                              "suction", "discharge"],
                "components": ["pump", "impeller", "casing", "volute"],
            },
            "Compressor Failure": {
                "primary": ["compressor", "comp", "compr"],
                "secondary": ["surge", "high discharge", "valve plate", "piston",
                              "unloader"],
                "components": ["compressor", "cylinder", "valve plate", "piston ring"],
            },
            "Conveyor / Belt Failure": {
                "primary": ["conveyor", "conv", "belt", "chain"],
                "secondary": ["tracking", "slip", "torn", "splice", "roller",
                              "idler", "tension"],
                "components": ["belt", "chain", "roller", "idler", "sprocket"],
            },
            "Lubrication Issue": {
                "primary": ["lubrication", "lube", "grease", "oil"],
                "secondary": ["dry", "contaminated", "low level", "oil analysis",
                              "oil sample"],
                "components": ["lube system", "grease fitting", "oil reservoir"],
            },
            "Preventive Maintenance": {
                "primary": ["PM", "inspection", "preventive", "routine", "scheduled"],
                "secondary": ["per schedule", "per plan", "task list", "all ok",
                              "no issues", "completed", "within spec", "normal",
                              "lubed", "cleaned", "greased", "torqued",
                              "oil sample", "vibration readings"],
                "components": [],
            },
            "Calibration": {
                "primary": ["calibrat", "calibration"],
                "secondary": ["verification", "as found", "as left", "adjustment"],
                "components": [],
            },
        }

        # Map base patterns to actual taxonomy categories
        for base_cat, patterns in base_patterns.items():
            # Find the closest matching taxonomy category
            matched_cat = None
            for tax_cat in self.taxonomy.keys():
                if base_cat.lower() in tax_cat.lower() or tax_cat.lower() in base_cat.lower():
                    matched_cat = tax_cat
                    break

            # Fallback: use first matching word
            if not matched_cat:
                for tax_cat in self.taxonomy.keys():
                    base_words = set(base_cat.lower().split())
                    tax_words = set(tax_cat.lower().split())
                    if base_words & tax_words:
                        matched_cat = tax_cat
                        break

            if matched_cat:
                rules[matched_cat] = patterns

        return rules

    def expand_abbreviations(self, text):
        """
        Expand known abbreviations in a text string.
        Smart enough to handle word boundaries and case variations.
        """
        if not text or not isinstance(text, str):
            return text

        expanded = text

        # Sort by length (longest first) to avoid partial matches
        sorted_abbrevs = sorted(
            self.abbreviations.items(),
            key=lambda x: len(x[0]),
            reverse=True
        )

        for abbrev, full in sorted_abbrevs:
            # Create pattern that matches whole words or slash-separated terms
            pattern = r'\b' + re.escape(abbrev) + r'\b'
            try:
                if re.search(pattern, expanded, re.IGNORECASE):
                    expanded = re.sub(pattern, full, expanded, flags=re.IGNORECASE)
            except re.error:
                continue

        return expanded

    def _keyword_classify(self, text):
        """
        Multi-signal keyword classification.
        Scores description against ALL categories and picks highest.
        Much smarter than single-keyword matching.
        """
        if not text or not isinstance(text, str):
            return NormalizationResult(
                original=text or "", interpretation="", category="Unknown",
                component="unknown", confidence="low", method="keyword"
            )

        expanded = self.expand_abbreviations(text)
        text_lower = text.lower().strip()
        exp_lower = expanded.lower().strip() if expanded else text_lower

        # Score against all categories using multi-signal matching
        scores = {}
        best_component = "unknown"

        for category, patterns in self.keyword_rules.items():
            score = 0.0
            matched_comp = "unknown"

            # Primary keywords = strong signal (3 points each)
            for kw in patterns.get("primary", []):
                if kw.lower() in exp_lower or kw.lower() in text_lower:
                    score += 3.0

            # Secondary keywords = supporting signal (1.5 points each)
            for kw in patterns.get("secondary", []):
                if kw.lower() in exp_lower or kw.lower() in text_lower:
                    score += 1.5

            # Component keywords = bonus signal (1 point each)
            for comp in patterns.get("components", []):
                if comp.lower() in exp_lower or comp.lower() in text_lower:
                    score += 1.0
                    matched_comp = comp

            if score > 0:
                scores[category] = {"score": score, "component": matched_comp}

        if not scores:
            return NormalizationResult(
                original=text, interpretation=expanded,
                category="Unknown", component="unknown",
                confidence="low", method="keyword"
            )

        # Pick highest scoring category
        best_cat = max(scores, key=lambda x: scores[x]["score"])
        best_score = scores[best_cat]["score"]
        best_component = scores[best_cat]["component"]

        # Determine confidence based on score and margin
        sorted_scores = sorted(scores.values(), key=lambda x: x["score"], reverse=True)
        if best_score >= 4.5:
            confidence = "high"
        elif best_score >= 3.0:
            if len(sorted_scores) >= 2 and sorted_scores[1]["score"] >= best_score * 0.7:
                confidence = "medium"
            else:
                confidence = "high"
        elif best_score >= 1.5:
            confidence = "medium"
        else:
            confidence = "low"

        return NormalizationResult(
            original=text, interpretation=expanded,
            category=best_cat, component=best_component,
            confidence=confidence, method="keyword"
        )

    def _keyword_classify_OLD_REMOVED(self, text):
        """
        Classify a single description using keyword rules.
        Returns NormalizationResult.
        """
        if not text or not isinstance(text, str) or text.strip() == "":
            return NormalizationResult(
                original=text, interpretation="(empty description)",
                category="Preventive Maintenance", component="unknown",
                confidence="low", method="keyword"
            )

        text_lower = text.lower().strip()
        expanded = self.expand_abbreviations(text)

        best_category = None
        best_score = 0
        best_component = "unknown"

        for category, patterns in self.keyword_rules.items():
            score = 0

            # Check primary keywords (high weight)
            for kw in patterns.get("primary", []):
                if kw.lower() in text_lower or kw.lower() in expanded.lower():
                    score += 10

            # Check secondary keywords (medium weight)
            for kw in patterns.get("secondary", []):
                if kw.lower() in text_lower or kw.lower() in expanded.lower():
                    score += 5

            # Check component keywords
            for comp in patterns.get("components", []):
                if comp.lower() in text_lower or comp.lower() in expanded.lower():
                    score += 3
                    best_component = comp

            if score > best_score:
                best_score = score
                best_category = category

        # Determine confidence
        if best_score >= 15:
            confidence = "high"
        elif best_score >= 8:
            confidence = "medium"
        elif best_score > 0:
            confidence = "low"
        else:
            best_category = "Unknown"
            confidence = "low"

        return NormalizationResult(
            original=text,
            interpretation=expanded,
            category=best_category or "Unknown",
            component=best_component,
            confidence=confidence,
            method="keyword"
        )

    def _llm_classify_batch(self, descriptions):
        """
        Classify a batch of descriptions using Claude API.
        Returns list of NormalizationResult.
        """
        if not self.llm_client:
            return [self._keyword_classify(d) for d in descriptions]

        prompt = build_normalization_prompt(
            descriptions,
            industry=self.industry,
            client_abbreviations=self.client_abbreviations
        )

        try:
            response = self.llm_client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=4000,
                temperature=0,
                messages=[{"role": "user", "content": prompt}]
            )

            text = response.content[0].text.strip()

            # Clean response
            if text.startswith("```"):
                text = text.split("\n", 1)[1]
            if text.endswith("```"):
                text = text.rsplit("```", 1)[0]
            text = text.strip()

            results_json = json.loads(text)

            results = []
            for item in results_json:
                # Validate category against taxonomy
                category = item.get("category", "Unknown")
                if category not in self.taxonomy and category != "Unknown":
                    # Find closest match
                    for tax_cat in self.taxonomy:
                        if category.lower() in tax_cat.lower():
                            category = tax_cat
                            break

                results.append(NormalizationResult(
                    original=item.get("original", ""),
                    interpretation=item.get("interpretation", ""),
                    category=category,
                    component=item.get("component", "unknown"),
                    confidence=item.get("confidence", "medium"),
                    method="llm"
                ))

            return results

        except json.JSONDecodeError as e:
            print(f"LLM JSON parse error: {e}")
            return [self._keyword_classify(d) for d in descriptions]

        except Exception as e:
            print(f"LLM API error: {e}")
            return [self._keyword_classify(d) for d in descriptions]

    def normalize(self, descriptions, progress_callback=None):
        """
        Normalize a list of descriptions.
        
        Args:
            descriptions: List of technician text descriptions
            progress_callback: Optional function(processed, total) for progress
            
        Returns:
            DataFrame with columns: original, interpretation, category,
                                    component, confidence, method
        """
        total = len(descriptions)
        all_results = []

        if self.mode == "offline":
            # Pure keyword matching — fast and free
            for i, desc in enumerate(descriptions):
                result = self._keyword_classify(desc)
                all_results.append(result)
                if progress_callback and (i + 1) % 100 == 0:
                    progress_callback(i + 1, total)

        elif self.mode == "online":
            # Pure LLM — best quality, higher cost
            for batch_start in range(0, total, self.batch_size):
                batch_end = min(batch_start + self.batch_size, total)
                batch = descriptions[batch_start:batch_end]
                batch_results = self._llm_classify_batch(batch)
                all_results.extend(batch_results)

                if progress_callback:
                    progress_callback(batch_end, total)
                if batch_end < total:
                    time.sleep(0.5)

        elif self.mode == "hybrid":
            # Keyword first, LLM for uncertain cases — cost-optimized
            uncertain = []
            uncertain_indices = []

            for i, desc in enumerate(descriptions):
                result = self._keyword_classify(desc)
                all_results.append(result)

                # If keyword matching is uncertain, queue for LLM
                if result.confidence == "low" and result.category != "Preventive Maintenance":
                    uncertain.append(desc)
                    uncertain_indices.append(i)

            # Process uncertain cases with LLM
            if uncertain and self.llm_client:
                print(f"  Keyword classified {total - len(uncertain)}/{total}. "
                      f"Sending {len(uncertain)} uncertain cases to LLM...")

                for batch_start in range(0, len(uncertain), self.batch_size):
                    batch_end = min(batch_start + self.batch_size, len(uncertain))
                    batch = uncertain[batch_start:batch_end]
                    batch_indices = uncertain_indices[batch_start:batch_end]
                    llm_results = self._llm_classify_batch(batch)

                    for idx, result in zip(batch_indices, llm_results):
                        result.method = "hybrid-llm"
                        all_results[idx] = result

                    if batch_end < len(uncertain):
                        time.sleep(0.5)

            if progress_callback:
                progress_callback(total, total)

        # Convert to DataFrame
        df = pd.DataFrame([
            {
                "original": r.original,
                "interpretation": r.interpretation,
                "category": r.category,
                "component": r.component,
                "confidence": r.confidence,
                "method": r.method,
            }
            for r in all_results
        ])

        return df

    def get_summary(self, results_df):
        """Get a summary of normalization results."""
        summary = {
            "total_processed": len(results_df),
            "categories_found": results_df["category"].nunique(),
            "high_confidence": (results_df["confidence"] == "high").sum(),
            "medium_confidence": (results_df["confidence"] == "medium").sum(),
            "low_confidence": (results_df["confidence"] == "low").sum(),
            "method_breakdown": results_df["method"].value_counts().to_dict(),
            "category_breakdown": results_df["category"].value_counts().to_dict(),
        }

        # Top components
        components = results_df[results_df["component"] != "unknown"]
        if not components.empty:
            summary["top_components"] = components["component"].value_counts().head(10).to_dict()

        return summary

    def learn_client_vocabulary(self, descriptions, corrections=None):
        """
        Learn client-specific abbreviations and patterns from their data.
        This improves accuracy over time for recurring clients.
        
        Args:
            descriptions: List of client descriptions (for pattern detection)
            corrections: Optional dict of {wrong_category: correct_category}
                        from client feedback on previous results
        """
        # Detect frequent abbreviations not in our dictionary
        all_words = " ".join(str(d) for d in descriptions if d).split()
        word_freq = {}
        for word in all_words:
            word_upper = word.upper().strip(".,;:!?")
            if (len(word_upper) <= 6 and
                word_upper == word.strip(".,;:!?") and  # Was already uppercase
                word_upper not in self.abbreviations and
                word_upper.isalpha()):
                word_freq[word_upper] = word_freq.get(word_upper, 0) + 1

        # Report potential new abbreviations
        potential_new = {
            word: count for word, count in word_freq.items()
            if count >= 5  # Appears at least 5 times
        }

        if potential_new:
            print(f"\n  Detected {len(potential_new)} potential client-specific abbreviations:")
            for word, count in sorted(potential_new.items(), key=lambda x: x[1], reverse=True)[:15]:
                print(f"    {word}: appears {count} times — meaning unknown")
            print("  Add these to client_abbreviations dict to improve accuracy.")

        return potential_new


# ============================================================
# STANDALONE USAGE
# ============================================================

if __name__ == "__main__":
    """Quick demo of the normalizer with sample descriptions."""

    # Sample descriptions that a real technician might write
    test_descriptions = [
        "REPL mech seal on pump P-101 leaking bad",
        "BRG noise on conv C-301 DE side replaced",
        "MTR overheating on line 2 - tripped on O/L",
        "VLV stuck open CV-501 replaced actuator",
        "XMTR reading erratic recalibrated PT-101",
        "corrosion found on HX shell side patched",
        "performed PM inspection per schedule all ok",
        "pump cavitating low suction pressure",
        "CKT BKR tripped in MCC reset and tested",
        "conveyor belt tracking off adjusted idlers",
        "replaced PRV on steam header lifting early",
        "agitator seal leaking product replaced M/S",
        "oil sample taken from gearbox sent to lab",
        "robot servo fault axis 3 replaced encoder",
        "CIP system spray ball clogged cleaned",
        "",  # Empty description
        "fixed it",  # Vague description
        "pmp lkg frm seal area bad",  # Heavy abbreviation
    ]

    print("=" * 60)
    print("MaintSignal — Smart Normalizer Demo")
    print("=" * 60)

    # Test with different industries
    for industry in ["general_manufacturing", "oil_and_gas", "pharmaceutical"]:
        print(f"\n--- Industry: {INDUSTRY_TAXONOMIES.get(industry, {}).get('name', industry)} ---\n")

        normalizer = SmartNormalizer(mode="offline", industry=industry)
        results = normalizer.normalize(test_descriptions)
        summary = normalizer.get_summary(results)

        for _, row in results.iterrows():
            conf_marker = {"high": "●", "medium": "◐", "low": "○"}.get(row["confidence"], "?")
            print(f"  {conf_marker} [{row['category']:30s}] {row['original'][:50]}")
            if row["interpretation"] != row["original"]:
                print(f"    → Expanded: {row['interpretation'][:60]}")

        print(f"\n  Summary: {summary['total_processed']} processed, "
              f"{summary['categories_found']} categories, "
              f"{summary['high_confidence']} high confidence")

    # Demo abbreviation expansion
    print("\n--- Abbreviation Expansion Demo ---\n")
    normalizer = SmartNormalizer(mode="offline")
    test_texts = [
        "REPL MECH SEAL on PMP P-101",
        "BRG seized on CONV DE side",
        "XMTR fault on PT-201 recal",
        "CKT BKR tripped in MCC",
        "PRV lifting on STM header",
    ]
    for text in test_texts:
        expanded = normalizer.expand_abbreviations(text)
        print(f"  Original:  {text}")
        print(f"  Expanded:  {expanded}")
        print()
