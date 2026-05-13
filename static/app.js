const THEME_KEY = 'appcoruna-theme';
const LIGHT_THEME = 'light';
const DARK_THEME = 'dark';

function setMermaidTheme(theme) {
    mermaid.initialize({ startOnLoad: true, theme: theme === LIGHT_THEME ? 'default' : 'dark' });
}

function applyTheme(theme) {
    document.body.classList.toggle('light-mode', theme === LIGHT_THEME);
    document.body.classList.toggle('dark-mode', theme !== LIGHT_THEME);
    const toggle = document.getElementById('theme-toggle');
    if (toggle) {
        toggle.textContent = theme === LIGHT_THEME ? 'Modo oscuro' : 'Modo claro';
    }
    setMermaidTheme(theme);
}

const savedTheme = localStorage.getItem(THEME_KEY) || DARK_THEME;
applyTheme(savedTheme === LIGHT_THEME ? LIGHT_THEME : DARK_THEME);

// Global State
const state = {
    corunaCoords: [43.3623, -8.4115],
    theme: savedTheme === LIGHT_THEME ? LIGHT_THEME : DARK_THEME,
    zones: [],
    routes: [],
    routeLayers: null,
    ecorutaChart: null,
    maps: {}
};

document.getElementById('theme-toggle').addEventListener('click', () => {
    state.theme = state.theme === LIGHT_THEME ? DARK_THEME : LIGHT_THEME;
    localStorage.setItem(THEME_KEY, state.theme);
    applyTheme(state.theme);
    Object.values(state.maps).forEach(map => {
        map.eachLayer(layer => {
            if (layer instanceof L.TileLayer) {
                layer.setUrl(getTileUrl());
            }
        });
    });
    Object.values(state.maps).forEach(map => map && map.invalidateSize());
});

// Tab switching
document.querySelectorAll('.nav-links li').forEach(li => {
    li.addEventListener('click', () => {
        document.querySelectorAll('.nav-links li').forEach(el => el.classList.remove('active'));
        li.classList.add('active');
        const target = li.getAttribute('data-target');
        document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
        document.getElementById(target).classList.add('active');
        
        // Trigger resize events for maps/charts to render correctly
        window.dispatchEvent(new Event('resize'));
    });
});

// Initialize Maps
const mapOptions = {
    center: state.corunaCoords,
    zoom: 13,
    zoomControl: false,
    attributionControl: false
};

const tileLayer = 'https://{s}.basemaps.cartocdn.com/{theme}/{z}/{x}/{y}{r}.png';

function getTileUrl() {
    return state.theme === LIGHT_THEME
        ? tileLayer.replace('{theme}', 'light_all')
        : tileLayer.replace('{theme}', 'dark_all');
}

function buildMap(mapId) {
    const map = L.map(mapId, mapOptions);
    L.tileLayer(getTileUrl()).addTo(map);
    state.maps[mapId] = map;
    return map;
}

// Dashboard Map
const dashMap = buildMap('dashboard-map');

// AirWatch Map (Heatmap)
const airMap = buildMap('airwatch-map');

// EcoRuta Map
const ecoMap = buildMap('ecoruta-map');

// GreenScore Map
const greenMap = buildMap('greenscore-map');

// Add random markers to dashMap for demo
const zones = [
    { name: "Plaza de Lugo", coords: [43.367, -8.405], state: "good" },
    { name: "Ronda de Nelle", coords: [43.360, -8.418], state: "bad" },
    { name: "Cuatro Caminos", coords: [43.355, -8.402], state: "warning" }
];

zones.forEach(z => {
    const color = z.state === "good" ? "green" : z.state === "bad" ? "red" : "orange";
    L.circleMarker(z.coords, {
        radius: 8, fillColor: color, color: "#fff", weight: 1, opacity: 1, fillOpacity: 0.8
    }).addTo(dashMap).bindPopup(`<b>${z.name}</b><br>Estado: ${z.state}`);
});

const routePalette = {
    'ruta ecoóptima': '#22c55e',
    'ruta ecooptima': '#22c55e',
    'ruta alternativa': '#f59e0b',
    'ruta rápida': '#3b82f6',
    'ruta rapida': '#3b82f6'
};

function normalizeText(value) {
    return (value || '').toString().trim().toLowerCase();
}

