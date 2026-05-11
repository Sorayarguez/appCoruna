# Architecture - appCoruna / URBS

## 1. Propósito del sistema

URBS es una plataforma web de monitorización urbana para A Coruña. Su función es integrar datos de tráfico, calidad del aire, ruido, previsión ambiental y recomendaciones de movilidad en una sola interfaz. La arquitectura está pensada para servir una demo funcional, reproducible y visualmente coherente, con degradación controlada si alguna dependencia falla.

El sistema combina cuatro objetivos arquitectónicos:

- mostrar información urbana comprensible y accionable,
- mantener un flujo de datos reproducible a partir de FIWARE, CrateDB y seeders,
- separar la visualización del backend de cálculo,
- y sostener una experiencia usable incluso con servicios parciales.

## 2. Vista de alto nivel

La solución se organiza en estas capas:

- Presentación web.
- Backend Flask.
- Capa de datos y servicios FIWARE.
- Almacenamiento analítico y paneles de observabilidad.
- Servicios auxiliares de simulación, semilla y predicción.

En uso normal, el navegador consume una única web principal. Esa interfaz consulta al backend por JSON y, además, incrusta Grafana para análisis temporal. El backend obtiene datos de Orion o de sus equivalentes sintéticos y calcula agregaciones, rutas y respuestas del asistente.

## 3. Componentes principales

### 3.1 Frontend principal

El frontend principal vive en `index.html` en la raíz del proyecto. Es una aplicación de una sola página basada en HTML, CSS y JavaScript con Vue cargado por CDN. Gestiona:

- navegación por pestañas,
- mapas Leaflet,
- gráficos Chart.js,
- visualización 3D con Three.js,
- un chat flotante,
- el perfil de usuario,
- y la integración visual con Grafana.

Características clave:

- tema oscuro por defecto,
- modo claro alternativo,
- diseño responsive,
- estados vacíos y contenido de fallback,
- interacción directa con los endpoints del backend.

### 3.2 Backend Flask

`main.py` es el backend funcional. Expone endpoints JSON y sirve también el frontend raíz. Sus responsabilidades son:

- consolidar y normalizar datos de zonas,
- consultar Orion cuando existe,
- usar datos sintéticos cuando Orion no responde,
- calcular rutas EcoRuta,
- producir rankings GreenScore,
- devolver series para AirWatch y dashboard,
- gestionar el chat URBS con Ollama o fallback,
- y servir archivos estáticos cuando es necesario.

#### Endpoints principales

- `/api/zones`
- `/api/dashboard`
- `/api/airwatch`
- `/api/ecoruta`
- `/api/greenscore`
- `/api/chat`
- `/api/explain/<zone_id>`
- `/api/ecozones/<zone_id>/activate`
- `/api/ecozones/<zone_id>/deactivate`

### 3.3 FIWARE Orion

Orion es el broker de contexto. Recibe y expone entidades NGSI-LD/NGSI v2 relacionadas con tráfico, impacto ambiental, aire, ruido y sensores. En el repositorio se usan tanto seeders como simuladores para alimentar Orion con datos consistentes.

### 3.4 MongoDB

Se usa como base auxiliar del ecosistema FIWARE, principalmente para Orion e IoT Agent.

### 3.5 IoT Agent UL y Mosquitto

El IoT Agent y Mosquitto están presentes para sostener una cadena simulada de telemetría IoT. Esto permite que la arquitectura represente una ingestión realista aunque el uso principal de la demo vaya por seeders y simulación local.

### 3.6 CrateDB y QuantumLeap

CrateDB es el almacenamiento de series temporales para análisis y dashboarding. QuantumLeap actúa como capa de persistencia temporal para datos de contexto.

Los paneles de Grafana consultan tablas creadas por `seed_grafana.py`, especialmente:

- `ettrafficenvironmentimpact`
- `ettrafficflowobserved`

### 3.7 Grafana

Grafana aporta una capa de observabilidad temporal y análisis histórico embebido en la web. Está provisionado desde el repo para que el panel y el datasource se creen de forma reproducible.

Características relevantes:

- embedding activado,
- tema por defecto oscuro,
- acceso anónimo de solo lectura para la demo,
- dashboards y datasource provisionados por archivos del repositorio.

### 3.8 Ollama

Ollama da soporte al asistente URBS. El backend envía prompts al endpoint de generación para producir respuestas dinámicas. Si el modelo no responde, el backend devuelve una respuesta contextual de respaldo para no romper la UX.

### 3.9 Seeders y simulación

- `seed_data.py` alimenta Orion con zonas, métricas y forecasts.
- `seed_grafana.py` crea y rellena CrateDB con series temporales.
- `simulator.py` y `ml_predictor.py` complementan la generación de datos y forecasts.

## 4. Flujo de datos

### 4.1 Flujo principal de consulta

1. El usuario abre la web en el navegador.
2. El frontend carga la interfaz principal.
3. La UI llama a `/api/dashboard`, `/api/zones`, `/api/airwatch`, `/api/ecoruta`, `/api/greenscore` o `/api/chat` según la pantalla.
4. El backend consulta Orion o usa datos sintéticos.
5. El backend devuelve JSON normalizado.
6. El frontend renderiza mapas, indicadores, rankings, rutas o mensajes.
7. Grafana se incrusta para la vista temporal.

