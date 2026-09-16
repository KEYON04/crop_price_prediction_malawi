#!/bin/bash
# Run the full data ingestion, exogenous predictor enrichment, and preprocessing pipeline

echo "============================================================"
echo "Starting Crop Price Data & Indicator Pipeline (Nationwide All Regions)"
echo "============================================================"

# Ensure we are using the venv python if it exists, otherwise fallback to python
PYTHON_CMD="python"
if [ -f ".venv/Scripts/python.exe" ]; then
    PYTHON_CMD=".venv/Scripts/python.exe"
elif [ -f ".venv/bin/python" ]; then
    PYTHON_CMD=".venv/bin/python"
fi

echo "Using python executable: $PYTHON_CMD"

echo ""
echo "[Step 1/5] Fetching Raw WFP Market Price Data (All Regions)..."
$PYTHON_CMD data_ingest/fetch_wfp_data.py

echo ""
echo "[Step 2/5] Fetching Exogenous Predictors (Rainfall, FX, Inflation, Fuel)..."
$PYTHON_CMD data_ingest/fetch_exogenous_data.py

echo ""
echo "[Step 3/5] Preprocessing, Interpolating, and Merging Enriched Dataset..."
$PYTHON_CMD data_preprocess/clean_and_enrich_data.py

echo ""
echo "[Step 4/5] Training 18 Regional Models & Computing Inter-Regional Arbitrage..."
$PYTHON_CMD forecast/train_and_forecast.py

echo ""
echo "[Step 5/5] Compiling Printable Weekly Market Intelligence Reports..."
$PYTHON_CMD reports/generate_weekly_report.py

echo ""
echo "============================================================"
echo "Full Pipeline executed successfully!"
echo "Enriched dataset:   data/processed/clean_malawi_all_regions_enriched_prices.csv"
echo "Price forecasts:    data/forecasts/crop_price_forecasts.csv"
echo "Recommendations:    data/forecasts/market_recommendations.csv"
echo "Regional Arbitrage: data/forecasts/regional_arbitrage_opportunities.csv"
echo "Weekly bulletin:    reports/weekly_market_bulletin_latest.html"
echo "Launch UI:          streamlit run app/streamlit_app.py"
echo "============================================================"