function resolveZone(value) {
    const normalized = normalizeText(value);
    if (!normalized) {
        return null;
    }
    return state.zones.find(zone => {
        const id = normalizeText(zone.id);
        const name = normalizeText(zone.name);
        return id === normalized || name === normalized || name.includes(normalized) || id.includes(normalized);
    }) || null;
}

function clearRouteLayers() {
    if (state.routeLayers) {
        state.routeLayers.clearLayers();
    } else {
        state.routeLayers = L.layerGroup().addTo(ecoMap);
    }
}

function renderRouteResults(routes, originZone, destZone) {
    const container = document.getElementById('route-comparative');
    if (!routes.length) {
        container.innerHTML = '<p>No se encontraron rutas para esos valores.</p>';
        return;
    }

    container.innerHTML = routes.map(route => `
        <article class="route-card glass" style="border-left: 4px solid ${route.color}; padding: 0.9rem; margin-top: 0.75rem;">
            <div style="display:flex;justify-content:space-between;gap:1rem;align-items:center;">
                <strong>${route.name}</strong>
                <span style="color:${route.color};font-weight:700;">${route.label}</span>
            </div>
            <p style="margin-top:0.4rem; color: var(--muted-color);">${originZone.name} → ${destZone.name}</p>
            <div style="display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:0.4rem;margin-top:0.75rem;">
                <span>Distancia: ${route.distKm} km</span>
                <span>Tiempo: ${route.timeMin} min</span>
                <span>CO₂: ${route.co2g} g</span>
                <span>Índice: ${route.pollutionIndex}</span>
            </div>
        </article>
    `).join('');
}

function renderBestHoursChart(bestHours) {
    const ctx = document.getElementById('ecoruta-time').getContext('2d');
    if (state.ecorutaChart) {
        state.ecorutaChart.destroy();
    }
    state.ecorutaChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: bestHours.map(slot => slot.hour),
            datasets: [{
                label: 'NO2 estimado',
                data: bestHours.map(slot => slot.aqi),
                borderColor: '#22c55e',
                backgroundColor: 'rgba(34, 197, 94, 0.18)',
                tension: 0.35,
                fill: true
            }, {
                label: 'Tráfico',
                data: bestHours.map(slot => slot.traffic),
                borderColor: '#3b82f6',
                backgroundColor: 'rgba(59, 130, 246, 0.14)',
                tension: 0.35,
                fill: true,
                yAxisID: 'y1'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: { title: { display: true, text: 'NO2' } },
                y1: {
                    position: 'right',
                    grid: { drawOnChartArea: false },
                    title: { display: true, text: 'Tráfico' }
                }
            }
        }
    });
}

function fitRoutesOnMap(routes) {
    const bounds = [];
    routes.forEach(route => {
        route.points.forEach(point => bounds.push([point.lat, point.lon]));
    });
    if (bounds.length) {
        ecoMap.fitBounds(bounds, { padding: [24, 24] });
    }
}

async function loadZones() {
    try {
        const response = await fetch('/api/zones');
        const data = await response.json();
        state.zones = Array.isArray(data) ? data : [];
    } catch (error) {
        console.error('Error loading zones', error);
        state.zones = [];
    }
}

async function calculateRoute() {
    const originInput = document.getElementById('route-origin').value;
    const destInput = document.getElementById('route-dest').value;
    const mode = document.getElementById('route-mode').value;
    const originZone = resolveZone(originInput);
    const destZone = resolveZone(destInput);
    const comparative = document.getElementById('route-comparative');

    if (!originZone || !destZone) {
        comparative.innerHTML = '<p>Escribe un origen y destino válidos usando nombre o id de zona.</p>';
        return;
    }

    const params = new URLSearchParams({ origin: originZone.id, destination: destZone.id, mode });
    const response = await fetch(`/api/ecoruta?${params.toString()}`);
    const data = await response.json();
    const routes = Array.isArray(data.routes) ? data.routes : [];
    state.routes = routes;

    clearRouteLayers();
    routes.forEach(route => {
        const latLngs = route.points.map(point => [point.lat, point.lon]);
        const polyline = L.polyline(latLngs, { color: route.color, weight: 6, opacity: 0.9, lineCap: 'round' }).addTo(state.routeLayers);
        polyline.bindTooltip(`${route.name}: ${route.label}`, { sticky: true });
        L.circleMarker(latLngs[0], { radius: 7, color: route.color, fillColor: route.color, fillOpacity: 1 }).addTo(state.routeLayers);
        L.circleMarker(latLngs[latLngs.length - 1], { radius: 7, color: route.color, fillColor: '#ffffff', fillOpacity: 1 }).addTo(state.routeLayers);
    });

    renderRouteResults(routes, originZone, destZone);
    fitRoutesOnMap(routes);
    renderBestHoursChart(data.bestHours || []);
}

