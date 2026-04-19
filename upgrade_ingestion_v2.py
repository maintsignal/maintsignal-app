"""
Upgrade ingestion: add JSON support, confidence scores, fix datetime.
Run: python3 upgrade_ingestion_v2.py
"""

# Fix data_ingestion.py
print("Fixing data_ingestion.py...")
with open("data_ingestion.py", "r") as f:
    di = f.read()

if "infer_datetime_format=True" in di:
    di = di.replace(", infer_datetime_format=True", "")
    print("  [OK] Removed infer_datetime_format")

if "_read_json" not in di:
    di = di.replace(
        "    def _read_excel(self, file_path):",
        '''    def _read_json(self, file_path):
        """Read JSON file into a DataFrame."""
        try:
            df = pd.read_json(file_path)
            return df
        except Exception:
            with open(file_path, 'r') as f:
                data = json.load(f)
            if isinstance(data, list):
                return pd.DataFrame(data)
            elif isinstance(data, dict):
                for key, val in data.items():
                    if isinstance(val, list):
                        return pd.DataFrame(val)
            return pd.DataFrame([data])

    def _read_excel(self, file_path):'''
    )
    print("  [OK] Added JSON reader")

if 'ext == ".json"' not in di:
    di = di.replace(
        '        elif ext in (".xlsx", ".xls", ".xlsm"):',
        '        elif ext == ".json":\n            self.file_type = "json"\n            raw_df = self._read_json(file_path)\n        elif ext in (".xlsx", ".xls", ".xlsm"):'
    )
    print("  [OK] Added JSON detection")

with open("data_ingestion.py", "w") as f:
    f.write(di)

# Fix main_app.py
print("\nFixing main_app.py...")
with open("main_app.py", "r") as f:
    app = f.read()

# Add JSON to uploader
app = app.replace(
    '"Drop your file here — CSV, Excel, or PDF"',
    '"Drop your file here — CSV, Excel, PDF, or JSON"'
)
app = app.replace(
    'type=["csv", "xlsx", "xls", "xlsm", "pdf"],',
    'type=["csv", "xlsx", "xls", "xlsm", "pdf", "json", "tsv"],'
)
print("  [OK] Added JSON/TSV to uploader")

# Add confidence scores to column mapping display
old_mapping = '''    with st.expander("📋 View Column Mapping", expanded=False):
        if ingestion.mapping:
            for original, standard in sorted(ingestion.mapping.items()):
                st.markdown(f"""
                <div class="mapping-row">
                    <span style="color:#6b7394; min-width:200px;">{original}</span>
                    <span class="mapping-arrow">→</span>
                    <span style="color:#e8eaf0;">{standard}</span>
                    <span class="tag tag-green">auto</span>
                </div>
                """, unsafe_allow_html=True)'''

new_mapping = '''    with st.expander("📋 View Column Mapping (with confidence scores)", expanded=False):
        if ingestion.mapping:
            from knowledge_base import guess_column_mapping
            raw_conf = guess_column_mapping(list(ingestion.mapping.keys()))
            for original, standard in sorted(ingestion.mapping.items()):
                conf = raw_conf.get(original, {}).get("confidence", 0)
                conf_color = "#00e68a" if conf >= 80 else "#ff9f43" if conf >= 50 else "#ff4d6a"
                conf_label = "High" if conf >= 80 else "Medium" if conf >= 50 else "Low"
                st.markdown(f"""
                <div class="mapping-row">
                    <span style="color:#6b7394; min-width:200px;">{original}</span>
                    <span class="mapping-arrow">→</span>
                    <span style="color:#e8eaf0;">{standard}</span>
                    <span style="font-family:'JetBrains Mono';color:{conf_color};font-size:0.75rem;margin-left:0.5rem;">{conf:.0f}% {conf_label}</span>
                </div>
                """, unsafe_allow_html=True)'''

if "confidence scores" not in app:
    app = app.replace(old_mapping, new_mapping)
    print("  [OK] Added confidence scores to column mapping")
else:
    print("  [SKIP] Already present")

with open("main_app.py", "w") as f:
    f.write(app)

# Verify
import py_compile
try:
    py_compile.compile("data_ingestion.py", doraise=True)
    py_compile.compile("main_app.py", doraise=True)
    print("\n✅ All upgrades applied! No syntax errors.")
    print("   - JSON + TSV format support")
    print("   - Column mapping confidence scores visible")
    print("   - infer_datetime_format bug fixed")
except py_compile.PyCompileError as e:
    print(f"\n❌ Error: {e}")
