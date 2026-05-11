# PRD - appCoruna / URBS

## 1. Resumen ejecutivo

URBS es la plataforma urbana de appCoruna para A Coruña. Su objetivo es convertir datos de movilidad, calidad del aire, ruido y comportamiento urbano en una interfaz operativa, comprensible y útil para tres perfiles principales: ciudadanía, personal técnico y perfiles de gestión pública. La web combina visualización geográfica, análisis temporal, comparativas de rutas, ranking ambiental, paneles de estado y un asistente conversacional.

La propuesta de valor no es solo mostrar datos, sino ayudar a tomar decisiones: cuándo salir, qué ruta elegir, qué zonas evitar, qué barrios presentan mejor salubridad y qué medidas públicas pueden priorizarse.

## 2. Problema que resuelve

La información urbana suele estar repartida entre distintas fuentes y formatos: sensores IoT, APIs FIWARE, series temporales, dashboards analíticos y visualizaciones separadas. Esa fragmentación dificulta responder preguntas sencillas como:

- ¿Qué zona está más cargada ahora mismo?
- ¿Qué ruta me expone menos a contaminación y ruido?
- ¿Cómo evoluciona la calidad del aire en las próximas horas?
- ¿Qué barrios deberían recibir medidas de mitigación?

URBS centraliza esa información en una experiencia de uso única, con foco en consulta rápida y apoyo a la toma de decisiones.

## 3. Objetivos del producto

### 3.1 Objetivos de negocio y de utilidad

- Ofrecer una interfaz clara para explorar el estado ambiental y de movilidad de la ciudad.
- Reducir la distancia entre los datos técnicos y la interpretación para usuarios no expertos.
- Proporcionar una base visual coherente para decisiones de movilidad sostenible.
- Permitir que el producto funcione incluso si una fuente de datos falla, mediante datos sintéticos o de respaldo.

### 3.2 Objetivos de experiencia

- Mostrar la información principal sin obligar al usuario a navegar por múltiples sistemas.
- Mantener una estética urbana, moderna y consistente en toda la interfaz.
- Asegurar que la app sea usable en escritorio y móvil.
- Hacer que los estados importantes sean visibles de inmediato: alertas, calidad del aire, tráfico y rutas.

## 4. Usuarios objetivo

### 4.1 Ciudadanía

Personas que quieren desplazarse por la ciudad minimizando exposición a tráfico y contaminación. Necesitan respuestas prácticas, comparables y rápidas.

### 4.2 Personal técnico

Perfiles que analizan la evolución de zonas, métricas agregadas, alertas y tendencias temporales. Buscan consistencia de datos y herramientas de revisión.

### 4.3 Gestión pública

Perfiles que necesitan comprender prioridades urbanas, comparar zonas y justificar decisiones relacionadas con movilidad, calidad ambiental y medidas de mitigación.

## 5. Alcance funcional

### 5.1 Dashboard principal

Debe ofrecer una visión global del estado de la ciudad con:

- KPIs agregados de AQI, tráfico, alertas y GreenScore.
- Listado de alertas activas.
- Sincronización reciente de zonas y sensores.
- Diagrama visual de la arquitectura FIWARE.
- Grafana embebido con series temporales relevantes.
- Selector de modo ciudadano/alcalde.
- Indicador de sistema activo.

### 5.2 AirWatch

Debe permitir inspección visual profunda del aire y del tráfico con:

- Mapa de calor o distribución espacial.
- Vista 3D o inmersiva.
- Relación entre tráfico y contaminantes.
- Predicción de las próximas horas por zona.
- Indicadores por zona con evolución y tendencias.

### 5.3 EcoRuta

Debe permitir comparar opciones de desplazamiento entre origen y destino con:

- Selección de origen, destino y modo de transporte.
- Cálculo de al menos tres rutas cuando existen datos suficientes.
- Comparativa entre ruta ecoóptima, alternativa y rápida.
- Diferencias visibles por color, distancia, tiempo, emisiones e índice de exposición.
- Ajuste del cálculo según modo: caminar, bici, bus o coche.

### 5.4 GreenScore

Debe mostrar:

- Ranking de barrios o zonas.
- Comparativa mediante radar o indicador equivalente.
- Mapa de salubridad.
- Predicción o estimación de comportamiento por zona.
- Clasificación fácilmente entendible por personas no técnicas.

### 5.5 Histórico

Debe conservar la capacidad de revisar el pasado reciente de la ciudad mediante:

