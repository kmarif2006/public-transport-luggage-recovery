# AI-Assisted Passenger Belongings Recovery System
### 🚍 Smart Lost & Found Management for State Transport Services

The **AI-Assisted Passenger Belongings Recovery System** is a modern, digital solution designed to streamline the recovery of lost items for passengers traveling on government buses (e.g., TNSTC). By replacing manual registers with a centralized, AI-powered platform, the system ensures transparency, speed, and accuracy in reunited passengers with their belongings.

---

## 🚀 Key Features

### 👤 Passenger Portal
- **Lost Item Reporting**: Submit detailed reports including travel date, route, boarding/alighting points, and item description.
- **Reference IDs**: Unique IDs for every report to facilitate easy tracking.
- **Status Updates**: Real-time feedback on potential matches found by depot staff.

### 🏢 Depot Management Dashboard
- **Secure Authentication**: Role-based access for different bus depots (e.g., Chennai, Coimbatore, Madurai).
- **Found Item Logging**: Record found items with photos, route information, and specific notes.
- **Proactive Matching**: Instant notification of potential matches within the passenger database.

### 🤖 Intelligent AI Matching
- **Semantic Similarity**: Uses **Sentence-BERT (all-MiniLM-L6-v2)** to compare passenger descriptions with depot notes, identifying matches even with different wording (e.g., "blue bag" matches "azure rucksack").
- **Travel Logic**: A custom algorithm (see *Luggage Path Logic*) that correlates bus routes and stops to predict where an item is most likely to be found.

---

## 🛠️ Technical Stack

- **Backend**: Python 3.x, Flask (Web Framework)
- **Database**: MongoDB (Scalable NoSQL storage)
- **AI/ML**: `sentence-transformers` (Sentence-BERT), `scikit-learn` (Cosine Similarity)
- **Frontend**: Semantic HTML5, CSS3 (Modern Glassmorphism UI), JavaScript (Dynamic Form Handling)
- **Environment**: `python-dotenv` for secure configuration.

---

## 🧠 Implementation Details: The Matching Logic

### 1. Luggage Path Logic
Items lost on a bus typically travel *forward* from where the passenger alighted. 
- **Rule**: If a passenger travels from **Stop A** to **Stop C**, and the bus continues to **Stop D** and **Stop E**, the item can only be found at depots located at **Stop D** or **Stop E**.
- The system automatically filters out irrelevant reports based on this directional travel logic.

### 2. Semantic Similarity
Generic text matching (like keyword search) often fails. Our system converts descriptions into high-dimensional vectors (embeddings):
- **Model**: `all-MiniLM-L6-v2`
- **Metric**: Cosine Similarity
- **Threshold**: Configured to 0.25+ for "Potential Match" alerts, ensuring high recall while maintaining relevance.

---

## 📂 Project Structure

```text
Final_Project/
├── app.py              # Main Flask application logic
├── seed_db.py          # Script to initialize MongoDB with routes and depots
├── requirements.txt    # Project dependencies
├── .env                # Environment variables (Mongo URI, Secret Key)
├── static/
│   ├── uploads/        # Storage for found item images
│   └── css/js/         # UI assets
└── templates/
    ├── base.html       # Shared layout template
    ├── index.html      # Passenger reporting page
    ├── depot.html      # Depot dashboard & matching view
    └── depot_login.html # Staff authentication
```

---

## ▶️ Setup & Installation

### 1. Prerequisites
- Python 3.8+
- MongoDB (Local or Atlas)

### 2. Environment Setup
Create a `.env` file in the root directory:
```env
MONGO_URI=mongodb+srv://<user>:<password>@cluster.mongodb.net/tn_bus_lost_found
SECRET_KEY=your_secure_random_key_here
```

### 3. Installation
```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 4. Database Initialization
Run the seed script to populate routes and depot credentials:
```bash
python seed_db.py
```

### 5. Run the Application
```bash
python app.py
```
Access the portal at `http://127.0.0.1:5003`.

---

## 🏆 Impact
- **Social Impact**: Reduces passenger anxiety and increases trust in public transport.

