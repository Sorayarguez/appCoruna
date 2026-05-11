from flask import Flask, request, jsonify, send_from_directory
try:
    from flask_cors import CORS
except Exception:
    # Allow running locally even if flask_cors is not installed
    def CORS(app):
        print('Warning: flask_cors not installed; CORS disabled')
from datetime import datetime, timedelta
import os
import requests, math, heapq, random

app = Flask(__name__)
CORS(app)

ORION_URL = "http://orion:1026/v2"
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434/api/generate").strip()
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "phi").strip() or "phi"
ORION_HEADERS = {"fiware-service": "urbs", "Accept": "application/json"}

ZONES_META = [
    {"id": "centro",        "name": "Centro/María Pita",  "lat": 43.3713, "lon": -8.3961},
    {"id": "ensanche",      "name": "Ensanche",           "lat": 43.3680, "lon": -8.4050},
    {"id": "orzan",         "name": "Orzán",              "lat": 43.3745, "lon": -8.4083},
    {"id": "riazor",        "name": "Riazor",             "lat": 43.3701, "lon": -8.4201},
    {"id": "monteAlto",     "name": "Monte Alto",         "lat": 43.3778, "lon": -8.4147},
    {"id": "ciudadVieja",   "name": "Ciudad Vieja",       "lat": 43.3730, "lon": -8.3928},
    {"id": "osCastros",     "name": "Os Castros",         "lat": 43.3580, "lon": -8.4050},
    {"id": "labanhou",      "name": "Labañou",            "lat": 43.3622, "lon": -8.4183},
    {"id": "juanFlorez",    "name": "Juan Flórez",        "lat": 43.3660, "lon": -8.4120},
    {"id": "agraOrzan",     "name": "Agra do Orzán",      "lat": 43.3750, "lon": -8.4220},
    {"id": "cuatroCaminos", "name": "Cuatro Caminos",     "lat": 43.3608, "lon": -8.4089},
    {"id": "elvina",        "name": "Elviña",             "lat": 43.3344, "lon": -8.4094},
    {"id": "mesoiro",       "name": "Mesoiro",            "lat": 43.3289, "lon": -8.4247},
    {"id": "asXubias",      "name": "As Xubias",          "lat": 43.3531, "lon": -8.3842},
    {"id": "matogrande",    "name": "Matogrande",         "lat": 43.3469, "lon": -8.4283},
]

def get_entities(entity_type, limit=100):
    try:
        r = requests.get(f"{ORION_URL}/entities?type={entity_type}&limit={limit}", headers=ORION_HEADERS, timeout=5)
        return r.json() if r.status_code == 200 else []
    except:
        return []

def get_entity(eid):
    try:
        r = requests.get(f"{ORION_URL}/entities/{eid}", headers=ORION_HEADERS, timeout=5)
        return r.json() if r.status_code == 200 else None
    except:
        return None

def val(entity, attr, default=0):
    if not entity: return default
    return entity.get(attr, {}).get("value", default)


def ask_ollama(prompt, timeout=8):
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.7,
            "top_p": 0.9,
        },
    }
    response = requests.post(OLLAMA_URL, json=payload, timeout=timeout)
    response.raise_for_status()
    data = response.json()
    answer = (data.get("response") or "").strip()
    if not answer:
        raise ValueError("Ollama returned an empty response")
    return answer

