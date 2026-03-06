# Tamil Nadu Bus Depot Lost Luggage Management System

A professional, government-grade platform for managing lost and found luggage across all bus depots in Tamil Nadu. Built for users (passengers) and official depot managers with high-precision AI semantic matching and real-time route integration.

---

## 🚀 System Status: **PRODUCTION-READY** 

| Component | Status | Details |
| :--- | :--- | :--- |
| **User Sign-up/Login** | ✅ Working | Supports Email/Password, Google OAuth, and Microsoft OAuth. |
| **Depot Search & Filters** | ✅ Working | Auto-filtering search boxes for 35+ Tamil Nadu depots. |
| **Map Selection & Routing** | ✅ Working | Marker-click selection for Start/End with high-contrast pathing. |
| **Lost Luggage Reporting** | ✅ Working | Multi-depot broadcasting, optional bus number, and photo uploads. |
| **Depot Manager Dashboard** | ✅ Working | Depot-specific report views, status updates, and found item ledger. |
| **AI Semantic Matching** | ✅ Working | `all-MiniLM-L6-v2` path-aware matching scoring (%) against found items. |
| **Real-time Notifications** | ✅ Working | Instant WebSocket (Socket.IO) updates for depot managers. |

---

## 📁 Folder Structure & Architecture

```text
Final_Project/
├── app.py                       # Main Flask Application Entry (Socket.IO)
├── .env                         # Environment Secrets (MongoDB, OAuth IDs)
├── requirements.txt             # Python Dependency List
├── manager_credentials.json     # 🔐 AUTO-GENERATED: List of all manager accounts
│
├── backend/                     # Python Flask Modular Architecture
│   ├── __init__.py              # App Factory & Blueprint Registration
│   ├── extensions.py            # Shared Objects: MongoDB, SocketIO, Bcrypt, JWT
│   ├── semantic_matcher.py      # 🤖 AI Matcher: Item Similarity Scoring logic
│   ├── auth/                    # JWT & OAuth (Google/Microsoft) Handlers
│   ├── luggage/                 # Passenger Reporting & Match retrieval logic
│   ├── manager/                 # Official Depot Manager control logic
│   └── depots/                  # Geographic Depot Data Service
│
├── frontend/                    # Vanilla Web Interface (No Frameworks)
│   ├── map.html                 # 🗺️ Core Activity: Route select & Report trigger
│   ├── dashboard.html           # 👤 Passenger: View matches & current status
│   ├── manager_dashboard.html   # 👨‍💼 Manager: Depot Ledger & Found updates
│   ├── depot_login.html         # Official Login Portal
│   ├── css/                     # map.css (Leaflet-themed), main.css (Global)
│   └── js/                      # map.js (Leaflet logic), manager.js (Dashboard logic)
│
└── database/                    # Data Setup Scripts
    └── seed_depots.py           # Seed 35+ official TN bus depots
```

---

## 🛠️ Tech Stack

- **Backend**: Python 3.10+ (Flask, Flask-Blueprints, Flask-JWT-Extended, Flask-SocketIO)
- **Database**: MongoDB Atlas (Vector-search ready structure)
- **Frontend**: Vanilla HTML5, CSS3, JavaScript (Leaflet.js for Maps)
- **AI/ML**: `sentence-transformers` (all-MiniLM-L6-v2) for semantic text matching.

---

## 📝 User Journey (Testing Guide)

### 1. **Passenger Flow**
1. **Login**: Sign up at `signup.html` or Login at `login.html`.
2. **Select Route**: Navigate to `map.html`.
   - Use the **Search Filter** to find "Chennai" or "Madurai".
   - Click a marker ➔ **"Set as Starting Point"**.
   - Click another marker ➔ **"Set as Destination"**.
3. **Report**: Click **"Calculate & Draw Route"**.
   - The map draws the path (`#2563EB`).
   - The **"START REPORTING"** button appears.
   - Submit your report (Bus number is optional).
4. **Track**: View your AI matches and status in `dashboard.html`.

### 2. **Official Manager Flow**
1. **Login**: Use credentials from `manager_credentials.json` at `depot_login.html`.
2. **Dashboard**: View only reports that passed through your depot.
3. **Register Found Item**: Upload a photo and description of a found item to trigger AI matching for passengers.
4. **Update Status**: Change report status (Reported ➔ Under Review ➔ Found ➔ Returned).

---

## 🐛 Troubleshooting & Known Issues
- **Map Visibility**: Ensure the browser window is resized or refreshed. We added an `invalidateSize()` trigger in `map.js` to handle all Leaflet rendering race conditions.
- **Matching accuracy**: For best results, passengers should provide at least 15-20 characters in the "Description" field (e.g., "Red VIP suitcase with broken handle").

---

**Developed for Tamil Nadu State Transport Corporation (TNSTC/MTC/SETC)**  
✨ *Production ready and secured with JWT & OAuth.*
