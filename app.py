"""
app.py — TN Bus Lost & Found — Smart Recovery Platform
=======================================================
Architecture:
  - lost_reports  : submitted by passengers
  - found_reports : submitted by depot staff
  - matches       : persisted links between lost + found (with score + status)

All state is 100% database-driven — nothing is held in memory between requests.
"""

import os
import uuid
import logging
from datetime import datetime

from flask import (
    Flask, render_template, request,
    redirect, url_for, session, flash, jsonify
)
from werkzeug.utils import secure_filename
from pymongo import MongoClient
from dotenv import load_dotenv

from similarity import TextSimilarity, ImageSimilarity, UnifiedScorer

# ──────────────────────────────────────────────────────────────────────────────
# SECTION 1 — App Setup & Config
# ──────────────────────────────────────────────────────────────────────────────
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'tn-bus-lost-found-dev-key-2026')

# ── MongoDB ───────────────────────────────────────────────────────────────────
MONGO_URI = os.environ.get('MONGO_URI')
client = MongoClient(MONGO_URI)
db = client['tn_bus_lost_found']

lost_collection    = db['lost_reports']   # Passenger lost item reports
found_collection   = db['found_reports']  # Depot found item reports
matches_collection = db['matches']        # Persisted AI-match links
depots_collection  = db['depots']         # Depot credentials

# ── AI Models (loaded once at startup) ───────────────────────────────────────
logger.info("Initialising AI models…")
text_sim  = TextSimilarity()
image_sim = ImageSimilarity(db=db)
logger.info(f"CLIP available: {image_sim.available}")