# ─── Fallback synthetic data when Orion is empty ───────────────────────────────
def synthetic_zone_data():
    base = [
        {"id":"centro","name":"Centro/María Pita","lat":43.3713,"lon":-8.3961,"no2":58,"pm25":22,"pm10":38,"co2":210,"noise":72,"traffic":800},
        {"id":"ensanche","name":"Ensanche","lat":43.3680,"lon":-8.4050,"no2":52,"pm25":18,"pm10":32,"co2":188,"noise":68,"traffic":650},
        {"id":"orzan","name":"Orzán","lat":43.3745,"lon":-8.4083,"no2":35,"pm25":12,"pm10":22,"co2":128,"noise":58,"traffic":320},
        {"id":"riazor","name":"Riazor","lat":43.3701,"lon":-8.4201,"no2":38,"pm25":13,"pm10":24,"co2":138,"noise":62,"traffic":410},
        {"id":"monteAlto","name":"Monte Alto","lat":43.3778,"lon":-8.4147,"no2":28,"pm25":9,"pm10":16,"co2":102,"noise":51,"traffic":210},
        {"id":"ciudadVieja","name":"Ciudad Vieja","lat":43.3730,"lon":-8.3928,"no2":32,"pm25":11,"pm10":20,"co2":118,"noise":55,"traffic":290},
        {"id":"osCastros","name":"Os Castros","lat":43.3580,"lon":-8.4050,"no2":41,"pm25":14,"pm10":26,"co2":150,"noise":60,"traffic":380},
        {"id":"labanhou","name":"Labañou","lat":43.3622,"lon":-8.4183,"no2":36,"pm25":12,"pm10":22,"co2":132,"noise":57,"traffic":290},
        {"id":"juanFlorez","name":"Juan Flórez","lat":43.3660,"lon":-8.4120,"no2":49,"pm25":17,"pm10":30,"co2":178,"noise":66,"traffic":560},
        {"id":"agraOrzan","name":"Agra do Orzán","lat":43.3750,"lon":-8.4220,"no2":33,"pm25":11,"pm10":20,"co2":122,"noise":54,"traffic":270},
        {"id":"cuatroCaminos","name":"Cuatro Caminos","lat":43.3608,"lon":-8.4089,"no2":68,"pm25":26,"pm10":46,"co2":245,"noise":75,"traffic":920},
        {"id":"elvina","name":"Elviña","lat":43.3344,"lon":-8.4094,"no2":30,"pm25":10,"pm10":18,"co2":110,"noise":52,"traffic":340},
        {"id":"mesoiro","name":"Mesoiro","lat":43.3289,"lon":-8.4247,"no2":24,"pm25":8,"pm10":14,"co2":88,"noise":47,"traffic":180},
        {"id":"asXubias","name":"As Xubias","lat":43.3531,"lon":-8.3842,"no2":62,"pm25":28,"pm10":50,"co2":225,"noise":70,"traffic":490},
        {"id":"matogrande","name":"Matogrande","lat":43.3469,"lon":-8.4283,"no2":26,"pm25":9,"pm10":16,"co2":96,"noise":49,"traffic":220},
    ]
    now = datetime.utcnow().isoformat() + "Z"
    result = []
    for z in base:
        noise_f = random.uniform(0.9, 1.1)
        gs = round(max(0, min(100, 100 - (z["no2"]*0.4 + z["pm25"]*0.3 + z["noise"]*0.1 + (z["traffic"]/10)*0.2))), 1)
        result.append({**z,
            "no2": round(z["no2"]*noise_f, 1),
            "pm25": round(z["pm25"]*noise_f, 1),
            "pm10": round(z["pm10"]*noise_f, 1),
            "co2": round(z["co2"]*noise_f, 1),
            "noise": round(z["noise"]*noise_f, 1),
            "traffic": int(z["traffic"]*noise_f),
            "aqi": round(z["no2"]*2.1 + z["pm25"]*1.5, 1),
            "greenScore": gs,
            "timestamp": now,
        })
    return result

