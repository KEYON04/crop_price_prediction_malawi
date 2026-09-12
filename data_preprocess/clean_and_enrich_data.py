import os
import pandas as pd
import numpy as np

def clean_and_enrich_northern_data(wfp_input_path, exo_input_path, output_path):
    print(f"Loading raw WFP prices from {wfp_input_path}...")
    df_wfp = pd.read_csv(wfp_input_path)
    
    # 1. Filter for Northern Region
    df_wfp = df_wfp[df_wfp['admin1'].str.contains('Northern Region', na=False, case=False)].copy()
    print(f"Found {len(df_wfp)} records in Northern Region.")
    
    # 2. Target crops mapping (prioritized order so 'Soybeans' is not matched by 'Beans')
    target_crop_rules = [
        ('Soybeans', 'Soya beans'),
        ('Soya', 'Soya beans'),
        ('Groundnuts', 'Groundnuts'),
        ('Tomatoes', 'Tomatoes'),
        ('Tomato', 'Tomatoes'),
        ('Rice', 'Rice'),
        ('Maize', 'Maize'),
        ('Beans', 'Beans')
    ]
    
    # Standardize commodity name
    def map_commodity(comm_str):
        if not isinstance(comm_str, str):
            return np.nan
        # Exclude seed if strictly forecasting consumption price
        if 'seed' in comm_str.lower():
            return np.nan
        for key, std_name in target_crop_rules:
            if key.lower() in comm_str.lower():
                return std_name
        return np.nan

    df_wfp['commodity_clean'] = df_wfp['commodity'].apply(map_commodity)
    df_wfp = df_wfp.dropna(subset=['commodity_clean']).copy()
    
    # Parse date to YYYY-MM-01 format (monthly resolution)
    df_wfp['date'] = pd.to_datetime(df_wfp['date'])
    df_wfp['date_monthly'] = df_wfp['date'].dt.to_period('M').dt.to_timestamp()
    
    # Select key columns
    cols_to_keep = ['date_monthly', 'admin1', 'market', 'commodity_clean', 'unit', 'currency', 'price']
    existing_cols = [c for c in cols_to_keep if c in df_wfp.columns]
    df_filtered = df_wfp[existing_cols].copy()
    # Fix common enumerator unit errors (e.g., 50kg bag price entered into 1kg column)
    # Agricultural retail food prices in Malawi per KG are never > 20,000 MWK
    def correct_bag_price(row):
        p = row['price']
        if pd.isna(p) or p <= 0:
            return np.nan
        if p > 20000:
            # Likely a 50kg bag price
            corrected = p / 50.0
            if corrected < 20000:
                return corrected
            return np.nan
        return p

    df_filtered['price'] = df_filtered.apply(correct_bag_price, axis=1)
    df_filtered = df_filtered.dropna(subset=['price'])
    df_filtered.rename(columns={'date_monthly': 'date', 'commodity_clean': 'commodity'}, inplace=True)

    # Aggregate monthly median prices per commodity in Northern Region (median prevents single-station distortions)
    df_agg = df_filtered.groupby(['date', 'admin1', 'commodity'], as_index=False)['price'].median()
    
    # 3. Interpolate missing monthly dates per crop to create continuous time series
    print("Harmonizing time series grid for each crop...")
    crop_frames = []
    
    all_crops = df_agg['commodity'].unique()
    min_date = df_agg['date'].min()
    max_date = df_agg['date'].max()
    full_date_range = pd.date_range(start=min_date, end=max_date, freq='MS')
    
    for crop in all_crops:
        crop_df = df_agg[df_agg['commodity'] == crop].set_index('date')
        # Reindex to full monthly range
        crop_reindexed = crop_df.reindex(full_date_range)
        crop_reindexed['commodity'] = crop
        crop_reindexed['admin1'] = 'Northern Region'
        
        # Interpolate missing prices linearly
        crop_reindexed['price'] = crop_reindexed['price'].interpolate(method='linear', limit_direction='both')
        crop_reindexed = crop_reindexed.reset_index().rename(columns={'index': 'date'})
        crop_frames.append(crop_reindexed)
        
    df_clean = pd.concat(crop_frames, ignore_index=True)
    
    # 4. Load Exogenous Indicators
    print(f"Loading exogenous predictors from {exo_input_path}...")
    if os.path.exists(exo_input_path):
        df_exo = pd.read_csv(exo_input_path)
        df_exo['date'] = pd.to_datetime(df_exo['date'])
        
        # Merge on date
        df_enriched = pd.merge(df_clean, df_exo, on='date', how='left')
    else:
        print("Warning: Exogenous data file not found, proceeding with price data only.")
        df_enriched = df_clean.copy()
        
    # 5. Feature Engineering
    print("Generating temporal and macroeconomic features...")
    df_enriched['year'] = df_enriched['date'].dt.year
    df_enriched['month'] = df_enriched['date'].dt.month
    df_enriched['quarter'] = df_enriched['date'].dt.quarter
    
    # Malawi harvest season (April to June)
    df_enriched['is_harvest_season'] = df_enriched['month'].isin([4, 5, 6]).astype(int)
    # Lean season (December to March)
    df_enriched['is_lean_season'] = df_enriched['month'].isin([12, 1, 2, 3]).astype(int)
    
    # Price in USD (if MWK/USD exchange rate present)
    if 'mwk_usd_exchange_rate' in df_enriched.columns:
        df_enriched['price_usd'] = df_enriched['price'] / df_enriched['mwk_usd_exchange_rate']
        
    # Crop-specific lag and rolling features
    df_enriched = df_enriched.sort_values(by=['commodity', 'date']).reset_index(drop=True)
    
    for lag in [1, 2, 3, 12]:
        df_enriched[f'price_lag_{lag}m'] = df_enriched.groupby('commodity')['price'].shift(lag)
        
    # Moving Averages
    df_enriched['price_ma_3m'] = df_enriched.groupby('commodity')['price'].transform(lambda x: x.rolling(3, min_periods=1).mean())
    df_enriched['price_ma_6m'] = df_enriched.groupby('commodity')['price'].transform(lambda x: x.rolling(6, min_periods=1).mean())
    df_enriched['price_std_3m'] = df_enriched.groupby('commodity')['price'].transform(lambda x: x.rolling(3, min_periods=1).std()).fillna(0)
    
    # Fill remaining initial NaNs for lag features
    lag_cols = [c for c in df_enriched.columns if 'lag' in c]
    for col in lag_cols:
        df_enriched[col] = df_enriched[col].fillna(df_enriched['price'])
        
    # 6. Save final output
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df_enriched.to_csv(output_path, index=False)
    
    # Also save to default clean_malawi_prices.csv for pipeline compatibility
    compat_path = "data/processed/clean_malawi_prices.csv"
    df_enriched.to_csv(compat_path, index=False)
    
    print(f"Successfully generated enriched dataset at {output_path} ({len(df_enriched)} rows, {len(df_enriched.columns)} features)")
    print(f"Crops covered: {df_enriched['commodity'].unique().tolist()}")
    print(f"Date range: {df_enriched['date'].min().date()} to {df_enriched['date'].max().date()}")
    print(f"Feature set: {list(df_enriched.columns)}")

if __name__ == "__main__":
    wfp_raw = "data/raw/wfp_malawi_prices.csv"
    exo_raw = "data/raw/exogenous_indicators.csv"
    output_enriched = "data/processed/clean_northern_region_enriched_prices.csv"
    
    clean_and_enrich_northern_data(wfp_raw, exo_raw, output_enriched)
