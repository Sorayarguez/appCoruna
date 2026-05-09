#!/usr/bin/env python3
"""
Seed script: populates Orion Context Broker with realistic data
for all 15 zones of A Coruña + POIs
"""
import requests, json, random, math
from datetime import datetime, timedelta

ORION = "http://localhost:1026/v2"
HEADERS = {"fiware-service": "urbs", "Content-Type": "application/json"}

ZONES = [
    {"id": "centro",       "name": "Centro/María Pita",  "lat": 43.3713, "lon": -8.3961, "type": "plaza",       "base_traffic": 800, "base_no2": 58, "base_pm25": 22, "base_noise": 72},
    {"id": "ensanche",     "name": "Ensanche",           "lat": 43.3680, "lon": -8.4050, "type": "comercial",   "base_traffic": 650, "base_no2": 52, "base_pm25": 18, "base_noise": 68},
    {"id": "orzan",        "name": "Orzán",              "lat": 43.3745, "lon": -8.4083, "type": "residencial", "base_traffic": 320, "base_no2": 35, "base_pm25": 12, "base_noise": 58},
    {"id": "riazor",       "name": "Riazor",             "lat": 43.3701, "lon": -8.4201, "type": "estadio",     "base_traffic": 410, "base_no2": 38, "base_pm25": 13, "base_noise": 62},
    {"id": "monteAlto",    "name": "Monte Alto",         "lat": 43.3778, "lon": -8.4147, "type": "residencial", "base_traffic": 210, "base_no2": 28, "base_pm25": 9,  "base_noise": 51},
    {"id": "ciudadVieja",  "name": "Ciudad Vieja",       "lat": 43.3730, "lon": -8.3928, "type": "historico",   "base_traffic": 290, "base_no2": 32, "base_pm25": 11, "base_noise": 55},
    {"id": "osCastros",    "name": "Os Castros",         "lat": 43.3580, "lon": -8.4050, "type": "residencial", "base_traffic": 380, "base_no2": 41, "base_pm25": 14, "base_noise": 60},
    {"id": "labanhou",     "name": "Labañou",            "lat": 43.3622, "lon": -8.4183, "type": "residencial", "base_traffic": 290, "base_no2": 36, "base_pm25": 12, "base_noise": 57},
    {"id": "juanFlorez",   "name": "Juan Flórez",        "lat": 43.3660, "lon": -8.4120, "type": "comercial",   "base_traffic": 560, "base_no2": 49, "base_pm25": 17, "base_noise": 66},
    {"id": "agraOrzan",    "name": "Agra do Orzán",      "lat": 43.3750, "lon": -8.4220, "type": "residencial", "base_traffic": 270, "base_no2": 33, "base_pm25": 11, "base_noise": 54},
    {"id": "cuatroCaminos","name": "Cuatro Caminos",     "lat": 43.3608, "lon": -8.4089, "type": "nodo",        "base_traffic": 920, "base_no2": 68, "base_pm25": 26, "base_noise": 75},
    {"id": "elvina",       "name": "Elviña",             "lat": 43.3344, "lon": -8.4094, "type": "campus",      "base_traffic": 340, "base_no2": 30, "base_pm25": 10, "base_noise": 52},
    {"id": "mesoiro",      "name": "Mesoiro",            "lat": 43.3289, "lon": -8.4247, "type": "periferico",  "base_traffic": 180, "base_no2": 24, "base_pm25": 8,  "base_noise": 47},
    {"id": "asXubias",     "name": "As Xubias",          "lat": 43.3531, "lon": -8.3842, "type": "industrial",  "base_traffic": 490, "base_no2": 62, "base_pm25": 28, "base_noise": 70},
    {"id": "matogrande",   "name": "Matogrande",         "lat": 43.3469, "lon": -8.4283, "type": "residencial", "base_traffic": 220, "base_no2": 26, "base_pm25": 9,  "base_noise": 49},
]

