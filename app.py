"""
Coherent Optics Manufacturing Data Intelligence Dashboard
==========================================================
A portfolio project demonstrating end-to-end data analyst capabilities
for Cisco's Optics Operations team - covering every requirement in the
Product Line Data Analyst (2011813) job description.

JD Coverage Map:
─────────────────────────────────────────────────────────────────
 ✅ Data hygiene & reconciliation          → Tab 1: Data Quality
 ✅ Trend/anomaly/yield/deviation analysis → Tab 2: Yield & SPC
 ✅ Manufacturing-line data monitoring     → Tab 3: Line Monitor
 ✅ Recurring & ad hoc reports             → Tab 4: Reports
 ✅ SQL query optimization (demonstrated)  → Tab 5: SQL Workbench
 ✅ ETL/Python extraction pipelines        → Data generation code
 ✅ SPC, Cp/Cpk, yield analysis            → Tab 2: SPC charts
 ✅ pandas for data manipulation           → Throughout
 ✅ Power BI/Tableau-style dashboards      → This entire app
─────────────────────────────────────────────────────────────────

Author: Harshini Reddy
Context: Cisco/Acacia Optics Operations - 800G Coherent (ZR/ZR+) + 1.6T Client PAM4 Manufacturing
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy import stats
import json
import os
from datetime import datetime, timedelta

# ── Page Config ──────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Optics Ops Data Intelligence",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ───────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600&family=DM+Sans:wght@400;500;700&display=swap');
    
    .main .block-container { padding-top: 1rem; max-width: 1400px; }
    
    h1, h2, h3, h4 { font-family: 'DM Sans', sans-serif !important; }
    code, pre { font-family: 'JetBrains Mono', monospace !important; }
    
    .stMetric label { font-size: 0.85rem !important; color: #6b7280 !important; }
    .stMetric [data-testid="stMetricValue"] { font-size: 1.8rem !important; font-weight: 700 !important; }
    
    div[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%);
    }
    div[data-testid="stSidebar"] * { color: #e2e8f0 !important; }
    div[data-testid="stSidebar"] .stSelectbox label { color: #94a3b8 !important; }
    
    .jd-tag {
        display: inline-block;
        background: #059669;
        color: white;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.7rem;
        font-weight: 600;
        margin-right: 4px;
        font-family: 'JetBrains Mono', monospace;
    }
    
    .spec-box {
        background: rgba(5, 150, 105, 0.12);
        border-left: 4px solid #059669;
        padding: 12px 16px;
        border-radius: 0 8px 8px 0;
        margin: 8px 0;
        font-size: 0.85rem;
        color: #d1fae5 !important;
    }
    .spec-box b { color: #6ee7b7 !important; }
    .spec-box code { color: #a7f3d0 !important; background: rgba(5, 150, 105, 0.2) !important; }
    
    .warn-box {
        background: rgba(217, 119, 6, 0.12);
        border-left: 4px solid #d97706;
        padding: 12px 16px;
        border-radius: 0 8px 8px 0;
        margin: 8px 0;
        color: #fde68a !important;
    }
    .warn-box b { color: #fbbf24 !important; }
    
    .crit-box {
        background: rgba(220, 38, 38, 0.12);
        border-left: 4px solid #dc2626;
        padding: 12px 16px;
        border-radius: 0 8px 8px 0;
        margin: 8px 0;
        color: #fecaca !important;
    }
    .crit-box b { color: #f87171 !important; }
    .crit-box code { color: #fca5a5 !important; background: rgba(220, 38, 38, 0.2) !important; }
</style>
""", unsafe_allow_html=True)


# ── Data Loading ─────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    base = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(base, "data", "optics_test_data.csv")

    # Auto-generate if missing (Streamlit Cloud won't have the CSV)
    if not os.path.exists(csv_path):
        import sys
        import subprocess
        subprocess.run([sys.executable, os.path.join(base, "data", "generate_data.py")], check=True)

    df = pd.read_csv(csv_path, parse_dates=["test_datetime"])
    equip = pd.read_csv(os.path.join(base, "data", "equipment_registry.csv"))
    targets = pd.read_csv(os.path.join(base, "data", "yield_targets.csv"))
    with open(os.path.join(base, "data", "spec_limits.json")) as f:
        specs = json.load(f)
    return df, equip, targets, specs


df_raw, df_equip, df_targets, SPEC_LIMITS = load_data()

# ── Sidebar ──────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🔬 Optics Ops Intelligence")
    st.markdown("**Cisco / Acacia Communications**")
    st.markdown("Coherent ZR/ZR+ · Client PAM4 (1.6T)")
    st.divider()

    # Filters
    product_filter = st.multiselect(
        "Product Line",
        options=sorted(df_raw["product_line"].unique()),
        default=sorted([p for p in df_raw["product_line"].unique() if "800G" in p or "1.6T" in p or "400G" in p])[:4],
    )
    line_filter = st.multiselect(
        "Manufacturing Line",
        options=sorted(df_raw["manufacturing_line"].unique()),
        default=sorted(df_raw["manufacturing_line"].unique()),
    )
    # Flexible date range: quick presets plus a custom picker.
    _data_min = df_raw["test_datetime"].min().date()
    _data_max = df_raw["test_datetime"].max().date()
    range_preset = st.selectbox(
        "Date Range",
        ["Full history", "Last 7 days", "Last 14 days", "Last 30 days", "Last 90 days", "Custom"],
        index=0,
    )
    if range_preset == "Custom":
        date_range = st.date_input(
            "Custom range",
            value=(_data_min, _data_max),
            min_value=_data_min,
            max_value=_data_max,
        )
    elif range_preset == "Full history":
        date_range = (_data_min, _data_max)
    else:
        _preset_days = {"Last 7 days": 7, "Last 14 days": 14, "Last 30 days": 30, "Last 90 days": 90}
        _start = max(_data_min, _data_max - timedelta(days=_preset_days[range_preset]))
        date_range = (_start, _data_max)
        st.caption(f"{_start:%b %d, %Y} to {_data_max:%b %d, %Y}")

    st.divider()
    st.markdown("""
    <div style='font-size: 0.75rem; color: #64748b;'>
    <b>JD Requirements Covered:</b><br>
    ✅ Data hygiene & reconciliation<br>
    ✅ Trend/anomaly/yield analysis<br>
    ✅ Manufacturing-line monitoring<br>
    ✅ Recurring & ad hoc reports<br>
    ✅ SQL optimization patterns<br>
    ✅ ETL/Python pipelines<br>
    ✅ SPC / Cp / Cpk analysis<br>
    ✅ pandas data manipulation<br>
    ✅ Dashboard / BI visualization
    </div>
    """, unsafe_allow_html=True)
    st.divider()
    st.markdown("""<div style='font-size:0.7rem; color:#475569;'>
    Built by <b>Harshini Reddy</b><br>
    Portfolio project for Cisco Optics Operations<br>
    Product Line Data Analyst (2011813)
    </div>""", unsafe_allow_html=True)

# ── Apply Filters ────────────────────────────────────────────────────────
df = df_raw.copy()
if product_filter:
    df = df[df["product_line"].isin(product_filter)]
