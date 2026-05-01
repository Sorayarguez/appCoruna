from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
import requests

app = FastAPI(title="URBS API - Módulos Mejorados")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ORION_URL = "http://orion:1026/v2"
OLLAMA_URL = "http://ollama:11434/api/generate"

import math
import heapq

def get_entities(entity_type):
    try:
        res = requests.get(f"{ORION_URL}/entities?type={entity_type}&limit=100", headers={"fiware-service": "urbs"})
        return res.json() if res.status_code == 200 else []
    except:
        return []

@app.get("/api/route")
def get_green_route(origin: str = None, destination: str = None):
    """Módulo 1: GreenRoute. Calcula una ruta basada en el índice de salubridad."""
    impacts = get_entities("TrafficEnvironmentImpact")
    flows = get_entities("TrafficFlowObserved")
    forecasts = get_entities("TrafficEnvironmentImpactForecast")
    items = get_entities("ItemFlowObserved")
    
    # Mapeo de entidades por refTrafficFlowObserved (Segmento)
    data_map = {}
    for flow in flows:
        seg_id = flow["id"].split(":")[-1]
        data_map[seg_id] = {"flow": flow, "impact": None, "forecast": None, "items": None}
        
    for imp in impacts:
        if "refTrafficFlowObserved" in imp:
            seg_id = imp["refTrafficFlowObserved"]["value"].split(":")[-1]
            if seg_id in data_map: data_map[seg_id]["impact"] = imp

    for fc in forecasts:
        if "refTrafficFlowObserved" in fc:
            seg_id = fc["refTrafficFlowObserved"]["value"].split(":")[-1]
            # Solo la previsión a +4h o la más reciente
            if seg_id in data_map: data_map[seg_id]["forecast"] = fc
            
    for item in items:
        if "refRoadSegment" in item:
            seg_id = item["refRoadSegment"]["value"].split(":")[-1]
            if seg_id in data_map: data_map[seg_id]["items"] = item

    route_segments = []
    for seg_id, data in data_map.items():
        imp = data["impact"]
        if not imp: continue
        
        loc = imp.get("location", {}).get("value", {}).get("coordinates", [0, 0])
        no2 = imp.get("NO2Concentration", {}).get("value", 0)
        pm25 = imp.get("PM25Concentration", {}).get("value", 0)
        noise = imp.get("noiseLevel", {}).get("value", 0)
        
        # Flujo de tráfico
        flow = data["flow"]
        intensity = flow.get("intensity", {}).get("value", 0) if flow else 0
        
        # Previsión
        fc = data["forecast"]
        fc_no2 = fc.get("NO2Concentration", {}).get("value", no2) if fc else no2
        
        # Item flow (peatones)
        it = data["items"]
        pedestrians = it.get("intensity", {}).get("value", 0) if it else 0
        
        # Calcular índice de salubridad combinando todo
        # Penaliza NO2, PM25, Ruido, Tráfico, y previsión futura
        # Beneficia (ligeramente) zonas con alta afluencia peatonal si no hay polución
        salubrity_score = 100 - (no2 * 0.4 + pm25 * 0.3 + noise * 0.1 + (intensity/10) * 0.1 + fc_no2 * 0.1)
        salubrity_index = max(0.1, min(100, salubrity_score)) # Evitar 0 para cálculos de coste
        
        color = "#39ff14" if salubrity_index > 75 else "#ffff00" if salubrity_index > 45 else "#ff3366"
        
        route_segments.append({
            "segmentId": seg_id,
            "coordinates": loc,
            "salubrityIndex": round(salubrity_index, 2),
            "no2": no2,
            "pm25": pm25,
            "noise": noise,
            "pedestrians": pedestrians,
            "color": color
        })
        
    # Si no hay origen ni destino explícito, devolvemos todo como "heatmap"
    if not origin or not destination:
        return {"route": route_segments, "is_path": False}
        
    # Lógica de cálculo de ruta (Grafo completo con Dijkstra)
    # Coste = distancia_euclídea * factor_insalubridad
    # Factor insalubridad = (100 - salubrity_index) + 1 (para evitar coste 0)
    
    seg_dict = {s["segmentId"]: s for s in route_segments}
    if origin not in seg_dict or destination not in seg_dict:
        return {"route": route_segments, "is_path": False, "error": "Origen o destino no encontrados"}
        
    def dist(s1, s2):
        return math.hypot(s1["coordinates"][0] - s2["coordinates"][0], s1["coordinates"][1] - s2["coordinates"][1])
        
    # Construir grafo
    graph = {s["segmentId"]: [] for s in route_segments}
    for s1 in route_segments:
        # Conectar con los 4 más cercanos para no hacer grafo denso irracional
        dists = [(dist(s1, s2), s2) for s2 in route_segments if s1["segmentId"] != s2["segmentId"]]
        dists.sort(key=lambda x: x[0])
        for d, s2 in dists[:4]:
            # El coste es la distancia ponderada por lo perjudicial que es el destino
            cost = d * ((100 - s2["salubrityIndex"]) + 5) 
            graph[s1["segmentId"]].append((cost, s2["segmentId"]))
            
    # Dijkstra
    pq = [(0, origin, [])]
    visited = set()
    best_path = []
    
    while pq:
        cost, current, path = heapq.heappop(pq)
        
        if current in visited:
            continue
        visited.add(current)
        
        path = path + [current]
        
        if current == destination:
            best_path = path
            break
            
        for edge_cost, neighbor in graph.get(current, []):
            if neighbor not in visited:
                heapq.heappush(pq, (cost + edge_cost, neighbor, path))
                
    # Reconstruir la ruta resultante
    final_route = [seg_dict[node] for node in best_path]
    return {"route": final_route, "is_path": True}

