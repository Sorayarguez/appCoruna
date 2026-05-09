#!/usr/bin/env python3
"""
Seed FIWARE Orion Context Broker with realistic synthetic data
for all 15 zones of A Coruña + 8 POI traffic nodes.
"""
import requests
import random
import math
import time
from datetime import datetime, timezone

ORION = "http://orion:1026/v2"
HEADERS = {"fiware-service": "urbs", "Content-Type": "application/json"}

ZONES = [
    {"id": "centro",       "name": "Centro / María Pita", "lat": 43.3713, "lon": -8.3961, "type": "Plaza principal",    "base_traffic": 750, "base_no2": 55, "base_pm25": 28, "base_noise": 68},
    {"id": "ensanche",     "name": "Ensanche",             "lat": 43.3680, "lon": -8.4050, "type": "Comercial",          "base_traffic": 620, "base_no2": 48, "base_pm25": 22, "base_noise": 65},
    {"id": "orzan",        "name": "Orzán",                "lat": 43.3745, "lon": -8.4083, "type": "Residencial/playa",  "base_traffic": 340, "base_no2": 28, "base_pm25": 14, "base_noise": 52},
    {"id": "riazor",       "name": "Riazor",               "lat": 43.3701, "lon": -8.4201, "type": "Estadio/playa",      "base_traffic": 280, "base_no2": 22, "base_pm25": 10, "base_noise": 45},
    {"id": "monteAlto",    "name": "Monte Alto",           "lat": 43.3778, "lon": -8.4147, "type": "Residencial alto",   "base_traffic": 180, "base_no2": 18, "base_pm25": 8,  "base_noise": 42},
    {"id": "ciudadVieja",  "name": "Ciudad Vieja",         "lat": 43.3730, "lon": -8.3928, "type": "Histórico",          "base_traffic": 310, "base_no2": 25, "base_pm25": 12, "base_noise": 50},
    {"id": "osCastros",    "name": "Os Castros",           "lat": 43.3580, "lon": -8.4050, "type": "Residencial",        "base_traffic": 220, "base_no2": 20, "base_pm25": 9,  "base_noise": 46},
    {"id": "labanhou",     "name": "Labañou",              "lat": 43.3622, "lon": -8.4183, "type": "Residencial",        "base_traffic": 290, "base_no2": 24, "base_pm25": 11, "base_noise": 48},
    {"id": "juanFlorez",   "name": "Juan Flórez",          "lat": 43.3660, "lon": -8.4120, "type": "Comercial",          "base_traffic": 510, "base_no2": 42, "base_pm25": 19, "base_noise": 61},
    {"id": "agraOrzan",    "name": "Agra do Orzán",        "lat": 43.3750, "lon": -8.4220, "type": "Residencial",        "base_traffic": 260, "base_no2": 21, "base_pm25": 10, "base_noise": 47},
    {"id": "cuatroCaminos","name": "Cuatro Caminos",       "lat": 43.3608, "lon": -8.4089, "type": "Nodo tráfico",       "base_traffic": 880, "base_no2": 72, "base_pm25": 38, "base_noise": 74},
    {"id": "elvina",       "name": "Elviña",               "lat": 43.3344, "lon": -8.4094, "type": "Universidad/campus", "base_traffic": 350, "base_no2": 29, "base_pm25": 13, "base_noise": 53},
    {"id": "mesoiro",      "name": "Mesoiro",              "lat": 43.3289, "lon": -8.4247, "type": "Periférico",         "base_traffic": 140, "base_no2": 15, "base_pm25": 6,  "base_noise": 38},
    {"id": "asXubias",     "name": "As Xubias",            "lat": 43.3531, "lon": -8.3842, "type": "Industrial/puerto",  "base_traffic": 410, "base_no2": 61, "base_pm25": 35, "base_noise": 70},
    {"id": "matogrande",   "name": "Matogrande",           "lat": 43.3469, "lon": -8.4283, "type": "Residencial nuevo",  "base_traffic": 200, "base_no2": 17, "base_pm25": 7,  "base_noise": 40},
]

