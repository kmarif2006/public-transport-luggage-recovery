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
// Render the routes a depot operates (depot dashboard overview map)
// ─────────────────────────────────────────────────────────────────────────────

let _depotRoutesLayer = null;

/**
 * Draw every route a depot operates as a light colored overview (straight
 * segments — decorative), with origin/destination markers. Data comes from
 * /api/transport/depots/<phone>/routes.
 *
 * @param {L.Map} map
 * @param {Array} routes - [{ route_no, origin_name, dest_name, stops:[{name,lat,lon}] }]
 */
function renderDepotRoutes(map, routes) {
  if (_depotRoutesLayer) {
    map.removeLayer(_depotRoutesLayer);
    _depotRoutesLayer = null;
  }
  if (!routes || !routes.length) return;

  const colors = ['#1F6FB2', '#C62828', '#2E7D32', '#D4960A', '#6D28D9', '#0891B2'];
  const group  = L.layerGroup();
  const all    = [];

  routes.forEach((rt, i) => {
    const color = colors[i % colors.length];
    const pts = (rt.stops || [])
      .filter(s => s.lat != null && s.lon != null)
      .map(s => [s.lat, s.lon]);
    if (pts.length > 1) {
      L.polyline(pts, { color, weight: 3, opacity: 0.55 }).addTo(group)
        .bindPopup(`<b>${rt.route_no}</b><br>${rt.origin_name} → ${rt.dest_name}`);
    }
    if (pts.length) {
      L.marker(pts[0], { icon: stopIcon(color), title: rt.origin_name }).addTo(group);
      L.marker(pts[pts.length - 1], { icon: depotIcon(color), title: rt.dest_name }).addTo(group);
      all.push(...pts);
    }
  });

  group.addTo(map);
  _depotRoutesLayer = group;
  if (all.length) map.fitBounds(L.latLngBounds(all), { padding: [30, 30] });
}

// ─────────────────────────────────────────────────────────────────────────────
// Render a SINGLE selected transport route (used by the 500-route selector)
// ─────────────────────────────────────────────────────────────────────────────

let _singleRouteLayer = null;

/**
 * Draw one route's ordered stop_sequence (from /api/transport/routes/<id>).
 * Clears any previously drawn single route first. Pans to fit the route.
 *
 * @param {L.Map} map
 * @param {Object} route - { stops: [{stop_id,name,lat,lon,is_major}], route_no, ... }
 * @param {string} color
 */
function renderSingleRoute(map, route, color = '#1F6FB2') {
  if (_singleRouteLayer) {
    map.removeLayer(_singleRouteLayer);
    _singleRouteLayer = null;
  }
  if (!route || !route.stops || !route.stops.length) return;

  const group   = L.layerGroup();
  const latLons = route.stops
    .filter(s => s.lat != null && s.lon != null)
    .map(s => [s.lat, s.lon]);

  // Stop markers (drawn immediately; markers sit above the road line anyway).
  route.stops.forEach((s, i) => {
    if (s.lat == null || s.lon == null) return;
    const isEnd = (i === 0 || i === route.stops.length - 1);
    L.marker([s.lat, s.lon], {
      icon: isEnd ? depotIcon(color) : stopIcon(color),
      title: s.name
    }).addTo(group).bindPopup(
      `<b style="color:${color}">${s.name}</b>` +
      (isEnd ? `<br><span style="font-size:11px;color:#555">${i === 0 ? 'Origin' : 'Destination'}</span>` : '')
    );
  });

  group.addTo(map);
  _singleRouteLayer = group;
  if (latLons.length) map.fitBounds(L.latLngBounds(latLons), { padding: [40, 40] });

  // Road-following path (async): fetch cached OSRM geometry from the backend,
  // fall back to straight segments between stops if it is unavailable.
  const drawPath = (coords, dashed) => {
    if (group !== _singleRouteLayer) return;   // a newer route was selected
    L.polyline(coords, {
      color, weight: 5, opacity: 0.85,
      dashArray: dashed ? '6 8' : null
    }).addTo(group);
  };
  if (route.route_id) {
    fetch(`/api/transport/routes/${route.route_id}/geometry`)
      .then(r => r.json())
      .then(g => {
        if (g.coords && g.coords.length) drawPath(g.coords, g.source !== 'osrm');
        else drawPath(latLons, true);
      })
      .catch(() => drawPath(latLons, true));
  } else {
    drawPath(latLons, true);
  }
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
