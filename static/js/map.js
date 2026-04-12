/**
 * map.js — Leaflet Map Logic for TN Bus Lost & Found
 * =====================================================
 * Fetches route data from /api/routes and renders:
 *   - Color-coded polylines for each bus route
 *   - Circular markers for each stop with popups
 *   - Pulsing markers for depots
 *   - Click-to-select: clicking a stop fills the form dropdowns
 *
 * Used by: index.html (passenger form), status.html (info map)
 *
 * Leaflet must be loaded before this script (via CDN in base.html).
 */

// ─────────────────────────────────────────────────────────────────────────────
// Depot metadata (mirrors app.py DEPOTS dict)
// Used purely for map popup labels — not for auth logic.
// ─────────────────────────────────────────────────────────────────────────────
const DEPOT_INFO = {
  "Chennai":      { phone: "9000000001", name: "Chennai Depot" },
  "Coimbatore":   { phone: "9000000002", name: "Coimbatore Depot" },
  "Madurai":      { phone: "9000000003", name: "Madurai Depot" },
  "Salem":        { phone: "9000000004", name: "Salem Depot" },
  "Tirunelveli":  { phone: "9000000005", name: "Tirunelveli Depot" }
};

// ─────────────────────────────────────────────────────────────────────────────
// Initialise Leaflet map
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Creates and returns a Leaflet map centred over Tamil Nadu.
 * @param {string} containerId - HTML element id for the map div
 * @returns {L.Map}
 */
function initMap(containerId) {
  const map = L.map(containerId, {
    center: [10.8, 78.5],   // Centre of Tamil Nadu
    zoom: 7,
    zoomControl: true,
    scrollWheelZoom: true
  });

  // OpenStreetMap tiles (free, no API key needed)
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    maxZoom: 18
  }).addTo(map);

  return map;
}

// ─────────────────────────────────────────────────────────────────────────────
// Custom marker icons
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Create a small colored circle marker for route stops.
 * @param {string} color - CSS hex color
 */
function stopIcon(color) {
  return L.divIcon({
    className: '',
    html: `<div style="
      width:12px; height:12px;
      background:${color};
      border:2px solid white;
      border-radius:50%;
      box-shadow:0 0 4px rgba(0,0,0,0.4);
    "></div>`,
    iconSize: [12, 12],
    iconAnchor: [6, 6]
  });
}

/**
 * Create a pulsing depot marker (larger, with an animated ring).
 * @param {string} color - CSS hex color for the depot
 */
function depotIcon(color) {
  return L.divIcon({
    className: '',
    html: `
      <div style="position:relative;width:28px;height:28px;">
        <div style="
          position:absolute; inset:0;
          background:${color}33;
          border-radius:50%;
          animation: pulse-ring 1.5s ease-out infinite;
        "></div>
        <div style="
          position:absolute; top:4px; left:4px;
          width:20px; height:20px;
          background:${color};
          border:2px solid white;
          border-radius:50%;
          display:flex; align-items:center; justify-content:center;
          box-shadow:0 2px 6px rgba(0,0,0,0.3);
        ">
          <svg width="10" height="10" viewBox="0 0 24 24" fill="white">
            <path d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z"/>
          </svg>
        </div>
      </div>`,
    iconSize: [28, 28],
    iconAnchor: [14, 14]
  });
}

// ─────────────────────────────────────────────────────────────────────────────
// Render all routes onto a Leaflet map
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Fetch routes from /api/routes and draw them on the provided map.
 *
 * @param {L.Map} map - Leaflet map instance
 * @param {Function|null} onStopClick - callback(stopName) when a stop marker is clicked
 *        Pass null on pages where stop-selection is not needed.
 */
