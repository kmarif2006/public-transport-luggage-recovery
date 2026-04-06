"""
seed_managers.py — Seeds all depot manager accounts into MongoDB.
Run this ONCE after seeding depots:  python seed_managers.py

Credentials follow the pattern in manager_credentials.json:
  Email   : manager.{DEPOT_ID}@tnstc.gov.in
  Password: {DEPOT_ID}_pass123
"""
import os
import json
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

try:
    from flask_bcrypt import Bcrypt
    _bcrypt = Bcrypt()

    class FakeApp:
        config = {}

    _bcrypt.init_app(FakeApp())

    def hash_pw(pw):
        return _bcrypt.generate_password_hash(pw).decode("utf-8")

except ImportError:
    import bcrypt as _bcrypt_raw

    def hash_pw(pw):
        return _bcrypt_raw.hashpw(pw.encode(), _bcrypt_raw.gensalt()).decode("utf-8")


def seed_managers():
    uri = os.environ.get("MONGODB_URI")
    db_name = os.environ.get("MONGODB_DB_NAME", "tn_bus_lost_luggage")

    print(f"[SEED] Connecting to: {db_name}")
    client = MongoClient(uri, tlsAllowInvalidCertificates=True)
    db = client[db_name]

    # Load credentials from JSON file
    creds_path = os.path.join(os.path.dirname(__file__), "manager_credentials.json")
    with open(creds_path, "r") as f:
        creds_data = json.load(f)

    managers_data = creds_data.get("managers", [])

    # Get existing depots to match names
    depots = {d["depot_id"]: d for d in db.depots.find()}

    created = 0
    skipped = 0

    for m in managers_data:
        depot_id = m["depot_id"]
        email = m["manager_email"].lower()
        password = m["default_password"]

        # Skip if manager already exists
        if db.users.find_one({"email": email}):
            print(f"  [SKIP] {email} already exists")
            skipped += 1
            continue

        # Find matching depot (case-insensitive)
        depot = depots.get(depot_id) or depots.get(depot_id.upper()) or depots.get(depot_id.lower())
        depot_name = depot["name"] if depot else f"Depot {depot_id}"

        user_doc = {
            "name": f"Manager — {depot_name}",
            "email": email,
            "password_hash": hash_pw(password),
            "google_id": None,
            "microsoft_id": None,
            "role": "manager",
            "assigned_depot_id": depot_id.upper(),  # Normalize to uppercase to match seed_depots.py
            "assigned_depot_name": depot_name,
            "created_at": __import__("datetime").datetime.utcnow(),
        }

        db.users.insert_one(user_doc)
        print(f"  [OK] Created manager: {email} → Depot {depot_id.upper()}")
        created += 1

    print(f"\n[SEED] Done! Created: {created} | Skipped (already existed): {skipped}")
    client.close()


if __name__ == "__main__":
    seed_managers()
