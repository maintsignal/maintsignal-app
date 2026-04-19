"""
Add Industry Benchmarking tab to main_app.py
Run: python3 add_benchmark_tab.py
"""

with open("main_app.py", "r") as f:
    content = f.read()

# 1. Add import
old_import = "from root_cause_correlation import"
new_import = "from industry_benchmarking import calculate_client_metrics, benchmark_against_industry, INDUSTRY_BENCHMARKS\nfrom root_cause_correlation import"

if "industry_benchmarking" not in content:
    content = content.replace(old_import, new_import)
    print("[1/3] Added industry_benchmarking import")
else:
    print("[1/3] Import already present")

# 2. Add tab
old_tabs = '''    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs([
        "📋 Data Quality", "🏭 Problem Assets", "🧠 Failure Analysis",
        f"💰 Financial Impact", "✅ Recommendations",
        "🔍 Compliance", "📈 Trends", "📚 Knowledge", "🔗 Root Cause"
    ])'''

new_tabs = '''    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10 = st.tabs([
        "📋 Quality", "🏭 Assets", "🧠 Failures",
        f"💰 Financial", "✅ Actions",
        "🔍 Compliance", "📈 Trends", "📚 Knowledge", "🔗 Root Cause", "📊 Benchmark"
    ])'''

if "tab10" not in content:
    content = content.replace(old_tabs, new_tabs)
    print("[2/3] Added Benchmark tab (now 10 tabs)")
else:
    print("[2/3] Tab already present")

# 3. Add tab content before EXPORT
export_marker = '''    # ============================================================
    # EXPORT
    # ============================================================'''

benchmark_tab = '''    # ============================================================
    # TAB 10: INDUSTRY BENCHMARKING
    # ============================================================
    with tab10:
        st.markdown('<div class="sec-label">Industry Benchmarking</div>', unsafe_allow_html=True)
        st.markdown('<div class="sec-title">How You Compare to Industry Peers</div>', unsafe_allow_html=True)

        with st.spinner("Calculating benchmarks..."):
            client_metrics = calculate_client_metrics(df, quality_results=quality, downtime_results=downtime)
            bench_results = benchmark_against_industry(client_metrics, industry=selected_industry)

        # Overall score
        b_score = bench_results["summary_score"]
        b_color = "#00e68a" if b_score >= 70 else "#ff9f43" if b_score >= 45 else "#ff4d6a"
        st.markdown(f"""
        <div class="insight-box" style="border-left:3px solid {b_color};">
            <div style="display:flex;justify-content:space-between;align-items:center;">
                <div>
                    <strong style="font-size:1.1rem;color:#e8eaf0;">Industry Position: {bench_results['overall_rating']}</strong>
                    <div style="color:#6b7394;font-size:0.85rem;">Compared to {bench_results['industry']} peers</div>
                </div>
                <span style="font-family:'JetBrains Mono';font-size:2rem;font-weight:900;color:{b_color};">{b_score}%</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Individual metrics
        st.markdown("<br>", unsafe_allow_html=True)
        for comp in bench_results["comparisons"]:
            r_color = {"world_class": "#00e68a", "above_average": "#00e68a", "below_average": "#ff9f43", "critical": "#ff4d6a"}.get(comp["rating"], "#6b7394")
            r_icon = {"world_class": "★", "above_average": "✓", "below_average": "!", "critical": "✗"}.get(comp["rating"], "?")

            # Calculate position on scale
            wc = comp["world_class"]
            avg = comp["industry_average"]
            poor = comp["poor"]
            val = comp["client_value"]

            st.markdown(f"""
            <div class="insight-box" style="padding:1rem 1.2rem;">
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.4rem;">
                    <div>
                        <span style="color:{r_color};font-weight:700;margin-right:0.5rem;">{r_icon}</span>
                        <strong style="color:#e8eaf0;">{comp['metric']}</strong>
                        <span style="color:#6b7394;font-size:0.75rem;margin-left:0.5rem;">({comp['rating_label']})</span>
                    </div>
                    <span style="font-family:'JetBrains Mono';color:{r_color};font-weight:700;font-size:1.1rem;">{val}{comp['unit']}</span>
                </div>
                <div style="display:flex;justify-content:space-between;font-size:0.72rem;color:#6b7394;margin-bottom:0.3rem;">
                    <span>Poor: {poor}{comp['unit']}</span>
                    <span>Average: {avg}{comp['unit']}</span>
                    <span>World Class: {wc}{comp['unit']}</span>
                </div>
                <div style="height:8px;background:#1c2436;border-radius:4px;overflow:hidden;position:relative;">
                    <div style="position:absolute;left:50%;top:0;bottom:0;width:1px;background:#6b7394;"></div>
                    <div style="height:100%;width:{min(max(((val - poor) / max(wc - poor, 1)) * 100, 5), 100) if comp['direction'] == 'higher_better' else min(max(((poor - val) / max(poor - wc, 1)) * 100, 5), 100)}%;background:{r_color};border-radius:4px;"></div>
                </div>
                <div style="font-size:0.7rem;color:#6b7394;margin-top:0.3rem;">Source: {comp['source']}</div>
            </div>
            """, unsafe_allow_html=True)

        # Strengths and Weaknesses
        if bench_results["strengths"]:
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("**Strengths vs Industry**")
            for s in bench_results["strengths"]:
                st.markdown(f'<div class="insight-box success" style="padding:0.5rem 1rem;font-size:0.85rem;">✓ {s}</div>', unsafe_allow_html=True)

        if bench_results["weaknesses"]:
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("**Gaps vs Industry**")
            for w in bench_results["weaknesses"]:
                st.markdown(f'<div class="insight-box critical" style="padding:0.5rem 1rem;font-size:0.85rem;">✗ {w}</div>', unsafe_allow_html=True)

    ''' + export_marker

if "TAB 10: INDUSTRY BENCHMARKING" not in content:
    content = content.replace(export_marker, benchmark_tab)
    print("[3/3] Added Benchmark tab content")
else:
    print("[3/3] Tab content already present")

with open("main_app.py", "w") as f:
    f.write(content)

import py_compile
try:
    py_compile.compile("main_app.py", doraise=True)
    print("\n✅ Industry Benchmarking integrated! (10 tabs)")
except py_compile.PyCompileError as e:
    print(f"\n❌ Syntax error: {e}")