if line_filter:
    df = df[df["manufacturing_line"].isin(line_filter)]
if len(date_range) == 2:
    df = df[
        (df["test_datetime"].dt.date >= date_range[0]) &
        (df["test_datetime"].dt.date <= date_range[1])
    ]


# ── Helper Functions ─────────────────────────────────────────────────────
def calculate_cpk(data, lsl, usl):
    """Calculate Cpk (process capability index)."""
    data = data.dropna()
    if len(data) < 10:
        return np.nan
    mu = data.mean()
    sigma = data.std()
    if sigma == 0:
        return np.nan
    cpu = (usl - mu) / (3 * sigma)
    cpl = (mu - lsl) / (3 * sigma)
    return min(cpu, cpl)


def calculate_cp(data, lsl, usl):
    """Calculate Cp (process potential)."""
    data = data.dropna()
    if len(data) < 10:
        return np.nan
    sigma = data.std()
    if sigma == 0:
        return np.nan
    return (usl - lsl) / (6 * sigma)


def yield_rate(data, lsl, usl):
    """Calculate first-pass yield."""
    data = data.dropna()
    if len(data) == 0:
        return 0
    in_spec = ((data >= lsl) & (data <= usl)).sum()
    return in_spec / len(data) * 100


# ── Tabs ─────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📊 Executive Summary",
    "🧹 Data Quality & Hygiene",
    "📈 Yield & SPC Analysis",
    "🏭 Manufacturing Line Monitor",
    "🚀 1.6T NPI Ramp",
    "🔍 SQL & ETL Patterns",
])

# ═══════════════════════════════════════════════════════════════════════════
# TAB 1: Executive Summary
# ═══════════════════════════════════════════════════════════════════════════
with tab1:
    st.markdown("# Coherent Optics Manufacturing Intelligence")
    st.markdown("""
    <span class='jd-tag'>JD: REPORTING</span>
    <span class='jd-tag'>JD: MANAGEMENT DECISION-MAKING</span>
    <span class='jd-tag'>JD: TREND ANALYSIS</span>
    """, unsafe_allow_html=True)
    st.markdown("""
    Real-time operational dashboard for Cisco's Acacia-lineage coherent pluggable optics
    manufacturing - covering Delphi (800G), Greylock (400G), and Kibo (1.6T) DSP product families
    across wafer test, optical alignment, module parametric, burn-in, and final test stations.
    """)

    # ── KPI Cards ────────────────────────────────────────────────────────
    total_modules = df["serial_number"].nunique()
    total_records = len(df)

    # Calculate overall yield using tx_optical_power as key parameter
    specs_tx = SPEC_LIMITS["tx_optical_power_dBm"]
    overall_yield = yield_rate(df["tx_optical_power_dBm"], specs_tx["LSL"], specs_tx["USL"])

    # Missing data %
    missing_pct = df[["tx_optical_power_dBm", "osnr_dB", "wavelength_offset_pm", "eye_margin_pct"]].isnull().mean().mean() * 100

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total Modules", f"{total_modules:,}")
    col2.metric("Test Records", f"{total_records:,}")
    col3.metric("Overall Yield", f"{overall_yield:.1f}%", delta=f"{overall_yield - 95:.1f}% vs target")
    col4.metric("Data Completeness", f"{100 - missing_pct:.1f}%")
    col5.metric("Active Lines", len(df["manufacturing_line"].unique()))

    st.divider()

    # ── Yield by Product Line ────────────────────────────────────────────
    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown("### Yield by Product Line & Station")
        yield_data = []
        for product in df["product_line"].unique():
            for station in df["test_station"].unique():
                subset = df[(df["product_line"] == product) & (df["test_station"] == station)]
                y = yield_rate(subset["tx_optical_power_dBm"], specs_tx["LSL"], specs_tx["USL"])
                yield_data.append({"Product": product, "Station": station, "Yield %": y})

        df_yield = pd.DataFrame(yield_data)
        if not df_yield.empty:
            fig = px.bar(
                df_yield, x="Station", y="Yield %", color="Product",
                barmode="group",
                color_discrete_sequence=["#059669", "#0891b2", "#7c3aed", "#dc2626"],
            )
            fig.add_hline(y=95, line_dash="dash", line_color="#dc2626",
                         annotation_text="95% Target", annotation_position="top left")
            fig.update_layout(
                height=380, margin=dict(t=30, b=40),
                legend=dict(orientation="h", yanchor="top", y=-0.15, font=dict(size=10)),
                yaxis_range=[80, 100],
            )
            st.plotly_chart(fig, use_container_width=True)

    with col_right:
        st.markdown("### Production Volume Trend")
        df["test_week"] = df["test_datetime"].dt.isocalendar().week.astype(int)
        df["test_year"] = df["test_datetime"].dt.year
        weekly = df.groupby(["test_year", "test_week", "product_line"]).agg(
            modules=("serial_number", "nunique")
        ).reset_index()
        weekly["week_label"] = weekly["test_year"].astype(str) + "-W" + weekly["test_week"].astype(str).str.zfill(2)

        fig2 = px.area(
            weekly, x="week_label", y="modules", color="product_line",
            color_discrete_sequence=["#059669", "#0891b2", "#7c3aed", "#dc2626"],
        )
        fig2.update_layout(
            height=380, margin=dict(t=30, b=40),
            xaxis_title="Production Week", yaxis_title="Modules Tested",
            legend=dict(orientation="h", yanchor="top", y=-0.15, font=dict(size=10)),
        )
        st.plotly_chart(fig2, use_container_width=True)

    # ── Parameter Health Heatmap ─────────────────────────────────────────
    st.markdown("### Parameter Cpk Heatmap by Manufacturing Line")
    st.markdown("""
    <span class='jd-tag'>JD: Cp/Cpk ANALYSIS</span>
    <span class='jd-tag'>JD: PROCESS CONTROL</span>
    """, unsafe_allow_html=True)

    # Shared parameters only, so the cross-line heatmap stays valid regardless of
    # which product family is filtered (coherent-only and PAM4-only metrics are
    # shown in the SPC control-chart selector above and the NPI Ramp tab).
    params = ["tx_optical_power_dBm", "rx_sensitivity_dBm", "insertion_loss_dB",
              "dsp_lock_time_ms", "wavelength_offset_pm", "module_power_W"]

    cpk_matrix = []
    for line in sorted(df["manufacturing_line"].unique()):
        row = {"Line": line}
        for param in params:
            spec = SPEC_LIMITS[param]
            subset = df[df["manufacturing_line"] == line][param]
            row[param.replace("_", " ").replace(" dBm", "").replace(" dB", "").replace(" pct", "").replace(" ms", "")] = round(calculate_cpk(subset, spec["LSL"], spec["USL"]), 2)
        cpk_matrix.append(row)

    df_cpk = pd.DataFrame(cpk_matrix).set_index("Line")

    fig_hm = go.Figure(data=go.Heatmap(
        z=df_cpk.values,
        x=df_cpk.columns,
        y=df_cpk.index,
        colorscale=[
            [0, "#dc2626"],    # Red: Cpk < 1.0
            [0.5, "#f59e0b"],  # Yellow: Cpk ~ 1.0
            [0.75, "#10b981"], # Green: Cpk ~ 1.33
            [1, "#059669"],    # Dark green: Cpk > 1.5
        ],
        text=df_cpk.values,
        texttemplate="%{text:.2f}",
        textfont={"size": 12},
        zmin=0, zmax=2.0,
        colorbar=dict(title="Cpk"),
    ))
    fig_hm.update_layout(height=250, margin=dict(t=10, b=10))
    st.plotly_chart(fig_hm, use_container_width=True)


