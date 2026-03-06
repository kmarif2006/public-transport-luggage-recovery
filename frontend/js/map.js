/**
 * Tamil Nadu Bus Lost Luggage — Route Map JS
 * Stack: Leaflet.js + OpenStreetMap + Leaflet Routing Machine (OSRM)
 * Passenger-first design: large markers, icon-based popups, touch-friendly
 */

'use strict';

const API_BASE = '/api';
const getAuthToken = () => localStorage.getItem('jwt_token');

// State
let tnMap, markersLayer, routingControl;
let allDepots = [];
let sourceDepot = null;
let destinationDepot = null;
window.currentRouteDepots = [];

// Brand colours
const C = {
  MAROON: '#7A0C0C',
  GREEN: '#16a34a',
  AMBER: '#b45309',
  BLUE: '#2563EB',
  WHITE: '#ffffff',
};

/* =====================================================================
   INIT
   ===================================================================== */

function initMap() {
  console.log('[MAP] initMap: entering function');
  try {
    console.log('[MAP] initMap: checking for div#map');
    if (!document.getElementById('map')) {
      throw new Error('div#map not found in DOM');
    }

    console.log('[MAP] initMap: constructing L.map');
    window.tnMap = L.map('map', { zoomControl: false });
    tnMap = window.tnMap; // keep local ref too

    console.log('[MAP] initMap: setView');
    tnMap.setView([11.1271, 78.6569], 7);

    console.log('[MAP] initMap: adding zoom control');
    L.control.zoom({ position: 'bottomright' }).addTo(tnMap);

    console.log('[MAP] initMap: adding tile layer');
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
      maxZoom: 18,
    }).addTo(tnMap);

    console.log('[MAP] initMap: adding markersLayer');
    markersLayer = L.layerGroup().addTo(tnMap);

    console.log('[MAP] initMap: fetching depots');
    fetchDepots();

    console.log('[MAP] initMap: setting up events');
    setupEventListeners();

    console.log('[MAP] initMap: scheduling invalidateSize');
    setTimeout(() => {
      console.log('[MAP] invalidateSize (300ms)');
      tnMap.invalidateSize();
    }, 300);
    setTimeout(() => {
      console.log('[MAP] invalidateSize (1000ms)');
      tnMap.invalidateSize();
    }, 1000);

    console.log('[MAP] initMap: success');
  } catch (err) {
    console.error('[MAP] initMap: CRASHED ->', err);
    throw err; // Re-throw for boot() to catch and display on screen
  }
}

/* =====================================================================
   DEPOT DATA
   ===================================================================== */

function fetchDepots() {
  fetch(`${API_BASE}/depots`)
    .then(r => r.json())
    .then(data => {
      allDepots = data.depots || [];
      populateDropdowns(allDepots);
      displayMarkers(allDepots);
    })
    .catch(err => console.error('Error fetching depots:', err));
}

function populateDropdowns(depots) {
  const src = document.getElementById('source-depot-select');
  const dst = document.getElementById('destination-depot-select');
  const sorted = [...depots].sort((a, b) => a.name.localeCompare(b.name));

  sorted.forEach(d => {
    const text = `${d.name} (${d.district})`;
    src.appendChild(new Option(text, d.depot_id));
    dst.appendChild(new Option(text, d.depot_id));
  });
}

/* =====================================================================
   MAP MARKERS
   ===================================================================== */

function displayMarkers(depots) {
  markersLayer.clearLayers();
  depots.forEach(d => {
    if (!d.latitude || !d.longitude) return;

    // Choose colour based on selection state
    let color = C.MAROON;
    let scale = 'scale(1)';
    if (sourceDepot && d.depot_id === sourceDepot.depot_id) { color = C.GREEN; scale = 'scale(1.25)'; }
    else if (destinationDepot && d.depot_id === destinationDepot.depot_id) { color = C.AMBER; scale = 'scale(1.25)'; }

    const icon = L.divIcon({
      className: 'custom-bus-icon',
      html: `<div class="bus-marker-inner"
                        style="border-color:${color}; color:${color}; transform:${scale};">
                     <i class="fas fa-bus"></i>
                   </div>`,
      iconSize: [52, 52],
      iconAnchor: [26, 26],
    });

    const marker = L.marker([d.latitude, d.longitude], { icon });
    marker.bindPopup(buildPopup(d, color), { maxWidth: 260 });
    markersLayer.addLayer(marker);
  });
}

