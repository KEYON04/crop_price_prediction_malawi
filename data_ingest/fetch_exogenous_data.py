import os
import requests
import pandas as pd
import numpy as np
from datetime import datetime

REGIONAL_COORDINATES = {
    "Northern Region": {"lat": -11.45, "lon": 34.02, "name": "Mzuzu"},
    "Central Region": {"lat": -13.98, "lon": 33.78, "name": "Lilongwe"},
    "Southern Region": {"lat": -15.79, "lon": 35.01, "name": "Blantyre"}
}

def fetch_worldbank_indicator(country_code="MWI", indicator="PA.NUS.FCRF", date_range="2000:2026"):
    """
    Fetch annual/monthly economic indicators from World Bank API for Malawi.
    PA.NUS.FCRF = Official exchange rate (LCU per US$, period average)
    FP.CPI.TOTL.ZG = Inflation, consumer prices (annual %)
    """
    url = f"http://api.worldbank.org/v2/country/{country_code}/indicator/{indicator}?date={date_range}&format=json&per_page=1000"
    try:
        res = requests.get(url, timeout=15)
        res.raise_for_status()
        json_data = res.json()
        if len(json_data) > 1 and json_data[1]:
            records = []
            for entry in json_data[1]:
                year = entry.get('date')
                val = entry.get('value')
                if year and val is not None:
                    records.append({'year': int(year), indicator: float(val)})
            return pd.DataFrame(records)
    except Exception as e:
        print(f"Warning: Could not fetch WB indicator {indicator}: {e}")
    return pd.DataFrame()

def fetch_openmeteo_climate_for_region(region_name, lat, lon):
    """
    Fetch historical precipitation & temperature trends for a specific Malawi region via Open-Meteo archive API.
    """
    start_date = "2000-01-01"
    end_date = datetime.now().strftime("%Y-%m-%d")
    url = f"https://archive-api.open-meteo.com/v1/archive?latitude={lat}&longitude={lon}&start_date={start_date}&end_date={end_date}&daily=precipitation_sum,temperature_2m_max,temperature_2m_min&timezone=Africa%2FBlantyre"
    
    try:
        print(f"Fetching historical weather data for {region_name} via Open-Meteo...")
        res = requests.get(url, timeout=20)
        res.raise_for_status()
        data = res.json()
        if "daily" in data:
            df_daily = pd.DataFrame(data["daily"])
            df_daily['date'] = pd.to_datetime(df_daily['time'])
            df_daily['year_month'] = df_daily['date'].dt.to_period('M')
            
            # Resample to monthly aggregation
            df_monthly = df_daily.groupby('year_month').agg({
                'precipitation_sum': 'sum',
                'temperature_2m_max': 'mean',
                'temperature_2m_min': 'mean'
            }).reset_index()
            df_monthly['date'] = df_monthly['year_month'].dt.to_timestamp()
            df_monthly = df_monthly.drop(columns=['year_month'])
            df_monthly.rename(columns={
                'precipitation_sum': 'rainfall_mm',
                'temperature_2m_max': 'temp_max_c',
                'temperature_2m_min': 'temp_min_c'
            }, inplace=True)
            df_monthly['region'] = region_name
            print(f"  -> Retrieved {len(df_monthly)} monthly weather observations for {region_name}.")
            return df_monthly
    except Exception as e:
        print(f"Warning: Open-Meteo API query for {region_name} failed: {e}")
    
    return pd.DataFrame()

def generate_fallback_exogenous(date_range_months, region_name="Northern Region"):
    """
    Synthesize realistic historical exogenous features for Malawi regions
    if external APIs fail or have incomplete coverage.
    """
    df = pd.DataFrame({'date': date_range_months})
    df['year'] = df['date'].dt.year
    df['month'] = df['date'].dt.month
    df['region'] = region_name
    
    # Regional rainfall profiles
    # North: wetter late rainy season; South: earlier onset, warmer; Central: balanced
    base_mult = {
        "Northern Region": {1: 220, 2: 200, 3: 180, 4: 80, 5: 20, 6: 5, 7: 2, 8: 2, 9: 5, 10: 25, 11: 90, 12: 180},
        "Central Region": {1: 240, 2: 210, 3: 150, 4: 40, 5: 10, 6: 2, 7: 1, 8: 1, 9: 3, 10: 15, 11: 70, 12: 190},
        "Southern Region": {1: 260, 2: 230, 3: 160, 4: 50, 5: 15, 6: 5, 7: 3, 8: 3, 9: 5, 10: 20, 11: 85, 12: 220}
    }
    rain_profile = base_mult.get(region_name, base_mult["Central Region"])
    df['rainfall_mm'] = df['month'].map(rain_profile) * np.random.uniform(0.85, 1.15, len(df))
    
    years_from_2003 = df['year'] - 2003
    df['mwk_usd_exchange_rate'] = 90.0 * (1.15 ** years_from_2003) + np.random.normal(0, 10, len(df))
    df['cpi_inflation_rate'] = 10.0 + 5.0 * np.sin(years_from_2003) + np.random.normal(0, 2, len(df))
    df['fuel_price_mwk_liter'] = df['mwk_usd_exchange_rate'] * 1.35
    
    # Regional temperatures
    temp_offset = {"Northern Region": 0.0, "Central Region": 1.2, "Southern Region": 2.8}.get(region_name, 1.0)
    df['temp_max_c'] = (26.5 + temp_offset) + 3.0 * np.cos((df['month'] - 11) * np.pi / 6)
    df['temp_min_c'] = (15.0 + temp_offset) + 3.0 * np.cos((df['month'] - 11) * np.pi / 6)
    
    return df[['date', 'region', 'rainfall_mm', 'temp_max_c', 'temp_min_c', 'mwk_usd_exchange_rate', 'cpi_inflation_rate', 'fuel_price_mwk_liter']]