def local_fallback_response(msg, mode="ciudadano", lang="es"):
    """Generate contextual fallback responses when Ollama is unavailable."""
    msg_lower = msg.lower()
    
    # Pick a random zone for context
    zone = random.choice(ZONES_META)
    zone_name = zone["name"]
    
    # Heuristic responses by keyword (varied templates)
    templates_ciudadano_es = [
        f"URBS sugiere: Evita hoy el tráfico de {zone_name} (NO₂ elevado). Considera ciclovía a través de Orzán.",
        f"Análisis rápido: La calidad del aire en {zone_name} está moderada. Camina preferiblemente mañana por la mañana.",
        f"Transporte: Usa autobús en las horas de menor tráfico. {zone_name} tiene picos entre 7-9 y 17-20h.",
        f"Eco-consejo: La bicicleta es tu mejor aliada ahora. {zone_name} muestra tráfico moderado a alto.",
        f"URBS recomienda: Sal 30 min antes para evitar hora punta en {zone_name}.",
    ]
    templates_ciudadano_en = [
        f"URBS suggests: Avoid traffic in {zone_name} today (high NO₂). Consider biking through Orzán.",
        f"Quick analysis: Air quality in {zone_name} is moderate. Walk preferably tomorrow morning.",
        f"Transport: Use bus during low-traffic hours. {zone_name} peaks between 7-9am and 5-8pm.",
        f"Eco-tip: Your bike is your best friend now. {zone_name} shows moderate to high traffic.",
        f"URBS recommends: Leave 30 min early to avoid rush hour in {zone_name}.",
    ]
    templates_alcalde_es = [
        f"Política: {zone_name} requiere restricciones vehiculares. Sugerencia ZBE parcial en horas pico.",
        f"ML Insight: Correlación tráfico-contaminación en {zone_name} es crítica. Presupuesto para ciclocarriles recomendado.",
        f"Análisis: Reducciones de tráfico en {zone_name} bajarían NO₂ 12-18%. Horizonte: 2-3 años.",
        f"Prospectiva: {zone_name} superará umbrales AQ en 4h. Alerta de política pública: activar protocolo.",
        f"RSC: Partenariado público-privado en movilidad eléctrica en {zone_name} reduce emisiones 20%.",
    ]
    templates_alcalde_en = [
        f"Policy: {zone_name} requires vehicle restrictions. Partial Low Emission Zone (LEZ) during peak hours.",
        f"ML Insight: Traffic-pollution correlation in {zone_name} is critical. Bike lane budget recommended.",
        f"Analysis: Traffic reduction in {zone_name} would lower NO₂ by 12-18%. Timeline: 2-3 years.",
        f"Forecast: {zone_name} will exceed AQ thresholds in 4h. Public alert: activate protocol.",
        f"CSR: Public-private partnership in e-mobility in {zone_name} reduces emissions by 20%.",
    ]
    
    if mode == "alcalde":
        templates = templates_alcalde_en if lang == "en" else templates_alcalde_es
    else:
        templates = templates_ciudadano_en if lang == "en" else templates_ciudadano_es
    
    return random.choice(templates)

# ─── API endpoints ──────────────────────────────────────────────────────────────

@app.route("/api/zones", methods=["GET"])
def get_zones():
    """Returns all zones with current sensor data — from Orion or synthetic fallback"""
    impacts = get_entities("TrafficEnvironmentImpact")
    flows   = get_entities("TrafficFlowObserved")

    flow_map = {}
    for f in flows:
        zid = f["id"].split(":")[-1]
        flow_map[zid] = f

    zones = []
    if impacts:
        for imp in impacts:
            zid = imp["id"].split(":")[-1]
            flow = flow_map.get(zid, {})
            no2   = val(imp, "NO2Concentration")
            pm25  = val(imp, "PM25Concentration")
            pm10  = val(imp, "PM10Concentration")
            co2   = val(imp, "CO2Concentration")
            noise = val(imp, "noiseLevel")
            traffic = val(flow, "intensity")
            aqi   = val(imp, "aqi") or round(no2*2.1 + pm25*1.5, 1)
            gs    = val(imp, "greenScore") or round(max(0, min(100, 100-(no2*0.4+pm25*0.3+noise*0.1+(traffic/10)*0.2))), 1)
            name  = val(imp, "name") or zid
            loc   = imp.get("location", {}).get("value", {}).get("coordinates", [-8.40, 43.37])
            ts    = imp.get("TimeInstant", {}).get("value", datetime.utcnow().isoformat()+"Z")
            zones.append({
                "id": zid, "name": name,
                "lat": loc[1], "lon": loc[0],
                "no2": no2, "pm25": pm25, "pm10": pm10,
                "co2": co2, "noise": noise, "traffic": traffic,
                "aqi": aqi, "greenScore": gs, "timestamp": ts,
            })
    else:
        zones = synthetic_zone_data()

    # sanitize and normalize coordinates and ids
    for z in zones:
        # ensure id is a string
        if 'id' in z and isinstance(z['id'], str):
            z['id'] = z['id']
        # coerce numeric lat/lon and fix swapped values if necessary
        try:
            lat = float(z.get('lat', 0))
            lon = float(z.get('lon', 0))
        except Exception:
            # fallback to metadata if available
            meta = next((m for m in ZONES_META if m['id'].lower() == str(z.get('id','')).lower()), None)
            if meta:
                lat = meta['lat']; lon = meta['lon']
            else:
                lat = 43.362; lon = -8.411
        # If values look swapped (lat out of plausible range and lon looks like lat), swap them
        lat_ok = 40.0 <= lat <= 46.0
        lon_ok = -25.0 <= lon <= 5.0
        if not lat_ok and lon_ok:
            lat, lon = lon, lat
        # second check: both outside but reversed ranges
        if not lat_ok and not lon_ok:
            if -25.0 <= lat <= 5.0 and 40.0 <= lon <= 46.0:
                lat, lon = lon, lat
        z['lat'] = round(float(lat), 6)
        z['lon'] = round(float(lon), 6)
    return jsonify(zones)

