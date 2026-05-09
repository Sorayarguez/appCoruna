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
OLLAMA_URL = os.environ.get("OLLAMA_URL", "").strip()
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

    # normalize ids to lowercase for consistent matching
    for z in zones:
        if 'id' in z and isinstance(z['id'], str):
            z['id'] = z['id']
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
            fc_map[zid] = []
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
    if OLLAMA_URL:
        try:
            res = requests.post(OLLAMA_URL, json={"model": "llama3", "prompt": prompt, "stream": False}, timeout=15)
            if res.status_code == 200:
                return jsonify({"response": res.json().get("response", "Sin respuesta")})
        except:
            pass
    # Fallback smart responses
    msg_l = msg.lower()
    if "riazor" in msg_l or "playa" in msg_l:
        if mode == "alcalde": return jsonify({"response": "Riazor presenta AQI ~80. Recomendación: mantener monitorización, no se requieren intervenciones en el tráfico a corto plazo."})
        else: return jsonify({"response": "Riazor está genial (AQI ~80). Coge la bici o vete a dar un paseo que el aire está de lujo hoy."})
    if "tráfico" in msg_l or "trafico" in msg_l:
        if mode == "alcalde": return jsonify({"response": "Saturación detectada en Cuatro Caminos y el Centro. Se sugiere activar protocolo de restricción de tráfico en Centro antes de las 14h para reducir impacto."})
        else: return jsonify({"response": "Cuatro Caminos y el Centro están a tope. Si vas por ahí vas a tragar humo, evítalos entre las 8-9h y 18-20h, te lo digo yo que llevo horas mirando."})
    if "contamina" in msg_l or "no2" in msg_l or "aire" in msg_l:
        if mode == "alcalde": return jsonify({"response": "Las métricas indican picos de contaminación en Cuatro Caminos y As Xubias. Mesoiro mantiene niveles óptimos. Analizar posible expansión de ZBE."})
        else: return jsonify({"response": "Mesoiro gana otra vez, ya van 4 días seguidos, alguien avise a Orzán. Sin embargo, Cuatro Caminos está fatal hoy, ni te acerques."})
    if "bici" in msg_l or "ciclista" in msg_l:
        if mode == "alcalde": return jsonify({"response": "El eje Orzán-Riazor-Monte Alto presenta viabilidad alta para movilidad activa. Fomentar uso del carril bici en esta zona tiene alto beneficio (coste bajo, impacto ambiental positivo)."})
        else: return jsonify({"response": "Coge la bici y tira por Orzán → Riazor → Monte Alto. ¡Aprovecha que el aire está limpio y te ahorras un buen atasco!"})

    if mode == "alcalde": return jsonify({"response": "Sistema URBS operativo. Analizando métricas de política pública y sostenibilidad. ¿Qué zona requiere evaluación?"})
    else:
        import random
        if lang == "en":
            respuestas = [
                "Hello! I am URBS. Watch out, the City Center is a mess today, trust me, I've been monitoring for 3 hours.",
                "Hey there! URBS here. The breeze in Riazor is amazing today. Do you want me to trace a route?",
                "What's up! Monitoring A Coruña... by the way, if you're driving through Cuatro Caminos, arm yourself with patience.",
                "Hello, hello! If you're looking for the best place for a walk, check the GreenScore, you won't regret it.",
                "I'm URBS. Today the air smells like the sea and like you're running late. Where are you heading?"
            ]
        else:
            respuestas = [
                "¡Hola! Soy URBS. Ojo, el Centro está fatal hoy, te lo digo yo que llevo 3 horas monitorizando.",
                "¡Epa! Aquí URBS. La brisa en Riazor hoy es de primera. ¿Quieres que te trace una ruta?",
                "¡Qué pasa! Monitorizando A Coruña estoy... por cierto, si vas en coche por Cuatro Caminos, ármate de paciencia.",
                "¡Hola, hola! Si buscas el mejor sitio para pasear, échale un ojo al GreenScore, no te arrepentirás.",
                "Soy URBS. Hoy el ambiente huele a mar y a que llegas tarde. ¿A dónde vas?"
            ]
        return jsonify({"response": random.choice(respuestas)})

@app.route("/api/explain/<zone_id>", methods=["GET"])
def explain_zone(zone_id):
    entity = get_entity(f"urn:ngsi-ld:TrafficEnvironmentImpact:{zone_id}")
    no2 = val(entity, "NO2Concentration") if entity else "desconocido"
    flow = get_entity(f"urn:ngsi-ld:TrafficFlowObserved:{zone_id}")
    traffic = val(flow, "intensity") if flow else "desconocida"
    prompt = (f"En la zona {zone_id} de A Coruña el NO2 es {no2} µg/m³ y el tráfico {traffic} veh/h. "
              f"Explica en 2 frases la correlación entre tráfico y contaminación.")
    if OLLAMA_URL:
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
