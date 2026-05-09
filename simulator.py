import time
import random
import requests
import paho.mqtt.client as mqtt
from faker import Faker
from datetime import datetime

ORION_URL = "http://localhost:1026/v2"
IOTA_URL = "http://localhost:4041/iot"
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
API_KEY = "urbs_key"

fake = Faker('es_ES')

# Grupo de servicio en el IoT Agent
headers = {
    "fiware-service": "urbs",
    "fiware-servicepath": "/",
    "Content-Type": "application/json"
}

def provision_service():
    print("Provisionando Servicio IoT...")
    payload = {
        "services": [{
            "apikey": API_KEY,
            "cbroker": "http://orion:1026",
            "entity_type": "Thing",
            "resource": "/iot/d"
        }]
    }
    requests.post(f"{IOTA_URL}/services", headers=headers, json=payload)

# Generar 10 segmentos para A Coruña
segments = []
for i in range(1, 11):
    lat = 43.36 + random.uniform(-0.02, 0.02)
    lon = -8.41 + random.uniform(-0.02, 0.02)
    segments.append({
        "id": f"Coruna-Segment-{i}",
        "lat": lat,
        "lon": lon
    })

def register_devices():
    print("Registrando Dispositivos (TrafficFlowObserved & TrafficEnvironmentImpact)...")
    for seg in segments:
        # Dispositivo de tráfico (Protocolo MQTT)
        dev_traffic = {
            "devices": [{
                "device_id": f"traffic_{seg['id']}",
                "apikey": API_KEY,
                "entity_name": f"urn:ngsi-ld:TrafficFlowObserved:{seg['id']}",
                "entity_type": "TrafficFlowObserved",
                "protocol": "PDI-IoTA-UltraLight",
                "transport": "MQTT",
                "attributes": [
                    {"object_id": "i", "name": "intensity", "type": "Number"},
                    {"object_id": "o", "name": "occupancy", "type": "Number"},
                    {"object_id": "s", "name": "averageVehicleSpeed", "type": "Number"}
                ],
                "static_attributes": [
                    {"name": "location", "type": "geo:json", "value": {"type": "Point", "coordinates": [seg["lon"], seg["lat"]]}}
                ]
            }]
        }
        requests.post(f"{IOTA_URL}/devices", headers=headers, json=dev_traffic)
        
        # Dispositivo de peatones/ciclistas (Protocolo HTTP)
        dev_item = {
            "devices": [{
                "device_id": f"item_{seg['id']}",
                "apikey": API_KEY,
                "entity_name": f"urn:ngsi-ld:ItemFlowObserved:Pedestrian-{seg['id']}",
                "entity_type": "ItemFlowObserved",
                "protocol": "PDI-IoTA-UltraLight",
                "transport": "HTTP",
                "attributes": [
                    {"object_id": "ped", "name": "intensity", "type": "Number"}
                ],
                "static_attributes": [
                    {"name": "itemType", "type": "Text", "value": "pedestrian"},
                    {"name": "refRoadSegment", "type": "Relationship", "value": f"urn:ngsi-ld:RoadSegment:{seg['id']}"},
                    {"name": "location", "type": "geo:json", "value": {"type": "Point", "coordinates": [seg["lon"], seg["lat"]]}}
                ]
            }]
        }
        requests.post(f"{IOTA_URL}/devices", headers=headers, json=dev_item)
        
        # Dispositivo de Medio Ambiente (Protocolo HTTP)
        dev_env = {
            "devices": [{
                "device_id": f"env_{seg['id']}",
                "apikey": API_KEY,
                "entity_name": f"urn:ngsi-ld:TrafficEnvironmentImpact:{seg['id']}",
                "entity_type": "TrafficEnvironmentImpact",
                "protocol": "PDI-IoTA-UltraLight",
                "transport": "HTTP",
                "attributes": [
                    {"object_id": "no2", "name": "NO2Concentration", "type": "Number"},
                    {"object_id": "pm25", "name": "PM25Concentration", "type": "Number"},
                    {"object_id": "noise", "name": "noiseLevel", "type": "Number"}
                ],
                "static_attributes": [
                    {"name": "refTrafficFlowObserved", "type": "Relationship", "value": f"urn:ngsi-ld:TrafficFlowObserved:{seg['id']}"},
                    {"name": "location", "type": "geo:json", "value": {"type": "Point", "coordinates": [seg["lon"], seg["lat"]]}}
                ]
            }]
        }
        requests.post(f"{IOTA_URL}/devices", headers=headers, json=dev_env)

