import os
import sys
import pandas as pd
from datetime import datetime

def generate_reports(output_dir="reports"):
    os.makedirs(output_dir, exist_ok=True)
    
    recs_path = "data/forecasts/market_recommendations.csv"
    forecasts_path = "data/forecasts/crop_price_forecasts.csv"
    processed_path = "data/processed/clean_malawi_all_regions_enriched_prices.csv"
    if not os.path.exists(processed_path):
        processed_path = "data/processed/clean_northern_region_enriched_prices.csv"
    arb_path = "data/forecasts/regional_arbitrage_opportunities.csv"
    
    if not os.path.exists(recs_path) or not os.path.exists(forecasts_path):
        print("Warning: Forecast and recommendation files not found. Run forecast/train_and_forecast.py first.")
        return
        
    df_recs = pd.read_csv(recs_path)
    df_fc = pd.read_csv(forecasts_path)
    df_hist = pd.read_csv(processed_path) if os.path.exists(processed_path) else pd.DataFrame()
    df_arb = pd.read_csv(arb_path) if os.path.exists(arb_path) else pd.DataFrame()
    
    report_date_str = datetime.now().strftime("%d %B %Y")
    report_file_date = datetime.now().strftime("%Y%m%d")
    
    regions = sorted(df_recs['region'].unique()) if 'region' in df_recs.columns else ['Northern Region']
    
    # 1. Generate Markdown Bulletin
    md_content = f"""# Malawi National & Regional Crop Price Intelligence Bulletin
**Published:** {report_date_str}  
**Target Coverage:** Nationwide (Northern Region, Central Region, Southern Region)  
**Reporting Agency:** AgriPrice Intelligence Initiative (Malawi)  

---

## 1. Executive Summary & National Market Conditions

This weekly intelligence report delivers short-term (2–4 weeks) and seasonal (12 weeks) wholesale and retail commodity price projections for key staples and cash crops across all three agro-economic regions of Malawi. Projections combine regional market records (WFP/FAMIS) with macroeconomic regressors including official MWK/USD exchange rate trends, regional rainfall aggregates (Open-Meteo), and fuel logistics tariffs.

### Key Regional Highlights
"""
    for reg in regions:
        df_r = df_recs[df_recs['region'] == reg] if 'region' in df_recs.columns else df_recs
        md_content += f"\n#### 📍 {reg}\n"
        for _, row in df_r.iterrows():
            md_content += f"- **{row['commodity']}**: Trading at **{row['current_price_mwk']:,.0f} MWK/kg**. 4-week forecast: **{row['pct_change_4w']:+.1f}%** | 12-week forecast: **{row['pct_change_12w']:+.1f}%**. Action: `{row['action_badge']}` ({row['risk_level']} Risk).\n"

    # Cross-regional arbitrage highlights
    if not df_arb.empty:
        md_content += """
---

## 2. Inter-Regional Arbitrage & Trade Opportunities

| Commodity | Origin (Cheaper) | Destination (Premium) | Price Spread | Est. Freight | Net Margin | Net ROI | Opportunity Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
"""
        for _, a in df_arb.iterrows():
            orig = a['origin_region'].replace(' Region', '')
            dest = a['destination_region'].replace(' Region', '')
            md_content += f"| **{a['commodity']}** | {orig} ({a['origin_price_mwk']:,.0f} MWK) | {dest} ({a['destination_price_mwk']:,.0f} MWK) | {a['gross_spread_mwk']:,.0f} MWK ({a['pct_spread']:+.1f}%) | {a['freight_cost_mwk']:,.0f} MWK | **{a['net_margin_mwk']:+,.0f} MWK/kg** | {a['net_roi_pct']:+.1f}% | `{a['badge']}` |\n"

    md_content += """
---

## 3. Comprehensive Regional Action Matrix

| Region | Commodity | Current (MWK/kg) | 4-Week Forecast | 4W Change (%) | 12-Week Forecast | 12W Change (%) | Net Storage Margin (12W) | Action | Risk Level |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
"""
    for _, r in df_recs.iterrows():
        reg_name = r.get('region', 'Northern Region')
        net_str = f"{r['net_storage_return_pct_12w']:+.1f}%" if pd.notna(r.get('net_storage_return_pct_12w')) else "N/A (Perishable)"
        md_content += f"| {reg_name} | **{r['commodity']}** | {r['current_price_mwk']:,.0f} | {r['forecast_4w_mwk']:,.0f} | {r['pct_change_4w']:+.1f}% | {r['forecast_12w_mwk']:,.0f} | {r['pct_change_12w']:+.1f}% | {net_str} | `{r['action_badge']}` | **{r['risk_level']}** |\n"

    md_content += """
---

## 4. Stakeholder Operational Guidance

### 🚜 Smallholder Farmers & Grain Cooperatives
"""
    for _, r in df_recs.iterrows():
        reg_name = r.get('region', 'Northern Region')
        md_content += f"- **[{reg_name} | {r['commodity']}]**: {r['summary']}\n"

    md_content += """
### 🏫 School Feeding Committees & Institutional Grain Buyers
"""
    for _, r in df_recs.iterrows():
        reg_name = r.get('region', 'Northern Region')
        md_content += f"- **[{reg_name} | {r['commodity']}]**: {r['institutional_advice']}\n"

    md_content += f"""
---

## 5. Technical Notes & Methodology
- **Regional ML Models**: Separate Prophet and SARIMAX ensemble models trained independently per region and commodity (18 models total) to capture local soil, weather, transport, and harvest cycles.
- **Inter-Regional Arbitrage**: Evaluates regional market differentials against real-world freight tariffs along the M1 transport spine (~140 MWK/kg).
- **Storage Economics**: Grain storage profitability assumes 2.5% monthly carrying cost for hermetic PICS bags, fumigation, and loss allowance.

---
*Report generated automatically by Malawi AgriPrice Intelligence Pipeline.*
"""

    md_path = os.path.join(output_dir, f"weekly_market_bulletin_{report_file_date}.md")
    latest_md_path = os.path.join(output_dir, "weekly_market_bulletin_latest.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_content)
    with open(latest_md_path, "w", encoding="utf-8") as f:
        f.write(md_content)

    # 2. Generate Printable Styled HTML Bulletin
    html_rows = ""
    for _, r in df_recs.iterrows():
        badge_bg = "#dcfce7" if "HOLD" in r['action_badge'] else ("#fee2e2" if "SELL" in r['action_badge'] else "#e0f2fe")
        badge_fg = "#15803d" if "HOLD" in r['action_badge'] else ("#b91c1c" if "SELL" in r['action_badge'] else "#0369a1")
        net_val = f"{r['net_storage_return_pct_12w']:+.1f}%" if pd.notna(r.get('net_storage_return_pct_12w')) else "—"
        reg_name = r.get('region', 'Northern Region')
        
        html_rows += f"""
        <tr>
            <td style="color: #64748b; font-size: 0.9em;">{reg_name}</td>
            <td style="font-weight: 600;">{r['commodity']}</td>
            <td>{r['current_price_mwk']:,.0f} MWK</td>
            <td>{r['forecast_4w_mwk']:,.0f} MWK <span style="font-size: 0.85em; color: {'#15803d' if r['pct_change_4w'] >= 0 else '#b91c1c'};">({r['pct_change_4w']:+.1f}%)</span></td>
            <td>{r['forecast_12w_mwk']:,.0f} MWK <span style="font-size: 0.85em; color: {'#15803d' if r['pct_change_12w'] >= 0 else '#b91c1c'};">({r['pct_change_12w']:+.1f}%)</span></td>
            <td>{net_val}</td>
            <td><span style="background: {badge_bg}; color: {badge_fg}; padding: 3px 10px; border-radius: 12px; font-weight: 600; font-size: 0.85em;">{r['action_badge']}</span></td>
            <td><strong>{r['risk_level']}</strong></td>
        </tr>
        """

    arb_html_rows = ""
    if not df_arb.empty:
        for _, a in df_arb.iterrows():
            badge_bg = "#dcfce7" if "TRADE" in a['badge'] else ("#fef3c7" if "MARGINAL" in a['badge'] else "#f1f5f9")
            badge_fg = "#15803d" if "TRADE" in a['badge'] else ("#b45309" if "MARGINAL" in a['badge'] else "#64748b")
            arb_html_rows += f"""
            <tr>
                <td style="font-weight: 600;">{a['commodity']}</td>
                <td>{a['origin_region'].replace(' Region', '')} ({a['origin_price_mwk']:,.0f} MWK)</td>
                <td>{a['destination_region'].replace(' Region', '')} ({a['destination_price_mwk']:,.0f} MWK)</td>
                <td>{a['gross_spread_mwk']:,.0f} MWK ({a['pct_spread']:+.1f}%)</td>
                <td><strong>{a['net_margin_mwk']:+,.0f} MWK/kg</strong> ({a['net_roi_pct']:+.1f}% ROI)</td>
                <td><span style="background: {badge_bg}; color: {badge_fg}; padding: 3px 10px; border-radius: 12px; font-weight: 600; font-size: 0.85em;">{a['badge']}</span></td>
            </tr>
            """

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Malawi Nationwide Crop Price Intelligence Bulletin</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 40px auto;
            max-width: 1000px;
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
            font-size: 13.5px;
        }}
        th, td {{
            padding: 10px 12px;
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
            padding: 12px 16px;
            margin-bottom: 10px;
            border-radius: 6px;
        }}
        .badge {{
            display: inline-block;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 600;
            margin-right: 6px;
        }}
        .footer {{
            margin-top: 40px;
            border-top: 1px solid #e2e8f0;
            padding-top: 15px;
            color: #64748b;
            font-size: 12px;
        }}
        @media print {{
            body {{ margin: 20px; }}
            .header-box {{ -webkit-print-color-adjust: exact; }}
        }}
    </style>
