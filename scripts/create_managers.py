import os
import sys
from datetime import datetime, timezone
from pymongo import MongoClient
from flask_bcrypt import Bcrypt
from dotenv import load_dotenv

# Add parent directory to path to import backend modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

load_dotenv()

def create_managers():
    uri = os.environ.get("MONGODB_URI")
    db_name = os.environ.get("MONGODB_DB_NAME", "tn_bus_lost_luggage")
    
    print(f"Connecting to MongoDB: {db_name}")
    client = MongoClient(uri, tlsAllowInvalidCertificates=True)
    db = client[db_name]
    bcrypt = Bcrypt()

    depots = list(db.depots.find({}))
    if not depots:
        print("[!] No depots found in database. Seed depots first.")
        return

    print(f"Generating manager accounts for {len(depots)} depots...")
    
    for depot in depots:
        # Use depot_id or fallback to _id
        depot_id = depot.get("depot_id") or str(depot["_id"])
        email = f"manager.{depot_id}@tnstc.gov.in".lower()
        password = f"{depot_id}_pass123"
        
        # Check if manager already exists
        extant = db.users.find_one({"email": email})
        if extant:
            print(f"  - Manager {email} already exists. Skipping.")
            continue
            
        pw_hash = bcrypt.generate_password_hash(password).decode("utf-8")
        
        manager_user = {
            "name": f"Manager - {depot['name']}",
            "email": email,
            "password_hash": pw_hash,
            "google_id": None,
            "microsoft_id": None,
            "role": "manager",
            "assigned_depot_id": depot_id,
            "created_at": datetime.now(timezone.utc),
        }
        
        db.users.insert_one(manager_user)
        print(f"  [+] Created: {email} | Pass: {password}")

    print("\n DONE: All manager accounts generated successfully.")

if __name__ == "__main__":
    create_managers()
