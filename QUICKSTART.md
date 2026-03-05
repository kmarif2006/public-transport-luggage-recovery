# 🚀 Quick Start Guide - TN Bus Lost Luggage System

## ⚡ Running the Application (5 Minutes)

### Step 1: Activate Virtual Environment
```bash
cd c:\Users\HP\Desktop\Final_Project
venv\Scripts\activate   # Windows
```

### Step 2: Verify Environment Variables
Check that `.env` file has:
- ✅ MongoDB URI (already configured)
- ✅ SECRET_KEY (already configured)
- ✅ JWT_SECRET_KEY (already configured)

OAuth credentials are optional for local testing.

### Step 3: Seed the Database (First Time Only)
```bash
python database/seed_depots.py
```

Expected output: `✓ Seeded depots into database 'tn_bus_lost_luggage'`

### Step 4: Start the Server
```bash
python app.py
```

Expected output:
```
✓ MongoDB connected to 'tn_bus_lost_luggage'
 * Running on http://127.0.0.1:5000
```

### Step 5: Open in Browser
Navigate to: **http://localhost:5000**

---

## 🎯 Testing the Application

### Test as Passenger User

1. **Create Account**
   - Go to http://localhost:5000
   - Click "Create an account"
   - Fill in: Name, Email, Password
   - Click "Create account"

2. **Select Depot**
   - You'll see Tamil Nadu map with markers
   - Click any depot marker (Chennai, Coimbatore, etc.)
   - Click "Select this depot" button

3. **Submit Report**
   - Fill in the lost luggage form:
     - Item name: "Red Backpack"
     - Description: "Contains books and laptop"
     - Date lost: Select date
     - Bus number: "TN-01-AB-1234"
     - Contact phone: "+91-9876543210"
   - Click "Submit report"

4. **Track Reports**
   - Navigate to dashboard
   - View your submitted reports

### Test as Depot Manager

1. **Create Manager Account** (One-time setup)
   
   Open MongoDB Compass or mongosh and run:
   
   ```javascript
   // First, get a depot ID
   db.depots.findOne({city: "Chennai"})
   
   // Then create manager account (replace _id with actual ObjectId)
   db.users.insertOne({
     "name": "Chennai Depot Manager",
     "email": "manager@chennai.com",
     "password_hash": "$2b$12$LqXfKsJh9X8zYqJ5ZqJ5ZqJ5ZqJ5ZqJ5ZqJ5ZqJ5ZqJ5ZqJ5ZqJ5Z",  // bcrypt hash of "manager123"
     "google_id": null,
     "microsoft_id": null,
     "role": "manager",
     "assigned_depot_id": ObjectId("YOUR_DEPOT_ID_HERE"),
     "created_at": ISODate()
   })
   ```

2. **Login as Manager**
   - Go to http://localhost:5000/depot_login.html
   - Email: `manager@chennai.com`
   - Password: `manager123`
   - Click "Login as Manager"

3. **Manage Reports**
   - View all reports for your depot
   - Update status dropdown
   - Click "Update" to change status

---

## 🔑 Pre-configured Test Accounts

### Passenger User Account
- Email: `user@example.com`
- Password: Create via signup

### Manager Account (After Setup)
- Email: `manager@chennai.com`
- Password: `manager123`
- Assigned to: Chennai Depot

---

## 📍 Available Test Depots

The system includes 10 major Tamil Nadu bus depots:

1. **Chennai** - Mofussil Bus Terminus (13.0827, 80.2707)
2. **Coimbatore** - Central Bus Depot (11.0168, 76.9558)
3. **Madurai** - Periyar Bus Stand (9.9252, 78.1198)
4. **Trichy** - Central Bus Stand (10.7905, 78.7047)
5. **Salem** - New Bus Stand (11.6643, 78.1460)
6. **Tirunelveli** - New Bus Stand (8.7139, 77.7567)
7. **Erode** - Central Bus Stand (11.3410, 77.7172)
8. **Vellore** - Bus Stand (12.9165, 79.1325)
9. **Thanjavur** - New Bus Stand (10.7870, 79.1378)
10. **Kanchipuram** - Bus Stand (12.8342, 79.7036)

---

## 🧪 Testing Checklist

- [ ] User signup works
- [ ] User login works
- [ ] Map loads with depot markers
- [ ] Clicking depot marker shows popup
- [ ] Selecting depot confirms selection
- [ ] Submitting luggage report works
- [ ] Dashboard shows submitted reports
- [ ] Manager login portal accessible
- [ ] Manager can view depot reports
- [ ] Manager can update report status
- [ ] Real-time notifications work (optional)

---

## ⚠️ Common Issues & Solutions

### Issue: MongoDB Connection Error
**Solution:** Check `.env` file, ensure `MONGODB_URI` is correct

### Issue: Map Not Loading
**Solution:** Check browser console, verify internet connection (Leaflet CDN)

### Issue: Login Fails Silently
**Solution:** Check browser Network tab for API errors

### Issue: OAuth Not Working
**Solution:** OAuth is optional. Use email/password login for testing.

---

## 🌐 URLs Reference

| Page | URL |
|------|-----|
| User Login | http://localhost:5000/login.html |
| User Signup | http://localhost:5000/signup.html |
| Interactive Map | http://localhost:5000/map.html |
| User Dashboard | http://localhost:5000/dashboard.html |
| Manager Login | http://localhost:5000/depot_login.html |
| Manager Dashboard | http://localhost:5000/manager_dashboard.html |

---

## 📊 API Testing with Curl

### Test User Signup
```bash
curl -X POST http://localhost:5000/api/auth/signup \
  -H "Content-Type: application/json" \
  -d "{\"name\":\"Test User\",\"email\":\"test@example.com\",\"password\":\"password123\"}"
```

### Test User Login
```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"test@example.com\",\"password\":\"password123\"}"
```

### Get All Depots
```bash
curl http://localhost:5000/api/depots
```

---

## 🎉 Success Indicators

✅ MongoDB connected without errors  
✅ Server running on port 5000  
✅ Frontend pages load correctly  
✅ Map displays all 10 depot markers  
✅ User authentication works  
✅ Report submission works  
✅ Manager dashboard accessible  

---

## 📞 Support

For issues or questions:
1. Check browser console for JavaScript errors
2. Check terminal for Python/Flask errors
3. Verify MongoDB connection in `.env`
4. Ensure virtual environment is activated

---

**Happy Testing! 🚌🧳**
