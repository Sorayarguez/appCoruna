# Data Model - appCoruna / URBS

## 1. Propósito del modelo de datos

URBS combina datos de contexto FIWARE, agregaciones operativas del backend, series temporales en CrateDB y derivados de cálculo para visualización. Este documento describe el modelo lógico y el modelo persistente que usan la aplicación y los seeders del proyecto.

El objetivo es que cualquier persona del equipo entienda:

- qué entidades existen,
- qué representa cada campo,
- cómo se relacionan entre sí,
- qué datos se guardan en Orion,
- qué datos se materializan en CrateDB,
- y qué derivaciones calcula el backend a partir de ellas.

## 2. Capas del modelo

### 2.1 Modelo de contexto FIWARE

Es la capa principal de datos operativos. Incluye entidades como tráfico, impacto ambiental, calidad del aire, ruido, dispositivos y forecasts. Vive en Orion.

### 2.2 Modelo agregado de la aplicación

El backend no entrega directamente las entidades crudas al frontend. Normaliza y agrega los valores en estructuras como `zones`, `dashboard`, `forecasts`, `routes` y `ranked`.

### 2.3 Modelo temporal analítico

CrateDB almacena series temporales de tráfico e impacto ambiental para el dashboard de Grafana.

### 2.4 Modelo sintético de respaldo

Cuando faltan datos reales, el backend construye zonas sintéticas con una estructura idéntica a la que espera la interfaz.

## 3. Entidad agregada principal: Zone

`Zone` es la unidad lógica que la interfaz usa en casi todas las pantallas. Representa un barrio, zona o nodo urbano con medidas consolidadas.

### 3.1 Campos

- `id`: identificador lógico de la zona.
- `name`: nombre legible.
- `lat`, `lon`: coordenadas geográficas en WGS84.
- `no2`, `pm25`, `pm10`, `co2`, `noise`, `traffic`: métricas instantáneas o agregadas.
- `aqi`: índice de calidad del aire.
- `greenScore`: puntuación sintética de salubridad urbana.
- `timestamp`: momento de referencia de la lectura.

### 3.2 Uso

`Zone` alimenta:

- el mapa principal,
- el ranking GreenScore,
- la comparativa de rutas,
- la pantalla AirWatch,
- y los resúmenes del dashboard.

### 3.3 Origen

Se construye desde Orion cuando existen entidades válidas. Si no, se crea desde `synthetic_zone_data()`.

## 4. Entidades FIWARE principales

### 4.1 TrafficFlowObserved

Representa el flujo de tráfico observado en un tramo o punto urbano.

#### Campos principales

- `id`: URI de entidad.
- `type`: `TrafficFlowObserved`.
- `name`: nombre de la zona o tramo.
- `location`: punto geográfico en `geo:json`.
- `intensity`: intensidad del tráfico.
- `averageVehicleSpeed`: velocidad media.
- `occupancy`: ocupación del tramo.
- `laneDirection`: dirección del carril.
- `vehicleType`: tipo de vehículo predominante.
- `TimeInstant` o `dateObserved`: instante de observación.
- `refRoadSegment`: referencia al tramo de carretera asociado, cuando existe.

#### Significado de los campos

- `intensity` mide cuántos vehículos circulan.
- `averageVehicleSpeed` ayuda a interpretar congestión.
- `occupancy` representa saturación relativa.
- `location` permite colocar el dato en mapa.

#### Origen en el proyecto

- `seed_data.py` crea una entidad por zona.
- `ml_predictor.py` genera forecasts asociados a esta entidad.
- `seed_grafana.py` lo materializa en CrateDB para análisis temporal.

### 4.2 TrafficEnvironmentImpact

Representa el impacto ambiental asociado al tráfico en una zona.

#### Campos principales

- `id`
- `type`: `TrafficEnvironmentImpact`
- `name`
- `location`
- `NO2Concentration`
- `PM25Concentration`
- `PM10Concentration`
- `CO2Concentration`
- `noiseLevel`
- `aqi`
- `greenScore`
- `TimeInstant` o `dateObserved`
- `refTrafficFlowObserved`

#### Significado

- `NO2Concentration`: concentración de dióxido de nitrógeno.
- `PM25Concentration`: partículas finas PM2.5.
- `PM10Concentration`: partículas PM10.
- `CO2Concentration`: CO2 estimado o derivado.
- `noiseLevel`: nivel acústico ambiental.
- `aqi`: índice global de calidad del aire.
- `greenScore`: métrica sintética de salubridad combinando tráfico, ruido y contaminantes.

