import os
import sys
from datetime import datetime

# Ensure project root is in sys.path so 'forecast' and other modules are importable
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st

try:
    from forecast.recommendations import calculate_interregional_arbitrage
except ImportError:
    from forecast import calculate_interregional_arbitrage

# Page configuration
st.set_page_config(
    page_title="Malawi AgriPrice Intelligence | Nationwide",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for rich, modern aesthetics
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    
    h1, h2, h3, h4 {
        font-family: 'Outfit', sans-serif;
        font-weight: 600;
    }
    
    .hero-card {
        background: linear-gradient(135deg, #0b3b24 0%, #165b37 50%, #1f7a4b 100%);
        color: white;
        padding: 24px 30px;
        border-radius: 16px;
        margin-bottom: 22px;
        box-shadow: 0 10px 25px -5px rgba(16, 185, 129, 0.2);
        border: 1px solid rgba(255, 255, 255, 0.12);
    }
    
    .hero-title {
        font-size: 2.1rem;
        font-weight: 700;
        margin-bottom: 6px;
        letter-spacing: -0.5px;
    }
    
    .hero-subtitle {
        font-size: 1.02rem;
        color: #d1fae5;
        max-width: 950px;
        line-height: 1.5;
    }
    
    .metric-card {
        background: white;
        border-radius: 14px;
        padding: 18px 22px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.08);
    }
    
    .metric-label {
        font-size: 0.82rem;
        font-weight: 600;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 4px;
    }
    
    .metric-value {
        font-size: 1.75rem;
        font-weight: 700;
        color: #0f172a;
        margin-bottom: 4px;
    }
    
    .badge-hold {
        background-color: #dcfce7;
        color: #15803d;
        padding: 4px 12px;
        border-radius: 9999px;
        font-weight: 600;
        font-size: 0.85rem;
        display: inline-block;
        border: 1px solid #86efac;
    }
    
    .badge-sell {
        background-color: #fee2e2;
        color: #b91c1c;
        padding: 4px 12px;
        border-radius: 9999px;
        font-weight: 600;
        font-size: 0.85rem;
        display: inline-block;
        border: 1px solid #fca5a5;
    }
    
    .badge-monitor {
        background-color: #e0f2fe;
        color: #0369a1;
        padding: 4px 12px;
        border-radius: 9999px;
        font-weight: 600;
        font-size: 0.85rem;
        display: inline-block;
        border: 1px solid #bae6fd;
    }

    .badge-trade {
        background-color: #fef08a;
        color: #854d0e;
        padding: 4px 12px;
        border-radius: 9999px;
        font-weight: 600;
        font-size: 0.85rem;
        display: inline-block;
        border: 1px solid #fde047;
    }
    
    .info-card {
        background: #f8fafc;
        border-left: 4px solid #10b981;
        padding: 16px 20px;
        border-radius: 8px;
        margin: 12px 0;
    }
</style>
""", unsafe_allow_html=True)

# Helper functions to load data
@st.cache_data
def load_data():
    processed_path = os.path.join(PROJECT_ROOT, "data", "processed", "clean_malawi_all_regions_enriched_prices.csv")
    if not os.path.exists(processed_path):
        processed_path = os.path.join(PROJECT_ROOT, "data", "processed", "clean_northern_region_enriched_prices.csv")
        
    forecast_path = os.path.join(PROJECT_ROOT, "data", "forecasts", "crop_price_forecasts.csv")
    recs_path = os.path.join(PROJECT_ROOT, "data", "forecasts", "market_recommendations.csv")
    metrics_path = os.path.join(PROJECT_ROOT, "data", "forecasts", "model_evaluation_metrics.csv")
    arb_path = os.path.join(PROJECT_ROOT, "data", "forecasts", "regional_arbitrage_opportunities.csv")
    
    df_hist = pd.read_csv(processed_path) if os.path.exists(processed_path) else pd.DataFrame()
    df_fc = pd.read_csv(forecast_path) if os.path.exists(forecast_path) else pd.DataFrame()
    df_recs = pd.read_csv(recs_path) if os.path.exists(recs_path) else pd.DataFrame()
    df_metrics = pd.read_csv(metrics_path) if os.path.exists(metrics_path) else pd.DataFrame()
    df_arb = pd.read_csv(arb_path) if os.path.exists(arb_path) else pd.DataFrame()
    
    if not df_hist.empty:
        df_hist['date'] = pd.to_datetime(df_hist['date'])
    if not df_fc.empty:
        df_fc['date'] = pd.to_datetime(df_fc['date'])
        
    return df_hist, df_fc, df_recs, df_metrics, df_arb

df_hist, df_fc, df_recs, df_metrics, df_arb = load_data()

# Hero Banner
st.markdown("""
<div class="hero-card">
    <div class="hero-title">🌾 Malawi AgriPrice Intelligence Platform</div>
    <div class="hero-subtitle">
        Nationwide AI-driven crop price forecasting (2–4 weeks & seasonal 12 weeks) and strategic market advisory across <b>Northern</b>, <b>Central</b>, and <b>Southern</b> Malawi with dedicated regional machine learning models.
    </div>
</div>
""", unsafe_allow_html=True)

if df_hist.empty or df_fc.empty:
    st.error("Data pipeline outputs not found. Please run `automation/run_all.py` to generate multi-region forecasts and recommendations.")
    st.stop()

# Sidebar controls
st.sidebar.image("https://img.icons8.com/color/96/wheat.png", width=60)
st.sidebar.header("Navigation & Filters")

# 1. Region Selector
regions_in_data = sorted(df_hist['region'].unique().tolist()) if 'region' in df_hist.columns else ['Northern Region']
region_options = ["All Malawi (National View)"] + regions_in_data
selected_region = st.sidebar.selectbox("Select Target Region:", region_options, index=0)

# 2. Crop Selector
available_crops = sorted(df_hist['commodity'].unique().tolist())
selected_crop = st.sidebar.selectbox("Select Crop / Commodity:", available_crops, index=2 if 'Maize' in available_crops else 0)

# 3. Horizon slider
forecast_horizon = st.sidebar.select_slider(
    "Forecast Horizon:",
    options=[1, 2, 3, 6],
    value=3,
    format_func=lambda x: f"{x * 4} Weeks ({x} Months)"
)

st.sidebar.markdown("---")
st.sidebar.subheader("Visualization Settings")
show_confidence = st.sidebar.checkbox("Show 80% & 95% Confidence Cones", value=True)
show_lean_season = st.sidebar.checkbox("Highlight Lean Season (Dec–Mar)", value=True)
show_harvest_season = st.sidebar.checkbox("Highlight Harvest Season (Apr–Jun)", value=True)

st.sidebar.markdown("---")
st.sidebar.subheader("Arbitrage Freight Tariff")
freight_slider = st.sidebar.slider(
    "M1 Corridor Trucking Cost (MWK/kg):",
    min_value=80, max_value=300, value=140, step=10,
    help="Estimated freight and handling tariff between regional hubs (Lilongwe, Blantyre, Mzuzu)."
)

# Ground-Truth Calibration Tool in Sidebar
st.sidebar.markdown("---")
st.sidebar.subheader("🎯 Ground-Truth Triangulation")
st.sidebar.caption("Calibrate baseline with real-time field survey prices (e.g., IFPRI, FEWS NET, or local traders).")
enable_calibration = st.sidebar.checkbox(
    "Calibrate Field Price",
    value=False,
    help="When enabled, dynamically re-anchors model projections and metrics using your verified ground-truth price."
)

# Filter Data according to selections
is_national = selected_region == "All Malawi (National View)"

if not is_national:
    filtered_hist = df_hist[(df_hist['region'] == selected_region) & (df_hist['commodity'] == selected_crop)].sort_values('date')
    filtered_fc = df_fc[(df_fc['region'] == selected_region) & (df_fc['commodity'] == selected_crop)].sort_values('date').head(forecast_horizon)
    filtered_rec = df_recs[(df_recs['region'] == selected_region) & (df_recs['commodity'] == selected_crop)]
    region_recs_table = df_recs[df_recs['region'] == selected_region]
else:
    filtered_hist = df_hist[df_hist['commodity'] == selected_crop].sort_values('date')
    filtered_fc = df_fc[df_fc['commodity'] == selected_crop].sort_values('date')
    filtered_rec = pd.DataFrame()
    region_recs_table = df_recs

raw_baseline_price = float(filtered_hist['price'].iloc[-1]) if not filtered_hist.empty else 1000.0

if enable_calibration:
    calibrated_price = st.sidebar.number_input(
        f"Verified Field Price ({selected_crop} MWK/kg):",
        min_value=50.0,
        max_value=50000.0,
        value=float(round(raw_baseline_price, 1)),
        step=25.0,
        help="Input your verified real-world market price in MWK/kg."
    )
    calibration_factor = calibrated_price / raw_baseline_price if raw_baseline_price > 0 else 1.0
    calib_delta_pct = (calibration_factor - 1.0) * 100.0
    if abs(calib_delta_pct) > 0.05:
        st.sidebar.info(f"⚡ Baseline shifted from **{raw_baseline_price:,.0f} MWK** → **{calibrated_price:,.0f} MWK** ({calib_delta_pct:+.1f}%)")
        
    # Dynamically rescale forecast series
    if calibration_factor != 1.0 and not filtered_fc.empty:
        filtered_fc = filtered_fc.copy()
        for c in ['price_pred', 'price_lower_95', 'price_upper_95', 'price_lower_80', 'price_upper_80', 'prophet_pred', 'sarima_pred']:
            if c in filtered_fc.columns:
                filtered_fc[c] = (filtered_fc[c] * calibration_factor).round(2)
else:
    calibrated_price = raw_baseline_price
    calibration_factor = 1.0
    calib_delta_pct = 0.0

st.sidebar.caption("Data Sources: WFP VAM, FAMIS Malawi, Open-Meteo Weather, World Bank Open Data.")

# Main Tabs
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📊 Market Overview & Advisory",
    "📈 Price Forecast & Trajectory",
    "🗺️ Inter-Regional Arbitrage",
    "🌧️ Macro & Weather Drivers",
    "⚙️ What-If Scenario Simulator",
    "📄 Weekly Market Bulletin"
])

# ==========================================
# TAB 1: OVERVIEW & MARKET RECOMMENDATIONS
# ==========================================
with tab1:
    if enable_calibration and abs(calib_delta_pct) > 0.05:
        st.success(f"🎯 **Ground-Truth Calibration Active:** Model projections and KPI metrics dynamically re-anchored to verified market price of **{calibrated_price:,.0f} MWK/kg** ({calib_delta_pct:+.1f}% triangulation adjustment against historical baseline).")
        
    if not is_national:
        st.subheader(f"Market Signals: {selected_crop} — [{selected_region}]")
        
        current_p = calibrated_price if enable_calibration else (float(filtered_hist['price'].iloc[-1]) if not filtered_hist.empty else 0)
        last_date = filtered_hist['date'].iloc[-1].strftime('%B %Y') if not filtered_hist.empty else "N/A"
        
        if not filtered_rec.empty:
            rec_row = filtered_rec.iloc[0]
            p_4w = (rec_row['forecast_4w_mwk'] * calibration_factor) if enable_calibration else rec_row['forecast_4w_mwk']
            pct_4w = ((p_4w - current_p) / current_p * 100) if current_p > 0 else rec_row['pct_change_4w']
            p_12w = (rec_row['forecast_12w_mwk'] * calibration_factor) if enable_calibration else rec_row['forecast_12w_mwk']
            pct_12w = ((p_12w - current_p) / current_p * 100) if current_p > 0 else rec_row['pct_change_12w']
            badge = rec_row['action_badge']
            risk = rec_row['risk_level']
            summary_txt = rec_row['summary']
            inst_txt = rec_row['institutional_advice']
        else:
            p_4w, pct_4w, p_12w, pct_12w, badge, risk = current_p, 0, current_p, 0, "MONITOR", "Medium"
            summary_txt = "Monitor local markets."
            inst_txt = "Follow standard procurement schedules."

        # KPI row
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Current Price ({last_date})</div>
                <div class="metric-value">{current_p:,.0f} <span style="font-size: 1rem; color: #64748b;">MWK/kg</span></div>
                <div style="color: #64748b; font-size: 0.85rem;">Regional median in {selected_region.replace(' Region', '')}</div>
            </div>
            """, unsafe_allow_html=True)
            
        with col2:
            arrow_4w = "▲" if pct_4w >= 0 else "▼"
            color_4w = "#15803d" if pct_4w >= 0 else "#b91c1c"
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">4-Week Projection</div>
                <div class="metric-value">{p_4w:,.0f} <span style="font-size: 1rem; color: #64748b;">MWK/kg</span></div>
                <div style="color: {color_4w}; font-weight: 600; font-size: 0.95rem;">{arrow_4w} {abs(pct_4w):.1f}% in 4 weeks</div>
            </div>
            """, unsafe_allow_html=True)
            
        with col3:
            arrow_12w = "▲" if pct_12w >= 0 else "▼"
            color_12w = "#15803d" if pct_12w >= 0 else "#b91c1c"
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">12-Week Projection</div>
                <div class="metric-value">{p_12w:,.0f} <span style="font-size: 1rem; color: #64748b;">MWK/kg</span></div>
                <div style="color: {color_12w}; font-weight: 600; font-size: 0.95rem;">{arrow_12w} {abs(pct_12w):.1f}% in 12 weeks</div>
            </div>
            """, unsafe_allow_html=True)
            
        with col4:
            badge_class = "badge-hold" if "HOLD" in badge else ("badge-sell" if "SELL" in badge else "badge-monitor")
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Regional Recommendation</div>
                <div style="margin-top: 4px; margin-bottom: 8px;">
                    <span class="{badge_class}">{badge}</span>
                </div>
                <div style="color: #64748b; font-size: 0.85rem;">Volatility Risk: <strong>{risk}</strong></div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.subheader(f"Commodity Action Matrix ({selected_region})")
        
        display_cols = ['commodity', 'current_price_mwk', 'forecast_4w_mwk', 'pct_change_4w', 'forecast_12w_mwk', 'pct_change_12w', 'action_badge', 'risk_level']
        st.dataframe(
            region_recs_table[display_cols].rename(columns={
                'commodity': 'Commodity',
                'current_price_mwk': 'Current (MWK/kg)',
                'forecast_4w_mwk': '4-Week (MWK/kg)',
                'pct_change_4w': '4W % Change',
                'forecast_12w_mwk': '12-Week (MWK/kg)',
                'pct_change_12w': '12W % Change',
                'action_badge': 'Action Advice',
                'risk_level': 'Risk Rating'
            }),
            use_container_width=True,
            hide_index=True
        )
        
        # Stakeholder Guidance
        st.markdown("### Operational Stakeholder Guidance")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"""
            <div class="info-card">
                <h4 style="margin: 0 0 8px 0; color: #065f46;">🚜 Smallholder Farmers & Grain Cooperatives</h4>
                <p style="margin: 0; color: #1e293b; font-size: 0.95rem; line-height: 1.5;">{summary_txt}</p>
            </div>
            """, unsafe_allow_html=True)
        with c2:
            st.markdown(f"""
            <div class="info-card" style="border-left-color: #0284c7;">
                <h4 style="margin: 0 0 8px 0; color: #075985;">🏫 School Feeding Committees & Institutional Buyers</h4>
                <p style="margin: 0; color: #1e293b; font-size: 0.95rem; line-height: 1.5;">{inst_txt}</p>
            </div>
            """, unsafe_allow_html=True)
            
    else:
        # National Overview Mode
        st.subheader(f"National Cross-Regional Price Matrix: {selected_crop}")
        
        # Build side-by-side comparison across regions for selected crop
        latest_crop_df = df_hist[df_hist['commodity'] == selected_crop].groupby('region').tail(1)
        
        n_cols = st.columns(3)
        for idx, reg in enumerate(regions_in_data):
            reg_data = latest_crop_df[latest_crop_df['region'] == reg]
            reg_rec = df_recs[(df_recs['region'] == reg) & (df_recs['commodity'] == selected_crop)]
            
            p_val = float(reg_data['price'].iloc[0]) if not reg_data.empty else 0
            b_val = reg_rec['action_badge'].iloc[0] if not reg_rec.empty else "MONITOR"
            p12_val = reg_rec['pct_change_12w'].iloc[0] if not reg_rec.empty else 0
            
            with n_cols[idx]:
                badge_class = "badge-hold" if "HOLD" in b_val else ("badge-sell" if "SELL" in b_val else "badge-monitor")
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">{reg}</div>
                    <div class="metric-value">{p_val:,.0f} <span style="font-size: 0.9rem; color: #64748b;">MWK/kg</span></div>
                    <div style="margin: 6px 0;"><span class="{badge_class}">{b_val}</span></div>
                    <div style="color: {'#15803d' if p12_val >= 0 else '#b91c1c'}; font-size: 0.88rem; font-weight: 600;">12-Week Projection: {p12_val:+.1f}%</div>
                </div>
                """, unsafe_allow_html=True)
                
        st.markdown("<br>", unsafe_allow_html=True)
        st.subheader("All-Malawi Comprehensive Regional Action Matrix")
        
        display_cols = ['region', 'commodity', 'current_price_mwk', 'forecast_4w_mwk', 'pct_change_4w', 'forecast_12w_mwk', 'pct_change_12w', 'action_badge', 'risk_level']
        st.dataframe(
            df_recs[display_cols].rename(columns={
                'region': 'Region',
                'commodity': 'Commodity',
                'current_price_mwk': 'Current (MWK/kg)',
                'forecast_4w_mwk': '4-Week (MWK/kg)',
                'pct_change_4w': '4W % Change',
                'forecast_12w_mwk': '12-Week (MWK/kg)',
                'pct_change_12w': '12W % Change',
                'action_badge': 'Action Advice',
                'risk_level': 'Risk Rating'
            }),
            use_container_width=True,
            hide_index=True
        )

# ==========================================
# TAB 2: PRICE FORECAST & TRAJECTORY
# ==========================================
with tab2:
    if not is_national:
        st.subheader(f"Price Trajectory & Forecast Cone: {selected_crop} ({selected_region})")
        
        fig = go.Figure()
        recent_hist = filtered_hist.tail(36).copy()
        
        fig.add_trace(go.Scatter(
            x=recent_hist['date'], y=recent_hist['price'],
            mode='lines+markers', name=f'Historical Price ({selected_region.replace(" Region", "")})',
            line=dict(color='#0f766e', width=2.5), marker=dict(size=5, color='#0f766e')
        ))
        
        if 'price_ma_3m' in recent_hist.columns:
            fig.add_trace(go.Scatter(
                x=recent_hist['date'], y=recent_hist['price_ma_3m'],
                mode='lines', name='3-Month Moving Average',
                line=dict(color='#f59e0b', width=1.5, dash='dot')
            ))
            
        last_pt = pd.DataFrame([{
            'date': recent_hist['date'].iloc[-1],
            'price_pred': recent_hist['price'].iloc[-1],
            'price_lower_80': recent_hist['price'].iloc[-1],
            'price_upper_80': recent_hist['price'].iloc[-1],
            'price_lower_95': recent_hist['price'].iloc[-1],
            'price_upper_95': recent_hist['price'].iloc[-1]
        }])
        fc_plot = pd.concat([last_pt, filtered_fc], ignore_index=True)
        
        if show_confidence and 'price_upper_95' in fc_plot.columns:
            fig.add_trace(go.Scatter(
                x=fc_plot['date'], y=fc_plot['price_upper_95'],
                mode='lines', line=dict(width=0), showlegend=False, hoverinfo='skip'
            ))
            fig.add_trace(go.Scatter(
                x=fc_plot['date'], y=fc_plot['price_lower_95'],
                mode='lines', line=dict(width=0), fill='tonexty',
                fillcolor='rgba(16, 185, 129, 0.12)', name='95% Confidence Interval'
            ))
            fig.add_trace(go.Scatter(
                x=fc_plot['date'], y=fc_plot['price_upper_80'],
                mode='lines', line=dict(width=0), showlegend=False, hoverinfo='skip'
            ))
            fig.add_trace(go.Scatter(
                x=fc_plot['date'], y=fc_plot['price_lower_80'],
                mode='lines', line=dict(width=0), fill='tonexty',
                fillcolor='rgba(16, 185, 129, 0.22)', name='80% Confidence Interval'
            ))
            
        fig.add_trace(go.Scatter(
            x=fc_plot['date'], y=fc_plot['price_pred'],
            mode='lines+markers', name='Regional Ensemble Forecast',
            line=dict(color='#10b981', width=3, dash='solid'),
            marker=dict(size=6, color='#10b981')
        ))
        
        fig.update_layout(
            title=f"Monthly Price Forecast Cone — {selected_crop} ({selected_region})",
            xaxis_title="Timeline", yaxis_title="Price (MWK/kg)",
            hovermode="x unified", legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            plot_bgcolor="#ffffff", paper_bgcolor="#ffffff",
            margin=dict(l=20, r=20, t=60, b=20), height=500
        )
        st.plotly_chart(fig, use_container_width=True)
        
    else:
        # National comparison chart: All 3 regions on single plot
        st.subheader(f"Cross-Regional Price Trajectory Comparison: {selected_crop}")
        
        fig = go.Figure()
        region_colors = {
            "Northern Region": "#0284c7",
            "Central Region": "#10b981",
            "Southern Region": "#f59e0b"
        }
        
        for reg in regions_in_data:
            reg_hist = df_hist[(df_hist['region'] == reg) & (df_hist['commodity'] == selected_crop)].tail(36)
            reg_fc = df_fc[(df_fc['region'] == reg) & (df_fc['commodity'] == selected_crop)].head(forecast_horizon)
            
            c_color = region_colors.get(reg, "#64748b")
            
            fig.add_trace(go.Scatter(
                x=reg_hist['date'], y=reg_hist['price'],
                mode='lines', name=f'{reg.replace(" Region", "")} (Hist)',
                line=dict(color=c_color, width=2)
            ))
            
            if not reg_fc.empty and not reg_hist.empty:
                last_pt = pd.DataFrame([{'date': reg_hist['date'].iloc[-1], 'price_pred': reg_hist['price'].iloc[-1]}])
                fc_comb = pd.concat([last_pt, reg_fc[['date', 'price_pred']]], ignore_index=True)
                fig.add_trace(go.Scatter(
                    x=fc_comb['date'], y=fc_comb['price_pred'],
                    mode='lines+markers', name=f'{reg.replace(" Region", "")} (Forecast)',
                    line=dict(color=c_color, width=3, dash='dot'),
                    marker=dict(size=5)
                ))
                
        fig.update_layout(
            title=f"Multi-Region Historical & Projected Prices — {selected_crop}",
            xaxis_title="Date", yaxis_title="Price (MWK/kg)",
            hovermode="x unified", legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            plot_bgcolor="#ffffff", paper_bgcolor="#ffffff",
            margin=dict(l=20, r=20, t=60, b=20), height=520
        )
        st.plotly_chart(fig, use_container_width=True)

# ==========================================
# TAB 3: INTER-REGIONAL ARBITRAGE
# ==========================================
with tab3:
    st.subheader(f"Inter-Regional Price Spreads & Trade Flow Analysis")
    st.markdown("""
    Compare live and forecasted commodity prices between **Northern**, **Central**, and **Southern** markets.
    Arbitrage profitability accounts for freight transportation along the **M1 Transport Corridor**.
    """)
    
    # Recalculate dynamic arbitrage based on freight slider
    live_arb = calculate_interregional_arbitrage(df_hist, df_fc, freight_cost_mwk=float(freight_slider))
    
    # Crop filter for arbitrage
    arb_crop_df = live_arb[live_arb['commodity'] == selected_crop] if not live_arb.empty else pd.DataFrame()
    
    # Visual spread comparison
    st.markdown(f"#### Current Price Differential across Regions ({selected_crop})")
    curr_prices = df_hist[df_hist['commodity'] == selected_crop].groupby('region').tail(1)[['region', 'price']].copy()
    if enable_calibration and not is_national:
        curr_prices.loc[curr_prices['region'] == selected_region, 'price'] = calibrated_price
    
    if not curr_prices.empty:
        fig_bar = px.bar(
            curr_prices, x='region', y='price', color='region',
            color_discrete_map={"Northern Region": "#0284c7", "Central Region": "#10b981", "Southern Region": "#f59e0b"},
            text='price', labels={'price': 'Current Price (MWK/kg)', 'region': 'Region'}
        )
        fig_bar.update_traces(texttemplate='%{text:,.0f} MWK', textposition='outside')
        fig_bar.update_layout(showlegend=False, height=350, margin=dict(l=20, r=20, t=30, b=20))
        st.plotly_chart(fig_bar, use_container_width=True)
        
    if not arb_crop_df.empty:
        st.markdown(f"#### Cross-Regional Trade Corridors ({selected_crop})")
        for _, row in arb_crop_df.iterrows():
            is_opp = "TRADE OPPORTUNITY" in row['badge']
            card_border = "#10b981" if is_opp else ("#f59e0b" if "MARGINAL" in row['badge'] else "#e2e8f0")
            badge_cls = "badge-hold" if is_opp else ("badge-monitor" if "MARGINAL" in row['badge'] else "badge-sell")
            
            st.markdown(f"""
            <div style="background: white; border-left: 5px solid {card_border}; border-radius: 10px; padding: 16px 20px; margin-bottom: 12px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); border-top: 1px solid #e2e8f0; border-right: 1px solid #e2e8f0; border-bottom: 1px solid #e2e8f0;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                    <div style="font-size: 1.1rem; font-weight: 700; color: #0f172a;">
                        🚚 Route: {row['origin_region'].replace(' Region', '')} ➔ {row['destination_region'].replace(' Region', '')}
                    </div>
                    <div><span class="{badge_cls}">{row['badge']}</span></div>
                </div>
                <div style="font-size: 0.95rem; color: #334155; margin-bottom: 8px;">
                    {row['action_summary']}
                </div>
                <div style="display: flex; gap: 20px; font-size: 0.88rem; color: #64748b;">
                    <div>Buy Price: <b>{row['origin_price_mwk']:,.0f} MWK</b></div>
                    <div>Sell Price: <b>{row['destination_price_mwk']:,.0f} MWK</b></div>
                    <div>Gross Spread: <b>{row['gross_spread_mwk']:,.0f} MWK ({row['pct_spread']:+.1f}%)</b></div>
                    <div>Freight Tariff: <b>{row['freight_cost_mwk']:,.0f} MWK</b></div>
                    <div style="color: {'#15803d' if row['net_margin_mwk'] > 0 else '#b91c1c'}; font-weight: 700;">Net Margin: {row['net_margin_mwk']:+,.0f} MWK/kg ({row['net_roi_pct']:+.1f}% ROI)</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info(f"No storable grain arbitrage data available for {selected_crop} (perishable or insufficient regional spread).")

    st.markdown("---")
    st.subheader("All-Commodity Regional Arbitrage Opportunities Table")
    if not live_arb.empty:
        st.dataframe(
            live_arb[[
                'commodity', 'origin_region', 'destination_region', 'origin_price_mwk',
                'destination_price_mwk', 'gross_spread_mwk', 'pct_spread',
                'net_margin_mwk', 'net_roi_pct', 'badge'
            ]].rename(columns={
                'commodity': 'Commodity',
                'origin_region': 'Origin (Buy)',
                'destination_region': 'Destination (Sell)',
                'origin_price_mwk': 'Origin (MWK)',
                'destination_price_mwk': 'Dest (MWK)',
                'gross_spread_mwk': 'Gross Spread',
                'pct_spread': 'Spread %',
                'net_margin_mwk': 'Net Margin (MWK/kg)',
                'net_roi_pct': 'Net ROI %',
                'badge': 'Status'
            }),
            use_container_width=True,
            hide_index=True
        )