function buildPopup(d, headerColor) {
  return `
    <div class="depot-popup-header" style="background:${headerColor};">
      <h4>${d.name}</h4>
      <small>${d.type || ''} Depot</small>
    </div>
    <div class="depot-popup-body">
      <p><i class="fas fa-map-marker-alt"></i> ${d.city}, ${d.district}</p>
      <div class="popup-btn-group">
        <button class="popup-action-btn btn-start"
          onclick="selectAs('source','${d.depot_id}')">
          <i class="fas fa-play-circle"></i> SET AS START
        </button>
        <button class="popup-action-btn btn-dest"
          onclick="selectAs('destination','${d.depot_id}')">
          <i class="fas fa-flag-checkered"></i> SET AS DESTINATION
        </button>
      </div>
    </div>`;
}

/* =====================================================================
   DEPOT SELECTION (from popup or dropdown)
   ===================================================================== */

window.selectAs = (type, id) => {
  const select = document.getElementById(`${type}-depot-select`);
  select.value = id;

  if (type === 'source') {
    sourceDepot = allDepots.find(d => d.depot_id === id);
    handleSourceChange(id);
  } else {
    destinationDepot = allDepots.find(d => d.depot_id === id);
    handleDestinationChange(id);
  }
  tnMap.closePopup();

  // passive analytics — non-blocking
  fetch(`${API_BASE}/select-depot`, {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${getAuthToken()}`, 'Content-Type': 'application/json' },
    body: JSON.stringify({ depot_id: id }),
  }).catch(() => { });
};

function handleSourceChange(forceId) {
  const id = forceId || document.getElementById('source-depot-select').value;
  sourceDepot = allDepots.find(d => d.depot_id === id) || null;

  const dst = document.getElementById('destination-depot-select');
  const drawBtn = document.getElementById('draw-route-btn');

  if (sourceDepot) {
    dst.disabled = false;
    tnMap.flyTo([sourceDepot.latitude, sourceDepot.longitude], 11, { animate: true, duration: 1 });
  } else {
    dst.disabled = true;
    destinationDepot = null;
    dst.value = '';
    drawBtn.disabled = true;
  }
  updateSelectionUI();
  displayMarkers(allDepots);
}

function handleDestinationChange(forceId) {
  const id = forceId || document.getElementById('destination-depot-select').value;
  destinationDepot = allDepots.find(d => d.depot_id === id) || null;

  const drawBtn = document.getElementById('draw-route-btn');
  if (destinationDepot) {
    drawBtn.disabled = false;
    tnMap.flyTo([destinationDepot.latitude, destinationDepot.longitude], 11, { animate: true, duration: 1 });
  } else {
    drawBtn.disabled = true;
  }
  updateSelectionUI();
  displayMarkers(allDepots);
}

/** Update instruction banner text based on current state */
function updateSelectionUI() {
  const banner = document.getElementById('map-instruction');
  if (!sourceDepot) {
    banner.innerHTML = '<i class="fas fa-hand-pointer"></i> Tap a depot — SET AS START';
  } else if (!destinationDepot) {
    banner.innerHTML = `<i class="fas fa-check-circle" style="color:#4ade80"></i> Start: <strong>${sourceDepot.name}</strong> — now pick Destination`;
  } else {
    banner.innerHTML = `<i class="fas fa-route"></i> ${sourceDepot.name} <i class="fas fa-arrow-right"></i> ${destinationDepot.name} — Click Calculate Route`;
  }

  // Hide route info if selections reset
  if (!sourceDepot || !destinationDepot) {
    document.getElementById('route-info').classList.add('hidden');
    document.getElementById('report-luggage-btn').classList.add('hidden');
    if (routingControl) { tnMap.removeControl(routingControl); routingControl = null; }
  }
}

/* =====================================================================
   ROUTE DRAWING
   ===================================================================== */

function drawRoute() {
  if (!sourceDepot || !destinationDepot) return;
  if (routingControl) { map.removeControl(routingControl); routingControl = null; }

  routingControl = L.Routing.control({
    waypoints: [
      L.latLng(sourceDepot.latitude, sourceDepot.longitude),
      L.latLng(destinationDepot.latitude, destinationDepot.longitude),
    ],
    lineOptions: { styles: [{ color: C.BLUE, opacity: 0.9, weight: 7 }] },
    createMarker: () => null,
    addWaypoints: false,
    draggableWaypoints: false,
    fitSelectedRoutes: true,
    show: false,              // hide the turn-by-turn panel
    collapsible: true,
  }).addTo(map);

  routingControl.on('routesfound', (e) => {
    const route = e.routes[0];
    const distKm = (route.summary.totalDistance / 1000).toFixed(1);
    const depotsOnRoute = findDepotsNearRoute(route.coordinates);
    window.currentRouteDepots = depotsOnRoute.map(d => d.depot_id);

    document.getElementById('route-summary').textContent =
      `${sourceDepot.name}  →  ${destinationDepot.name}`;
    document.getElementById('route-distance').textContent = `${distKm} km`;
    document.getElementById('route-depot-count').textContent = depotsOnRoute.length;

    document.getElementById('route-info').classList.remove('hidden');
    document.getElementById('report-luggage-btn').classList.remove('hidden');
    document.getElementById('map-instruction').innerHTML =
      `<i class="fas fa-check-circle" style="color:#4ade80"></i> Route drawn — click <strong>Report Lost Luggage</strong>`;

    // Auto-open form after 1.2 s so the user can see the route first
    setTimeout(() => openReportModal(), 1200);
  });

  routingControl.on('routingerror', () => {
    alert('Could not calculate route. Please try different depots.');
  });
}

/* =====================================================================
   DEPOTS NEAR ROUTE
   ===================================================================== */

function findDepotsNearRoute(coords) {
  const THRESHOLD_KM = 15;
  return allDepots.filter(d => {
    if (d.depot_id === sourceDepot.depot_id || d.depot_id === destinationDepot.depot_id) return true;
    for (let i = 0; i < coords.length; i += 15) {
      if (haversine(d.latitude, d.longitude, coords[i].lat, coords[i].lng) <= THRESHOLD_KM) return true;
    }
    return false;
  });
}

function haversine(lat1, lon1, lat2, lon2) {
  const R = 6371;
  const dLa = (lat2 - lat1) * Math.PI / 180;
  const dLo = (lon2 - lon1) * Math.PI / 180;
  const a = Math.sin(dLa / 2) ** 2 +
    Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) * Math.sin(dLo / 2) ** 2;
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}

/* =====================================================================
   FILTER DROPDOWNS
   ===================================================================== */

function filterSelect(type, query) {
  const select = document.getElementById(`${type}-depot-select`);
  const current = select.value;
  const q = query.toLowerCase();
  const label = type === 'source' ? '🟢 Select Starting Point' : '🏁 Select Destination';

  select.innerHTML = `<option value="">${label}</option>`;
  allDepots.forEach(d => {
    const match = `${d.name} ${d.city} ${d.district}`.toLowerCase().includes(q);
    if (match || !q) {
      const opt = new Option(`${d.name} (${d.district})`, d.depot_id);
      opt.selected = d.depot_id === current;
      select.appendChild(opt);
    }
  });
}

/* =====================================================================
   MODAL
   ===================================================================== */

window.openReportModal = () => {
  if (!sourceDepot || !destinationDepot) {
    alert('Please select both a starting point and a destination first.');
    return;
  }
  document.getElementById('modal-route-text').textContent =
    `${sourceDepot.name}  →  ${destinationDepot.name}`;
  document.getElementById('depot-id-input').value = sourceDepot.depot_id;

  // Default date to today
  const today = new Date().toISOString().split('T')[0];
  const dateField = document.getElementById('date-lost');
  if (!dateField.value) dateField.value = today;
  dateField.setAttribute('max', today);

  document.getElementById('report-modal').classList.remove('hidden');
  document.body.style.overflow = 'hidden';
};

window.closeReportModal = () => {
  document.getElementById('report-modal').classList.add('hidden');
  document.body.style.overflow = '';
};

/* =====================================================================
   SUBMIT REPORT
   ===================================================================== */

async function submitReport(e) {
  e.preventDefault();
  const btn = document.getElementById('submit-report-btn');
  btn.disabled = true;
  btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Submitting...';

  const form = new FormData();
  form.append('source_depot_id', sourceDepot.depot_id);
  form.append('destination_depot_id', destinationDepot.depot_id);
  form.append('route_depots', JSON.stringify(window.currentRouteDepots));
  form.append('item_name', document.getElementById('item-name').value.trim());
  form.append('item_description', document.getElementById('item-description').value.trim());
  form.append('date_lost', document.getElementById('date-lost').value);
  form.append('contact_phone', document.getElementById('contact-phone').value.trim());
  form.append('bus_number', document.getElementById('bus-number').value.trim());

  const photo = document.getElementById('photo_upload').files[0];
  if (photo) form.append('photo', photo);

  try {
    const res = await fetch(`${API_BASE}/report-luggage`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${getAuthToken()}` },
      body: form,
    });
    const data = await res.json();

    if (data.message === 'Report submitted' || data.id) {
      alert('✅ Report submitted successfully! Redirecting to your dashboard...');
      window.location.href = '/dashboard.html';
    } else {
      alert(data.message || 'Submission failed. Please try again.');
      btn.disabled = false;
      btn.innerHTML = '<i class="fas fa-paper-plane"></i> Submit Report';
    }
  } catch {
    alert('Network error. Please check your connection and try again.');
    btn.disabled = false;
    btn.innerHTML = '<i class="fas fa-paper-plane"></i> Submit Report';
  }
}

