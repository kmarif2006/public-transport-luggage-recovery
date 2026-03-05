/**
 * Tamil Nadu Bus Lost Luggage Tracking — Route Map JS
 * Official Ministerial Redesign - Advanced Routing Mode
 */

const API_BASE = "/api";
const AUTH_TOKEN = localStorage.getItem("jwt_token");
let map, markersLayer, routingControl;
let allDepots = [];
let sourceDepot = null;
let destinationDepot = null;

// Official Map Standard Colors
const COLORS = {
  MAROON: "#7A0C0C",
  GOLD: "#D4AF37",
  BLUE: "#004080",
  PATH: "#3B82F6", // High contrast blue for route
  STOP: "#EF4444"   // Red for start/end
};

/** Initialize Map */
function initMap() {
  if (!AUTH_TOKEN) {
    window.location.href = "/login.html";
    return;
  }

  // Centered on Tamil Nadu
  map = L.map('map', {
    zoomControl: false
  }).setView([11.1271, 78.6569], 7);

  L.control.zoom({ position: 'bottomright' }).addTo(map);

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap contributors'
  }).addTo(map);

  markersLayer = L.layerGroup().addTo(map);

  fetchDepots();
  setupEventListeners();

  // Ensure Leaflet calculates the correct container size after layout
  setTimeout(() => {
    map.invalidateSize();
  }, 200);
}

/** Fetch all depots */
function fetchDepots() {
  fetch(`${API_BASE}/depots`)
    .then(res => res.json())
    .then(data => {
      allDepots = data.depots || [];
      populateDropdowns(allDepots);
      displayMarkers(allDepots);
    })
    .catch(err => console.error("Error fetching depots:", err));
}

/** Populate Source/Destination Dropdowns */
function populateDropdowns(depots) {
  const srcSelect = document.getElementById('source-depot-select');
  const dstSelect = document.getElementById('destination-depot-select');

  // Sort alphabetically
  const sorted = [...depots].sort((a, b) => a.name.localeCompare(b.name));

  sorted.forEach(d => {
    const opt = document.createElement('option');
    opt.value = d.depot_id;
    opt.textContent = `${d.name} (${d.district})`;
    srcSelect.appendChild(opt);
    dstSelect.appendChild(opt.cloneNode(true));
  });
}

/** Display Markers */
function displayMarkers(depots) {
  markersLayer.clearLayers();
  depots.forEach(d => {
    if (!d.latitude || !d.longitude) return;

    let markerColor = COLORS.MAROON;
    let isSelected = false;

    // Custom styling for selected points
    if (sourceDepot && d.depot_id === sourceDepot.depot_id) {
      markerColor = "#10B981"; // Green for Start
      isSelected = true;
    } else if (destinationDepot && d.depot_id === destinationDepot.depot_id) {
      markerColor = COLORS.GOLD; // Gold for End
      isSelected = true;
    }

    const icon = L.divIcon({
      className: 'custom-bus-icon',
      html: `<div class="bus-marker-inner" style="border-color: ${markerColor}; color: ${markerColor}; background: ${isSelected ? 'rgba(255,255,255,0.9)' : 'white'}; transform: ${isSelected ? 'scale(1.2)' : 'scale(1)'}; shadow: ${isSelected ? '0 0 15px rgba(0,0,0,0.3)' : 'none'}">
                <i class="fas fa-bus"></i>
             </div>`,
      iconSize: [40, 40],
      iconAnchor: [20, 20]
    });

    const marker = L.marker([d.latitude, d.longitude], { icon: icon });

    const popupContent = `
      <div class="popup-header" style="background: ${markerColor}; color: white; padding: 12px; border-radius: 8px 8px 0 0; text-align:center;">
        <strong style="display:block; font-size: 1.1rem;">${d.name}</strong>
        <small style="opacity:0.9;">${d.type} Depot</small>
      </div>
      <div style="padding: 15px; background: white; border-radius: 0 0 8px 8px; box-shadow: 0 4px 10px rgba(0,0,0,0.1);">
        <p style="margin: 0 0 12px 0; font-size: 0.9rem; color: #4B5563;"><i class="fas fa-map-marker-alt"></i> ${d.district}, ${d.city}</p>
        <div style="display: flex; flex-direction: column; gap: 8px;">
            <button onclick="selectAs('source', '${d.depot_id}')" class="btn-primary" style="padding: 8px; font-size: 0.85rem; background: #10B981; border:none; color:white; border-radius:4px; cursor:pointer;">
                <i class="fas fa-play"></i> Set as Starting Point
            </button>
            <button onclick="selectAs('destination', '${d.depot_id}')" class="btn-primary" style="padding: 8px; font-size: 0.85rem; background: ${COLORS.GOLD}; border:none; color:white; border-radius:4px; cursor:pointer;">
                <i class="fas fa-flag-checkered"></i> Set as Destination
            </button>
        </div>
      </div>
    `;

    marker.bindPopup(popupContent);
    markersLayer.addLayer(marker);
  });
}

