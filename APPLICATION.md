# APPLICATION.md - URBS

## 1. Objetivo

**URBS** es la plataforma urbana inteligente de appCoruna para A Coruña que integra datos de movilidad, calidad del aire, ruido y comportamiento urbano en una interfaz operativa y accesible. 

**Problema que resuelve:** La información urbana está fragmentada en múltiples fuentes (APIs FIWARE, sensores IoT, dashboards analíticos) dificultando responder preguntas prácticas como:
- ¿Qué zona está más cargada ahora?
- ¿Qué ruta minimiza exposición a contaminación?
- ¿Cómo evoluciona la calidad del aire en las próximas horas?
- ¿Qué barrios requieren medidas de mitigación?

URBS centraliza esta información en una experiencia única con foco en consulta rápida y soporte a la toma de decisiones de movilidad sostenible, orientada a tres perfiles: ciudadanía, personal técnico y gestión pública.

---

## 2. Estado del Arte

La monitorización urbana ha evolucionado desde dashboards fragmentados hacia plataformas integradas. Las soluciones actuales en contextos de ciudades inteligentes combinan:

- **Plataformas FIWARE:** estándares abiertos para datos urbanos, pero requieren especialización técnica.
- **Dashboards de analítica:** Grafana, Kibana (potentes para series temporales, pero orientadas a expertos).
- **APIs de tráfico y aire:** Google Maps, OpenWeatherMap, AirVisual (externas, no adaptables localmente).

En Europa, varias ciudades han consolidado aproximaciones de referencia: **Santander** fue pionera en despliegues IoT urbanos a gran escala; **Barcelona** ha impulsado modelos de gobernanza del dato urbano y plataformas de servicios digitales; **Helsinki** y su ecosistema metropolitano han avanzado en movilidad como servicio (MaaS) con integración multimodal; **Ámsterdam** ha promovido laboratorios urbanos orientados a sostenibilidad y eficiencia energética. Estas iniciativas suelen destacar por su capacidad de captación de datos y analítica, pero con frecuencia separan la capa técnica de la experiencia ciudadana.

URBS se posiciona en ese contexto como una implementación local orientada a decisión operativa y comprensión inmediata, manteniendo compatibilidad con el enfoque FIWARE y priorizando la usabilidad para perfiles no expertos.

**Diferenciadores de URBS:**
- Interfaz unificada para ciudadanía no técnica + gestión pública.
- Integración transparente de FIWARE sin exposición técnica.
- Resiliencia: funciona degradado si servicios fallan (fallback sintético).
- Cálculo de rutas **ecoóptimas** (no solo rápidas) considerando contaminación, tráfico y modo de transporte.
- Asistente conversacional contextual adaptado a rol (ciudadano/alcalde).

---

## 3. Funcionalidades Principales

| Módulo | Descripción |
|--------|-------------|
| **Dashboard** | KPIs globales (AQI, tráfico, alertas), sincronización de sensores, diagrama FIWARE, Grafana embebido. |
| **AirWatch** | Mapa de calor, vista 3D, correlación tráfico-contaminación, predicción horaria (6h). |
| **EcoRuta** | Cálculo de 3 rutas (ecoóptima, alternativa, rápida) con comparativa de distancia, tiempo, CO₂ e índice de exposición. |
| **GreenScore** | Ranking de barrios, radar comparativo, mapa de salubridad, clasificación accesible. |
| **Histórico** | Series temporales, paneles de evolución, exportación de snapshots. |
| **Perfil + Asistente** | Avatar, logros, retos semanales, chat URBS contextual (español/inglés). |

---

## 4. Funcionalidades Detalladas (extraído del PRD)

### 4.1 Dashboard Principal
- **KPIs agregados:** AQI global, intensidad de tráfico, número de alertas, GreenScore promedio.
- **Alertas activas:** lista con severidad y zona afectada.
- **Sincronización reciente:** timestamp de última actualización de sensores.
- **Diagrama FIWARE:** visualización de flujo de datos y arquitectura.
- **Grafana embebido:** panel `urbs-dashboard` con series de 24h.

### 4.2 AirWatch - Inspección Visual Profunda
- **Mapa de calor:** visualiza distribución espacial de NO₂, PM2.5, PM10, ruido.
- **Vista 3D:** inmersiva con mapeo altura=contaminación.
- **Relación tráfico-contaminantes:** superpone intensidad de vehículos con concentraciones.
- **Predicción 6h:** por zona, con confianza indicada.
- **Indicadores por zona:** evolución y tendencias (↑/↓).

