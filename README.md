# Tamil Nadu Bus Depot Lost Luggage Management System

A comprehensive web application for managing lost and found luggage at Tamil Nadu State Transport bus depots.

## ✨ Features

### For Passengers (Users)
- ✅ Secure signup/login with email/password, Google OAuth, or Microsoft OAuth
- ✅ Interactive map of Tamil Nadu showing all bus depots (Leaflet.js + OpenStreetMap)
- ✅ Click-to-select depot from map markers
- ✅ Submit detailed lost luggage reports
- ✅ Track report status in real-time dashboard

### For Depot Managers
- ✅ Separate manager login portal
- ✅ View all reports submitted to their assigned depot
- ✅ Update report status (Reported → Under Review → Found → Returned)
- ✅ Contact information for reporting users
- ✅ Real-time notifications via Socket.IO when new reports arrive

## 🛠️ Tech Stack

**Frontend**
- HTML5, CSS3, Vanilla JavaScript
- Leaflet.js for interactive maps
- OpenStreetMap tiles
- Socket.IO client for real-time updates

**Backend**
- Python 3.10+
- Flask (Blueprints architecture)
- Flask-SocketIO for WebSocket support
- PyJWT for authentication
- bcrypt for password hashing

**Database**
- MongoDB Atlas (cloud) or local MongoDB

**Authentication**
- Custom email/password with JWT tokens
- Google OAuth 2.0
- Microsoft OAuth 2.0

## 📁 Project Structure

```
Final_Project/
├── backend/
│   ├── __init__.py              # App factory & route registration
│   ├── config.py                # Configuration classes
│   ├── extensions.py            # Flask extensions (MongoDB, SocketIO, etc.)
│   ├── auth/
│   │   ├── routes.py            # Auth endpoints (login, signup, OAuth)
│   │   ├── jwt_handler.py       # JWT token creation/validation
│   │   └── oauth.py             # Google & Microsoft OAuth flows
│   ├── depots/
│   │   └── routes.py            # Depot listing & selection APIs
│   ├── luggage/
│   │   ├── models.py            # Luggage report schemas
│   │   └── routes.py            # Report submission & tracking APIs
│   └── manager/
│       └── routes.py            # Manager dashboard APIs
├── frontend/
│   ├── login.html               # User login page
│   ├── signup.html              # User signup page
│   ├── map.html                 # Interactive depot map
│   ├── dashboard.html           # User's report tracking
│   ├── manager_dashboard.html   # Manager admin panel
│   ├── depot_login.html         # Manager login portal
│   ├── css/
│   │   └── style.css            # Application styles
│   └── js/
│       ├── auth.js              # Authentication logic
│       ├── map.js               # Leaflet map initialization
│       ├── reports.js           # Report submission & tracking
│       └── manager.js           # Manager dashboard logic
├── database/
│   └── seed_depots.py           # Seed script for depot data
├── templates/
│   └── base.html                # Base Jinja2 template
├── static/
│   └── uploads/                 # User-uploaded images (optional)
├── .env                         # Environment variables
├── app.py                       # Application entry point
├── requirements.txt             # Python dependencies
└── README.md                    # This file
```

## 🚀 Installation & Setup

### Prerequisites
- Python 3.10 or higher
- MongoDB Atlas account (free tier works) OR local MongoDB installation
- Git (optional, for version control)

### Step 1: Navigate to Project

```bash
cd c:\Users\HP\Desktop\Final_Project
```

### Step 2: Create Virtual Environment (Optional but Recommended)

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**Linux/Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables

Edit the `.env` file with your credentials:

```env
# Flask Configuration
SECRET_KEY=your-secret-key-here
FLASK_ENV=development

# MongoDB Atlas Configuration
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/tn_bus_lost_luggage
MONGODB_DB_NAME=tn_bus_lost_luggage

# JWT Configuration
JWT_SECRET_KEY=your-jwt-secret-key

# Google OAuth (Get from Google Cloud Console)
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
GOOGLE_OAUTH_REDIRECT_URI=http://localhost:5000/api/auth/google/callback

# Microsoft OAuth (Get from Azure Portal)
MS_CLIENT_ID=your-microsoft-client-id
MS_CLIENT_SECRET=your-microsoft-client-secret
MS_TENANT_ID=common
MS_OAUTH_REDIRECT_URI=http://localhost:5000/api/auth/microsoft/callback
```

### Step 5: Seed the Database

Populate the database with Tamil Nadu bus depots:

```bash
python database/seed_depots.py
```

You should see: `✓ Seeded depots into database 'tn_bus_lost_luggage'`

### Step 6: Run the Application

```bash
python app.py
```

The server will start on **http://localhost:5000**

## 📖 Usage Guide

### For Passengers

1. **Sign Up / Login**
   - Visit http://localhost:5000
   - Create account with email/password or use Google/Microsoft

2. **Select Your Depot**
   - After login, you'll see the Tamil Nadu map
   - Click on any depot marker
   - Click "Select this depot" button

3. **Submit Lost Luggage Report**
   - Fill in the form:
     - Item name
     - Description
     - Date lost
     - Bus number
     - Contact phone
   - Click "Submit report"

4. **Track Your Reports**
   - Navigate to "My Reports" dashboard
   - View status of all submissions

