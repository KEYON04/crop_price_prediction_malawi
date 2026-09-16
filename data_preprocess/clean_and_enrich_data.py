import os
import pandas as pd
import numpy as np

VALID_REGIONS = ["Northern Region", "Central Region", "Southern Region"]

def clean_and_enrich_all_regions_data(wfp_input_path, exo_input_path, output_path):
    print(f"Loading raw WFP prices from {wfp_input_path}...")
    df_wfp = pd.read_csv(wfp_input_path)
    
    # 1. Standardize admin1 region names
    def standardize_region(admin1_str):
        if not isinstance(admin1_str, str):
            return np.nan
        for r in VALID_REGIONS:
            if r.lower() in admin1_str.lower() or admin1_str.lower() in r.lower():
                return r
        return np.nan

    df_wfp['region'] = df_wfp['admin1'].apply(standardize_region)
    df_wfp = df_wfp.dropna(subset=['region']).copy()
    print(f"Found {len(df_wfp)} records across regions: {df_wfp['region'].value_counts().to_dict()}")
    
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
    
    def map_commodity(comm_str):
        if not isinstance(comm_str, str):
            return np.nan
        if 'seed' in comm_str.lower():
            return np.nan
        for key, std_name in target_crop_rules:
            if key.lower() in comm_str.lower():
                return std_name
        return np.nan

    df_wfp['commodity_clean'] = df_wfp['commodity'].apply(map_commodity)
    df_wfp = df_wfp.dropna(subset=['commodity_clean']).copy()
    
    # Parse date to monthly resolution (YYYY-MM-01)
    df_wfp['date'] = pd.to_datetime(df_wfp['date'])
    df_wfp['date_monthly'] = df_wfp['date'].dt.to_period('M').dt.to_timestamp()
    
    # Fix common enumerator unit errors (50kg bag price entered into 1kg column)
    def correct_bag_price(row):
        p = row['price']
        if pd.isna(p) or p <= 0:
            return np.nan
        if p > 20000:
            corrected = p / 50.0
            if corrected < 20000:
                return corrected
            return np.nan
        return p

    df_wfp['price_clean'] = df_wfp.apply(correct_bag_price, axis=1)
    df_filtered = df_wfp.dropna(subset=['price_clean']).copy()
    df_filtered = df_filtered[['date_monthly', 'region', 'commodity_clean', 'market', 'price_clean']].rename(
        columns={'date_monthly': 'date', 'commodity_clean': 'commodity', 'price_clean': 'price'}
    )

    # Aggregate monthly median prices per (date, region, commodity) with market count verification
    print("Aggregating monthly median prices per region and crop with market quorum check...")
    df_agg = df_filtered.groupby(['date', 'region', 'commodity']).agg(
        price=('price', 'median'),
        market_count=('market', 'nunique')
    ).reset_index()

    # Quorum adjustment: if an observation has only 1 reporting market (e.g. single border market survey)
    # and deviates by > 20% from the recent 3-month regional price, blend it with the recent multi-market trend
    adjusted_frames = []
    for (reg, crop), group in df_agg.groupby(['region', 'commodity']):
        group = group.sort_values('date').copy()
        rolling_recent = group['price'].shift(1).rolling(3, min_periods=1).median()
        for idx, row in group.iterrows():
            m_cnt = row['market_count']
            p = row['price']
            hist_ref = rolling_recent.loc[idx]
            if m_cnt == 1 and pd.notna(hist_ref) and abs(p - hist_ref) / hist_ref > 0.20:
                # Blend 55% single-market quote with 45% recent regional market baseline
                group.loc[idx, 'price'] = round(0.55 * p + 0.45 * hist_ref, 2)
        adjusted_frames.append(group[['date', 'region', 'commodity', 'price']])
        
    df_agg = pd.concat(adjusted_frames, ignore_index=True)
    
    # 3. Harmonize time series grid for each (region, crop)
    print("Harmonizing time series grid across all region-crop pairs...")
    all_regions = df_agg['region'].unique()
    all_crops = df_agg['commodity'].unique()
    min_date = df_agg['date'].min()
    max_date = df_agg['date'].max()
    full_date_range = pd.date_range(start=min_date, end=max_date, freq='MS')
    
    series_frames = []
    for reg in all_regions:
        for crop in all_crops:
            sub = df_agg[(df_agg['region'] == reg) & (df_agg['commodity'] == crop)].set_index('date')
            sub_reindexed = sub.reindex(full_date_range)
            sub_reindexed['region'] = reg
            sub_reindexed['commodity'] = crop
            # Linear interpolation for gaps, bounded
            sub_reindexed['price'] = sub_reindexed['price'].interpolate(method='linear', limit_direction='both')
            sub_reindexed = sub_reindexed.reset_index().rename(columns={'index': 'date'})
            series_frames.append(sub_reindexed)
            
    df_clean = pd.concat(series_frames, ignore_index=True)
    df_clean = df_clean.dropna(subset=['price']).copy()
    
    # 4. Load Exogenous Indicators
    print(f"Loading exogenous predictors from {exo_input_path}...")
    if os.path.exists(exo_input_path):
        df_exo = pd.read_csv(exo_input_path)
        df_exo['date'] = pd.to_datetime(df_exo['date'])
        
        if 'region' in df_exo.columns:
            df_enriched = pd.merge(df_clean, df_exo, on=['date', 'region'], how='left')
        else:
            df_enriched = pd.merge(df_clean, df_exo, on='date', how='left')
    else:
        print("Warning: Exogenous data file not found, proceeding with price data only.")
        df_enriched = df_clean.copy()
        
    # 5. Feature Engineering
    print("Generating temporal, seasonal, and macroeconomic features...")
    df_enriched['year'] = df_enriched['date'].dt.year
    df_enriched['month'] = df_enriched['date'].dt.month
    df_enriched['quarter'] = df_enriched['date'].dt.quarter
    
    # Malawi seasons
    df_enriched['is_harvest_season'] = df_enriched['month'].isin([4, 5, 6]).astype(int)
    df_enriched['is_lean_season'] = df_enriched['month'].isin([12, 1, 2, 3]).astype(int)
    
    # Price in USD
    if 'mwk_usd_exchange_rate' in df_enriched.columns:
        df_enriched['price_usd'] = df_enriched['price'] / df_enriched['mwk_usd_exchange_rate']
        
    # Region & Crop specific lag and rolling features
    df_enriched = df_enriched.sort_values(by=['region', 'commodity', 'date']).reset_index(drop=True)
    
    for lag in [1, 2, 3, 12]:
        df_enriched[f'price_lag_{lag}m'] = df_enriched.groupby(['region', 'commodity'])['price'].shift(lag)
        
    # Moving Averages per (region, commodity)
    df_enriched['price_ma_3m'] = df_enriched.groupby(['region', 'commodity'])['price'].transform(lambda x: x.rolling(3, min_periods=1).mean())
    df_enriched['price_ma_6m'] = df_enriched.groupby(['region', 'commodity'])['price'].transform(lambda x: x.rolling(6, min_periods=1).mean())
    df_enriched['price_std_3m'] = df_enriched.groupby(['region', 'commodity'])['price'].transform(lambda x: x.rolling(3, min_periods=1).std()).fillna(0)
    
    # Fill remaining initial NaNs for lag features
    lag_cols = [c for c in df_enriched.columns if 'lag' in c]
    for col in lag_cols:
        df_enriched[col] = df_enriched[col].fillna(df_enriched['price'])
        
    # Standardize column naming: provide both 'admin1' and 'region' for backwards compatibility
    df_enriched['admin1'] = df_enriched['region']
    
    # 6. Save final outputs
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df_enriched.to_csv(output_path, index=False)
    
    # Backwards compatibility outputs
    north_output = "data/processed/clean_northern_region_enriched_prices.csv"
    df_north = df_enriched[df_enriched['region'] == 'Northern Region'].copy()
    df_north.to_csv(north_output, index=False)
    
    default_compat = "data/processed/clean_malawi_prices.csv"
    df_enriched.to_csv(default_compat, index=False)
    
    print(f"\nSuccessfully generated enriched dataset at {output_path} ({len(df_enriched)} rows, {len(df_enriched.columns)} features)")
    print(f"Regions: {df_enriched['region'].unique().tolist()}")
    print(f"Crops: {df_enriched['commodity'].unique().tolist()}")
    print(f"Date range: {df_enriched['date'].min().date()} to {df_enriched['date'].max().date()}")
    print(f"Observations per region: {df_enriched.groupby('region').size().to_dict()}")

if __name__ == "__main__":
    wfp_raw = "data/raw/wfp_malawi_prices.csv"
    exo_all = "data/raw/exogenous_indicators_all_regions.csv"
    if not os.path.exists(exo_all):
        exo_all = "data/raw/exogenous_indicators.csv"
        
    out_all = "data/processed/clean_malawi_all_regions_enriched_prices.csv"
    clean_and_enrich_all_regions_data(wfp_raw, exo_all, out_all)
