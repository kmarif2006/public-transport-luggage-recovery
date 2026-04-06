# OAuth Setup Guide for TNSTC Lost & Found

## 🔐 Google OAuth Setup

### 1. Create Google OAuth App
1. Go to: https://console.cloud.google.com/
2. Create a new project or select existing
3. Go to "APIs & Services" → "Credentials"
4. Click "Create Credentials" → "OAuth client ID"
5. Select "Web application"
6. Add authorized redirect URI: `http://127.0.0.1:5000/google/callback`
7. Copy Client ID and Client Secret

### 2. Set Environment Variables
```bash
# For Windows (PowerShell)
$env:GOOGLE_CLIENT_ID = "your_google_client_id_here"
$env:GOOGLE_CLIENT_SECRET = "your_google_client_secret_here"

# For Windows (Command Prompt)
set GOOGLE_CLIENT_ID=your_google_client_id_here
set GOOGLE_CLIENT_SECRET=your_google_client_secret_here
```

### 3. Or Update Code Directly
In `final_working_server.py`, lines 41-42:
```python
app.config['GOOGLE_CLIENT_ID'] = 'your_actual_google_client_id'
app.config['GOOGLE_CLIENT_SECRET'] = 'your_actual_google_client_secret'
```

## 🔐 Microsoft OAuth Setup

### 1. Create Microsoft App
1. Go to: https://portal.azure.com/#blade/Microsoft_AAD_RegisteredApps
2. Click "New registration"
3. Name: "TNSTC Lost & Found"
4. Redirect URI: `http://127.0.0.1:5000/microsoft/callback`
5. Copy Application (client) ID
6. Go to "Certificates & secrets" → "New client secret"
7. Copy the secret value

### 2. Set Environment Variables
```bash
# For Windows (PowerShell)
$env:MS_CLIENT_ID = "your_microsoft_client_id_here"
$env:MS_CLIENT_SECRET = "your_microsoft_client_secret_here"

# For Windows (Command Prompt)
set MS_CLIENT_ID=your_microsoft_client_id_here
set MS_CLIENT_SECRET=your_microsoft_client_secret_here
```

### 3. Or Update Code Directly
In `final_working_server.py`, lines 45-46:
```python
app.config['MS_CLIENT_ID'] = 'your_actual_microsoft_client_id'
app.config['MS_CLIENT_SECRET'] = 'your_actual_microsoft_client_secret'
```

## 🧪 Test OAuth

### 1. Start Server
```bash
cd d:\minip\public-transport-luggage-recovery
.\venv\Scripts\python.exe final_working_server.py
```

### 2. Test OAuth Endpoints
```bash
# Test Google OAuth URL
curl http://127.0.0.1:5000/api/auth/google/url

# Test Microsoft OAuth URL
curl http://127.0.0.1:5000/api/auth/microsoft/url
```

### 3. Test via Browser
1. Go to: http://127.0.0.1:5000/login.html
2. Click "Continue with Google" or "Continue with Microsoft"
3. Should redirect to OAuth provider
4. After login, should redirect back and log in

## 🔍 Troubleshooting

### OAuth Not Working?
1. Check if credentials are set correctly
2. Verify redirect URIs match exactly
3. Check server console for error messages
4. Ensure OAuth app is configured for "Testing" mode

### Common Issues:
- **"OAuth not configured" message**: Credentials not set
- **Redirect mismatch**: URI doesn't match what's configured
- **Invalid client**: Wrong client ID/secret
- **Scope issues**: OAuth app missing required scopes

## 🚀 Production Deployment

For production:
1. Use environment variables (not hardcoded credentials)
2. Update redirect URIs to production domain
3. Enable OAuth apps for production use
4. Use HTTPS (required for OAuth)
5. Consider using a secrets management service
