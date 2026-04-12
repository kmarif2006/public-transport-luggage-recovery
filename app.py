"""
app.py — TN Bus Lost & Found — Smart Recovery Platform
=======================================================
Main Flask application.  Structured in clear sections:

  SECTION 1 — App setup & config
  SECTION 2 — Route & depot data
  SECTION 3 — Helper functions (route logic, file handling)
  SECTION 4 — Matching engine (unified scoring)
  SECTION 5 — Flask routes (passengers)
  SECTION 6 — Flask routes (depot staff)
  SECTION 7 — API endpoints (status, routes for map, resolve)
"""

import os
import uuid
import logging
from datetime import datetime
from functools import lru_cache

from flask import (
    Flask, render_template, request,
    redirect, url_for, session, flash, jsonify
)
from werkzeug.utils import secure_filename
from pymongo import MongoClient
from dotenv import load_dotenv

# Our own AI engine — see similarity.py
from similarity import TextSimilarity, ImageSimilarity, UnifiedScorer

# ──────────────────────────────────────────────────────────────────────────────
# SECTION 1 — App Setup & Config
# ──────────────────────────────────────────────────────────────────────────────
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'tn-bus-lost-found-dev-key-2026')

# ── MongoDB ──────────────────────────────────────────────────────────────────
MONGO_URI = os.environ.get('MONGO_URI')
client = MongoClient(MONGO_URI)
db = client['tn_bus_lost_found']

lost_collection   = db['lost_reports']
found_collection  = db['found_reports']
depots_collection = db['depots']
# image_embeddings collection is managed internally by ImageSimilarity

# ── AI models (loaded once at startup) ───────────────────────────────────────
logger.info("Initialising AI models…")
text_sim  = TextSimilarity()                 # SBERT
image_sim = ImageSimilarity(db=db)           # CLIP (optional, graceful fallback)
scorer    = UnifiedScorer()
logger.info(f"CLIP available: {image_sim.available}")