#### Origen

- `seed_data.py` crea una entidad por zona.
- `ml_predictor.py` actualiza forecasts relacionados.
- `seed_grafana.py` crea la tabla temporal equivalente.

### 4.3 TrafficEnvironmentImpactForecast

Predicción del impacto ambiental para horas futuras.

#### Campos principales

- `id`
- `type`: `TrafficEnvironmentImpactForecast`
- `name`
- `forecastHour`
- `NO2Concentration`
- `PM25Concentration`
- `airQualityIndex`
- `trafficIntensity`
- `validFrom`
- `validTo`
- `refTrafficFlowObserved`
- `refTrafficEnvironmentImpact`

#### Uso

- AirWatch muestra una predicción de 6 horas.
- El backend usa estas previsiones o, si no existen, las genera sintéticamente.

#### Origen

- `seed_data.py` crea forecasts de 1 a 6 horas.
- `ml_predictor.py` genera forecasts recurrentemente.
- `main.py` puede sintetizar forecasts si no hay entidades en Orion.

### 4.4 AirQualityObserved

Entidad consolidada de calidad del aire.

#### Campos principales

- `NO2`
- `PM2.5`
- `PM10`
- `CO2`
- `airQualityIndex`
- `airQualityLevel`
- `location`
- `TimeInstant`

#### Uso

Sirve como visión agregada de calidad del aire para visualizaciones y referencias de dominio.

### 4.5 NoiseLevelObserved

Entidad de ruido ambiental.

#### Campos principales

- `LAeq`
- `LAmax`
- `LAmin`
- `location`
- `TimeInstant`

#### Uso

Complementa la lectura de impacto ambiental, ya que el ruido forma parte del `greenScore` y de las alertas.

### 4.6 ItemFlowObserved

Flujo de peatones o ciclistas.

#### Campos principales

- `itemType`
- `intensity`
- `cyclistCount`
- `location`
- `refRoadSegment`
- `TimeInstant` o `dateObserved`

#### Uso

Extiende el modelo hacia movilidad activa y permite hablar de afluencia no motorizada.

### 4.7 Device

Representa un dispositivo sensor o fuente de datos.

#### Campos principales

- `id`
- `type`: `Device`
- `category`
- `location`
- `refDeviceModel`

#### Uso

Permite rastrear el origen de las mediciones y relacionarlo con el modelo físico.

### 4.8 DeviceModel

Describe el modelo de dispositivo o sensor.

#### Campos principales

- `id`
- `type`: `DeviceModel`
- `brandName`
- atributos de fabricante o especificación técnica

#### Uso

Se usa como metadato de trazabilidad del sensor.

## 5. Relaciones entre entidades

### 5.1 Impacto y tráfico

`TrafficEnvironmentImpact.refTrafficFlowObserved` enlaza el estado ambiental con el tramo de tráfico que lo produce o condiciona.

### 5.2 Forecasts

`TrafficEnvironmentImpactForecast.refTrafficEnvironmentImpact` apunta a la entidad de impacto base, y `refTrafficFlowObserved` enlaza con el flujo de tráfico correspondiente.

### 5.3 Dispositivos

`Device.refDeviceModel` vincula el dispositivo con su modelo.

### 5.4 Movilidad activa

`ItemFlowObserved` puede enlazarse con un `refRoadSegment` para analizar afluencia de peatones o ciclistas en el mismo contexto de movilidad.

## 6. Derivaciones calculadas por la aplicación

### 6.1 `aqi`

Calculado o ajustado a partir de contaminantes principales, normalmente con peso mayor para NO2 y PM2.5.

### 6.2 `greenScore`

Puntuación sintética de 0 a 100 que combina:

- NO2,
- PM2.5,
- ruido,
- tráfico.

Su objetivo no es científico sino orientado a UX y comparabilidad.

### 6.3 `routes`

EcoRuta construye rutas con:

- distancia aproximada,
- tiempo estimado,
- CO2 estimado,
- índice de contaminación del recorrido,
- puntos geográficos para dibujar la ruta.

### 6.4 `bestHours`

El backend calcula horas recomendadas para viajar en función del ritmo diario esperado.

