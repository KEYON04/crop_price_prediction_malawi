import pandas as pd
import numpy as np

def generate_crop_recommendations(df_history, df_forecasts):
    """
    Generate actionable market recommendations and risk assessments for Northern Region crops.
    """
    crops = df_forecasts['commodity'].unique()
    recommendation_records = []
    
    perishable_crops = ['Tomatoes']
    storable_grains = ['Maize', 'Beans', 'Rice', 'Groundnuts', 'Soya beans']
    
    for crop in crops:
        crop_hist = df_history[df_history['commodity'] == crop].sort_values('date')
        crop_fc = df_forecasts[df_forecasts['commodity'] == crop].sort_values('date')
        
        if crop_hist.empty or crop_fc.empty:
            continue
            
        current_price = float(crop_hist['price'].iloc[-1])
        latest_date = crop_hist['date'].iloc[-1]
        
        # 1-month and 3-month predictions
        p_1m = float(crop_fc['price_pred'].iloc[0])
        pct_change_1m = ((p_1m - current_price) / current_price) * 100.0
        
        p_3m = float(crop_fc['price_pred'].iloc[min(2, len(crop_fc) - 1)])
        pct_change_3m = ((p_3m - current_price) / current_price) * 100.0
        
        # Volatility estimation from historical 12-month rolling std
        recent_std = float(crop_hist['price'].tail(12).std())
        volatility_ratio = (recent_std / current_price) if current_price > 0 else 0
        
        if volatility_ratio > 0.25:
            risk_level = "High"
            risk_color = "red"
        elif volatility_ratio > 0.12:
            risk_level = "Medium"
            risk_color = "orange"
        else:
            risk_level = "Low"
            risk_color = "green"
            
        # Storage cost model (~2.5% per month for fumigation, bagging, loss allowance)
        est_storage_cost_3m = current_price * 0.075
        net_profit_storage_3m = (p_3m - current_price) - est_storage_cost_3m
        net_return_pct_3m = (net_profit_storage_3m / current_price) * 100.0
        
        # Recommendation logic
        if crop in perishable_crops:
            if pct_change_1m > 8:
                action = "HARVEST & SELL STAGGERED"
                action_badge = "SELL / STAGGER"
                summary = "Strong short-term demand projected. Stagger harvests across 2–3 weeks to capture peak market prices without spoilage."
            elif pct_change_1m < -5:
                action = "SELL IMMEDIATELY"
                action_badge = "SELL NOW"
                summary = "Downside price pressure detected. Offload ripe produce to local markets (Mzuzu, Karonga) to avoid post-harvest losses."
            else:
                action = "MONITOR CLOSELY"
                action_badge = "MONITOR"
                summary = "Stable pricing expected. Balance sales between roadside stalls and wholesale depot deliveries."
        else:
            # Grains and legumes
            if pct_change_3m > 12.0 and net_return_pct_3m > 5.0:
                action = "HOLD & STORE"
                action_badge = "HOLD & STORE"
                summary = f"Strong upward trajectory projected (+{pct_change_3m:.1f}% in 12 weeks). Net return after storage costs is +{net_return_pct_3m:.1f}%. Safe hermetic storage (PICS bags) recommended."
            elif pct_change_1m < -4.0:
                action = "SELL IMMEDIATELY"
                action_badge = "SELL NOW"
                summary = f"Upcoming harvest supply surge or downward trend expected (-{abs(pct_change_1m):.1f}% in 4 weeks). Liquidate inventory to secure current high prices."
            elif pct_change_3m < 0.0:
                action = "OFFLOAD / HEDGE"
                action_badge = "SELL / HEDGE"
                summary = "Softening demand or market saturation anticipated. Sell incrementally over the next 2 to 4 weeks."
            else:
                action = "HOLD / SELECTIVE SALE"
                action_badge = "HOLD / SELECTIVE"
                summary = f"Moderate appreciation forecasted (+{pct_change_1m:.1f}% in 4w). Sell only if cash flow is needed; otherwise store for seasonal lean price peaks."
                
        # Advice tailored for school procurement / institutional buyers
        if pct_change_3m > 10.0:
            school_advice = f"Procure bulk supply now for next term's school feeding program before anticipated +{pct_change_3m:.1f}% price surge."
        elif pct_change_3m < -5.0:
            school_advice = "Delay large contract purchases. Prices are projected to soften in coming months as regional supplies expand."
        else:
            school_advice = "Maintain standard recurring purchasing schedules. Prices remain in the expected equilibrium range."
            
        record = {
            'commodity': crop,
            'current_price_mwk': round(current_price, 2),
            'forecast_4w_mwk': round(p_1m, 2),
            'pct_change_4w': round(pct_change_1m, 1),
            'forecast_12w_mwk': round(p_3m, 2),
            'pct_change_12w': round(pct_change_3m, 1),
            'net_storage_return_pct_12w': round(net_return_pct_3m, 1) if crop in storable_grains else None,
            'action': action,
            'action_badge': action_badge,
            'risk_level': risk_level,
            'risk_color': risk_color,
            'farmer_trader_summary': summary,
            'institutional_school_advice': school_advice,
            'latest_price_date': latest_date.strftime('%Y-%m-%d')
        }
        recommendation_records.append(record)
        
    df_recs = pd.DataFrame(recommendation_records)
    return df_recs
