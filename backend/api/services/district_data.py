"""
Malawi District Registry, Geographic Metadata, and Road Logistics Matrix.
Covers all 28 districts across Northern, Central, and Southern regions.
"""

DISTRICTS = [
    # Northern Region (6 districts)
    {
        "id": "chitipa",
        "name": "Chitipa",
        "region": "Northern Region",
        "market_center": "Chitipa Boma Market",
        "market_type": "Border Transit Depot",
        "lat": -9.7022,
        "lon": 33.2699,
        "base_factor": {
            "Maize": 0.96,     # Proximity to Zambian/Tanzanian border cross-flows
            "Rice": 0.95,      # Lake corridor inflows
            "Beans": 0.92      # Major bean surplus producing highland
        }
    },
    {
        "id": "karonga",
        "name": "Karonga",
        "region": "Northern Region",
        "market_center": "Karonga Main Market",
        "market_type": "Lakeshore & Border Transit Hub",
        "lat": -9.9333,
        "lon": 33.9333,
        "base_factor": {
            "Maize": 0.98,
            "Rice": 0.88,      # Prime Kilombero & Faya rice irrigation production hub (Songwe / Hara)
            "Beans": 0.95
        }
    },
    {
        "id": "likoma",
        "name": "Likoma",
        "region": "Northern Region",
        "market_center": "Likoma Island Port Market",
        "market_type": "Island Deficit Market",
        "lat": -12.0667,
        "lon": 34.7333,
        "base_factor": {
            "Maize": 1.25,     # High waterborne freight costs via Ilala ferry
            "Rice": 1.15,
            "Beans": 1.22
        }
    },
    {
        "id": "mzimba",
        "name": "Mzimba",
        "region": "Northern Region",
        "market_center": "Mzimba Boma / Jenda Market",
        "market_type": "Agricultural Production Basin",
        "lat": -11.9000,
        "lon": 33.6000,
        "base_factor": {
            "Maize": 0.94,     # Massive grain surplus production
            "Rice": 1.02,
            "Beans": 0.93
        }
    },
    {
        "id": "mzuzu",
        "name": "Mzuzu",
        "region": "Northern Region",
        "market_center": "Mzuzu Central / Taifa Market",
        "market_type": "Northern Commercial Capital & Trade Hub",
        "lat": -11.4656,
        "lon": 34.0207,
        "base_factor": {
            "Maize": 1.05,     # Urban consumer demand center, premium market
            "Rice": 0.98,      # Proximity to Karonga/Nkhata Bay rice
            "Beans": 1.04      # High urban bean consumption
        }
    },
    {
        "id": "nkhata_bay",
        "name": "Nkhata Bay",
        "region": "Northern Region",
        "market_center": "Nkhata Bay Port Market",
        "market_type": "Lakeshore Depot",
        "lat": -11.6066,
        "lon": 34.2907,
        "base_factor": {
            "Maize": 1.04,     # Cassava primary staple, grains imported
            "Rice": 0.92,      # Lakeshore rice production
            "Beans": 1.03
        }
    },
    {
        "id": "rumphi",
        "name": "Rumphi",
        "region": "Northern Region",
        "market_center": "Rumphi Boma Market",
        "market_type": "Valley Agricultural Center",
        "lat": -11.0186,
        "lon": 33.8575,
        "base_factor": {
            "Maize": 0.95,
            "Rice": 0.94,
            "Beans": 0.91      # High altitude bean cultivation
        }
    },

    # Central Region (9 districts)
    {
        "id": "dedza",
        "name": "Dedza",
        "region": "Central Region",
        "market_center": "Dedza Boma / Lizulu Border Market",
        "market_type": "Highland Breadbasket & Border Trade",
        "lat": -14.3781,
        "lon": 34.3331,
        "base_factor": {
            "Maize": 0.93,
            "Rice": 1.04,
            "Beans": 0.90      # Renowned national bean production center
        }
    },
    {
        "id": "dowa",
        "name": "Dowa",
        "region": "Central Region",
        "market_center": "Dowa Boma / Mponela Market",
        "market_type": "Agricultural Surplus Breadbasket",
        "lat": -13.6539,
        "lon": 33.9378,
        "base_factor": {
            "Maize": 0.92,     # Mponela is a premier trading depot for maize
            "Rice": 1.03,
            "Beans": 0.94
        }
    },
    {
        "id": "kasungu",
        "name": "Kasungu",
        "region": "Central Region",
        "market_center": "Kasungu Main Market",
        "market_type": "Commercial Agricultural Breadbasket",
        "lat": -13.0333,
        "lon": 33.4833,
        "base_factor": {
            "Maize": 0.91,     # Malawi's largest commercial maize estate & smallholder surplus
            "Rice": 1.05,
            "Beans": 0.95
        }
    },
    {
        "id": "lilongwe",
        "name": "Lilongwe",
        "region": "Central Region",
        "market_center": "Mitundu / Tsoka / Area 3 Market",
        "market_type": "National Capital & Central Consumption Hub",
        "lat": -13.9833,
        "lon": 33.7833,
        "base_factor": {
            "Maize": 1.04,     # High urban demand
            "Rice": 1.02,
            "Beans": 1.05
        }
    },
    {
        "id": "mchinji",
        "name": "Mchinji",
        "region": "Central Region",
        "market_center": "Mchinji Boma / Kamwendo Market",
        "market_type": "Cross-Border Transit Breadbasket",
        "lat": -13.8000,
        "lon": 32.8800,
        "base_factor": {
            "Maize": 0.92,     # High surplus and trade with Zambia (Chipata corridor)
            "Rice": 1.06,
            "Beans": 0.93
        }
    },
    {
        "id": "nkhotakota",
        "name": "Nkhotakota",
        "region": "Central Region",
        "market_center": "Nkhotakota Boma Market",
        "market_type": "Lakeshore Rice & Grain Exchange",
        "lat": -12.9167,
        "lon": 34.2833,
        "base_factor": {
            "Maize": 1.02,
            "Rice": 0.89,      # Major rice irrigation schemes (Bua, Dwangwa)
            "Beans": 1.04
        }
    },
    {
        "id": "ntcheu",
        "name": "Ntcheu",
        "region": "Central Region",
        "market_center": "Ntcheu Boma / Lizulu Market",
        "market_type": "Corridor Transit & Vegetable Hub",
        "lat": -14.8203,
        "lon": 34.6358,
        "base_factor": {
            "Maize": 0.95,     # Link between Central and Southern regions on M1
            "Rice": 1.03,
            "Beans": 0.92
        }
    },
    {
        "id": "ntchisi",
        "name": "Ntchisi",
        "region": "Central Region",
        "market_center": "Ntchisi Boma Market",
        "market_type": "Highland Agricultural Depot",
        "lat": -13.3667,
        "lon": 33.9167,
        "base_factor": {
            "Maize": 0.93,
            "Rice": 1.07,
            "Beans": 0.92
        }
    },
    {
        "id": "salima",
        "name": "Salima",
        "region": "Central Region",
        "market_center": "Salima Boma / Chipoka Port Market",
        "market_type": "Lakeshore Transport & Rice Basin",
        "lat": -13.7804,
        "lon": 34.4587,
        "base_factor": {
            "Maize": 0.99,
            "Rice": 0.91,      # Salima ADD rice basin (Lifuwu schemes)
            "Beans": 1.02
        }
    },

    # Southern Region (13 districts)
    {
        "id": "balaka",
        "name": "Balaka",
        "region": "Southern Region",
        "market_center": "Balaka Central Market",
        "market_type": "Railway & Road Junction Depot",
        "lat": -14.9794,
        "lon": 34.9558,
        "base_factor": {
            "Maize": 1.02,     # Semi-arid corridor, high demand
            "Rice": 1.01,
            "Beans": 1.02
        }
    },
    {
        "id": "blantyre",
        "name": "Blantyre",
        "region": "Southern Region",
        "market_center": "Blantyre Limbe / Mbayani Market",
        "market_type": "Commercial Capital & Premium Deficit Hub",
        "lat": -15.7861,
        "lon": 35.0058,
        "base_factor": {
            "Maize": 1.14,     # Southern premium consumer market
            "Rice": 1.08,      # High disposable income retail demand
            "Beans": 1.12      # Highest retail bean demand in Malawi
        }
    },
    {
        "id": "chikwawa",
        "name": "Chikwawa",
        "region": "Southern Region",
        "market_center": "Chikwawa Boma Market",
        "market_type": "Lower Shire Valley Agro-Ecosystem",
        "lat": -16.0333,
        "lon": 34.8000,
        "base_factor": {
            "Maize": 1.08,     # Drought prone, early harvest, structural grain deficit
            "Rice": 1.02,
            "Beans": 1.06
        }
    },
    {
        "id": "chiradzulu",
        "name": "Chiradzulu",
        "region": "Southern Region",
        "market_center": "Chiradzulu Boma Market",
        "market_type": "Peri-Urban Agricultural Basin",
        "lat": -15.7000,
        "lon": 35.1833,
        "base_factor": {
            "Maize": 1.06,
            "Rice": 1.04,
            "Beans": 1.07
        }
    },
    {
        "id": "machinga",
        "name": "Machinga",
        "region": "Southern Region",
        "market_center": "Liwonde Transit Market",
        "market_type": "Shire River Transit Crossroads",
        "lat": -15.1685,
        "lon": 35.3000,
        "base_factor": {
            "Maize": 1.04,
            "Rice": 0.94,      # Proximity to Lake Chilwa rice schemes
            "Beans": 1.05
        }
    },
    {
        "id": "mangochi",
        "name": "Mangochi",
        "region": "Southern Region",
        "market_center": "Mangochi Boma / Monkey Bay Market",
        "market_type": "Lake Basin & High Tourism Demand",
        "lat": -14.4781,
        "lon": 35.2645,
        "base_factor": {
            "Maize": 1.07,
            "Rice": 0.93,      # Lake Malombe & southern lake rice cultivation
            "Beans": 1.08
        }
    },
    {
        "id": "mulanje",
        "name": "Mulanje",
        "region": "Southern Region",
        "market_center": "Mulanje Boma / Limbuli Border Market",
        "market_type": "High Rainfall Tea Belt & Border Depot",
        "lat": -16.0319,
        "lon": 35.5000,
        "base_factor": {
            "Maize": 1.09,     # Land pressure due to tea estates, food imported
            "Rice": 1.05,
            "Beans": 1.06
        }
    },
    {
        "id": "mwanza",
        "name": "Mwanza",
        "region": "Southern Region",
        "market_center": "Mwanza Border Market",
        "market_type": "International Transit Port (Mozambique)",
        "lat": -15.6000,
        "lon": 34.5167,
        "base_factor": {
            "Maize": 1.05,
            "Rice": 1.06,
            "Beans": 1.04
        }
    },
    {
        "id": "neno",
        "name": "Neno",
        "region": "Southern Region",
        "market_center": "Neno Boma Market",
        "market_type": "Highland Agricultural Depot",
        "lat": -15.4000,
        "lon": 34.6500,
        "base_factor": {
            "Maize": 1.03,
            "Rice": 1.07,
            "Beans": 1.01
        }
    },
    {
        "id": "nsanje",
        "name": "Nsanje",
        "region": "Southern Region",
        "market_center": "Nsanje Boma Market",
        "market_type": "Extreme Southern Deficit & Border Depot",
        "lat": -16.9167,
        "lon": 35.2667,
        "base_factor": {
            "Maize": 1.15,     # High transport cost from Central surplus areas
            "Rice": 1.06,
            "Beans": 1.10
        }
    },
    {
        "id": "phalombe",
        "name": "Phalombe",
        "region": "Southern Region",
        "market_center": "Phalombe Boma Market",
        "market_type": "Lake Chilwa Basin Agricultural Center",
        "lat": -15.8064,
        "lon": 35.6507,
        "base_factor": {
            "Maize": 1.07,
            "Rice": 0.92,      # Major rice producing plain
            "Beans": 1.05
        }
    },
    {
        "id": "thyolo",
        "name": "Thyolo",
        "region": "Southern Region",
        "market_center": "Thyolo Boma / Luchenza Market",
        "market_type": "Tea Estate & High Population Density Hub",
        "lat": -16.0678,
        "lon": 35.1406,
        "base_factor": {
            "Maize": 1.08,     # Land scarcity, high reliance on purchased staples
            "Rice": 1.05,
            "Beans": 1.07
        }
    },
    {
        "id": "zomba",
        "name": "Zomba",
        "region": "Southern Region",
        "market_center": "Zomba Central / Chinamwali Market",
        "market_type": "Historic University City & Trade Basin",
        "lat": -15.3833,
        "lon": 35.3333,
        "base_factor": {
            "Maize": 1.06,     # High urban and student population demand
            "Rice": 0.95,      # Close proximity to Lake Chilwa rice schemes
            "Beans": 1.08
        }
    }
]

