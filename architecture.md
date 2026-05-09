# Architecture - appCoruna / URBS

## Resumen

La aplicación se organiza como una web Flask con un frontend principal en la raíz del proyecto y un backend que expone JSON para las distintas pestañas. La experiencia visual depende de Leaflet, Chart.js, Three.js, Mermaid y un dashboard Grafana embebido.

## Capas

### Presentación

- `index.html`: interfaz principal servida por Flask y usada por el navegador.
- `static/index.html`: variante estática de apoyo con la misma línea visual.
- `static/style.css` y estilos embebidos del frontend raíz: tema oscuro por defecto y versión clara.

### Interacción

- `static/app.js`: control de mapas, rutas, 3D, charts y cambio de tema en la versión estática.
- La versión raíz integra Vue para pestañas, gráficas, avatar, chat y mapas.

### Backend

- `main.py`: endpoints de dashboard, zones, airwatch, ecoruta, greenscore, chat y explicación.
- `ml_predictor.py`: forecast de entidades de impacto ambiental.
- `simulator.py` y `seed_data.py`: inyección de datos de ejemplo y semilla.

### Servicios externos

- FIWARE Orion: almacenamiento de entidades.
- QuantumLeap y CrateDB: series temporales.
- Grafana: panel analítico embebido.
- Mosquitto e IoT Agent: ingesta simulada.

## Provisioning y observabilidad (reciente)

- Grafana está provisionado desde el repo (`grafana/provisioning` y `grafana/dashboards`) para asegurar availability y reproducibilidad.
- Datasource `cratedb` (tipo `grafana-postgresql-datasource`) apunta a `cratedb:5432` y usa la base `doc` para consultas.
- Seeders: `seed_grafana.py` crea tablas `ettrafficenvironmentimpact` y `ettrafficflowobserved` en CrateDB y las llena con datos sintéticos coherentes con `seed_data.py`.
- La integración local se gestiona con `docker-compose.yml` que monta estos recursos y activa `GF_SECURITY_ALLOW_EMBEDDING`.

## Flujo de datos

1. El simulador o los seeders crean o alimentan entidades FIWARE.
2. `main.py` agrega, normaliza y expone los datos para cada pestaña.
3. El frontend consulta `/api/dashboard`, `/api/airwatch`, `/api/ecoruta`, `/api/greenscore` y `/api/chat`.
4. La interfaz renderiza mapas, comparativas, rankings y gráficas.
5. Grafana aporta una vista temporal embebida en el dashboard.

## Pantallas de la web

### Dashboard

- KPIs globales.
- Alertas activas.
- Estado de sensores.
- Diagrama FIWARE.
- Grafana embebido.

### AirWatch

- Mapa de calor.
- Scatter tráfico/NO2.
- Vista 3D inmersiva.
- Predicción por zona y por hora.

### EcoRuta

- Selector de origen y destino.
- Selector de modo de desplazamiento.
- Cálculo de rutas eco, alternativa y rápida.
- Comparativa de distancia, tiempo, CO2 e índice de contaminación.

### GreenScore

- Ranking por barrios.
- Radar comparativo.
- Mapa de salubridad.

### Histórico

- Series temporales.
- Exportación.
- Grafana integrado.

### Perfil

- Avatar y edición de nombre.
- Logros.
- Reto semanal.
- Asistente URBS.

## Tema y responsive

- El modo oscuro es el punto de partida.
- El modo claro ajusta fondos, tarjetas, texto, inputs y tooltips.
- Los mapas actualizan sus teselas al cambiar el tema.
- El layout se adapta a móvil apilando sidebar, contenido, mapas y chat.

## Riesgos y dependencias

- Si Orion no responde, el backend usa datos sintéticos.
- Grafana necesita el contenedor activo en `localhost:3000`.
- La vista embebida de Grafana funciona mejor cuando el stack se levanta con Docker Compose.