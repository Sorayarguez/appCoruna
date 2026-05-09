# appCoruna / URBS

appCoruna es una plataforma web de monitorización urbana para A Coruña. La interfaz principal combina mapas, paneles analíticos, predicciones, rutas sostenibles, ranking ambiental y un asistente conversacional en una sola experiencia.

## Funcionalidad visible en la web

- Dashboard global con KPIs, alertas y diagrama FIWARE.
- AirWatch con mapa, vista 3D, correlación tráfico/contaminación y previsión horaria.
- EcoRuta con selección de origen, destino y modo, más tres rutas comparativas.
- GreenScore con ranking de barrios, radar comparativo y mapa de salubridad.
- Histórico con series temporales y exportación.
- Perfil de usuario con logros y asistente URBS.
- Grafana embebido para visualizar paneles temporales.

## Stack

- Backend: Flask.
- Frontend: HTML, CSS y JavaScript sin framework en la versión raíz.
- Visualización: Leaflet, Chart.js, Three.js y Mermaid.
- Datos: FIWARE Orion, simulación local y fallback sintético.
- Despliegue: Docker Compose para el stack completo.

## Cómo arrancar

1. Instala dependencias Python.
   ```bash
   pip install -r requirements.txt
   ```

2. Levanta el stack completo, incluyendo Grafana.
   ```bash
   docker compose up -d
   ```

3. Si quieres ejecutar solo el backend localmente.
   ```bash
   python main.py
   ```

4. Si quieres datos simulados adicionales.
   ```bash
   python simulator.py
   python ml_predictor.py
   ```

## Endpoints principales

- `/api/zones`: zonas con métricas actuales.
- `/api/dashboard`: KPIs globales y alertas.
- `/api/airwatch`: series de zonas y forecasts.
- `/api/ecoruta`: cálculo de rutas alternativas.
- `/api/greenscore`: ranking y predicción ambiental.
- `/api/chat`: asistente URBS.
- `/api/explain/<zone_id>`: explicación de tráfico/contaminación.
- `/api/ecozones/<zone_id>/activate` y `/api/ecozones/<zone_id>/deactivate`: gestión ZBE.

## Interfaz

- El modo oscuro es el predeterminado.
- El modo claro mantiene contraste adecuado en dashboard, cards, inputs y mapas.
- EcoRuta diferencia visualmente la ruta ecoóptima, la alternativa y la rápida.
- La web es responsiva y se adapta a pantallas pequeñas apilando sidebar, tarjetas, mapas y chat.

## Grafana

- La vista embebida usa el panel `urbs-dashboard` expuesto por Grafana.
- El contenedor Grafana está configurado para permitir embedding y acceso anónimo de solo lectura.
- Si trabajas sin Docker, el panel depende de que el servicio `localhost:3000` esté activo.

## Provisioning y seeders

- Los dashboards y el datasource se provisionan desde `./grafana/provisioning` y `./grafana/dashboards`.
- Hay un seeder `seed_grafana.py` que crea las tablas `ettrafficenvironmentimpact` y `ettrafficflowobserved` en CrateDB (esquema `doc`) y las rellena con datos sintéticos.
- Para poblar CrateDB manualmente:

```bash
docker compose run --rm grafana-seed
```

Esto insertará filas coherentes con las entidades de `seed_data.py` y añadirá algunas alertas de prueba para verificar los paneles.
