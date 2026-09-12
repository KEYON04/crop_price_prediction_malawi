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
    print("=" * 60)
    print("Starting Crop Price Data & Indicator Pipeline (Northern Region)")
    print("=" * 60)

    python_exe = sys.executable

    run_step("[Step 1/5] Fetching Raw WFP Market Price Data...", [python_exe, "data_ingest/fetch_wfp_data.py"])
    run_step("[Step 2/5] Fetching Exogenous Predictors (Rainfall, FX, Inflation, Fuel)...", [python_exe, "data_ingest/fetch_exogenous_data.py"])
    run_step("[Step 3/5] Preprocessing, Interpolating, and Merging Enriched Dataset...", [python_exe, "data_preprocess/clean_and_enrich_data.py"])
    run_step("[Step 4/5] Training Models & Generating Multi-Crop Price Forecasts & Recommendations...", [python_exe, "forecast/train_and_forecast.py"])
    run_step("[Step 5/5] Compiling Printable Weekly Market Intelligence Reports...", [python_exe, "reports/generate_weekly_report.py"])

    print("\n" + "=" * 60)
    print("Full Pipeline executed successfully!")
    print("Enriched dataset: data/processed/clean_northern_region_enriched_prices.csv")
    print("Price forecasts:  data/forecasts/crop_price_forecasts.csv")
    print("Recommendations:  data/forecasts/market_recommendations.csv")
    print("Weekly bulletin:  reports/weekly_market_bulletin_latest.html")
    print("Launch UI:        streamlit run app/streamlit_app.py")
    print("=" * 60)

if __name__ == "__main__":
    main()