- Series temporales de variables clave.
- Paneles de evolución.
- Exportación o consulta de snapshots, cuando la implementación lo permita.
- Integración con Grafana para análisis temporal.

### 5.6 Perfil y asistente

Debe incluir:

- Perfil de usuario con nombre, avatar y logros.
- Retos semanales o motivadores de movilidad sostenible.
- Asistente URBS para respuestas contextuales.
- Diferenciación de tono entre modo ciudadano y modo alcalde.

## 6. Requisitos funcionales detallados

### 6.1 Visualización y navegación

- La app debe cargar en modo oscuro por defecto.
- El modo claro debe ser igualmente legible y no romper contrastes.
- La navegación debe ser clara por pestañas: Dashboard, AirWatch, EcoRuta, GreenScore y Perfil.
- La interfaz debe mantener coherencia visual entre módulos.

### 6.2 Datos y resiliencia

- Si Orion no responde, el backend debe seguir devolviendo información usando fallback sintético.
- Si Grafana o CrateDB no están disponibles, la app debe seguir funcionando con el resto de módulos.
- Las vistas deben tolerar ausencia parcial de datos sin romper la pantalla.

### 6.3 Asistente conversacional

- El asistente URBS debe responder a mensajes de usuario.
- Debe soportar los modos ciudadano y alcalde.
- Debe responder en español o inglés según el idioma seleccionado.
- Si el modelo local no responde, debe devolver una respuesta contextual de respaldo en lugar de un mensaje vacío.

### 6.4 Rutas

- EcoRuta debe calcular rutas usando información de zonas y costes ponderados.
- La ruta ecoóptima, la alternativa y la rápida deben diferenciarse visualmente.
- Los resultados deben incluir distancia, tiempo estimado, CO2 estimado y un índice de exposición/polución.

### 6.5 Mapa y responsive

- Los mapas deben adaptarse a pantallas pequeñas.
- El sidebar debe reorganizarse en móvil sin provocar desbordes horizontales.
- El chat flotante debe conservar accesibilidad en pantallas reducidas.

## 7. Requisitos no funcionales

### 7.1 Usabilidad

- El usuario debe entender el estado general en pocos segundos.
- Los textos clave deben ser claros y no demasiado técnicos.
- Las alertas deben ser visibles, pero no invasivas.

### 7.2 Rendimiento

- Las vistas principales deben cargar con rapidez razonable para una demo local.
- El backend debe responder incluso cuando algunas fuentes externas fallan.
- El sistema debe evitar bloqueos largos cuando el asistente conversacional no esté disponible.

### 7.3 Compatibilidad

- Debe funcionar en navegadores modernos.
- Debe adaptarse a resoluciones de escritorio y móvil.
- Debe poder ejecutarse con Docker Compose o localmente con Python.

### 7.4 Mantenibilidad

- La arquitectura debe permitir añadir nuevas zonas, sensores o paneles.
- Los datos de demostración deben estar desacoplados de la capa de presentación.
- Los documentos del proyecto deben describir el sistema sin depender de conocimiento previo.

## 8. Criterios de aceptación

- La web carga correctamente y muestra un dashboard completo.
- El dashboard incluye KPIs, alertas, arquitectura FIWARE y Grafana.
- EcoRuta calcula y representa varias rutas con métricas comparables.
- GreenScore presenta ranking y mapa de salubridad.
- El asistente responde con contenido contextual o fallback útil.
- La experiencia sigue siendo usable si Orion, Grafana o el modelo local fallan temporalmente.
- El diseño sigue siendo claro en escritorio y móvil.

## 9. Fuera de alcance

- Autenticación real de usuarios.
- Gestión de permisos por rol con persistencia segura.
- Optimización de rutas en tiempo real sobre red vial externa oficial.
- Persistencia histórica ilimitada más allá de los datos de demostración y series del stack local.
- Integración con sistemas de producción de la ciudad.

## 10. Supuestos y dependencias

- Se asume que existen datos sintéticos o reales para poblar la demo.
- Se asume que Orion, CrateDB, Grafana y Ollama pueden levantarse localmente cuando el stack completo está activo.
- Se asume que la app puede funcionar degradada con fallback si alguno de esos servicios no responde.

## 11. Evolución esperada

En futuras iteraciones, URBS puede ampliar:

- más sensores y más zonas,
- reglas de priorización pública,
- un modo de análisis para eventos especiales,
- alertas más inteligentes,
- integración con notificaciones o exportaciones,
- y una capa de analítica predictiva más rica.
