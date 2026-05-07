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
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x0f172a);
    
    const camera = new THREE.PerspectiveCamera(75, container.clientWidth / container.clientHeight, 0.1, 1000);
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    
    renderer.setSize(container.clientWidth, container.clientHeight);
    container.appendChild(renderer.domElement);
    
    // Add simple plane
    const plane = new THREE.Mesh(
        new THREE.PlaneGeometry(10, 10, 10, 10),
        new THREE.MeshBasicMaterial({ color: 0x1e293b, wireframe: true })
    );
    plane.rotation.x = -Math.PI / 2;
    scene.add(plane);
    
    // Add columns
    const geoms = new THREE.BoxGeometry(0.5, 1, 0.5);
    for(let i=0; i<5; i++) {
        const mat = new THREE.MeshBasicMaterial({ color: Math.random() > 0.5 ? 0xef4444 : 0x22c55e, opacity: 0.8, transparent: true });
        const mesh = new THREE.Mesh(geoms, mat);
        mesh.position.set((Math.random() - 0.5) * 8, 0.5, (Math.random() - 0.5) * 8);
        mesh.scale.y = Math.random() * 3 + 1;
        mesh.position.y = mesh.scale.y / 2;
        scene.add(mesh);
    }
    
    camera.position.set(0, 5, 8);
    camera.lookAt(0, 0, 0);
    
    function animate() {
        requestAnimationFrame(animate);
        scene.rotation.y += 0.005;
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
