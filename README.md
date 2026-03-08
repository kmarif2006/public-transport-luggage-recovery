# AI-Assisted Passenger Belongings Recovery System
### 🚍 Intelligent Lost & Found Management for State Transport Services (TNSTC MVP)

The **AI-Assisted Passenger Belongings Recovery System** is a full-stack digital platform designed to automate and optimize the recovery of lost items in public transport. By leveraging **Sentence-BERT** for semantic matching and a custom **Luggage Path Logic** algorithm, the system bridge the gap between passengers and depot administrators, ensuring that lost items are tracked and returned with high efficiency.

---

## 📑 Project Abstract
In traditional transport systems, lost items are recorded in manual registers, leading to fragmented information and low recovery rates. This project introduces a centralized MongoDB-backed Flask application that:
1.  Allows passengers to report lost items with precise travel metadata.
2.  Provides depot staff with a secure dashboard to log found items (with image support).
3.  Automatically suggests matches using AI-driven similarity scores and route-based directional logic.

---

## ✅ Implementation Status (What's been implemented)

### **Backend & Logic**
- [x] **Flask Application Core**: Robust routing and session management.
- [x] **MongoDB Integration**: Persistent storage for lost reports, found reports, and depot credentials.
- [x] **Luggage Path Logic**: A directional algorithm that filters matches based on the bus's travel sequence (Stop A → Stop B → Stop C).
- [x] **AI Matching Engine**: Integrated `SentenceTransformer` (`all-MiniLM-L6-v2`) for semantic text similarity.
- [x] **Authentication**: Secure depot-specific login system.

### **Frontend & UI**
- [x] **Passenger Portal**: Dynamic forms with real-time stop suggestions based on selected routes.
- [x] **Depot Dashboard**: Comprehensive view of submitted found reports and auto-suggested passenger matches.
- [x] **Responsive Design**: Modern Glassmorphism UI using CSS3 and Vanilla JS.
- [x] **File Uploads**: Image processing for found items using `werkzeug`.

### **Data & Setup**
- [x] **Database Seeding**: Python script (`seed_db.py`) to automatically populate the database with real-world routes (Chennai, Coimbatore, Madurai, etc.).
- [x] **Environment Configuration**: Secure `.env` handling for API keys and database URIs.

---

## 🛠️ Technical Stack

-   **Frontend**: HTML5, CSS3, JavaScript (ES6+), FontAwesome Icons.
-   **Backend**: Python 3.11+, Flask.
-   **Database**: MongoDB (NoSQL) via `pymongo`.
-   **AI/ML**: `sentence-transformers`, `scikit-learn` (Cosine Similarity).
-   **Security**: `python-dotenv`, `werkzeug.security`.

---

## 🧠 Core Algorithm: AI Matching Logic

### 1. Luggage Path Logic
Items lost on a bus typically stay on the bus until it reaches a depot or the end of its route.
-   **Example**: If a passenger boards at **Chennai** and gets down at **Villupuram**, the item is logicaly found at depots *after* Villupuram (e.g., **Salem**, **Erode**, or **Coimbatore**).
-   The system uses the `ROUTES` stop sequence to validate these "downstream" depots.

### 2. Semantic Description Matching
Traditional keyword search fails (e.g., "blue bag" vs "navy rucksack"). 
-   The system converts descriptions into **384-dimensional embeddings**.
-   **Cosine Similarity** compares the `Lost Description` vs `Depot Notes`.
-   **Threshold**: Set at `0.25` to balance high sensitivity with relevance.

---

## ▶️ How to Run the Project

### 1. Prerequisites
- **Python 3.11+** installed.
- **MongoDB** instance (Local or Atlas) ready.

### 2. Setup Environment
Clone/copy the project and create a `.env` file in the root:
```env
MONGO_URI=your_mongodb_connection_string
SECRET_KEY=your_random_secret_key
```

### 3. Installation
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Install requirements
pip install -r requirements.txt
```

### 4. Initialize Database
Before running the app, seed the depot authentication and route data:
```bash
python seed_db.py
```

### 5. Start Application
```bash
python app.py
```
Visit `http://127.0.0.1:5003` in your browser.

---

## 🏆 Impact & Roadmap
- **Social Impact**: Reduces passenger anxiety and increases trust in public transport.
- **Future Scope**:
    - Aadhaar-based identity verification for item collection.
    - Automated SMS/WhatsApp notifications via Twilio.
    - Computer Vision for automatic item categorization from photos.
    - Multi-language support (Tamil & English).
