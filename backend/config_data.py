# Routes and Depot Mapping for TN Bus Lost Luggage

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
    {
        "id": "ch-py",
        "name": "Chennai ↔ Puducherry",
        "stops": ["Chennai", "Poonamallee", "Tindivanam", "Puducherry"]
    },
    {
        "id": "co-md",
        "name": "Coimbatore ↔ Madurai",
        "stops": ["Coimbatore", "Palladam", "Dharapuram", "Oddanchatram", "Dindigul", "Madurai"]
    }
]

# Mapping of Depot IDs to their corresponding Stops
DEPOT_STOP_MAPPING = {
    "D001": "Chennai",
    "D002": "Madurai",
    "D003": "Coimbatore",
    "D004": "Tirunelveli",
    "D005": "Salem",
    "D006": "Chennai", # T. Nagar
    "D007": "Trichy",
    "D008": "Erode",
    "D009": "Vellore",
    "D010": "Thanjavur",
    # ... more mappings can be added as needed
}
