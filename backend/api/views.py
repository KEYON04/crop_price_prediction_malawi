import json
from django.shortcuts import render
from django.http import JsonResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .services.district_data import DISTRICTS, DISTRICT_LOOKUP
from .services.prediction_engine import generate_price_forecast, get_current_district_price
from .services.decision_engine import evaluate_decision
from .services.arbitrage_engine import (
    calculate_trade_corridor,
    recommend_destinations_for_district,
    get_top_national_arbitrage
)

from .models import MarketSubscriber

COMMODITIES = [
    {
        "id": "Maize",
        "name": "Maize",
        "chichewa_name": "Chimanga",
        "unit": "kg",
        "default_bag_kg": 50,
        "image": "/static/images/maize.jpg",
        "description": "Primary national staple grain. High seasonal price volatility driven by lean season supply exhaustion.",
        "storage_standard": "Hermetic PICS bags with moisture <= 13.5%"
    },
    {
        "id": "Rice",
        "name": "Rice",
        "chichewa_name": "Mpunga",
        "unit": "kg",
        "default_bag_kg": 50,
        "image": "/static/images/rice.jpg",
        "description": "High-value premium cash staple (Kilombero, Faya). High consumer demand in urban centers.",
        "storage_standard": "PICS bags / clean jute bags in elevated pallets"
    },
    {
        "id": "Beans",
        "name": "Beans",
        "chichewa_name": "Nyemba",
        "unit": "kg",
        "default_bag_kg": 50,
        "image": "/static/images/beans.jpg",
        "description": "Essential protein pulse crop (Sugar beans, Nanyati). Prone to bruchid weevil infestation without hermetic storage.",
        "storage_standard": "Strict airtight hermetic sealing (PICS) with moisture <= 12.0%"
    }
]


def dashboard_view(request):
    """
    Renders the professional executive web dashboard interface.
    """
    context = {
        "districts": DISTRICTS,
        "commodities": COMMODITIES,
    }
    return render(request, "index.html", context)


@api_view(["GET"])
def api_districts(request):
    """
    Returns list of all 28 districts across Malawi with geographic and market metadata.
    """
    grouped = {
        "Northern Region": [d for d in DISTRICTS if d["region"] == "Northern Region"],
        "Central Region": [d for d in DISTRICTS if d["region"] == "Central Region"],
        "Southern Region": [d for d in DISTRICTS if d["region"] == "Southern Region"],
    }
    return Response({
        "total_districts": len(DISTRICTS),
        "districts": DISTRICTS,
        "by_region": grouped
    })


@api_view(["GET"])
def api_commodities(request):
    """
    Returns the supported commodities (Maize, Rice, Beans).
    """
    return Response({
        "commodities": COMMODITIES
    })


@api_view(["GET"])
def api_predictions(request):
    """
    Returns weekly (1-4w) and monthly (1-6m) price forecasts with 80% and 95% confidence cones.
    Query params:
      - district (default: 'lilongwe')
      - commodity (default: 'Maize')
      - custom_spot_price (optional float)
    """
    district_id = request.GET.get("district", "lilongwe")
    commodity = request.GET.get("commodity", "Maize")
    custom_spot = request.GET.get("custom_spot_price")
    
    try:
        custom_spot = float(custom_spot) if custom_spot else None
    except ValueError:
        custom_spot = None

    if commodity not in ["Maize", "Rice", "Beans"]:
        commodity = "Maize"

    forecast = generate_price_forecast(district_id, commodity, custom_spot_price=custom_spot)
    return Response(forecast)


@api_view(["GET"])
def api_decisions(request):
    """
    Returns strategic market decision (HOLD & STORE vs SELL NOW vs MONITOR),
    storage carrying economics, risk levels, and smallholder/coop advisories.
    """
    district_id = request.GET.get("district", "lilongwe")
    commodity = request.GET.get("commodity", "Maize")
    custom_spot = request.GET.get("custom_spot_price")

    try:
        custom_spot = float(custom_spot) if custom_spot else None
    except ValueError:
        custom_spot = None

    if commodity not in ["Maize", "Rice", "Beans"]:
        commodity = "Maize"

    decision_data = evaluate_decision(district_id, commodity, custom_spot_price=custom_spot)
    return Response(decision_data)


@api_view(["GET"])
def api_arbitrage(request):
    """
    Calculates inter-district trade corridors from a given origin district,
    ranking destination selling markets by net margin and ROI after road freight.
    Query params:
      - origin (default: 'kasungu')
      - commodity (default: 'Maize')
      - tonnage (default: 5.0 MT)
    """
    origin_id = request.GET.get("origin", "kasungu")
    commodity = request.GET.get("commodity", "Maize")
    tonnage_str = request.GET.get("tonnage", "5.0")
    custom_spot = request.GET.get("custom_origin_price")

    try:
        tonnage = float(tonnage_str)
    except ValueError:
        tonnage = 5.0

    try:
        custom_spot = float(custom_spot) if custom_spot else None
    except ValueError:
        custom_spot = None

    if commodity not in ["Maize", "Rice", "Beans"]:
        commodity = "Maize"

    recommendations = recommend_destinations_for_district(
        origin_id, commodity, custom_origin_price=custom_spot, cargo_tonnage=tonnage
    )
    return Response(recommendations)


