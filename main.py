from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime, timedelta
import requests, math, heapq, random

app = Flask(__name__)
CORS(app)

ORION_URL = "http://orion:1026/v2"
OLLAMA_URL = "http://ollama:11434/api/generate"
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

    return jsonify(zones)

@app.route("/api/dashboard", methods=["GET"])
def get_dashboard():
    zones_r = requests.get("http://localhost:8000/api/zones", timeout=5)
    zones = zones_r.json() if zones_r.status_code == 200 else synthetic_zone_data()
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
    zones_r = requests.get("http://localhost:8000/api/zones", timeout=5)
    zones = zones_r.json() if zones_r.status_code == 200 else synthetic_zone_data()
    # 6-hour forecasts per zone
    forecasts_orion = get_entities("TrafficEnvironmentImpactForecast", 200)
    fc_map = {}
    for fc in forecasts_orion:
        ref = fc.get("refTrafficFlowObserved", {}).get("value", "")
        zid = ref.split(":")[-1] if ref else None
        h   = val(fc, "forecastHour") or 1
        if zid:
            if zid not in fc_map: fc_map[zid] = []
            fc_map[zid].append({"hour": int(h), "no2": val(fc, "NO2Concentration"), "aqi": val(fc, "airQualityIndex"), "traffic": val(fc, "trafficIntensity")})
    # If no forecasts, generate synthetic
    for z in zones:
        zid = z["id"]
        if zid not in fc_map:
            fc_map[zid] = []
            for h in range(1, 7):
                hour_abs = (datetime.utcnow().hour + h) % 24
                peak = 1.3 if (7 <= hour_abs <= 9 or 17 <= hour_abs <= 20) else 0.75
                fc_map[zid].append({"hour": h, "no2": round(z["no2"]*peak*random.uniform(0.9,1.1),1),
                    "aqi": round(z["aqi"]*peak, 1), "traffic": int(z["traffic"]*peak)})
        else:
            fc_map[zid].sort(key=lambda x: x["hour"])
    return jsonify({"zones": zones, "forecasts": fc_map})

