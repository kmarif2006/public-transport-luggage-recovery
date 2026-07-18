import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()
client = MongoClient(os.environ.get('MONGO_URI'))
db = client['tn_bus_lost_found']

print("--- RECENT LOST REPORTS ---")
for r in db.lost_reports.find().sort('_id', -1).limit(2):
    print(f"Name: {r.get('name')}, Route: {r.get('route_id')}, Src: {r.get('source')}, Dst: {r.get('destination')}")

print("\n--- RECENT FOUND REPORTS ---")
for r in db.found_reports.find().sort('_id', -1).limit(2):
    print(f"ID: {r.get('found_id')}, Depot: {r.get('depot_phone')}, Route: {r.get('route_id')}, Img: {r.get('image_path')}")

print("\n--- RECENT MATCHES ---")
for m in db.matches.find().sort('_id', -1).limit(5):
    print(f"Match for Found: {m.get('found_id')}, Score: {m.get('score')}")