def rnd(base, pct=0.2):
    """Add ±pct% noise to a base value"""
    return round(base * (1 + random.uniform(-pct, pct)), 2)

def delete_entity(eid):
    requests.delete(f"{ORION}/entities/{eid}", headers=HEADERS)

def upsert_entity(data):
    eid = data["id"]
    r = requests.post(f"{ORION}/entities", json=data, headers=HEADERS)
    if r.status_code == 422:
        # Already exists → update
        attrs = {k: v for k, v in data.items() if k not in ("id", "type")}
        requests.patch(f"{ORION}/entities/{eid}/attrs", json=attrs, headers=HEADERS)
    return r.status_code

def seed_zone(z):
    zid = z["id"]
    ts = datetime.utcnow().isoformat() + "Z"

    flow_id = f"urn:ngsi-ld:TrafficFlowObserved:{zid}"
    impact_id = f"urn:ngsi-ld:TrafficEnvironmentImpact:{zid}"
    aq_id = f"urn:ngsi-ld:AirQualityObserved:{zid}"
    noise_id = f"urn:ngsi-ld:NoiseLevelObserved:{zid}"
    item_id = f"urn:ngsi-ld:ItemFlowObserved:{zid}"

    traffic = rnd(z["base_traffic"])
    speed = round(max(10, 50 - traffic / 30 + random.uniform(-5, 5)), 1)
    occupancy = round(min(95, traffic / 12 + random.uniform(-5, 5)), 1)
    no2 = rnd(z["base_no2"])
    pm25 = rnd(z["base_pm25"])
    pm10 = round(pm25 * random.uniform(1.5, 2.2), 2)
    co2 = round(no2 * random.uniform(3.5, 5.0), 2)
    noise = rnd(z["base_noise"])
    aqi = round(no2 * 2.1 + pm25 * 1.5, 1)

    green_score = round(max(0, min(100,
        100 - (no2 * 0.4 + pm25 * 0.3 + noise * 0.1 + (traffic/10) * 0.2)
    )), 1)

    # TrafficFlowObserved
    upsert_entity({
        "id": flow_id, "type": "TrafficFlowObserved",
        "name": {"type": "Text", "value": z["name"]},
        "location": {"type": "geo:json", "value": {"type": "Point", "coordinates": [z["lon"], z["lat"]]}},
        "intensity": {"type": "Number", "value": traffic},
        "averageVehicleSpeed": {"type": "Number", "value": speed},
        "occupancy": {"type": "Number", "value": occupancy},
        "laneDirection": {"type": "Text", "value": "forward"},
        "vehicleType": {"type": "Text", "value": "car"},
        "TimeInstant": {"type": "DateTime", "value": ts},
    })

    # TrafficEnvironmentImpact
    upsert_entity({
        "id": impact_id, "type": "TrafficEnvironmentImpact",
        "name": {"type": "Text", "value": z["name"]},
        "location": {"type": "geo:json", "value": {"type": "Point", "coordinates": [z["lon"], z["lat"]]}},
        "NO2Concentration": {"type": "Number", "value": no2},
        "PM25Concentration": {"type": "Number", "value": pm25},
        "PM10Concentration": {"type": "Number", "value": pm10},
        "CO2Concentration": {"type": "Number", "value": co2},
        "noiseLevel": {"type": "Number", "value": noise},
        "aqi": {"type": "Number", "value": aqi},
        "greenScore": {"type": "Number", "value": green_score},
        "refTrafficFlowObserved": {"type": "Relationship", "value": flow_id},
        "TimeInstant": {"type": "DateTime", "value": ts},
    })

    # AirQualityObserved
    upsert_entity({
        "id": aq_id, "type": "AirQualityObserved",
        "name": {"type": "Text", "value": z["name"]},
        "location": {"type": "geo:json", "value": {"type": "Point", "coordinates": [z["lon"], z["lat"]]}},
        "NO2": {"type": "Number", "value": no2},
        "PM2.5": {"type": "Number", "value": pm25},
        "PM10": {"type": "Number", "value": pm10},
        "CO2": {"type": "Number", "value": co2},
        "airQualityIndex": {"type": "Number", "value": aqi},
        "airQualityLevel": {"type": "Text", "value": "unhealthy" if aqi > 150 else "moderate" if aqi > 100 else "good"},
        "TimeInstant": {"type": "DateTime", "value": ts},
    })

    # NoiseLevelObserved
    upsert_entity({
        "id": noise_id, "type": "NoiseLevelObserved",
        "name": {"type": "Text", "value": z["name"]},
        "location": {"type": "geo:json", "value": {"type": "Point", "coordinates": [z["lon"], z["lat"]]}},
        "LAeq": {"type": "Number", "value": noise},
        "LAmax": {"type": "Number", "value": round(noise + random.uniform(3, 8), 1)},
        "LAmin": {"type": "Number", "value": round(noise - random.uniform(5, 10), 1)},
        "TimeInstant": {"type": "DateTime", "value": ts},
    })

    # ItemFlowObserved (pedestrians)
    pedestrians = int(traffic * random.uniform(0.3, 0.8))
    cyclists = int(traffic * random.uniform(0.05, 0.15))
    upsert_entity({
        "id": item_id, "type": "ItemFlowObserved",
        "name": {"type": "Text", "value": z["name"]},
        "location": {"type": "geo:json", "value": {"type": "Point", "coordinates": [z["lon"], z["lat"]]}},
        "intensity": {"type": "Number", "value": pedestrians},
        "itemType": {"type": "Text", "value": "Pedestrian"},
        "cyclistCount": {"type": "Number", "value": cyclists},
        "refRoadSegment": {"type": "Relationship", "value": flow_id},
        "TimeInstant": {"type": "DateTime", "value": ts},
    })

    # Forecasts for next 6 hours
    for h in range(1, 7):
        fc_id = f"urn:ngsi-ld:TrafficEnvironmentImpactForecast:{zid}-{h}h"
        valid_from = datetime.utcnow() + timedelta(hours=h-1)
        valid_to = datetime.utcnow() + timedelta(hours=h)
        # Morning peak 7-9, evening peak 17-20
        hour_now = datetime.utcnow().hour + h
        peak_factor = 1.3 if (7 <= (hour_now % 24) <= 9 or 17 <= (hour_now % 24) <= 20) else 0.8
        fc_no2 = round(no2 * peak_factor * random.uniform(0.9, 1.1), 2)
        upsert_entity({
            "id": fc_id, "type": "TrafficEnvironmentImpactForecast",
            "name": {"type": "Text", "value": z["name"]},
            "forecastHour": {"type": "Number", "value": h},
            "NO2Concentration": {"type": "Number", "value": fc_no2},
            "PM25Concentration": {"type": "Number", "value": round(pm25 * peak_factor * random.uniform(0.9, 1.1), 2)},
            "airQualityIndex": {"type": "Number", "value": round(aqi * peak_factor, 1)},
            "trafficIntensity": {"type": "Number", "value": int(traffic * peak_factor)},
            "validFrom": {"type": "DateTime", "value": valid_from.isoformat() + "Z"},
            "validTo": {"type": "DateTime", "value": valid_to.isoformat() + "Z"},
            "refTrafficFlowObserved": {"type": "Relationship", "value": flow_id},
        })

    print(f"  ✓ {z['name']} — NO2:{no2} PM2.5:{pm25} Noise:{noise} Traffic:{traffic} GS:{green_score}")

if __name__ == "__main__":
    print("🌊 Seeding A Coruña FIWARE data...")
    for z in ZONES:
        try:
            seed_zone(z)
        except Exception as e:
            print(f"  ✗ Error in {z['name']}: {e}")
    print(f"\n✅ Done. {len(ZONES)} zones seeded with TrafficFlow, EnvImpact, AirQuality, NoiseLevelObserved + Forecasts.")
