"""
Manager notify user functionality
"""
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone
import secrets
from flask import Blueprint, jsonify, request
from bson import ObjectId

# Email configuration
EMAIL_CONFIG = {
    'smtp_server': 'smtp.gmail.com',
    'smtp_port': 587,
    'sender_email': 'tnbus.lostfound@gmail.com',
    'sender_password': 'your-app-password',
}

def generate_verification_code():
    """Generate secure verification code"""
    return secrets.token_urlsafe(8).upper()

def send_match_notification_email(user_email, user_name, item_name, match_details, depot_info):
    """Send email notification to user about found item"""
    
    verification_code = generate_verification_code()
    
    # Google Form URL (you'll create this)
    google_form_url = "https://forms.gle/your-verification-form"
    
    subject = f"🎉 MATCH FOUND! Your {item_name} has been located!"
    
    body = f"""
Dear {user_name},

🎉 GREAT NEWS! A product similar to your lost item has been found!

📱 ITEM DETAILS:
• Lost Item: {item_name}
• Match Score: {match_details.get('match_score', 'N/A')}%
• Found Location: {depot_info.get('name', 'Depot')} ({depot_info.get('city', 'City')})
• Found Date: {match_details.get('found_date', 'N/A')}
• Description: {match_details.get('description', 'N/A')}

🔔 NEXT STEPS - VERIFICATION REQUIRED:

📝 CLAIM YOUR ITEM: {google_form_url}
🔐 Your Verification Code: {verification_code}

⚠️ IMPORTANT:
• Upload proof of purchase (receipt, invoice, or photos)
• Include verification code in form
• Only rightful owner can claim the item

📍 DEPOT CONTACT INFORMATION:
• Depot: {depot_info.get('name', 'Depot')}
• Address: {depot_info.get('city', 'City')}, {depot_info.get('district', 'District')}
• Phone: {depot_info.get('contact_number', 'Contact Number')}
• Manager: {depot_info.get('manager_email', 'N/A')}

⏰ Please complete verification within 7 days.

Thank you for using TN Bus Lost & Found System!

🚌 Tamil Nadu State Transport Corporation
📞 Helpline: 1800-425-1234
🌐 www.tnlostfound.gov.in
    """
    
    # Send email
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_CONFIG['sender_email']
        msg['To'] = user_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        
        server = smtplib.SMTP(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['smtp_port'])
        server.starttls()
        server.login(EMAIL_CONFIG['sender_email'], EMAIL_CONFIG['sender_password'])
        server.send_message(msg)
        server.quit()
        
        print(f"✅ Email sent to {user_email}")
        print(f"🔐 Verification code: {verification_code}")
        
        return True, verification_code
        
    except Exception as e:
        print(f"❌ Email failed: {e}")
        return False, None
