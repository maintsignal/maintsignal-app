"""
MaintSignal - AI Upgrade Script
Upgrades the keyword classifier to multi-signal scoring
and enhances the LLM prompt with few-shot examples.

Run: python upgrade_ai.py
"""
import os

# ============================================================
# STEP 1: Patch smart_normalizer.py - upgrade keyword classifier
# ============================================================
print("Upgrading smart_normalizer.py...")

with open("smart_normalizer.py", "r") as f:
    norm_content = f.read()

# Replace the _keyword_classify method with multi-signal scoring
old_keyword_method = '''    def _keyword_classify(self, text):'''

new_keyword_method = '''    def _keyword_classify(self, text):
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

    def _keyword_classify_OLD_REMOVED(self, text):'''

if "_keyword_classify_OLD_REMOVED" not in norm_content:
    norm_content = norm_content.replace(old_keyword_method, new_keyword_method)
    with open("smart_normalizer.py", "w") as f:
        f.write(norm_content)
    print("  [OK] Upgraded keyword classifier to multi-signal scoring")
else:
    print("  [SKIP] Already upgraded")


# ============================================================
# STEP 2: Patch knowledge_base.py - upgrade LLM prompt
# ============================================================
print("Upgrading knowledge_base.py prompt...")

with open("knowledge_base.py", "r") as f:
    kb_content = f.read()

# Add few-shot examples and enhanced prompt
old_prompt_start = '''def build_normalization_prompt(descriptions, industry=None, client_abbreviations=None):
    """
    Build the optimal prompt for LLM-based failure normalization.
    This is the core intelligence — the prompt IS the product.
    """'''

new_prompt_start = '''def build_normalization_prompt(descriptions, industry=None, client_abbreviations=None):
    """
    Build the optimal prompt for LLM-based failure normalization.
    Enhanced with few-shot examples and chain-of-thought reasoning.
    This is the core intelligence - the prompt IS the product.
    """'''

# Replace the entire prompt function
old_prompt_func_end = '''    return prompt'''
# Find the FIRST occurrence of return prompt after build_normalization_prompt
import re

# Replace just the prompt string template
old_prompt_template = '''    prompt = f"""You are a senior maintenance & reliability engineer with 20+ years of experience in {industry_name}. You specialize in analyzing CMMS work order data.

CONTEXT:
These are real technician-written work order descriptions from a {industry_name} plant. Technicians write under time pressure, use heavy abbreviations, shorthand, and plant-specific jargon. The same failure can be described dozens of different ways.

YOUR TASK:
Classify each description into exactly ONE failure category. Extract the affected component. Expand all abbreviations in your interpretation.'''

new_prompt_template = '''    # Get few-shot examples for this industry
    few_shot_examples = {
        "pharmaceutical": [
            {"original": "REPL mech seal P-101 lkg", "category": "Seal / Packing Failure", "component": "mechanical seal", "confidence": "high"},
            {"original": "CIP valve stuck closed prod line 2", "category": "Valve / Actuator Failure", "component": "CIP valve", "confidence": "high"},
            {"original": "PM per SOP-M-042", "category": "Preventive Maintenance", "component": "N/A", "confidence": "high"},
            {"original": "fixed it", "category": "Unknown", "component": "unknown", "confidence": "low"},
        ],
        "oil_and_gas": [
            {"original": "PSV popped reset @ 150psi", "category": "Valve / Actuator Failure", "component": "pressure safety valve", "confidence": "high"},
            {"original": "pump P-2201A high vib DE brg", "category": "Bearing Failure", "component": "drive end bearing", "confidence": "high"},
            {"original": "annual API 510 inspection", "category": "Preventive Maintenance", "component": "pressure vessel", "confidence": "high"},
            {"original": "same problem again", "category": "Unknown", "component": "unknown", "confidence": "low"},
        ],
        "general_manufacturing": [
            {"original": "BRG noise conv DE side", "category": "Bearing Failure", "component": "drive end bearing", "confidence": "high"},
            {"original": "MTR tripped on O/L", "category": "Motor / Drive Failure", "component": "motor", "confidence": "high"},
            {"original": "replaced filters and lubed bearings", "category": "Preventive Maintenance", "component": "filters and bearings", "confidence": "high"},
            {"original": "done", "category": "Unknown", "component": "unknown", "confidence": "low"},
        ],
    }
    examples = few_shot_examples.get(industry or "general_manufacturing", few_shot_examples["general_manufacturing"])
    examples_str = "\\n".join(
        f'    Input: "{ex["original"]}" -> Category: {ex["category"]}, Component: {ex["component"]}, Confidence: {ex["confidence"]}'
        for ex in examples
    )

    prompt = f"""You are a senior maintenance & reliability engineer with 20+ years of experience in {industry_name}. You specialize in CMMS work order data classification.

CONTEXT:
These are real technician-written work order descriptions from a {industry_name} facility. Technicians write under extreme time pressure using heavy abbreviations, shorthand, and inconsistent spelling.

YOUR REASONING PROCESS FOR EACH DESCRIPTION:
1. EXPAND all abbreviations to full words
2. IDENTIFY the root failure mode (what BROKE, not what was DONE to fix it)
3. IDENTIFY the specific component affected
4. CLASSIFY into exactly ONE failure category
5. ASSESS confidence based on how clear the description is

EXAMPLES OF CORRECT CLASSIFICATION:
{examples_str}'''