@app.route("/api/dashboard", methods=["GET"])
def get_dashboard():
    # Support optional filtering by zone id (?zone=zone_id) — 'global' or empty means all
    zone_filter = request.args.get("zone", None)
    try:
        zones = get_zones().get_json() or synthetic_zone_data()
    except:
        zones = synthetic_zone_data()
    if zone_filter and zone_filter != 'global':
        zones = [z for z in zones if z.get('id') == zone_filter]
    if not zones:
        zones = synthetic_zone_data()
    avg_aqi  = round(sum(z["aqi"] for z in zones) / len(zones), 1)
    avg_gs   = round(sum(z["greenScore"] for z in zones) / len(zones), 1)
    avg_traf = round(sum(z["traffic"] for z in zones) / len(zones))
    alerts   = [z for z in zones if z["no2"] > 55 or z["noise"] > 70]
    return jsonify({
        "avgAqi": avg_aqi, "avgGreenScore": avg_gs,
        "avgTraffic": avg_traf, "alertCount": len(alerts),
        "alerts": [{"zone": a["name"], "no2": a["no2"], "noise": a["noise"]} for a in alerts],
        "zones": zones,
    })

@app.route("/api/airwatch", methods=["GET"])
def get_airwatch():
    # optional query param `zone` to return only that zone (or 'global' for all)
    zone_filter = request.args.get("zone", None)
    try:
        zones = get_zones().get_json() or synthetic_zone_data()
    except:
        zones = synthetic_zone_data()
    if zone_filter and zone_filter != 'global':
        zones = [z for z in zones if z.get('id') == zone_filter]
    # 6-hour forecasts per zone
    forecasts_orion = get_entities("TrafficEnvironmentImpactForecast", 200)
    fc_map = {}
    for fc in forecasts_orion:
        ref = fc.get("refTrafficFlowObserved", {}).get("value", "")
        zid = ref.split(":")[-1] if ref else None
        zid_l = zid.lower() if zid else None
        h   = val(fc, "forecastHour") or 1
        if zid:
            key = zid_l
            if key not in fc_map: fc_map[key] = []
            fc_map[key].append({"hour": int(h), "no2": val(fc, "NO2Concentration"), "aqi": val(fc, "airQualityIndex"), "traffic": val(fc, "trafficIntensity")})
    # If no forecasts, generate synthetic
    # Build lookup map for zones by lowercase id
    zone_lookup = { (z.get('id') or '').lower(): z for z in zones }
    for z in zones:
        zid = z["id"]
        zid_l = zid.lower() if isinstance(zid, str) else zid
        if zid_l not in fc_map:
            fc_map[zid_l] = []
            for h in range(1, 7):
                hour_abs = (datetime.utcnow().hour + h) % 24
                peak = 1.3 if (7 <= hour_abs <= 9 or 17 <= hour_abs <= 20) else 0.75
                fc_map[zid_l].append({"hour": h, "no2": round(z["no2"]*peak*random.uniform(0.9,1.1),1),
                    "aqi": round(z["aqi"]*peak, 1), "traffic": int(z["traffic"]*peak)})
        else:
            fc_map[zid_l].sort(key=lambda x: x["hour"])
    # Prepare return forecasts mapping using original zone ids when possible
    out_fc = {}
    for zl, arr in fc_map.items():
        orig = zone_lookup.get(zl, {}).get('id') or zl
        out_fc[orig] = arr

    # If caller requested a single zone, filter zones and forecasts (case-insensitive)
    if zone_filter and zone_filter != 'global':
        zf = zone_filter.lower()
        zones = [z for z in zones if (z.get('id') or '').lower() == zf]
        out_fc = {k: v for k, v in out_fc.items() if (k or '').lower() == zf}

    return jsonify({"zones": zones, "forecasts": out_fc})

