# AI-Assisted Passenger Belongings Recovery System  
### Smart Lost & Found Management for state transport  Services

---

## 🚍 Project Overview

The **AI-Assisted Passenger Belongings Recovery System** is a centralized digital platform designed to solve the persistent problem of passengers losing personal belongings while traveling on government buses.

Traditional recovery mechanisms in transport depots rely on **manual registers, fragmented communication, and human memory**, often resulting in delays, misplacement, or permanent loss of passenger items.

This project modernizes the entire workflow by introducing a **secure, transparent, and AI-supported system** that connects **passengers, conductors, and depot administrators** through a unified platform.

---

## 🎯 Problem Statement

- Lost-item handling is manual and inefficient  
- No centralized database across depots  
- Poor coordination between passengers and depot staff  
- High dependency on verbal communication  
- Limited traceability and accountability  

---

## 💡 Proposed Solution

The system introduces a centralized web-based platform where:

- **Passengers** submit lost-item reports using travel details  
- **Depot staff** upload found items with route data and images  
- **AI-assisted matching** analyzes:
  - Text descriptions  
  - Travel metadata  
  - Item images  
- A **confidence score** supports decision-making with human verification  
- Verified items can be returned physically or via secure parcel delivery  

---

## 🧠 Key Features

### 👤 Passenger Module
- Lost-item reporting with travel details  
- SMS-based confirmation for verification  
- Transparent recovery status tracking  

### 🏢 Depot Staff Module
- Depot-specific secure login  
- Found-item reporting with image upload  
- Controlled item release workflow  

### 🤖 AI Matching Engine
- Intelligent matching of lost and found items  
- Text similarity and route-based alignment  
- Confidence score generation  

### 🔐 Security & Governance
- Role-based depot access  
- Controlled verification and release  
- Centralized and traceable records  

---

## 🏗️ System Architecture

- **Frontend**: HTML, CSS, JavaScript  
- **Backend**: Python Flask  
- **Database**: Centralized relational database  
- **AI Module**: Similarity-driven matching logic  
- **Notifications**: SMS-based passenger alerts  

---

## 📸 Application Interfaces

| Figure | Description |
|------|-------------|
| Fig. 1 | Passenger Lost Item Reporting Interface |
| Fig. 2 | Depot Selection Screen |
| Fig. 3 | Depot Staff Authentication Interface |
| Fig. 4 | Found Item Reporting Dashboard |
| Fig. 5 | AI Matching & Notification Interface |

Screenshots are available in the `screenshots/` folder.

---

## 📁 Project Structure

srm-project/
├── app.py
├── static/
├── templates/
├── requirements.txt
├── setup_venv.sh
├── .env.example
├── screenshots/
└── README.md


---

## ▶️ How to Run the Project

```bash
# Create virtual environment
python -m venv venv

# Activate environment
venv\Scripts\activate        # Windows
source venv/bin/activate    # Linux / macOS

# Install dependencies
pip install -r requirements.txt

# Run application
python app.py

🌍 Real-World Impact

Reduces dependency on manual registers

Improves recovery accuracy and response time

Enhances passenger trust in public transport

Supports digital governance initiatives

Demonstrates practical AI in civic systems

🚀 Future Enhancements

Aadhaar / e-ticket integration

Mobile app for depot staff and conductors

Advanced computer vision for item recognition

Blockchain-based tamper-proof records

Nationwide deployment

🏆 Why This Project Stands Out

Solves a real-world civic problem

Combines AI, system design, and governance

Focuses on practical deployment

Scalable and socially impactful