if "YOUR REASONING PROCESS" not in kb_content:
    kb_content = kb_content.replace(old_prompt_template, new_prompt_template)
    # Also update the rules section
    old_rules = '''RULES:
1. Classify based on the ROOT FAILURE, not the repair action. "Replaced bearing" = Bearing Failure, not "Replacement."
2. If a description mentions multiple issues, classify by the PRIMARY failure.
3. "PM", "inspection", "routine", "scheduled" = Preventive Maintenance unless a specific failure is described.
4. Empty, nonsensical, or single-word descriptions with no failure context = "Preventive Maintenance" if it seems routine, otherwise flag as "Unknown."
5. Expand ALL abbreviations in the "interpretation" field.
6. If unsure between two categories, pick the more specific one.'''

    new_rules = '''CLASSIFICATION RULES:
1. Classify by ROOT FAILURE, not repair action. "Replaced bearing" = Bearing Failure. "Replaced seal" = Seal Failure.
2. If description mentions BOTH a failure AND PM activity, classify as the FAILURE.
3. Multiple failures mentioned = classify by the PRIMARY/first failure.
4. Pure PM/inspection/routine/scheduled with NO failure = "Preventive Maintenance".
5. Vague descriptions ("fixed it", "done", "ok") with no component = "Unknown" with LOW confidence.
6. "Replaced" or "changed" implies something failed - classify by what was replaced.
7. Expand ALL abbreviations in the interpretation field.
8. If unsure between two categories, pick the more SPECIFIC one.'''

    kb_content = kb_content.replace(old_rules, new_rules)

    with open("knowledge_base.py", "w") as f:
        f.write(kb_content)
    print("  [OK] Enhanced LLM prompt with few-shot examples and chain-of-thought")
else:
    print("  [SKIP] Prompt already enhanced")

# ============================================================
# STEP 3: Verify both files compile
# ============================================================
print("\nVerifying code...")
import py_compile
try:
    py_compile.compile("smart_normalizer.py", doraise=True)
    print("  [OK] smart_normalizer.py - no syntax errors")
except py_compile.PyCompileError as e:
    print(f"  [ERROR] smart_normalizer.py - {e}")

try:
    py_compile.compile("knowledge_base.py", doraise=True)
    print("  [OK] knowledge_base.py - no syntax errors")
except py_compile.PyCompileError as e:
    print(f"  [ERROR] knowledge_base.py - {e}")

print("\n✅ AI Upgrade complete!")
print("   - Offline mode: Multi-signal scoring (was single keyword)")
print("   - Online mode: Few-shot examples + chain-of-thought reasoning")
print("   - Both modes now score against ALL categories simultaneously")
print("   - Confidence calibration based on score margins")
print("\nRestart Streamlit to see the difference.")