### 6.5 `ranked`

GreenScore ordena las zonas según `greenScore` descendente y añade metadatos como posición, tendencia y predicción.

## 7. Modelo temporal en CrateDB

CrateDB guarda series temporales que Grafana consulta para paneles históricos y comparativas.

### 7.1 Tabla `ettrafficenvironmentimpact`

#### Columnas

- `time_index TIMESTAMP WITH TIME ZONE`
- `entity_id TEXT`
- `zone_name TEXT`
- `longitude DOUBLE PRECISION`
- `latitude DOUBLE PRECISION`
- `NO2Concentration DOUBLE PRECISION`
- `PM25Concentration DOUBLE PRECISION`
- `PM10Concentration DOUBLE PRECISION`
- `CO2Concentration DOUBLE PRECISION`
- `noiseLevel DOUBLE PRECISION`
- `aqi DOUBLE PRECISION`
- `greenScore DOUBLE PRECISION`

#### Uso

Permite ver cómo evolucionan los indicadores ambientales por zona.

### 7.2 Tabla `ettrafficflowobserved`

#### Columnas

- `time_index TIMESTAMP WITH TIME ZONE`
- `entity_id TEXT`
- `zone_name TEXT`
- `longitude DOUBLE PRECISION`
- `latitude DOUBLE PRECISION`
- `intensity DOUBLE PRECISION`
- `averageVehicleSpeed DOUBLE PRECISION`
- `occupancy DOUBLE PRECISION`

#### Uso

Permite comparar congestión, velocidad y ocupación del tráfico por tramo o zona.

### 7.3 Relación con Grafana

Las tablas se crean y rellenan con `seed_grafana.py` y se consultan desde el dashboard `urbs-dashboard` provisionado en el repositorio.

## 8. Modelo sintético de respaldo

Cuando no hay respuesta real desde Orion o CrateDB, el backend genera datos sintéticos con la misma estructura que esperan el frontend y los dashboards.

### 8.1 Campos garantizados

El fallback de zona siempre intenta entregar:

- `id`
- `name`
- `lat`
- `lon`
- `no2`
- `pm25`
- `pm10`
- `co2`
- `noise`
- `traffic`
- `aqi`
- `greenScore`
- `timestamp`

### 8.2 Objetivo del fallback

- evitar pantallas vacías,
- mantener la demo operativa,
- y garantizar consistencia entre módulos aunque la fuente principal falle.

## 9. Convenciones de datos

- Coordenadas siempre en WGS84 con longitud primero en `geo:json`.
- Identificadores de zona en minúscula o camelCase según el contexto.
- Tiempos en UTC.
- Lecturas ambientales expresadas en valores numéricos simples.
- El frontend trabaja con valores ya normalizados por el backend.

## 10. Calidad y coherencia

### 10.1 Coherencia entre seeders

- `seed_data.py` y `seed_grafana.py` comparten el mismo conjunto de zonas.
- Los nombres y coordenadas deben mantenerse alineados entre documentos, Orion y CrateDB.

### 10.2 Coherencia con el backend

- `main.py` conoce la estructura de `Zone` y la reconstituye desde Orion.
- El frontend espera campos estables en la forma agregada.

### 10.3 Riesgo de divergencia

Si se añaden nuevas zonas o atributos, deben actualizarse conjuntamente:

- `seed_data.py`
- `seed_grafana.py`
- `main.py`
- `data_model.md`
- y, si aplica, los dashboards de Grafana.

## 11. Casos de uso de lectura

### 11.1 Dashboard

Consume `Zone` y entidades agregadas para KPIs, alertas y sincronización.

### 11.2 AirWatch

Consume `Zone`, forecasts y métricas ambientales para mapa y visualización temporal.

### 11.3 EcoRuta

Usa `Zone` como grafo base para calcular rutas y comparar modos.

### 11.4 GreenScore

Ordena zonas por `greenScore` y usa campos derivados de calidad del aire y tráfico.

### 11.5 Grafana

Consulta las tablas de CrateDB para visualización temporal.

## 12. Evolución futura del modelo

En una evolución posterior se podrían añadir:

- sensores por calle o distrito,
- entidades de eventos urbanos,
- medidores de bicicleta y transporte público,
- alertas con severidad y expiración,
- preferencias de usuario,
- y un modelo histórico de largo plazo para comparar temporadas.
