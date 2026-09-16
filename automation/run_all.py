import sys
import subprocess
import os

def run_step(description, command):
    print(f"\n{description}")
    print(f"Running: {' '.join(command)}")
    result = subprocess.run(command)
    if result.returncode != 0:
        print(f"Error: Step failed with return code {result.returncode}")
        sys.exit(result.returncode)

def main():
    print("=" * 70)
    print("Starting Malawi Nationwide Crop Price & Market Intelligence Pipeline")
    print("Coverage: Northern Region, Central Region, Southern Region")
    print("=" * 70)

    python_exe = sys.executable

    run_step("[Step 1/5] Ingesting Raw WFP Market Price Data (All Regions)...", [python_exe, "data_ingest/fetch_wfp_data.py"])
    run_step("[Step 2/5] Fetching Regional Weather & Macro Indicators (Open-Meteo, World Bank)...", [python_exe, "data_ingest/fetch_exogenous_data.py"])
    run_step("[Step 3/5] Cleaning, Interpolating, and Building Multi-Region Enriched Dataset...", [python_exe, "data_preprocess/clean_and_enrich_data.py"])
    run_step("[Step 4/5] Training 18 Regional Prophet+SARIMAX Models & Computing Arbitrage...", [python_exe, "forecast/train_and_forecast.py"])
    run_step("[Step 5/5] Compiling Nationwide & Regional Weekly Market Bulletins...", [python_exe, "reports/generate_weekly_report.py"])

    print("\n" + "=" * 70)
    print("Full Nationwide Pipeline executed successfully!")
    print("Enriched dataset:       data/processed/clean_malawi_all_regions_enriched_prices.csv")
    print("Price forecasts:        data/forecasts/crop_price_forecasts.csv")
    print("Recommendations:        data/forecasts/market_recommendations.csv")
    print("Regional Arbitrage:     data/forecasts/regional_arbitrage_opportunities.csv")
    print("Weekly bulletin:        reports/weekly_market_bulletin_latest.html")
    print("Interactive Dashboard:  streamlit run app/streamlit_app.py")
    print("=" * 70)

if __name__ == "__main__":
    main()