# ==========================================
# TAB 4: MACRO & WEATHER DRIVERS
# ==========================================
with tab4:
    st.subheader("Macroeconomic Trends & Regional Climate Indicators")
    
    col_w1, col_w2 = st.columns(2)
    
    with col_w1:
        st.markdown("#### Regional Rainfall Seasonality (Open-Meteo)")
        if 'rainfall_mm' in df_hist.columns and not df_hist.empty:
            weather_recent = df_hist.groupby(['date', 'region'])['rainfall_mm'].mean().reset_index().tail(72)
            fig_rain = px.line(
                weather_recent, x='date', y='rainfall_mm', color='region',
                labels={'rainfall_mm': 'Monthly Rainfall (mm)', 'date': 'Timeline'},
                color_discrete_map={"Northern Region": "#0284c7", "Central Region": "#10b981", "Southern Region": "#f59e0b"}
            )
            fig_rain.update_layout(height=350, margin=dict(l=20, r=20, t=20, b=20))
            st.plotly_chart(fig_rain, use_container_width=True)
            
    with col_w2:
        st.markdown("#### Official MWK / USD Exchange Rate")
        if 'mwk_usd_exchange_rate' in df_hist.columns and not df_hist.empty:
            fx_recent = df_hist.groupby('date')['mwk_usd_exchange_rate'].mean().reset_index().tail(72)
            fig_fx = px.line(
                fx_recent, x='date', y='mwk_usd_exchange_rate',
                labels={'mwk_usd_exchange_rate': 'MWK / USD', 'date': 'Timeline'},
                color_discrete_sequence=['#d97706']
            )
            fig_fx.update_layout(height=350, margin=dict(l=20, r=20, t=20, b=20))
            st.plotly_chart(fig_fx, use_container_width=True)