POIS = [
    {"id": "torrehercules", "name": "Torre de Hércules", "lat": 43.3857, "lon": -8.4061, "base_traffic": 420},
    {"id": "puerto",        "name": "Puerto de A Coruña", "lat": 43.3687, "lon": -8.3928, "base_traffic": 580},
    {"id": "estacion",      "name": "Estación Tren/Bus",  "lat": 43.3558, "lon": -8.4075, "base_traffic": 660},
    {"id": "chuac",         "name": "Hospital CHUAC",     "lat": 43.3394, "lon": -8.4108, "base_traffic": 390},
    {"id": "aquarium",      "name": "Aquarium Finisterrae","lat": 43.3847, "lon": -8.4117, "base_traffic": 230},
    {"id": "marineda",      "name": "Marineda City",      "lat": 43.3281, "lon": -8.4414, "base_traffic": 740},
    {"id": "aeropuerto",    "name": "Aeropuerto",         "lat": 43.3022, "lon": -8.3786, "base_traffic": 310},
    {"id": "santamargarita","name": "Parque Sta. Margarita","lat": 43.3644, "lon": -8.4156,"base_traffic": 180},
]

def jitter(val, pct=0.15):
    return round(val * (1 + random.uniform(-pct, pct)), 2)

def upsert_entity(entity):
    eid = entity["id"]
    r = requests.post(f"{ORION}/entities", json=entity, headers=HEADERS)
    if r.status_code == 422:  # already exists
        attrs = {k: v for k, v in entity.items() if k not in ("id", "type")}
        requests.patch(f"{ORION}/entities/{eid}/attrs", json=attrs, headers=HEADERS)
    return r.status_code