# ── File Upload Config ────────────────────────────────────────────────────────
UPLOAD_FOLDER = os.path.join('static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024   # 5 MB
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# ──────────────────────────────────────────────────────────────────────────────
# SECTION 2 — Static Route & Depot Data
# ──────────────────────────────────────────────────────────────────────────────
# Stops include lat/lon for the Leaflet map.
ROUTES = [
    {
        "id": "ch-co",
        "name": "Chennai ↔ Coimbatore",
        "color": "#1F6FB2",
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
        "color": "#C62828",
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
        "color": "#2E7D32",
        "stops": [
            {"name": "Madurai",      "lat":  9.9252, "lon": 78.1198},
            {"name": "Virudhunagar", "lat":  9.5851, "lon": 77.9624},
            {"name": "Kovilpatti",   "lat":  9.1710, "lon": 77.8652},
            {"name": "Tirunelveli",  "lat":  8.7139, "lon": 77.7567},
        ]
    },
]

# Build a quick stop-name → coords lookup used by the map API
STOP_COORDS = {
    stop["name"]: (stop["lat"], stop["lon"])
    for route in ROUTES
    for stop in route["stops"]
}

# Depot credentials (same as seed_db.py — kept here for login auth)
DEPOTS = {
    "9000000001": {"name": "Chennai Depot",     "password": "pass123", "stop": "Chennai",     "routes": ["ch-co", "ch-md"]},
    "9000000002": {"name": "Coimbatore Depot",  "password": "pass123", "stop": "Coimbatore",  "routes": ["ch-co"]},
    "9000000003": {"name": "Madurai Depot",     "password": "pass123", "stop": "Madurai",     "routes": ["ch-md", "md-tn"]},
    "9000000004": {"name": "Salem Depot",       "password": "pass123", "stop": "Salem",       "routes": ["ch-co"]},
    "9000000005": {"name": "Tirunelveli Depot", "password": "pass123", "stop": "Tirunelveli", "routes": ["md-tn"]},
}


# ──────────────────────────────────────────────────────────────────────────────
# SECTION 3 — Helper Functions
# ──────────────────────────────────────────────────────────────────────────────

def get_route_by_id(route_id: str):
    """Return the route dict for a given route ID, or None."""
    for route in ROUTES:
        if route["id"] == route_id:
            return route
    return None

def get_stop_names(route: dict) -> list:
    """Return a plain list of stop name strings from a route dict."""
    return [s["name"] for s in route["stops"]]

def allowed_file(filename: str) -> bool:
    """True if the file extension is in the allowed set."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def generate_tracking_id() -> str:
    """Return a human-readable tracking ID like TRK-A1B2C3D4."""
    return f"TRK-{uuid.uuid4().hex[:8].upper()}"

def save_uploaded_image(file) -> str:
    """
    Save an uploaded image to the uploads folder.
    Returns relative path like 'uploads/abc.jpg', or None if invalid.
    """
    if file and file.filename and allowed_file(file.filename):
        filename = secure_filename(f"{uuid.uuid4().hex[:8]}_{file.filename}")
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        return f"uploads/{filename}"
    return None

def get_depots() -> dict:
    """Load depot info from MongoDB into a dict keyed by phone number."""
    return {d["phone"]: d for d in depots_collection.find()}

def luggage_could_be_at_depot(stops: list, src: str, dst: str, depot_stop: str) -> bool:
    """
    Check if a lost item could have reached the depot.

    When a passenger gets off at 'dst', their luggage stays on the bus
    and travels to later stops. So the depot must come AFTER 'dst'.

    Example: src=Chennai, dst=Salem → depot could be Erode or Coimbatore.
    """
    try:
        i = stops.index(src)
        j = stops.index(dst)
        k = stops.index(depot_stop)
        if i < j:
            return k > j    # Forward journey: depot is past destination
        elif i > j:
            return k < j    # Reverse journey: depot is before destination
        else:
            return False    # Same stop — invalid
    except ValueError:
        return False        # Stop not in this route


# ──────────────────────────────────────────────────────────────────────────────
# SECTION 4 — Matching Engine
# ──────────────────────────────────────────────────────────────────────────────

def compute_and_save_matches(found_report: dict, depot_stop: str) -> int:
    """
    Run AI matching for a found report against ALL pending lost reports.
    Save each qualifying match to the 'matches' collection (upsert — no duplicates).

    Returns the count of new matches saved.
    """
    found_id  = found_report["found_id"]
    route     = get_route_by_id(found_report.get("route_id", ""))
    if not route:
        return 0

    stops = get_stop_names(route)

    # Pre-compute the found item's image embedding (cached in MongoDB by ImageSimilarity)
    found_img_full = None
    if found_report.get("image_path"):
        found_img_full = os.path.join("static", found_report["image_path"])

    new_matches = 0

    # Only consider lost reports that are still pending (not already resolved)
    pending_lost = lost_collection.find({
        "route_id": found_report.get("route_id"),
        "date":     found_report.get("date"),
        "status":   {"$ne": "resolved"}
    })

    for lost in pending_lost:
        # ── Hard filter: route logic ──────────────────────────────────────────
        if not luggage_could_be_at_depot(
            stops, lost.get("source", ""), lost.get("destination", ""), depot_stop
        ):
            continue

        # ── Text similarity ────────────────────────────────────────────────────
        text_score = text_sim.similarity(
            lost.get("description", ""),
            found_report.get("notes", "")
        )

        # ── Image similarity (optional) ────────────────────────────────────────
        image_score = 0.0
        if found_img_full and lost.get("image_path"):
            image_score = image_sim.similarity(
                found_img_full,
                os.path.join("static", lost["image_path"])
            )

        # ── Unified score ─────────────────────────────────────────────────────
        score = UnifiedScorer.compute(text_score, image_score, route_score=1.0)

        if not score["is_match"]:
            continue

        # ── Upsert into matches collection ────────────────────────────────────
        # Use (found_id + request_id) as the unique key — prevents duplicates
        # even if matching runs multiple times for the same pair.
        matches_collection.update_one(
            {
                "found_id":   found_id,
                "request_id": lost["request_id"]
            },
            {
                "$setOnInsert": {
                    "found_id":    found_id,
                    "request_id":  lost["request_id"],
                    "depot_phone": found_report["depot_phone"],
                    "depot_name":  found_report["depot_name"],
                    "score":       score,
                    "status":      "pending",   # pending → resolved
                    "created_at":  datetime.now().isoformat()
                }
            },
            upsert=True
        )
        new_matches += 1

    return new_matches


def get_matches_for_depot(depot_phone: str) -> list:
    """
    Load all non-resolved matches for this depot from MongoDB.
    Enriches each match with the full lost_report and found_report data.
    Groups them by found_id for display.
    """
    # Fetch only pending matches belonging to this depot
    raw_matches = list(matches_collection.find({
        "depot_phone": depot_phone,
        "status":      {"$ne": "resolved"}
    }).sort("created_at", -1))

    if not raw_matches:
        return []

    # Collect all unique found_ids and request_ids for batch fetching
    found_ids   = list({m["found_id"]   for m in raw_matches})
    request_ids = list({m["request_id"] for m in raw_matches})

    # Batch fetch from DB (much faster than one query per match)
    found_map = {
        f["found_id"]: f
        for f in found_collection.find({"found_id": {"$in": found_ids}})
    }
    lost_map = {
        l["request_id"]: l
        for l in lost_collection.find({"request_id": {"$in": request_ids}})
    }

    # Group matches by found_id
    groups = {}
    for match in raw_matches:
        fid  = match["found_id"]
        rid  = match["request_id"]
        lost = lost_map.get(rid)
        if not lost:
            continue   # Lost report deleted — skip

        # Attach score and match_id to the lost report dict for the template
        enriched_lost = dict(lost)
        enriched_lost["score"]    = match["score"]
        enriched_lost["match_id"] = str(match["_id"])

        if fid not in groups:
            groups[fid] = {
                "found_report": found_map.get(fid, {}),
                "matches":      []
            }
        groups[fid]["matches"].append(enriched_lost)

    # Sort each group's matches by score descending
    result = list(groups.values())
    for g in result:
        g["matches"].sort(key=lambda x: x["score"]["final"], reverse=True)

    return result


# ──────────────────────────────────────────────────────────────────────────────
# SECTION 5 — Passenger Routes
# ──────────────────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    """Passenger homepage: report form + Leaflet map."""
    last_tracking_id = session.pop('last_tracking_id', None)
    return render_template('index.html', routes=ROUTES, last_tracking_id=last_tracking_id)


@app.route('/lost', methods=['POST'])
def submit_lost():
    """Accept a lost luggage report from a passenger."""
    route_id    = request.form.get('route_id')
    date        = request.form.get('date')
    source      = request.form.get('source')
    destination = request.form.get('destination')
    description = request.form.get('description')
    phone       = request.form.get('phone')
    name        = request.form.get('name')

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

    tracking_id = generate_tracking_id()
    request_id  = uuid.uuid4().hex   # Internal unique key for DB relations

    report = {
        "request_id":    request_id,    # Unique internal ID (used in matches)
        "tracking_id":   tracking_id,   # Human-readable ID shown to passenger
        "route_id":      route_id,
        "route_name":    route["name"],
        "date":          date,
        "source":        source,
        "destination":   destination,
        "description":   description,
        "phone":         phone,
        "name":          name,
        "status":        "pending",     # pending | resolved
        "matched_depot": None,
        "matched_at":    None,
        "created_at":    datetime.now().isoformat()
    }

    lost_collection.insert_one(report)

    flash(
        f'Report submitted! Your Tracking ID is <strong>{tracking_id}</strong> — '
        f'save it to check your claim status.',
        'success'
    )
    session['last_tracking_id'] = tracking_id
    return redirect(url_for('index'))


@app.route('/status')
def status_page():
    """Passenger self-service status check page."""
    return render_template('status.html')


# ──────────────────────────────────────────────────────────────────────────────
# SECTION 6 — Depot Staff Routes
# ──────────────────────────────────────────────────────────────────────────────

@app.route('/depot-login')
def depot_login_page():
    return render_template('depot_login.html', depots=get_depots())


@app.route('/depot/login', methods=['POST'])
def depot_login():
    phone    = request.form.get('phone')
    password = request.form.get('password')
    depots   = get_depots()

    if phone in depots and depots[phone]["password"] == password:
        session['depot_phone'] = phone
        session['depot_name']  = depots[phone]["name"]
        flash(f'Welcome, {depots[phone]["name"]}!', 'success')
        return redirect(url_for('depot_dashboard'))

    flash('Invalid phone number or password.', 'error')
    return redirect(url_for('depot_login_page'))


@app.route('/depot/logout')
def depot_logout():
    session.pop('depot_phone', None)
    session.pop('depot_name',  None)
    flash('Logged out successfully.', 'success')
    return redirect(url_for('depot_login_page'))


@app.route('/depot')
def depot_dashboard():
    """Depot dashboard: register found items + view AI matches from DB."""
    if 'depot_phone' not in session:
        flash('Please login to access depot dashboard.', 'error')
        return redirect(url_for('depot_login_page'))

    depot_phone = session['depot_phone']
    depots      = get_depots()
    depot       = depots.get(depot_phone)

    if not depot:
        session.clear()
        flash('Invalid depot session.', 'error')
        return redirect(url_for('depot_login_page'))

    depot_routes = [r for r in ROUTES if r["id"] in depot["routes"]]
    depot_found  = list(found_collection.find(
        {"depot_phone": depot_phone}
    ).sort("created_at", -1))

    # Load matches from DB (not recomputed — already populated at submit_found time)
    all_matches = get_matches_for_depot(depot_phone)

    return render_template(
        'depot.html',
        depot=depot,
        depot_phone=depot_phone,
        routes=depot_routes,
        found_reports=depot_found,
        all_matches=all_matches,
        clip_available=image_sim.available
    )


@app.route('/depot/found', methods=['POST'])
def submit_found():
    """Accept a found luggage report from depot staff and run AI matching."""
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

    # Handle optional image upload
    image_path = None
    if 'image' in request.files:
        image_path = save_uploaded_image(request.files['image'])

    # Pre-compute CLIP embedding now so matching is fast later
    if image_path and image_sim.available:
        image_sim.embed(os.path.join("static", image_path))

    found_id = uuid.uuid4().hex   # Unique internal ID for this found report

    report = {
        "found_id":    found_id,          # Unique internal ID (used in matches)
        "id":          found_id[:8],      # Short display ID
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

    # Run AI matching and SAVE results to matches collection
    n = compute_and_save_matches(report, depot["stop"])

    if n > 0:
        flash(f'Found report submitted! {n} potential match(es) found!', 'success')
    else:
        flash('Found report submitted. No matches yet.', 'success')

    return redirect(url_for('depot_dashboard'))


# ──────────────────────────────────────────────────────────────────────────────
# SECTION 7 — API Endpoints
# ──────────────────────────────────────────────────────────────────────────────

@app.route('/api/status/<tracking_id>')
def api_status(tracking_id: str):
    """
    Return JSON status of a lost report by tracking ID.
    Used by the passenger 'Check Status' page.
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
    """Return all routes with stop coordinates for the Leaflet map."""
    return jsonify(ROUTES)


@app.route('/api/stops/<route_id>')
def get_stops(route_id: str):
    """Return stop names for a route (backward-compatible dropdown API)."""
    route = get_route_by_id(route_id)
    if route:
        return jsonify({"stops": get_stop_names(route)})
    return jsonify({"stops": []}), 404


@app.route('/api/match/resolve', methods=['POST'])
def resolve_match():
    """
    Mark a specific match as resolved.
    Updates BOTH the matches collection AND the lost_reports collection.

    Expected JSON body:
      { "match_id": "<MongoDB ObjectId hex>", "request_id": "<uuid hex>" }

    Why both IDs?
      - match_id   → mark THIS specific found↔lost pairing as resolved
      - request_id → mark the lost report itself as resolved (stops future matches)
    """
    if 'depot_phone' not in session:
        return jsonify({"success": False, "message": "Not authenticated"}), 401

    data       = request.get_json(silent=True) or {}
    match_id   = data.get('match_id', '').strip()
    request_id = data.get('request_id', '').strip()
    depot_name = session.get('depot_name', '')

    # Validate required fields
    if not match_id or not request_id:
        return jsonify({
            "success": False,
            "message": "Both match_id and request_id are required."
        }), 400

    from bson import ObjectId

    # ── Step 1: Mark this match as resolved ───────────────────────────────────
    match_result = matches_collection.update_one(
        {"_id": ObjectId(match_id), "status": {"$ne": "resolved"}},
        {"$set": {
            "status":      "resolved",
            "resolved_at": datetime.now().isoformat(),
            "resolved_by": depot_name
        }}
    )

    if match_result.modified_count == 0:
        return jsonify({
            "success": False,
            "message": "Match not found or already resolved."
        }), 404

    # ── Step 2: Mark the lost report as resolved ──────────────────────────────
    # This prevents it from matching other found reports in the future.
    lost_collection.update_one(
        {"request_id": request_id},
        {"$set": {
            "status":        "resolved",
            "matched_depot": depot_name,
            "matched_at":    datetime.now().isoformat()
        }}
    )

    # ── Step 3: Cancel all OTHER pending matches for this lost report ─────────
    # Once resolved, there's no point showing the same lost item under
    # other found reports in the depot dashboard.
    matches_collection.update_many(
        {
            "request_id": request_id,
            "status":     "pending"
        },
        {"$set": {"status": "cancelled"}}
    )

    return jsonify({
        "success": True,
        "message": "Match resolved successfully."
    })


# ──────────────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    app.run(debug=True, use_reloader=False, port=5003)