/** Selection Helpers */
window.selectAs = (type, id) => {
  const select = document.getElementById(`${type}-depot-select`);
  select.value = id;

  // Track selection on backend for analytical purposes (Production requirement)
  fetch(`${API_BASE}/select-depot`, {
    method: "POST",
    headers: {
      "Authorization": `Bearer ${AUTH_TOKEN}`,
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ depot_id: id })
  }).catch(err => console.warn("Selection tracking failed (Passive):", err));

  if (type === 'source') {
    sourceDepot = allDepots.find(d => d.depot_id === id);
    handleSourceChange(id);
  } else {
    destinationDepot = allDepots.find(d => d.depot_id === id);
    handleDestinationChange(id);
  }
  map.closePopup();
};

function handleSourceChange(forceId) {
  const id = forceId || document.getElementById('source-depot-select').value;
  sourceDepot = allDepots.find(d => d.depot_id === id);
  const dstSelect = document.getElementById('destination-depot-select');

  if (sourceDepot) {
    dstSelect.disabled = false;
    map.flyTo([sourceDepot.latitude, sourceDepot.longitude], 12, { animate: true });
  } else {
    dstSelect.disabled = true;
    destinationDepot = null;
    dstSelect.value = "";
  }
  updateRouteUI();
  displayMarkers(allDepots);
}

function handleDestinationChange(forceId) {
  const id = forceId || document.getElementById('destination-depot-select').value;
  destinationDepot = allDepots.find(d => d.depot_id === id);
  const drawBtn = document.getElementById('draw-route-btn');

  if (destinationDepot) {
    drawBtn.disabled = false;
    map.flyTo([destinationDepot.latitude, destinationDepot.longitude], 12, { animate: true });
  } else {
    drawBtn.disabled = true;
  }
  updateRouteUI();
  displayMarkers(allDepots);
}

function updateRouteUI() {
  if (!sourceDepot || !destinationDepot) {
    if (routingControl) map.removeControl(routingControl);
    document.getElementById('route-info').classList.add('hidden');
    document.getElementById('report-luggage-btn').classList.add('hidden');
  }
}

/** Draw Route and Find Depots along path */
function drawRoute() {
  if (!sourceDepot || !destinationDepot) return;
  if (routingControl) map.removeControl(routingControl);

  // High contrast pathing using Tamil Nadu Transport Identity Blue
  routingControl = L.Routing.control({
    waypoints: [
      L.latLng(sourceDepot.latitude, sourceDepot.longitude),
      L.latLng(destinationDepot.latitude, destinationDepot.longitude)
    ],
    lineOptions: {
      styles: [{ color: "#2563EB", opacity: 0.9, weight: 8 }]
    },
    createMarker: () => null,
    addWaypoints: false,
    draggableWaypoints: false,
    fitSelectedRoutes: true,
    show: false
  }).addTo(map);

  routingControl.on('routesfound', function (e) {
    const routes = e.routes;
    const summary = routes[0].summary;
    const distanceKm = (summary.totalDistance / 1000).toFixed(1);

    // Find all depots within 10km of the calculated travel path
    const depotsInRoute = findDepotsNearRoute(routes[0].coordinates);
    window.currentRouteDepots = depotsInRoute.map(d => d.depot_id);

    // Update UI with route data
    document.getElementById('route-summary').textContent = `${sourceDepot.name} ➔ ${destinationDepot.name}`;
    document.getElementById('route-distance').textContent = `${distanceKm} km`;
    document.getElementById('route-depot-count').textContent = depotsInRoute.length;

    // Unhide info and action button
    document.getElementById('route-info').classList.remove('hidden');
    document.getElementById('report-luggage-btn').classList.remove('hidden');

    // Automatic non-blocking trigger of the report form
    setTimeout(() => {
      openReportModal(sourceDepot.depot_id, `${sourceDepot.name} ➔ ${destinationDepot.name}`);
    }, 1000);
  });
}

function findDepotsNearRoute(coordinates) {
  const thresholdKm = 10;
  return allDepots.filter(d => {
    // Always include source and dest
    if (d.depot_id === sourceDepot.depot_id || d.depot_id === destinationDepot.depot_id) return true;

    // Check distance to route points (sampled every 20 points for performance)
    for (let i = 0; i < coordinates.length; i += 20) {
      const dist = getDistance(d.latitude, d.longitude, coordinates[i].lat, coordinates[i].lng);
      if (dist <= thresholdKm) return true;
    }
    return false;
  });
}