# ── File upload config ────────────────────────────────────────────────────────
UPLOAD_FOLDER = os.path.join('static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024   # 5 MB

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# ──────────────────────────────────────────────────────────────────────────────
# SECTION 2 — Route & Depot Data
# ──────────────────────────────────────────────────────────────────────────────
# Each stop has lat/lon coordinates for the Leaflet map.
ROUTES = [
    {
        "id": "ch-co",
        "name": "Chennai ↔ Coimbatore",
        "color": "#1F6FB2",   # Blue on map
        "stops": [
            {"name": "Chennai",      "lat": 13.0827, "lon": 80.2707},
            {"name": "Chengalpattu", "lat": 12.6919, "lon": 79.9765},
            {"name": "Villupuram",   "lat": 11.9390, "lon": 79.4938},
            {"name": "Salem",        "lat": 11.6643, "lon": 78.1460},
            {"name": "Erode",        "lat": 11.3410, "lon": 77.7172},
            {"name": "Coimbatore",   "lat": 11.0168, "lon": 76.9558},
        ]
    },
    {
        "id": "ch-md",
        "name": "Chennai ↔ Madurai",
        "color": "#C62828",   # Red on map
        "stops": [
            {"name": "Chennai",      "lat": 13.0827, "lon": 80.2707},
            {"name": "Chengalpattu", "lat": 12.6919, "lon": 79.9765},
            {"name": "Villupuram",   "lat": 11.9390, "lon": 79.4938},
            {"name": "Trichy",       "lat": 10.7905, "lon": 78.7047},
            {"name": "Dindigul",     "lat": 10.3624, "lon": 77.9695},
            {"name": "Madurai",      "lat":  9.9252, "lon": 78.1198},
        ]
    },
    {
        "id": "md-tn",
        "name": "Madurai ↔ Tirunelveli",
        "color": "#2E7D32",   # Green on map
        "stops": [
            {"name": "Madurai",      "lat":  9.9252, "lon": 78.1198},
            {"name": "Virudhunagar", "lat":  9.5851, "lon": 77.9624},
            {"name": "Kovilpatti",   "lat":  9.1710, "lon": 77.8652},
            {"name": "Tirunelveli", "lat":  8.7139, "lon": 77.7567},
        ]
    },
]

# Map stop name → (lat, lon) for quick lookup
STOP_COORDS = {}
for route in ROUTES:
    for stop in route["stops"]:
        STOP_COORDS[stop["name"]] = (stop["lat"], stop["lon"])

DEPOTS = {
    "9000000001": {
        "name": "Chennai Depot",
        "password": "pass123",
        "stop": "Chennai",
        "routes": ["ch-co", "ch-md"]
    },
    "9000000002": {
        "name": "Coimbatore Depot",
        "password": "pass123",
        "stop": "Coimbatore",
        "routes": ["ch-co"]
    },
    "9000000003": {
        "name": "Madurai Depot",
        "password": "pass123",
        "stop": "Madurai",
        "routes": ["ch-md", "md-tn"]
    },
    "9000000004": {
        "name": "Salem Depot",
        "password": "pass123",
        "stop": "Salem",
        "routes": ["ch-co"]
    },
    "9000000005": {
        "name": "Tirunelveli Depot",
        "password": "pass123",
        "stop": "Tirunelveli",
        "routes": ["md-tn"]
    },
}


# ──────────────────────────────────────────────────────────────────────────────
# SECTION 3 — Helper Functions
# ──────────────────────────────────────────────────────────────────────────────

def get_lost_reports():
    return list(lost_collection.find().sort("created_at", -1))

def get_found_reports():
    return list(found_collection.find().sort("created_at", -1))

def get_depots():
    """Load depot info from MongoDB into a dict keyed by phone."""
    return {d["phone"]: d for d in depots_collection.find()}

def get_route_by_id(route_id: str) -> dict | None:
    """Return the route dict for a given route ID string."""
    for route in ROUTES:
        if route["id"] == route_id:
            return route
    return None

def get_stop_names(route: dict) -> list[str]:
    """Extract a plain list of stop name strings from a route dict."""
    return [s["name"] for s in route["stops"]]

def allowed_file(filename: str) -> bool:
    """Check if the uploaded file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def generate_tracking_id() -> str:
    """Generate a human-readable tracking ID like TRK-A1B2C3D4."""
    unique = uuid.uuid4().hex[:8].upper()
    return f"TRK-{unique}"

def save_uploaded_image(file) -> str | None:
    """
    Save an uploaded image file to the uploads folder.
    Returns the relative path (e.g. 'uploads/abc.jpg') or None.
    """
    if file and file.filename and allowed_file(file.filename):
        filename = secure_filename(f"{uuid.uuid4().hex[:8]}_{file.filename}")
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        return f"uploads/{filename}"
    return None

def luggage_could_be_at_depot(stops: list, src: str, dst: str, depot_stop: str) -> bool:
    """
    Determine whether a passenger's lost luggage could have ended up
    at a given depot stop.

    Logic:
      After a passenger alights at 'dst', the luggage remains on the bus
      and travels to subsequent stops.  So the depot must be AFTER 'dst'
      in the direction of travel.

    Example (Chennai → Coimbatore direction):
      src=Chennai, dst=Salem → luggage could be at Erode or Coimbatore.
    """
    try:
        i = stops.index(src)
        j = stops.index(dst)
        k = stops.index(depot_stop)
        if i < j:            # Forward direction
            return k > j
        elif i > j:          # Reverse direction
            return k < j
        else:
            return False     # Same stop — invalid journey
    except ValueError:
        return False         # Stop not found in route


# ──────────────────────────────────────────────────────────────────────────────
# SECTION 4 — Matching Engine (Unified Scoring)
# ──────────────────────────────────────────────────────────────────────────────

def find_matches_for_depot(depot_phone: str, found_report: dict) -> list[dict]:
    """
    Find all lost reports that are potential matches for a found item.

    For each candidate lost report, computes:
      - text_score  : SBERT cosine similarity of descriptions
      - image_score : CLIP cosine similarity of images (0 if no images)
      - route_score : 1.0 if route logic passes, else 0.0
      - final_score : 0.5*text + 0.3*image + 0.2*route

    Returns a list of dicts:
      { ...lost_report_fields..., "score": {text, image, route, final, is_match} }
    sorted by final_score descending.
    """
    depots = get_depots()
    depot  = depots.get(depot_phone)
    if not depot:
        return []

    route = get_route_by_id(found_report.get("route_id", ""))
    if not route:
        return []

    depot_stop = depot["stop"]
    stops      = get_stop_names(route)

    # Precompute found-item image embedding once (reused for all candidates)
    found_img_path = None
    if found_report.get("image_path"):
        found_img_path = os.path.join("static", found_report["image_path"])

    results = []

    for lost in get_lost_reports():
        # ── Filter: must be same route and same date ──────────────────────────
        if lost.get("route_id") != found_report.get("route_id"):
            continue
        if lost.get("date") != found_report.get("date"):
            continue

        # ── Filter: route logic — depot must be after passenger's destination ─
        route_ok = luggage_could_be_at_depot(
            stops, lost.get("source", ""), lost.get("destination", ""), depot_stop
        )
        route_score = 1.0 if route_ok else 0.0
        if not route_ok:
            continue   # Skip immediately — route mismatch is a hard filter

        # ── Text similarity ────────────────────────────────────────────────────
        text_score = text_sim.similarity(
            lost.get("description", ""),
            found_report.get("notes", "")
        )

        # ── Image similarity (optional) ────────────────────────────────────────
        image_score = 0.0
        if found_img_path and lost.get("image_path"):
            lost_img_path = os.path.join("static", lost["image_path"])
            image_score = image_sim.similarity(found_img_path, lost_img_path)

        # ── Compute unified score ──────────────────────────────────────────────
        score = UnifiedScorer.compute(text_score, image_score, route_score)

        if score["is_match"]:
            lost_with_score = dict(lost)           # copy the lost report
            lost_with_score["score"] = score       # attach score breakdown
            results.append(lost_with_score)

    # Sort best matches first
    results.sort(key=lambda x: x["score"]["final"], reverse=True)
    return results


# ──────────────────────────────────────────────────────────────────────────────
# SECTION 5 — Flask Routes (Passenger-facing)
# ──────────────────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    """Passenger homepage — lost luggage report form + Leaflet map."""
    # Pop the tracking ID so the success card only shows once after submission
    last_tracking_id = session.pop('last_tracking_id', None)
    return render_template('index.html', routes=ROUTES, last_tracking_id=last_tracking_id)


@app.route('/lost', methods=['POST'])
def submit_lost():
    """Handle lost luggage report submission from passengers."""
    route_id    = request.form.get('route_id')
    date        = request.form.get('date')
    source      = request.form.get('source')
    destination = request.form.get('destination')
    description = request.form.get('description')
    phone       = request.form.get('phone')
    name        = request.form.get('name')

    # Basic validation
    if not all([route_id, date, source, destination, description, phone, name]):
        flash('Please fill in all required fields.', 'error')
        return redirect(url_for('index'))

    route = get_route_by_id(route_id)
    if not route:
        flash('Invalid route selected.', 'error')
        return redirect(url_for('index'))

    stop_names = get_stop_names(route)
    if source not in stop_names or destination not in stop_names:
        flash('Invalid source or destination for selected route.', 'error')
        return redirect(url_for('index'))

    # Generate unique tracking ID (human-readable)
    tracking_id = generate_tracking_id()

    # Build and save report
    report = {
        "tracking_id":  tracking_id,                  # NEW: TRK-XXXXXXXX
        "id":           str(uuid.uuid4())[:8],
        "route_id":     route_id,
        "route_name":   route["name"],
        "date":         date,
        "source":       source,
        "destination":  destination,
        "description":  description,
        "phone":        phone,
        "name":         name,
        "status":       "pending",                    # NEW: tracking status
        "matched_depot": None,                         # NEW: filled when matched
        "matched_at":   None,                          # NEW: filled when matched
        "created_at":   datetime.now().isoformat()
    }

    lost_collection.insert_one(report)

    flash(
        f'Report submitted! Your Tracking ID is <strong>{tracking_id}</strong> — '
        f'save it to check your claim status.',
        'success'
    )
    # Pass tracking_id in session so index.html can display it prominently
    session['last_tracking_id'] = tracking_id
    return redirect(url_for('index'))


@app.route('/status')
def status_page():
    """Passenger 'Check Status' page — enter tracking ID to see status."""
    return render_template('status.html')


# ──────────────────────────────────────────────────────────────────────────────
# SECTION 6 — Flask Routes (Depot Staff)
# ──────────────────────────────────────────────────────────────────────────────

@app.route('/depot-login')
def depot_login_page():
    """Depot login page."""
    return render_template('depot_login.html', depots=get_depots())


@app.route('/depot/login', methods=['POST'])
def depot_login():
    """Handle depot staff login."""
    phone    = request.form.get('phone')
    password = request.form.get('password')

    depots = get_depots()
    if phone in depots and depots[phone]["password"] == password:
        session['depot_phone'] = phone
        session['depot_name']  = depots[phone]["name"]
        flash(f'Welcome, {depots[phone]["name"]}!', 'success')
        return redirect(url_for('depot_dashboard'))

    flash('Invalid phone number or password.', 'error')
    return redirect(url_for('depot_login_page'))


@app.route('/depot/logout')
def depot_logout():
    """Log out depot staff."""
    session.pop('depot_phone', None)
    session.pop('depot_name',  None)
    flash('Logged out successfully.', 'success')
    return redirect(url_for('depot_login_page'))


@app.route('/depot')
def depot_dashboard():
    """Depot dashboard — found item form + matched lost reports."""
    if 'depot_phone' not in session:
        flash('Please login to access depot dashboard.', 'error')
        return redirect(url_for('depot_login_page'))

    depot_phone = session['depot_phone']
    depots      = get_depots()
    depot       = depots.get(depot_phone)

    if not depot:
        session.pop('depot_phone', None)
        flash('Invalid depot session.', 'error')
        return redirect(url_for('depot_login_page'))

    depot_routes = [r for r in ROUTES if r["id"] in depot["routes"]]
    depot_found  = list(found_collection.find({"depot_phone": depot_phone}).sort("created_at", -1))

    # Run matching for every found report this depot has logged
    all_matches = []
    for found in depot_found:
        matches = find_matches_for_depot(depot_phone, found)
        if matches:
            all_matches.append({
                "found_report": found,
                "matches":      matches    # each match has a .score dict
            })

    return render_template(
        'depot.html',
        depot=depot,
        depot_phone=depot_phone,
        routes=depot_routes,
        found_reports=depot_found,
        all_matches=all_matches,
        clip_available=image_sim.available    # show/hide image score badge
    )


@app.route('/depot/found', methods=['POST'])
def submit_found():
    """Handle found luggage report from depot staff."""
    if 'depot_phone' not in session:
        flash('Please login to submit found reports.', 'error')
        return redirect(url_for('depot_login_page'))

    depot_phone = session['depot_phone']
    depots      = get_depots()
    depot       = depots.get(depot_phone)

    if not depot:
        flash('Invalid depot session.', 'error')
        return redirect(url_for('depot_login_page'))

    route_id = request.form.get('route_id')
    date     = request.form.get('date')
    notes    = request.form.get('notes')

    if not all([route_id, date, notes]):
        flash('Please fill in all required fields.', 'error')
        return redirect(url_for('depot_dashboard'))

    if route_id not in depot["routes"]:
        flash('This depot does not serve the selected route.', 'error')
        return redirect(url_for('depot_dashboard'))

    route = get_route_by_id(route_id)

    # Handle image upload
    image_path = None
    if 'image' in request.files:
        image_path = save_uploaded_image(request.files['image'])

    # Pre-compute CLIP embedding for uploaded image (stored in MongoDB for reuse)
    if image_path and image_sim.available:
        full_path = os.path.join("static", image_path)
        image_sim.embed(full_path)   # result auto-cached in MongoDB

    report = {
        "id":          str(uuid.uuid4())[:8],
        "depot_phone": depot_phone,
        "depot_name":  depot["name"],
        "route_id":    route_id,
        "route_name":  route["name"] if route else "Unknown",
        "date":        date,
        "notes":       notes,
        "image_path":  image_path,
        "status":      "open",
        "created_at":  datetime.now().isoformat()
    }

    found_collection.insert_one(report)

    matches = find_matches_for_depot(depot_phone, report)
    if matches:
        flash(f'Found report submitted! {len(matches)} potential match(es) found!', 'success')
    else:
        flash('Found report submitted. No matches yet — check back as more reports come in.', 'success')

    return redirect(url_for('depot_dashboard'))


# ──────────────────────────────────────────────────────────────────────────────
# SECTION 7 — API Endpoints
# ──────────────────────────────────────────────────────────────────────────────

@app.route('/api/status/<tracking_id>')
def api_status(tracking_id: str):
    """
    JSON endpoint: return status of a lost report by tracking ID.

    Response:
      { found: true, tracking_id, status, name, route_name,
        date, description, matched_depot, matched_at }
      or
      { found: false, message: "..." }
    """
    tracking_id = tracking_id.strip().upper()
    report = lost_collection.find_one({"tracking_id": tracking_id})
    if not report:
        return jsonify({"found": False, "message": "Tracking ID not found."}), 404

    return jsonify({
        "found":         True,
        "tracking_id":   report.get("tracking_id"),
        "status":        report.get("status", "pending"),
        "name":          report.get("name"),
        "route_name":    report.get("route_name"),
        "date":          report.get("date"),
        "description":   report.get("description"),
        "matched_depot": report.get("matched_depot"),
        "matched_at":    report.get("matched_at"),
        "created_at":    report.get("created_at")
    })


@app.route('/api/routes')
def api_routes():
    """
    JSON endpoint: return all routes with stop coordinates.
    Used by Leaflet.js map on the frontend.

    Response: list of route objects, each with id, name, color, stops[{name,lat,lon}]
    """
    return jsonify(ROUTES)


@app.route('/api/stops/<route_id>')
def get_stops(route_id: str):
    """
    JSON endpoint: return stop NAMES for a route (used by form dropdowns).
    Kept for backward-compatibility.
    """
    route = get_route_by_id(route_id)
    if route:
        return jsonify({"stops": get_stop_names(route)})
    return jsonify({"stops": []}), 404


@app.route('/api/match/resolve', methods=['POST'])
def resolve_match():
    """
    Mark a lost report as 'resolved' and record which depot found it.
    Called by depot staff when they confirm a passenger has collected their item.

    POST body (form or JSON):
      { tracking_id: "TRK-XXXX", depot_phone: "9000000001" }
    """
    if 'depot_phone' not in session:
        return jsonify({"success": False, "message": "Not authenticated"}), 401

    data = request.get_json(silent=True) or request.form
    tracking_id  = (data.get('tracking_id') or '').strip().upper()
    depot_phone  = session['depot_phone']
    depot_name   = session.get('depot_name', '')

    if not tracking_id:
        return jsonify({"success": False, "message": "tracking_id required"}), 400

    result = lost_collection.update_one(
        {"tracking_id": tracking_id, "status": {"$ne": "resolved"}},
        {"$set": {
            "status":        "resolved",
            "matched_depot": depot_name,
            "matched_at":    datetime.now().isoformat()
        }}
    )

    if result.modified_count == 0:
        return jsonify({"success": False, "message": "Report not found or already resolved"}), 404

    return jsonify({"success": True, "message": f"Report {tracking_id} marked as resolved."})


# ──────────────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    app.run(debug=True, port=5003)
