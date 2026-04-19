"""
MaintSignal - main_app.py Upgrade Script
Adds Compliance, Trends, and Knowledge Capture tabs to the Streamlit dashboard.
Run: python upgrade_app.py
"""

# Read current main_app.py
with open("main_app.py", "r") as f:
    content = f.read()

# 1. ADD NEW IMPORTS after existing imports
old_imports = "from smart_normalizer import SmartNormalizer"
new_imports = """from smart_normalizer import SmartNormalizer
from compliance_checker import analyze_compliance_gaps, generate_compliance_summary, COMPLIANCE_FRAMEWORKS, detect_industry_frameworks
from trend_analyzer import analyze_trends, generate_trend_summary
from knowledge_capture import extract_abbreviations, extract_equipment_patterns, generate_failure_code_library, analyze_knowledge_gaps, generate_quick_reference_card"""

if "compliance_checker" not in content:
    content = content.replace(old_imports, new_imports)
    print("[1/4] Added new imports")
else:
    print("[1/4] Imports already present, skipping")

# 2. CHANGE TABS FROM 5 TO 8
old_tabs = '''    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📋 Data Quality", "🏭 Problem Assets", "🧠 Failure Analysis",
        f"💰 Financial Impact", "✅ Recommendations"
    ])'''

new_tabs = '''    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
        "📋 Data Quality", "🏭 Problem Assets", "🧠 Failure Analysis",
        f"💰 Financial Impact", "✅ Recommendations",
        "🔍 Compliance Audit", "📈 Trends", "📚 Knowledge Capture"
    ])'''

if "tab6, tab7, tab8" not in content:
    content = content.replace(old_tabs, new_tabs)
    print("[2/4] Upgraded tabs from 5 to 8")
else:
    print("[2/4] Tabs already upgraded, skipping")

# 3. ADD NEW TAB CONTENTS before the EXPORT section
old_export = '''    # ============================================================
    # EXPORT
    # ============================================================'''