</head>
<body>
    <div class="header-box">
        <h1>🌾 Malawi National & Regional Crop Price Intelligence Bulletin</h1>
        <p>Issued: {report_date_str} | Coverage: Northern, Central & Southern Regions | AgriPrice Initiative</p>
    </div>

    <h2>1. Executive Summary</h2>
    <p>This report covers market intelligence, price trends, and trading opportunities across Malawi for <strong>Maize, Beans, Groundnuts, Rice, Soya beans,</strong> and <strong>Tomatoes</strong>.</p>

    <h2>2. Inter-Regional Arbitrage Spreads</h2>
    <table>
        <thead>
            <tr>
                <th>Crop</th>
                <th>Origin (Buy)</th>
                <th>Destination (Sell)</th>
                <th>Gross Spread</th>
                <th>Net Margin (After Freight)</th>
                <th>Trade Status</th>
            </tr>
        </thead>
        <tbody>
            {arb_html_rows}
        </tbody>
    </table>

    <h2>3. Regional Commodity Forecast Matrix</h2>
    <table>
        <thead>
            <tr>
                <th>Region</th>
                <th>Crop</th>
                <th>Current Price</th>
                <th>4-Week Forecast</th>
                <th>12-Week Forecast</th>
                <th>Storage Margin (12W)</th>
                <th>Recommended Action</th>
                <th>Risk</th>
            </tr>
        </thead>
        <tbody>
            {html_rows}
        </tbody>
    </table>

    <h2>4. Stakeholder Recommendations</h2>
    <h3>🚜 Farmers & Cooperatives</h3>
    {''.join([f'<div class="card"><strong>[{r.get("region", "National")} | {r["commodity"]}]</strong>: {r["summary"]}</div>' for _, r in df_recs.iterrows()])}

    <div class="footer">
        <p>Published by AgriPrice Intelligence Initiative Malawi. Data Sources: WFP VAM, FAMIS, Open-Meteo, World Bank Data.</p>
    </div>
</body>
</html>
"""

    html_path = os.path.join(output_dir, f"weekly_market_bulletin_{report_file_date}.html")
    latest_html_path = os.path.join(output_dir, "weekly_market_bulletin_latest.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    with open(latest_html_path, "w", encoding="utf-8") as f:
        f.write(html_content)
        
    print(f"\nGenerated weekly market bulletins in {output_dir}:")
    print(f"  - Markdown: {md_path}")
    print(f"  - HTML: {html_path}")

if __name__ == "__main__":
    generate_reports()