document.getElementById('btn-calc-route').addEventListener('click', () => {
    calculateRoute().catch(error => {
        console.error('Route calculation failed', error);
        document.getElementById('route-comparative').innerHTML = '<p>No se pudo calcular la ruta.</p>';
    });
});

document.getElementById('route-dest').addEventListener('keydown', event => {
    if (event.key === 'Enter') {
        calculateRoute().catch(error => console.error(error));
    }
});

document.getElementById('route-origin').addEventListener('keydown', event => {
    if (event.key === 'Enter') {
        calculateRoute().catch(error => console.error(error));
    }
});

// Fetch Dashboard Data
async function loadDashboard() {
    try {
        const res = await fetch('/api/dashboard');
        const data = await res.json();
        if(data && data.length > 0) {
            let totalNo2 = 0;
            let alerts = 0;
            data.forEach(d => {
                const val = d.NO2Concentration?.value || 0;
                totalNo2 += val;
                if(val > 40) alerts++;
            });
            document.getElementById('kpi-air').innerText = Math.round(totalNo2 / data.length) + " µg/m³";
            document.getElementById('kpi-alerts').innerText = alerts;
            document.getElementById('kpi-greenscore').innerText = "82/100"; // Mock
            document.getElementById('kpi-traffic').innerText = "Medio"; // Mock
            
            const alertsList = document.getElementById('alerts-list');
            alertsList.innerHTML = '';
            if(alerts > 0) {
                alertsList.innerHTML = `<li>Alerta: Nivel alto de NO2 en Ronda de Nelle</li>`;
            } else {
                alertsList.innerHTML = `<li>Todo en orden</li>`;
            }
        }
    } catch(e) {
        console.error("Error loading dashboard", e);
    }
}
loadZones();
loadDashboard();