def fetch_and_build_all_regions_exogenous(output_path, force=False):
    if os.path.exists(output_path) and os.path.getsize(output_path) > 1000 and not force:
        print(f"Regional exogenous dataset already exists at {output_path} ({os.path.getsize(output_path)} bytes). Skipping download.")
        return
        
    print("Building multi-region exogenous dataset for all Malawi regions (North, Central, South)...")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # 1. World Bank indicators (national level)
    df_fx = fetch_worldbank_indicator(indicator="PA.NUS.FCRF")
    df_cpi = fetch_worldbank_indicator(indicator="FP.CPI.TOTL.ZG")
    
    start_date = "2000-01-01"
    end_date = datetime.now().strftime("%Y-%m-%d")
    dates = pd.date_range(start=start_date, end=end_date, freq='MS')
    
    all_region_dfs = []
    
    for region_name, coords in REGIONAL_COORDINATES.items():
        print(f"\nProcessing climate indicators for [{region_name}] ({coords['name']})...")
        df_weather = fetch_openmeteo_climate_for_region(region_name, coords['lat'], coords['lon'])
        
        df_base = pd.DataFrame({'date': dates})
        df_base['year'] = df_base['date'].dt.year
        df_base['month'] = df_base['date'].dt.month
        df_base['region'] = region_name
        
        if not df_weather.empty:
            df_base = pd.merge(df_base, df_weather[['date', 'rainfall_mm', 'temp_max_c', 'temp_min_c']], on='date', how='left')
            
        if not df_fx.empty:
            df_fx_copy = df_fx.copy()
            df_fx_copy.rename(columns={"PA.NUS.FCRF": "mwk_usd_exchange_rate"}, inplace=True)
            df_base = pd.merge(df_base, df_fx_copy, on='year', how='left')
            
        if not df_cpi.empty:
            df_cpi_copy = df_cpi.copy()
            df_cpi_copy.rename(columns={"FP.CPI.TOTL.ZG": "cpi_inflation_rate"}, inplace=True)
            df_base = pd.merge(df_base, df_cpi_copy, on='year', how='left')
            
        df_fallback = generate_fallback_exogenous(df_base['date'], region_name)
        
        for col in ['rainfall_mm', 'temp_max_c', 'temp_min_c', 'mwk_usd_exchange_rate', 'cpi_inflation_rate', 'fuel_price_mwk_liter']:
            if col not in df_base.columns:
                df_base[col] = df_fallback[col]
            else:
                df_base[col] = df_base[col].fillna(df_fallback[col])
                
        cols = ['date', 'region', 'rainfall_mm', 'temp_max_c', 'temp_min_c', 'mwk_usd_exchange_rate', 'cpi_inflation_rate', 'fuel_price_mwk_liter']
        all_region_dfs.append(df_base[cols])
        
    df_all_out = pd.concat(all_region_dfs, ignore_index=True).sort_values(['region', 'date']).reset_index(drop=True)
    df_all_out.to_csv(output_path, index=False)
    print(f"\nSaved multi-region exogenous indicators to {output_path} ({len(df_all_out)} rows across {df_all_out['region'].nunique()} regions)")
    
    # Backwards compatibility output for northern region
    north_file = "data/raw/exogenous_indicators.csv"
    df_north = df_all_out[df_all_out['region'] == 'Northern Region'].drop(columns=['region']).copy()
    df_north.to_csv(north_file, index=False)
    print(f"Saved backwards-compatible Northern indicators to {north_file}")

if __name__ == "__main__":
    import sys
    force_download = "--force" in sys.argv
    out_file = "data/raw/exogenous_indicators_all_regions.csv"
    fetch_and_build_all_regions_exogenous(out_file, force=force_download)
