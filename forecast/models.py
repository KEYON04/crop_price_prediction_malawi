import numpy as np
import pandas as pd
import warnings
from datetime import timedelta
from prophet import Prophet
from statsmodels.tsa.statespace.sarimax import SARIMAX

warnings.filterwarnings('ignore')

def calculate_metrics(y_true, y_pred):
    """
    Calculate evaluation metrics: MAE, RMSE, MAPE.
    """
    y_true = np.array(y_true, dtype=float)
    y_pred = np.array(y_pred, dtype=float)
    mask = (y_true != 0) & ~np.isnan(y_true) & ~np.isnan(y_pred)
    if not np.any(mask):
        return {'MAE': 0.0, 'RMSE': 0.0, 'MAPE': 0.0}
    
    mae = np.mean(np.abs(y_true[mask] - y_pred[mask]))
    rmse = np.sqrt(np.mean((y_true[mask] - y_pred[mask]) ** 2))
    mape = np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100.0
    return {
        'MAE': round(float(mae), 2),
        'RMSE': round(float(rmse), 2),
        'MAPE': round(float(mape), 2)
    }

def fit_prophet_model(df_crop, horizon_months=6, regressor_cols=None):
    """
    Fit Prophet model with optional exogenous regressors and generate future predictions.
    """
    if regressor_cols is None:
        regressor_cols = ['rainfall_mm', 'mwk_usd_exchange_rate', 'fuel_price_mwk_liter', 'is_lean_season']
    
    df_p = df_crop[['date', 'price'] + [c for c in regressor_cols if c in df_crop.columns]].copy()
    df_p.rename(columns={'date': 'ds', 'price': 'y'}, inplace=True)
    df_p = df_p.sort_values('ds').reset_index(drop=True)
    
    # Train/validation split: last 6 months for evaluation
    val_len = min(6, max(2, int(len(df_p) * 0.1)))
    train_df = df_p.iloc[:-val_len].copy()
    test_df = df_p.iloc[-val_len:].copy()
    
    m = Prophet(
        yearly_seasonality=True,
        weekly_seasonality=False,
        daily_seasonality=False,
        seasonality_mode='multiplicative',
        interval_width=0.95
    )
    
    avail_regressors = [c for c in regressor_cols if c in df_p.columns]
    for r in avail_regressors:
        m.add_regressor(r)
        
    m.fit(train_df)
    
    # Evaluate on test set
    val_forecast = m.predict(test_df)
    metrics = calculate_metrics(test_df['y'], val_forecast['yhat'])
    
    # Refit on full series for forward forecast
    m_full = Prophet(
        yearly_seasonality=True,
        weekly_seasonality=False,
        daily_seasonality=False,
        seasonality_mode='multiplicative',
        interval_width=0.95
    )
    for r in avail_regressors:
        m_full.add_regressor(r)
    m_full.fit(df_p)
    
    # Create future dataframe
    future_dates = pd.date_range(
        start=df_p['ds'].max() + pd.DateOffset(months=1),
        periods=horizon_months,
        freq='MS'
    )
    df_future = pd.DataFrame({'ds': future_dates})
    
    # Populate future regressors (project from recent trends or seasonal averages)
    last_row = df_p.iloc[-1]
    for r in avail_regressors:
        if r == 'is_lean_season':
            df_future[r] = df_future['ds'].dt.month.isin([12, 1, 2, 3]).astype(int)
        elif r == 'rainfall_mm':
            month_avg = df_p.groupby(df_p['ds'].dt.month)[r].mean()
            df_future[r] = df_future['ds'].dt.month.map(month_avg)
        elif r in ['mwk_usd_exchange_rate', 'fuel_price_mwk_liter']:
            # Assume 1% monthly inflation drift if recent trend
            rates = [last_row[r] * ((1.01) ** i) for i in range(1, horizon_months + 1)]
            df_future[r] = rates
        else:
            df_future[r] = last_row[r]
            
    full_future_df = pd.concat([df_p[['ds'] + avail_regressors], df_future], ignore_index=True)
    full_fc = m_full.predict(full_future_df)
    
    out_df = full_fc[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].tail(horizon_months).copy()
    out_df.rename(columns={
        'ds': 'date',
        'yhat': 'price_pred',
        'yhat_lower': 'price_lower_95',
        'yhat_upper': 'price_upper_95'
    }, inplace=True)
    
    # 80% interval approximation
    spread_95 = (out_df['price_upper_95'] - out_df['price_lower_95']) / (2 * 1.96)
    out_df['price_lower_80'] = out_df['price_pred'] - 1.28 * spread_95
    out_df['price_upper_80'] = out_df['price_pred'] + 1.28 * spread_95
    out_df['model'] = 'Prophet'
    
    return out_df, metrics