new_tab_code = '''    # ============================================================
    # TAB 6: COMPLIANCE AUDIT
    # ============================================================
    with tab6:
        st.markdown('<div class="sec-label">Compliance Audit</div>', unsafe_allow_html=True)
        st.markdown('<div class="sec-title">Regulatory Gap Analysis</div>', unsafe_allow_html=True)

        # Map industry selection to compliance industry
        compliance_industry_map = {
            "pharmaceutical": "pharmaceutical",
            "food_and_beverage": "food_and_beverage",
            "oil_and_gas": "oil_and_gas",
            "automotive": "automotive_manufacturing",
            "general_manufacturing": "general_manufacturing",
        }
        comp_industry = compliance_industry_map.get(selected_industry, "general_manufacturing")

        with st.spinner("Running compliance gap analysis..."):
            comp_results = analyze_compliance_gaps(df, industry=comp_industry)
            comp_summary = generate_compliance_summary(comp_results)

        # Overall compliance score
        comp_color = "#00e68a" if comp_summary["score"] >= 85 else "#ff9f43" if comp_summary["score"] >= 65 else "#ff4d6a"
        st.markdown(f"""
        <div class="insight-box" style="border-left:3px solid {comp_color};">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.5rem;">
                <div>
                    <strong style="font-size:1.1rem;color:#e8eaf0;">Overall Compliance Score</strong>
                    <span style="margin-left:1rem;background:{comp_color}22;color:{comp_color};padding:0.2rem 0.6rem;border-radius:4px;font-size:0.75rem;font-weight:700;">{comp_summary['risk_label']}</span>
                </div>
                <span style="font-family:'JetBrains Mono';font-size:1.8rem;font-weight:900;color:{comp_color};">{comp_summary['score']}%</span>
            </div>
            <div style="color:#6b7394;font-size:0.88rem;">{comp_summary['summary']}</div>
        </div>
        """, unsafe_allow_html=True)

        # Framework details
        for fw in comp_results["frameworks_checked"]:
            fw_color = "#00e68a" if fw["score"] >= 85 else "#ff9f43" if fw["score"] >= 65 else "#ff4d6a"
            with st.expander(f"{fw['name']} — {fw['score']}% ({fw['risk_level']} risk)", expanded=True):
                # Field scores
                for field, score in fw["field_scores"].items():
                    s_color = "#00e68a" if score["status"] == "pass" else "#ff9f43" if score["status"] == "warning" else "#ff4d6a"
                    icon = "✓" if score["status"] == "pass" else "!" if score["status"] == "warning" else "✗"
                    st.markdown(f"""
                    <div style="margin-bottom:0.6rem;">
                        <div style="display:flex;justify-content:space-between;font-size:0.85rem;margin-bottom:0.2rem;">
                            <span style="color:#e8eaf0;">{icon} {score['label']}</span>
                            <span style="font-family:'JetBrains Mono';color:{s_color};">{score['completeness']}%</span>
                        </div>
                        <div style="height:4px;background:#1c2436;border-radius:2px;overflow:hidden;">
                            <div style="height:100%;width:{score['completeness']}%;background:{s_color};border-radius:2px;"></div>
                        </div>
                        <div style="font-size:0.72rem;color:#6b7394;margin-top:0.15rem;">{score['reason']}</div>
                    </div>
                    """, unsafe_allow_html=True)

                # Check results
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown("**Compliance Checks**")
                for check in fw["check_results"]:
                    c_color = "#00e68a" if check["status"] == "pass" else "#ff9f43" if check["status"] == "warning" else "#ff4d6a"
                    c_icon = "✓" if check["status"] == "pass" else "!" if check["status"] == "warning" else "✗"
                    st.markdown(f"""
                    <div class="insight-box" style="padding:0.6rem 1rem;border-left:2px solid {c_color};">
                        <strong style="color:{c_color};font-size:0.85rem;">{c_icon} {check['name']}</strong>
                        <div style="color:#6b7394;font-size:0.8rem;">{check['finding']}</div>
                    </div>
                    """, unsafe_allow_html=True)

        # Remediation actions
        if comp_results["remediation_actions"]:
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("**Priority Remediation Actions**")
            for action in comp_results["remediation_actions"][:8]:
                a_color = "#ff4d6a" if action["priority"] == "HIGH" else "#ff9f43"
                st.markdown(f"""
                <div class="insight-box">
                    <div style="display:flex;align-items:center;gap:0.6rem;margin-bottom:0.3rem;">
                        <span class="tag" style="background:{a_color}22;color:{a_color};">{action['priority']}</span>
                        <strong style="color:#e8eaf0;font-size:0.9rem;">{action['action']}</strong>
                    </div>
                    <div style="color:#6b7394;font-size:0.82rem;">Current: {action['current']} | Target: {action['target']}</div>
                    <div style="color:#00e68a;font-size:0.78rem;margin-top:0.2rem;">Why: {action['reason']}</div>
                </div>
                """, unsafe_allow_html=True)

    # ============================================================
    # TAB 7: TREND ANALYSIS
    # ============================================================
    with tab7:
        st.markdown('<div class="sec-label">Trend Analysis</div>', unsafe_allow_html=True)
        st.markdown('<div class="sec-title">Patterns Over Time</div>', unsafe_allow_html=True)

        with st.spinner("Analyzing trends..."):
            trend_results = analyze_trends(df, date_col="created_date", period="monthly")
            trend_summary = generate_trend_summary(trend_results)

        if "error" in trend_results:
            st.warning(f"Trend analysis limited: {trend_results['error']}")
        else:
            # Date range info
            dr = trend_results.get("date_range", {})
            st.markdown(f"""
            <div class="insight-box success">
                📈 Data spans <strong>{dr.get('span_days', 0)} days</strong>
                ({dr.get('start', '')} to {dr.get('end', '')}) across
                <strong>{dr.get('num_periods', 0)} periods</strong>
            </div>
            """, unsafe_allow_html=True)

            # Alerts
            for alert in trend_results.get("alerts", []):
                a_color = "#ff4d6a" if alert.get("severity") == "critical" else "#ff9f43"
                st.markdown(f"""
                <div class="insight-box" style="border-left:3px solid {a_color};">
                    <strong style="color:{a_color};">⚠ {alert['title']}</strong>
                    <div style="color:#6b7394;font-size:0.85rem;">{alert['detail']}</div>
                </div>
                """, unsafe_allow_html=True)

            # Insights
            for insight in trend_results.get("insights", []):
                i_color = "#00e68a" if insight["type"] == "positive" else "#3d8bfd"
                st.markdown(f"""
                <div class="insight-box" style="border-left:3px solid {i_color};">
                    <strong style="color:{i_color};">💡 {insight['title']}</strong>
                    <div style="color:#6b7394;font-size:0.85rem;">{insight['detail']}</div>
                </div>
                """, unsafe_allow_html=True)

            # Volume by period chart
            if trend_results.get("failure_trends", {}).get("volume"):
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown("**Work Order Volume by Period**")
                vol = trend_results["failure_trends"]["volume"]
                vol_df = pd.DataFrame(list(vol.items()), columns=["Period", "Count"])
                st.bar_chart(vol_df.set_index("Period"))

            # PM Ratio trend
            if trend_results.get("failure_trends", {}).get("pm_ratio"):
                st.markdown("**Planned vs Reactive Maintenance Ratio**")
                pm = trend_results["failure_trends"]["pm_ratio"]
                pm_df = pd.DataFrame(list(pm.items()), columns=["Period", "PM Ratio %"])
                st.line_chart(pm_df.set_index("Period"))

            # Deteriorating assets
            deteriorating = trend_results.get("asset_trends", {}).get("deteriorating", [])
            if deteriorating:
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown("**⚠ Deteriorating Assets** (failure rate increasing)")
                for asset in deteriorating[:5]:
                    st.markdown(f"""
                    <div class="insight-box critical">
                        <strong style="color:#e8eaf0;">{asset['asset_id']}</strong>
                        <span style="color:#ff4d6a;margin-left:1rem;">+{asset['change_pct']}% increase</span>
                        <div style="color:#6b7394;font-size:0.82rem;">
                            Early avg: {asset['early_avg']} failures/period → Recent avg: {asset['recent_avg']} failures/period
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

            # Improving assets
            improving = trend_results.get("asset_trends", {}).get("improving", [])
            if improving:
                st.markdown("**✓ Improving Assets** (failure rate decreasing)")
                for asset in improving[:5]:
                    st.markdown(f"""
                    <div class="insight-box success">
                        <strong style="color:#e8eaf0;">{asset['asset_id']}</strong>
                        <span style="color:#00e68a;margin-left:1rem;">{asset['change_pct']}% decrease</span>
                        <div style="color:#6b7394;font-size:0.82rem;">
                            Early avg: {asset['early_avg']} failures/period → Recent avg: {asset['recent_avg']} failures/period
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

            # Seasonal patterns
            seasonal = trend_results.get("seasonal_patterns", {})
            if seasonal:
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown("**Seasonal Failure Patterns**")
                season_data = []
                for month_num, data in sorted(seasonal.items()):
                    season_data.append({
                        "Month": data["month_name"][:3],
                        "Failures": data["count"],
                        "vs Average": f"{data['vs_average']:+.0f}%",
                    })
                st.dataframe(pd.DataFrame(season_data), use_container_width=True, hide_index=True)

    # ============================================================
    # TAB 8: KNOWLEDGE CAPTURE
    # ============================================================
    with tab8:
        st.markdown('<div class="sec-label">Knowledge Capture</div>', unsafe_allow_html=True)
        st.markdown('<div class="sec-title">Organizational Knowledge Extraction</div>', unsafe_allow_html=True)

        with st.spinner("Extracting knowledge from work order history..."):
            descriptions = df["description"].astype(str).tolist() if "description" in df.columns else []
            abbrevs = extract_abbreviations(descriptions)
            patterns = extract_equipment_patterns(df, desc_col="description", asset_col="asset_id")
            failure_library = generate_failure_code_library(df, industry=selected_industry, desc_col="description")
            knowledge_gaps = analyze_knowledge_gaps(df, desc_col="description")

        # Knowledge gaps overview
        st.markdown(f"""
        <div class="insight-box warning">
            <strong style="color:#ff9f43;">Knowledge Gap Analysis</strong>
            <div style="display:flex;gap:2rem;margin-top:0.5rem;flex-wrap:wrap;">
                <div style="text-align:center;">
                    <div style="font-family:'JetBrains Mono';font-size:1.4rem;font-weight:900;color:#ff4d6a;">{knowledge_gaps['vague_percentage']}%</div>
                    <div style="font-size:0.75rem;color:#6b7394;">Vague Descriptions</div>
                </div>
                <div style="text-align:center;">
                    <div style="font-family:'JetBrains Mono';font-size:1.4rem;font-weight:900;color:#ff9f43;">{knowledge_gaps['short_percentage']}%</div>
                    <div style="font-size:0.75rem;color:#6b7394;">Too Short (&lt;10 chars)</div>
                </div>
                <div style="text-align:center;">
                    <div style="font-family:'JetBrains Mono';font-size:1.4rem;font-weight:900;color:#ff4d6a;">{knowledge_gaps['no_cause_percentage']}%</div>
                    <div style="font-size:0.75rem;color:#6b7394;">No Root Cause</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Recommended failure code library
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("**Recommended Failure Code Library**")
        st.markdown(f"""
        <div class="insight-box success">
            <strong style="color:#00e68a;">Recommendation:</strong>
            <span style="color:#a8b0c8;font-size:0.88rem;"> {failure_library['recommendation']}</span>
            <div style="margin-top:0.4rem;font-size:0.82rem;color:#6b7394;">
                Coverage: {failure_library['coverage']}% of work orders categorized into {failure_library['total_codes']} codes
            </div>
        </div>
        """, unsafe_allow_html=True)

        for code in failure_library.get("recommended_codes", [])[:12]:
            if code["category"] == "Other / Unclassified":
                continue
            pct = code["percentage"]
            color = "#00e68a" if "Preventive" in code["category"] else "#ff9f43"
            st.markdown(f"""
            <div class="insight-box" style="padding:0.6rem 1rem;">
                <div style="display:flex;justify-content:space-between;align-items:center;">
                    <div>
                        <span style="font-family:'JetBrains Mono';color:{color};font-weight:700;font-size:0.82rem;">{code['code']}</span>
                        <span style="color:#e8eaf0;margin-left:0.8rem;">{code['category']}</span>
                    </div>
                    <span style="font-family:'JetBrains Mono';color:#6b7394;font-size:0.82rem;">{code['frequency']} WOs ({pct}%)</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # Discovered abbreviations
        if abbrevs:
            st.markdown("<br>", unsafe_allow_html=True)
            with st.expander("📖 Discovered Abbreviations", expanded=False):
                for a in abbrevs[:20]:
                    status = "Known" if a["known"] else "NEW"
                    s_color = "#00e68a" if a["known"] else "#ff9f43"
                    st.markdown(f"""
                    <div style="display:flex;justify-content:space-between;padding:0.4rem 0;border-bottom:1px solid #1c2436;font-size:0.85rem;">
                        <div>
                            <span style="font-family:'JetBrains Mono';color:#e8eaf0;font-weight:700;">{a['abbreviation']}</span>
                            <span style="color:#6b7394;margin-left:1rem;">= {a['expansion']}</span>
                        </div>
                        <div>
                            <span style="color:#6b7394;">{a['frequency']}x</span>
                            <span style="color:{s_color};margin-left:0.5rem;font-size:0.75rem;">[{status}]</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

        # Equipment work patterns
        if patterns:
            st.markdown("<br>", unsafe_allow_html=True)
            with st.expander("🔧 Equipment Work Patterns", expanded=False):
                for p in patterns[:5]:
                    st.markdown(f"""
                    <div class="insight-box" style="margin-bottom:0.5rem;">
                        <strong style="color:#e8eaf0;">Equipment Type: {p['equipment_type']}</strong>
                        <span style="color:#6b7394;margin-left:1rem;">{p['total_work_orders']} WOs, {p['unique_descriptions']} unique descriptions</span>
                    </div>
                    """, unsafe_allow_html=True)
                    for task in p["top_tasks"][:5]:
                        st.markdown(f"""
                        <div style="padding:0.3rem 1rem;font-size:0.82rem;color:#6b7394;">
                            "{task['description']}" — <strong style="color:#e8eaf0;">{task['count']}x</strong> ({task['percentage']}%)
                        </div>
                        """, unsafe_allow_html=True)

    # ============================================================
    # EXPORT
    # ============================================================'''

