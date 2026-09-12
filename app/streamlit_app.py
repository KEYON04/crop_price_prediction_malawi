import os
import sys
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="Malawi AgriPrice Intelligence | Northern Region",
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
        padding: 26px 32px;
        border-radius: 16px;
        margin-bottom: 24px;
        box-shadow: 0 10px 25px -5px rgba(16, 185, 129, 0.2);
        border: 1px solid rgba(255, 255, 255, 0.12);
    }
    
    .hero-title {
        font-size: 2.2rem;
        font-weight: 700;
        margin-bottom: 8px;
        letter-spacing: -0.5px;
    }
    
    .hero-subtitle {
        font-size: 1.05rem;
        color: #d1fae5;
        max-width: 900px;
        line-height: 1.5;
    }
    
    .metric-card {
        background: white;
        border-radius: 14px;
        padding: 20px 24px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.08);
    }
    
    .metric-label {
        font-size: 0.85rem;
        font-weight: 600;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 4px;
    }
    
    .metric-value {
        font-size: 1.85rem;
        font-weight: 700;
        color: #0f172a;
        margin-bottom: 6px;
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
        border: 1px solid #7dd3fc;
    }
    
    .info-card {
        background: #f8fafc;
        border-left: 4px solid #10b981;
        padding: 16px 20px;
        border-radius: 8px;
        margin: 14px 0;
    }
</style>
""", unsafe_allow_html=True)

# Helper functions to load data
@st.cache_data
def load_data():
    processed_path = "data/processed/clean_northern_region_enriched_prices.csv"
    forecast_path = "data/forecasts/crop_price_forecasts.csv"
    recs_path = "data/forecasts/market_recommendations.csv"
    metrics_path = "data/forecasts/model_evaluation_metrics.csv"
    
    df_hist = pd.read_csv(processed_path) if os.path.exists(processed_path) else pd.DataFrame()
    df_fc = pd.read_csv(forecast_path) if os.path.exists(forecast_path) else pd.DataFrame()
    df_recs = pd.read_csv(recs_path) if os.path.exists(recs_path) else pd.DataFrame()
    df_metrics = pd.read_csv(metrics_path) if os.path.exists(metrics_path) else pd.DataFrame()
    
    if not df_hist.empty:
        df_hist['date'] = pd.to_datetime(df_hist['date'])
    if not df_fc.empty:
        df_fc['date'] = pd.to_datetime(df_fc['date'])
        
    return df_hist, df_fc, df_recs, df_metrics

df_hist, df_fc, df_recs, df_metrics = load_data()

# Hero Banner
st.markdown("""
<div class="hero-card">
    <div class="hero-title">🌾 Malawi AgriPrice Intelligence</div>
    <div class="hero-subtitle">
        Short-Term (2–4 Weeks) & Seasonal Crop Price Forecasting with Market Recommendations for the Northern Region (Mzuzu, Karonga, Chitipa, Rumphi, Nkhata Bay, Mzimba).
    </div>
