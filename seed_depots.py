import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

def seed_depots():
    uri = os.environ.get("MONGODB_URI")
    db_name = os.environ.get("MONGODB_DB_NAME", "tn_bus_lost_luggage")
    
    print(f"Connecting to MongoDB: {db_name}")
    client = MongoClient(uri, tlsAllowInvalidCertificates=True)
    db = client[db_name]
    
    # 20+ Real Tamil Nadu Depots (MTC, TNSTC, SETC)
    depots = [
        # MTC - Chennai
        {"depot_id": "D001", "name": "MTC - Pallavan Salai", "city": "Chennai", "district": "Chennai", "type": "MTC", "latitude": 13.0827, "longitude": 80.2707, "contact_number": "044-2345 5801"},
        {"depot_id": "D002", "name": "MTC - Adyar", "city": "Chennai", "district": "Chennai", "type": "MTC", "latitude": 13.0012, "longitude": 80.2565, "contact_number": "044-2345 5802"},
        {"depot_id": "D003", "name": "MTC - T.Nagar", "city": "Chennai", "district": "Chennai", "type": "MTC", "latitude": 13.0324, "longitude": 80.2337, "contact_number": "044-2345 5803"},
        {"depot_id": "D004", "name": "MTC - CMBT Koyambedu", "city": "Chennai", "district": "Chennai", "type": "MTC", "latitude": 13.0683, "longitude": 80.2046, "contact_number": "044-2345 5804"},
        
        # TNSTC - Madurai
        {"depot_id": "D005", "name": "TNSTC - Madurai Central (Mattuthavani)", "city": "Madurai", "district": "Madurai", "type": "TNSTC", "latitude": 9.9405, "longitude": 78.1564, "contact_number": "0452-2580 500"},
        {"depot_id": "D006", "name": "TNSTC - Arappalayam", "city": "Madurai", "district": "Madurai", "type": "TNSTC", "latitude": 9.9324, "longitude": 78.1062, "contact_number": "0452-2580 501"},
        
        # TNSTC - Coimbatore
        {"depot_id": "D007", "name": "TNSTC - Singanallur", "city": "Coimbatore", "district": "Coimbatore", "type": "TNSTC", "latitude": 10.9991, "longitude": 77.0163, "contact_number": "0422-257 2521"},
        {"depot_id": "D008", "name": "TNSTC - Gandhipuram Central", "city": "Coimbatore", "district": "Coimbatore", "type": "TNSTC", "latitude": 11.0183, "longitude": 76.9634, "contact_number": "0422-257 2522"},
        
        # TNSTC - Trichy
        {"depot_id": "D009", "name": "TNSTC - Trichy Central", "city": "Trichy", "district": "Tiruchirappalli", "type": "TNSTC", "latitude": 10.7937, "longitude": 78.6872, "contact_number": "0431-246 0456"},
        
        # TNSTC - Salem
        {"depot_id": "D010", "name": "TNSTC - Salem Central", "city": "Salem", "district": "Salem", "type": "TNSTC", "latitude": 11.6643, "longitude": 78.1460, "contact_number": "0427-241 1205"},
        
        # TNSTC - Tirunelveli
        {"depot_id": "D011", "name": "TNSTC - Tirunelveli New Bus Stand", "city": "Tirunelveli", "district": "Tirunelveli", "type": "TNSTC", "latitude": 8.7139, "longitude": 77.6975, "contact_number": "0462-255 2445"},
        
        # TNSTC - Erode
        {"depot_id": "D012", "name": "TNSTC - Erode Town", "city": "Erode", "district": "Erode", "type": "TNSTC", "latitude": 11.3410, "longitude": 77.7172, "contact_number": "0424-221 2101"},
        
        # TNSTC - Vellore
        {"depot_id": "D013", "name": "TNSTC - Vellore New Bus Stand", "city": "Vellore", "district": "Vellore", "type": "TNSTC", "latitude": 12.9349, "longitude": 79.1351, "contact_number": "0416-222 1445"},
        
        # TNSTC - Thanjavur
        {"depot_id": "D014", "name": "TNSTC - Thanjavur New Bus Stand", "city": "Thanjavur", "district": "Thanjavur", "type": "TNSTC", "latitude": 10.7870, "longitude": 79.1378, "contact_number": "04362-225 245"},
        
        # TNSTC - Tuticorin
        {"depot_id": "D015", "name": "TNSTC - Tuticorin City", "city": "Tuticorin", "district": "Thoothukudi", "type": "TNSTC", "latitude": 8.8100, "longitude": 78.1400, "contact_number": "0461-232 2445"},
        
        # TNSTC - Nagercoil
        {"depot_id": "D016", "name": "TNSTC - Nagercoil (Vadasery)", "city": "Nagercoil", "district": "Kanyakumari", "type": "TNSTC", "latitude": 8.1833, "longitude": 77.4119, "contact_number": "04652-278 123"},
        
        # TNSTC - Hosur
        {"depot_id": "D017", "name": "TNSTC - Hosur Town", "city": "Hosur", "district": "Krishnagiri", "type": "TNSTC", "latitude": 12.7409, "longitude": 77.8253, "contact_number": "04344-245 125"},
        
        # TNSTC - Dindigul
        {"depot_id": "D018", "name": "TNSTC - Dindigul Central", "city": "Dindigul", "district": "Dindigul", "type": "TNSTC", "latitude": 10.3673, "longitude": 77.9803, "contact_number": "0451-242 2445"},
        
        # TNSTC - Karur
        {"depot_id": "D019", "name": "TNSTC - Karur Central", "city": "Karur", "district": "Karur", "type": "TNSTC", "latitude": 10.9601, "longitude": 78.0766, "contact_number": "04324-232 245"},
        
        # SETC - (State Express Transport Corporation)
        {"depot_id": "D020", "name": "SETC - Broadway Chennai", "city": "Chennai", "district": "Chennai", "type": "SETC", "latitude": 13.0889, "longitude": 80.2905, "contact_number": "044-2534 1121"},
        {"depot_id": "D021", "name": "SETC - Madurai", "city": "Madurai", "district": "Madurai", "type": "SETC", "latitude": 9.9248, "longitude": 78.1147, "contact_number": "0452-2580 502"},
        {"depot_id": "D022", "name": "SETC - Tirunelveli Central", "city": "Tirunelveli", "district": "Tirunelveli", "type": "SETC", "latitude": 8.7183, "longitude": 77.6911, "contact_number": "0462-255 2446"},
    ]
    
    # Clean and insert
    print(f"Cleaning existing depots...")
    db.depots.delete_many({})
    
    print(f"Seeding {len(depots)} depots...")
    db.depots.insert_many(depots)
    
    print("DONE: Seeded real Tamil Nadu depot data.")

if __name__ == "__main__":
    seed_depots()