@app.get("/api/dashboard")
def get_dashboard_data():
    """Módulo 2: UrbanPulse. Retorna los datos actuales para el Dashboard."""
    return get_entities("TrafficEnvironmentImpact")

@app.get("/api/explain/{segment_id}")
def explain_pollution(segment_id: str):
    """Módulo 2: LLM local explica la situación de contaminación."""
    # Buscar impacto actual
    res_imp = requests.get(f"{ORION_URL}/entities/urn:ngsi-ld:TrafficEnvironmentImpact:{segment_id}", headers={"fiware-service": "urbs"})
    if res_imp.status_code == 200:
        imp = res_imp.json()
        no2 = imp.get("NO2Concentration", {}).get("value", 0)
    else:
        no2 = "desconocido"
        
    res_flow = requests.get(f"{ORION_URL}/entities/urn:ngsi-ld:TrafficFlowObserved:{segment_id}", headers={"fiware-service": "urbs"})
    if res_flow.status_code == 200:
        flow = res_flow.json()
        intensity = flow.get("intensity", {}).get("value", 0)
    else:
        intensity = "desconocida"

    prompt = f"Eres un experto en urbanismo y calidad del aire. En la calle {segment_id} el nivel de NO2 es de {no2} µg/m³ y la intensidad de tráfico es de {intensity} vehículos. En un máximo de 2 oraciones, explica cómo este tráfico correlaciona con la contaminación y menciona posibles picos de contaminación si el tráfico es elevado."
    
    try:
        res = requests.post(OLLAMA_URL, json={
            "model": "llama3",
            "prompt": prompt,
            "stream": False
        }, timeout=15)
        
        if res.status_code == 200:
            return {"explanation": res.json().get("response", "No response")}
        return {"explanation": "Modelo LLM no disponible."}
    except Exception as e:
        return {"explanation": f"El nivel actual de NO2 de {no2} µg/m³ está directamente causado por la intensidad de {intensity} vehículos en {segment_id}. Se recomienda activar medidas de restricción de acceso si persiste el volumen de tráfico actual."}

@app.post("/api/ecozones/{zone_id}/activate")
def activate_ecozone(zone_id: str):
    """Módulo 3: EcoZones. Activa la Zona de Bajas Emisiones dinámicamente."""
    # Modificar allowedVehicleType de todos los segmentos de tráfico a solo residentes y eléctricos
    flows = get_entities("TrafficFlowObserved")
    affected_segments = 0
    
    for flow in flows:
        flow_id = flow["id"]
        # En una app real, filtraríamos por zone_id. Aquí aplicamos a todos para el demo.
        payload = {
            "allowedVehicleType": {
                "value": ["electric", "resident", "publicTransport"],
                "type": "StructuredValue"
            }
        }
        res = requests.post(f"{ORION_URL}/entities/{flow_id}/attrs", json=payload, headers={"fiware-service": "urbs"})
        if res.status_code == 204:
            affected_segments += 1
            
            # Generar una previsión positiva a 1h
            seg_str = flow_id.split(":")[-1]
            forecast_id = f"urn:ngsi-ld:TrafficEnvironmentImpactForecast:{seg_str}-ZBE"
            valid_from = datetime.utcnow().isoformat() + "Z"
            valid_to = (datetime.utcnow() + timedelta(hours=1)).isoformat() + "Z"
            forecast_data = {
                "id": forecast_id,
                "type": "TrafficEnvironmentImpactForecast",
                "NO2Concentration": {"value": 20.0, "type": "Number"}, # Fuerte bajada simulada
                "PM25Concentration": {"value": 5.0, "type": "Number"},
                "airQualityIndex": {"value": 15, "type": "Number"},
                "validFrom": {"value": valid_from, "type": "DateTime"},
                "validTo": {"value": valid_to, "type": "DateTime"},
                "refTrafficFlowObserved": {"value": flow_id, "type": "Relationship"}
            }
            # Evita error si ya existe
            requests.post(f"{ORION_URL}/entities", json=forecast_data, headers={"fiware-service": "urbs", "Content-Type": "application/json"})
            requests.post(f"{ORION_URL}/entities/{forecast_id}/attrs", json={"NO2Concentration":{"value":20.0,"type":"Number"}, "validFrom":{"value":valid_from,"type":"DateTime"}}, headers={"fiware-service": "urbs"})

    return {"status": "success", "message": f"ZBE activada. {affected_segments} segmentos restringidos a vehículos limpios. Previsión actualizada."}

@app.post("/api/ecozones/{zone_id}/deactivate")
def deactivate_ecozone(zone_id: str):
    """Módulo 3: EcoZones. Desactiva la ZBE."""
    flows = get_entities("TrafficFlowObserved")
    for flow in flows:
        flow_id = flow["id"]
        payload = {
            "allowedVehicleType": {
                "value": ["any"],
                "type": "StructuredValue"
            }
        }
        requests.post(f"{ORION_URL}/entities/{flow_id}/attrs", json=payload, headers={"fiware-service": "urbs"})
    return {"status": "success", "message": "ZBE desactivada."}

@app.get("/api/3d/pollution")
def get_3d_pollution():
    """Endpoint para renderizar volumétricas en Three.js"""
    impacts = get_entities("TrafficEnvironmentImpact")
    points = []
    for d in impacts:
        coords = d.get("location", {}).get("value", {}).get("coordinates", [0, 0])
        val = d.get("NO2Concentration", {}).get("value", 0)
        points.append({
            "lat": coords[1],
            "lon": coords[0],
            "intensity": val
        })
    return {"points": points}
