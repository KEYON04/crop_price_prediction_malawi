"""
Market Recommendation and Inter-District Arbitrage Engine.
Identifies optimal sourcing (buy) and destination (sell) markets across all 28 districts
of Malawi for Maize, Rice, and Beans to maximize trade profit after road freight logistics.
"""

from .district_data import DISTRICTS, DISTRICT_LOOKUP, calculate_road_distance, calculate_freight_tariff
from .prediction_engine import get_current_district_price


def calculate_trade_corridor(origin_id, dest_id, commodity, custom_origin_price=None, cargo_tonnage=5.0):
    """
    Calculates the financial feasibility of buying a commodity in origin_id
    and selling in dest_id for a given cargo volume (metric tons).
    """
    orig = DISTRICT_LOOKUP.get(origin_id.lower())
    dest = DISTRICT_LOOKUP.get(dest_id.lower())

    if not orig or not dest:
        return None

    orig_p = custom_origin_price if custom_origin_price and custom_origin_price > 0 else get_current_district_price(orig["id"], commodity)
    dest_p = get_current_district_price(dest["id"], commodity)

    distance_km = calculate_road_distance(orig["id"], dest["id"])
    freight_per_kg = calculate_freight_tariff(distance_km)

    gross_spread_mwk = round(dest_p - orig_p, 2)
    gross_spread_pct = round((gross_spread_mwk / orig_p) * 100.0, 1) if orig_p > 0 else 0.0

    net_margin_per_kg = round(gross_spread_mwk - freight_per_kg, 2)
    total_cost_per_kg = orig_p + freight_per_kg
    net_roi_pct = round((net_margin_per_kg / total_cost_per_kg) * 100.0, 1) if total_cost_per_kg > 0 else 0.0

    # Cargo volume financials
    cargo_kg = cargo_tonnage * 1000.0
    purchase_outlay_mwk = round(orig_p * cargo_kg, 0)
    freight_outlay_mwk = round(freight_per_kg * cargo_kg, 0)
    total_investment_mwk = purchase_outlay_mwk + freight_outlay_mwk
    gross_revenue_mwk = round(dest_p * cargo_kg, 0)
    net_profit_mwk = round(gross_revenue_mwk - total_investment_mwk, 0)

    # Viability status
    if net_margin_per_kg >= 100 and net_roi_pct >= 12.0:
        status = "TRADE OPPORTUNITY"
        badge_class = "badge-opportunity"
        color = "#16a34a"  # Green
        summary = (
            f"High-profit trade corridor! Sourcing in {orig['name']} ({orig_p:,.0f} MWK/kg) and "
            f"selling in {dest['name']} ({dest_p:,.0f} MWK/kg) yields +{net_margin_per_kg:,.0f} MWK/kg "
            f"net margin (+{net_roi_pct}% ROI) after {freight_per_kg:,.0f} MWK/kg freight."
        )
    elif net_margin_per_kg > 0 and net_roi_pct >= 4.0:
        status = "MODERATE MARGIN"
        badge_class = "badge-moderate"
        color = "#2563eb"  # Blue
        summary = (
            f"Viable commercial route. Net margin is +{net_margin_per_kg:,.0f} MWK/kg (+{net_roi_pct}% ROI). "
            f"Ensure backhaul cargo or fuel efficiency to maximize margins."
        )
    elif net_margin_per_kg > 0:
        status = "MARGINAL SPREAD"
        badge_class = "badge-marginal"
        color = "#d97706"  # Amber
        summary = (
            f"Price spread (+{gross_spread_mwk:,.0f} MWK) barely covers freight tariffs ({freight_per_kg:,.0f} MWK). "
            f"Thin net buffer of only +{net_margin_per_kg:,.0f} MWK/kg; sensitive to transit delays."
        )
    else:
        status = "UNPROFITABLE"
        badge_class = "badge-unprofitable"
        color = "#94a3b8"  # Slate Gray
        summary = (
            f"Arbitrage not viable. Freight cost ({freight_per_kg:,.0f} MWK/kg) exceeds the price differential "
            f"({gross_spread_mwk:,.0f} MWK/kg), producing a loss of {net_margin_per_kg:,.0f} MWK/kg."
        )

    return {
        "origin": orig,
        "destination": dest,
        "commodity": commodity,
        "distance_km": distance_km,
        "freight_tariff_mwk_per_kg": freight_per_kg,
        "origin_price_mwk": orig_p,
        "destination_price_mwk": dest_p,
        "gross_spread_mwk": gross_spread_mwk,
        "gross_spread_pct": gross_spread_pct,
        "net_margin_mwk_per_kg": net_margin_per_kg,
        "net_roi_pct": net_roi_pct,
        "status": status,
        "badge_class": badge_class,
        "color": color,
        "summary": summary,
        "cargo_simulation": {
            "tonnage_mt": cargo_tonnage,
            "cargo_kg": cargo_kg,
            "purchase_outlay_mwk": purchase_outlay_mwk,
            "freight_outlay_mwk": freight_outlay_mwk,
            "total_investment_mwk": total_investment_mwk,
            "gross_revenue_mwk": gross_revenue_mwk,
            "net_profit_mwk": net_profit_mwk
        }
    }


def recommend_destinations_for_district(origin_id, commodity, custom_origin_price=None, cargo_tonnage=5.0):
    """
    Ranks all other 27 districts as potential selling destinations for an origin district,
    ordered by highest net profit per kg.
    """
    orig = DISTRICT_LOOKUP.get(origin_id.lower())
    if not orig:
        orig = DISTRICTS[0]

    routes = []
    for dest in DISTRICTS:
        if dest["id"] == orig["id"]:
            continue
        corr = calculate_trade_corridor(
            orig["id"], dest["id"], commodity,
            custom_origin_price=custom_origin_price,
            cargo_tonnage=cargo_tonnage
        )
        if corr:
            routes.append(corr)

    # Sort primarily by net margin (descending), then net ROI
    routes.sort(key=lambda x: x["net_margin_mwk_per_kg"], reverse=True)
    return {
        "origin_district": orig,
        "commodity": commodity,
        "total_destinations_evaluated": len(routes),
        "viable_opportunities_count": len([r for r in routes if r["status"] in ["TRADE OPPORTUNITY", "MODERATE MARGIN"]]),
        "ranked_routes": routes
    }


def get_top_national_arbitrage(commodity, limit=10, cargo_tonnage=5.0):
    """
    Scans all 28 x 27 = 756 district pairs across Malawi to find the absolute
    most lucrative trade opportunities nationwide.
    """
    all_corridors = []
    
    # Efficient pairwise scan
    for orig in DISTRICTS:
        for dest in DISTRICTS:
            if orig["id"] == dest["id"]:
                continue
            corr = calculate_trade_corridor(orig["id"], dest["id"], commodity, cargo_tonnage=cargo_tonnage)
            if corr and corr["net_margin_mwk_per_kg"] > 0:
                all_corridors.append(corr)

    # Sort descending by net margin
    all_corridors.sort(key=lambda x: x["net_margin_mwk_per_kg"], reverse=True)
    
    return {
        "commodity": commodity,
        "cargo_tonnage": cargo_tonnage,
        "total_routes_analyzed": len(DISTRICTS) * (len(DISTRICTS) - 1),
        "top_routes": all_corridors[:limit]
    }