// 3D AirWatch Scene
function init3D() {
        const container = document.getElementById('airwatch-3d');
        if(!container) return;
        // clear previous
        container.innerHTML = '';
        const scene = new THREE.Scene();
        scene.background = new THREE.Color(0x0b1220);

        const camera = new THREE.PerspectiveCamera(50, container.clientWidth / container.clientHeight, 0.1, 1000);
        const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
        renderer.setSize(container.clientWidth, container.clientHeight);
        container.appendChild(renderer.domElement);

        // simple orbit controls if available
        if(THREE.OrbitControls){
            const controls = new THREE.OrbitControls(camera, renderer.domElement);
            controls.target.set(0,0,0);
            controls.update();
        }

        // UI: variable selector
        const varSel = document.createElement('select');
        varSel.id = 'aw3dVar';
        ['no2','pm25','pm10','co2','noise'].forEach(v=>{const o=document.createElement('option');o.value=v;o.text=v.toUpperCase();varSel.appendChild(o);});
        varSel.style.position='absolute'; varSel.style.left='12px'; varSel.style.top='12px'; varSel.style.zIndex=10; container.appendChild(varSel);

        // tooltip overlay
        const tip = document.createElement('div');
        tip.style.position='absolute'; tip.style.right='12px'; tip.style.top='12px'; tip.style.zIndex=10; tip.style.color='#cbd5e1'; tip.style.background='rgba(3,7,18,0.6)'; tip.style.padding='6px 8px'; tip.style.borderRadius='6px';
        tip.innerText = '3D: cargando...'; container.appendChild(tip);

        // fetch zones and build instanced bars
        const build = async () => {
            tip.innerText = 'Cargando zonas...';
            let zones=[];
            try{const r = await fetch('/api/zones'); zones = await r.json();}catch(e){ zones = [] }
            if(!zones || !zones.length){ tip.innerText='No hay datos'; return; }

            // projection constants (meters per deg)
            const centerLat = 43.3623, centerLon = -8.4115; // approximate center
            const metersPerDegLat = 110574;
            const metersPerDegLon = 111320 * Math.cos(centerLat * Math.PI/180);

            const count = zones.length;
            const geom = new THREE.BoxGeometry(1, 1, 1);
            const material = new THREE.MeshBasicMaterial({ vertexColors: true, transparent: true });
            const inst = new THREE.InstancedMesh(geom, material, count);
            inst.instanceMatrix.setUsage(THREE.DynamicDrawUsage);
            scene.add(inst);

            // color attribute per instance via color buffer
            const color = new THREE.Color();
            const dummy = new THREE.Object3D();
            const values = zones.map(z=>({id:z.id,name:z.name,lat:z.lat,lon:z.lon,no2:z.no2||0,pm25:z.pm25||0,pm10:z.pm10||0,co2:z.co2||0,noise:z.noise||0}));

            const updateInstances = () => {
                const varName = document.getElementById('aw3dVar').value || 'no2';
                const maxVal = Math.max(...values.map(v=>v[varName]||0), 1);
                for(let i=0;i<values.length;i++){
                    const v = values[i];
                    const dx = (v.lon - centerLon) * metersPerDegLon / 200; // scale down
                    const dz = (v.lat - centerLat) * metersPerDegLat / 200;
                    const height = Math.max(0.5, (v[varName]||0) / maxVal * 6);
                    dummy.position.set(dx, height/2, -dz);
                    dummy.scale.set(0.8, height, 0.8);
                    dummy.updateMatrix();
                    inst.setMatrixAt(i, dummy.matrix);
                    // color gradient green->yellow->red
                    const t = Math.min(1, (v[varName]||0)/maxVal);
                    color.setHSL((0.33 - 0.33*t), 0.8, 0.5);
                    inst.setColorAt(i, color);
                }
                inst.instanceMatrix.needsUpdate = true;
                if(inst.instanceColor) inst.instanceColor.needsUpdate = true;
                tip.innerText = `Variable: ${varName.toUpperCase()} — max ${Math.round(maxVal*10)/10}`;
            };

            // initial camera framing
            camera.position.set(0, 10, 18);
            camera.lookAt(0, 0, 0);

            varSel.onchange = updateInstances;
            updateInstances();

            // simple hover: raycaster
            const ray = new THREE.Raycaster();
            const mouse = new THREE.Vector2();
            const overlay = document.createElement('div'); overlay.style.position='absolute'; overlay.style.left='12px'; overlay.style.bottom='12px'; overlay.style.zIndex=10; overlay.style.color='#e2e8f0'; overlay.style.background='rgba(2,6,23,0.6)'; overlay.style.padding='6px 8px'; overlay.style.borderRadius='6px'; overlay.innerText='Hover: zona'; container.appendChild(overlay);
            function onMove(e){
                const rect = renderer.domElement.getBoundingClientRect();
                mouse.x = ((e.clientX-rect.left)/rect.width)*2-1; mouse.y = -((e.clientY-rect.top)/rect.height)*2+1;
                ray.setFromCamera(mouse, camera);
                const intersects = ray.intersectObject(inst);
                if(intersects.length){ const idx = intersects[0].instanceId; if(idx!=null){ const z = values[idx]; overlay.innerText = `${z.name}: ${document.getElementById('aw3dVar').value.toUpperCase()}=${z[document.getElementById('aw3dVar').value]}`; } }
            }
            renderer.domElement.addEventListener('mousemove', onMove);

        };

        build();

        function animate() {
            requestAnimationFrame(animate);
            scene.rotation.y += 0.002;
            renderer.render(scene, camera);
        }
        animate();
}
// Init slightly after to ensure dimensions
setTimeout(init3D, 500);

// Charts
const ctxCorr = document.getElementById('airwatch-correlation').getContext('2d');
new Chart(ctxCorr, {
    type: 'scatter',
    data: {
        datasets: [{
            label: 'Tráfico vs Contaminación',
            data: [{x: 10, y: 20}, {x: 15, y: 30}, {x: 30, y: 50}, {x: 50, y: 80}],
            backgroundColor: '#3b82f6'
        }]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
            x: { title: { display: true, text: 'Tráfico (vehículos/h)' } },
            y: { title: { display: true, text: 'NO2 (µg/m³)' } }
        }
    }
});

