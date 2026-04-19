#!/bin/bash
# Run this script from ~/Projects/maintsignal to fix the API normalization issue
# Usage: bash fix_normalizer.sh

cd ~/Projects/maintsignal

# Create a Python script to do the replacement
python3 << 'PYEOF'
import re

with open("main_app.py", "r") as f:
    content = f.read()

# Find and replace the normalization section
old_block = '''    with st.spinner("🧠 Normalizing failure descriptions..."):
        normalizer = SmartNormalizer(
            mode=selected_mode,
            industry=selected_industry,
            api_key=api_key if api_key else None,
        )
        descriptions = df["description"].tolist() if "description" in df.columns else []
        norm_results = normalizer.normalize(descriptions)
        norm_summary = normalizer.get_summary(norm_results)'''

new_block = '''    st.markdown("🧠 **Normalizing failure descriptions...**")
    try:
        normalizer = SmartNormalizer(
            mode=selected_mode,
            industry=selected_industry,
            api_key=api_key if api_key else None,
        )
        descriptions = df["description"].tolist() if "description" in df.columns else []

        if selected_mode in ["online", "hybrid"] and api_key:
            progress_bar = st.progress(0, text="Processing descriptions with AI...")
            def update_progress(done, total):
                progress_bar.progress(min(done / max(total, 1), 1.0), text=f"AI processing: {done}/{total} descriptions")
            norm_results = normalizer.normalize(descriptions, progress_callback=update_progress)
            progress_bar.empty()
        else:
            with st.spinner("Running offline normalization..."):
                norm_results = normalizer.normalize(descriptions)

        norm_summary = normalizer.get_summary(norm_results)
        st.success(f"Normalized {len(descriptions):,} descriptions into {norm_summary.get('categories_found', 0)} categories")
    except Exception as e:
        st.warning(f"AI normalization error: {str(e)[:150]}. Falling back to offline mode.")
        normalizer = SmartNormalizer(mode="offline", industry=selected_industry)
        descriptions = df["description"].tolist() if "description" in df.columns else []
        norm_results = normalizer.normalize(descriptions)
        norm_summary = normalizer.get_summary(norm_results)'''

if old_block in content:
    content = content.replace(old_block, new_block)
    with open("main_app.py", "w") as f:
        f.write(content)
    print("SUCCESS: Normalization section fixed with progress bar and error fallback.")
else:
    # Try finding it with different whitespace
    print("WARNING: Exact match not found. Trying alternative match...")
    
    # Check if already fixed
    if "progress_bar = st.progress" in content:
        print("ALREADY FIXED: The progress bar code is already in main_app.py.")
    else:
        # Manual approach - find the line and replace
        lines = content.split('\n')
        start_idx = None
        end_idx = None
        for i, line in enumerate(lines):
            if 'Normalizing failure descriptions' in line:
                start_idx = i
            if start_idx and 'norm_summary = normalizer.get_summary' in line:
                end_idx = i
                break
        
        if start_idx and end_idx:
            new_lines = new_block.split('\n')
            lines[start_idx:end_idx+1] = new_lines
            content = '\n'.join(lines)
            with open("main_app.py", "w") as f:
                f.write(content)
            print(f"SUCCESS: Replaced lines {start_idx+1} to {end_idx+1} with fixed code.")
        else:
            print(f"ERROR: Could not find normalization section. start={start_idx}, end={end_idx}")
            print("Please manually edit main_app.py around the 'Normalizing failure descriptions' line.")

PYEOF

echo ""
echo "Now pushing to GitHub..."
git add .
git commit -m "Fix API normalization with progress bar and error fallback"
git push
echo ""
echo "Done! Streamlit Cloud will auto-redeploy in 2-3 minutes."
