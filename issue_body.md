1) PESTAÑAS Y FUNCIONALIDADES DETALLADAS

### DASHBOARD
- Definición clara, simple y llamativa de la página web
- KPIs globales en tiempo real: índice medio de calidad del aire, nivel medio de tráfico, número de alertas activas, GreenScore medio de la ciudad
- Panel de alertas activas (superación de umbrales de NO₂, CO₂, ruido, congestión)
- Mapa general Leaflet con markers para cada zona mostrando su estado actual  (color según nivel de contaminación)
- Diagrama UML de entidades en Mermaid renderizado en la página
- Último dato actualizado de cada sensor (timestamp)

### AIRWATCH
- Mapa de calor animado (heatmap Leaflet) de contaminación que evoluciona mostrando datos en tiempo real desde Orion
- Vista 3D inmersiva con ThreeJS: representación de la ciudad de Coruña con "burbujas" o columnas 3D por zona cuya altura/color representa el nivel de contaminación. Debe ser interactiva (rotar, zoom, click en zona para detalle)
- Panel de correlación tráfico ↔ contaminación: gráfico de dispersión (ChartJS) mostrando la relación entre TrafficFlowObserved e índices de contaminación
- Predicciones de calidad del aire para las próximas 6 horas usando
  TrafficEnvironmentImpactForecast
- Indicadores en tiempo real por contaminante: NO₂, CO₂, PM10, PM2.5, ruido (dB)

### ECORUTA
- Mapa Leaflet con selector de origen y destino (click en mapa o búsqueda por nombre de zona)
- Cálculo de al menos 3 rutas alternativas entre origen y destino
- Cada ruta coloreada según su "índice de contaminación" calculado a partir de los TrafficEnvironmentImpact de las zonas que atraviesa:
  - Verde: ruta limpia
  - Amarillo: contaminación moderada
  - Rojo: ruta contaminada
- Panel comparativo de rutas con: distancia estimada, tiempo estimado,
 huella de CO₂ estimada (g/km), índice de contaminación medio
- Funcionalidad "Mejor hora para salir": dado un origen-destino, mostrar un gráfico (ChartJS) con la predicción de contaminación/tráfico por franjas horarias del día, indicando la franja óptima para circular
- Leyenda clara y tooltip en cada ruta al hacer hover

### GREENSCORE
- Mapa choroplético de Coruña: cada barrio coloreado según su GreenScore actual (0-100, calculado combinando: calidad del aire 40%, nivel de ruido 30%, intensidad de tráfico 30%)
- Ranking en tiempo real de barrios de mejor a peor GreenScore con indicador de tendencia (↑ mejorando, ↓ empeorando respecto a hora anterior)
- Radar chart (ChartJS) comparativo: seleccionar hasta 3 barrios y comparar sus dimensiones ambientales (aire, ruido, tráfico, forecasts)
- Predicción del GreenScore para el día siguiente por barrio usando el modelo ML
- Badge/medalla para el barrio más verde del día

### HISTÓRICO
- Selector de zona, métrica y rango de fechas
- Gráfico de líneas (ChartJS) con evolución temporal de cualquier métrica usando datos de QuantumLeap
- Gráfico de barras con comparativa entre zonas para una misma métrica
- Dashboard Grafana embebido (iframe) con paneles preconfigurados de series temporales
- Botón de exportación de datos a CSV

### MI PERFIL
Mantenlo como está ahora mismo, con la foto, el nombre, valores, logros obtenidos...
Además de manter el perfil, mantén también el asistente / ayudante URBS (revisa que funcione al hacerle preguntas tu)
