import os
import sys
import pandas as pd
from datetime import datetime

def generate_reports(output_dir="reports"):
    os.makedirs(output_dir, exist_ok=True)
    
    recs_path = "data/forecasts/market_recommendations.csv"
    forecasts_path = "data/forecasts/crop_price_forecasts.csv"
    processed_path = "data/processed/clean_northern_region_enriched_prices.csv"
    
    if not os.path.exists(recs_path) or not os.path.exists(forecasts_path):
        print("Warning: Forecast and recommendation files not found. Run forecast/train_and_forecast.py first.")
        return
        
    df_recs = pd.read_csv(recs_path)
    df_fc = pd.read_csv(forecasts_path)
    df_hist = pd.read_csv(processed_path) if os.path.exists(processed_path) else pd.DataFrame()
    
    report_date_str = datetime.now().strftime("%d %B %Y")
    report_file_date = datetime.now().strftime("%Y%m%d")
    
    # 1. Generate Markdown Bulletin
    md_content = f"""# Northern Malawi Crop Price & Market Intelligence Bulletin
**Published:** {report_date_str}  
**Target Coverage:** Northern Region (Mzuzu, Karonga, Chitipa, Rumphi, Nkhata Bay, Mzimba)  
**Reporting Agency:** AgriPrice Intelligence Initiative (Malawi)  

---

## 1. Executive Summary & Market Conditions

This weekly intelligence report delivers short-term (2–4 weeks) and seasonal (12 weeks) wholesale and retail commodity price projections for key staples and cash crops across the Northern Region of Malawi. Projections combine regional market records (WFP/FAMIS) with macroeconomic regressors including official MWK/USD exchange rate trends, regional rainfall aggregates, and fuel logistics tariffs.

### Key Highlights
"""
    for _, row in df_recs.iterrows():
        md_content += f"- **{row['commodity']}**: Currently trading at **{row['current_price_mwk']:,.0f} MWK/kg**. Projected 4-week trend: **{row['pct_change_4w']:+.1f}%** | 12-week trend: **{row['pct_change_12w']:+.1f}%**. Recommended Action: `{row['action_badge']}` ({row['risk_level']} Volatility Risk).\n"

    md_content += """
---

## 2. Comprehensive Commodity Action Matrix

| Commodity | Current (MWK/kg) | 4-Week Forecast | 4W Change (%) | 12-Week Forecast | 12W Change (%) | Net Storage Margin (12W) | Recommendation | Volatility Risk |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
"""
    for _, r in df_recs.iterrows():
        net_str = f"{r['net_storage_return_pct_12w']:+.1f}%" if pd.notna(r.get('net_storage_return_pct_12w')) else "N/A (Perishable)"
        md_content += f"| **{r['commodity']}** | {r['current_price_mwk']:,.0f} | {r['forecast_4w_mwk']:,.0f} | {r['pct_change_4w']:+.1f}% | {r['forecast_12w_mwk']:,.0f} | {r['pct_change_12w']:+.1f}% | {net_str} | `{r['action_badge']}` | **{r['risk_level']}** |\n"

    md_content += """
---

## 3. Stakeholder Operational Guidance

### 🚜 Smallholder Farmers & Grain Cooperatives
"""
    for _, r in df_recs.iterrows():
        md_content += f"- **{r['commodity']}**: {r['farmer_trader_summary']}\n"

    md_content += """
### 🏫 School Feeding Committees & Institutional Grain Buyers
"""
    for _, r in df_recs.iterrows():
        md_content += f"- **{r['commodity']}**: {r['institutional_school_advice']}\n"

    md_content += f"""
---

## 4. Technical Notes & Methodology
- **Forecasting Models**: Hybrid Ensemble combining **Facebook Prophet** (multiplicative seasonal decomposition + regressors) and **SARIMAX** (1,1,1) autoregressive state-space filtering.
- **Storage Economics**: Grain storage profitability assumes an average monthly carrying cost of 2.5% (covering hermetic PICS bags, Actellic Super dusting, storage facility rental, and shrinkage allowance).
- **Data Verification**: Historical series validated against WFP VAM and FEWS NET monitoring stations in Mzuzu, Bolero, and Karonga.

---
*Report generated automatically by Malawi AgriPrice Intelligence Pipeline.*
"""

    md_path = os.path.join(output_dir, f"weekly_market_bulletin_{report_file_date}.md")
    latest_md_path = os.path.join(output_dir, "weekly_market_bulletin_latest.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_content)
    with open(latest_md_path, "w", encoding="utf-8") as f:
        f.write(md_content)

    # 2. Generate Printable, Styled HTML Bulletin
    html_rows = ""
    for _, r in df_recs.iterrows():
        badge_bg = "#dcfce7" if "HOLD" in r['action_badge'] else ("#fee2e2" if "SELL" in r['action_badge'] else "#e0f2fe")
        badge_fg = "#15803d" if "HOLD" in r['action_badge'] else ("#b91c1c" if "SELL" in r['action_badge'] else "#0369a1")
        net_val = f"{r['net_storage_return_pct_12w']:+.1f}%" if pd.notna(r.get('net_storage_return_pct_12w')) else "—"
        
        html_rows += f"""
        <tr>
            <td style="font-weight: 600;">{r['commodity']}</td>
            <td>{r['current_price_mwk']:,.0f} MWK</td>
            <td>{r['forecast_4w_mwk']:,.0f} MWK <span style="font-size: 0.85em; color: {'#15803d' if r['pct_change_4w'] >= 0 else '#b91c1c'};">({r['pct_change_4w']:+.1f}%)</span></td>
            <td>{r['forecast_12w_mwk']:,.0f} MWK <span style="font-size: 0.85em; color: {'#15803d' if r['pct_change_12w'] >= 0 else '#b91c1c'};">({r['pct_change_12w']:+.1f}%)</span></td>
            <td>{net_val}</td>
            <td><span style="background: {badge_bg}; color: {badge_fg}; padding: 3px 10px; border-radius: 12px; font-weight: 600; font-size: 0.85em;">{r['action_badge']}</span></td>
            <td><strong>{r['risk_level']}</strong></td>
        </tr>
        """

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Malawi Northern Region Crop Price Intelligence Bulletin</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 40px auto;
            max-width: 960px;
            color: #1e293b;
            line-height: 1.6;
        }}
        .header-box {{
            background: linear-gradient(135deg, #0b3b24 0%, #165b37 100%);
            color: white;
            padding: 24px 30px;
            border-radius: 12px;
            margin-bottom: 25px;
        }}
        .header-box h1 {{ margin: 0 0 6px 0; font-size: 24px; }}
        .header-box p {{ margin: 0; color: #d1fae5; font-size: 14px; }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            font-size: 14px;
        }}
        th, td {{
            padding: 12px 14px;
            border-bottom: 1px solid #e2e8f0;
            text-align: left;
        }}
        th {{
            background: #f1f5f9;
            color: #475569;
            font-weight: 600;
        }}
        .card {{
            background: #f8fafc;
            border-left: 4px solid #10b981;
            padding: 14px 18px;
            margin-bottom: 12px;
            border-radius: 6px;
        }}
        @media print {{
            body {{ margin: 10px; }}
            .header-box {{ -webkit-print-color-adjust: exact; }}
        }}
    </style>
</head>
<body>
    <div class="header-box">
        <h1>🌾 Malawi AgriPrice Intelligence Bulletin</h1>
        <p>Northern Region Weekly Commodity Outlook & Strategic Market Advice | Issued: {report_date_str}</p>
    </div>

    <h2>Commodity Pricing & Decision Matrix</h2>
    <table>
        <thead>
            <tr>
                <th>Commodity</th>
                <th>Current (kg)</th>
                <th>4-Week Forecast</th>
                <th>12-Week Forecast</th>
                <th>Net Storage Margin</th>
                <th>Strategic Action</th>
                <th>Risk Rating</th>
            </tr>
        </thead>
        <tbody>
            {html_rows}
        </tbody>
    </table>

    <h2>Operational Guidance for Smallholders & Cooperatives</h2>
    {''.join([f'<div class="card"><strong>{r["commodity"]}:</strong> {r["farmer_trader_summary"]}</div>' for _, r in df_recs.iterrows()])}

    <h2>School Feeding Programs & Procurement Planning</h2>
    {''.join([f'<div class="card" style="border-left-color: #0284c7;"><strong>{r["commodity"]}:</strong> {r["institutional_school_advice"]}</div>' for _, r in df_recs.iterrows()])}

    <footer style="margin-top: 30px; font-size: 12px; color: #64748b; border-top: 1px solid #e2e8f0; padding-top: 15px;">
        Generated by AgriPrice Intelligence System for Northern Region Malawi (FAMIS/WFP VAM/Open-Meteo).
    </footer>
</body>
</html>
"""
    html_path = os.path.join(output_dir, f"weekly_market_bulletin_{report_file_date}.html")
    latest_html_path = os.path.join(output_dir, "weekly_market_bulletin_latest.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    with open(latest_html_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"Generated weekly reports successfully:")
    print(f" - Markdown: {md_path}")
    print(f" - Printable HTML: {html_path}")

if __name__ == "__main__":
    generate_reports()