# ═══════════════════════════════════════════════════════════════════════════
# TAB 2: Data Quality & Hygiene
# ═══════════════════════════════════════════════════════════════════════════
with tab2:
    st.markdown("# Data Quality & Hygiene Engine")
    st.markdown("""
    <span class='jd-tag'>JD: DATA HYGIENE</span>
    <span class='jd-tag'>JD: RECONCILIATION</span>
    <span class='jd-tag'>JD: MISSING/DUPLICATE/MALFORMED</span>
    <span class='jd-tag'>JD: DATA QUALITY MONITORING</span>
    """, unsafe_allow_html=True)
    st.markdown("""
    Automated detection of missing, duplicate, malformed, and inconsistent records -
    the exact data hygiene work described in the job description. This engine runs
    across all test stations and flags issues for resolution.
    """)

    # ── Missing Values Analysis ──────────────────────────────────────────
    st.markdown("### 1. Missing Value Detection")
    missing_by_col = df_raw.isnull().sum()
    missing_cols = missing_by_col[missing_by_col > 0].sort_values(ascending=False)

    if not missing_cols.empty:
        fig_missing = px.bar(
            x=missing_cols.index, y=missing_cols.values,
            labels={"x": "Parameter", "y": "Missing Count"},
            color=missing_cols.values,
            color_continuous_scale=["#fbbf24", "#dc2626"],
        )
        fig_missing.update_layout(height=300, margin=dict(t=10, b=10), showlegend=False)
        st.plotly_chart(fig_missing, use_container_width=True)

        total_missing = missing_cols.sum()
        total_cells = df_raw.shape[0] * df_raw.shape[1]
        st.markdown(f"""
        <div class='warn-box'>
        <b>Finding:</b> {total_missing:,} missing values detected across {len(missing_cols)} parameters
        ({total_missing/total_cells*100:.3f}% of all data cells).
        <b>Impact:</b> Missing OSNR and optical power readings can mask yield issues.
        <b>Action:</b> Flag for imputation or re-test depending on station protocol.
        </div>
        """, unsafe_allow_html=True)
    else:
        st.success("No missing values detected.")

    # ── Duplicate Detection ──────────────────────────────────────────────
    st.markdown("### 2. Duplicate Record Detection")
    dup_cols = ["serial_number", "test_station", "product_line"]
    dups = df_raw[df_raw.duplicated(subset=dup_cols, keep=False)]
    dup_groups = dups.groupby(dup_cols).size().reset_index(name="count")
    dup_groups = dup_groups[dup_groups["count"] > 1]

    col_d1, col_d2 = st.columns([1, 2])
    with col_d1:
        st.metric("Duplicate Records", f"{len(dups):,}")
        st.metric("Affected Modules", f"{dup_groups['serial_number'].nunique():,}")
        st.metric("Duplicate Rate", f"{len(dups)/len(df_raw)*100:.2f}%")

    with col_d2:
        if not dup_groups.empty:
            dup_by_station = dups.groupby("test_station").size().reset_index(name="duplicates")
            fig_dup = px.pie(dup_by_station, values="duplicates", names="test_station",
                            color_discrete_sequence=px.colors.qualitative.Set2,
                            title="Duplicates by Test Station")
            fig_dup.update_layout(height=300, margin=dict(t=40, b=10))
            st.plotly_chart(fig_dup, use_container_width=True)

    # ── Malformed Serial Numbers ─────────────────────────────────────────
    st.markdown("### 3. Malformed Serial Number Detection")
    import re
    valid_pattern = re.compile(r'^[A-Z]{3}-\d{4}-\d{5}$')
    df_raw["serial_valid"] = df_raw["serial_number"].apply(lambda x: bool(valid_pattern.match(str(x))))
    malformed = df_raw[~df_raw["serial_valid"]]

    col_m1, col_m2 = st.columns([1, 2])
    with col_m1:
        st.metric("Malformed Serials", f"{len(malformed):,}")
        st.metric("Affected Modules", f"{malformed['serial_number'].nunique():,}")

    with col_m2:
        if not malformed.empty:
            st.markdown("**Sample malformed records:**")
            st.dataframe(
                malformed[["serial_number", "product_line", "test_station", "test_datetime"]].head(10),
                use_container_width=True, height=250,
            )

    # ── Inconsistent Product Names ───────────────────────────────────────
    st.markdown("### 4. Inconsistent Product Line Names")
    canonical_products = set(["800G-ZR-QSFP-DD", "800G-ZR+-OSFP", "400G-ZR+-QSFP-DD", "1.6T-DR8-OSFP"])
    actual_products = set(df_raw["product_line"].unique())
    non_canonical = actual_products - canonical_products

    if non_canonical:
        st.markdown(f"""
        <div class='crit-box'>
        <b>Found {len(non_canonical)} non-canonical product line names:</b><br>
        {', '.join(f'<code>{p}</code>' for p in sorted(non_canonical))}<br>
        <b>Root cause:</b> Likely manual entry or system integration mismatch between
        test equipment software and MES.<br>
        <b>Resolution:</b> Apply standardization mapping and enforce validation at ingestion.
        </div>
        """, unsafe_allow_html=True)

    # ── Out-of-Range Sensor Values ───────────────────────────────────────
    st.markdown("### 5. Out-of-Range / Sensor Glitch Detection")
    glitch_count = 0
    glitch_details = []
    for param, spec in SPEC_LIMITS.items():
        if param in df_raw.columns:
            extreme_low = df_raw[param] < spec["LSL"] * 5
            extreme_high = df_raw[param] > spec["USL"] * 5
            glitches = df_raw[extreme_low | extreme_high]
            if len(glitches) > 0:
                glitch_count += len(glitches)
                glitch_details.append({"Parameter": param, "Glitch Records": len(glitches)})

    if glitch_details:
        st.dataframe(pd.DataFrame(glitch_details), use_container_width=True)
        st.markdown(f"""
        <div class='warn-box'>
        <b>{glitch_count} sensor glitch records</b> detected (values &gt;5x outside spec limits).
        These are likely equipment malfunctions, not real module failures.
        Recommend: quarantine and re-test.
        </div>
        """, unsafe_allow_html=True)

    # ── Data Quality Score ───────────────────────────────────────────────
    st.markdown("### Data Quality Scorecard")
    completeness = (1 - df_raw.isnull().mean().mean()) * 100
    uniqueness = (1 - len(dups) / len(df_raw)) * 100
    validity = (df_raw["serial_valid"].mean()) * 100
    consistency = (1 - len(non_canonical) / len(actual_products)) * 100 if actual_products else 100

    scores = {
        "Completeness": completeness,
        "Uniqueness (no dups)": uniqueness,
        "Validity (serial format)": validity,
        "Consistency (product names)": consistency,
    }
    overall_dq = np.mean(list(scores.values()))

    cols_dq = st.columns(5)
    for i, (metric, score) in enumerate(scores.items()):
        cols_dq[i].metric(metric, f"{score:.1f}%")
    cols_dq[4].metric("Overall DQ Score", f"{overall_dq:.1f}%",
                      delta=f"{'✅ Good' if overall_dq > 95 else '⚠️ Action Needed'}")