const ctxRadar = document.getElementById('greenscore-radar').getContext('2d');
new Chart(ctxRadar, {
    type: 'radar',
    data: {
        labels: ['Calidad Aire', 'Ruido', 'Tráfico', 'Zonas Verdes', 'Limpieza'],
        datasets: [{
            label: 'Centro',
            data: [65, 59, 90, 81, 56],
            fill: true,
            backgroundColor: 'rgba(59, 130, 246, 0.2)',
            borderColor: 'rgb(59, 130, 246)',
            pointBackgroundColor: 'rgb(59, 130, 246)',
            pointBorderColor: '#fff',
            pointHoverBackgroundColor: '#fff',
            pointHoverBorderColor: 'rgb(59, 130, 246)'
        }]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
    }
});

const ctxLine = document.getElementById('hist-line').getContext('2d');
new Chart(ctxLine, {
    type: 'line',
    data: {
        labels: ['00:00', '04:00', '08:00', '12:00', '16:00', '20:00'],
        datasets: [{
            label: 'Evolución NO2',
            data: [20, 15, 60, 45, 55, 30],
            borderColor: '#22c55e',
            tension: 0.4
        }]
    },
    options: { responsive: true, maintainAspectRatio: false }
});

const ctxBar = document.getElementById('hist-bar').getContext('2d');
new Chart(ctxBar, {
    type: 'bar',
    data: {
        labels: ['Centro', 'Los Rosales', 'Cuatro Caminos', 'Monte Alto'],
        datasets: [{
            label: 'Media NO2 Semanal',
            data: [45, 20, 50, 25],
            backgroundColor: '#8b5cf6'
        }]
    },
    options: { responsive: true, maintainAspectRatio: false }
});

// URBS Assistant Logic
document.getElementById('btn-send-chat').addEventListener('click', async () => {
    const input = document.getElementById('chat-msg');
    const msg = input.value.trim();
    if(!msg) return;
    
    const chatWin = document.getElementById('chat-window');
    chatWin.innerHTML += `<div class="message user">${msg}</div>`;
    input.value = '';
    chatWin.scrollTop = chatWin.scrollHeight;
    
    chatWin.innerHTML += `<div class="message bot">Analizando tu solicitud...</div>`;
    chatWin.scrollTop = chatWin.scrollHeight;
    
    try {
        const res = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: msg, mode: state.mode, lang: state.lang })
        });
        const data = await res.json();
        const reply = data.response || data.explanation || "No pude conectar con el modelo.";
        chatWin.innerHTML += `<div class="message bot">${reply}</div>`;
    } catch(e) {
        chatWin.innerHTML += `<div class="message bot">Lo siento, hubo un error de conexión con mi núcleo.</div>`;
    }
    chatWin.scrollTop = chatWin.scrollHeight;
});

// Grafana Dashboard Loading with Health Check
async function loadGrafanaDashboard() {
    const iframe = document.getElementById('grafana-iframe');
    const loading = document.getElementById('grafana-loading');
    const maxRetries = 30;
    const retryInterval = 2000; // 2 segundos
    
    for (let attempt = 0; attempt < maxRetries; attempt++) {
        try {
            // Probar que Grafana está listo
            const response = await fetch('/grafana/api/health');
            if (response.ok) {
                // Grafana está listo, mostrar iframe
                iframe.src = '/grafana/d/urbs-dashboard';
                iframe.style.display = 'block';
                loading.style.display = 'none';
                console.log('Grafana dashboard cargado correctamente');
                return;
            }
        } catch (error) {
            console.log(`Intento ${attempt + 1}/${maxRetries}: Esperando a Grafana...`);
        }
        
        // Esperar antes de reintentar
        await new Promise(resolve => setTimeout(resolve, retryInterval));
    }
    
    // Si se agotaron los reintentos, mostrar mensaje de error
    loading.innerHTML = 'Error: No se pudo conectar con Grafana. Por favor, recarga la página.';
    loading.style.color = '#ef4444';
}

// Cargar dashboard cuando se acceda a la pestaña de Histórico
const historicoTab = document.querySelector('[data-target="historico"]');
if (historicoTab) {
    historicoTab.addEventListener('click', () => {
        // Solo cargar si no se ha cargado aún
        if (document.getElementById('grafana-iframe').src === '') {
            loadGrafanaDashboard();
        }
    });
}

// O cargar automáticamente después de que la página esté lista
document.addEventListener('DOMContentLoaded', () => {
    // Esperar un poco para que todo esté preparado
    setTimeout(loadGrafanaDashboard, 1000);
});