# ==========================================
# TAB 5: WHAT-IF SCENARIO SIMULATOR
# ==========================================
with tab5:
    st.subheader(f"Macroeconomic & Climate Stress Testing Simulator: {selected_crop}")
    st.markdown("Simulate how macroeconomic currency shocks and climate events will shift market prices across regions.")
    
    sim_col1, sim_col2, sim_col3 = st.columns(3)
    with sim_col1:
        deval_shock = st.slider("MWK Currency Devaluation (%):", 0, 50, 10, step=5)
    with sim_col2:
        fuel_shock = st.slider("Fuel Tariff Increase (%):", 0, 40, 15, step=5)
    with sim_col3:
        rain_deficit = st.slider("Rainfall Deficit / Drought (%):", 0, 60, 20, step=10)
        
    # Simulation Elasticity Elasticity weights
    base_price = float(filtered_hist['price'].iloc[-1]) if not filtered_hist.empty else 1000.0
    
    # Crop price elasticity coefficients
    fx_elasticity = 0.45
    fuel_elasticity = 0.30
    climate_elasticity = 0.35 if selected_crop in ['Maize', 'Rice'] else 0.20
    
    sim_price_pct = (deval_shock * fx_elasticity) + (fuel_shock * fuel_elasticity) + (rain_deficit * climate_elasticity)
    simulated_price = base_price * (1.0 + sim_price_pct / 100.0)
    
    res_col1, res_col2, res_col3 = st.columns(3)
    with res_col1:
        st.metric("Baseline Current Price", f"{base_price:,.0f} MWK/kg")
    with res_col2:
        st.metric("Projected Shock Increase", f"+{sim_price_pct:.1f}%", delta_color="inverse")
    with res_col3:
        st.metric("Simulated Stressed Price", f"{simulated_price:,.0f} MWK/kg", f"+{simulated_price - base_price:,.0f} MWK")

