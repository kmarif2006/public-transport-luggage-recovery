"""
Seed script for the `depots` collection in MongoDB.

Includes major Tamil Nadu depots with approximate coordinates.
"""

from datetime import datetime, timezone

from pymongo import MongoClient

SAMPLE_DEPOTS = [
    {
        "name": "Chennai Mofussil Bus Terminus",
        "city": "Chennai",
        "district": "Chennai",
        "latitude": 13.0827,
        "longitude": 80.2707,
        "contact_number": "+91-44-12345678",
    },
    {
        "name": "Coimbatore Central Bus Depot",
        "city": "Coimbatore",
        "district": "Coimbatore",
        "latitude": 11.0168,
        "longitude": 76.9558,
        "contact_number": "+91-422-1234567",
    },
    {
        "name": "Madurai Periyar Bus Stand",
        "city": "Madurai",
        "district": "Madurai",
        "latitude": 9.9252,
        "longitude": 78.1198,
        "contact_number": "+91-452-1234567",
    },
    {
        "name": "Trichy Central Bus Stand",
        "city": "Tiruchirappalli",
        "district": "Tiruchirappalli",
        "latitude": 10.7905,
        "longitude": 78.7047,
        "contact_number": "+91-431-1234567",
    },
    {
        "name": "Salem New Bus Stand",
        "city": "Salem",
        "district": "Salem",
        "latitude": 11.6643,
        "longitude": 78.1460,
        "contact_number": "+91-427-1234567",
    },
    {
        "name": "Tirunelveli New Bus Stand",
        "city": "Tirunelveli",
        "district": "Tirunelveli",
        "latitude": 8.7139,
        "longitude": 77.7567,
        "contact_number": "+91-462-1234567",
    },
    {
        "name": "Erode Central Bus Stand",
        "city": "Erode",
        "district": "Erode",
        "latitude": 11.3410,
        "longitude": 77.7172,
        "contact_number": "+91-424-1234567",
    },
    {
        "name": "Vellore Bus Stand",
        "city": "Vellore",
        "district": "Vellore",
        "latitude": 12.9165,
        "longitude": 79.1325,
        "contact_number": "+91-416-1234567",
    },
    {
        "name": "Thanjavur New Bus Stand",
        "city": "Thanjavur",
        "district": "Thanjavur",
        "latitude": 10.7870,
        "longitude": 79.1378,
        "contact_number": "+91-4362-123456",
    },
    {
        "name": "Kanchipuram Bus Stand",
        "city": "Kanchipuram",
        "district": "Kanchipuram",
        "latitude": 12.8342,
        "longitude": 79.7036,
        "contact_number": "+91-44-22334455",
    },
]


def seed(uri: str, db_name: str):
    client = MongoClient(uri)
    db = client[db_name]
    depots = db.depots

    for depot in SAMPLE_DEPOTS:
        existing = depots.find_one(
            {"name": depot["name"], "city": depot["city"], "district": depot["district"]}
        )
        if existing:
            continue
        depot_doc = depot | {
            "manager_id": None,
            "created_at": datetime.now(timezone.utc),
        }
        depots.insert_one(depot_doc)

    print(f"Seeded depots into database '{db_name}'.")


if __name__ == "__main__":
    import os

    uri = os.environ.get("MONGODB_URI", "mongodb://localhost:27017/tn_bus_lost_luggage")
    db_name = os.environ.get("MONGODB_DB_NAME", "tn_bus_lost_luggage")
    seed(uri, db_name)