</div>
""", unsafe_allow_html=True)

if df_hist.empty or df_fc.empty:
    st.error("Data pipeline outputs not found. Please run `automation/run_all.py` first to generate processed data and forecasts.")
    st.stop()

# Sidebar controls
st.sidebar.image("https://img.icons8.com/color/96/wheat.png", width=64)
st.sidebar.header("Navigation & Filters")

available_crops = sorted(df_hist['commodity'].unique().tolist())
selected_crop = st.sidebar.selectbox("Select Crop / Commodity:", available_crops, index=2 if 'Maize' in available_crops else 0)

forecast_horizon = st.sidebar.select_slider(
    "Forecast Horizon:",
    options=[1, 2, 3, 6],
    value=3,
    format_func=lambda x: f"{x * 4} Weeks ({x} Months)"
)

show_confidence = st.sidebar.checkbox("Show 80% & 95% Confidence Cones", value=True)
show_lean_season = st.sidebar.checkbox("Highlight Lean Season (Dec–Mar)", value=True)
show_harvest_season = st.sidebar.checkbox("Highlight Harvest Season (Apr–Jun)", value=True)

st.sidebar.markdown("---")
st.sidebar.caption("Data Sources: WFP VAM, FAMIS Malawi, Open-Meteo, World Bank Open Data.")

# Main Tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Market Overview & Advisory",
    "📈 Price Forecast & Trajectory",
    "🌧️ Macro & Weather Drivers",
    "⚙️ What-If Scenario Simulator",
    "📄 Weekly Market Bulletin"
])

# Crop specific data
crop_hist = df_hist[df_hist['commodity'] == selected_crop].sort_values('date')
crop_fc = df_fc[df_fc['commodity'] == selected_crop].sort_values('date').head(forecast_horizon)
crop_rec = df_recs[df_recs['commodity'] == selected_crop]

# ==========================================
# TAB 1: OVERVIEW & MARKET RECOMMENDATIONS
# ==========================================
with tab1:
    st.subheader(f"Current Market Signals: {selected_crop} (Northern Region)")
    
    current_p = float(crop_hist['price'].iloc[-1])
    last_date = crop_hist['date'].iloc[-1].strftime('%B %Y')
    
    if not crop_rec.empty:
        rec_row = crop_rec.iloc[0]
        p_4w = rec_row['forecast_4w_mwk']
        pct_4w = rec_row['pct_change_4w']
        p_12w = rec_row['forecast_12w_mwk']
        pct_12w = rec_row['pct_change_12w']
        badge = rec_row['action_badge']
        risk = rec_row['risk_level']
    else:
        p_4w, pct_4w, p_12w, pct_12w, badge, risk = current_p, 0, current_p, 0, "MONITOR", "Medium"

    # KPI row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Latest Price ({last_date})</div>
            <div class="metric-value">{current_p:,.0f} <span style="font-size: 1rem; color: #64748b;">MWK/kg</span></div>
            <div style="color: #64748b; font-size: 0.85rem;">Regional median across Northern markets</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col2:
        arrow_4w = "▲" if pct_4w >= 0 else "▼"
        color_4w = "#15803d" if pct_4w >= 0 else "#b91c1c"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">4-Week Projection</div>
            <div class="metric-value">{p_4w:,.0f} <span style="font-size: 1rem; color: #64748b;">MWK/kg</span></div>
            <div style="color: {color_4w}; font-weight: 600; font-size: 0.95rem;">{arrow_4w} {abs(pct_4w):.1f}% over 4 weeks</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col3:
        arrow_12w = "▲" if pct_12w >= 0 else "▼"
        color_12w = "#15803d" if pct_12w >= 0 else "#b91c1c"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">12-Week Projection</div>
            <div class="metric-value">{p_12w:,.0f} <span style="font-size: 1rem; color: #64748b;">MWK/kg</span></div>
            <div style="color: {color_12w}; font-weight: 600; font-size: 0.95rem;">{arrow_12w} {abs(pct_12w):.1f}% over 12 weeks</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col4:
        badge_class = "badge-hold" if "HOLD" in badge else ("badge-sell" if "SELL" in badge else "badge-monitor")
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Market Recommendation</div>
            <div style="margin-top: 4px; margin-bottom: 8px;">
                <span class="{badge_class}">{badge}</span>
            </div>
            <div style="color: #64748b; font-size: 0.85rem;">Volatility Risk: <strong>{risk}</strong></div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    
    # Detailed Decision Matrix
    st.subheader("Regional Crop Advisory & Strategic Action Matrix")
    
    st.dataframe(
        df_recs[[
            'commodity', 'current_price_mwk', 'forecast_4w_mwk', 'pct_change_4w', 
            'forecast_12w_mwk', 'pct_change_12w', 'action_badge', 'risk_level'
        ]].rename(columns={
            'commodity': 'Commodity',
            'current_price_mwk': 'Current (MWK/kg)',
            'forecast_4w_mwk': '4-Week (MWK/kg)',
            'pct_change_4w': '4-Week %',
            'forecast_12w_mwk': '12-Week (MWK/kg)',
            'pct_change_12w': '12-Week %',
            'action_badge': 'Action Advice',
            'risk_level': 'Risk Rating'
        }),
        use_container_width=True,
        hide_index=True
    )
    
    # Role-Based Advisory Cards
    st.markdown("### Stakeholder Actionable Guidance")
    col_a, col_b = st.columns(2)
    
    with col_a:
        st.markdown(f"""
        <div class="info-card">
            <h4 style="margin: 0 0 8px 0; color: #065f46;">🚜 Smallholder Farmers & Cooperatives</h4>
            <p style="margin: 0; color: #1e293b; font-size: 0.95rem; line-height: 1.5;">
                {rec_row['farmer_trader_summary'] if not crop_rec.empty else 'Monitor local market depots in Mzuzu and Karonga.'}
            </p>
        </div>
        """, unsafe_allow_html=True)
        
    with col_b:
        st.markdown(f"""
        <div class="info-card" style="border-left-color: #0284c7;">
            <h4 style="margin: 0 0 8px 0; color: #075985;">🏫 School Feeding & Institutional Buyers</h4>
            <p style="margin: 0; color: #1e293b; font-size: 0.95rem; line-height: 1.5;">
                {rec_row['institutional_school_advice'] if not crop_rec.empty else 'Plan food procurement contracts based on seasonal harvest cycles.'}
            </p>
        </div>
        """, unsafe_allow_html=True)

# ==========================================
# TAB 2: PRICE FORECAST & HISTORICAL TRAJECTORY
# ==========================================
with tab2:
    st.subheader(f"Price Trajectory & Forecast Cone: {selected_crop}")
    
    # Interactive Plotly Chart
    fig = go.Figure()
    
    # Show last 36 months of history for readability
    recent_hist = crop_hist.tail(36).copy()
    
    # 1. Historical line
    fig.add_trace(go.Scatter(
        x=recent_hist['date'],
        y=recent_hist['price'],
        mode='lines+markers',
        name='Historical Median Price',
        line=dict(color='#0f766e', width=2.5),
        marker=dict(size=5, color='#0f766e')
    ))
    
    # 2. Moving Average
    if 'price_ma_3m' in recent_hist.columns:
        fig.add_trace(go.Scatter(
            x=recent_hist['date'],
            y=recent_hist['price_ma_3m'],
            mode='lines',
            name='3-Month Moving Avg',
            line=dict(color='#f59e0b', width=1.5, dash='dot')
        ))
        
    # Connect last historical point to forecast
    last_pt = pd.DataFrame([{
        'date': recent_hist['date'].iloc[-1],
        'price_pred': recent_hist['price'].iloc[-1],
        'price_lower_80': recent_hist['price'].iloc[-1],
        'price_upper_80': recent_hist['price'].iloc[-1],
        'price_lower_95': recent_hist['price'].iloc[-1],
        'price_upper_95': recent_hist['price'].iloc[-1],
    }])
    plot_fc = pd.concat([last_pt, crop_fc], ignore_index=True)
    
    # 3. 95% Confidence Band
    if show_confidence and 'price_lower_95' in plot_fc.columns:
        fig.add_trace(go.Scatter(
            x=plot_fc['date'],
            y=plot_fc['price_upper_95'],
            mode='lines',
            line=dict(width=0),
            showlegend=False,
            hoverinfo='skip'
        ))
        fig.add_trace(go.Scatter(
            x=plot_fc['date'],
            y=plot_fc['price_lower_95'],
            mode='lines',
            line=dict(width=0),
            fill='tonexty',
            fillcolor='rgba(16, 185, 129, 0.12)',
            name='95% Prediction Interval'
        ))
        
    # 4. 80% Confidence Band
    if show_confidence and 'price_lower_80' in plot_fc.columns:
        fig.add_trace(go.Scatter(
            x=plot_fc['date'],
            y=plot_fc['price_upper_80'],
            mode='lines',
            line=dict(width=0),
            showlegend=False,
            hoverinfo='skip'
        ))
        fig.add_trace(go.Scatter(
            x=plot_fc['date'],
            y=plot_fc['price_lower_80'],
            mode='lines',
            line=dict(width=0),
            fill='tonexty',
            fillcolor='rgba(16, 185, 129, 0.22)',
            name='80% Prediction Interval'
        ))
        
    # 5. Forecast Trajectory
    fig.add_trace(go.Scatter(
        x=plot_fc['date'],
        y=plot_fc['price_pred'],
        mode='lines+markers',
        name='Ensemble Forecast',
        line=dict(color='#059669', width=3, dash='dash'),
        marker=dict(size=7, color='#059669')
    ))
    
    # Lean season vertical shading (Dec-Mar)
    if show_lean_season:
        for year in [recent_hist['date'].dt.year.max() - 1, recent_hist['date'].dt.year.max()]:
            fig.add_vrect(
                x0=f"{year}-12-01",
                x1=f"{year+1}-03-31",
                fillcolor="rgba(239, 68, 68, 0.07)",
                layer="below",
                line_width=0,
                annotation_text="Lean Season (Peak Prices)",
                annotation_position="top left",
                annotation_font_size=10
            )
            
    fig.update_layout(
        title=f"<b>{selected_crop} Price Projection</b> (MWK / kg) — Northern Malawi",
        xaxis_title="Date",
        yaxis_title="Price (MWK/kg)",
        hovermode="x unified",
        template="plotly_white",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=520,
        margin=dict(l=40, r=40, t=80, b=40)
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Model evaluation metrics
    st.markdown("### Model Evaluation & Validation Accuracy")
    if not df_metrics.empty:
        st.dataframe(
            df_metrics.rename(columns={
                'commodity': 'Commodity',
                'ensemble_mae': 'Ensemble MAE (MWK)',
                'ensemble_rmse': 'Ensemble RMSE',
                'ensemble_mape': 'Ensemble MAPE (%)',
                'prophet_mape': 'Prophet MAPE (%)',
                'sarimax_mape': 'SARIMAX MAPE (%)'
            }),
            use_container_width=True,
            hide_index=True
        )

# ==========================================
# TAB 3: MACRO & CLIMATE DRIVERS
# ==========================================
with tab3:
    st.subheader("Exogenous Predictors & Economic Transmission Channels")
    st.write("Food crop prices in Northern Malawi respond heavily to regional rainfall distribution, MWK/USD currency devaluations, and diesel/transportation tariffs.")
    
    col_d1, col_d2 = st.columns(2)
    
    with col_d1:
        # Dual-axis Rainfall vs Price
        fig_rain = go.Figure()
        fig_rain.add_trace(go.Bar(
            x=recent_hist['date'],
            y=recent_hist['rainfall_mm'],
            name='Monthly Rainfall (mm)',
            marker_color='rgba(59, 130, 246, 0.4)',
            yaxis='y2'
        ))
        fig_rain.add_trace(go.Scatter(
            x=recent_hist['date'],
            y=recent_hist['price'],
            name=f'{selected_crop} Price (MWK/kg)',
            line=dict(color='#047857', width=2.5)
        ))
        fig_rain.update_layout(
            title=f"<b>{selected_crop} Price vs Rainfall</b> (Northern Region)",
            yaxis=dict(title="Price (MWK/kg)"),
            yaxis2=dict(title="Rainfall (mm)", overlaying='y', side='right', showgrid=False),
            template="plotly_white",
            legend=dict(orientation="h", y=1.1),
            height=380
        )
        st.plotly_chart(fig_rain, use_container_width=True)
        
    with col_d2:
        # Currency Devaluation vs Price
        fig_fx = go.Figure()
        fig_fx.add_trace(go.Scatter(
            x=recent_hist['date'],
            y=recent_hist['mwk_usd_exchange_rate'],
            name='Exchange Rate (MWK / USD)',
            line=dict(color='#9333ea', width=2, dash='dot'),
            yaxis='y2'
        ))
        fig_fx.add_trace(go.Scatter(
            x=recent_hist['date'],
            y=recent_hist['price'],
            name=f'{selected_crop} Price (MWK/kg)',
            line=dict(color='#047857', width=2.5)
        ))
        fig_fx.update_layout(
            title=f"<b>{selected_crop} Price vs Exchange Rate (MWK/USD)</b>",
            yaxis=dict(title="Price (MWK/kg)"),
            yaxis2=dict(title="MWK / USD Rate", overlaying='y', side='right', showgrid=False),
            template="plotly_white",
            legend=dict(orientation="h", y=1.1),
            height=380
        )
        st.plotly_chart(fig_fx, use_container_width=True)

    # Driver Explanations
    st.markdown("""
    <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 16px; margin-top: 10px;">
        <div class="metric-card">
            <h4 style="color: #0369a1; margin-top: 0;">🌧️ Rainfall & Seasonality</h4>
            <p style="font-size: 0.9rem; color: #475569;">Heavy rains from Dec–March hinder road transport in Chitipa and Karonga, spiking depot transport premiums while field stocks are lowest.</p>
        </div>
        <div class="metric-card">
            <h4 style="color: #7e22ce; margin-top: 0;">💵 FX Devaluation</h4>
            <p style="font-size: 0.9rem; color: #475569;">Imported agricultural inputs (fertilizer, packaging) and fuel react rapidly to official MWK/USD adjustments, lifting replacement costs.</p>
        </div>
        <div class="metric-card">
            <h4 style="color: #b45309; margin-top: 0;">⛽ Fuel & Logistics</h4>
            <p style="font-size: 0.9rem; color: #475569;">Long-haul freight between Lilongwe, Blantyre, and Mzuzu passes pump price shocks directly to staple food retail margins within 2–3 weeks.</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ==========================================
