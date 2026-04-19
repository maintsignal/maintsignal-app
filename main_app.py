"""
MaintSignal — Prototype v2
Multi-format, multi-industry maintenance intelligence tool.
Accepts CSV, Excel, PDF. Works for any industry. Smart LLM normalization.

Run: streamlit run main_app.py
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import io
import json

from knowledge_base import INDUSTRY_TAXONOMIES, get_failure_taxonomy, GLOBAL_ABBREVIATIONS
from data_ingestion import DataIngestor, IngestionResult
from smart_normalizer import SmartNormalizer
from industry_benchmarking import calculate_client_metrics, benchmark_against_industry, INDUSTRY_BENCHMARKS
from root_cause_correlation import analyze_root_cause_correlations, generate_correlation_summary
from compliance_checker import analyze_compliance_gaps, generate_compliance_summary, COMPLIANCE_FRAMEWORKS, detect_industry_frameworks
from trend_analyzer import analyze_trends, generate_trend_summary
from knowledge_capture import extract_abbreviations, extract_equipment_patterns, generate_failure_code_library, analyze_knowledge_gaps, generate_quick_reference_card


# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="MaintSignal — Maintenance Intelligence",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# CUSTOM STYLING
# ============================================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;700&display=swap');
    .stApp { background-color: #06080d; }
    section[data-testid="stSidebar"] { background-color: #0c0f17; }
    .main-header { font-family: 'Outfit', sans-serif; font-size: 2rem; font-weight: 800; color: #e8eaf0; letter-spacing: -1px; margin-bottom: 0.2rem; }
    .accent { color: #00e68a; }
    .subtitle { font-size: 1rem; color: #6b7394; margin-bottom: 1.5rem; }
    .metric-card { background: #111621; border: 1px solid #1c2436; border-radius: 12px; padding: 1.3rem; text-align: center; }
    .metric-val { font-family: 'JetBrains Mono', monospace; font-size: 1.8rem; font-weight: 700; }
    .metric-label { font-size: 0.8rem; color: #6b7394; margin-top: 0.2rem; }
    .good { color: #00e68a; }
    .warn { color: #ff9f43; }
    .bad { color: #ff4d6a; }
    .sec-label { font-family: 'JetBrains Mono', monospace; font-size: 0.72rem; color: #00e68a; text-transform: uppercase; letter-spacing: 2.5px; margin-bottom: 0.4rem; }
    .sec-title { font-family: 'Outfit', sans-serif; font-size: 1.3rem; font-weight: 700; color: #e8eaf0; margin-bottom: 0.8rem; }
    .insight-box { background: #111621; border: 1px solid #1c2436; border-radius: 10px; padding: 1rem 1.2rem; margin-bottom: 0.6rem; }
    .insight-box.critical { border-left: 3px solid #ff4d6a; }
    .insight-box.warning { border-left: 3px solid #ff9f43; }
    .insight-box.success { border-left: 3px solid #00e68a; }
    .mapping-row { display: flex; align-items: center; gap: 0.8rem; padding: 0.5rem 0.8rem; background: #111621; border: 1px solid #1c2436; border-radius: 8px; margin-bottom: 0.4rem; font-size: 0.85rem; }
    .mapping-arrow { color: #00e68a; font-weight: 700; }
    .tag { display: inline-block; padding: 0.15rem 0.5rem; border-radius: 4px; font-size: 0.7rem; font-family: 'JetBrains Mono', monospace; font-weight: 600; }
    .tag-green { background: rgba(0,230,138,0.1); color: #00e68a; }
    .tag-orange { background: rgba(255,159,67,0.1); color: #ff9f43; }
    .tag-red { background: rgba(255,77,106,0.1); color: #ff4d6a; }
    .tag-blue { background: rgba(77,148,255,0.1); color: #4d94ff; }
    hr { border-color: #1c2436; }
</style>
""", unsafe_allow_html=True)