# Quick lookup dictionary by ID or Name
DISTRICT_LOOKUP = {d["id"]: d for d in DISTRICTS}
for d in DISTRICTS:
    DISTRICT_LOOKUP[d["name"].lower()] = d


def calculate_road_distance(dist_a_id, dist_b_id):
    """
    Computes accurate road transit distance (km) between any two Malawi districts.
    Combines geodesic haversine distance with Malawi road network winding factor (1.35x).
    """
    import math

    if dist_a_id == dist_b_id:
        return 0

    da = DISTRICT_LOOKUP.get(dist_a_id.lower())
    db = DISTRICT_LOOKUP.get(dist_b_id.lower())

    if not da or not db:
        return 250  # Default average distance

    # Haversine formula
    lat1, lon1 = math.radians(da["lat"]), math.radians(da["lon"])
    lat2, lon2 = math.radians(db["lat"]), math.radians(db["lon"])

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
    c = 2 * math.asin(math.sqrt(a))
    radius_earth_km = 6371.0
    haversine_km = radius_earth_km * c

    # Road tortuosity multiplier across Malawi's rift valley and highway corridor
    road_km = haversine_km * 1.34 + 15.0  # +15 km local feeder access
    return round(road_km, 1)


def calculate_freight_tariff(distance_km):
    """
    Calculates realistic freight cost per kg (MWK/kg) along Malawi transport corridors.
    Includes base handling/loading fee + distance tariff based on current diesel fuel price.
    """
    if distance_km <= 0:
        return 0.0

    # Base handling, loading & unloading fee per kg
    base_handling_mwk = 35.0

    # Road transit tariff per km per kg (~0.28 MWK / km / kg on M1 paved corridor)
    per_km_rate = 0.28

    tariff = base_handling_mwk + (distance_km * per_km_rate)
    return round(tariff, 2)

