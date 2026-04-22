"""
Add JSON and XML file upload support to main_app.py and data_ingestion.py
Run: python3 add_file_formats.py
"""

# ============================================================
# 1. Update data_ingestion.py - add JSON and XML readers
# ============================================================
with open("data_ingestion.py", "r") as f:
    content = f.read()

# Add json and xml imports
if "import xml" not in content:
    content = content.replace(
        "import pandas as pd",
        "import pandas as pd\nimport json as json_lib\nimport xml.etree.ElementTree as ET"
    )
    print("[1/4] Added json and xml imports")
else:
    print("[1/4] Imports already present")

# Add JSON reader method
json_method = '''
    def _read_json(self, file_obj):
        """Read JSON file - supports array of objects or nested structures."""
        try:
            raw = json_lib.load(file_obj)
            
            # Handle different JSON structures
            if isinstance(raw, list):
                # Array of objects - most common
                return pd.DataFrame(raw)
            elif isinstance(raw, dict):
                # Check for nested data key
                for key in ["data", "records", "work_orders", "workorders", "items", "results"]:
                    if key in raw and isinstance(raw[key], list):
                        return pd.DataFrame(raw[key])
                # Single level dict - wrap in list
                return pd.DataFrame([raw])
            else:
                return None
        except Exception as e:
            return None

    def _read_xml(self, file_obj):
        """Read XML file - extracts records from repeating elements."""
        try:
            tree = ET.parse(file_obj)
            root = tree.getroot()
            
            # Find repeating child elements (work orders, records, etc.)
            # Use the most common child tag
            child_tags = {}
            for child in root:
                tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
                child_tags[tag] = child_tags.get(tag, 0) + 1
            
            if not child_tags:
                return None
            
            # Use the most frequent tag as the record element
            record_tag = max(child_tags, key=child_tags.get)
            
            records = []
            for elem in root.iter():
                tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
                if tag == record_tag:
                    record = {}
                    for child in elem:
                        child_tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
                        record[child_tag] = child.text
                    if record:
                        records.append(record)
            
            if records:
                return pd.DataFrame(records)
            return None
        except Exception as e:
            return None
'''

if "_read_json" not in content:
    # Insert before _auto_map_columns
    content = content.replace(
        "    def _auto_map_columns",
        json_method + "\n    def _auto_map_columns"
    )
    print("[2/4] Added JSON and XML reader methods")
else:
    print("[2/4] Readers already present")

# Update the ingest method to handle JSON and XML
old_detect = '''        # Detect file type
        file_type = self._detect_type(file_obj)'''

new_detect = '''        # Detect file type
        file_type = self._detect_type(file_obj)
        
        # Also check filename extension for JSON/XML
        filename = getattr(file_obj, 'name', '').lower()
        if filename.endswith('.json'):
            file_type = "json"
        elif filename.endswith('.xml'):
            file_type = "xml"'''

if "filename.endswith" not in content:
    content = content.replace(old_detect, new_detect)
    print("[3/4] Added JSON/XML detection by filename")
else:
    print("[3/4] Detection already present")

# Add JSON/XML handling in the read logic
old_read = '''        if file_type == "csv":'''
new_read = '''        if file_type == "json":
            raw_df = self._read_json(file_obj)
            if raw_df is None:
                result.errors.append("Could not parse JSON file")
                return result
        elif file_type == "xml":
            raw_df = self._read_xml(file_obj)
            if raw_df is None:
                result.errors.append("Could not parse XML file")
                return result
        elif file_type == "csv":'''

if 'file_type == "json"' not in content:
    content = content.replace(old_read, new_read)
    print("[4/4] Added JSON/XML to read logic")
else:
    print("[4/4] Read logic already present")

with open("data_ingestion.py", "w") as f:
    f.write(content)

# ============================================================
# 2. Update main_app.py - add JSON and XML to file uploader
# ============================================================
with open("main_app.py", "r") as f:
    app = f.read()

# Update file uploader to accept more types
old_uploader = 'type=["csv", "xlsx", "xls", "pdf"]'
new_uploader = 'type=["csv", "xlsx", "xls", "pdf", "json", "xml"]'

if '"json"' not in app:
    app = app.replace(old_uploader, new_uploader)
    with open("main_app.py", "w") as f:
        f.write(app)
    print("[OK] Updated file uploader to accept JSON and XML")
else:
    print("[SKIP] File uploader already updated")

# Verify
import py_compile
try:
    py_compile.compile("data_ingestion.py", doraise=True)
    py_compile.compile("main_app.py", doraise=True)
    print("\n✅ JSON and XML support added!")
    print("   Supported formats: CSV, Excel (.xlsx/.xls), PDF, JSON, XML")
except py_compile.PyCompileError as e:
    print(f"\n❌ Error: {e}")
