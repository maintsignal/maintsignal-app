"""
Add Root Cause Correlation tab to main_app.py
Run: python add_root_cause_tab.py
"""

with open("main_app.py", "r") as f:
    content = f.read()

# 1. Add import
old_import = "from compliance_checker import"
new_import = "from root_cause_correlation import analyze_root_cause_correlations, generate_correlation_summary\nfrom compliance_checker import"

if "root_cause_correlation" not in content:
    content = content.replace(old_import, new_import)
    print("[1/3] Added root_cause_correlation import")
else:
    print("[1/3] Import already present")

# 2. Add tab
old_tabs = '''    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
        "📋 Data Quality", "🏭 Problem Assets", "🧠 Failure Analysis",
        f"💰 Financial Impact", "✅ Recommendations",
        "🔍 Compliance Audit", "📈 Trends", "📚 Knowledge Capture"
    ])'''

new_tabs = '''    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs([
        "📋 Data Quality", "🏭 Problem Assets", "🧠 Failure Analysis",
        f"💰 Financial Impact", "✅ Recommendations",
        "🔍 Compliance", "📈 Trends", "📚 Knowledge", "🔗 Root Cause"
    ])'''

if "tab9" not in content:
    content = content.replace(old_tabs, new_tabs)
    print("[2/3] Added Root Cause tab (now 9 tabs)")
else:
    print("[2/3] Tab already present")

# 3. Add tab content before EXPORT section
export_marker = '''    # ============================================================
    # EXPORT
    # ============================================================'''

root_cause_tab = '''    # ============================================================
    # TAB 9: ROOT CAUSE CORRELATION
    # ============================================================
    with tab9:
        st.markdown('<div class="sec-label">Root Cause Correlation</div>', unsafe_allow_html=True)
        st.markdown('<div class="sec-title">Hidden Failure Relationships</div>', unsafe_allow_html=True)

        with st.spinner("Analyzing failure correlations..."):
            # Use normalized categories if available
            rc_df = df.copy()
            if "category" in norm_results.columns:
                rc_df["_norm_category"] = norm_results["category"].values[:len(rc_df)]
                rc_results = analyze_root_cause_correlations(rc_df, category_col="_norm_category")
            else:
                rc_results = analyze_root_cause_correlations(rc_df)
            rc_summary = generate_correlation_summary(rc_results)

        # Summary metrics
        rc1, rc2, rc3, rc4 = st.columns(4)
        with rc1:
            st.markdown(f"""<div class="metric-card"><div class="metric-value" style="color:#ff9f43;">{rc_summary['total_chains']}</div><div class="metric-label">Failure Chains</div></div>""", unsafe_allow_html=True)
        with rc2:
            st.markdown(f"""<div class="metric-card"><div class="metric-value" style="color:#ff4d6a;">{rc_summary['total_repeats']}</div><div class="metric-label">Repeat Failures</div></div>""", unsafe_allow_html=True)
        with rc3:
            st.markdown(f"""<div class="metric-card"><div class="metric-value" style="color:#3d8bfd;">{rc_summary['total_co_occurrences']}</div><div class="metric-label">Co-Occurring</div></div>""", unsafe_allow_html=True)
        with rc4:
            st.markdown(f"""<div class="metric-card"><div class="metric-value" style="color:#00e68a;">{rc_summary['total_cascades']}</div><div class="metric-label">Cascade Patterns</div></div>""", unsafe_allow_html=True)

        # Insights
        for insight in rc_results.get("insights", []):
            i_color = "#ff4d6a" if insight["type"] == "critical" else "#ff9f43" if insight["type"] == "warning" else "#3d8bfd"
            st.markdown(f"""
            <div class="insight-box" style="border-left:3px solid {i_color};">
                <strong style="color:{i_color};">{insight['title']}</strong>
                <div style="color:#6b7394;font-size:0.85rem;margin-top:0.3rem;">{insight['detail']}</div>
            </div>
            """, unsafe_allow_html=True)

        # Failure Chains
        if rc_results["failure_chains"]:
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("**Failure Chains** — When A fails, B follows")
            for chain in rc_results["failure_chains"][:8]:
                st.markdown(f"""
                <div class="insight-box">
                    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.3rem;">
                        <div style="font-size:0.9rem;">
                            <strong style="color:#ff9f43;">{chain['first_failure']}</strong>
                            <span style="color:#6b7394;"> → </span>
                            <strong style="color:#ff4d6a;">{chain['second_failure']}</strong>
                        </div>
                        <span style="font-family:'JetBrains Mono';color:#e8eaf0;font-size:0.85rem;">{chain['occurrences']}x</span>
                    </div>
                    <div style="color:#6b7394;font-size:0.8rem;">Average {chain['avg_days_between']} days between failures</div>
                </div>
                """, unsafe_allow_html=True)

        # Repeat Failures
        if rc_results["repeat_failures"]:
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("**Chronic Repeat Failures** — Same asset, same problem, recurring")
            for repeat in rc_results["repeat_failures"][:8]:
                st.markdown(f"""
                <div class="insight-box" style="border-left:3px solid #ff4d6a;">
                    <div style="display:flex;justify-content:space-between;align-items:center;">
                        <div>
                            <strong style="color:#e8eaf0;">{repeat['asset_id']}</strong>
                            <span style="color:#ff9f43;margin-left:0.5rem;">{repeat['category']}</span>
                        </div>
                        <span style="font-family:'JetBrains Mono';color:#ff4d6a;">{repeat['occurrence_count']}x every {repeat['avg_interval_days']} days</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        # Cascade Patterns
        if rc_results["cascade_patterns"]:
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("**Cascade Patterns** — One failure type consistently triggers another")
            for cascade in rc_results["cascade_patterns"][:5]:
                st.markdown(f"""
                <div class="insight-box">
                    <div style="display:flex;justify-content:space-between;align-items:center;">
                        <div style="font-size:0.88rem;">
                            <strong style="color:#ff9f43;">{cascade['cause']}</strong>
                            <span style="color:#6b7394;"> causes </span>
                            <strong style="color:#ff4d6a;">{cascade['effect']}</strong>
                        </div>
                        <span style="font-family:'JetBrains Mono';color:#e8eaf0;">{cascade['cascade_rate']}% rate</span>
                    </div>
                    <div style="color:#6b7394;font-size:0.8rem;">{cascade['interpretation']}</div>
                </div>
                """, unsafe_allow_html=True)

    ''' + export_marker

if "TAB 9: ROOT CAUSE CORRELATION" not in content:
    content = content.replace(export_marker, root_cause_tab)
    print("[3/3] Added Root Cause tab content")
else:
    print("[3/3] Tab content already present")

with open("main_app.py", "w") as f:
    f.write(content)

# Verify
import py_compile
try:
    py_compile.compile("main_app.py", doraise=True)
    print("\n✅ Root Cause Correlation integrated!")
    print("   - 9 tabs total")
    print("   - Failure chains (A triggers B)")
    print("   - Repeat failures (chronic problems)")
    print("   - Co-occurring failures (shared root cause)")
    print("   - Cascade patterns (cause-effect rates)")
except py_compile.PyCompileError as e:
    print(f"\n❌ Syntax error: {e}")