def fit_sarimax_model(df_crop, horizon_months=6, regressor_cols=None):
    """
    Fit SARIMAX model with optional exogenous indicators.
    """
    if regressor_cols is None:
        regressor_cols = ['rainfall_mm', 'mwk_usd_exchange_rate', 'fuel_price_mwk_liter']
        
    df_s = df_crop.sort_values('date').reset_index(drop=True)
    avail_regressors = [c for c in regressor_cols if c in df_s.columns]
    
    y = df_s['price'].astype(float)
    X = df_s[avail_regressors].astype(float) if avail_regressors else None
    
    val_len = min(6, max(2, int(len(df_s) * 0.1)))
    y_train = y.iloc[:-val_len]
    X_train = X.iloc[:-val_len] if X is not None else None
    y_test = y.iloc[-val_len:]
    X_test = X.iloc[-val_len:] if X is not None else None
    
    try:
        model = SARIMAX(y_train, exog=X_train, order=(1, 1, 1), seasonal_order=(1, 0, 0, 12),
                        enforce_stationarity=False, enforce_invertibility=False)
        res = model.fit(disp=False, maxiter=100)
        y_val_pred = res.forecast(steps=val_len, exog=X_test)
        metrics = calculate_metrics(y_test, y_val_pred)
    except Exception:
        # Fallback to simple AR(1)
        model = SARIMAX(y_train, order=(1, 1, 0), enforce_stationarity=False)
        res = model.fit(disp=False)
        y_val_pred = res.forecast(steps=val_len)
        metrics = calculate_metrics(y_test, y_val_pred)
        
    # Fit on full data
    try:
        model_full = SARIMAX(y, exog=X, order=(1, 1, 1), seasonal_order=(1, 0, 0, 12),
                             enforce_stationarity=False, enforce_invertibility=False)
        res_full = model_full.fit(disp=False, maxiter=100)
    except Exception:
        model_full = SARIMAX(y, order=(1, 1, 0), enforce_stationarity=False)
        res_full = model_full.fit(disp=False)
        
    # Future exog
    future_dates = pd.date_range(
        start=df_s['date'].max() + pd.DateOffset(months=1),
        periods=horizon_months,
        freq='MS'
    )
    if X is not None:
        last_row = X.iloc[-1]
        future_X = pd.DataFrame(index=range(horizon_months))
        for col in avail_regressors:
            if col == 'rainfall_mm':
                month_avg = df_s.groupby(df_s['date'].dt.month)[col].mean()
                future_X[col] = [month_avg.get(d.month, last_row[col]) for d in future_dates]
            elif col in ['mwk_usd_exchange_rate', 'fuel_price_mwk_liter']:
                future_X[col] = [last_row[col] * (1.01 ** i) for i in range(1, horizon_months + 1)]
            else:
                future_X[col] = last_row[col]
        forecast_res = res_full.get_forecast(steps=horizon_months, exog=future_X)
    else:
        forecast_res = res_full.get_forecast(steps=horizon_months)
        
    pred_mean = forecast_res.predicted_mean.values
    conf_int_95 = forecast_res.conf_int(alpha=0.05).values
    conf_int_80 = forecast_res.conf_int(alpha=0.20).values
    
    out_df = pd.DataFrame({
        'date': future_dates,
        'price_pred': np.maximum(0, pred_mean),
        'price_lower_80': np.maximum(0, conf_int_80[:, 0]),
        'price_upper_80': np.maximum(0, conf_int_80[:, 1]),
        'price_lower_95': np.maximum(0, conf_int_95[:, 0]),
        'price_upper_95': np.maximum(0, conf_int_95[:, 1]),
        'model': 'SARIMAX'
    })
    
    return out_df, metrics

def fit_ensemble_model(df_crop, horizon_months=6):
    """
    Ensemble combination of Prophet and SARIMAX for robust crop price forecasting.
    """
    prophet_df, p_metrics = None, None
    sarimax_df, s_metrics = None, None
    
    try:
        prophet_df, p_metrics = fit_prophet_model(df_crop, horizon_months=horizon_months)
    except Exception as e:
        print(f"Warning: Prophet fitting failed ({e})")
        
    try:
        sarimax_df, s_metrics = fit_sarimax_model(df_crop, horizon_months=horizon_months)
    except Exception as e:
        print(f"Warning: SARIMAX fitting failed ({e})")
        
    if prophet_df is not None and sarimax_df is not None:
        # 50/50 blend of predictions and intervals
        ensemble_df = prophet_df.copy()
        for col in ['price_pred', 'price_lower_80', 'price_upper_80', 'price_lower_95', 'price_upper_95']:
            ensemble_df[col] = (prophet_df[col].values + sarimax_df[col].values) / 2.0
        ensemble_df['model'] = 'Ensemble (Prophet + SARIMAX)'
        
        ensemble_metrics = {
            'MAE': round((p_metrics['MAE'] + s_metrics['MAE']) / 2.0, 2),
            'RMSE': round((p_metrics['RMSE'] + s_metrics['RMSE']) / 2.0, 2),
            'MAPE': round((p_metrics['MAPE'] + s_metrics['MAPE']) / 2.0, 2)
        }
        return ensemble_df, ensemble_metrics, {'Prophet': p_metrics, 'SARIMAX': s_metrics}
    elif prophet_df is not None:
        return prophet_df, p_metrics, {'Prophet': p_metrics}
    elif sarimax_df is not None:
        return sarimax_df, s_metrics, {'SARIMAX': s_metrics}
    else:
        raise RuntimeError("Both Prophet and SARIMAX forecasting models failed.")
