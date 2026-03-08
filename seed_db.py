import os
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

    # Clear existing depots to avoid duplicates during seeding
    depots_collection.delete_many({})
    
    # Insert seed data
    result = depots_collection.insert_many(DEPOTS_DATA)
    print(f"Successfully seeded {len(result.inserted_ids)} depots.")

if __name__ == "__main__":
    seed_db()
