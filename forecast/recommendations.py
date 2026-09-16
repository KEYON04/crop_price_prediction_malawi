import pandas as pd
import numpy as np

DEFAULT_FREIGHT_COST_MWK_KG = 140.0  # Estimated trucking & handling cost per kg along M1 transport corridor

def calculate_interregional_arbitrage(df_history, df_forecasts, freight_cost_mwk=DEFAULT_FREIGHT_COST_MWK_KG):
    """
    Calculate price spreads and arbitrage profitability across Malawi regions
    (Northern Region, Central Region, Southern Region) for each storable commodity.
    """
    storable_crops = ['Maize', 'Beans', 'Rice', 'Groundnuts', 'Soya beans']
    arbitrage_records = []
    
    regions = sorted(df_history['region'].unique()) if 'region' in df_history.columns else []
    if len(regions) < 2:
        return pd.DataFrame()
        
    for crop in storable_crops:
        crop_hist = df_history[df_history['commodity'] == crop]
        crop_fc = df_forecasts[df_forecasts['commodity'] == crop]
        
        # Get latest current price per region
        latest_prices = {}
        forecast_4w_prices = {}
        forecast_12w_prices = {}
        
        for reg in regions:
            reg_h = crop_hist[crop_hist['region'] == reg].sort_values('date')
            reg_f = crop_fc[crop_fc['region'] == reg].sort_values('date') if 'region' in crop_fc.columns else pd.DataFrame()
            
            if not reg_h.empty:
                latest_prices[reg] = float(reg_h['price'].iloc[-1])
            if not reg_f.empty:
                forecast_4w_prices[reg] = float(reg_f['price_pred'].iloc[0])
                forecast_12w_prices[reg] = float(reg_f['price_pred'].iloc[min(2, len(reg_f) - 1)])
                
        # Compare every unique pair of regions
        for i in range(len(regions)):
            for j in range(i + 1, len(regions)):
                reg_a = regions[i]
                reg_b = regions[j]
                
                if reg_a not in latest_prices or reg_b not in latest_prices:
                    continue
                    
                p_a = latest_prices[reg_a]
                p_b = latest_prices[reg_b]
                
                # Determine origin (cheaper) and destination (expensive)
                if p_a <= p_b:
                    origin, dest = reg_a, reg_b
                    buy_price, sell_price = p_a, p_b
                else:
                    origin, dest = reg_b, reg_a
                    buy_price, sell_price = p_b, p_a
                    
                gross_spread = sell_price - buy_price
                pct_spread = (gross_spread / buy_price) * 100.0 if buy_price > 0 else 0
                net_margin = gross_spread - freight_cost_mwk
                net_roi = (net_margin / (buy_price + freight_cost_mwk)) * 100.0 if (buy_price + freight_cost_mwk) > 0 else 0
                
                if net_margin > 0 and pct_spread >= 15.0:
                    status = "VIABLE ARBITRAGE"
                    badge = "TRADE OPPORTUNITY"
                    action_summary = f"Buy in {origin.replace(' Region', '')} ({buy_price:,.0f} MWK), ship to {dest.replace(' Region', '')} ({sell_price:,.0f} MWK). Estimated net profit: {net_margin:,.0f} MWK/kg ({net_roi:+.1f}% ROI)."
                elif net_margin > 0:
                    status = "MARGINAL SPREAD"
                    badge = "MARGINAL"
                    action_summary = f"Spread ({gross_spread:,.0f} MWK/kg) marginally covers freight ({freight_cost_mwk:,.0f} MWK/kg). Low safety buffer for transport delays."
                else:
                    status = "UNPROFITABLE"
                    badge = "NO ARBITRAGE"
                    action_summary = f"Regional price difference ({gross_spread:,.0f} MWK/kg) is insufficient to offset transport costs ({freight_cost_mwk:,.0f} MWK/kg)."
                    
                arbitrage_records.append({
                    'commodity': crop,
                    'origin_region': origin,
                    'destination_region': dest,
                    'origin_price_mwk': round(buy_price, 2),
                    'destination_price_mwk': round(sell_price, 2),
                    'gross_spread_mwk': round(gross_spread, 2),
                    'pct_spread': round(pct_spread, 1),
                    'freight_cost_mwk': round(freight_cost_mwk, 2),
                    'net_margin_mwk': round(net_margin, 2),
                    'net_roi_pct': round(net_roi, 1),
                    'status': status,
                    'badge': badge,
                    'action_summary': action_summary
                })
                
    df_arb = pd.DataFrame(arbitrage_records)
    return df_arb