### 4.3 EcoRuta - Decisión de Movilidad
- **Selección:** origen, destino, modo (coche/bus/bici/caminar).
- **Cálculo multi-ruta:** ecoóptima (mín. contaminación+ruido), alternativa (equilibrio), rápida (mín. tiempo).
- **Comparativa visual:** código de colores, distancia, tiempo, CO₂ estimado (kg), índice de exposición (0-100).
- **Ponderación adaptativa:** penalizaciones específicas por modo (restricciones bus, rutas ciclopistas, áreas peatonales).

### 4.4 GreenScore - Ranking Ambiental
- **Métrica sintética:** combina tráfico, ruido (dB), NO₂ (ppm), PM2.5 (µg/m³), CO₂ (ppm).
- **Ranking interactivo:** ordena zonas de salubridad alta → baja.
- **Comparativa radar:** selecciona hasta 3 zonas, visualiza diferencias en 6 ejes.
- **Mapa de salubridad:** código cromático verde (excelente) → rojo (crítico).

### 4.5 Requisitos No Funcionales Clave
- **Resiliencia:** Si Orion no responde, el backend genera datos sintéticos consistentes.
- **Degradación controlada:** ausencia de Grafana, Ollama o CrateDB no rompe funcionalidad.
- **Responsive:** adapta a escritorio, tablet y móvil sin desbordamientos horizontales.
- **Asistente fallback:** si Ollama no responde, retorna contexto útil en lugar de vacío.

---

## 5. Diagrama de Arquitectura

```
┌──────────────────────────────────────────────────────────────────┐
│                        PRESENTACIÓN (Frontend)                   │
├──────────────────────────────────────────────────────────────────┤
│  index.html (Vue CDN) → Dashboard, AirWatch, EcoRuta,            │
│  GreenScore, Perfil, Chat flotante                               │
│  - Leaflet (maps) | Chart.js (gráficos) | Three.js (3D)         │
│  - Grafana embedded (series temporales)                           │
└──────────────┬───────────────────────────────────┬────────────────┘
               │ REST API JSON                      │ iFrame Grafana
               │                                     │
┌──────────────▼──────────────────────────────────────────────────┐
│                  BACKEND (Flask - main.py)                      │
├──────────────────────────────────────────────────────────────────┤
│  /api/zones | /api/dashboard | /api/airwatch                    │
│  /api/ecoruta | /api/greenscore | /api/chat                     │
│                                                                   │
│  Normalización & Cálculo:                                        │
│  • Consolidación de datos de Orion → Zonas agregadas            │
│  • Cálculo de rutas (Dijkstra) | Ranking GreenScore            │
│  • Respuestas asistente (Ollama o fallback contextual)          │
└──────────────┬──────────────────────────────────────────────────┘
               │
    ┌──────────┴─────────────┬──────────────────┬────────────────┐
    │                        │                  │                │
    ▼                        ▼                  ▼                ▼
┌─────────────┐      ┌──────────────┐    ┌──────────┐    ┌────────────┐
│ FIWARE      │      │   CrateDB    │    │  Ollama  │    │  Seeders   │
│ Orion       │      │ (QuantumLeap)│    │  (LLM)   │    │ (sintéticos)│
│ + MongoDB   │      │              │    │          │    │            │
│             │      │ - series     │    │ Respuestas   │ seed_data  │
│ - Contexto  │      │ - histórico  │    │ dinámicas    │seed_grafana│
│ - Entidades │      │              │    │              │simulator   │
│ - Atributos │      │ Grafana ←────┤    │              │ml_predictor│
└─────────────┘      └──────────────┘    └──────────────┘ └────────────┘
       ▲
       │ (MQTT)
   ┌───┴───────┐
   │  Mosquitto │
   │ IoT Agent  │
   └────────────┘
```

**Flujo de datos principal:**
1. Seeders pueblan Orion (zonas, tráfico, impacto ambiental) y CrateDB (series).
2. Frontend carga y llama `/api/dashboard`, `/api/zones`, etc.
3. Backend consulta Orion (o crea fallback sintético) y devuelve JSON normalizado.
4. Frontend renderiza mapas (Leaflet), gráficos (Chart.js), 3D (Three.js).
5. Grafana muestra series históricas embebido en la web.
6. Chat URBS: frontend → `/api/chat` → Ollama → respuesta dinámica.

