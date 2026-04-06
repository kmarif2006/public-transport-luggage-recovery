# Gmail SMTP Setup Guide for TNSTC Lost & Found

## 📧 Gmail Configuration Steps

### 1. Create a Gmail Account (if you don't have one)
- Create: `tnstc.luggage.recovery@gmail.com`
- Or use your existing Gmail account

### 2. Enable 2-Factor Authentication
1. Go to: https://myaccount.google.com/security
2. Enable 2-Step Verification
3. Follow the setup process

### 3. Generate App Password
1. Go to: https://myaccount.google.com/apppasswords
2. Select "Mail" for the app
3. Select "Other (Custom name)" and enter "TNSTC Lost & Found"
4. Click "Generate"
5. Copy the 16-character password (e.g., `abcd efgh ijkl mnop`)

### 4. Update the Code
In `final_working_server.py`, line 543:

```python
# Replace with your actual credentials
gmail_user = "your_email@gmail.com"  # Your Gmail address
gmail_app_password = "abcd_efgh_ijkl_mnop"  # Your 16-char app password (without spaces)
```

### 5. Test the Notification
1. Restart the server
2. Login as depot manager
3. Click "Notify User" on any match
4. Check server console for email sending status

## 📨 Email Template Features

The system sends professional emails with:
- ✅ Match details and similarity score
- ✅ Report and found item information
- ✅ Depot contact details
- ✅ Next steps for user
- ✅ Automatic status update to "found"

## 🔄 Alternative: Use a Test Email Service

For testing without Gmail, you can temporarily modify the code to use a test service:

```python
# For testing only - print email to console instead of sending
print(f"📧 EMAIL TO: {user_email}")
print(f"📧 SUBJECT: {subject}")
print(f"📧 BODY: {body}")
# Skip actual SMTP sending
```

## 🛡️ Security Notes

- ✅ Use App Password (not your regular password)
- ✅ Never commit passwords to Git
- ✅ Consider using environment variables for production
- ✅ Gmail has daily sending limits (100-500 emails/day)

## 🚀 Production Deployment

For production, consider:
- Using a dedicated email service (SendGrid, AWS SES)
- Setting up email templates
- Adding email tracking
- Implementing unsubscribe options