### For Depot Managers

1. **Create Manager Account**
   - You need to manually create a manager account in MongoDB:
   
   ```javascript
   // In MongoDB Compass or mongosh:
   db.users.insertOne({
     "name": "Chennai Manager",
     "email": "chennai.manager@tnbus.gov.in",
     "password_hash": "$2b$12$...",  // Use bcrypt to hash password
     "google_id": null,
     "microsoft_id": null,
     "role": "manager",
     "assigned_depot_id": ObjectId("..."),  // Get from depots collection
     "created_at": ISODate()
   })
   ```

2. **Login as Manager**
   - Visit http://localhost:5000/depot_login.html
   - Enter manager credentials

3. **Manage Reports**
   - View all reports for your depot
   - Update status as items are found/returned
   - Contact users via phone number

## 🔌 API Endpoints

### Authentication
- `POST /api/auth/signup` - Create new user account
- `POST /api/auth/login` - Login with email/password
- `GET /api/auth/google/url` - Get Google OAuth URL
- `GET /api/auth/google/callback?code=...` - Google OAuth callback
- `GET /api/auth/microsoft/url` - Get Microsoft OAuth URL
- `GET /api/auth/microsoft/callback?code=...` - Microsoft OAuth callback
- `GET /api/auth/me` - Get current user info (requires JWT)

### Depots
- `GET /api/depots` - List all bus depots (for map markers)
- `POST /api/select-depot` - Select a depot (requires JWT)

### Luggage Reports
- `POST /api/report-luggage` - Submit new report (requires JWT)
- `GET /api/my-reports` - Get user's reports (requires JWT)

### Manager Dashboard
- `GET /api/manager/reports` - Get all reports for manager's depot (requires manager JWT)
- `PUT /api/manager/update-status` - Update report status (requires manager JWT)

## 🗄️ Database Collections

### users
```javascript
{
  _id: ObjectId,
  name: String,
  email: String,
  password_hash: String | null,
  google_id: String | null,
  microsoft_id: String | null,
  role: "user" | "manager",
  assigned_depot_id: ObjectId | null,
  created_at: Date
}
```

### depots
```javascript
{
  _id: ObjectId,
  name: String,
  city: String,
  district: String,
  latitude: Number,
  longitude: Number,
  manager_id: ObjectId | null,
  contact_number: String,
  created_at: Date
}
```

### lost_luggage_reports
```javascript
{
  _id: ObjectId,
  user_id: ObjectId,
  depot_id: ObjectId,
  item_name: String,
  item_description: String,
  date_lost: String,
  bus_number: String,
  contact_phone: String,
  status: "reported" | "under_review" | "found" | "returned",
  created_at: Date
}
```

### selected_depots
```javascript
{
  _id: ObjectId,
  user_id: ObjectId,
  depot_id: ObjectId,
  selected_at: Date
}
```

## 🔒 Security Features

✅ bcrypt password hashing  
✅ JWT token authentication  
✅ Role-based access control (user vs manager)  
✅ CORS protection  
✅ Input validation  
✅ Environment variable configuration  
✅ Secure session management  

## 📡 Real-Time Features

When a new luggage report is submitted:
1. Backend emits Socket.IO event `new_luggage_report`
2. All managers connected to that depot's room receive notification
3. New report appears instantly in manager dashboard without refresh

## 🐛 Troubleshooting

### MongoDB Connection Fails
- Check your `MONGODB_URI` in `.env`
- Ensure MongoDB Atlas allows connections from your IP
- Verify network access in Atlas dashboard

### OAuth Not Working
- Ensure redirect URIs match exactly in Google/Azure portals
- Check that OAuth consent screen is configured
- Enable required APIs (Google+ for Google OAuth)

### Map Markers Not Loading
- Check browser console for errors
- Verify `/api/depots` endpoint returns data
- Ensure MongoDB has depot documents

### Socket.IO Not Connecting
- Check that JWT token is valid
- Verify WebSocket isn't blocked by firewall/proxy

## 🌐 Deployment

### Production Checklist
- [ ] Set strong `SECRET_KEY` and `JWT_SECRET_KEY`
- [ ] Use production MongoDB connection string
- [ ] Configure OAuth redirect URIs for production domain
- [ ] Enable HTTPS (required for OAuth)
- [ ] Set `FLASK_ENV=production`
- [ ] Use a production WSGI server (Gunicorn, uWSGI)
- [ ] Configure reverse proxy (Nginx, Apache)

### Deploy to Heroku/Railway/Render
1. Push code to Git repository
2. Connect to cloud provider
3. Set environment variables in provider dashboard
4. Deploy!

## 🎯 Future Enhancements

- [ ] Image upload for lost items
- [ ] AI-powered matching between lost and found items
- [ ] SMS notifications
- [ ] Email notifications
- [ ] Multi-language support (Tamil, English, Hindi)
- [ ] Admin analytics dashboard
- [ ] Mobile app (React Native)
- [ ] QR code generation for tracking

## 📄 License

This project is for educational purposes as part of a final year project.

## 👨‍💻 Credits

Developed for Tamil Nadu State Transport Corporation  
Built with ❤️ using Flask, MongoDB, and Leaflet.js