---

## 6. Diagrama del Modelo de Datos

### 6.1 Entidades FIWARE (Orion)

```
┌───────────────────────────────────────────────────────────┐
│           ENTIDADES FIWARE (Orion/NGSI-LD)               │
├───────────────────────────────────────────────────────────┤
│                                                            │
│  TrafficFlowObserved                                      │
│  • id, type, location (geo:json)                          │
│  • intensity, averageVehicleSpeed, occupancy             │
│  • vehicleType, laneDirection, dateObserved              │
│           │                                                │
│           ├─ references → RoadSegment                     │
│           │                                                │
│           └─ derived → TrafficEnvironmentImpact           │
│                                                            │
│  TrafficEnvironmentImpact                                 │
│  • id, type, location                                     │
│  • NO2Concentration, PM25Concentration                    │
│  • PM10Concentration, CO2Concentration                    │
│  • noiseLevel, aqi, greenScore                           │
│  • refTrafficFlowObserved (FK)                            │
│           │                                                │
│           └─ projects → TrafficEnvironmentImpactForecast  │
│                                                            │
│  TrafficEnvironmentImpactForecast                         │
│  • id, type, forecastHour (1-6)                           │
│  • NO2Concentration, PM25Concentration                    │
│  • airQualityIndex, trafficIntensity                      │
│  • validFrom, validTo                                     │
│  • refTrafficFlowObserved, refTrafficEnvironmentImpact    │
│                                                            │
│  AirQualityObserved (consolidado)                         │
│  • NO2, PM2.5, PM10, CO2                                  │
│  • airQualityIndex, airQualityLevel                       │
│  • location, TimeInstant                                  │
│                                                            │
│  NoiseLevelObserved                                       │
│  • LAeq, LAmax, LAmin                                     │
│  • location, TimeInstant                                  │
│                                                            │
│  ItemFlowObserved (peatones/ciclistas)                    │
│  • flowRate, location, TimeInstant                        │
│                                                            │
└───────────────────────────────────────────────────────────┘
```

### 6.2 Agregación del Backend (Normalización)

```
┌─────────────────────────────────────────────────────────┐
│      ZONE (Entidad agregada del backend)                │
├─────────────────────────────────────────────────────────┤
│  id: string                    # ej: "zone-centro"     │
│  name: string                  # ej: "Centro Ciudad"   │
│  lat, lon: float               # WGS84                 │
│                                                          │
│  TRÁFICO:                                               │
│  ├─ traffic: int               # intensidad (0-100)   │
│  ├─ avgSpeed: float            # km/h                  │
│  └─ occupancy: float           # % saturación         │
│                                                          │
│  AIRE Y RUIDO:                                          │
│  ├─ no2: float                 # ppm                   │
│  ├─ pm25: float                # µg/m³                │
│  ├─ pm10: float                # µg/m³                │
│  ├─ co2: float                 # ppm                   │
│  ├─ noise: float               # dB                    │
│  └─ aqi: int                   # 0-500 (EPA)          │
│                                                          │
│  SINTÉTICAS:                                            │
│  ├─ greenScore: float          # 0-100 (salubridad)   │
│  ├─ forecasts: [Forecast]      # predicción 6h       │
│  └─ timestamp: iso8601         # última actualiz.    │
│                                                          │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│      ROUTE (Resultado de EcoRuta)                       │
├─────────────────────────────────────────────────────────┤
│  type: "eco" | "alternative" | "fast"                   │
│  waypoints: [lat, lon]         # secuencia de puntos    │
│  distance: float               # km                     │
│  duration: int                 # minutos                │
│  co2Estimate: float            # kg                     │
│  exposureIndex: float          # 0-100 (contamin.)     │
│  mode: "car" | "bus" | "bike" | "walk"                 │
│  summary: string               # descripción corta     │
│                                                          │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│      TEMPORALES (CrateDB vía QuantumLeap)               │
├─────────────────────────────────────────────────────────┤
│  ettrafficflowobserved                                  │
│  ├─ entity_id, entity_type                             │
│  ├─ intensity, averageVehicleSpeed, occupancy         │
│  └─ time_index (timestamp)                             │
│                                                          │
│  ettrafficenvironmentimpact                             │
│  ├─ entity_id, entity_type                             │
│  ├─ NO2Concentration, PM25Concentration, ...          │
│  └─ time_index (timestamp)                             │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

