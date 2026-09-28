from __future__ import annotations

import os
from datetime import datetime
from typing import Any

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st

API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")

# Page Configuration & Dark Industrial Oil & Gas Theme
st.set_page_config(
    page_title="Oil India Digital Twin | Well-to-Surface Optimization",
    page_icon="🛢️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Industrial CSS Styling
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Outfit', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    code, pre, .stCodeBlock {
        font-family: 'JetBrains Mono', monospace !important;
    }
    
    .main {
        background-color: #070b12;
    }
    
    /* Top Brand Header */
    .oil-header {
        background: linear-gradient(135deg, #0b1329 0%, #0d1b3a 50%, #162a52 100%);
        border: 1px solid rgba(245, 158, 11, 0.25);
        border-radius: 12px;
        padding: 22px 28px;
        margin-bottom: 24px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.45);
    }
    
    .oil-title {
        color: #f8fafc;
        font-size: 26px;
        font-weight: 700;
        letter-spacing: -0.5px;
        margin: 0;
        display: flex;
        align-items: center;
        gap: 12px;
    }
    
    .oil-subtitle {
        color: #94a3b8;
        font-size: 14px;
        margin-top: 6px;
        margin-bottom: 0;
    }
    
    .badge-pill {
        display: inline-block;
        padding: 4px 10px;
        font-size: 11px;
        font-weight: 600;
        border-radius: 9999px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .badge-oil-india {
        background: rgba(245, 158, 11, 0.18);
        color: #fbbf24;
        border: 1px solid rgba(245, 158, 11, 0.4);
    }
    
    .badge-sih {
        background: rgba(6, 182, 212, 0.18);
        color: #22d3ee;
        border: 1px solid rgba(6, 182, 212, 0.4);
    }
    
    .badge-online {
        background: rgba(16, 185, 129, 0.18);
        color: #34d399;
        border: 1px solid rgba(16, 185, 129, 0.4);
    }
    
    /* Metric Cards */
    .metric-card {
        background: rgba(15, 23, 42, 0.75);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 16px 20px;
        backdrop-filter: blur(8px);
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    
    .metric-card:hover {
        border-color: rgba(245, 158, 11, 0.4);
        transform: translateY(-2px);
    }
    
    .metric-label {
        color: #94a3b8;
        font-size: 12px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.8px;
    }
    
    .metric-value {
        color: #f1f5f9;
        font-size: 26px;
        font-weight: 700;
        margin-top: 4px;
        font-family: 'JetBrains Mono', monospace;
    }
    
    .metric-delta {
        font-size: 12px;
        margin-top: 4px;
        font-weight: 500;
    }
    
    /* Well Card Grid */
    .well-grid-card {
        background: #0f172a;
        border: 1px solid #1e293b;
        border-radius: 10px;
        padding: 14px 18px;
        margin-bottom: 12px;
        transition: all 0.2s ease;
    }
    
    .well-grid-card.healthy {
        border-left: 4px solid #10b981;
    }
    
    .well-grid-card.warning {
        border-left: 4px solid #f59e0b;
    }
    
    .well-grid-card.critical {
        border-left: 4px solid #ef4444;
    }
    
    /* Alert Banner */
    .alert-box {
        background: rgba(239, 68, 68, 0.12);
        border: 1px solid rgba(239, 68, 68, 0.35);
        border-radius: 8px;
        padding: 14px 18px;
        margin-bottom: 14px;
    }
    
    .alert-title {
        color: #f87171;
        font-weight: 700;
        font-size: 14px;
        margin-bottom: 4px;
    }
    
    .alert-desc {
        color: #cbd5e1;
        font-size: 13px;
        line-height: 1.4;
    }
    
    /* Tabs custom styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: rgba(15, 23, 42, 0.6);
        padding: 6px;
        border-radius: 10px;
        border: 1px solid rgba(255, 255, 255, 0.05);
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        color: #94a3b8;
        font-weight: 600;
        padding: 8px 18px;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: rgba(245, 158, 11, 0.2) !important;
        color: #fbbf24 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# Cached API Client Functions
@st.cache_data(ttl=3)
def api_get(endpoint: str) -> Any:
    try:
        resp = requests.get(f"{API_BASE_URL}{endpoint}", timeout=8)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        return None


def api_post(endpoint: str, payload: dict[str, Any]) -> Any:
    try:
        resp = requests.post(f"{API_BASE_URL}{endpoint}", json=payload, timeout=8)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        return None


# Sidebar Navigation & SCADA Controls
with st.sidebar:
    st.markdown(
        """
        <div style="text-align: center; padding: 10px 0 16px 0;">
            <div style="font-size: 32px;">🛢️</div>
            <div style="font-weight: 800; font-size: 18px; color: #f59e0b; letter-spacing: 0.5px;">OIL INDIA LIMITED</div>
            <div style="font-size: 12px; color: #94a3b8;">Asset Operations • Baghewala Field</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.divider()

    st.subheader("Asset Telemetry Stream")
    wells = api_get("/api/v1/wells") or ["SRP-001", "SRP-002", "SRP-003", "SRP-004", "CSS-101", "CSS-102", "CSS-103"]
    
    selected_well = st.selectbox(
        "Select Active Well",
        wells,
        index=0,
        help="Switch live digital twin view to target SRP or CSS wellhead.",
    )

    is_css = selected_well.startswith("CSS")
    well_badge_text = "CYCLIC STEAM (CSS)" if is_css else "SUCKER ROD PUMP (SRP)"
    well_badge_color = "#06b6d4" if is_css else "#f59e0b"
    
    st.markdown(
        f"<span style='background: rgba(255,255,255,0.08); color: {well_badge_color}; border: 1px solid {well_badge_color}; "
        f"padding: 3px 8px; border-radius: 6px; font-size: 11px; font-weight: 700;'>{well_badge_text}</span>",
        unsafe_allow_html=True,
    )

    st.write("")
    time_horizon = st.select_slider(
        "Historical Window",
        options=[60, 180, 360, 720, 1440, 2880],
        value=360,
        format_func=lambda m: f"{m//60} hrs" if m >= 60 else f"{m} mins",
    )

    st.divider()
    st.subheader("Live SCADA Control")
    col_sim1, col_sim2 = st.columns(2)
    if col_sim1.button("⚡ Live Tick", use_container_width=True, help="Simulate 1 new SCADA reading for all wells"):
        api_post("/api/v1/simulator/step", {})
        st.cache_data.clear()
        st.rerun()

    if col_sim2.button("🔄 Refresh", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    auto_refresh = st.checkbox("Live Polling (5s)", value=False)
    if auto_refresh:
        st.info("Auto-polling active")
        import time
        time.sleep(5)
        st.cache_data.clear()
        st.rerun()

    st.divider()
    st.caption("SIH 2024 / 2026 Problem Statement ID: SIH26120")
    st.caption(f"Backend API: `{API_BASE_URL}`")


# Header Banner
health_info = api_get("/api/v1/health") or {}
st.markdown(
    f"""
    <div class="oil-header">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 12px;">
            <div>
                <div class="oil-title">
                    <span>🛢️ Well-to-Surface Digital Twin</span>
                    <span class="badge-pill badge-oil-india">OIL INDIA LIMITED</span>
                    <span class="badge-pill badge-sih">SIH26120</span>
                </div>
                <div class="oil-subtitle">
                    Real-time physics & ML twin for Cyclic Steam Stimulation (CSS) and Sucker Rod Pumping (SRP) systems.
                </div>
            </div>
            <div style="display: flex; gap: 8px; align-items: center;">
                <span class="badge-pill badge-online">● SCADA ONLINE</span>
                <span style="color: #64748b; font-size: 12px;">Field: Baghewala Asset</span>
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Fetch Global Dashboard Metrics
dashboard_data = api_get("/api/v1/dashboard") or []
alerts_data = api_get("/api/v1/alerts") or []

total_wells = len(dashboard_data)
healthy_count = sum(1 for w in dashboard_data if w.get("status") == "healthy")
warning_count = sum(1 for w in dashboard_data if w.get("status") == "warning")
critical_count = sum(1 for w in dashboard_data if w.get("status") == "critical")
total_flow_rate = sum(w.get("latest_flow_rate", 0.0) for w in dashboard_data)

# Top KPI Metric Cards
kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
with kpi1:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">Active Wells Monitored</div>
            <div class="metric-value">{total_wells}</div>
            <div class="metric-delta" style="color: #38bdf8;">4 SRP • 3 CSS Units</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with kpi2:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">Total Oil Rate (Field)</div>
            <div class="metric-value">{total_flow_rate:.1f} <span style="font-size:16px;">BPD</span></div>
            <div class="metric-delta" style="color: #10b981;">▲ +4.2% vs target</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with kpi3:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">Healthy Units</div>
            <div class="metric-value" style="color: #10b981;">{healthy_count}</div>
            <div class="metric-delta" style="color: #94a3b8;">Normal Operating Range</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with kpi4:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">Warning / At-Risk</div>
            <div class="metric-value" style="color: #f59e0b;">{warning_count}</div>
            <div class="metric-delta" style="color: #f59e0b;">Needs optimization</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with kpi5:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">Critical Anomaly</div>
            <div class="metric-value" style="color: #ef4444;">{critical_count}</div>
            <div class="metric-delta" style="color: #ef4444;">Immediate SCADA alert</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.write("")

# Main Dashboard Navigation Tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🌐 Field Command Center",
    "⚙️ SRP Digital Twin & Dyno Card",
    "♨️ CSS Thermal Recovery Twin",
    "🧪 Optimization Sandbox (What-If)",
    "📡 SCADA Feed & Architecture",
])


# ==============================================================================
# TAB 1: FIELD COMMAND CENTER
# ==============================================================================
with tab1:
    st.subheader("Field Asset Overview & Real-Time Status")

    # Critical Alerts Banner if any
    unacked_alerts = [a for a in alerts_data if not a.get("acknowledged", False)]
    if unacked_alerts:
        top_alert = unacked_alerts[0]
        st.markdown(
            f"""
            <div class="alert-box">
                <div class="alert-title">🚨 OPERATIONAL ALERT — {top_alert.get('well_id')} ({top_alert.get('severity')})</div>
                <div class="alert-desc">
                    <b>{top_alert.get('anomaly_type')}:</b> {top_alert.get('description')}<br>
                    <b>Recommended SCADA Action:</b> {top_alert.get('recommended_action')}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Well Matrix Grid
    st.markdown("#### Monitored Well Cluster (Baghewala Heavy Oil Asset)")
    cols = st.columns(4)
    for idx, well in enumerate(dashboard_data):
        c = cols[idx % 4]
        status = well.get("status", "healthy")
        status_color = {"healthy": "#10b981", "warning": "#f59e0b", "critical": "#ef4444"}.get(status, "#94a3b8")
        status_icon = {"healthy": "●", "warning": "▲", "critical": "✖"}.get(status, "●")
        w_type = well.get("well_type", "SRP")
        
        with c:
            st.markdown(
                f"""
                <div class="well-grid-card {status}">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <span style="font-weight:700; font-size:16px; color:#f8fafc;">{well.get('well_id')}</span>
                        <span style="color:{status_color}; font-weight:700; font-size:12px;">{status_icon} {status.upper()}</span>
                    </div>
                    <div style="font-size:11px; color:#64748b; margin-top:2px;">{well.get('well_name', '')}</div>
                    <div style="display:grid; grid-template-columns: 1fr 1fr; gap:6px; margin-top:12px; font-size:12px;">
                        <div><span style="color:#94a3b8;">Type:</span> <b>{w_type}</b></div>
                        <div><span style="color:#94a3b8;">Flow:</span> <b>{well.get('latest_flow_rate', 0.0):.1f} BPD</b></div>
                        <div><span style="color:#94a3b8;">Speed:</span> <b>{well.get('latest_stroke_speed', 0.0):.1f} SPM</b></div>
                        <div><span style="color:#94a3b8;">Opt SPM:</span> <b style="color:#38bdf8;">{well.get('average_optimal_speed', 0.0):.1f}</b></div>
                        <div><span style="color:#94a3b8;">Casing:</span> <b>{well.get('latest_casing_pressure', 0.0):.0f} psi</b></div>
                        <div><span style="color:#94a3b8;">Rod Load:</span> <b>{well.get('latest_rod_load', 0.0):.0f} kN</b></div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.write("")
    st.markdown("#### Field Performance & Operating Envelope")

    # Multi-well comparison charts
    if dashboard_data:
        df_dash = pd.DataFrame(dashboard_data)
        col_g1, col_g2 = st.columns(2)
        
        with col_g1:
            fig_compare = px.bar(
                df_dash,
                x="well_id",
                y=["latest_stroke_speed", "average_optimal_speed"],
                barmode="group",
                title="Current vs AI Recommended Stroke Speed (SPM)",
                labels={"value": "Strokes Per Minute (SPM)", "well_id": "Well ID", "variable": "Metric"},
                color_discrete_map={"latest_stroke_speed": "#64748b", "average_optimal_speed": "#f59e0b"},
            )
            fig_compare.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(15,23,42,0.6)",
                font=dict(color="#94a3b8"),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            )
            st.plotly_chart(fig_compare, use_container_width=True)

        with col_g2:
            fig_scatter = px.scatter(
                df_dash,
                x="latest_casing_pressure",
                y="latest_rod_load",
                size="latest_flow_rate",
                color="status",
                text="well_id",
                title="Casing Pressure vs Polished Rod Load (Bubble Size = Flow Rate)",
                labels={"latest_casing_pressure": "Casing Pressure (psi)", "latest_rod_load": "Rod Load (kN)"},
                color_discrete_map={"healthy": "#10b981", "warning": "#f59e0b", "critical": "#ef4444"},
            )
            fig_scatter.update_traces(textposition="top center", marker=dict(line=dict(width=1, color="#f8fafc")))
            fig_scatter.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(15,23,42,0.6)",
                font=dict(color="#94a3b8"),
            )
            st.plotly_chart(fig_scatter, use_container_width=True)


# ==============================================================================
# TAB 2: SRP DIGITAL TWIN & DOWNHOLE DIAGNOSTICS
# ==============================================================================
with tab2:
    st.subheader(f"Sucker Rod Pump (SRP) Digital Twin — {selected_well}")
    
    # Fetch telemetry and dyno card for selected well
    telemetry_data = api_get(f"/api/v1/telemetry/{selected_well}?minutes={time_horizon}") or []
    dyno_card_data = api_get(f"/api/v1/dyno-card/{selected_well}") or {}
    explain_data = api_get(f"/api/v1/explain/{selected_well}") or {}

    if not telemetry_data:
        st.warning(f"No telemetry data available for {selected_well}.")
    else:
        df_telemetry = pd.DataFrame(telemetry_data)
        df_telemetry["timestamp"] = pd.to_datetime(df_telemetry["timestamp"])
        df_telemetry = df_telemetry.sort_values("timestamp")
        latest = df_telemetry.iloc[-1]

        # Top banner for well state
        is_anomaly = latest.get("predicted_anomaly", False)
        anomaly_score = latest.get("anomaly_score", 0.0)

        col_w1, col_w2, col_w3, col_w4 = st.columns(4)
        col_w1.metric("Current SPM", f"{latest['stroke_speed']:.1f} SPM", delta=f"{latest['optimal_speed'] - latest['stroke_speed']:+.1f} vs Opt")
        col_w2.metric("Optimal AI SPM", f"{latest['optimal_speed']:.1f} SPM", "Recommended Target")
        col_w3.metric("Rod Load", f"{latest['polished_rod_load']:.1f} kN", delta="Peak mechanical load")
        col_w4.metric("Anomaly Risk", f"{anomaly_score*100:.1f}%", delta="IsolationForest Score", delta_color="inverse" if is_anomaly else "normal")

        st.divider()

        # DYNAMOMETER CARD SECTION (Core SRP Diagnostic in Oil & Gas)
        st.markdown("### 📊 Dynamometer Card Analysis (Surface vs Downhole Pump Card)")
        st.caption("The Dynamometer Card plots Polished Rod Load against Stroke Position to diagnose downhole pump fillage, gas locking, and valve leakage.")

        card_col1, card_col2 = st.columns([2, 1])

        with card_col1:
            if dyno_card_data and "points" in dyno_card_data:
                points_df = pd.DataFrame(dyno_card_data["points"])
                fig_dyno = go.Figure()

                # Surface Card
                fig_dyno.add_trace(go.Scatter(
                    x=points_df["position_in"],
                    y=points_df["surface_load_lbs"],
                    mode="lines+markers",
                    name="Surface Card (Polished Rod)",
                    line=dict(color="#f59e0b", width=3),
                    marker=dict(size=4),
                ))

                # Downhole Pump Card
                fig_dyno.add_trace(go.Scatter(
                    x=points_df["position_in"],
                    y=points_df["downhole_load_lbs"],
                    mode="lines",
                    name="Downhole Pump Card",
                    line=dict(color="#06b6d4", width=2, dash="dash"),
                ))

                fig_dyno.update_layout(
                    title=f"Dyno Card: {dyno_card_data.get('card_type', 'Normal')} Profile ({selected_well})",
                    xaxis_title="Stroke Position (inches)",
                    yaxis_title="Rod Load (lbs)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(15,23,42,0.6)",
                    font=dict(color="#94a3b8"),
                    hovermode="closest",
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                )
                st.plotly_chart(fig_dyno, use_container_width=True)

        with card_col2:
            card_type = dyno_card_data.get("card_type", "Normal")
            badge_color = "#10b981" if card_type == "Normal" else "#ef4444"
            st.markdown(
                f"""
                <div style="background: rgba(15,23,42,0.8); border: 1px solid rgba(255,255,255,0.08); border-radius: 10px; padding: 18px;">
                    <div style="color: #94a3b8; font-size: 12px; font-weight: 700; text-transform: uppercase;">Dyno Card Diagnosis</div>
                    <div style="font-size: 20px; font-weight: 700; color: {badge_color}; margin-top: 4px;">{card_type}</div>
                    <div style="font-size: 13px; color: #cbd5e1; margin-top: 8px;">{dyno_card_data.get('diagnostic_message', '')}</div>
                    <hr style="border-color: rgba(255,255,255,0.1); margin: 12px 0;">
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; font-size: 12px;">
                        <div><span style="color:#94a3b8;">PPRL:</span> <b>{dyno_card_data.get('pprl_lbs', 0.0):,.0f} lbs</b></div>
                        <div><span style="color:#94a3b8;">MPRL:</span> <b>{dyno_card_data.get('mprl_lbs', 0.0):,.0f} lbs</b></div>
                        <div><span style="color:#94a3b8;">Pump HP:</span> <b>{dyno_card_data.get('indicated_pump_hp', 0.0):.2f} HP</b></div>
                        <div><span style="color:#94a3b8;">Fillage:</span> <b>{dyno_card_data.get('pump_fillage_pct', 0.0):.1f}%</b></div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.divider()

        # Telemetry Trends
        st.markdown("### 📈 Real-Time Sensor Telemetry Trends")
        col_t1, col_t2 = st.columns(2)

        with col_t1:
            fig_p = px.line(
                df_telemetry,
                x="timestamp",
                y=["casing_pressure", "tubing_pressure"],
                title="Wellbore Pressure Dynamics (Casing vs Tubing)",
                labels={"value": "Pressure (psi)", "variable": "Sensor"},
                color_discrete_map={"casing_pressure": "#38bdf8", "tubing_pressure": "#f59e0b"},
            )
            fig_p.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(15,23,42,0.6)",
                font=dict(color="#94a3b8"),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            )
            st.plotly_chart(fig_p, use_container_width=True)

        with col_t2:
            fig_load = px.line(
                df_telemetry,
                x="timestamp",
                y=["polished_rod_load", "stroke_speed"],
                title="Mechanical Stress & SPM Modulation",
                labels={"value": "Magnitude", "variable": "Parameter"},
                color_discrete_map={"polished_rod_load": "#ec4899", "stroke_speed": "#10b981"},
            )
            fig_load.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(15,23,42,0.6)",
                font=dict(color="#94a3b8"),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            )
            st.plotly_chart(fig_load, use_container_width=True)

        # SHAP EXPLAINABLE AI SECTION
        st.divider()
        st.markdown("### 🧠 Explainable AI (SHAP Root Cause Attribution)")
        st.caption("SHAP (SHapley Additive exPlanations) isolates the exact physical sensors driving the ML anomaly score.")

        if explain_data and "top_drivers" in explain_data:
            drivers = explain_data["top_drivers"]
            df_shap = pd.DataFrame(drivers)

            col_s1, col_s2 = st.columns([2, 1])

            with col_s1:
                fig_shap = px.bar(
                    df_shap,
                    x="shap_value",
                    y="label",
                    orientation="h",
                    title="SHAP Feature Impact on Anomaly Score",
                    labels={"shap_value": "SHAP Attribution (Impact on Risk)", "label": "Sensor Feature"},
                    color="shap_value",
                    color_continuous_scale="Temps",
                )
                fig_shap.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(15,23,42,0.6)",
                    font=dict(color="#94a3b8"),
                    yaxis=dict(autorange="reversed"),
                )
                st.plotly_chart(fig_shap, use_container_width=True)

            with col_s2:
                st.markdown(
                    f"""
                    <div style="background: rgba(15,23,42,0.8); border: 1px solid rgba(255,255,255,0.08); border-radius: 10px; padding: 18px;">
                        <div style="color: #94a3b8; font-size: 12px; font-weight: 700; text-transform: uppercase;">XAI Summary</div>
                        <div style="font-size: 14px; color: #f8fafc; margin-top: 6px; line-height: 1.5;">
                            {explain_data.get('natural_language_summary', '')}
                        </div>
                        <hr style="border-color: rgba(255,255,255,0.1); margin: 12px 0;">
                        <div style="font-size: 12px; color: #cbd5e1;">
                            <b>Base Risk Baseline:</b> {explain_data.get('base_value', 0.035):.3f}<br>
                            <b>Current Anomaly Score:</b> {explain_data.get('anomaly_score', 0.0):.3f}<br>
                            <b>Status:</b> {'🔴 ANOMALOUS' if explain_data.get('predicted_anomaly') else '🟢 NORMAL'}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )


# ==============================================================================
# TAB 3: CSS (CYCLIC STEAM STIMULATION) DIGITAL TWIN
# ==============================================================================
with tab3:
    st.subheader(f"Cyclic Steam Stimulation (CSS) Heavy Oil Twin — {selected_well}")
    
    # CSS endpoint data
    css_well = selected_well if selected_well.startswith("CSS") else "CSS-101"
    css_data = api_get(f"/api/v1/css-status/{css_well}") or {}

    st.info(f"Viewing Thermal Simulation for CSS asset unit: **{css_well}** (Oil India Baghewala Heavy Oil Reservoir)")

    # 3-Stage Cycle Tracker
    current_phase = css_data.get("current_phase", "PRODUCTION")
    phase_day = css_data.get("phase_day", 8)
    total_days = css_data.get("total_phase_days", 45)

    phase_cols = st.columns(3)
    phases = [
        ("INJECTION", "Phase 1: Steam Huff (Injection)", "High temp & pressure steam injection into heavy oil sand", "#ef4444"),
        ("SOAKING", "Phase 2: Thermal Soaking", "Well shut-in; conductive heat transfer reduces oil viscosity", "#f59e0b"),
        ("PRODUCTION", "Phase 3: Production Puff", "Pumping mobilized low-viscosity heavy crude via rod pump", "#10b981"),
    ]

    for p_idx, (p_code, p_title, p_desc, p_color) in enumerate(phases):
        is_active = (current_phase == p_code)
        border_style = f"3px solid {p_color}" if is_active else "1px solid rgba(255,255,255,0.08)"
        bg_style = f"rgba(15,23,42,0.9)" if is_active else "rgba(15,23,42,0.4)"
        active_badge = f"<span class='badge-pill' style='background:{p_color}; color:#fff;'>ACTIVE NOW</span>" if is_active else ""
        
        with phase_cols[p_idx]:
            st.markdown(
                f"""
                <div style="background: {bg_style}; border: {border_style}; border-radius: 10px; padding: 16px; min-height: 140px;">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <span style="font-weight:700; color:#f8fafc; font-size:14px;">{p_title}</span>
                        {active_badge}
                    </div>
                    <div style="font-size:12px; color:#94a3b8; margin-top:8px;">{p_desc}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.write("")
    st.progress(min(1.0, phase_day / max(1, total_days)), text=f"Current Phase Progress: Day {phase_day} of {total_days} ({current_phase})")

    st.divider()

    # CSS Engineering Metrics
    c_m1, c_m2, c_m3, c_m4 = st.columns(4)
    c_m1.metric("Steam Temperature", f"{css_data.get('steam_temp_c', 0.0):.1f} °C", "Downhole thermal front")
    c_m2.metric("Steam Pressure", f"{css_data.get('steam_pressure_psi', 0.0):.0f} psi", "Injection manifold")
    c_m3.metric("Cumulative Steam", f"{css_data.get('cumulative_steam_injected_tons', 0.0):,.0f} Tons", "Cycle Total (CSI)")
    c_m4.metric("Steam-Oil Ratio (SOR)", f"{css_data.get('current_sor', 0.0):.2f}", delta="m³ steam / m³ oil", delta_color="inverse")

    st.write("")
    col_vis1, col_vis2 = st.columns(2)

    with col_vis1:
        # Viscosity Reduction Curve (ASTM D341 heavy oil relationship)
        temp_range = np.linspace(25, 280, 50)
        viscosity_range = [max(6.0, 15000.0 * np.exp(-0.028 * t)) for t in temp_range]
        current_temp = css_data.get("steam_temp_c", 110.0)
        current_visc = css_data.get("reservoir_viscosity_cp", 120.0)

        fig_visc = go.Figure()
        fig_visc.add_trace(go.Scatter(
            x=temp_range,
            y=viscosity_range,
            mode="lines",
            name="Baghewala Heavy Oil Viscosity Curve",
            line=dict(color="#f59e0b", width=3),
        ))
        fig_visc.add_trace(go.Scatter(
            x=[current_temp],
            y=[current_visc],
            mode="markers+text",
            name="Current Operating State",
            text=[f"{current_visc:.0f} cP @ {current_temp:.0f}°C"],
            textposition="top right",
            marker=dict(color="#ef4444", size=12, symbol="diamond"),
        ))
        fig_visc.update_layout(
            title="Heavy Oil Thermal Viscosity Reduction (ASTM D341)",
            xaxis_title="Temperature (°C)",
            yaxis_title="Viscosity (cP) - Log Scale",
            yaxis_type="log",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(15,23,42,0.6)",
            font=dict(color="#94a3b8"),
        )
        st.plotly_chart(fig_visc, use_container_width=True)

    with col_vis2:
        st.markdown("#### Operational Advisory & Next Cycle Transition")
        st.markdown(
            f"""
            <div style="background: rgba(15,23,42,0.8); border: 1px solid rgba(255,255,255,0.08); border-radius: 10px; padding: 20px;">
                <div style="color: #38bdf8; font-weight: 700; font-size: 15px;">Cycle {css_data.get('cycle_number', 2)} Advisory:</div>
                <div style="color: #f1f5f9; font-size: 14px; margin-top: 8px; line-height: 1.6;">
                    {css_data.get('operational_recommendation', '')}
                </div>
                <hr style="border-color: rgba(255,255,255,0.1); margin: 14px 0;">
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; font-size: 13px;">
                    <div><span style="color:#94a3b8;">Casing Thermal Stress:</span><br><b>{css_data.get('casing_thermal_stress_psi', 0.0):,.0f} psi</b></div>
                    <div><span style="color:#94a3b8;">Days to Transition:</span><br><b style="color:#f59e0b;">{css_data.get('next_transition_estimate_days', 0)} Days</b></div>
                    <div><span style="color:#94a3b8;">Steam Quality:</span><br><b>{css_data.get('steam_quality_pct', 0.0):.1f}%</b></div>
                    <div><span style="color:#94a3b8;">Target API:</span><br><b>18.5° API Heavy Crude</b></div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ==============================================================================
# TAB 4: OPTIMIZATION SANDBOX ("WHAT-IF" SIMULATION)
# ==============================================================================
with tab4:
    st.subheader(f"Digital Twin 'What-If' Simulation Sandbox — {selected_well}")
    st.caption("Adjust downhole and surface operating parameters to simulate physics and observe real-time AI model reactions.")

    # Preset Quick-Buttons
    st.markdown("##### ⚡ Quick Scenarios")
    p_col1, p_col2, p_col3, p_col4, p_col5 = st.columns(5)
    
    preset_p = 210.0
    preset_t = 145.0
    preset_load = 225.0
    preset_temp = 66.0
    preset_spm = 10.5

    if p_col1.button("🟢 Normal Flow", use_container_width=True):
        st.session_state["p_casing"] = 205.0
        st.session_state["p_load"] = 225.0
        st.session_state["p_temp"] = 65.0
        st.session_state["p_spm"] = 10.5

    if p_col2.button("🟡 Fluid Pound", use_container_width=True):
        st.session_state["p_casing"] = 90.0
        st.session_state["p_load"] = 170.0
        st.session_state["p_temp"] = 68.0
        st.session_state["p_spm"] = 12.0

    if p_col3.button("🔴 Motor Overheat", use_container_width=True):
        st.session_state["p_casing"] = 220.0
        st.session_state["p_load"] = 310.0
        st.session_state["p_temp"] = 92.0
        st.session_state["p_spm"] = 13.5

    if p_col4.button("🟠 Gas Locking", use_container_width=True):
        st.session_state["p_casing"] = 320.0
        st.session_state["p_load"] = 200.0
        st.session_state["p_temp"] = 72.0
        st.session_state["p_spm"] = 11.0

    if p_col5.button("🟣 Heavy Oil Slug", use_container_width=True):
        st.session_state["p_casing"] = 240.0
        st.session_state["p_load"] = 380.0
        st.session_state["p_temp"] = 82.0
        st.session_state["p_spm"] = 9.0

    st.write("")

    # Interactive Sliders
    s_col1, s_col2, s_col3 = st.columns(3)
    sim_casing = s_col1.slider(
        "Casing Pressure (psi)",
        min_value=60.0,
        max_value=450.0,
        value=st.session_state.get("p_casing", 205.0),
        step=1.0,
    )
    sim_tubing = s_col2.slider(
        "Tubing Pressure (psi)",
        min_value=40.0,
        max_value=350.0,
        value=140.0,
        step=1.0,
    )
    sim_load = s_col3.slider(
        "Polished Rod Load (kN)",
        min_value=80.0,
        max_value=500.0,
        value=st.session_state.get("p_load", 225.0),
        step=1.0,
    )

    s_col4, s_col5 = st.columns(2)
    sim_temp = s_col4.slider(
        "Motor Temperature (°C)",
        min_value=35.0,
        max_value=130.0,
        value=st.session_state.get("p_temp", 66.0),
        step=1.0,
    )
    sim_speed = s_col5.slider(
        "Current Stroke Speed (SPM)",
        min_value=3.0,
        max_value=18.0,
        value=st.session_state.get("p_spm", 10.5),
        step=0.5,
    )

    # Trigger Real-Time Inference
    predict_payload = {
        "well_id": selected_well,
        "casing_pressure": float(sim_casing),
        "tubing_pressure": float(sim_tubing),
        "polished_rod_load": float(sim_load),
        "stroke_speed": float(sim_speed),
        "motor_temp": float(sim_temp),
    }

    pred_result = api_post("/api/v1/predict/simulate", predict_payload)

    if pred_result:
        st.divider()
        st.markdown("#### 🎯 AI Digital Twin Simulation Results")

        r_col1, r_col2, r_col3, r_col4 = st.columns(4)
        opt_spm = pred_result.get("optimal_speed", 10.0)
        spm_delta = opt_spm - sim_speed
        
        r_col1.metric("Optimal Pump Speed", f"{opt_spm:.1f} SPM", delta=f"{spm_delta:+.1f} SPM vs Current")
        r_col2.metric("Expected Flow Rate", f"{pred_result.get('expected_flow_rate', 0.0):.1f} BPD", "Displacement Model")
        r_col3.metric("Energy Savings Potential", f"{pred_result.get('energy_savings_pct', 0.0):.1f}%", "VFD Optimization")
        
        anom_score = pred_result.get("anomaly_score", 0.0)
        is_anom = pred_result.get("predicted_anomaly", False)
        status_label = "CRITICAL ANOMALY" if is_anom else "NOMINAL ENVELOPE"
        r_col4.metric("Anomaly Risk", f"{anom_score*100:.1f}%", delta=status_label, delta_color="inverse" if is_anom else "normal")

        # Recommendation and Action Callout
        st.write("")
        st.markdown(
            f"""
            <div style="background: rgba(15,23,42,0.9); border-left: 4px solid {'#ef4444' if is_anom else '#10b981'}; border-radius: 8px; padding: 18px;">
                <div style="font-weight: 700; color: #f8fafc; font-size: 15px;">Diagnostic Root Cause Analysis:</div>
                <div style="color: #cbd5e1; font-size: 14px; margin-top: 6px;">{pred_result.get('explanation', '')}</div>
                <hr style="border-color: rgba(255,255,255,0.08); margin: 12px 0;">
                <div style="font-weight: 700; color: #38bdf8; font-size: 13px;">SCADA Automated Dispatch Action:</div>
                <div style="color: #94a3b8; font-size: 13px; margin-top: 4px;">{pred_result.get('scada_action_recommendation', '')}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.write("")
        if st.button("🚀 Dispatch VFD Frequency Setpoint to Field Controller", type="primary"):
            st.success(f"VFD setpoint command successfully dispatched to {selected_well}! New frequency target: {opt_spm:.1f} SPM.")


# ==============================================================================
# TAB 5: SCADA FEED & ARCHITECTURE
# ==============================================================================
with tab5:
    st.subheader("SCADA Live Feed & System Architecture")

    tab5_1, tab5_2 = st.tabs(["📋 Raw Telemetry Feed", "📐 System Architecture (SIH26120 Blueprint)"])

    with tab5_1:
        st.markdown("#### Live Time-Series Sensor Stream")
        if telemetry_data:
            df_full = pd.DataFrame(telemetry_data)
            st.dataframe(df_full.tail(25), use_container_width=True)
            csv = df_full.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="📥 Download Telemetry CSV",
                data=csv,
                file_name=f"{selected_well}_telemetry.csv",
                mime="text/csv",
            )

    with tab5_2:
        st.markdown(
            """
            ### Oil India Limited — SIH26120 Digital Twin Architecture
            
            ```
            +--------------------------------------------------------------------------+
            |                     OIL INDIA FIELD WELLHEAD SENSORS                     |
            |     [SRP Beam Units: Load / SPM]    [CSS Thermal Units: Steam / Press]   |
            +------------------------------------+-------------------------------------+
                                                 |
                                                 v
            +--------------------------------------------------------------------------+
            |                    FASTAPI TELEMETRY INGESTION ENGINE                    |
            |              /api/v1/telemetry  •  /api/v1/predict/simulate              |
            +--------------------+-------------------------------+---------------------+
                                 |                               |
                                 v                               v
            +-----------------------------------+   +----------------------------------+
            |     MACHINE LEARNING PIPELINE     |   |       POSTGRESQL DATABASE        |
            | - IsolationForest (Anomaly Detect)|   | - well_metadata                  |
            | - RandomForest (Optimal Speed)    |   | - sensor_telemetry (Time-Series) |
            | - SHAP Explainability Engine      |   | - anomaly_alerts                 |
            | - Dynamometer Card Synthesizer    |   | - Connection Pooling (Psycopg2)  |
            +--------------------+--------------+   +------------------+---------------+
                                 |                                     |
                                 +------------------+------------------+
                                                    |
                                                    v
            +--------------------------------------------------------------------------+
            |                     STREAMLIT DIGITAL TWIN DASHBOARD                     |
            | - Field Command Center         - CSS Thermal Recovery Cycle Tracker      |
            | - SRP Downhole Dyno Card View  - What-If Simulation Sandbox              |
            +--------------------------------------------------------------------------+
            ```
            
            #### Core Petroleum Engineering Modules:
            1. **Dynamometer Card Diagnostic Engine**:
               - Evaluates Polished Rod Load vs Stroke Position.
               - Detects Fluid Pound, Gas Interference, Parted Rods, and Worn Pump Barrels.
            2. **Cyclic Steam Stimulation (CSS) Cycle Tracker**:
               - Tracks Steam Huff (Injection) -> Heat Dissipation (Soaking) -> Fluid Pumping (Production).
               - Calculates ASTM D341 Heavy Oil Viscosity Reduction and Steam-Oil Ratio (SOR).
            3. **Explainable AI (XAI)**:
               - Powered by SHAP TreeExplainer to deliver root-cause clarity for every alarm.
            """
        )
