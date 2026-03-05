import sys
import os
from datetime import datetime, timezone

# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend import create_app
from backend.extensions import mongo, bcrypt

def create_manager(name, email, password, depot_id):
    app = create_app()
    with app.app_context():
        # Check if depot exists
        depot = mongo.db.depots.find_one({"depot_id": depot_id})
        if not depot:
            print(f"ERROR: Depot ID '{depot_id}' not found in database.")
            return

        # Check if email exists
        if mongo.db.users.find_one({"email": email.lower()}):
            print(f"ERROR: Email '{email}' is already registered.")
            return

        pw_hash = bcrypt.generate_password_hash(password).decode("utf-8")
        user = {
            "name": name,
            "email": email.lower(),
            "password_hash": pw_hash,
            "google_id": None,
            "microsoft_id": None,
            "role": "manager",
            "assigned_depot_id": depot_id,
            "created_at": datetime.now(timezone.utc),
        }
        
        mongo.db.users.insert_one(user)
        print(f"SUCCESS: Manager '{name}' created for depot '{depot['name']}' ({depot_id}).")

if __name__ == "__main__":
    if len(sys.argv) < 5:
        print("Usage: python create_manager.py <name> <email> <password> <depot_id>")
        print("Example: python create_manager.py 'John Doe' 'manager@tnstc.gov.in' 'secure-pass-123' 'D001'")
        sys.exit(1)

    name, email, password, depot_id = sys.argv[1:5]
    create_manager(name, email, password, depot_id)
