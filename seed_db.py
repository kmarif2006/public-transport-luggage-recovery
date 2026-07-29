import os
import sys
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

DEPOTS_DATA = [
    {
        "phone": "9000000001",
        "name": "Chennai Depot",
        "password": "pass123",
        "stop": "Chennai",
        "routes": ["ch-co", "ch-md"]
    },
    {
        "phone": "9000000002",
        "name": "Coimbatore Depot",
        "password": "pass123",
        "stop": "Coimbatore",
        "routes": ["ch-co"]
    },
    {
        "phone": "9000000003",
        "name": "Madurai Depot",
        "password": "pass123",
        "stop": "Madurai",
        "routes": ["ch-md", "md-tn"]
    },
    {
        "phone": "9000000004",
        "name": "Salem Depot",
        "password": "pass123",
        "stop": "Salem",
        "routes": ["ch-co"]
    },
    {
        "phone": "9000000005",
        "name": "Tirunelveli Depot",
        "password": "pass123",
        "stop": "Tirunelveli",
        "routes": ["md-tn"]
    },
]

def seed_db():
    uri = os.environ.get('MONGO_URI')
    if not uri:
        print("MONGO_URI not found in environment")
        return

    client = MongoClient(uri)
    db = client['tn_bus_lost_found']
    depots_collection = db['depots']

    # DEPRECATED: seed_transport.py is now the authoritative depot seeder (it
    # builds the full 100-depot master and preserves logins). Running this old
    # 5-depot seeder would wipe that master, so refuse unless explicitly forced.
    if depots_collection.find_one({"depot_code": {"$exists": True}}) and "--force" not in sys.argv:
        print("Transport-master depots detected. This legacy seeder is deprecated; "
              "use `python seed_transport.py`. Re-run with --force to override.")
        return

    # Clear existing depots to avoid duplicates during seeding
    depots_collection.delete_many({})
    
    # Insert seed data
    result = depots_collection.insert_many(DEPOTS_DATA)
    print(f"Successfully seeded {len(result.inserted_ids)} depots.")

if __name__ == "__main__":
    seed_db()
