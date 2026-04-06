# Working OAuth Setup - Quick Guide

## 🚀 METHOD 1: Quick OAuth Setup (5 Minutes)

### Google OAuth Setup
1. **Go to:** https://console.cloud.google.com/
2. **Create new project** or use existing
3. **Enable APIs:** Google+ API, Google OAuth2 API
4. **Create OAuth Client:**
   - Go to "Credentials" → "Create Credentials" → "OAuth client ID"
   - Select "Web application"
   - Name: "TNSTC Lost & Found"
   - **Authorized redirect URI:** `http://127.0.0.1:5000/google/callback`
   - Click "Create"
5. **Copy credentials:**
   - Client ID: `xxxxxxxxxx.apps.googleusercontent.com`
   - Client Secret: `xxxxxxxxxx`

### Set Environment Variables
```bash
# Windows PowerShell
$env:GOOGLE_CLIENT_ID = "your_google_client_id_here"
$env:GOOGLE_CLIENT_SECRET = "your_google_client_secret_here"

# Windows Command Prompt
set GOOGLE_CLIENT_ID=your_google_client_id_here
set GOOGLE_CLIENT_SECRET=your_google_client_secret_here
```

## 🚀 METHOD 2: Use OAuth Playground (Testing Only)

### Google OAuth Playground
1. **Go to:** https://developers.google.com/oauthplayground
2. **Settings (gear icon) → Check "Use your own OAuth credentials"**
3. **Enter your OAuth client ID and secret**
4. **Select scopes:** `email`, `profile`
5. **Authorize APIs** → Get authorization code
6. **Exchange authorization code for tokens**

## 🚀 METHOD 3: Skip OAuth (Recommended for Testing)

The system already works perfectly with email/password login. OAuth is optional.

### Current Status
✅ Email/password login works perfectly
✅ All other functionality works
✅ OAuth buttons show helpful messages
❌ OAuth requires external setup

### To Enable OAuth Later
1. Follow Method 1 above
2. Set environment variables
3. Restart server
4. OAuth buttons will work

## 🧪 Testing OAuth

### Test OAuth Endpoints
```bash
# Start server first
.\venv\Scripts\python.exe final_working_server.py

# Test OAuth URLs
curl http://127.0.0.1:5000/api/auth/google/url
curl http://127.0.0.1:5000/api/auth/microsoft/url
```

### Expected Results
**Without OAuth:**
```
{"url": null, "message": "Google OAuth not configured..."}
```

**With OAuth:**
```
{"url": "https://accounts.google.com/o/oauth2/v2/auth?..."}
```

## 🌐 Browser Testing

1. **Go to:** http://127.0.0.1:5000/login.html
2. **Click OAuth buttons:**
   - Without OAuth: Shows helpful message
   - With OAuth: Redirects to Google/Microsoft
3. **Email/password login:** Always works

## 🔍 Troubleshooting

### OAuth Not Working?
1. **Check server console:** Shows OAuth status on startup
2. **Check environment variables:** Are they set?
3. **Check redirect URI:** Must match exactly
4. **Check OAuth app:** Is it configured for testing?

### Common Issues
- **"redirect_uri_mismatch"**: URI doesn't match OAuth app
- **"invalid_client"**: Wrong client ID/secret
- **"access_denied"**: User denied permission

## 🎯 Recommendation

**For now:** Use email/password login (works perfectly)
**For production:** Set up OAuth following Method 1

The system is fully functional without OAuth. OAuth is just an additional login option.