@app.route("/api/ecoruta", methods=["GET"])
def get_ecoruta():
    origin_id  = request.args.get("origin", "")
    dest_id    = request.args.get("destination", "")
    mode       = (request.args.get("mode", "walk") or "walk").lower().strip()
    mode_alias = {"pedestrian": "walk", "foot": "walk", "walking": "walk", "bike": "bike", "bici": "bike", "bus": "bus", "autobus": "bus", "car": "car", "coche": "car"}
    mode       = mode_alias.get(mode, mode)
    mode_profiles = {
        "car":  {"speed": 30.0, "co2_rate": 140.0, "distance_w": 0.9, "pollution_w": 0.22, "traffic_w": 0.24, "exposure": 0.35, "neighbor_count": 6},
        "bus":  {"speed": 20.0, "co2_rate": 68.0,  "distance_w": 0.92, "pollution_w": 0.16, "traffic_w": 0.2,  "exposure": 0.55, "neighbor_count": 6},
        "bike": {"speed": 15.0, "co2_rate": 0.0,   "distance_w": 1.05, "pollution_w": 0.42, "traffic_w": 0.18, "exposure": 0.9,  "neighbor_count": 4},
        "walk": {"speed": 5.0,  "co2_rate": 0.0,   "distance_w": 1.0,  "pollution_w": 0.5,  "traffic_w": 0.12, "exposure": 1.0,  "neighbor_count": 4},
    }
    profile = mode_profiles.get(mode, mode_profiles["walk"])
    try:
        zones_r = requests.get("http://localhost:8000/api/zones", timeout=3)
        zones = zones_r.json() if zones_r.status_code == 200 else synthetic_zone_data()
    except Exception:
        zones = synthetic_zone_data()
    zone_map = {z["id"]: z for z in zones}
    hub_ids = {"centro", "ensanche", "cuatroCaminos", "juanFlorez", "orzan", "riazor", "ciudadVieja"}
    bus_hubs = hub_ids | {"matogrande", "asXubias"}
    bus_core_ids = {"centro", "ensanche", "cuatroCaminos", "juanFlorez", "ciudadVieja"}

    def dist(a, b):
        return math.hypot(a["lat"]-b["lat"], a["lon"]-b["lon"])

    def salubrity_cost(z):
        return z["no2"]*0.4 + z["pm25"]*0.3 + z["noise"]*0.15 + (z["traffic"]/100)*0.15

    def mode_edge_cost(from_zone, to_zone):
        d_km = dist(from_zone, to_zone) * 111
        base = d_km * profile["distance_w"]
        pollution = salubrity_cost(to_zone) * profile["pollution_w"]
        traffic = (to_zone.get("traffic", 0) / 100.0) * profile["traffic_w"]
        access_penalty = 0.0
        if mode == "bike" and to_zone.get("traffic", 0) > 700:
            access_penalty += 2.0
        if mode == "walk" and d_km > 1.6:
            access_penalty += 1.25
        if mode == "bus":
            # Bus should prefer major corridors and hubs, not arbitrary neighborhood hops.
            if to_zone["id"] in bus_hubs:
                access_penalty -= 0.35
            else:
                access_penalty += 0.95
            if from_zone["id"] not in bus_hubs:
                access_penalty += 0.4
            # Penalize very short hops for bus so it avoids awkward stop-by-stop zigzags.
            if d_km < 0.8:
                access_penalty += 0.75
        if mode == "car" and to_zone.get("traffic", 0) < 300:
            access_penalty += 0.2
        return base + pollution + traffic + access_penalty

    def bus_anchor(zones_subset, avoid_ids=None):
        avoid_ids = set(avoid_ids or [])
        candidates = [z for z in zones_subset if z["id"] in bus_core_ids and z["id"] not in avoid_ids]
        if not candidates:
            candidates = [z for z in zones_subset if z["id"] not in avoid_ids]
        return min(candidates, key=lambda z: salubrity_cost(z) + (z.get("traffic", 0) / 220.0) + (0.15 * abs(z["lat"] - 43.365)) + (0.15 * abs(z["lon"] + 8.41))) if candidates else None

    def bus_spine_path(src_id, dst_id, preferred_hub_id=None):
        # Build a transit-oriented candidate set: origin, destination and the main bus spine hubs.
        candidate_ids = {src_id, dst_id} | bus_core_ids
        candidate_zones = [z for z in zones if z["id"] in candidate_ids]
        candidate_map = {z["id"]: z for z in candidate_zones}
        candidate_graph = {z["id"]: [] for z in candidate_zones}

        for z1 in candidate_zones:
            nbrs = sorted(candidate_zones, key=lambda z2: dist(z1, z2))[:min(5, len(candidate_zones))]
            for z2 in nbrs:
                if z2["id"] != z1["id"]:
                    d_km = dist(z1, z2) * 111
                    # Keep bus on broad, connected corridors: short local zigzags are discouraged.
                    corridor_bonus = -0.28 if z2["id"] in bus_core_ids else 0.18
                    if z1["id"] not in bus_core_ids:
                        corridor_bonus += 0.35
                    if d_km < 1.0:
                        corridor_bonus += 0.6
                    candidate_graph[z1["id"]].append((d_km * 0.92 + salubrity_cost(z2) * 0.08 + corridor_bonus, z2["id"]))

        def candidate_dijkstra(src, dst):
            pq = [(0, src, [src])]
            seen = set()
            while pq:
                c, cur, path = heapq.heappop(pq)
                if cur in seen:
                    continue
                seen.add(cur)
                if cur == dst:
                    return path, c
                for ec, nb in candidate_graph.get(cur, []):
                    if nb not in seen:
                        heapq.heappush(pq, (c + ec, nb, path + [nb]))
            return [], float("inf")

        hub = candidate_map.get(preferred_hub_id) if preferred_hub_id in candidate_map else bus_anchor(candidate_zones, avoid_ids={src_id, dst_id})
        if not hub:
            return [], float("inf")
        if hub["id"] in (src_id, dst_id):
            hub = bus_anchor(candidate_zones, avoid_ids={src_id, dst_id, hub["id"]}) or hub

        path_a, cost_a = candidate_dijkstra(src_id, hub["id"])
        path_b, cost_b = candidate_dijkstra(hub["id"], dst_id)
        if path_a and path_b:
            return path_a + path_b[1:], cost_a + cost_b
        return [], float("inf")

    def route_color(cost):
        return "#22c55e" if cost < 25 else "#eab308" if cost < 45 else "#ef4444"

    if origin_id and dest_id and origin_id in zone_map and dest_id in zone_map:
        # Dijkstra on a mode-aware zone graph
        graph = {z["id"]: [] for z in zones}
        for z1 in zones:
            nbrs = sorted(zones, key=lambda z2: dist(z1, z2))[:profile["neighbor_count"]]
            for z2 in nbrs:
                if z2["id"] != z1["id"]:
                    cost = mode_edge_cost(z1, z2)
                    graph[z1["id"]].append((cost, z2["id"]))

        def dijkstra(src, dst):
            pq = [(0, src, [src])]
            visited = set()
            while pq:
                c, cur, path = heapq.heappop(pq)
                if cur in visited: continue
                visited.add(cur)
                if cur == dst: return path, c
                for ec, nb in graph.get(cur, []):
                    if nb not in visited:
                        heapq.heappush(pq, (c+ec, nb, path+[nb]))
            return [], float("inf")

        # Route 1: optimal (min pollution)
        path1, cost1 = dijkstra(origin_id, dest_id)

        # Bus-specific refinement: force the main route through a bus interchange spine.
        if mode == "bus":
            bus_hub = bus_anchor(zones, avoid_ids={origin_id, dest_id})
            path1_bus, cost1_bus = bus_spine_path(origin_id, dest_id, preferred_hub_id=bus_hub["id"] if bus_hub else None)
            if path1_bus:
                path1, cost1 = path1_bus, cost1_bus

        # Route 2: through a healthy intermediate zone.
        mid_zones = [z for z in zones if z["id"] not in (origin_id, dest_id)]
        if mode == "bus":
            mid_zones = [z for z in mid_zones if z["id"] in bus_core_ids] or mid_zones
        mid = min(mid_zones, key=lambda z: salubrity_cost(z)) if mid_zones else None
        path2 = []
        cost2 = float("inf")
        if mid:
            if mode == "bus":
                p2a, c2a = bus_spine_path(origin_id, mid["id"])
                p2b, c2b = bus_spine_path(mid["id"], dest_id)
            else:
                p2a, c2a = dijkstra(origin_id, mid["id"])
                p2b, c2b = dijkstra(mid["id"], dest_id)
            if p2a and p2b:
                path2 = p2a + p2b[1:]
                cost2 = c2a + c2b
            elif mid:
                path2 = [origin_id, mid["id"], dest_id]
                cost2 = salubrity_cost(mid)

        # Route 3: fastest (fewest hops, ignores pollution)
        graph3 = {z["id"]: [] for z in zones}
        for z1 in zones:
            nbrs = sorted(zones, key=lambda z2: dist(z1, z2))[:max(3, profile["neighbor_count"] - 2)]
            for z2 in nbrs:
                if z2["id"] != z1["id"]:
                    graph3[z1["id"]].append((dist(z1, z2), z2["id"]))
        pq3 = [(0, origin_id, [origin_id])]
        visited3 = set()
        path3, cost3 = [], float("inf")
        while pq3:
            c, cur, path = heapq.heappop(pq3)
            if cur in visited3: continue
            visited3.add(cur)
            if cur == dest_id:
                path3, cost3 = path, c
                break
            for ec, nb in graph3.get(cur, []):
                if nb not in visited3:
                    heapq.heappush(pq3, (c+ec, nb, path+[nb]))

        if not path3:
            path3 = [origin_id, dest_id]
            cost3 = dist(zone_map[origin_id], zone_map[dest_id])

        route_palette = {
            "Ruta EcoÓptima": "#22c55e",
            "Ruta Alternativa": "#f59e0b",
            "Ruta Rápida": "#3b82f6",
        }

        def build_route(path, name, label):
            if not path: return None
            nodes = [zone_map[z] for z in path if z in zone_map]
            if not nodes: return None
            avg_cost = round(sum(salubrity_cost(n) for n in nodes)/len(nodes), 1)
            dist_km = round(sum(dist(nodes[i], nodes[i+1])*111 for i in range(len(nodes)-1)), 2)
            time_min = round(dist_km / profile["speed"] * 60)
            if mode == "bus":
                transfers = max(0, sum(1 for n in nodes[1:-1] if n["id"] in bus_core_ids) - 1)
                time_min += transfers * 5 + max(0, len(nodes) - 2) * 1
            co2g = round(dist_km * profile["co2_rate"], 1)
            color = route_palette.get(name, route_color(avg_cost))
            return {
                "name": name, "label": label, "mode": mode, "color": color,
                "speedKmh": profile["speed"], "co2Rate": profile["co2_rate"],
                "transfers": max(0, sum(1 for n in nodes[1:-1] if n["id"] in bus_core_ids) - 1) if mode == "bus" else 0,
                "points": [{"lat": n["lat"], "lon": n["lon"], "name": n["name"]} for n in nodes],
                "distKm": dist_km, "timeMin": time_min, "co2g": co2g,
                "pollutionIndex": avg_cost,
            }

        routes = [r for r in [
            build_route(path1, "Ruta EcoÓptima", "Menor contaminación" if mode != "bus" else "Eje bus principal"),
            build_route(path2, "Ruta Alternativa", "Via zona verde" if mode != "bus" else "Con intercambio simple"),
            build_route(path3, "Ruta Rápida", "Más directa"),
        ] if r]

        # Best hour to go
        origin_zone = zone_map.get(origin_id)
        best_hours = []
        for h in range(24):
            peak = 1.4 if (7 <= h <= 9 or 17 <= h <= 20) else 1.1 if (10 <= h <= 16) else 0.6
            aqi_h = round((origin_zone["aqi"] if origin_zone else 50) * peak * random.uniform(0.95, 1.05), 1)
            best_hours.append({"hour": f"{h:02d}:00", "aqi": aqi_h, "traffic": int((origin_zone["traffic"] if origin_zone else 300) * peak)})

        return jsonify({"routes": routes, "bestHours": best_hours, "zones": zones})
    else:
        return jsonify({"routes": [], "bestHours": [], "zones": zones})

