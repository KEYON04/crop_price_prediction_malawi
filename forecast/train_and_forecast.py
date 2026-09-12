import os
import sys
import pandas as pd
import numpy as np

# Add parent directory to path to enable clean imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from forecast.models import fit_ensemble_model
from forecast.recommendations import generate_crop_recommendations

def run_training_and_forecasting(input_path, output_dir, horizon_months=6):
    print("=" * 60)
    print("Executing Malawi Crop Price Forecasting Engine (Northern Region)")
    print("=" * 60)
    
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input processed dataset not found at {input_path}")
        
    df = pd.read_csv(input_path)
    df['date'] = pd.to_datetime(df['date'])
    
    crops = sorted(df['commodity'].unique())
    print(f"Loaded {len(df)} records across {len(crops)} crops: {crops}")
    
    os.makedirs(output_dir, exist_ok=True)
    
    all_forecasts = []
    all_metrics = []
    
    for crop in crops:
        print(f"\nTraining forecasting models for crop: [{crop}]...")
        crop_df = df[df['commodity'] == crop].sort_values('date').reset_index(drop=True)
        
        try:
            fc_df, ens_metrics, model_details = fit_ensemble_model(crop_df, horizon_months=horizon_months)
            fc_df['commodity'] = crop
            all_forecasts.append(fc_df)
            
            row_metrics = {
                'commodity': crop,
                'ensemble_mae': ens_metrics.get('MAE'),
                'ensemble_rmse': ens_metrics.get('RMSE'),
                'ensemble_mape': ens_metrics.get('MAPE'),
            }
            if 'Prophet' in model_details:
                row_metrics['prophet_mape'] = model_details['Prophet'].get('MAPE')
            if 'SARIMAX' in model_details:
                row_metrics['sarimax_mape'] = model_details['SARIMAX'].get('MAPE')
                
            all_metrics.append(row_metrics)
            print(f"  -> Model evaluated: Ensemble MAPE = {ens_metrics.get('MAPE')}% (MAE: {ens_metrics.get('MAE')})")
            
        except Exception as e:
            print(f"  -> Error forecasting {crop}: {e}")
            
    if not all_forecasts:
        raise RuntimeError("No crop forecasts could be generated.")
        
    df_all_fc = pd.concat(all_forecasts, ignore_index=True)
    df_metrics = pd.DataFrame(all_metrics)
    
    # Save forecasts
    fc_path = os.path.join(output_dir, "crop_price_forecasts.csv")
    df_all_fc.to_csv(fc_path, index=False)
    print(f"\nSaved multi-crop forecasts to: {fc_path} ({len(df_all_fc)} forecast rows)")
    
    # Save metrics
    metrics_path = os.path.join(output_dir, "model_evaluation_metrics.csv")
    df_metrics.to_csv(metrics_path, index=False)
    print(f"Saved evaluation metrics to: {metrics_path}")
    
    # Generate market recommendations
    print("\nGenerating market recommendations and risk assessments...")
    df_recs = generate_crop_recommendations(df, df_all_fc)
    recs_path = os.path.join(output_dir, "market_recommendations.csv")
    df_recs.to_csv(recs_path, index=False)
    print(f"Saved market recommendations to: {recs_path}")
    
    print("\n" + "=" * 60)
    print("Market Recommendations Summary:")
    print("=" * 60)
    for _, row in df_recs.iterrows():
        print(f"[{row['commodity']:<12}] Current: {row['current_price_mwk']:>8.1f} MWK | 4w: {row['pct_change_4w']:>+5.1f}% | 12w: {row['pct_change_12w']:>+5.1f}% | Action: {row['action_badge']} ({row['risk_level']} Risk)")
    print("=" * 60)
    
    return df_all_fc, df_metrics, df_recs

if __name__ == "__main__":
    clean_data_path = "data/processed/clean_northern_region_enriched_prices.csv"
    if not os.path.exists(clean_data_path):
        clean_data_path = "data/processed/clean_malawi_prices.csv"
        
    forecasts_dir = "data/forecasts"
    run_training_and_forecasting(clean_data_path, forecasts_dir)