# ============================================================
# SIDEBAR — CONFIGURATION
# ============================================================
with st.sidebar:
    st.markdown("### ⚙️ Configuration")
    st.markdown("---")

    # Industry selection
    industry_options = {
        "general_manufacturing": "🏭 General Manufacturing",
        "pharmaceutical": "💊 Pharmaceutical",
        "food_and_beverage": "🍔 Food & Beverage",
        "oil_and_gas": "🛢️ Oil & Gas",
        "automotive_manufacturing": "🚗 Automotive",
    }
    selected_industry = st.selectbox(
        "Plant Industry",
        options=list(industry_options.keys()),
        format_func=lambda x: industry_options[x],
        help="Select the client's industry for specialized failure taxonomy and terminology"
    )

    st.markdown("---")

    # Production value
    prod_value = st.number_input(
        "Production Value ($/hour)",
        min_value=500, max_value=500000, value=10000, step=500,
        help="Estimated production output value per hour — used for financial impact calculation"
    )

    # Currency
    currency = st.selectbox(
        "Currency", ["USD ($)", "EUR (€)", "GBP (£)", "INR (₹)", "CAD (C$)", "AUD (A$)"],
        help="Display currency for financial figures"
    )
    currency_symbol = currency.split("(")[1].replace(")", "")

    st.markdown("---")

    # Normalization mode
    norm_mode = st.radio(
        "AI Normalization Mode",
        ["Offline (Free)", "Online (Claude API)", "Hybrid (Smart)"],
        help="Offline uses keyword matching. Online uses Claude API for best results. Hybrid uses keywords first, then LLM for uncertain cases."
    )
    mode_map = {"Offline (Free)": "offline", "Online (Claude API)": "online", "Hybrid (Smart)": "hybrid"}
    selected_mode = mode_map[norm_mode]

    api_key = ""
    if selected_mode in ["online", "hybrid"]:
        api_key = st.text_input("Anthropic API Key", type="password",
                                 help="Get your key at console.anthropic.com")

    st.markdown("---")

    # Client info (for report generation)
    st.markdown("**Client Details** (for report)")
    client_name = st.text_input("Company Name", value="", placeholder="Acme Manufacturing")
    plant_name = st.text_input("Plant / Site Name", value="", placeholder="Houston Plant")

    st.markdown("---")
    st.markdown(
        '<div style="font-size: 0.75rem; color: #6b7394; text-align: center;">'
        'MaintSignal v2.0 Prototype<br>Works with any maintenance system'
        '</div>',
        unsafe_allow_html=True
    )


# ============================================================
# ANALYSIS FUNCTIONS
# ============================================================

def analyze_data_quality(df):
    """Run data quality analysis on normalized DataFrame."""
    total = len(df)
    results = {}

    # Completeness per field
    check_fields = {
        "asset_id": "Equipment/Asset ID",
        "location": "Functional Location",
        "failure_code": "Failure Code",
        "cause_code": "Cause Code",
        "downtime_start": "Downtime Start Time",
        "downtime_end": "Downtime End Time",
        "description": "Work Description",
        "labor_hours": "Labor Hours",
        "cost": "Recorded Cost",
    }

    completeness = {}
    for col, label in check_fields.items():
        if col in df.columns:
            if df[col].dtype == 'datetime64[ns]':
                filled = df[col].notna().sum()
            else:
                filled = df[col].astype(str).str.strip().replace("", np.nan).notna().sum()
            completeness[label] = round((filled / total) * 100, 1)

    results["completeness"] = completeness
    results["avg_completeness"] = round(np.mean(list(completeness.values())), 1) if completeness else 0

    # Consistency checks
    issues = []
    if "created_date" in df.columns and "completed_date" in df.columns:
        valid = df.dropna(subset=["created_date", "completed_date"])
        backwards = valid[valid["completed_date"] < valid["created_date"]]
        if len(backwards) > 0:
            issues.append({"issue": "Completion date before creation date",
                          "count": len(backwards), "severity": "critical"})

    if "order_id" in df.columns:
        dupes = df[df.duplicated(subset=["order_id"], keep=False)]
        if len(dupes) > 0:
            issues.append({"issue": "Duplicate work orders",
                          "count": len(dupes), "severity": "warning"})

    results["consistency_issues"] = issues
    total_issues = sum(i["count"] for i in issues)
    results["consistency_score"] = round(max(0, (1 - total_issues / max(total, 1)) * 100), 1)

    # Usability
    usability = 100
    if "failure_code" in df.columns:
        filled = df[df["failure_code"].astype(str).str.strip() != ""]
        if len(filled) > 0:
            generic = filled[filled["failure_code"].str.upper().isin(
                ["OTHER", "UNKNOWN", "MISC", "GENERAL", "NA", "N/A"])].shape[0]
            usability = round((1 - generic / len(filled)) * 100, 1)
    results["usability_score"] = usability

    results["overall_score"] = round(
        results["avg_completeness"] * 0.4 +
        results["consistency_score"] * 0.3 +
        results["usability_score"] * 0.3, 1)

    return results


