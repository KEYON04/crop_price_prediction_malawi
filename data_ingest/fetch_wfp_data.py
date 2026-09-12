import os
import sys
import requests
import pandas as pd

def fetch_wfp_malawi_data(output_path, force=False):
    if os.path.exists(output_path) and os.path.getsize(output_path) > 100000 and not force:
        print(f"Raw WFP dataset already exists at {output_path} ({os.path.getsize(output_path)} bytes). Skipping download.")
        return

    print("Querying HDX API for Malawi WFP food prices...")
    url = "https://data.humdata.org/api/3/action/package_show?id=wfp-food-prices-for-malawi"
    
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        if not data.get("success", False):
            raise Exception("Failed to fetch dataset info from HDX")
            
        resources = data["result"]["resources"]
        
        # Find the CSV resource
        csv_url = None
        for resource in resources:
            if resource.get("format", "").lower() == "csv" and "wfp_food_prices_mwi.csv" in resource.get("url", ""):
                csv_url = resource["url"]
                break
                
        # Fallback if specific name not found
        if not csv_url:
            for resource in resources:
                if resource.get("format", "").lower() == "csv":
                    csv_url = resource["url"]
                    break
                    
        if not csv_url:
            raise Exception("Could not find a CSV resource for this dataset.")
            
        print(f"Downloading data from: {csv_url}")
        df = pd.read_csv(csv_url)
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        df.to_csv(output_path, index=False)
        print(f"Successfully saved raw data to {output_path} ({len(df)} rows)")
    except Exception as e:
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            print(f"Warning: Network query failed ({e}). Reusing existing file at {output_path}.")
        else:
            raise

if __name__ == "__main__":
    force_download = "--force" in sys.argv
    output_file = "data/raw/wfp_malawi_prices.csv"
    fetch_wfp_malawi_data(output_file, force=force_download)