def generate_crop_recommendations(df_history, df_forecasts):
    """
    Generate actionable market recommendations and risk assessments for each region and crop.
    """
    recommendation_records = []
    perishable_crops = ['Tomatoes']
    storable_grains = ['Maize', 'Beans', 'Rice', 'Groundnuts', 'Soya beans']
    
    # Check if multi-region data is present
    has_regions = 'region' in df_history.columns and 'region' in df_forecasts.columns
    regions = sorted(df_history['region'].unique()) if has_regions else ['Northern Region']
    
    for reg in regions:
        df_hist_reg = df_history[df_history['region'] == reg] if has_regions else df_history
        df_fc_reg = df_forecasts[df_forecasts['region'] == reg] if has_regions else df_forecasts
        
        crops = df_fc_reg['commodity'].unique()
        
        for crop in crops:
            crop_hist = df_hist_reg[df_hist_reg['commodity'] == crop].sort_values('date')
            crop_fc = df_fc_reg[df_fc_reg['commodity'] == crop].sort_values('date')
            
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
            
            # Regional context prefix
            reg_short = reg.replace(" Region", "")
            
            # Recommendation logic
            if crop in perishable_crops:
                if pct_change_1m > 8:
                    action = "HARVEST & SELL STAGGERED"
                    action_badge = "SELL / STAGGER"
                    summary = f"Strong short-term demand projected in {reg_short}. Stagger harvests across 2–3 weeks to capture peak market prices without spoilage."
                elif pct_change_1m < -5:
                    action = "SELL IMMEDIATELY"
                    action_badge = "SELL NOW"
                    summary = f"Downside price pressure detected in {reg_short}. Offload ripe produce to local markets to avoid post-harvest spoilage."
                else:
                    action = "MONITOR CLOSELY"
                    action_badge = "MONITOR"
                    summary = f"Stable pricing expected in {reg_short}. Balance sales between farmgate and wholesale market depots."
            else:
                # Grains and legumes
                if pct_change_3m > 12.0 and net_return_pct_3m > 5.0:
                    action = "HOLD & STORE"
                    action_badge = "HOLD & STORE"
                    summary = f"Strong upward trajectory in {reg_short} (+{pct_change_3m:.1f}% in 12w). Net storage margin is +{net_return_pct_3m:.1f}%. Hermetic storage (PICS bags) strongly recommended."
                elif pct_change_1m < -4.0:
                    action = "SELL IMMEDIATELY"
                    action_badge = "SELL NOW"
                    summary = f"Seasonal supply influx or downward price pressure in {reg_short} (-{abs(pct_change_1m):.1f}% in 4w). Liquidate inventory to secure current price."
                elif pct_change_3m < 0.0:
                    action = "OFFLOAD / HEDGE"
                    action_badge = "SELL / HEDGE"
                    summary = f"Softening demand or market saturation anticipated in {reg_short}. Sell incrementally over coming weeks."
                else:
                    action = "HOLD / SELECTIVE SALE"
                    action_badge = "HOLD / SELECTIVE"
                    summary = f"Moderate appreciation in {reg_short} (+{pct_change_1m:.1f}% in 4w). Sell for working capital; otherwise store for seasonal lean price peak."
                    
            if pct_change_3m > 10.0:
                school_advice = f"Lock in procurement contracts now for {reg_short} school feeding programs before projected +{pct_change_3m:.1f}% seasonal surge."
            elif pct_change_3m < -5.0:
                school_advice = f"Delay bulk institutional orders in {reg_short}; prices projected to soften as local harvests enter the market."
            else:
                school_advice = f"Maintain standard recurring purchases in {reg_short}. Market remains within the normal equilibrium band."
                
            record = {
                'region': reg,
                'commodity': crop,
                'current_price_mwk': round(current_price, 2),
                'forecast_4w_mwk': round(p_1m, 2),
                'pct_change_4w': round(pct_change_1m, 1),
                'forecast_12w_mwk': round(p_3m, 2),
                'pct_change_12w': round(pct_change_3m, 1),
                'net_storage_return_pct_12w': round(net_return_pct_3m, 1) if crop in storable_grains else None,
                'action': action,
                'action_badge': action_badge,
                'summary': summary,
                'risk_level': risk_level,
                'risk_color': risk_color,
                'institutional_advice': school_advice,
                'as_of_date': latest_date.strftime('%Y-%m-%d') if hasattr(latest_date, 'strftime') else str(latest_date)
            }
            recommendation_records.append(record)
            
    return pd.DataFrame(recommendation_records)