def analyze_downtime(df):
    """Analyze downtime patterns by asset."""
    # Identify breakdown orders
    if "order_type" in df.columns:
        type_col = df["order_type"].astype(str).str.lower()
        breakdowns = df[
            type_col.str.contains("breakdown|pm01|corrective|emergency|unplanned|cm|bd",
                                   na=False, regex=True)
        ].copy()
        if len(breakdowns) == 0:
            breakdowns = df.copy()
    else:
        breakdowns = df.copy()

    if "asset_id" not in df.columns:
        return {"top_assets": [], "total_breakdowns": 0, "total_downtime_hours": 0}

    breakdowns = breakdowns[breakdowns["asset_id"].astype(str).str.strip() != ""]

    metrics = []
    for aid in breakdowns["asset_id"].unique():
        adata = breakdowns[breakdowns["asset_id"] == aid]
        fc = len(adata)
        dt_hours = 0

        # Try malfunction times
        if "downtime_start" in adata.columns and "downtime_end" in adata.columns:
            for _, row in adata.iterrows():
                try:
                    if pd.notna(row["downtime_start"]) and pd.notna(row["downtime_end"]):
                        diff = (row["downtime_end"] - row["downtime_start"]).total_seconds() / 3600
                        if 0 < diff < 720:
                            dt_hours += diff
                except:
                    pass

        # Fallback to labor hours
        if dt_hours == 0 and "labor_hours" in adata.columns:
            dt_hours = adata["labor_hours"].sum()

        name = ""
        if "asset_name" in adata.columns:
            names = adata["asset_name"].astype(str).replace("", np.nan).dropna().unique()
            name = names[0] if len(names) > 0 else aid

        cost = adata["cost"].sum() if "cost" in adata.columns else 0

        metrics.append({
            "asset_id": aid,
            "asset_name": name if name else aid,
            "failure_count": fc,
            "total_downtime_hours": round(dt_hours, 1),
            "mttr_hours": round(dt_hours / fc, 1) if fc > 0 else 0,
            "actual_cost": round(cost, 2),
        })

    metrics.sort(key=lambda x: x["total_downtime_hours"], reverse=True)

    return {
        "top_assets": metrics[:10],
        "total_breakdowns": len(breakdowns),
        "total_downtime_hours": round(sum(m["total_downtime_hours"] for m in metrics), 1),
    }


def score_color(score):
    if score >= 75: return "good"
    if score >= 55: return "warn"
    return "bad"


def render_metric(value, label, css_class=""):
    st.markdown(f'<div class="metric-card"><div class="metric-val {css_class}">{value}</div><div class="metric-label">{label}</div></div>', unsafe_allow_html=True)


# ============================================================
# MAIN APP
# ============================================================

st.markdown('<div class="main-header">⚡ Maint<span class="accent">Signal</span></div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Upload maintenance data from any system. Get intelligence in seconds.</div>', unsafe_allow_html=True)

# File upload
st.markdown('<div class="sec-label">Step 1</div>', unsafe_allow_html=True)
st.markdown('<div class="sec-title">Upload Your Plant Data</div>', unsafe_allow_html=True)

