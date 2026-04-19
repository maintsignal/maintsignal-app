"""
Integrate Learning Loop into main_app.py
- Auto-saves classification results after each analysis
- Adds learning stats to sidebar
Run: python3 add_learning_loop.py
"""

with open("main_app.py", "r") as f:
    content = f.read()

# 1. Add import
old_import = "from spare_parts_analysis import"
new_import = "from learning_loop import save_classification_results, get_learning_stats, save_correction, get_few_shot_examples_from_corrections\nfrom spare_parts_analysis import"

if "learning_loop" not in content:
    content = content.replace(old_import, new_import)
    print("[1/3] Added learning_loop import")
else:
    print("[1/3] Import already present")

# 2. Add auto-save after normalization results are generated
# Find the export section and add save before it
export_marker = '''    # ============================================================
    # EXPORT
    # ============================================================
    st.markdown("---")'''

save_code = '''    # ============================================================
    # LEARNING LOOP - Auto-save results
    # ============================================================
    try:
        save_classification_results(
            norm_results, 
            industry=selected_industry, 
            client_name=client_name,
            source_file=uploaded_file.name if uploaded_file else "demo_data"
        )
    except Exception as e:
        pass  # Don't break the app if learning save fails

    # ============================================================
    # EXPORT
    # ============================================================
    st.markdown("---")'''

if "LEARNING LOOP" not in content:
    content = content.replace(export_marker, save_code)
    print("[2/3] Added auto-save after analysis")
else:
    print("[2/3] Auto-save already present")

# 3. Add learning stats to sidebar
old_sidebar_end = '''    st.sidebar.markdown("---")'''

# Find the LAST occurrence of sidebar markdown ---
# Add learning stats after the sidebar configuration section
learning_sidebar = '''    st.sidebar.markdown("---")
    
    # Learning Loop Stats
    try:
        l_stats = get_learning_stats()
        if l_stats.get("total_runs", 0) > 0:
            st.sidebar.markdown("**Learning Database**")
            st.sidebar.caption(f"Analyses completed: {l_stats.get('total_runs', 0)}")
            st.sidebar.caption(f"Patterns learned: {l_stats.get('total_unique_patterns', 0)}")
            st.sidebar.caption(f"Corrections stored: {l_stats.get('total_corrections', 0)}")
    except:
        pass'''

if "Learning Database" not in content:
    # Replace only the first occurrence
    content = content.replace(old_sidebar_end, learning_sidebar, 1)
    print("[3/3] Added learning stats to sidebar")
else:
    print("[3/3] Learning stats already present")

with open("main_app.py", "w") as f:
    f.write(content)

import py_compile
try:
    py_compile.compile("main_app.py", doraise=True)
    print("\n✅ Learning Loop integrated!")
    print("   - Auto-saves every analysis run")
    print("   - Stores classification patterns")
    print("   - Shows learning stats in sidebar")
    print("   - Gets smarter with each client analysis")
except py_compile.PyCompileError as e:
    print(f"\n❌ Syntax error: {e}")