/* =====================================================================
   EVENT LISTENERS
   ===================================================================== */

function setupEventListeners() {
  // Filter inputs
  document.getElementById('source-filter').addEventListener('input',
    e => filterSelect('source', e.target.value));
  document.getElementById('destination-filter').addEventListener('input',
    e => filterSelect('destination', e.target.value));

  // Dropdowns
  document.getElementById('source-depot-select').addEventListener('change', () => handleSourceChange());
  document.getElementById('destination-depot-select').addEventListener('change', () => handleDestinationChange());

  // Buttons
  document.getElementById('draw-route-btn').addEventListener('click', drawRoute);
  document.getElementById('report-luggage-btn').addEventListener('click', openReportModal);

  // Form submit
  document.getElementById('report-form').addEventListener('submit', submitReport);

  // Char counter
  document.getElementById('item-description').addEventListener('input', function () {
    document.getElementById('char-count').textContent = this.value.length;
  });

  // Close modal on backdrop click
  document.getElementById('report-modal').addEventListener('click', (e) => {
    if (e.target === document.getElementById('report-modal')) closeReportModal();
  });

  // ESC key
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') closeReportModal();
  });
}

/* =====================================================================
   BOOT
   ===================================================================== */
function boot() {
  console.log('[MAP] Booting check...');

  if (!getAuthToken()) {
    console.warn('[MAP] Unauthorized. Redirecting...');
    window.location.href = '/login.html';
    return;
  }

  if (typeof L === 'undefined') {
    console.error('[MAP] Leaflet (L) missing!');
    return;
  }

  const mapDiv = document.getElementById('map');
  if (!mapDiv) {
    console.warn('[MAP] Div #map not found. Retrying in 100ms...');
    setTimeout(boot, 100);
    return;
  }

  try {
    initMap();
    console.log('[MAP] initMap() called successfully.');
  } catch (err) {
    console.error('[MAP] initMap() crashed:', err);
  }
}

if (document.readyState === 'loading') {
  window.addEventListener('load', boot);
} else {
  boot();
}