def create_subscription():
    # Orion Context Broker suscripción para QuantumLeap
    sub_payload = {
        "description": "Notify QuantumLeap of environment changes",
        "subject": {
            "entities": [{"idPattern": ".*", "type": "TrafficEnvironmentImpact"}],
            "condition": {"attrs": ["NO2Concentration", "PM25Concentration"]}
        },
        "notification": {
            "http": {"url": "http://quantumleap:8668/v2/notify"},
            "attrs": ["NO2Concentration", "PM25Concentration", "noiseLevel"],
            "metadata": ["dateCreated", "dateModified"]
        }
    }
    requests.post(f"{ORION_URL}/subscriptions", headers=headers, json=sub_payload)

if __name__ == "__main__":
    # Esperar a que inicien los contenedores
    time.sleep(10)
    provision_service()
    register_devices()
    create_subscription()
    
    # Cliente MQTT
    client = mqtt.Client()
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_start()
    
    print("Simulador iniciado. Generando datos cada 30 segundos...")
    
    while True:
        hour = datetime.now().hour
        # Simular picos matutinos (8-9h) y vespertinos (17-19h)
        if 8 <= hour <= 9 or 17 <= hour <= 19:
            traffic_multiplier = 2.5
        else:
            traffic_multiplier = 1.0
    
        for seg in segments:
            # Generar datos de tráfico aleatorios pero realistas
            intensity = int(random.uniform(50, 200) * traffic_multiplier)
            occupancy = round(random.uniform(0.1, 0.4) * traffic_multiplier, 2)
            speed = round(random.uniform(20, 60) / traffic_multiplier, 2)
            
            # 1. Enviar Tráfico por MQTT (Topic: /urbs_key/traffic_Coruna-Segment-X/attrs)
            payload_traffic = f"i|{intensity}|o|{occupancy}|s|{speed}"
            topic = f"/{API_KEY}/traffic_{seg['id']}/attrs"
            client.publish(topic, payload_traffic)
            
            # Generar datos ambientales correlacionados
            no2 = round(intensity * 0.3 + random.uniform(5, 15), 2)
            pm25 = round(intensity * 0.1 + random.uniform(2, 8), 2)
            noise = round(40 + (intensity * 0.1) + random.uniform(-5, 5), 2)
            
            # 2. Enviar Ambiente por HTTP al IoT Agent
            payload_env = f"no2|{no2}|pm25|{pm25}|noise|{noise}"
            req_url = f"http://localhost:7896/iot/d?k={API_KEY}&i=env_{seg['id']}"
            requests.post(req_url, data=payload_env, headers={"Content-Type": "text/plain", "fiware-service": "urbs"})
            
            # 3. Enviar Peatones por HTTP
            pedestrians = int(random.uniform(10, 100) * (2.0 if 12 <= hour <= 14 or 18 <= hour <= 20 else 0.5))
            payload_item = f"ped|{pedestrians}"
            req_item_url = f"http://localhost:7896/iot/d?k={API_KEY}&i=item_{seg['id']}"
            requests.post(req_item_url, data=payload_item, headers={"Content-Type": "text/plain", "fiware-service": "urbs"})
        
        print(f"[{datetime.now().isoformat()}] Datos actualizados en los {len(segments)} segmentos. Multiplicador de Tráfico: x{traffic_multiplier}")
        time.sleep(30)