@app.route("/api/greenscore", methods=["GET"])
def get_greenscore():
    try:
        zones_r = requests.get("http://localhost:8000/api/zones", timeout=3)
        zones = zones_r.json() if zones_r.status_code == 200 else synthetic_zone_data()
    except Exception:
        zones = synthetic_zone_data()
    ranked = sorted(zones, key=lambda z: z["greenScore"], reverse=True)
    # Simulate previous hour trend
    for i, z in enumerate(ranked):
        z["rank"] = i + 1
        z["trend"] = random.choice(["up", "down", "stable"])
        z["prevScore"] = round(z["greenScore"] + random.uniform(-5, 5), 1)
        z["mlPrediction"] = round(z["greenScore"] * random.uniform(0.92, 1.08), 1)
    best = ranked[0] if ranked else None
    return jsonify({"ranked": ranked, "bestZone": best})

@app.route("/api/chat", methods=["POST"])
def chat_urbs():
    data = request.json or {}
    msg = data.get("message", "")
    mode = data.get("mode", "ciudadano")
    lang = data.get("lang", "es")

    if mode == "alcalde":
        prompt = (f"Eres URBS, un sistema avanzado de análisis urbano y políticas públicas de A Coruña. "
                  f"Responde de forma técnica, orientada a macro decisiones, coste-beneficio, predicciones ML y alertas de política pública en {'Inglés' if lang == 'en' else 'Español'}. "
                  f"Usuario: '{msg}'")
    else:
        prompt = (f"Eres URBS, el asistente virtual de movilidad y medio ambiente de A Coruña. "
                  f"Responde con humor urbano. Da consejos personales y accionables sobre cómo afecta al ciudadano en {'Inglés' if lang == 'en' else 'Español'}. "
                  f"Usuario: '{msg}'")
    try:
        return jsonify({"response": ask_ollama(prompt, timeout=8)})
    except Exception as e:
        print(f"Ollama error: {e}")

    # Better local fallback when Ollama is unavailable: produce varied contextual answers
    try:
        fb = local_fallback_response(msg, mode=mode, lang=lang)
        return jsonify({"response": fb})
    except Exception:
        # last-resort static message
        if mode == "alcalde":
            return jsonify({"response": "URBS no puede conectar con el modelo en este momento. Reintenta en unos segundos o revisa que Ollama esté levantado."})
        return jsonify({"response": "URBS no puede conectar con el modelo ahora mismo. Reintenta en unos segundos o revisa que Ollama esté levantado."})

