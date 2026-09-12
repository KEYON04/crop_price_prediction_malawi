import os
import pandas as pd

def clean_wfp_malawi_data(input_path, output_path):
    print(f"Loading raw data from {input_path}...")
    df = pd.read_csv(input_path)
    
    # Filter for Northern Region
    df = df[df['admin1'].str.contains('Northern Region', na=False, case=False)]
    
    # Target crops
    target_crops = ['Maize', 'Beans', 'Tomatoes', 'Rice', 'Groundnuts', 'Soya beans']
    
    # We will do a generic matching to capture the main crop categories
    pattern = '|'.join(target_crops)
    df_filtered = df[df['commodity'].str.contains(pattern, na=False, case=False)]
    
    # Select relevant columns
    cols_to_keep = ['date', 'admin1', 'commodity', 'unit', 'price', 'currency']
    df_filtered = df_filtered[cols_to_keep].copy()
    
    # Convert date to datetime
    df_filtered['date'] = pd.to_datetime(df_filtered['date'])
    
    # Clean up commodity names to just the base crop name for simplicity
    for crop in target_crops:
        df_filtered.loc[df_filtered['commodity'].str.contains(crop, case=False, na=False), 'commodity_clean'] = crop
        
    # If a row didn't match cleanly, keep its original commodity name
    df_filtered['commodity_clean'] = df_filtered['commodity_clean'].fillna(df_filtered['commodity'])
    
    # Drop original commodity and rename clean one
    df_filtered = df_filtered.drop('commodity', axis=1)
    df_filtered = df_filtered.rename(columns={'commodity_clean': 'commodity'})
    
    # Group by date, region, and commodity to get regional averages
    df_filtered = df_filtered.groupby(['date', 'admin1', 'commodity', 'unit', 'currency'], as_index=False)['price'].mean()
    
    # Sort by date
    df_filtered = df_filtered.sort_values(by=['commodity', 'date'])
    
    # Save the cleaned dataset
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df_filtered.to_csv(output_path, index=False)
    
    print(f"Successfully processed and saved clean data to {output_path} ({len(df_filtered)} rows)")
    print(f"Available crops: {df_filtered['commodity'].unique()}")
    if len(df_filtered) > 0:
        print(f"Date range: {df_filtered['date'].min().date()} to {df_filtered['date'].max().date()}")

if __name__ == "__main__":
    input_file = "data/raw/wfp_malawi_prices.csv"
    output_file = "data/processed/clean_malawi_prices.csv"
    clean_wfp_malawi_data(input_file, output_file)