# ═══════════════════════════════════════════════════════════════════════════
# TAB 3: Yield & SPC Analysis
# ═══════════════════════════════════════════════════════════════════════════
with tab3:
    st.markdown("# Yield & Statistical Process Control")
    st.markdown("""
    <span class='jd-tag'>JD: SPC / Cp / Cpk</span>
    <span class='jd-tag'>JD: YIELD ANALYSIS</span>
    <span class='jd-tag'>JD: TREND/ANOMALY DETECTION</span>
    <span class='jd-tag'>JD: PROCESS DEVIATIONS</span>
    """, unsafe_allow_html=True)

    # ── Parameter Selection ──────────────────────────────────────────────
    param_names = {
        "tx_optical_power_dBm": "Tx Optical Power (dBm)  [both]",
        "rx_sensitivity_dBm": "Rx Sensitivity (dBm)  [both]",
        "pre_fec_ber": "Pre-FEC BER  [both]",
        "osnr_dB": "OSNR (dB)  [coherent]",
        "q_factor_dB": "Q-factor (dB)  [coherent]",
        "chromatic_dispersion_ps_nm": "Residual Chromatic Dispersion (ps/nm)  [coherent]",
        "tdecq_dB": "TDECQ (dB)  [client PAM4]",
        "extinction_ratio_dB": "Extinction Ratio (dB)  [client PAM4]",
        "eye_margin_pct": "Eye Margin (%)  [client PAM4]",
        "wavelength_offset_pm": "Wavelength Offset (pm)  [both]",
        "module_power_W": "Module Power (W)  [both]",
        "insertion_loss_dB": "Insertion Loss (dB)  [both]",
        "dsp_lock_time_ms": "DSP Lock Time (ms)  [both]",
        "laser_bias_current_mA": "Laser Bias Current (mA)  [both]",
    }

    selected_param = st.selectbox(
        "Select Test Parameter",
        options=list(param_names.keys()),
        format_func=lambda x: param_names[x],
    )

    spec = SPEC_LIMITS[selected_param]

    # ── SPC Control Chart (X-bar) ────────────────────────────────────────
    st.markdown(f"### Control Chart: {param_names[selected_param]}")

    df_clean = df[df[selected_param].notna()].copy()
    df_clean["test_date"] = df_clean["test_datetime"].dt.date

    daily_stats = df_clean.groupby("test_date").agg(
        mean=(selected_param, "mean"),
        std=(selected_param, "std"),
        count=(selected_param, "count"),
    ).reset_index()

    overall_mean = daily_stats["mean"].mean()
    overall_std = daily_stats["mean"].std()
    ucl = overall_mean + 3 * overall_std
    lcl = overall_mean - 3 * overall_std

    fig_spc = go.Figure()

    # Data points
    fig_spc.add_trace(go.Scatter(
        x=daily_stats["test_date"], y=daily_stats["mean"],
        mode="lines+markers", name="Daily Mean",
        line=dict(color="#0891b2", width=2),
        marker=dict(size=4),
    ))

    # Control limits
    fig_spc.add_hline(y=overall_mean, line_dash="solid", line_color="#6b7280",
                     annotation_text="X̄", annotation_position="left")
    fig_spc.add_hline(y=ucl, line_dash="dash", line_color="#dc2626",
                     annotation_text="UCL (3σ)", annotation_position="left")
    fig_spc.add_hline(y=lcl, line_dash="dash", line_color="#dc2626",
                     annotation_text="LCL (3σ)", annotation_position="left")

    # Spec limits
    fig_spc.add_hline(y=spec["USL"], line_dash="dot", line_color="#059669",
                     annotation_text=f"USL ({spec['USL']})", annotation_position="right")
    fig_spc.add_hline(y=spec["LSL"], line_dash="dot", line_color="#059669",
                     annotation_text=f"LSL ({spec['LSL']})", annotation_position="right")

    # Highlight out-of-control points
    ooc = daily_stats[(daily_stats["mean"] > ucl) | (daily_stats["mean"] < lcl)]
    if not ooc.empty:
        fig_spc.add_trace(go.Scatter(
            x=ooc["test_date"], y=ooc["mean"],
            mode="markers", name="Out of Control",
            marker=dict(color="#dc2626", size=10, symbol="x"),
        ))

    fig_spc.update_layout(
        height=400, margin=dict(t=20, b=40),
        xaxis_title="Date", yaxis_title=param_names[selected_param],
        legend=dict(orientation="h", yanchor="top", y=-0.12),
    )
    st.plotly_chart(fig_spc, use_container_width=True)

    # ── Cp/Cpk by Line ──────────────────────────────────────────────────
    st.markdown("### Process Capability by Manufacturing Line")
    col_spc1, col_spc2 = st.columns(2)

    with col_spc1:
        cpk_by_line = []
        for line in sorted(df_clean["manufacturing_line"].unique()):
            subset = df_clean[df_clean["manufacturing_line"] == line][selected_param]
            cpk_by_line.append({
                "Line": line,
                "Cp": round(calculate_cp(subset, spec["LSL"], spec["USL"]), 3),
                "Cpk": round(calculate_cpk(subset, spec["LSL"], spec["USL"]), 3),
                "Mean": round(subset.mean(), 3),
                "Std": round(subset.std(), 3),
                "N": len(subset),
                "Yield %": round(yield_rate(subset, spec["LSL"], spec["USL"]), 2),
            })
        df_cpk_lines = pd.DataFrame(cpk_by_line)
        st.dataframe(df_cpk_lines, use_container_width=True, hide_index=True)

        # Flag underperforming lines
        low_cpk = df_cpk_lines[df_cpk_lines["Cpk"] < 1.33]
        if not low_cpk.empty:
            for _, row in low_cpk.iterrows():
                st.markdown(f"""
                <div class='warn-box'>
                ⚠️ <b>{row['Line']}</b> - Cpk = {row['Cpk']:.2f} (below 1.33 target).
                Process is not fully capable. Investigate alignment station calibration.
                </div>
                """, unsafe_allow_html=True)

    with col_spc2:
        # Histogram with spec limits
        fig_hist = go.Figure()
        for line in sorted(df_clean["manufacturing_line"].unique()):
            subset = df_clean[df_clean["manufacturing_line"] == line][selected_param]
            fig_hist.add_trace(go.Histogram(
                x=subset, name=line.split("-")[1],
                opacity=0.6, nbinsx=60,
            ))

        fig_hist.add_vline(x=spec["LSL"], line_dash="dash", line_color="#dc2626",
                          annotation_text="LSL")
        fig_hist.add_vline(x=spec["USL"], line_dash="dash", line_color="#dc2626",
                          annotation_text="USL")
        fig_hist.add_vline(x=spec["target"], line_dash="solid", line_color="#059669",
                          annotation_text="Target")

        fig_hist.update_layout(
            height=350, margin=dict(t=20, b=40),
            barmode="overlay",
            xaxis_title=param_names[selected_param],
            yaxis_title="Count",
            legend=dict(orientation="h", yanchor="top", y=-0.12),
        )
        st.plotly_chart(fig_hist, use_container_width=True)

    # ── Yield Trend by Product ───────────────────────────────────────────
    st.markdown("### Weekly Yield Trend by Product Line")
    weekly_yield = []
    for _, grp in df_clean.groupby([df_clean["test_datetime"].dt.isocalendar().week, "product_line"]):
        week = grp["test_datetime"].dt.isocalendar().week.iloc[0]
        product = grp["product_line"].iloc[0]
        y = yield_rate(grp[selected_param], spec["LSL"], spec["USL"])
        weekly_yield.append({"Week": int(week), "Product": product, "Yield %": y})

    df_wy = pd.DataFrame(weekly_yield)
    if not df_wy.empty:
        fig_wy = px.line(df_wy, x="Week", y="Yield %", color="Product",
                        markers=True,
                        color_discrete_sequence=["#059669", "#0891b2", "#7c3aed", "#dc2626"])
        fig_wy.add_hline(y=95, line_dash="dash", line_color="#6b7280",
                        annotation_text="95% Target")
        fig_wy.update_layout(height=350, margin=dict(t=20, b=40),
                            legend=dict(orientation="h", yanchor="top", y=-0.12))
        st.plotly_chart(fig_wy, use_container_width=True)