def seed_zone(z):
    zid = z["id"]
    ts = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    traffic = jitter(z["base_traffic"])
    no2     = jitter(z["base_no2"])
    pm25    = jitter(z["base_pm25"])
    noise   = jitter(z["base_noise"])
    pm10    = round(pm25 * 1.6, 2)
    co2     = round(no2 * 3.8, 2)
    speed   = round(max(5, 60 - traffic / 30), 1)
    aqi     = min(500, round(no2 * 1.5 + pm25 * 2.5))
    pedestrians = jitter(80, 0.5)

    # TrafficFlowObserved
    tfo = {
        "id": f"urn:ngsi-ld:TrafficFlowObserved:{zid}",
        "type": "TrafficFlowObserved",
        "address": {"value": z["name"], "type": "Text"},
        "location": {"value": {"type": "Point", "coordinates": [z["lon"], z["lat"]]}, "type": "geo:json"},
        "intensity": {"value": traffic, "type": "Number"},
        "averageVehicleSpeed": {"value": speed, "type": "Number"},
        "occupancy": {"value": round(min(1.0, traffic / 1200), 3), "type": "Number"},
        "laneId": {"value": 1, "type": "Number"},
        "dateObserved": {"value": ts, "type": "DateTime"},
    }
    upsert_entity(tfo)

    # TrafficEnvironmentImpact
    tei = {
        "id": f"urn:ngsi-ld:TrafficEnvironmentImpact:{zid}",
        "type": "TrafficEnvironmentImpact",
        "address": {"value": z["name"], "type": "Text"},
        "location": {"value": {"type": "Point", "coordinates": [z["lon"], z["lat"]]}, "type": "geo:json"},
        "NO2Concentration": {"value": no2, "type": "Number"},
        "PM25Concentration": {"value": pm25, "type": "Number"},
        "noiseLevel": {"value": noise, "type": "Number"},
        "refTrafficFlowObserved": {"value": f"urn:ngsi-ld:TrafficFlowObserved:{zid}", "type": "Relationship"},
        "dateObserved": {"value": ts, "type": "DateTime"},
    }
    upsert_entity(tei)

    # AirQualityObserved
    aqo = {
        "id": f"urn:ngsi-ld:AirQualityObserved:{zid}",
        "type": "AirQualityObserved",
        "address": {"value": z["name"], "type": "Text"},
        "location": {"value": {"type": "Point", "coordinates": [z["lon"], z["lat"]]}, "type": "geo:json"},
        "NO2": {"value": no2, "type": "Number"},
        "PM2.5": {"value": pm25, "type": "Number"},
        "PM10": {"value": pm10, "type": "Number"},
        "CO2": {"value": co2, "type": "Number"},
        "airQualityIndex": {"value": aqi, "type": "Number"},
        "dateObserved": {"value": ts, "type": "DateTime"},
    }
    upsert_entity(aqo)

    # NoiseLevelObserved
    nlo = {
        "id": f"urn:ngsi-ld:NoiseLevelObserved:{zid}",
        "type": "NoiseLevelObserved",
        "address": {"value": z["name"], "type": "Text"},
        "location": {"value": {"type": "Point", "coordinates": [z["lon"], z["lat"]]}, "type": "geo:json"},
        "loudness": {"value": noise, "type": "Number"},
        "dateObserved": {"value": ts, "type": "DateTime"},
    }
    upsert_entity(nlo)

    # ItemFlowObserved (pedestrians)
    ifo = {
        "id": f"urn:ngsi-ld:ItemFlowObserved:{zid}",
        "type": "ItemFlowObserved",
        "address": {"value": z["name"], "type": "Text"},
        "location": {"value": {"type": "Point", "coordinates": [z["lon"], z["lat"]]}, "type": "geo:json"},
        "intensity": {"value": pedestrians, "type": "Number"},
        "itemType": {"value": "Pedestrian", "type": "Text"},
        "refRoadSegment": {"value": f"urn:ngsi-ld:TrafficFlowObserved:{zid}", "type": "Relationship"},
        "dateObserved": {"value": ts, "type": "DateTime"},
    }
    upsert_entity(ifo)

    # TrafficEnvironmentImpactForecast (next 6h)
    for h in [1, 2, 4, 6]:
        factor = 1 + math.sin(h) * 0.15
        fid = f"urn:ngsi-ld:TrafficEnvironmentImpactForecast:{zid}-h{h}"
        fc = {
            "id": fid,
            "type": "TrafficEnvironmentImpactForecast",
            "address": {"value": z["name"], "type": "Text"},
            "location": {"value": {"type": "Point", "coordinates": [z["lon"], z["lat"]]}, "type": "geo:json"},
            "NO2Concentration": {"value": round(no2 * factor, 2), "type": "Number"},
            "PM25Concentration": {"value": round(pm25 * factor, 2), "type": "Number"},
            "airQualityIndex": {"value": round(aqi * factor), "type": "Number"},
            "hoursAhead": {"value": h, "type": "Number"},
            "refTrafficFlowObserved": {"value": f"urn:ngsi-ld:TrafficFlowObserved:{zid}", "type": "Relationship"},
        }
        upsert_entity(fc)

    print(f"  ✓ {z['name']:30s} NO2={no2:5.1f} PM2.5={pm25:5.1f} Noise={noise:5.1f} Traffic={traffic:5.0f}")

def seed_poi(p):
    ts = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    tfo = {
        "id": f"urn:ngsi-ld:TrafficFlowObserved:{p['id']}",
        "type": "TrafficFlowObserved",
        "address": {"value": p["name"], "type": "Text"},
        "location": {"value": {"type": "Point", "coordinates": [p["lon"], p["lat"]]}, "type": "geo:json"},
        "intensity": {"value": jitter(p["base_traffic"]), "type": "Number"},
        "averageVehicleSpeed": {"value": round(max(10, 50 - p["base_traffic"]/40), 1), "type": "Number"},
        "dateObserved": {"value": ts, "type": "DateTime"},
    }
    upsert_entity(tfo)
    print(f"  ✓ POI: {p['name']}")

if __name__ == "__main__":
    print("\n🔵 Seeding A Coruña zones...")
    for z in ZONES:
        seed_zone(z)

    print("\n🟡 Seeding POI traffic nodes...")
    for p in POIS:
        seed_poi(p)

    print(f"\n✅ Done! {len(ZONES)} zones + {len(POIS)} POIs seeded into Orion.")