@api_view(["GET"])
def api_top_arbitrage(request):
    """
    Scans all 756 district pairs across Malawi to surface the top 10 most profitable
    inter-district trade opportunities nationwide.
    """
    commodity = request.GET.get("commodity", "Maize")
    limit_str = request.GET.get("limit", "10")
    tonnage_str = request.GET.get("tonnage", "5.0")

    try:
        limit = int(limit_str)
    except ValueError:
        limit = 10

    try:
        tonnage = float(tonnage_str)
    except ValueError:
        tonnage = 5.0

    if commodity not in ["Maize", "Rice", "Beans"]:
        commodity = "Maize"

    top_corridors = get_top_national_arbitrage(commodity, limit=limit, cargo_tonnage=tonnage)
    return Response(top_corridors)


@api_view(["POST"])
def api_auth_signup(request):
    """
    Subscribes a user to AgriPrice Malawi market intelligence email bulletins.
    """
    data = request.data
    email = data.get("email", "").strip().lower()
    full_name = data.get("full_name", "").strip()
    district = data.get("district", "Lilongwe").strip()
    report_frequency = data.get("report_frequency", "weekly")
    organization_type = data.get("organization_type", "farmer")
    phone = data.get("phone", "").strip()

    if not email or "@" not in email:
        return Response({"error": "A valid email address is required (Imelo yovomerezeka ikufunika)."}, status=400)

    if not full_name:
        full_name = email.split("@")[0].title()

    subscriber, created = MarketSubscriber.objects.update_or_create(
        email=email,
        defaults={
            "full_name": full_name,
            "district": district,
            "report_frequency": report_frequency,
            "organization_type": organization_type,
            "phone": phone,
            "is_active": True,
        }
    )

    request.session["subscriber_id"] = subscriber.id
    request.session.modified = True

    return Response({
        "status": "success",
        "created": created,
        "message": f"Welcome {subscriber.full_name}! You are registered to receive {subscriber.get_report_frequency_display()} for {subscriber.district}.",
        "subscriber": {
            "id": subscriber.id,
            "full_name": subscriber.full_name,
            "email": subscriber.email,
            "district": subscriber.district,
            "report_frequency": subscriber.report_frequency,
            "organization_type": subscriber.organization_type,
        }
    })


@api_view(["POST"])
def api_auth_signin(request):
    """
    Signs in a registered subscriber by email.
    """
    email = request.data.get("email", "").strip().lower()
    if not email:
        return Response({"error": "Please provide your email address."}, status=400)

    subscriber = MarketSubscriber.objects.filter(email=email).first()
    if not subscriber:
        # Create a new active profile gracefully
        name = email.split("@")[0].title()
        subscriber = MarketSubscriber.objects.create(
            email=email,
            full_name=name,
            district="Lilongwe",
            report_frequency="weekly",
            organization_type="farmer",
            is_active=True
        )

    request.session["subscriber_id"] = subscriber.id
    request.session.modified = True

    return Response({
        "status": "success",
        "message": f"Welcome back, {subscriber.full_name}!",
        "subscriber": {
            "id": subscriber.id,
            "full_name": subscriber.full_name,
            "email": subscriber.email,
            "district": subscriber.district,
            "report_frequency": subscriber.report_frequency,
            "organization_type": subscriber.organization_type,
        }
    })


@api_view(["GET"])
def api_auth_me(request):
    """
    Returns the currently signed-in subscriber profile.
    """
    subscriber_id = request.session.get("subscriber_id")
    if subscriber_id:
        subscriber = MarketSubscriber.objects.filter(id=subscriber_id, is_active=True).first()
        if subscriber:
            return Response({
                "authenticated": True,
                "subscriber": {
                    "id": subscriber.id,
                    "full_name": subscriber.full_name,
                    "email": subscriber.email,
                    "district": subscriber.district,
                    "report_frequency": subscriber.report_frequency,
                    "organization_type": subscriber.organization_type,
                }
            })

    return Response({"authenticated": False, "subscriber": None})


@api_view(["POST"])
def api_auth_signout(request):
    """
    Signs out the current subscriber.
    """
    request.session.flush()
    return Response({"status": "success", "message": "Signed out successfully."})


@api_view(["POST"])
def api_send_market_report(request):
    """
    Dispatches / simulates instant market intelligence bulletin to subscriber email.
    """
    email = request.data.get("email", "").strip().lower()
    district = request.data.get("district", "Lilongwe")
    commodity = request.data.get("commodity", "Maize")

    subscriber = MarketSubscriber.objects.filter(email=email).first() if email else None
    name = subscriber.full_name if subscriber else "Valued Stakeholder"
    target_email = email or (subscriber.email if subscriber else "user@example.com")

    return Response({
        "status": "success",
        "email": target_email,
        "message": f"Market Bulletin for {commodity} ({district}) successfully queued for delivery to {target_email}.",
        "delivery_details": {
            "recipient": f"{name} <{target_email}>",
            "subject": f"AgriPrice Malawi: Weekly Intelligence & Arbitrage Bulletin - {district}",
            "district": district,
            "commodity": commodity,
            "dispatch_time": "Instant",
            "next_schedule": "Next Monday at 06:00 AM CAT"
        }
    })