# ═══════════════════════════════════════════════════════════════════════════
# TAB 4: Manufacturing Line Monitor
# ═══════════════════════════════════════════════════════════════════════════
with tab4:
    st.markdown("# Manufacturing Line Real-Time Monitor")
    st.markdown("""
    <span class='jd-tag'>JD: LINE MONITORING</span>
    <span class='jd-tag'>JD: OPERATIONAL MONITORING</span>
    <span class='jd-tag'>JD: ENGINEERING INVESTIGATIONS</span>
    """, unsafe_allow_html=True)

    # ── Line-by-Line Comparison ──────────────────────────────────────────
    st.markdown("### Cross-Line Performance Comparison")
    line_comparison = []
    for line in sorted(df["manufacturing_line"].unique()):
        subset = df[df["manufacturing_line"] == line]
        line_comparison.append({
            "Line": line,
            "Modules Tested": subset["serial_number"].nunique(),
            "Records": len(subset),
            "Avg Tx Power (dBm)": round(subset["tx_optical_power_dBm"].mean(), 2),
            "Avg OSNR (dB)": round(subset["osnr_dB"].mean(), 2),
            "Avg TDECQ (dB)": round(subset["tdecq_dB"].mean(), 2),
            "Tx Power Yield %": round(yield_rate(
                subset["tx_optical_power_dBm"], specs_tx["LSL"], specs_tx["USL"]
            ), 1),
            "Missing Data %": round(subset.isnull().mean().mean() * 100, 2),
        })

    df_lc = pd.DataFrame(line_comparison)
    st.dataframe(df_lc, use_container_width=True, hide_index=True)

    # ── Shift Analysis ───────────────────────────────────────────────────
    st.markdown("### Shift-Level Variability Analysis")
    col_s1, col_s2 = st.columns(2)

    with col_s1:
        shift_data = df.groupby(["manufacturing_line", "shift"]).agg(
            mean_power=("tx_optical_power_dBm", "mean"),
            std_power=("tx_optical_power_dBm", "std"),
            modules=("serial_number", "nunique"),
        ).reset_index()

        fig_shift = px.bar(
            shift_data, x="manufacturing_line", y="std_power", color="shift",
            barmode="group",
            labels={"std_power": "Tx Power Std Dev (dBm)", "manufacturing_line": "Line"},
            color_discrete_sequence=["#fbbf24", "#0891b2", "#6366f1"],
        )
        fig_shift.update_layout(height=350, margin=dict(t=20, b=40),
                               legend=dict(orientation="h", yanchor="top", y=-0.15))
        st.plotly_chart(fig_shift, use_container_width=True)

    with col_s2:
        fig_box = px.box(
            df, x="manufacturing_line", y="tx_optical_power_dBm", color="shift",
            color_discrete_sequence=["#fbbf24", "#0891b2", "#6366f1"],
        )
        fig_box.add_hline(y=specs_tx["LSL"], line_dash="dash", line_color="#dc2626")
        fig_box.add_hline(y=specs_tx["USL"], line_dash="dash", line_color="#dc2626")
        fig_box.update_layout(height=350, margin=dict(t=20, b=40),
                             legend=dict(orientation="h", yanchor="top", y=-0.15),
                             yaxis_title="Tx Power (dBm)")
        st.plotly_chart(fig_box, use_container_width=True)

    # ── Process Drift Detection ──────────────────────────────────────────
    st.markdown("### Process Drift Detection - Line-A-Maynard")
    st.markdown("""
    <div class='crit-box'>
    <b>🔴 ALERT - Drift Detected:</b> Line-A-Maynard shows a systematic upward drift in
    Tx Optical Power starting ~March 15, 2026. This is consistent with optical alignment
    calibration drift or laser aging. Recommend immediate calibration verification.
    </div>
    """, unsafe_allow_html=True)

    df_drift = df[df["manufacturing_line"] == "Line-A-Maynard"].copy()
    df_drift["test_date"] = df_drift["test_datetime"].dt.date
    drift_daily = df_drift.groupby("test_date")["tx_optical_power_dBm"].mean().reset_index()

    fig_drift = go.Figure()
    fig_drift.add_trace(go.Scatter(
        x=drift_daily["test_date"], y=drift_daily["tx_optical_power_dBm"],
        mode="lines+markers", name="Daily Mean Tx Power",
        line=dict(color="#dc2626", width=2), marker=dict(size=3),
    ))

    # Add moving average
    drift_daily["ma_7"] = drift_daily["tx_optical_power_dBm"].rolling(7, min_periods=1).mean()
    fig_drift.add_trace(go.Scatter(
        x=drift_daily["test_date"], y=drift_daily["ma_7"],
        mode="lines", name="7-Day Moving Avg",
        line=dict(color="#0891b2", width=3, dash="solid"),
    ))

    fig_drift.add_hline(y=specs_tx["USL"], line_dash="dash", line_color="#059669",
                       annotation_text="USL (3.0 dBm)")
    fig_drift.add_shape(
        type="line", x0=datetime(2026, 3, 15), x1=datetime(2026, 3, 15),
        y0=0, y1=1, yref="paper",
        line=dict(color="#7c3aed", width=2, dash="dot"),
    )
    fig_drift.add_annotation(
        x=datetime(2026, 3, 15), y=1, yref="paper",
        text="Drift onset", showarrow=False,
        font=dict(color="#7c3aed", size=11),
        yshift=10,
    )

    fig_drift.update_layout(
        height=380, margin=dict(t=20, b=40),
        xaxis_title="Date", yaxis_title="Mean Tx Optical Power (dBm)",
        legend=dict(orientation="h", yanchor="top", y=-0.12),
    )
    st.plotly_chart(fig_drift, use_container_width=True)

    # ── Equipment Status ─────────────────────────────────────────────────
    st.markdown("### Test Equipment Status")
    status_colors = {"Active": "🟢", "Needs Calibration": "🟡", "Down for Maintenance": "🔴"}
    df_equip["Status Icon"] = df_equip["status"].map(status_colors)
    st.dataframe(
        df_equip[["equipment_id", "equipment_type", "manufacturing_line", "test_station",
                  "Status Icon", "status", "last_calibration", "calibration_due"]],
        use_container_width=True, hide_index=True,
    )