@app.route("/api/explain/<zone_id>", methods=["GET"])
def explain_zone(zone_id):
    entity = get_entity(f"urn:ngsi-ld:TrafficEnvironmentImpact:{zone_id}")
    no2 = val(entity, "NO2Concentration") if entity else "desconocido"
    flow = get_entity(f"urn:ngsi-ld:TrafficFlowObserved:{zone_id}")
    traffic = val(flow, "intensity") if flow else "desconocida"
    prompt = (f"En la zona {zone_id} de A Coruña el NO2 es {no2} µg/m³ y el tráfico {traffic} veh/h. "
              f"Explica en 2 frases la correlación entre tráfico y contaminación.")
    try:
        return jsonify({"explanation": ask_ollama(prompt, timeout=6)})
    except Exception:
        pass
    return jsonify({"explanation": f"Con {traffic} veh/h, el NO₂ de {no2} µg/m³ en {zone_id} supera el umbral recomendado. Se prevén picos adicionales en hora punta."})

@app.route("/api/ecozones/<zone_id>/activate", methods=["POST"])
def activate_ecozone(zone_id):
    return jsonify({"status":"success","message":f"ZBE activada en {zone_id}. Acceso restringido a vehículos eléctricos y residentes."})

@app.route("/api/ecozones/<zone_id>/deactivate", methods=["POST"])
def deactivate_ecozone(zone_id):
    return jsonify({"status":"success","message":f"ZBE desactivada en {zone_id}."})
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_frontend(path):
    # Serve index.html at root and static files from the workspace
    if path == '' or path == 'index.html':
        return send_from_directory('.', 'index.html')
    # First try to serve file from workspace root, else from ./static
    try:
        return send_from_directory('.', path)
    except Exception:
        return send_from_directory('static', path)


if __name__ == "__main__":
    port = int(os.environ.get('PORT', 8000))
    app.run(host="0.0.0.0", port=port, debug=True)