col_up, col_info = st.columns([3, 1])
with col_up:
    uploaded = st.file_uploader(
        "Drop your file here — CSV, Excel, or PDF",
        type=["csv", "xlsx", "xls", "xlsm", "pdf"],
        help="We accept work order exports from any maintenance system: SAP, Maximo, Oracle, MaintainX, UpKeep, Fiix, or any spreadsheet."
    )
with col_info:
    st.markdown("<br>", unsafe_allow_html=True)
    use_demo = st.button("🔬 Try Demo Data", use_container_width=True)

# Process data
if uploaded or use_demo:
    ingestor = DataIngestor()

    if uploaded:
        # Save uploaded file temporarily
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded.name)[1]) as tmp:
            tmp.write(uploaded.getvalue())
            tmp_path = tmp.name

        with st.spinner(f"Reading {uploaded.name}..."):
            import os
            ingestion = ingestor.load_file(tmp_path)
        os.unlink(tmp_path)

        if ingestion.raw_df is None:
            st.error("Could not read the file. " + " ".join(ingestion.warnings))
            st.stop()

        st.success(f"Loaded **{ingestion.record_count:,}** records from **{uploaded.name}** ({ingestion.file_type.upper()})")

    else:
        # Generate demo data
        with st.spinner("Generating synthetic plant data..."):
            import sys
            sys.path.insert(0, ".")
            try:
                from generate_data import generate_data
                demo_df = generate_data(2000)
            except ImportError:
                # Fallback: create minimal demo data inline
                np.random.seed(42)
                import random
                records = []
                equips = ["P-101", "P-102", "C-301", "C-302", "K-201", "M-105", "M-106", "V-501", "HX-401"]
                descs = [
                    "pump leaking from seal area", "replaced mech seal", "BRG noise on conveyor",
                    "motor overheating tripped on O/L", "VLV stuck open replaced actuator",
                    "XMTR reading erratic recal", "PM inspection all ok", "belt tracking off adjusted",
                    "seal leak repaired", "bearing replaced DE side", "MTR vibration high",
                    "performed routine maintenance", "replaced PRV lifting early",
                    "pump cavitating low suction", "CKT BKR tripped reset",
                ]
                for i in range(2000):
                    eid = random.choice(equips)
                    ot = random.choice(["PM01", "PM01", "PM02", "PM02", "PM03"])
                    created = datetime(2024, 1, 1) + pd.Timedelta(days=random.randint(0, 730))
                    records.append({
                        "Order_Number": f"40{100000+i}", "Equipment_ID": eid if random.random() > 0.15 else "",
                        "Equipment_Name": eid, "Order_Type": ot,
                        "Priority": random.choice(["1-Emergency", "2-Urgent", "3-Normal", "4-Low"]),
                        "Created_Date": created.strftime("%Y-%m-%d"),
                        "Completed_Date": (created + pd.Timedelta(days=random.randint(0, 14))).strftime("%Y-%m-%d"),
                        "Short_Text": random.choice(descs),
                        "Damage_Code": random.choice(["MECH-WEAR", "MECH-LEAK", "ELEC-SHORT", "OTHER", "", "", ""]),
                        "Cause_Code": random.choice(["AGING", "OVERLOAD", "UNKNOWN", "", "", ""]),
                        "Actual_Hours": round(random.uniform(0.5, 16), 1),
                        "Actual_Cost": round(random.uniform(100, 8000), 2),
                        "Status": "COMPLETED",
                    })
                demo_df = pd.DataFrame(records)

            # Create temp file and ingest
            import tempfile, os
            with tempfile.NamedTemporaryFile(delete=False, suffix=".csv", mode="w") as f:
                demo_df.to_csv(f, index=False)
                tmp_path = f.name
            ingestion = ingestor.load_file(tmp_path)
            os.unlink(tmp_path)

        st.success(f"Loaded **{ingestion.record_count:,}** synthetic work orders")
        st.info("Demo data with intentional quality issues to showcase analysis.", icon="ℹ️")

    # ============================================================
    # STEP 2: SHOW COLUMN MAPPING
    # ============================================================
    st.markdown("---")
    st.markdown('<div class="sec-label">Step 2 — Auto-Detected</div>', unsafe_allow_html=True)
    st.markdown('<div class="sec-title">Column Mapping</div>', unsafe_allow_html=True)

    with st.expander("📋 View Column Mapping", expanded=False):
        if ingestion.mapping:
            for original, standard in sorted(ingestion.mapping.items()):
                st.markdown(f"""
                <div class="mapping-row">
                    <span style="color:#6b7394; min-width:200px;">{original}</span>
                    <span class="mapping-arrow">→</span>
                    <span style="color:#e8eaf0;">{standard}</span>
                    <span class="tag tag-green">auto</span>
                </div>
                """, unsafe_allow_html=True)

        if ingestion.unmapped_columns:
            st.markdown(f"**{len(ingestion.unmapped_columns)} unmapped columns** (not used in analysis)")
            for col in ingestion.unmapped_columns[:10]:
                st.markdown(f"""
                <div class="mapping-row">
                    <span style="color:#6b7394;">{col}</span>
                    <span class="mapping-arrow" style="color:#ff4d6a;">✗</span>
                    <span style="color:#ff4d6a;">unmapped</span>
                </div>
                """, unsafe_allow_html=True)

    if ingestion.warnings:
        with st.expander("⚠️ Ingestion Warnings", expanded=False):
            for w in ingestion.warnings:
                st.warning(w)

    # ============================================================
    # STEP 3: RUN ANALYSIS
    # ============================================================
    st.markdown("---")
    st.markdown('<div class="sec-label">Step 3</div>', unsafe_allow_html=True)
    st.markdown('<div class="sec-title">Analysis Results</div>', unsafe_allow_html=True)

    df = ingestion.df

    # Run analyses
    with st.spinner("🔍 Analyzing data quality..."):
        quality = analyze_data_quality(df)

    with st.spinner("⚙️ Analyzing downtime patterns..."):
        downtime = analyze_downtime(df)

    st.markdown("🧠 **Normalizing failure descriptions...**")
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
                progress_bar.progress(done / total, text=f"AI processing: {done}/{total} descriptions")
            norm_results = normalizer.normalize(descriptions, progress_callback=update_progress)
            progress_bar.empty()
        else:
            norm_results = normalizer.normalize(descriptions)
        
        norm_summary = normalizer.get_summary(norm_results)
    except Exception as e:
        st.warning(f"AI normalization encountered an error: {str(e)[:100]}. Falling back to offline mode.")
        normalizer = SmartNormalizer(mode="offline", industry=selected_industry)
        descriptions = df["description"].tolist() if "description" in df.columns else []
        norm_results = normalizer.normalize(descriptions)
        norm_summary = normalizer.get_summary(norm_results)

    # Financial calculation
    financial_assets = []
    total_loss = 0
    if downtime.get("top_assets"):
        for a in downtime["top_assets"]:
            loss = round(a["total_downtime_hours"] * prod_value, 2)
            financial_assets.append({**a, "estimated_loss": loss})
            total_loss += loss

    # ============================================================
    # DASHBOARD

    # ============================================================

    # Top metrics
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        render_metric(f"{quality['overall_score']}%", "Data Quality Score",
                      score_color(quality['overall_score']))
    with m2:
        render_metric(f"{downtime.get('total_breakdowns', 0):,}", "Breakdown Orders", "warn")
    with m3:
        render_metric(f"{downtime.get('total_downtime_hours', 0):,.0f} hrs",
                      "Unplanned Downtime", "bad")
    with m4:
        loss_str = f"{currency_symbol}{total_loss/1000000:.1f}M" if total_loss >= 1000000 else f"{currency_symbol}{total_loss:,.0f}"
        render_metric(loss_str, "Est. Production Loss", "bad")

    st.markdown("<br>", unsafe_allow_html=True)

    # Industry badge
    ind_info = INDUSTRY_TAXONOMIES.get(selected_industry, {})
    st.markdown(f"""
    <div style="display:flex; gap:0.8rem; align-items:center; margin-bottom:1rem;">
        <span class="tag tag-blue">{ind_info.get('name', selected_industry)}</span>
        <span class="tag tag-green">{norm_mode}</span>
        <span class="tag tag-orange">{ingestion.file_type.upper()} Import</span>
    </div>
    """, unsafe_allow_html=True)

    # Tabs
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10 = st.tabs([
        "📋 Quality", "🏭 Assets", "🧠 Failures",
        f"💰 Financial", "✅ Actions",
        "🔍 Compliance", "📈 Trends", "📚 Knowledge", "🔗 Root Cause", "📊 Benchmark"
    ])

    with tab1:
        st.markdown('<div class="sec-label">Data Quality</div>', unsafe_allow_html=True)
        st.markdown('<div class="sec-title">Completeness by Field</div>', unsafe_allow_html=True)

        for field, score in sorted(quality.get("completeness", {}).items(), key=lambda x: x[1]):
            color = "#00e68a" if score >= 75 else "#ff9f43" if score >= 55 else "#ff4d6a"
            st.markdown(f"""
            <div style="margin-bottom:0.7rem;">
                <div style="display:flex;justify-content:space-between;font-size:0.85rem;margin-bottom:0.2rem;">
                    <span style="color:#e8eaf0;">{field}</span>
                    <span style="font-family:'JetBrains Mono';color:{color};">{score}%</span>
                </div>
                <div style="height:5px;background:#1c2436;border-radius:3px;overflow:hidden;">
                    <div style="height:100%;width:{score}%;background:{color};border-radius:3px;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        if quality.get("consistency_issues"):
            st.markdown("<br>", unsafe_allow_html=True)
            for issue in quality["consistency_issues"]:
                sev = "critical" if issue["severity"] == "critical" else "warning"
                icon = "🔴" if sev == "critical" else "🟡"
                st.markdown(f'<div class="insight-box {sev}">{icon} <strong>{issue["issue"]}</strong> — {issue["count"]:,} records</div>', unsafe_allow_html=True)

    with tab2:
        st.markdown('<div class="sec-label">Downtime Intelligence</div>', unsafe_allow_html=True)
        st.markdown('<div class="sec-title">Top Problem Assets</div>', unsafe_allow_html=True)

        if financial_assets:
            max_dt = max(a["total_downtime_hours"] for a in financial_assets) or 1
            for a in financial_assets:
                pct = a["total_downtime_hours"] / max_dt * 100
                loss_str = f"{currency_symbol}{a['estimated_loss']:,.0f}"
                st.markdown(f"""
                <div class="insight-box">
                    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.4rem;">
                        <div><strong style="color:#e8eaf0;">{a['asset_id']}</strong>
                        <span style="color:#6b7394;margin-left:0.5rem;">{a['asset_name']}</span></div>
                        <span style="font-family:'JetBrains Mono';color:#ff4d6a;font-weight:700;">{loss_str}</span>
                    </div>
                    <div style="display:flex;gap:2rem;font-size:0.8rem;color:#6b7394;margin-bottom:0.4rem;">
                        <span>Failures: <strong style="color:#e8eaf0">{a['failure_count']}</strong></span>
                        <span>Downtime: <strong style="color:#e8eaf0">{a['total_downtime_hours']} hrs</strong></span>
                        <span>MTTR: <strong style="color:#e8eaf0">{a['mttr_hours']} hrs</strong></span>
                    </div>
                    <div style="height:5px;background:#1c2436;border-radius:3px;overflow:hidden;">
                        <div style="height:100%;width:{pct}%;background:#ff4d6a;border-radius:3px;"></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

    with tab3:
        st.markdown('<div class="sec-label">AI Normalization</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="sec-title">Failure Categories ({ind_info.get("name", "General")})</div>', unsafe_allow_html=True)

        st.markdown(f"""
        <div class="insight-box success">
            🧠 <strong>{norm_summary['total_processed']:,}</strong> descriptions normalized into
            <strong>{norm_summary['categories_found']}</strong> categories
            ({norm_summary['high_confidence']} high confidence,
            {norm_summary['medium_confidence']} medium,
            {norm_summary['low_confidence']} low)
        </div>
        """, unsafe_allow_html=True)

        cat_counts = norm_results["category"].value_counts()
        max_count = cat_counts.max() if not cat_counts.empty else 1

        for cat, count in cat_counts.items():
            pct = count / max_count * 100
            unique_desc = norm_results[norm_results["category"] == cat]["original"].nunique()
            color = "#00e68a" if "Preventive" in str(cat) or "Calibration" in str(cat) else "#ff9f43" if cat != "Unknown" else "#6b7394"
            st.markdown(f"""
            <div class="insight-box">
                <div style="display:flex;justify-content:space-between;margin-bottom:0.3rem;">
                    <strong style="color:{color};">{cat}</strong>
                    <span style="font-family:'JetBrains Mono';color:#e8eaf0;">{count:,} orders</span>
                </div>
                <div style="font-size:0.78rem;color:#6b7394;margin-bottom:0.4rem;">
                    {unique_desc} unique descriptions → 1 standardized category
                </div>
                <div style="height:5px;background:#1c2436;border-radius:3px;overflow:hidden;">
                    <div style="height:100%;width:{pct}%;background:{color};border-radius:3px;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # Show sample normalizations
        with st.expander("🔍 See Individual Normalizations (sample)", expanded=False):
            sample = norm_results[norm_results["original"].astype(str).str.strip() != ""].head(20)
            for _, row in sample.iterrows():
                conf_color = {"high": "#00e68a", "medium": "#ff9f43", "low": "#ff4d6a"}.get(row["confidence"], "#6b7394")
                st.markdown(f"""
                <div class="insight-box" style="padding:0.7rem 1rem;">
                    <div style="font-size:0.82rem;color:#6b7394;margin-bottom:0.2rem;">Original: <span style="color:#e8eaf0;">"{row['original']}"</span></div>
                    {"<div style='font-size:0.82rem;color:#6b7394;margin-bottom:0.2rem;'>Expanded: <span style=color:#00e68a;>" + row['interpretation'][:80] + "</span></div>" if row['interpretation'] and row['interpretation'] != row['original'] else ""}
                    <div style="display:flex;gap:0.8rem;align-items:center;font-size:0.8rem;">
                        <span class="tag tag-blue">{row['category']}</span>
                        <span style="color:#6b7394;">Component: {row['component']}</span>
                        <span style="color:{conf_color};">●  {row['confidence']}</span>
                        <span class="tag tag-green" style="font-size:0.65rem;">{row['method']}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

    with tab4:
        st.markdown('<div class="sec-label">Financial Impact</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="sec-title">Downtime Cost at {currency_symbol}{prod_value:,.0f}/hr</div>', unsafe_allow_html=True)

        st.markdown(f"""
        <div class="insight-box critical">
            💰 Total estimated production loss: <strong style="color:#ff4d6a;font-size:1.3rem;">
            {currency_symbol}{total_loss:,.0f}</strong>
        </div>
        """, unsafe_allow_html=True)

        if financial_assets:
            for a in financial_assets:
                pct_of_total = (a["estimated_loss"] / total_loss * 100) if total_loss > 0 else 0
                st.markdown(f"""
                <div class="insight-box">
                    <div style="display:flex;justify-content:space-between;">
                        <div><strong style="color:#e8eaf0;">{a['asset_id']}</strong>
                        <span style="color:#6b7394;margin-left:0.5rem;">{a['asset_name']}</span></div>
                        <div>
                            <span style="font-family:'JetBrains Mono';color:#ff4d6a;font-weight:700;">
                                {currency_symbol}{a['estimated_loss']:,.0f}</span>
                            <span style="color:#6b7394;font-size:0.78rem;margin-left:0.5rem;">({pct_of_total:.1f}%)</span>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

    with tab5:
        st.markdown('<div class="sec-label">Action Items</div>', unsafe_allow_html=True)
        st.markdown('<div class="sec-title">Prioritized Recommendations</div>', unsafe_allow_html=True)

        recs = []
        if quality["avg_completeness"] < 80:
            worst = min(quality.get("completeness", {}).items(), key=lambda x: x[1], default=("N/A", 0))
            recs.append(("HIGH", f"Improve {worst[0]} data entry",
                         f"Currently at {worst[1]}% completeness. Make this mandatory on work order closure.",
                         "Enables accurate asset-level tracking"))
        if quality["overall_score"] < 70:
            recs.append(("HIGH", "Standardize failure code taxonomy",
                         f"Implement a simplified {ind_info.get('name', 'industry')}-specific failure code set (15-20 codes max).",
                         "Unlocks root cause analysis"))
        if financial_assets:
            w = financial_assets[0]
            recs.append(("HIGH", f"Root cause investigation on {w['asset_id']}",
                         f"{w['failure_count']} breakdowns, {w['total_downtime_hours']:.0f} hrs downtime, ~{currency_symbol}{w['estimated_loss']:,.0f} in losses.",
                         "Eliminate top cost driver"))
        recs.append(("MEDIUM", "Standardize work order descriptions",
                     "Provide dropdown-based failure entry to improve future data quality.",
                     "Enables automated failure trending"))
        recs.append(("MEDIUM", "Schedule recurring data assessments",
                     "Run monthly to track improvement and catch new trends.",
                     "Continuous improvement loop"))

        for priority, title, detail, impact in recs:
            color = "#ff4d6a" if priority == "HIGH" else "#ff9f43"
            st.markdown(f"""
            <div class="insight-box">
                <div style="display:flex;align-items:center;gap:0.6rem;margin-bottom:0.4rem;">
                    <span class="tag" style="background:{color}22;color:{color};">{priority}</span>
                    <strong style="color:#e8eaf0;">{title}</strong>
                </div>
                <div style="color:#6b7394;font-size:0.88rem;margin-bottom:0.3rem;">{detail}</div>
                <div style="color:#00e68a;font-size:0.8rem;">↳ Impact: {impact}</div>
            </div>
            """, unsafe_allow_html=True)

    # ============================================================
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

        # ============================================================
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

        # ============================================================
    # EXPORT
    # ============================================================
    # ============================================================
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

        # ============================================================
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

        # ============================================================
    # EXPORT
    # ============================================================
    st.markdown("---")
    st.markdown('<div class="sec-label">Export</div>', unsafe_allow_html=True)

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        summary_data = {
            "Metric": ["Data Quality Score", "Completeness", "Consistency", "Usability",
                        "Total Breakdowns", "Total Downtime Hours", "Est. Production Loss",
                        "Industry", "Production Value/Hr"],
            "Value": [f"{quality['overall_score']}%", f"{quality['avg_completeness']}%",
                      f"{quality['consistency_score']}%", f"{quality['usability_score']}%",
                      downtime.get("total_breakdowns", 0), downtime.get("total_downtime_hours", 0),
                      f"{currency_symbol}{total_loss:,.0f}", ind_info.get("name", "General"),
                      f"{currency_symbol}{prod_value:,.0f}"]
        }
        pd.DataFrame(summary_data).to_excel(writer, sheet_name="Summary", index=False)
        if financial_assets:
            pd.DataFrame(financial_assets).to_excel(writer, sheet_name="Top Assets", index=False)
        norm_results.to_excel(writer, sheet_name="Failure Analysis", index=False)
        df.to_excel(writer, sheet_name="Normalized Data", index=False)
        if ingestion.raw_df is not None:
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
            pass

    report_name = f"maintsignal_{client_name.replace(' ', '_') or 'assessment'}_{datetime.now().strftime('%Y%m%d')}.xlsx"
    st.download_button(
        label="📥 Download Full Report (Excel)",
        data=output.getvalue(),
        file_name=report_name,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )
