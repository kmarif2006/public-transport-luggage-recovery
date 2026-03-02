"""
TN Bus Lost & Found MVP
A simple Flask app for Tamil Nadu Government Bus lost luggage tracking.
No database - all data stored in memory (resets on restart).
"""

import os
import uuid
from datetime import datetime
from difflib import SequenceMatcher
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'tn-bus-lost-found-dev-key-2026')

# File upload config
UPLOAD_FOLDER = os.path.join('static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB max

# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ============================================================================
# HARDCODED DATA
# ============================================================================

ROUTES = [
    {
        "id": "ch-co",
        "name": "Chennai ↔ Coimbatore",
        "stops": ["Chennai", "Chengalpattu", "Villupuram", "Salem", "Erode", "Coimbatore"]
    },
    {
        "id": "ch-md",
        "name": "Chennai ↔ Madurai",
        "stops": ["Chennai", "Chengalpattu", "Villupuram", "Trichy", "Dindigul", "Madurai"]
    },
    {
        "id": "md-tn",
        "name": "Madurai ↔ Tirunelveli",
        "stops": ["Madurai", "Virudhunagar", "Kovilpatti", "Tirunelveli"]
    },
]

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

# ============================================================================
# IN-MEMORY STORAGE
# ============================================================================

lost_reports = []
found_reports = []

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_route_by_id(route_id):
    """Get route dict by its ID."""
    for route in ROUTES:
        if route["id"] == route_id:
            return route
    return None


def luggage_could_be_at_depot(stops, src, dst, depot_stop):
    """
    Check if luggage could be found at depot_stop.
    
    Logic: When a person gets down at 'dst', the luggage stays on the bus
    and continues to subsequent stops until the last stop of that direction.
    
    Example: Chennai → Chengalpattu → Villupuram → Salem → Erode → Coimbatore
    If person boards at Chennai (src) and gets down at Salem (dst),
    luggage could be at Erode or Coimbatore (stops AFTER dst in travel direction).
    """
    try:
        i = stops.index(src)
        j = stops.index(dst)
        k = stops.index(depot_stop)
        
        if i < j:
            # Traveling forward (e.g., Chennai to Coimbatore direction)
            # Luggage could be at any stop AFTER destination, up to last stop
            return k > j
        elif i > j:
            # Traveling backward (e.g., Coimbatore to Chennai direction)
            # Luggage could be at any stop AFTER destination (lower index), down to first stop
            return k < j
        else:
            # Source and destination are same - no valid journey
            return False
    except ValueError:
        return False


def is_match(desc_a, desc_b, threshold=0.25):
    """
    Simple text similarity check using SequenceMatcher.
    Returns True if similarity ratio >= threshold.
    """
    if not desc_a or not desc_b:
        return False
    ratio = SequenceMatcher(None, desc_a.lower(), desc_b.lower()).ratio()
    return ratio >= threshold


def allowed_file(filename):
    """Check if uploaded file has allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def find_matches_for_depot(depot_phone, found_report):
    """
    Find lost reports that match a found report for a specific depot.
    Matching criteria:
    1. Same route
    2. Same date
    3. Depot stop is between user's source and destination
    4. Description similarity passes threshold
    """
    matches = []
    depot = DEPOTS.get(depot_phone)
    if not depot:
        return matches
    
    route = get_route_by_id(found_report["route_id"])
    if not route:
        return matches
    
    depot_stop = depot["stop"]
    
    for lost in lost_reports:
        # Check route match
        if lost["route_id"] != found_report["route_id"]:
            continue
        
        # Check date match
        if lost["date"] != found_report["date"]:
            continue
        
        # Check if luggage could be at this depot (depot is after passenger's destination)
        if not luggage_could_be_at_depot(route["stops"], lost["source"], lost["destination"], depot_stop):
            continue
        
        # Check description similarity
        if not is_match(lost["description"], found_report["notes"]):
            continue
        
        matches.append(lost)
    
    return matches


# ============================================================================
# ROUTES - PUBLIC
# ============================================================================

@app.route('/')
def index():
    """Passenger page - report lost luggage."""
    return render_template('index.html', routes=ROUTES)


@app.route('/depot-login')
def depot_login_page():
    """Depot login page."""
    return render_template('depot_login.html', depots=DEPOTS)


@app.route('/lost', methods=['POST'])
def submit_lost():
    """Handle lost luggage report submission from passengers."""
    route_id = request.form.get('route_id')
    date = request.form.get('date')
    source = request.form.get('source')
    destination = request.form.get('destination')
    description = request.form.get('description')
    phone = request.form.get('phone')
    name = request.form.get('name')
    
    # Basic validation
    if not all([route_id, date, source, destination, description, phone, name]):
        flash('Please fill in all required fields.', 'error')
        return redirect(url_for('index'))
    
    # Validate route exists
    route = get_route_by_id(route_id)
    if not route:
        flash('Invalid route selected.', 'error')
        return redirect(url_for('index'))
    
    # Validate stops are in route
    if source not in route["stops"] or destination not in route["stops"]:
        flash('Invalid source or destination for selected route.', 'error')
        return redirect(url_for('index'))
    
    # Create report
    report = {
        "id": str(uuid.uuid4())[:8],
        "route_id": route_id,
        "route_name": route["name"],
        "date": date,
        "source": source,
        "destination": destination,
        "description": description,
        "phone": phone,
        "name": name,
        "created_at": datetime.now().isoformat()
    }
    
    lost_reports.append(report)
    
    flash(f'Lost report submitted successfully! Reference ID: {report["id"]}', 'success')
    return redirect(url_for('index'))


@app.route('/api/stops/<route_id>')
def get_stops(route_id):
    """API endpoint to get stops for a route (for dynamic dropdowns)."""
    route = get_route_by_id(route_id)
    if route:
        return {"stops": route["stops"]}
    return {"stops": []}, 404


# ============================================================================
# ROUTES - DEPOT
# ============================================================================

@app.route('/depot/login', methods=['POST'])
def depot_login():
    """Handle depot staff login."""
    phone = request.form.get('phone')
    password = request.form.get('password')
    
    if phone in DEPOTS and DEPOTS[phone]["password"] == password:
        session['depot_phone'] = phone
        session['depot_name'] = DEPOTS[phone]["name"]
        flash(f'Welcome, {DEPOTS[phone]["name"]}!', 'success')
        return redirect(url_for('depot_dashboard'))
    
    flash('Invalid phone number or password.', 'error')
    return redirect(url_for('depot_login_page'))


@app.route('/depot/logout')
def depot_logout():
    """Log out depot staff."""
    session.pop('depot_phone', None)
    session.pop('depot_name', None)
    flash('Logged out successfully.', 'success')
    return redirect(url_for('depot_login_page'))


@app.route('/depot')
def depot_dashboard():
    """Depot dashboard - show found form and matches."""
    if 'depot_phone' not in session:
        flash('Please login to access depot dashboard.', 'error')
        return redirect(url_for('depot_login_page'))
    
    depot_phone = session['depot_phone']
    depot = DEPOTS.get(depot_phone)
    
    if not depot:
        session.pop('depot_phone', None)
        flash('Invalid depot session.', 'error')
        return redirect(url_for('depot_login_page'))
    
    # Get routes this depot serves
    depot_routes = [r for r in ROUTES if r["id"] in depot["routes"]]
    
    # Get found reports submitted by this depot
    depot_found = [f for f in found_reports if f.get("depot_phone") == depot_phone]
    
    # Get all matches for this depot's found reports
    all_matches = []
    for found in depot_found:
        matches = find_matches_for_depot(depot_phone, found)
        if matches:
            all_matches.append({
                "found_report": found,
                "matches": matches
            })
    
    return render_template(
        'depot.html',
        depot=depot,
        depot_phone=depot_phone,
        routes=depot_routes,
        found_reports=depot_found,
        all_matches=all_matches
    )


@app.route('/depot/found', methods=['POST'])
def submit_found():
    """Handle found luggage report submission from depot."""
    if 'depot_phone' not in session:
        flash('Please login to submit found reports.', 'error')
        return redirect(url_for('depot_login_page'))
    
    depot_phone = session['depot_phone']
    depot = DEPOTS.get(depot_phone)
    
    if not depot:
        flash('Invalid depot session.', 'error')
        return redirect(url_for('depot_login_page'))
    
    route_id = request.form.get('route_id')
    date = request.form.get('date')
    notes = request.form.get('notes')
    
    # Basic validation
    if not all([route_id, date, notes]):
        flash('Please fill in all required fields.', 'error')
        return redirect(url_for('depot_dashboard'))
    
    # Validate route is served by this depot
    if route_id not in depot["routes"]:
        flash('This depot does not serve the selected route.', 'error')
        return redirect(url_for('depot_dashboard'))
    
    route = get_route_by_id(route_id)
    
    # Handle file upload
    image_path = None
    if 'image' in request.files:
        file = request.files['image']
        if file and file.filename and allowed_file(file.filename):
            filename = secure_filename(f"{uuid.uuid4().hex[:8]}_{file.filename}")
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            image_path = f"uploads/{filename}"
    
    # Create found report
    report = {
        "id": str(uuid.uuid4())[:8],
        "depot_phone": depot_phone,
        "depot_name": depot["name"],
        "route_id": route_id,
        "route_name": route["name"] if route else "Unknown",
        "date": date,
        "notes": notes,
        "image_path": image_path,
        "created_at": datetime.now().isoformat()
    }
    
    found_reports.append(report)
    
    # Find matches immediately
    matches = find_matches_for_depot(depot_phone, report)
    
    if matches:
        flash(f'Found report submitted! {len(matches)} potential match(es) found!', 'success')
    else:
        flash('Found report submitted successfully. No matches found yet.', 'success')
    
    return redirect(url_for('depot_dashboard'))


# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    app.run(debug=True, port=5003)