@app.route("/api/ecoruta", methods=["GET"])
def get_ecoruta():
    origin_id  = request.args.get("origin", "")
    dest_id    = request.args.get("destination", "")
    zones_r = requests.get("http://localhost:8000/api/zones", timeout=5)
    zones = zones_r.json() if zones_r.status_code == 200 else synthetic_zone_data()
    zone_map = {z["id"]: z for z in zones}

    def dist(a, b):
        return math.hypot(a["lat"]-b["lat"], a["lon"]-b["lon"])

    def salubrity_cost(z):
        return z["no2"]*0.4 + z["pm25"]*0.3 + z["noise"]*0.15 + (z["traffic"]/100)*0.15

    def route_color(cost):
        return "#22c55e" if cost < 25 else "#eab308" if cost < 45 else "#ef4444"

    if origin_id and dest_id and origin_id in zone_map and dest_id in zone_map:
        # Dijkstra on full zone graph
        graph = {z["id"]: [] for z in zones}
        for z1 in zones:
            nbrs = sorted(zones, key=lambda z2: dist(z1, z2))[:5]
            for z2 in nbrs:
                if z2["id"] != z1["id"]:
                    d = dist(z1, z2)
                    cost = d * (salubrity_cost(z2) + 1)
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

        # Route 2: through mid-zone
        mid_zones = [z for z in zones if z["id"] not in (origin_id, dest_id)]
        mid = min(mid_zones, key=lambda z: salubrity_cost(z)) if mid_zones else None
        path2 = []
        cost2 = float("inf")
        if mid:
            p2a, c2a = dijkstra(origin_id, mid["id"])
            p2b, c2b = dijkstra(mid["id"], dest_id)
            if p2a and p2b:
                path2 = p2a + p2b[1:]
                cost2 = c2a + c2b

        # Route 3: fastest (fewest hops, ignores pollution)
        graph3 = {z["id"]: [] for z in zones}
        for z1 in zones:
            nbrs = sorted(zones, key=lambda z2: dist(z1, z2))[:3]
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

        def build_route(path, name, label):
            if not path: return None
            nodes = [zone_map[z] for z in path if z in zone_map]
            if not nodes: return None
            avg_cost = round(sum(salubrity_cost(n) for n in nodes)/len(nodes), 1)
            dist_km = round(sum(dist(nodes[i], nodes[i+1])*111 for i in range(len(nodes)-1)), 2)
            time_min = round(dist_km / 5.0 * 60) # walking 5km/h
            co2g = round(dist_km * 21, 1)
            color = route_color(avg_cost)
            return {
                "name": name, "label": label, "color": color,
                "points": [{"lat": n["lat"], "lon": n["lon"], "name": n["name"]} for n in nodes],
                "distKm": dist_km, "timeMin": time_min, "co2g": co2g,
                "pollutionIndex": avg_cost,
            }

        routes = [r for r in [
            build_route(path1, "Ruta EcoÓptima", "Menor contaminación"),
            build_route(path2, "Ruta Alternativa", "Via zona verde"),
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
    zones_r = requests.get("http://localhost:8000/api/zones", timeout=5)
    zones = zones_r.json() if zones_r.status_code == 200 else synthetic_zone_data()
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
    msg = (request.json or {}).get("message", "")
    prompt = (f"Eres URBS, el asistente virtual de movilidad y medio ambiente de A Coruña. "
              f"Responde de forma concisa y amigable en español. "
              f"Usuario: '{msg}'")
    try:
        res = requests.post(OLLAMA_URL, json={"model": "llama3", "prompt": prompt, "stream": False}, timeout=15)
        if res.status_code == 200:
            return jsonify({"response": res.json().get("response", "Sin respuesta")})
    except:
        pass
    # Fallback smart responses
    msg_l = msg.lower()
    if "riazor" in msg_l or "playa" in msg_l:
        return jsonify({"response": "Riazor tiene actualmente calidad de aire buena (AQI ~80). Es una de las mejores zonas para pasear en bici o a pie. ¡Recomendada!"})
    if "tráfico" in msg_l or "trafico" in msg_l:
        return jsonify({"response": "El mayor tráfico en A Coruña ahora mismo está en Cuatro Caminos y el Centro. Evítalos entre 8-9h y 18-20h."})
    if "contamina" in msg_l or "no2" in msg_l or "aire" in msg_l:
        return jsonify({"response": "Las zonas con mejor calidad del aire son Monte Alto, Mesoiro y Orzán. Las más contaminadas son Cuatro Caminos y As Xubias."})
    if "bici" in msg_l or "ciclista" in msg_l:
        return jsonify({"response": "Te recomiendo la ruta Orzán → Riazor → Monte Alto. Tiene bajo nivel de tráfico y buena calidad del aire. Mejor ir antes de las 9h o después de las 20h."})
    return jsonify({"response": f"Hola, soy URBS. Monitorizamos {len(ZONES_META)} zonas de A Coruña en tiempo real. ¿Te ayudo con rutas, calidad del aire o niveles de tráfico?"})

@app.route("/api/explain/<zone_id>", methods=["GET"])
def explain_zone(zone_id):
    entity = get_entity(f"urn:ngsi-ld:TrafficEnvironmentImpact:{zone_id}")
    no2 = val(entity, "NO2Concentration") if entity else "desconocido"
    flow = get_entity(f"urn:ngsi-ld:TrafficFlowObserved:{zone_id}")
    traffic = val(flow, "intensity") if flow else "desconocida"
    prompt = (f"En la zona {zone_id} de A Coruña el NO2 es {no2} µg/m³ y el tráfico {traffic} veh/h. "
              f"Explica en 2 frases la correlación entre tráfico y contaminación.")
    try:
        res = requests.post(OLLAMA_URL, json={"model":"llama3","prompt":prompt,"stream":False}, timeout=12)
        if res.status_code == 200:
            return jsonify({"explanation": res.json().get("response","")})
    except:
        pass
    return jsonify({"explanation": f"Con {traffic} veh/h, el NO₂ de {no2} µg/m³ en {zone_id} supera el umbral recomendado. Se prevén picos adicionales en hora punta."})

@app.route("/api/ecozones/<zone_id>/activate", methods=["POST"])
def activate_ecozone(zone_id):
    return jsonify({"status":"success","message":f"ZBE activada en {zone_id}. Acceso restringido a vehículos eléctricos y residentes."})

@app.route("/api/ecozones/<zone_id>/deactivate", methods=["POST"])
def deactivate_ecozone(zone_id):
    return jsonify({"status":"success","message":f"ZBE desactivada en {zone_id}."})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