# TAB 4: WHAT-IF SCENARIO SIMULATOR
# ==========================================
with tab4:
    st.subheader("What-If Stress Testing Simulator")
    st.write("Simulate the expected impact of macroeconomic shocks on projected crop prices over the next 4 to 12 weeks.")
    
    col_s1, col_s2 = st.columns([1, 2])
    
    with col_s1:
        st.markdown("#### Scenario Assumptions")
        fx_shock = st.slider("MWK Currency Devaluation (%):", min_value=-20, max_value=50, value=15, step=5)
        fuel_shock = st.slider("Fuel Price Increase (%):", min_value=-15, max_value=40, value=10, step=5)
        climate_shock = st.selectbox("Rainfall Shock Scenario:", [
            "Normal Historical Pattern",
            "Drought / Below Average (-30% Rain)",
            "Excess Flooding / Cyclone Surge (+40% Rain)"
        ])
        
        # Elasticity estimates for Malawi agricultural prices
        # Grains/legumes elasticity to FX ~ 0.40, fuel ~ 0.25
        fx_elasticity = 0.38
        fuel_elasticity = 0.22
        rain_elasticity = 0.15 if "Drought" in climate_shock else (0.10 if "Flooding" in climate_shock else 0.0)
        
        total_shock_pct = (fx_shock * fx_elasticity) + (fuel_shock * fuel_elasticity) + (rain_elasticity * 100)
        
    with col_s2:
        st.markdown("#### Simulated Impact on Forecast")
        base_4w = p_4w
        simulated_4w = base_4w * (1.0 + (total_shock_pct / 100.0))
        delta_sim = simulated_4w - base_4w
        
        st.markdown(f"""
        <div class="metric-card" style="margin-bottom: 16px;">
            <div class="metric-label">Estimated Price Under Selected Scenario</div>
            <div class="metric-value" style="color: #0f766e;">{simulated_4w:,.0f} <span style="font-size: 1rem; color: #64748b;">MWK/kg</span></div>
            <div style="font-weight: 600; color: {'#b91c1c' if delta_sim > 0 else '#15803d'}; font-size: 0.95rem;">
                {'+' if delta_sim > 0 else ''}{delta_sim:,.0f} MWK/kg ({'+' if total_shock_pct > 0 else ''}{total_shock_pct:.1f}%) vs Baseline Forecast
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Comparison bar chart
        fig_sim = go.Figure()
        fig_sim.add_trace(go.Bar(
            x=['Current Price', 'Baseline 4W Forecast', 'Shock Scenario 4W'],
            y=[current_p, base_4w, simulated_4w],
            marker_color=['#64748b', '#0d9488', '#e11d48'],
            text=[f"{current_p:,.0f}", f"{base_4w:,.0f}", f"{simulated_4w:,.0f}"],
            textposition='auto'
        ))
        fig_sim.update_layout(
            title=f"Scenario Comparison: {selected_crop}",
            yaxis_title="Price (MWK/kg)",
            template="plotly_white",
            height=320
        )
        st.plotly_chart(fig_sim, use_container_width=True)

# ==========================================
# TAB 5: WEEKLY MARKET BULLETIN
# ==========================================
with tab5:
    st.subheader("Northern Region Weekly Market Bulletin")
    st.write("Exportable summary for agricultural extension officers, radio broadcasts, and institutional procurement.")
    
    current_date_str = datetime.now().strftime('%d %B %Y')
    
    bulletin_content = f"""# Northern Malawi Crop Price & Market Bulletin
**Generated on:** {current_date_str}  
**Coverage Area:** Northern Region (Mzuzu, Karonga, Chitipa, Rumphi, Nkhata Bay, Mzimba)  

---

### Key Market Highlights
- **Maize:** Current regional median is **{df_recs[df_recs['commodity']=='Maize']['current_price_mwk'].values[0]:,.0f} MWK/kg**. Projected 4-week change is **{df_recs[df_recs['commodity']=='Maize']['pct_change_4w'].values[0]:+.1f}%**. Advice: **{df_recs[df_recs['commodity']=='Maize']['action_badge'].values[0]}**.
- **Beans:** Current price is **{df_recs[df_recs['commodity']=='Beans']['current_price_mwk'].values[0]:,.0f} MWK/kg** with **{df_recs[df_recs['commodity']=='Beans']['pct_change_4w'].values[0]:+.1f}%** 4-week trend. Advice: **{df_recs[df_recs['commodity']=='Beans']['action_badge'].values[0]}**.
- **Rice:** Steady demand at **{df_recs[df_recs['commodity']=='Rice']['current_price_mwk'].values[0]:,.0f} MWK/kg** with 12-week outlook of **{df_recs[df_recs['commodity']=='Rice']['pct_change_12w'].values[0]:+.1f}%**.
- **Groundnuts:** Retail median **{df_recs[df_recs['commodity']=='Groundnuts']['current_price_mwk'].values[0]:,.0f} MWK/kg**, projected **{df_recs[df_recs['commodity']=='Groundnuts']['pct_change_4w'].values[0]:+.1f}%** 4-week shift.
- **Soya beans:** Standing at **{df_recs[df_recs['commodity']=='Soya beans']['current_price_mwk'].values[0]:,.0f} MWK/kg**.
- **Tomatoes:** Perishable horticulture selling at **{df_recs[df_recs['commodity']=='Tomatoes']['current_price_mwk'].values[0]:,.0f} MWK/kg**. Staggered harvest advised.

---
*Published by AgriPrice Intelligence System for Northern Region Malawi.*
"""
    st.text_area("Market Bulletin Text Preview", bulletin_content, height=280)
    
    col_d1, col_d2, col_d3 = st.columns(3)
    
    with col_d1:
        st.download_button(
            label="📥 Download Bulletin (Markdown)",
            data=bulletin_content,
            file_name=f"malawi_northern_market_bulletin_{datetime.now().strftime('%Y%m%d')}.md",
            mime="text/markdown"
        )
    with col_d2:
        st.download_button(
            label="📊 Download Recommendations (CSV)",
            data=df_recs.to_csv(index=False),
            file_name="market_recommendations.csv",
            mime="text/csv"
        )
    with col_d3:
        st.download_button(
            label="📈 Download Forecasts (CSV)",
            data=df_fc.to_csv(index=False),
            file_name="crop_price_forecasts.csv",
            mime="text/csv"
        )
