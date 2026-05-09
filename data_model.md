# Data Model - appCoruna / URBS

## Modelo lógico de la web

La aplicación trabaja con zonas agregadas, datos FIWARE y derivados analíticos que alimentan mapas, tablas, gráficas y rankings.

## Entidades principales

### Zone

Zona operativa o barrio de A Coruña.

Campos relevantes:

- `id`
- `name`
- `lat`, `lon`
- `no2`, `pm25`, `pm10`, `co2`, `noise`, `traffic`
- `aqi`
- `greenScore`
- `timestamp`

### TrafficFlowObserved

Flujo de tráfico observado en una vía o tramo.

Campos relevantes:

- `intensity`
- `averageVehicleSpeed`
- `occupancy`
- `refRoadSegment`
- `refDevice`

### TrafficEnvironmentImpact

Medición ambiental asociada al impacto del tráfico.

Campos relevantes:

- `NO2Concentration`
- `PM25Concentration`
- `PM10Concentration`
- `CO2Concentration`
- `noiseLevel`
- `aqi`
- `greenScore`
- `location`
- `refTrafficFlowObserved`

### TrafficEnvironmentImpactForecast

Proyección temporal del impacto ambiental.

Campos relevantes:

- `forecastHour`
- `NO2Concentration`
- `airQualityIndex`
- `trafficIntensity`
- `hoursAhead`
- `refTrafficFlowObserved`
- `refTrafficEnvironmentImpact`

### AirQualityObserved

Entidad consolidada de calidad del aire usada en el diagrama y los indicadores.

Campos relevantes:

- `NO2`
- `PM2.5`
- `PM10`
- `CO2`
- `airQualityIndex`

### NoiseLevelObserved

Entidad para el ruido ambiental.

Campos relevantes:

- `loudness`
- `dateObserved`

### Device y DeviceModel

Metadatos del sensor o dispositivo que origina los datos.

Campos relevantes:

- `id`
- `category`
- `refDeviceModel`
- `brandName`

### ItemFlowObserved

Flujo de peatones o ciclistas, incluido como referencia funcional del dominio.

## Relaciones

- `TrafficEnvironmentImpact` se relaciona con `TrafficFlowObserved` mediante `refTrafficFlowObserved`.
- `TrafficEnvironmentImpactForecast` se relaciona con la entidad de impacto y con el flujo base.
- `Device` se enlaza con `DeviceModel` para metadatos de sensor.
- EcoRuta usa las zonas derivadas para calcular trayectorias y comparar costes.

## Derivaciones

- `aqi` se calcula a partir de contaminantes clave.
- `greenScore` pondera aire, ruido y tráfico.
- Las rutas usan un color fijo por tipo de ruta en backend y se muestran en el mapa.
- Las métricas de gráficos y rankings se sirven desde la agregación del backend.

## Esquema persistente en CrateDB (usado por Grafana)

- Tabla `ettrafficenvironmentimpact` (columnas principales):
	- `time_index TIMESTAMP WITH TIME ZONE`
	- `entity_id TEXT`
	- `zone_name TEXT`
	- `longitude DOUBLE PRECISION`, `latitude DOUBLE PRECISION`
	- `NO2Concentration`, `PM25Concentration`, `PM10Concentration`, `CO2Concentration` (DOUBLE)
	- `noiseLevel`, `aqi`, `greenScore`

- Tabla `ettrafficflowobserved` (columnas principales):
	- `time_index TIMESTAMP WITH TIME ZONE`, `entity_id`, `zone_name`, `longitude`, `latitude`
	- `intensity`, `averageVehicleSpeed`, `occupancy`

Estas tablas se crean y rellenan por `seed_grafana.py` y son consultadas por los paneles provisionados del dashboard `urbs-dashboard`.