### 4.2 Flujo de semilla y observabilidad

1. `seed_grafana.py` espera a que CrateDB esté disponible.
2. Crea tablas temporales y carga filas sintéticas.
3. Grafana arranca con el datasource ya preparado.
4. El dashboard embebido puede mostrar series útiles desde el primer arranque.

### 4.3 Flujo del asistente

1. El usuario escribe en el chat.
2. El frontend envía el mensaje a `/api/chat`.
3. `main.py` construye un prompt según modo e idioma.
4. Intenta llamar a Ollama.
5. Si falla, aplica fallback contextual.

## 5. Frontend por pantallas

### 5.1 Dashboard

Contiene:

- bienvenida,
- KPIs,
- alertas,
- sincronización reciente,
- diagrama FIWARE,
- y panel Grafana embebido.

También concentra la identidad visual principal de la app.

### 5.2 AirWatch

Incluye un mapa principal, una representación 3D y vistas analíticas para correlacionar tráfico, contaminación y predicción.

### 5.3 EcoRuta

Construye rutas sobre un grafo de zonas. El backend asigna costes según:

- distancia,
- contaminación,
- tráfico,
- modo de transporte,
- y penalizaciones específicas para bus, bici o caminata.

### 5.4 GreenScore

Ordena zonas por salubridad usando una métrica agregada y complementa con comparativas visuales.

### 5.5 Histórico

La vista histórica reusa datos temporales y, cuando corresponde, paneles Grafana.

### 5.6 Perfil

El perfil incluye avatar, puntos, retos, logros y el chatbot.

## 6. Diseño de backend

### 6.1 Normalización de datos

`main.py` convierte distintos formatos de entidades en una salida común para el frontend. Eso permite que la UI consuma zonas homogéneas aunque la fuente cambie.

### 6.2 Estrategia de fallback

La aplicación no depende de una sola fuente para mostrar algo útil. Si Orion falla, se generan zonas sintéticas. Si Ollama falla, se construyen respuestas contextuales. Si no hay forecasts, se sintetizan por hora.

### 6.3 Cálculo de rutas

EcoRuta usa grafos ponderados y Dijkstra. Existen perfiles por modo:

- coche,
- bus,
- bici,
- caminar.

Además, el modo bus favorece nodos principales y corredores de transporte, evitando zigzags absurdos.

### 6.4 Criterios de coste

El coste combina distancia, salubridad y tráfico. En bus hay penalizaciones o bonificaciones adicionales por hub, salto corto y conectividad.

## 7. Tema visual y responsive

### 7.1 Tema

- Dark mode como base.
- Light mode para compatibilidad visual y legibilidad.
- Ajustes de contraste en mapas, inputs, tarjetas y chats.

### 7.2 Responsive

- Sidebar apilada en móvil.
- Grid de tarjetas que cae a una columna en pantallas pequeñas.
- Mapas con alturas adaptadas.
- Chat flotante reubicado para no tapar contenido.

### 7.3 Diseño

La interfaz usa un lenguaje visual tipo glassmorphism con acentos cyan/verde para reforzar la identidad urbana y tecnológica.

## 8. Dependencias y puertos

### 8.1 Servicios del `docker-compose.yml`

- `mongo` en `27017`
- `orion` en `1026`
- `iot-agent` en `4041` y `7896`
- `mosquitto` en `1883`
- `cratedb` en `4200` y `5432`
- `quantumleap` en `8668`
- `grafana` en `3000`
- `ollama` en `11434`
- `backend` en `8000`
- `frontend` en `80`

### 8.2 Observaciones operativas

- Grafana depende de CrateDB y del seeder.
- El backend depende funcionalmente de Orion, QuantumLeap y Ollama, pero mantiene fallback si alguno falla.
- El frontend puede cargarse por Nginx o directamente desde Flask según el modo de ejecución.

## 9. Riesgos y mitigaciones

### 9.1 Caída de Orion

Mitigación: fallback sintético en backend.

### 9.2 Caída de Ollama

Mitigación: respuestas heurísticas contextuales y timeouts más cortos.

### 9.3 Grafana sin datos

Mitigación: `seed_grafana.py` crea tablas y filas antes de arrancar Grafana.

### 9.4 Inconsistencia de datos

Mitigación: `seed_data.py`, `seed_grafana.py` y `main.py` comparten modelo de zonas.

### 9.5 Requerimientos visuales en móvil

Mitigación: media queries específicas para sidebar, mapas, chat y tarjetas.

## 10. Decisiones de diseño

- El backend se mantiene sencillo y explícito para facilitar mantenimiento.
- La UI se concentra en un único archivo principal para simplificar despliegue y demo.
- Los datos sintéticos son una parte consciente del sistema y no un error de implementación.
- Grafana se usa como complemento analítico, no como sustituto de la app principal.

## 11. Expansión futura

- Separar el frontend en módulos si crece el alcance.
- Sustituir parte de los datos sintéticos por conectores reales.
- Añadir autenticación y preferencias de usuario.
- Mejorar la semántica del asistente con contexto conversacional persistente.
- Introducir alertas configurables y exportación de informes.
