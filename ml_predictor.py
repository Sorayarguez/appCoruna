import time
import requests
from datetime import datetime, timedelta
import random

ORION_URL = "http://localhost:1026/v2"

print("Iniciando ML Predictor para URBS...")

while True:
    try:
        # 1. Obtener el estado actual (NO2 y PM2.5) de las entidades ambientales en Orion
        res = requests.get(
            f"{ORION_URL}/entities?type=TrafficEnvironmentImpact", 
            headers={"fiware-service": "urbs"}
        )
        
        if res.status_code == 200:
            entities = res.json()
            for entity in entities:
                # Extraer el id del segmento de la entidad
                seg_id = entity["id"].split(":")[-1]
                no2 = entity.get("NO2Concentration", {}).get("value", 0)
                pm25 = entity.get("PM25Concentration", {}).get("value", 0)
                
                # Simular modelo predictivo (RandomForest/LSTM dummy)
                # Basado en el nivel actual, proyectamos si empeora o mejora
                trend = 1.15 if no2 > 50 else 0.85
                
                # Generamos predicciones para +1h, +2h, y +4h
                for hours_ahead in [1, 2, 4]:
                    pred_no2 = round(no2 * (trend ** hours_ahead) + random.uniform(-5, 5), 2)
                    pred_pm25 = round(pm25 * (trend ** hours_ahead) + random.uniform(-2, 2), 2)
                    
                    forecast_id = f"urn:ngsi-ld:TrafficEnvironmentImpactForecast:{seg_id}-plus{hours_ahead}h"
                    valid_from = (datetime.utcnow() + timedelta(hours=hours_ahead)).isoformat() + "Z"
                    valid_to = (datetime.utcnow() + timedelta(hours=hours_ahead+1)).isoformat() + "Z"
                    
                    forecast_data = {
                        "id": forecast_id,
                        "type": "TrafficEnvironmentImpactForecast",
                        "NO2Concentration": {"value": max(0, pred_no2), "type": "Number"},
                        "PM25Concentration": {"value": max(0, pred_pm25), "type": "Number"},
                        "airQualityIndex": {"value": int((pred_no2 + pred_pm25) / 2), "type": "Number"},
                        "validFrom": {"value": valid_from, "type": "DateTime"},
                        "validTo": {"value": valid_to, "type": "DateTime"},
                        "refTrafficEnvironmentImpact": {"value": entity["id"], "type": "Relationship"},
                        "refTrafficFlowObserved": {"value": f"urn:ngsi-ld:TrafficFlowObserved:{seg_id}", "type": "Relationship"}
                    }
                    
                    # Intentamos crear la entidad en Orion
                    create_res = requests.post(
                        f"{ORION_URL}/entities", 
                        json=forecast_data, 
                        headers={"fiware-service": "urbs", "Content-Type": "application/json"}
                    )
                    
                    # Si ya existe (422), actualizamos sus atributos
                    if create_res.status_code == 422:
                        update_payload = {
                            "NO2Concentration": {"value": max(0, pred_no2), "type": "Number"},
                            "PM25Concentration": {"value": max(0, pred_pm25), "type": "Number"},
                            "validFrom": {"value": valid_from, "type": "DateTime"},
                            "validTo": {"value": valid_to, "type": "DateTime"}
                        }
                        requests.post(
                            f"{ORION_URL}/entities/{forecast_id}/attrs", 
                            json=update_payload, 
                            headers={"fiware-service": "urbs", "Content-Type": "application/json"}
                        )
                        
            print(f"[{datetime.now().isoformat()}] Predicciones actualizadas para {len(entities)} segmentos ambientales.")
    except Exception as e:
        print(f"Error en ML predictor: {e}")
        
    # Ejecutar la simulación del modelo ML cada 60 segundos
    time.sleep(60)
