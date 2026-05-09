# PRD - appCoruna / URBS

## Objetivo

Construir una plataforma urbana para A Coruña que centralice monitorización ambiental, movilidad, predicción y consulta ciudadana sobre el estado de la ciudad.

## Usuarios objetivo

- Ciudadanía que quiere moverse con menos exposición a tráfico y contaminación.
- Personal técnico y de gestión que necesita una lectura rápida de la ciudad.
- Usuarios avanzados que comparan barrios, horas y rutas antes de desplazarse.

## Problemas que resuelve

- La información está dispersa entre sensores, mapas, series temporales y dashboards.
- Escoger una ruta saludable requiere comparar varias opciones y su impacto.
- Hace falta entender el contexto ambiental de cada barrio y su evolución.

## Alcance funcional

- Dashboard principal con KPIs, alertas, estado de sensores y arquitectura FIWARE.
- AirWatch con mapa de calor, vista 3D, scatter tráfico/NO2 y predicción de 6 horas.
- EcoRuta con origen, destino, modo y tres rutas comparativas coloreadas.
- GreenScore con ranking, radar de comparación y mapa de salubridad.
- Histórico con evolución de métricas, exportación y Grafana embebido.
- Perfil con logros, avatar, retos y asistente URBS.

## Requisitos de interfaz

- El tema oscuro debe ser el estado inicial.
- El tema claro debe ser legible en textos, tarjetas, inputs, tablas y bloques de mapa.
- Los mapas deben actualizarse al cambiar de tema.
- Grafana debe mostrarse embebido al abrir la web siempre que el stack esté levantado.
- La interfaz debe funcionar bien en móvil y escritorio.

## Notas de implementación recientes

- Grafana se provisiona con dashboards y datasource en `./grafana/provisioning` y `./grafana/dashboards`.
- Se añadió un seeder `seed_grafana.py` que puebla `CrateDB` (esquema `doc`) con series temporales coherentes y filas de prueba para alertas.
- La web arranca por defecto en modo oscuro (`GF_USERS_DEFAULT_THEME=dark` y lógica en `index.html`).
- `EcoRuta` asegura ahora devolver 3 rutas cuando hay datos suficientes y usa paleta consistente: `#22c55e` (eco), `#f59e0b` (alternativa), `#3b82f6` (rápida).

## Requisitos funcionales clave

- EcoRuta debe mostrar al menos tres rutas cuando hay datos suficientes.
- Las rutas rápida y alternativa deben distinguirse visualmente.
- El usuario debe poder cambiar el modo de transporte.
- El panel histórico debe seguir existiendo junto al resto de pestañas.
- El asistente URBS debe seguir disponible en la pestaña de perfil.

## Criterios de aceptación

- La web carga directamente en modo oscuro.
- El cambio a modo claro no reduce la legibilidad del dashboard.
- Las rutas se calculan y se renderizan con comparativa y mapa.
- Grafana aparece embebido y accesible dentro de la interfaz principal.
- En móvil, sidebar y contenido se reordenan sin desbordar horizontalmente.

## Fuera de alcance

- Autenticación real de usuarios.
- Persistencia histórica de largo plazo fuera de las fuentes ya integradas.
- Optimización de rutas sobre red vial externa en tiempo real.