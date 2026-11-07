"""
Decision Making Engine for Malawi Crop Intelligence Platform.
Evaluates storage economics, price appreciation curves, carrying costs,
and post-harvest risk factors to deliver actionable strategic decisions:
HOLD & STORE vs. SELL NOW vs. MONITOR in both Simple English and Chichewa.
"""

from .prediction_engine import generate_price_forecast, get_current_district_price
from .district_data import DISTRICT_LOOKUP

MONTHLY_STORAGE_CARRYING_COST_PCT = 2.5  # 2.5% per month (PICS bag, warehousing, capital opportunity)


def evaluate_decision(district_id, commodity, custom_spot_price=None):
    """
    Evaluates whether a farmer, cooperative, or trader in a given district
    should SELL NOW, HOLD & STORE, or MONITOR.
    Includes simple English and Chichewa translations for easy field understanding.
    """
    forecast_data = generate_price_forecast(district_id, commodity, custom_spot_price=custom_spot_price)
    dist = forecast_data["district"]
    current_price = forecast_data["current_price"]
    
    # 4-week (1 month) and 12-week (3 months) projected changes
    change_4w = forecast_data["recommendation_summary"]["4w_change_pct"]
    change_12w = forecast_data["recommendation_summary"]["12w_change_pct"]
    
    # Storage economics over 3 months (12 weeks)
    carrying_cost_12w_pct = MONTHLY_STORAGE_CARRYING_COST_PCT * 3.0  # 7.5%
    net_storage_roi_pct = round(change_12w - carrying_cost_12w_pct, 1)
    
    # Monetary profit estimation per 50kg bag and per 1,000kg (1 metric ton)
    gross_12w_price = current_price * (1.0 + (change_12w / 100.0))
    carrying_cost_mwk_per_kg = current_price * (carrying_cost_12w_pct / 100.0)
    net_profit_per_kg = round((gross_12w_price - current_price) - carrying_cost_mwk_per_kg, 1)
    net_profit_per_50kg_bag = round(net_profit_per_kg * 50.0, 0)
    net_profit_per_ton = round(net_profit_per_kg * 1000.0, 0)

    # Core Decision Logic with Chichewa & Simple English
    if net_storage_roi_pct >= 6.0 and change_12w > 12.0:
        decision = "HOLD & STORE"
        decision_chichewa = "Sungani / Musagulitse Pano"
        badge_class = "badge-hold"
        color = "#16a34a"  # Green
        summary = (
            f"Strong upward price trend in {dist['name']} (+{change_12w}% over 3 months). "
            f"Net gain after storage costs (7.5%) is +{net_storage_roi_pct}%. "
            f"Holding produce in hermetic PICS bags is strongly recommended."
        )
        simple_summary = (
            f"Prices are going up. If you store 1 bag for 3 months using PICS hermetic bags, "
            f"you will make about {net_profit_per_50kg_bag:,.0f} MWK extra profit per 50kg bag after storage costs."
        )
        chichewa_summary = (
            f"Mitengo ikukwera m'chigawo cha {dist['name']}. Mukasunga mbeu zanu m'zikhwama za PICS kwa miyezi 3, "
            f"mupeza phindu la {net_profit_per_50kg_bag:,.0f} MWK pa thumba lililonse la 50kg mutachotsa mtengo wosungira."
        )
        smallholder_action = (
            "Do not sell at current farmgate price. Clean and dry your produce, then store in airtight PICS bags. "
            f"Projected net profit is {net_profit_per_50kg_bag:,.0f} MWK per 50kg bag."
        )
        cooperative_action = (
            "Aggregate member volumes into community warehouse. Secure warehouse receipts. "
            "Target sales during lean season price peak."
        )
        institutional_action = (
            f"Lock in procurement contracts immediately in {dist['name']}. Prices are projected to surge "
            f"+{change_12w}% before the next harvest cycle."
        )
        risk_level = "Medium" if change_12w < 30.0 else "High (Price Surge Risk)"

    elif change_4w <= -3.0 or change_12w < carrying_cost_12w_pct:
        decision = "SELL NOW"
        decision_chichewa = "Gulisani Pano"
        badge_class = "badge-sell"
        color = "#dc2626"  # Red
        summary = (
            f"Price softening or downward pressure detected in {dist['name']} (4w: {change_4w}%, 12w: {change_12w}%). "
            f"Storage will not cover carrying costs (-{abs(net_storage_roi_pct)}% net loss). "
            f"Selling immediately is advised."
        )
        simple_summary = (
            f"Prices are expected to drop or stay low. Do not store; sell your produce now to secure today's price "
            f"and avoid storage losses."
        )
        chichewa_summary = (
            f"Mitengo ikuyembekezeka kutsika kapena kusakwera mokwanira. Osasunga; gulisani zokolola zanu pano "
            f"kuti mupeze ndalama zapanopa ndikupewa kutaya ndalama."
        )
        smallholder_action = (
            "Sell produce immediately to local buyers or ADMARC depots. Holding inventory will incur "
            "storage costs without offsetting price gains."
        )
        cooperative_action = (
            "Liquidate current stock holdings to minimize storage and interest overhead. "
            "Focus capital on lucrative trade corridors."
        )
        institutional_action = (
            f"Delay bulk spot purchases in {dist['name']}; local supply pressure is expected to keep prices softened."
        )
        risk_level = "High (Depreciation Risk)"

    else:
        decision = "MONITOR"
        decision_chichewa = "Dikirani / Yang'anirani"
        badge_class = "badge-monitor"
        color = "#d97706"  # Amber/Yellow
        summary = (
            f"Prices in {dist['name']} are in steady equilibrium (4w: +{change_4w}%, 12w: +{change_12w}%). "
            f"Storage returns (+{net_storage_roi_pct}%) marginally cover costs. Maintain staggered sales."
        )
        simple_summary = (
            "Prices are currently stable. Sell only what you need for household cash, and keep monitoring weekly price updates."
        )
        chichewa_summary = (
            "Mitengo ili bwinobwino panopa. Gulisani zochepa zofunikira pa banja, ndipo pitirizani kuyang'anira malipoti a sabata iliyonse."
        )
        smallholder_action = (
            "Sell in gradual portions to meet immediate household cash needs while maintaining "
            "food security reserves."
        )
        cooperative_action = (
            "Audit warehouse pest status. Track fuel tariffs and border trade movements before committing large volumes."
        )
        institutional_action = (
            "Execute standard scheduled procurements without forward contracting."
        )
        risk_level = "Low"

    return {
        "district": dist,
        "commodity": commodity,
        "current_price": current_price,
        "decision": decision,
        "decision_chichewa": decision_chichewa,
        "badge_class": badge_class,
        "color": color,
        "risk_level": risk_level,
        "metrics": {
            "change_4w_pct": change_4w,
            "change_12w_pct": change_12w,
            "carrying_cost_12w_pct": carrying_cost_12w_pct,
            "net_storage_roi_pct": net_storage_roi_pct,
            "net_profit_per_kg_mwk": net_profit_per_kg,
            "net_profit_per_50kg_bag_mwk": net_profit_per_50kg_bag,
            "net_profit_per_ton_mwk": net_profit_per_ton
        },
        "advisory": {
            "summary": summary,
            "simple_summary": simple_summary,
            "chichewa_summary": chichewa_summary,
            "smallholder": smallholder_action,
            "cooperative": cooperative_action,
            "institutional": institutional_action
        },
        "storage_best_practices": [
            f"Maintain grain moisture below {'13.5%' if commodity != 'Beans' else '12.0%'} using sun drying (Chotsani chinyezi).",
            "Use certified hermetic PICS bags with airtight triple-layer seal (Gwiritsani ntchito zikhwama za PICS).",
            "Place bags on wooden pallets off the floor (Ikani matumba pa matabwa osati pansi).",
            "Inspect storage facility weekly for rodent activity (Yang'anirani makoswe ndi madzi)."
        ]
    }