function renderRoutes(map, onStopClick = null) {
  fetch('/api/routes')
    .then(res => res.json())
    .then(routes => {
      const legend = buildLegend(routes);
      legend.addTo(map);

      routes.forEach(route => {
        const color = route.color;
        const latLons = route.stops.map(s => [s.lat, s.lon]);

        // ── Draw polyline ─────────────────────────────────────────────────
        L.polyline(latLons, {
          color,
          weight: 4,
          opacity: 0.8,
          dashArray: null
        }).addTo(map).bindPopup(`<b>${route.name}</b>`);

        // ── Draw stop markers ─────────────────────────────────────────────
        route.stops.forEach(stop => {
          const isDepot = stop.name in DEPOT_INFO;
          const marker  = L.marker([stop.lat, stop.lon], {
            icon: isDepot ? depotIcon(color) : stopIcon(color),
            title: stop.name
          }).addTo(map);

          // Build popup HTML
          let popupHtml = `<div style="font-family:Poppins,sans-serif;min-width:120px">
            <b style="color:${color}">${stop.name}</b>`;
          if (isDepot) {
            const d = DEPOT_INFO[stop.name];
            popupHtml += `<br><span style="font-size:11px;color:#555">🏢 ${d.name}</span>
              <br><span style="font-size:11px;color:#888">📞 ${d.phone}</span>`;
          }
          if (onStopClick) {
            popupHtml += `<br><button onclick="window._selectStop('${stop.name}')"
              style="margin-top:6px;padding:3px 8px;background:${color};color:white;
                     border:none;border-radius:4px;cursor:pointer;font-size:11px;">
              Select this stop</button>`;
          }
          popupHtml += `</div>`;
          marker.bindPopup(popupHtml);
        });
      });
    })
    .catch(err => console.error('Failed to load routes:', err));
}

// ─────────────────────────────────────────────────────────────────────────────
// Highlight a specific route (when user selects route from dropdown)
// ─────────────────────────────────────────────────────────────────────────────

let _highlightLayer = null;

/**
 * Highlights a specific route polyline on the map with a glow effect.
 * Removes the previous highlight first.
 *
 * @param {L.Map} map
 * @param {Array} routes - full routes array from API
 * @param {string} routeId - id of the route to highlight
 */
function highlightRoute(map, routes, routeId) {
  if (_highlightLayer) {
    map.removeLayer(_highlightLayer);
    _highlightLayer = null;
  }
  const route = routes.find(r => r.id === routeId);
  if (!route) return;

  const latLons = route.stops.map(s => [s.lat, s.lon]);
  _highlightLayer = L.polyline(latLons, {
    color: route.color,
    weight: 8,
    opacity: 0.5
  }).addTo(map);

  // Pan to route bounds
  map.fitBounds(_highlightLayer.getBounds(), { padding: [40, 40] });
}

// ─────────────────────────────────────────────────────────────────────────────
// Legend control
// ─────────────────────────────────────────────────────────────────────────────

function buildLegend(routes) {
  const legend = L.control({ position: 'bottomright' });
  legend.onAdd = function () {
    const div = L.DomUtil.create('div');
    div.style.cssText = `
      background:rgba(255,255,255,0.95);
      padding:10px 14px;
      border-radius:8px;
      box-shadow:0 2px 8px rgba(0,0,0,0.15);
      font-family:Poppins,sans-serif;
      font-size:12px;
      line-height:1.8;
    `;
    let html = '<b style="font-size:11px;text-transform:uppercase;letter-spacing:.05em;color:#555">Routes</b><br>';
    routes.forEach(r => {
      html += `<span style="color:${r.color}">&#9644;</span> ${r.name}<br>`;
    });
    html += '<hr style="border:none;border-top:1px solid #eee;margin:6px 0">';
    html += '<span style="font-size:10px;color:#888">&#x25CF; Click a stop to select</span>';
    div.innerHTML = html;
    return div;
  };
  return legend;
}

// ─────────────────────────────────────────────────────────────────────────────
// Add pulse animation keyframe (injected once into document <head>)
// ─────────────────────────────────────────────────────────────────────────────
(function injectPulseAnimation() {
  const style = document.createElement('style');
  style.textContent = `
    @keyframes pulse-ring {
      0%   { transform: scale(0.8); opacity: 0.8; }
      80%  { transform: scale(2);   opacity: 0; }
      100% { transform: scale(2);   opacity: 0; }
    }
  `;
  document.head.appendChild(style);
})();