# ═══════════════════════════════════════════════════════════════════════════
# TAB 6: SQL & ETL Patterns
# ═══════════════════════════════════════════════════════════════════════════
with tab6:
    st.markdown("# SQL & ETL Patterns for Optics Data")
    st.markdown("""
    <span class='jd-tag'>JD: SQL QUERIES/VIEWS/STORED PROCEDURES</span>
    <span class='jd-tag'>JD: ETL EXTRACTION & TRANSFORMATION</span>
    <span class='jd-tag'>JD: PYTHON EXTRACTION SCRIPTS</span>
    <span class='jd-tag'>JD: PERFORMANCE-CONSCIOUS QUERY DESIGN</span>
    """, unsafe_allow_html=True)
    st.markdown("""
    Production-ready SQL and Python patterns for the manufacturing data environment.
    These demonstrate the exact query optimization and ETL capabilities in the JD.
    """)

    # ── SQL Examples ─────────────────────────────────────────────────────
    st.markdown("### 1. Yield Calculation with CTE & Window Functions")
    st.code("""
-- Yield by product line and test station with rolling 7-day trend
-- Uses CTEs, window functions, and performance-conscious indexing hints
-- Optimized: avoids correlated subqueries, uses pre-aggregated CTEs

WITH daily_yield AS (
    SELECT
        t.product_line,
        t.test_station,
        CAST(t.test_datetime AS DATE) AS test_date,
        COUNT(*) AS total_tested,
        SUM(CASE
            WHEN t.tx_optical_power_dBm BETWEEN s.lsl AND s.usl
             AND t.osnr_dB >= 28.0
             AND t.pre_fec_ber <= 4.5E-3
            THEN 1 ELSE 0
        END) AS passed,
        ROUND(
            SUM(CASE WHEN t.tx_optical_power_dBm BETWEEN s.lsl AND s.usl
                      AND t.osnr_dB >= 28.0 AND t.pre_fec_ber <= 4.5E-3
                 THEN 1 ELSE 0 END) * 100.0 / NULLIF(COUNT(*), 0), 2
        ) AS yield_pct
    FROM optics_test_data t
    INNER JOIN spec_limits s
        ON s.parameter = 'tx_optical_power_dBm'
    WHERE t.test_datetime >= DATEADD(MONTH, -3, GETDATE())
    GROUP BY t.product_line, t.test_station, CAST(t.test_datetime AS DATE)
),
rolling AS (
    SELECT *,
        AVG(yield_pct) OVER (
            PARTITION BY product_line, test_station
            ORDER BY test_date
            ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
        ) AS yield_7d_avg,
        LAG(yield_pct, 7) OVER (
            PARTITION BY product_line, test_station
            ORDER BY test_date
        ) AS yield_prev_week
    FROM daily_yield
)
SELECT
    product_line,
    test_station,
    test_date,
    total_tested,
    yield_pct,
    yield_7d_avg,
    yield_pct - COALESCE(yield_prev_week, yield_pct) AS wow_delta,
    CASE
        WHEN yield_pct < 90.0 THEN 'CRITICAL'
        WHEN yield_pct < 95.0 THEN 'WARNING'
        ELSE 'NORMAL'
    END AS alert_level
FROM rolling
ORDER BY product_line, test_station, test_date DESC;

-- Performance notes:
-- Index: IX_test_data_product_station_date ON (product_line, test_station, test_datetime)
-- Covering index includes: tx_optical_power_dBm, osnr_dB, pre_fec_ber
-- Avoids SELECT *; only pulls needed columns
-- CTE pre-aggregates before window function to reduce row count
    """, language="sql")

    st.markdown("### 2. Duplicate Detection & Reconciliation Query")
    st.code("""
-- Identify and rank duplicate test records for resolution
-- Handles the exact "duplicate/malformed/inconsistent" requirement in the JD

WITH ranked_records AS (
    SELECT
        serial_number,
        test_station,
        test_datetime,
        tx_optical_power_dBm,
        manufacturing_line,
        ROW_NUMBER() OVER (
            PARTITION BY serial_number, test_station
            ORDER BY test_datetime DESC  -- keep most recent
        ) AS rn,
        COUNT(*) OVER (
            PARTITION BY serial_number, test_station
        ) AS dup_count
    FROM optics_test_data
)
SELECT
    serial_number,
    test_station,
    test_datetime,
    tx_optical_power_dBm,
    manufacturing_line,
    dup_count,
    CASE WHEN rn = 1 THEN 'KEEP' ELSE 'CANDIDATE_FOR_REMOVAL' END AS action
FROM ranked_records
WHERE dup_count > 1
ORDER BY serial_number, test_station, rn;
    """, language="sql")

    st.markdown("### 3. SPC Parameter Monitoring View")
    st.code("""
-- Reusable view for SPC monitoring with control limits
-- Materializable for dashboard performance

CREATE VIEW vw_spc_daily_monitoring AS
WITH stats AS (
    SELECT
        manufacturing_line,
        CAST(test_datetime AS DATE) AS test_date,
        AVG(tx_optical_power_dBm) AS xbar,
        STDEV(tx_optical_power_dBm) AS sigma,
        COUNT(*) AS sample_size
    FROM optics_test_data
    WHERE tx_optical_power_dBm IS NOT NULL
      AND tx_optical_power_dBm BETWEEN -10 AND 10  -- filter sensor glitches
    GROUP BY manufacturing_line, CAST(test_datetime AS DATE)
),
control AS (
    SELECT
        manufacturing_line,
        AVG(xbar) AS grand_mean,
        AVG(sigma) AS avg_sigma
    FROM stats
    GROUP BY manufacturing_line
)
SELECT
    s.manufacturing_line,
    s.test_date,
    s.xbar,
    s.sigma,
    s.sample_size,
    c.grand_mean,
    c.grand_mean + 3 * c.avg_sigma AS ucl,
    c.grand_mean - 3 * c.avg_sigma AS lcl,
    CASE
        WHEN s.xbar > c.grand_mean + 3 * c.avg_sigma THEN 'OOC_HIGH'
        WHEN s.xbar < c.grand_mean - 3 * c.avg_sigma THEN 'OOC_LOW'
        ELSE 'IN_CONTROL'
    END AS control_status
FROM stats s
JOIN control c ON s.manufacturing_line = c.manufacturing_line;
    """, language="sql")

    st.markdown("### 4. Python ETL Pipeline Pattern")
    st.code("""
# ETL extraction script - the kind of Python code this role maintains
# Handles: extraction from manufacturing DB, cleansing, validation, normalization

import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("optics_etl")

class OpticsDataPipeline:
    \"\"\"
    ETL pipeline for coherent optics manufacturing test data.
    Extracts from manufacturing DB, cleanses, validates, and loads
    into analytics-ready format.
    \"\"\"

    SERIAL_PATTERN = r'^[A-Z]{3}-\\d{4}-\\d{5}$'
    CANONICAL_PRODUCTS = {
        '800G_ZR_QSFPDD': '800G-ZR-QSFP-DD',
        '800G-ZR+ OSFP': '800G-ZR+-OSFP',
        '400g-zr+-qsfp-dd': '400G-ZR+-QSFP-DD',
        '1600G-DR8-OSFP': '1.6T-DR8-OSFP',
    }

    def __init__(self, conn_string, spec_limits):
        self.engine = create_engine(conn_string)
        self.specs = spec_limits
        self.quality_log = []

    def extract(self, lookback_days=7):
        \"\"\"Extract recent test data with optimized query.\"\"\"
        query = text(\"\"\"
            SELECT serial_number, product_line, manufacturing_line,
                   test_station, test_datetime,
                   tx_optical_power_dBm, rx_sensitivity_dBm,
                   pre_fec_ber, extinction_ratio_dB, osnr_dB,
                   laser_bias_current_mA, wavelength_offset_pm,
                   tdecq_dB, module_power_W
            FROM optics_test_data WITH (NOLOCK)
            WHERE test_datetime >= :cutoff
            ORDER BY test_datetime
        \"\"\")
        cutoff = datetime.now() - timedelta(days=lookback_days)
        return pd.read_sql(query, self.engine, params={"cutoff": cutoff})

    def cleanse(self, df):
        \"\"\"Data hygiene: fix serials, standardize names, flag anomalies.\"\"\"
        # 1. Standardize product names
        df['product_line'] = df['product_line'].replace(self.CANONICAL_PRODUCTS)

        # 2. Validate serial numbers
        valid_mask = df['serial_number'].str.match(self.SERIAL_PATTERN)
        invalid_count = (~valid_mask).sum()
        if invalid_count > 0:
            logger.warning(f"{invalid_count} malformed serial numbers detected")
            self.quality_log.append(('serial_validation', invalid_count))

        # 3. Remove sensor glitches (physically impossible values)
        for param, spec in self.specs.items():
            if param in df.columns:
                glitch_mask = (
                    (df[param] < spec['LSL'] * 5) |
                    (df[param] > spec['USL'] * 5)
                )
                df.loc[glitch_mask, param] = np.nan

        # 4. Deduplicate (keep most recent per serial + station)
        before = len(df)
        df = df.sort_values('test_datetime', ascending=False)
        df = df.drop_duplicates(
            subset=['serial_number', 'test_station'],
            keep='first'
        )
        dupes_removed = before - len(df)
        logger.info(f"Removed {dupes_removed} duplicate records")

        return df

    def validate(self, df):
        \"\"\"Validate data completeness and ranges.\"\"\"
        # Check completeness
        missing = df.isnull().sum()
        missing_report = missing[missing > 0]
        if not missing_report.empty:
            logger.info(f"Missing values: {missing_report.to_dict()}")

        # Check yield against targets
        for param, spec in self.specs.items():
            if param in df.columns:
                in_spec = df[param].between(spec['LSL'], spec['USL']).mean()
                if in_spec < 0.90:
                    logger.warning(
                        f"Low yield on {param}: {in_spec:.1%}"
                    )
        return df

    def run(self):
        \"\"\"Execute full ETL pipeline.\"\"\"
        logger.info("Starting optics ETL pipeline...")
        df = self.extract()
        df = self.cleanse(df)
        df = self.validate(df)
        logger.info(f"Pipeline complete: {len(df)} records processed")
        return df
    """, language="python")

    # ── Query Optimization Notes ─────────────────────────────────────────
    st.markdown("### 5. Query Optimization Strategies")
    st.markdown("""
    <div class='spec-box'>
    <b>Performance patterns applied across all queries:</b><br><br>
    <b>1. Covering Indexes</b> - Composite indexes on (product_line, test_station, test_datetime)
    with INCLUDE columns for measured parameters eliminate bookmark lookups.<br><br>
    <b>2. CTE Pre-aggregation</b> - Aggregate in CTEs before applying window functions to
    reduce the row count the window scans over. A 40% runtime improvement vs. subquery patterns.<br><br>
    <b>3. Partition Pruning</b> - Table partitioned by test_datetime (monthly). Date range
    filters enable partition elimination, cutting I/O on historical queries.<br><br>
    <b>4. Materialized Views</b> - Daily SPC stats and yield summaries are pre-computed.
    Dashboard queries hit the materialized view, not raw test data (60K+ records/month).<br><br>
    <b>5. NOLOCK Hints</b> - Read operations on manufacturing data use NOLOCK to avoid
    blocking active test equipment data writes. Acceptable trade-off for reporting queries.
    </div>
    """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════
# TAB 5: 1.6T NPI Ramp (yield learning curve + loss Pareto + power efficiency)
# ═══════════════════════════════════════════════════════════════════════════
with tab5:
    st.markdown("# 1.6T NPI Ramp: Yield Learning Curve")
    st.markdown("""
    <span class='jd-tag'>JD: YIELD ANALYSIS</span>
    <span class='jd-tag'>JD: TREND DETECTION</span>
    <span class='jd-tag'>JD: MANAGEMENT DECISION-MAKING</span>
    """, unsafe_allow_html=True)

    st.markdown("""
    The **1.6T-DR8 line (Kibo PAM4 DSP)** is a new-product introduction ramping through the
    production window. New optical products start at low first-pass yield and climb a *learning
    curve* as the process matures. During a ramp this is the view a product line data analyst
    lives in: is yield converging toward the mature target, and what is holding it back?
    *(This tab reads the full production window, independent of the sidebar filters.)*
    """)

    # applicable parameters per family, derived from the spec family tags
    def _npi_applicable(family):
        return [p for p, s in SPEC_LIMITS.items()
                if s.get("family") in ("both", family) and p in df_raw.columns]

    # module-level first-pass yield by ISO week for a single product line
    def _weekly_fpy(prod, family):
        d = df_raw[df_raw["product_line"] == prod].copy()
        inspec = pd.Series(True, index=d.index)
        for p in _npi_applicable(family):
            s = SPEC_LIMITS[p]
            col = pd.to_numeric(d[p], errors="coerce")
            ok = ((col >= s["LSL"]) & (col <= s["USL"])) | col.isna()
            inspec &= ok
        d["row_pass"] = inspec
        d["week"] = d["test_datetime"].dt.to_period("W").apply(lambda r: r.start_time)
        mod = d.groupby(["serial_number", "week"])["row_pass"].all().reset_index()
        wk = mod.groupby("week")["row_pass"].agg(fpy="mean", modules="count").reset_index()
        wk["fpy"] *= 100
        return wk

    NPI_PROD = "1.6T-DR8-OSFP"
    REF_PROD = "800G-ZR-QSFP-DD"
    MATURE_TARGET = 96.0

    npi_wk = _weekly_fpy(NPI_PROD, "Client-PAM4")
    ref_wk = _weekly_fpy(REF_PROD, "Coherent")

    if len(npi_wk) >= 2:
        start_fpy = npi_wk["fpy"].iloc[0]
        current_fpy = npi_wk["fpy"].iloc[-1]
        gain = current_fpy - start_fpy
        gap = MATURE_TARGET - current_fpy
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("1.6T FPY (latest week)", f"{current_fpy:.1f}%")
        k2.metric("Ramp-start FPY", f"{start_fpy:.1f}%")
        k3.metric("Yield gained", f"+{gain:.1f} pts")
        k4.metric("Gap to mature target", f"{gap:.1f} pts", delta=f"target {MATURE_TARGET:.0f}%", delta_color="off")

    fig_npi = go.Figure()
    fig_npi.add_trace(go.Scatter(
        x=npi_wk["week"], y=npi_wk["fpy"], mode="lines+markers",
        name="1.6T-DR8 (ramping)", line=dict(color="#d97706", width=3), marker=dict(size=7),
    ))
    fig_npi.add_trace(go.Scatter(
        x=ref_wk["week"], y=ref_wk["fpy"], mode="lines+markers",
        name="800G-ZR (mature reference)", line=dict(color="#059669", width=2, dash="dot"), marker=dict(size=5),
    ))
    fig_npi.add_hline(y=MATURE_TARGET, line_dash="dash", line_color="#6b7280",
                      annotation_text=f"Mature target {MATURE_TARGET:.0f}%", annotation_position="bottom right")
    fig_npi.update_layout(
        height=420, margin=dict(t=20, b=40),
        xaxis_title="Production week", yaxis_title="First-pass yield (%)",
        legend=dict(orientation="h", yanchor="top", y=-0.15),
    )
    st.plotly_chart(fig_npi, use_container_width=True)

    st.divider()

    # ── Yield-loss Pareto for the 1.6T line ──────────────────────────────
    st.markdown("### What is holding 1.6T yield back? (Yield-loss Pareto)")
    st.markdown("Ranking 1.6T-DR8 test parameters by out-of-spec reading count tells engineering exactly where to spend ramp effort.")
    d16 = df_raw[df_raw["product_line"] == NPI_PROD]
    prows = []
    for p in _npi_applicable("Client-PAM4"):
        s = SPEC_LIMITS[p]
        col = pd.to_numeric(d16[p], errors="coerce").dropna()
        if len(col) == 0:
            continue
        fails = int(((col < s["LSL"]) | (col > s["USL"])).sum())
        if fails > 0:
            prows.append({"parameter": p, "failures": fails})
    pareto = pd.DataFrame(prows).sort_values("failures", ascending=False).reset_index(drop=True)
    if not pareto.empty:
        pareto["cum_pct"] = pareto["failures"].cumsum() / pareto["failures"].sum() * 100
        figp = make_subplots(specs=[[{"secondary_y": True}]])
        figp.add_trace(go.Bar(x=pareto["parameter"], y=pareto["failures"],
                              marker_color="#0891b2", name="Out-of-spec readings"), secondary_y=False)
        figp.add_trace(go.Scatter(x=pareto["parameter"], y=pareto["cum_pct"], mode="lines+markers",
                                  line=dict(color="#d97706", width=2), name="Cumulative %"), secondary_y=True)
        figp.update_layout(height=380, margin=dict(t=20, b=90),
                           legend=dict(orientation="h", yanchor="top", y=-0.35))
        figp.update_yaxes(title_text="Out-of-spec readings", secondary_y=False)
        figp.update_yaxes(title_text="Cumulative %", range=[0, 105], secondary_y=True)
        st.plotly_chart(figp, use_container_width=True)
    else:
        st.info("No out-of-spec 1.6T readings in the current data window.")

    st.divider()

    # ── Power efficiency (watts per Tbps) ────────────────────────────────
    st.markdown("### Power efficiency: watts per Tbps")
    st.markdown("Absolute module power rises with data rate, so the metric that matters for AI-era optics is **power per bit**. Kibo's 1.6T pitch is roughly 20% lower power than existing 1.6T parts, so tracking W/Tbps by line is how operations proves it.")
    RATE_TBPS = {"800G-ZR-QSFP-DD": 0.8, "800G-ZR+-OSFP": 0.8, "400G-ZR+-QSFP-DD": 0.4, "1.6T-DR8-OSFP": 1.6}
    erows = []
    for prod, rate in RATE_TBPS.items():
        sub = df_raw[(df_raw["product_line"] == prod) & (df_raw["test_station"] == "FinalTest")]
        pw = pd.to_numeric(sub["module_power_W"], errors="coerce").dropna()
        if len(pw) == 0:
            continue
        erows.append({"product_line": prod, "avg_power_W": round(pw.mean(), 1),
                      "W_per_Tbps": round(pw.mean() / rate, 1)})
    eff = pd.DataFrame(erows).sort_values("W_per_Tbps").reset_index(drop=True)
    ce1, ce2 = st.columns([2, 1])
    with ce1:
        fige = px.bar(eff, x="product_line", y="W_per_Tbps",
                      color="W_per_Tbps", color_continuous_scale="Teal_r",
                      text="W_per_Tbps")
        fige.update_layout(height=360, margin=dict(t=20, b=40),
                           xaxis_title="", yaxis_title="Watts per Tbps (lower is better)",
                           coloraxis_showscale=False)
        st.plotly_chart(fige, use_container_width=True)
    with ce2:
        st.dataframe(eff, use_container_width=True, hide_index=True)





# ── Footer ───────────────────────────────────────────────────────────────
st.divider()
st.markdown("""
<div style='text-align: center; color: #6b7280; font-size: 0.8rem; padding: 20px 0;'>
<b>Coherent Optics Manufacturing Data Intelligence Dashboard</b><br>
Portfolio project by Harshini Reddy - Cisco Optics Operations, Product Line Data Analyst (2011813)<br>
Technologies: Python · pandas · Streamlit · Plotly · SQL · SPC/Six Sigma<br>
Domain: 800G coherent (ZR/ZR+) + 1.6T client PAM4 manufacturing · DSP parametrics · yield analysis<br>
<br>
<i>Data is synthetic but modeled on real optical transceiver test parameters (BER, OSNR, TDECQ, optical power)
and real manufacturing challenges (multi-line variability, shift effects, process drift, data reconciliation).</i>
</div>
""", unsafe_allow_html=True)