if "TAB 6: COMPLIANCE AUDIT" not in content:
    content = content.replace(old_export, new_tab_code + "\n" + old_export)
    print("[3/4] Added 3 new tab contents")
else:
    print("[3/4] Tab contents already present, skipping")

# 4. ADD NEW DATA TO EXCEL EXPORT
old_excel_end = '''        if ingestion.raw_df is not None:
            ingestion.raw_df.head(5000).to_excel(writer, sheet_name="Raw Data", index=False)'''

new_excel_end = '''        if ingestion.raw_df is not None:
            ingestion.raw_df.head(5000).to_excel(writer, sheet_name="Raw Data", index=False)

        # New v2 modules
        try:
            comp_data = []
            for fw in comp_results.get("frameworks_checked", []):
                for field, score in fw.get("field_scores", {}).items():
                    comp_data.append({
                        "Framework": fw["name"],
                        "Field": score["label"],
                        "Completeness": f"{score['completeness']}%",
                        "Status": score["status"].upper(),
                        "Reason": score["reason"],
                    })
            if comp_data:
                pd.DataFrame(comp_data).to_excel(writer, sheet_name="Compliance Audit", index=False)
        except:
            pass

        try:
            if failure_library.get("recommended_codes"):
                codes_df = pd.DataFrame(failure_library["recommended_codes"])
                codes_df.to_excel(writer, sheet_name="Failure Code Library", index=False)
        except:
            pass

        try:
            gaps_data = {
                "Metric": ["Vague Descriptions", "Too Short (<10 chars)", "No Root Cause Indicated", "Total Analyzed"],
                "Count": [knowledge_gaps["generic_actions"], knowledge_gaps["too_short"],
                          knowledge_gaps["no_root_cause"], knowledge_gaps["total_analyzed"]],
                "Percentage": [f"{knowledge_gaps['vague_percentage']}%", f"{knowledge_gaps['short_percentage']}%",
                               f"{knowledge_gaps['no_cause_percentage']}%", "100%"],
            }
            pd.DataFrame(gaps_data).to_excel(writer, sheet_name="Knowledge Gaps", index=False)
        except:
            pass'''

if "Compliance Audit" not in content.split("ExcelWriter")[1] if "ExcelWriter" in content else True:
    content = content.replace(old_excel_end, new_excel_end)
    print("[4/4] Added new data to Excel export")
else:
    print("[4/4] Excel export already upgraded, skipping")

# Write the upgraded file
with open("main_app.py", "w") as f:
    f.write(content)

print("\n✅ main_app.py upgraded successfully!")
print("   - 3 new imports added")
print("   - 8 tabs (was 5)")
print("   - Compliance Audit tab")
print("   - Trend Analysis tab with charts")
print("   - Knowledge Capture tab")
print("   - Excel export includes compliance + knowledge data")
print("\nRun: streamlit run main_app.py")
