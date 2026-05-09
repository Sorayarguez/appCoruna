mermaid.initialize({ startOnLoad: true, theme: 'dark' });

// Global State
const state = {
    corunaCoords: [43.3623, -8.4115]
};

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

const tileLayer = 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png';

// Dashboard Map
const dashMap = L.map('dashboard-map', mapOptions);
L.tileLayer(tileLayer).addTo(dashMap);

// AirWatch Map (Heatmap)
const airMap = L.map('airwatch-map', mapOptions);
L.tileLayer(tileLayer).addTo(airMap);

// EcoRuta Map
const ecoMap = L.map('ecoruta-map', mapOptions);
L.tileLayer(tileLayer).addTo(ecoMap);

// GreenScore Map
const greenMap = L.map('greenscore-map', mapOptions);
L.tileLayer(tileLayer).addTo(greenMap);

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
    
    chatWin.innerHTML += `<div class="message bot">Analizando tu solicitud usando FIWARE y OLLAMA... (simulado)</div>`;
    chatWin.scrollTop = chatWin.scrollHeight;
    
    try {
        const res = await fetch(`/api/explain/urn:ngsi-ld:RoadSegment:CalleReal`);
        const data = await res.json();
        chatWin.innerHTML += `<div class="message bot">${data.explanation || "No pude conectar con el modelo."}</div>`;
    } catch(e) {
        chatWin.innerHTML += `<div class="message bot">Lo siento, hubo un error de conexión con mi núcleo.</div>`;
    }
    chatWin.scrollTop = chatWin.scrollHeight;
});