# ==========================================
# TAB 6: WEEKLY MARKET BULLETIN
# ==========================================
with tab6:
    st.subheader("Automated Weekly Market Bulletins & Downloads")
    st.markdown("Download official printable weekly market intelligence bulletins covering all regions of Malawi.")
    
    latest_md_file = os.path.join(PROJECT_ROOT, "reports", "weekly_market_bulletin_latest.md")
    latest_html_file = os.path.join(PROJECT_ROOT, "reports", "weekly_market_bulletin_latest.html")
    
    btn_c1, btn_c2 = st.columns(2)
    
    if os.path.exists(latest_html_file):
        with open(latest_html_file, "r", encoding="utf-8") as f:
            html_data = f.read()
        with btn_c1:
            st.download_button(
                label="📥 Download Printable HTML Bulletin",
                data=html_data,
                file_name=f"malawi_crop_bulletin_{datetime.now().strftime('%Y%m%d')}.html",
                mime="text/html",
                use_container_width=True
            )
            
    if os.path.exists(latest_md_file):
        with open(latest_md_file, "r", encoding="utf-8") as f:
            md_data = f.read()
        with btn_c2:
            st.download_button(
                label="📄 Download Markdown Bulletin",
                data=md_data,
                file_name=f"malawi_crop_bulletin_{datetime.now().strftime('%Y%m%d')}.md",
                mime="text/markdown",
                use_container_width=True
            )
            
    if os.path.exists(latest_md_file):
        with st.expander("📄 Preview Latest Weekly Market Bulletin", expanded=True):
            st.markdown(md_data)