function getDistance(lat1, lon1, lat2, lon2) {
  const R = 6371; // km
  const dLat = (lat2 - lat1) * Math.PI / 180;
  const dLon = (lon2 - lon1) * Math.PI / 180;
  const a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
    Math.sin(dLon / 2) * Math.sin(dLon / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return R * c;
}

/** Modal Management */
window.openReportModal = (depotId, contextName) => {
  const modal = document.getElementById('report-modal');
  modal.classList.remove('hidden');
  document.getElementById('selected-depot-name').textContent = `Travel Path: ${contextName}`;
  document.getElementById('depot-id-input').value = depotId;
};

window.closeReportModal = () => {
  const modal = document.getElementById('report-modal');
  modal.classList.add('hidden');
  const form = document.getElementById('report-form');
  if (form) form.reset();
  const charCount = document.getElementById('char-count');
  if (charCount) charCount.textContent = "0";
};

/** Submit Report */
function submitReport(e) {
  e.preventDefault();
  const btn = document.getElementById('submit-report-btn');
  btn.disabled = true;
  btn.innerHTML = `<div class="loader"></div> Processing...`;

  const formData = new FormData();
  formData.append('reporter_name', document.getElementById('reporter-name').value);
  formData.append('source_depot_id', sourceDepot.depot_id);
  formData.append('destination_depot_id', destinationDepot.depot_id);
  formData.append('route_depots', JSON.stringify(window.currentRouteDepots || []));
  formData.append('item_name', document.getElementById('item-name').value);
  formData.append('item_description', document.getElementById('item-description').value);
  formData.append('date_lost', document.getElementById('date-lost').value);
  formData.append('contact_phone', document.getElementById('contact-phone').value);
  formData.append('bus_number', document.getElementById('bus-number').value);

  const photoFile = document.getElementById('photo_upload').files[0];
  if (photoFile) formData.append('photo', photoFile);

  fetch(`${API_BASE}/report-luggage`, {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${AUTH_TOKEN}` },
    body: formData
  })
    .then(res => res.json())
    .then(data => {
      if (data.id || data.message === "Report submitted") {
        alert("✅ Your lost luggage report has been submitted to all depots along your bus route.");
        window.location.href = "/dashboard.html";
      } else {
        alert(data.message || "Submission failed.");
        btn.disabled = false;
        btn.innerHTML = `<i class="fas fa-paper-plane"></i> Submit Official Report`;
      }
    })
    .catch(() => {
      alert("Network error. Please try again.");
      btn.disabled = false;
      btn.innerHTML = `<i class="fas fa-paper-plane"></i> Submit Official Report`;
    });
}

/** Event Listeners */
function setupEventListeners() {
  // Dropdown filters
  document.getElementById('source-filter').addEventListener('input', (e) => filterSelect('source', e.target.value));
  document.getElementById('destination-filter').addEventListener('input', (e) => filterSelect('destination', e.target.value));

  document.getElementById('source-depot-select').addEventListener('change', handleSourceChange);
  document.getElementById('destination-depot-select').addEventListener('change', handleDestinationChange);
  document.getElementById('draw-route-btn').addEventListener('click', drawRoute);
  document.getElementById('report-form').addEventListener('submit', submitReport);

  // Modal buttons
  document.getElementById('report-luggage-btn').addEventListener('click', () => {
    if (sourceDepot && destinationDepot) {
      openReportModal(sourceDepot.depot_id, `${sourceDepot.name} ➔ ${destinationDepot.name}`);
    } else {
      alert("Please select both source and destination depots first.");
    }
  });
  document.querySelector('.close-modal').addEventListener('click', closeReportModal);



  // Character Counter
  const desc = document.getElementById('item-description');
  if (desc) {
    desc.addEventListener('input', () => {
      const charCount = document.getElementById('char-count');
      if (charCount) charCount.textContent = desc.value.length;
    });
  }

  // Robust Closing Logic
  window.addEventListener('click', (e) => {
    const modal = document.getElementById('report-modal');
    if (e.target === modal) {
      closeReportModal();
    }
  });
}

function filterSelect(type, query) {
  const select = document.getElementById(`${type}-depot-select`);
  const q = query.toLowerCase();

  // Clear and re-populate based on filter
  const currentVal = select.value;
  select.innerHTML = `<option value="">Select ${type === 'source' ? 'Starting Point' : 'Destination'}</option>`;

  allDepots.forEach(d => {
    const text = `${d.name} ${d.city} ${d.district}`.toLowerCase();
    if (text.includes(q)) {
      const opt = document.createElement('option');
      opt.value = d.depot_id;
      opt.textContent = `${d.name} - ${d.city}`;
      if (d.depot_id === currentVal) opt.selected = true;
      select.appendChild(opt);
    }
  });
}

document.addEventListener('DOMContentLoaded', initMap);
