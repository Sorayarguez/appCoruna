# URBS - Urban Real-time Biosphere System (A Coruña)

URBS es una aplicación integral basada en FIWARE para la monitorización ambiental urbana, correlacionando el tráfico vehicular con la calidad del aire en tiempo real. 

## 🏗 Arquitectura y Módulos

El sistema está compuesto por 3 módulos principales integrados:

1. **GreenRoute**: Cálculo de rutas saludables basado en el índice de calidad del aire (NO2 y PM2.5).
2. **UrbanPulse**: Panel de control con gráficas correlacionadas de tráfico/contaminación y explicaciones generadas con fallback local cuando no hay servicio de IA disponible.
3. **EcoZones**: Gestión dinámica de Zonas de Bajas Emisiones (ZBE) mediante un sistema de alertas.

## 💾 Smart Data Models (NGSI v2)
Se implementan 4 modelos de datos clave, enlazados mediante referencias (Relationships):
- `TrafficFlowObserved`: Registra intensidad, velocidad y ocupación de las vías.
- `ItemFlowObserved`: Registra el paso de peatones o ciclistas.
- `TrafficEnvironmentImpact`: Registra mediciones ambientales actuales y referencia (`refTrafficFlowObserved`) al tramo que lo origina.
- `TrafficEnvironmentImpactForecast`: Proyecciones futuras (+1h, +2h, +4h) originadas por el modelo de ML.

*(Consulta el fichero `ngsi_entities.json` para ver ejemplos completos y relaciones).*

## 🚀 Despliegue (Paso a Paso)

Todo el proyecto está dockerizado para facilitar el despliegue de todos los componentes FIWARE (Orion, IoT Agent, QuantumLeap, CrateDB), Grafana y el Backend/Frontend personalizado.

1. **Clonar el repositorio y ubicarse en la carpeta**
   ```bash
   cd /home/soraya/xdei/P3/appCoruna
   ```

2. **Levantar todos los contenedores con Docker Compose**
   ```bash
   docker compose up -d
   ```
   *Nota: La primera vez descargará bastantes imágenes oficiales de FIWARE y BDs.*

3. **Instalar dependencias de Python** (para lanzar los simuladores localmente):
   ```bash
   pip install -r requirements.txt
   ```

4. **Iniciar el Simulador IoT (Ingesta de datos)**
   El simulador registrará los servicios y dispositivos, y comenzará a inyectar datos sintéticos para A Coruña mediante MQTT (tráfico) y HTTP (ambiente).
   ```bash
   python simulator.py
   ```

5. **Iniciar el modelo predictivo ML (En otra terminal)**
   Este script lee el estado actual de Orion y sube nuevas entidades de tipo "Forecast" simulando proyecciones futuras.
   ```bash
   python ml_predictor.py
   ```

## 🌍 Acceso e Interfaz de Usuario

- **Frontend Principal (Leaflet, Three.js, Chart.js)**: [http://localhost](http://localhost)
- **API FastAPI (Swagger UI)**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Grafana (Dashboard Analítico)**: [http://localhost:3000](http://localhost:3000) (Importar el fichero `grafana_dashboard.json`).

## ⚙️ Decisiones Tecnológicas Destacadas

- **Backend**: FastAPI por su extrema velocidad y simplicidad para mapear rutas RESTful.
- **Frontend**: Vanilla HTML5/JS/CSS3 usando CSS Grid, variables CSS, glassmorphism, y sin frameworks bloqueantes para una PWA ligera y visualmente impactante.
- **Visualización 3D**: Uso de `THREE.Points` para renderizar volumétricamente una simulación de partículas de polución.
- **IA Generativa**: El backend usa respuestas locales y solo consume un servicio externo de IA si se configura explícitamente mediante `OLLAMA_URL`.
