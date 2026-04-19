"""
Upgrade data_ingestion.py:
1. Store and expose column mapping confidence scores
2. Show mapping quality to users in dashboard

Run: python3 upgrade_mapping.py
"""

with open("data_ingestion.py", "r") as f:
    content = f.read()

# 1. Add confidence scores to IngestionResult
old_result_class = '''class IngestionResult:
    """Result of data ingestion."""
    def __init__(self):
        self.success = False
        self.df = None
        self.raw_df = None
        self.mapping = {}
        self.file_type = ""
        self.rows = 0
        self.columns = 0
        self.warnings = []
        self.errors = []'''

new_result_class = '''class IngestionResult:
    """Result of data ingestion."""
    def __init__(self):
        self.success = False
        self.df = None
        self.raw_df = None
        self.mapping = {}
        self.mapping_confidence = {}
        self.file_type = ""
        self.rows = 0
        self.columns = 0
        self.warnings = []
        self.errors = []
        self.sheets_available = []'''

if "mapping_confidence" not in content:
    content = content.replace(old_result_class, new_result_class)
    print("[1/3] Added confidence scores to IngestionResult")
else:
    print("[1/3] Already present")

# 2. Store confidence in _auto_map_columns
old_auto_map = '''    def _auto_map_columns(self, columns):
        """Auto-detect column mapping using the knowledge base."""
        raw_mapping = guess_column_mapping(columns)

        # Convert to simple {original: standard} format
        mapping = {}
        used_standards = set()

        # Sort by confidence (highest first) to avoid conflicts
        sorted_items = sorted(
            raw_mapping.items(),
            key=lambda x: x[1]["confidence"],
            reverse=True
        )

        for original, match in sorted_items:
            standard = match["maps_to"]
            if standard not in used_standards:
                mapping[original] = standard
                used_standards.add(standard)

        return mapping'''

new_auto_map = '''    def _auto_map_columns(self, columns):
        """Auto-detect column mapping using the knowledge base."""
        raw_mapping = guess_column_mapping(columns)

        mapping = {}
        self._mapping_confidence = {}
        used_standards = set()

        sorted_items = sorted(
            raw_mapping.items(),
            key=lambda x: x[1]["confidence"],
            reverse=True
        )

        for original, match in sorted_items:
            standard = match["maps_to"]
            confidence = match["confidence"]
            if standard not in used_standards:
                mapping[original] = standard
                self._mapping_confidence[original] = round(confidence, 1)
                used_standards.add(standard)

        return mapping'''

if "_mapping_confidence" not in content:
    content = content.replace(old_auto_map, new_auto_map)
    print("[2/3] Storing confidence scores in mapping")
else:
    print("[2/3] Already present")

# 3. Pass confidence to result
old_result_set = "result.mapping = mapping"
new_result_set = "result.mapping = mapping\n        result.mapping_confidence = getattr(self, '_mapping_confidence', {})"

if "result.mapping_confidence" not in content:
    content = content.replace(old_result_set, new_result_set, 1)
    print("[3/3] Passing confidence to result")
else:
    print("[3/3] Already present")

with open("data_ingestion.py", "w") as f:
    f.write(content)

import py_compile
try:
    py_compile.compile("data_ingestion.py", doraise=True)
    print("[OK] data_ingestion.py valid")
except py_compile.PyCompileError as e:
    print(f"[ERROR] {e}")

# Now add confidence display to main_app.py
print("\nUpgrading main_app.py...")

with open("main_app.py", "r") as f:
    app = f.read()

old_tags = '''    st.markdown(f"""
    <div style="display:flex; gap:0.8rem; align-items:center; margin-bottom:1rem;">
        <span class="tag tag-blue">{ind_info.get('name', selected_industry)}</span>
        <span class="tag tag-green">{norm_mode}</span>
        <span class="tag tag-orange">{ingestion.file_type.upper()} Import</span>
    </div>
    """, unsafe_allow_html=True)'''

new_tags = '''    st.markdown(f"""
    <div style="display:flex; gap:0.8rem; align-items:center; margin-bottom:1rem;">
        <span class="tag tag-blue">{ind_info.get('name', selected_industry)}</span>
        <span class="tag tag-green">{norm_mode}</span>
        <span class="tag tag-orange">{ingestion.file_type.upper()} Import</span>
        <span class="tag" style="background:rgba(0,232,122,.08);color:#00e68a;">{len(ingestion.mapping)} columns mapped</span>
    </div>
    """, unsafe_allow_html=True)

    # Column mapping with confidence scores
    if hasattr(ingestion, 'mapping_confidence') and ingestion.mapping_confidence:
        with st.expander("Column Mapping Details", expanded=False):
            for orig_col, std_col in ingestion.mapping.items():
                conf = ingestion.mapping_confidence.get(orig_col, 0)
                conf_color = "#00e68a" if conf >= 80 else "#ff9f43" if conf >= 50 else "#ff4d6a"
                conf_label = "High" if conf >= 80 else "Medium" if conf >= 50 else "Low"
                st.markdown(f"""
                <div style="display:flex;justify-content:space-between;align-items:center;padding:0.3rem 0;border-bottom:1px solid #1c2436;font-size:0.82rem;">
                    <div><span style="color:#6b7394;">{orig_col}</span> → <strong style="color:#e8eaf0;">{std_col}</strong></div>
                    <span style="font-family:monospace;color:{conf_color};font-size:0.75rem;">{conf_label} ({conf}%)</span>
                </div>
                """, unsafe_allow_html=True)'''

if "Column Mapping Details" not in app:
    app = app.replace(old_tags, new_tags)
    with open("main_app.py", "w") as f:
        f.write(app)
    print("[OK] Added mapping display to dashboard")
else:
    print("[SKIP] Already present")

try:
    py_compile.compile("main_app.py", doraise=True)
    print("[OK] main_app.py valid")
except py_compile.PyCompileError as e:
    print(f"[ERROR] {e}")

print("\n✅ Column mapping upgrade complete!")
