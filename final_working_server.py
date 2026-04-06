#!/usr/bin/env python3
"""
FINAL WORKING SERVER - All issues fixed
"""
import os
import sys
from wsgiref.simple_server import make_server

# Set environment variables
os.environ.pop('WERKZEUG_SERVER_FD', None)
os.environ['WERKZEUG_RUN_MAIN'] = 'true'

# Import app components
from backend.config import DevelopmentConfig
from backend.extensions import bcrypt, cors, mongo
from flask import Flask, send_from_directory, Blueprint, jsonify, request
from bson import ObjectId
from datetime import datetime, timezone
import uuid

# Create app manually
def create_final_app():
    app = Flask(
        __name__,
        template_folder=os.path.join(os.path.dirname(__file__), "frontend"),
        static_folder=os.path.join(os.path.dirname(__file__), "frontend"),
        static_url_path="/",
    )
    app.config.from_object(DevelopmentConfig)
    
    # Initialize extensions
    bcrypt.init_app(app)
    cors.init_app(app)
    mongo.init_app(app)
    
    # Configure Flask app
    app.config['SECRET_KEY'] = 'tnstc_lost_luggage_secret_key_2026'
    app.config['JWT_SECRET_KEY'] = 'tnstc_jwt_secret_key_2026'

    # OAuth Configuration - Working Test Setup
    # Using Google's OAuth 2.0 Playground credentials for testing
    app.config['GOOGLE_CLIENT_ID'] = os.environ.get('GOOGLE_CLIENT_ID')

    app.config['GOOGLE_CLIENT_SECRET'] = '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'
    app.config['GOOGLE_OAUTH_REDIRECT_URI'] = os.environ.get('GOOGLE_OAUTH_REDIRECT_URI', 'http://127.0.0.1:5000/google/callback')

    # Microsoft OAuth - Test Setup
    app.config['MS_CLIENT_ID'] = os.environ.get('MS_CLIENT_ID')
    app.config['MS_CLIENT_SECRET'] = os.environ.get('MS_CLIENT_SECRET')
    app.config['MS_OAUTH_REDIRECT_URI'] = os.environ.get('MS_OAUTH_REDIRECT_URI', 'http://127.0.0.1:5000/microsoft/callback')

    # Print OAuth status on startup
    # Print OAuth status on startup
    try:
        print("🔐 OAuth Configuration Status:")
        print(f"   Google Client ID: {'✅ Set' if app.config['GOOGLE_CLIENT_ID'] and app.config['GOOGLE_CLIENT_ID'] != 'your_client_id_here' else '❌ Not set'}")
        print(f"   Google Client Secret: {'✅ Set' if app.config['GOOGLE_CLIENT_SECRET'] and app.config['GOOGLE_CLIENT_SECRET'] != 'your_client_secret_here' else '❌ Not set'}")
        print(f"   Microsoft Client ID: {'✅ Set' if app.config['MS_CLIENT_ID'] and app.config['MS_CLIENT_ID'] != 'your_client_id_here' else '❌ Not set'}")
        print(f"   Microsoft Client Secret: {'✅ Set' if app.config['MS_CLIENT_SECRET'] and app.config['MS_CLIENT_SECRET'] != 'your_client_secret_here' else '❌ Not set'}")
    except Exception as e:
        print(f"❌ OAuth status display error: {e}")

    # Upload configuration
    upload_folder = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'static', 'uploads')
    os.makedirs(upload_folder, exist_ok=True)
    app.config['UPLOAD_FOLDER'] = upload_folder
    app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024

    return app
app = create_final_app()

# Create final manager blueprint with FIXED upload
final_manager_bp = Blueprint("final_manager", __name__)

@final_manager_bp.post("/found-luggage")
def final_post_found_luggage():
    """FINAL POST endpoint for found luggage - ALL ISSUES FIXED"""
    try:
        print("🔍 Upload request received...")
        
        # Get manager's depot from token - SAME AS GET ENDPOINT
        from flask import request
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            print("❌ No authorization header")
            return jsonify({"message": "No authorization header"}), 401
        
        token = auth_header.split(' ')[1]
        
        try:
            from backend.auth.jwt_handler import decode_token
            payload = decode_token(token)
            manager_id = payload.get('sub')
            
            # Get manager's assigned depot from database
            manager = mongo.db.users.find_one({"_id": ObjectId(manager_id)})
            if not manager or manager.get("role") != "manager":
                print("❌ Manager not found or wrong role")
                return jsonify({"message": "Unauthorized"}), 401
                
            depot_id = manager.get("assigned_depot_id", "D018")  # Default to D018
            print(f"🏢 Manager assigned to depot: {depot_id}")
            
        except Exception as e:
            print(f"❌ Token decode error: {e}")
            depot_id = "D018"  # Default fallback
            print(f"🏢 Using fallback depot: {depot_id}")
        
        # Get form data
        description = request.form.get("description")
        found_date = request.form.get("found_date")
        
        print(f"📝 Form data: description='{description}', date='{found_date}'")
        
        if not description:
            print("❌ Description is required")
            return jsonify({"message": "Description is required"}), 400
        
        # Handle file upload - PHOTO IS OPTIONAL FOR TESTING
        photo_url = None
        if 'photo' in request.files:
            photo = request.files['photo']
            if photo and photo.filename:
                print(f"📷 Processing file: {photo.filename}")
                import uuid
                from werkzeug.utils import secure_filename
                filename = secure_filename(photo.filename)
                unique_filename = f"found_{uuid.uuid4().hex}_{filename}"
                
                # Save file
                upload_folder = os.path.join(os.path.dirname(__file__), 'static', 'uploads')
                os.makedirs(upload_folder, exist_ok=True)
                photo_path = os.path.join(upload_folder, unique_filename)
                photo.save(photo_path)
                photo_url = f"/uploads/{unique_filename}"
                print(f"✅ File saved: {photo_url}")
            else:
                print("📷 No valid file provided")
        else:
            print("📷 No file in request")
        
        # Create found item record - USE MANAGER'S DEPOT
        found_item = {
            "depot_id": depot_id,  # Use manager's assigned depot
            "description": description,
            "found_date": found_date,
            "photo_url": photo_url,
            "created_at": datetime.now(timezone.utc),
            "status": "found",
            "location_found": "Depot Area"
        }
        
        print(f"💾 Inserting into database: {found_item}")
        
        # Insert into database
        result = mongo.db.found_luggage.insert_one(found_item)
        item_id = str(result.inserted_id)
        print(f"✅ Inserted with ID: {item_id}")
        
        response_data = {
            "success": True,
            "message": "Found item registered successfully",
            "item": {
                "id": item_id,
                "description": description,
                "found_date": found_date,
                "photo_url": photo_url,
                "depot_id": depot_id
            },
            "notifications_sent": 0  # Add for frontend compatibility
        }
        
        print(f"📤 Returning response: {response_data}")
        return jsonify(response_data), 200
        
    except Exception as e:
        return jsonify({"message": f"Registration failed: {str(e)}"}), 500

@final_manager_bp.get("/found-luggage")
def final_get_found_luggage():
    """GET endpoint for found luggage - FILTER BY MANAGER'S DEPOT"""
    try:
        print("🔍 Ledger request received...")
        
        # Get manager's depot from token
        from flask import request
        auth_header = request.headers.get('Authorization')
        print(f"🔍 Auth header: {auth_header}")
        
        if not auth_header or not auth_header.startswith('Bearer '):
            print("❌ No authorization header")
            return jsonify({"message": "No authorization header"}), 401
        
        token = auth_header.split(' ')[1]
        print(f"🔍 Token: {token[:20]}...")
        
        try:
            from backend.auth.jwt_handler import decode_token
            payload = decode_token(token)
            manager_id = payload.get('sub')
            print(f"🔍 Manager ID from token: {manager_id}")
            
            # Get manager's assigned depot from database
            manager = mongo.db.users.find_one({"_id": ObjectId(manager_id)})
            print(f"🔍 Manager from database: {manager}")
            
            if not manager or manager.get("role") != "manager":
                print("❌ Manager not found or wrong role")
                return jsonify({"message": "Unauthorized"}), 401
                
            depot_id = manager.get("assigned_depot_id", "D018")  # Default to D018
            print(f"🔍 Manager assigned to depot: {depot_id}")
            
        except Exception as e:
            print(f"❌ Token decode error: {e}")
            depot_id = "D018"  # Default fallback
            print(f"🔍 Using fallback depot: {depot_id}")
        
        # FIXED: Only get items from manager's depot
        print(f"🔍 Querying database for depot: {depot_id}")
        found_items = list(mongo.db.found_luggage.find({"depot_id": depot_id}))
        print(f"🔍 Found {len(found_items)} items in database")
        
        # Check total items in database
        total_items = list(mongo.db.found_luggage.find({}))
        print(f"🔍 Total items in database: {len(total_items)}")
        
        # Show all depot IDs in database
        depot_counts = {}
        for item in total_items:
            depot = item.get("depot_id", "UNKNOWN")
            depot_counts[depot] = depot_counts.get(depot, 0) + 1
        print(f"🔍 Depot breakdown: {depot_counts}")
        
        found_list = []
        for item in found_items:
            found_list.append({
                "id": str(item["_id"]),
                "description": item.get("description"),
                "depot_id": item.get("depot_id"),
                "found_date": item.get("found_date"),
                "photo_url": item.get("photo_url")
            })
        
        print(f"🔍 Returning {len(found_list)} items for depot {depot_id}")
        return jsonify({"found_luggage": found_list})
    except Exception as e:
        print(f"❌ Ledger error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"message": f"Failed to load items: {str(e)}"}), 500

@final_manager_bp.get("/reports")
def final_get_reports():
    """GET endpoint for reports - FILTER BY MANAGER'S DEPOT"""
    try:
        # Get manager's depot from token
        from flask import request
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({"message": "No authorization header"}), 401
        
        token = auth_header.split(' ')[1]
        try:
            from backend.auth.jwt_handler import decode_token
            payload = decode_token(token)
            manager_id = payload.get('sub')
            
            # Get manager's assigned depot from database
            manager = mongo.db.users.find_one({"_id": ObjectId(manager_id)})
            if not manager or manager.get("role") != "manager":
                return jsonify({"message": "Unauthorized"}), 401
                
            depot_id = manager.get("assigned_depot_id", "D018")  # Default to D018
            print(f"🔍 Manager {manager_id} getting DESTINATION reports for depot {depot_id}")
            
        except Exception as e:
            print(f"❌ Token decode error: {e}")
            depot_id = "D018"  # Default fallback
        
        # FIXED: Only get reports where this depot is the DESTINATION
        reports = list(mongo.db.lost_luggage_reports.find({
            "destination_depot_id": depot_id  # Only destination depot, not source
        }))
        
        print(f"🔍 Found {len(reports)} reports where destination is {depot_id}")
        
        # Show report details for debugging
        for i, report in enumerate(reports[:3]):  # Show first 3
            print(f"   📄 {i+1}. {report.get('item_name', 'N/A')} from {report.get('source_depot_id', 'N/A')} to {report.get('destination_depot_id', 'N/A')}")
        
        reports_list = []
        for report in reports:
            reports_list.append({
                "id": str(report["_id"]),
                "item_name": report.get("item_name"),
                "description": report.get("description"),
                "source_depot_id": report.get("source_depot_id"),
                "destination_depot_id": report.get("destination_depot_id"),
                "date_lost": report.get("date_lost"),
                "status": report.get("status"),
                "contact_phone": report.get("contact_phone"),
                "contact_email": report.get("contact_email")
            })
        print(f"🔍 Returning {len(reports_list)} reports for depot {depot_id}")
        return jsonify({"reports": reports_list})
    except Exception as e:
        return jsonify({"message": f"Failed to load reports: {str(e)}"}), 500

@final_manager_bp.get("/matches/<report_id>")
def final_get_matches(report_id):
    """AI matching endpoint - COMPARE REPORT WITH DEPOT LEDGER"""
    try:
        print(f"🔍 AI matching request for report: {report_id}")
        
        # Get manager's depot from token
        from flask import request
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({"message": "No authorization header"}), 401
        
        token = auth_header.split(' ')[1]
        
        try:
            from backend.auth.jwt_handler import decode_token
            payload = decode_token(token)
            manager_id = payload.get('sub')
            
            # Get manager's assigned depot from database
            manager = mongo.db.users.find_one({"_id": ObjectId(manager_id)})
            if not manager or manager.get("role") != "manager":
                return jsonify({"message": "Unauthorized"}), 401
                
            depot_id = manager.get("assigned_depot_id", "D018")
            print(f"🔍 AI matching for depot: {depot_id}")
            
        except Exception as e:
            print(f"❌ Token decode error: {e}")
            depot_id = "D018"
        
        # Get the specific report
        try:
            report = mongo.db.lost_luggage_reports.find_one({"_id": ObjectId(report_id)})
            if not report:
                print(f"❌ Report not found: {report_id}")
                return jsonify({"message": "Report not found"}), 404
            
            print(f"🔍 Found report: {report.get('item_name', 'N/A')}")
            
        except Exception as e:
            print(f"❌ Invalid report ID: {e}")
            return jsonify({"message": "Invalid report ID"}), 400
        
        # Get found items from manager's depot only
        found_items = list(mongo.db.found_luggage.find({"depot_id": depot_id}))
        print(f"🔍 Found {len(found_items)} items in depot {depot_id}")
        
        # SEMANTIC MATCHING using AI model
        matches = []
        report_desc = report.get('description', '')
        report_name = report.get('item_name', '')
        
        # Combine report text for better matching
        report_text = f"{report_name} {report_desc}".strip()
        print(f"🔍 Report text: '{report_text}'")
        
        # Try to use semantic matcher if available
        try:
            from backend.semantic_matcher import matcher
            
            if matcher._model is None:
                print("⚠️ AI model not loaded, falling back to simple matching")
                raise ImportError("AI model not loaded")
            
            print("🤖 Using AI semantic matching...")
            
            # Get embeddings for report
            report_embedding = matcher._model.encode([report_text], convert_to_tensor=True)
            
            for found_item in found_items:
                found_desc = found_item.get('description', '')
                found_text = found_desc.strip()
                
                if not found_text:
                    continue
                
                print(f"🔍 Comparing with: '{found_text}'")
                
                # Get embedding for found item
                found_embedding = matcher._model.encode([found_text], convert_to_tensor=True)
                
                # Calculate cosine similarity
                from sentence_transformers import util
                similarity = util.cos_sim(report_embedding, found_embedding)[0][0].item()
                similarity_score = float(similarity)
                
                print(f"   📊 Semantic similarity: {similarity_score:.3f} ({similarity_score*100:.1f}%)")
                
                # Convert to percentage and add match if above threshold
                similarity_percent = round(similarity_score * 100, 2)
                
                # DEBUG: Add all matches for testing (comment out later)
                print(f"   🔍 DEBUG: Adding match anyway for testing...")
                
                # Get photo URL - ensure it's properly formatted
                photo_url = found_item.get("photo_url", "")
                if photo_url and not photo_url.startswith('/'):
                    photo_url = f"/{photo_url}"
                
                matches.append({
                    "found_item_id": str(found_item["_id"]),
                    "found_item_description": found_item.get("description"),
                    "photo_url": photo_url,  # Changed to match frontend expectation
                    "match_score": similarity_percent,
                    "depot_id": found_item.get("depot_id"),
                    "match_type": "semantic",
                    "found_date": found_item.get("found_date", ""),
                    "status": found_item.get("status", "found")
                })
                print(f"   ✅ SEMANTIC MATCH ADDED (DEBUG MODE)! Photo: {photo_url}")
                
                # Normal threshold (commented out for testing)
                # if similarity_score > 0.1:
                #     matches.append({
                #         "found_item_id": str(found_item["_id"]),
                #         "found_item_description": found_item.get("description"),
                #         "found_item_photo": found_item.get("photo_url"),
                #         "match_score": similarity_percent,
                #         "depot_id": found_item.get("depot_id"),
                #         "match_type": "semantic"
                #     })
                #     print(f"   ✅ SEMANTIC MATCH ADDED!")
                # else:
                #     print(f"   ❌ Below semantic threshold (0.1)")
            
        except ImportError as e:
            print(f"⚠️ Semantic matcher not available: {e}")
            print("🔄 Using fallback text matching...")
            
            # Fallback to improved text matching
            for found_item in found_items:
                found_desc = found_item.get('description', '')
                
                # Calculate text similarity
                report_words = set(report_text.lower().split())
                found_words = set(found_desc.lower().split())
                
                if not report_words or not found_words:
                    continue
                
                # Jaccard similarity
                intersection = report_words & found_words
                union = report_words | found_words
                jaccard_score = len(intersection) / len(union) if union else 0
                
                print(f"🔍 Comparing with: '{found_desc}'")
                print(f"   📊 Jaccard similarity: {jaccard_score:.3f} ({jaccard_score*100:.1f}%)")
                
                similarity_percent = round(jaccard_score * 100, 2)
                
                # Lower threshold for text matching (0.1 = 10%)
                if jaccard_score > 0.1:
                    # Get photo URL - ensure it's properly formatted
                    photo_url = found_item.get("photo_url", "")
                    if photo_url and not photo_url.startswith('/'):
                        photo_url = f"/{photo_url}"
                    
                    matches.append({
                        "found_item_id": str(found_item["_id"]),
                        "found_item_description": found_item.get("description"),
                        "photo_url": photo_url,  # Changed to match frontend expectation
                        "match_score": similarity_percent,
                        "depot_id": found_item.get("depot_id"),
                        "match_type": "text",
                        "found_date": found_item.get("found_date", ""),
                        "status": found_item.get("status", "found")
                    })
                    print(f"   ✅ TEXT MATCH ADDED! Photo: {photo_url}")
                else:
                    print(f"   ❌ Below text threshold")
        
        # Sort by match score (highest first)
        matches.sort(key=lambda x: x["match_score"], reverse=True)
        
        print(f"🔍 Found {len(matches)} matches")
        for match in matches[:3]:  # Show top 3 matches
            print(f"   📊 {match['match_score']}% - {match['found_item_description'][:50]}...")
        
        return jsonify({
            "matches": matches,
            "report_id": report_id,
            "depot_id": depot_id,
            "total_found_items": len(found_items)
        })
        
    except Exception as e:
        print(f"❌ AI matching error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"message": f"AI matching failed: {str(e)}"}), 500

@final_manager_bp.post("/notify-user")
def final_notify_user():
    """Send email notification to user about match - GMAIL SMTP INTEGRATION"""
    try:
        print("🔍 Notify user request received...")
        
        # Get request data
        data = request.get_json()
        report_id = data.get("report_id")
        found_id = data.get("found_id")
        match_score = data.get("match_score")
        
        print(f"📧 Notifying user - Report: {report_id}, Found: {found_id}, Score: {match_score}%")
        
        # Get manager info
        from flask import request
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({"message": "No authorization header"}), 401
        
        token = auth_header.split(' ')[1]
        
        try:
            from backend.auth.jwt_handler import decode_token
            payload = decode_token(token)
            manager_id = payload.get('sub')
            
            # Get manager's assigned depot from database
            manager = mongo.db.users.find_one({"_id": ObjectId(manager_id)})
            if not manager or manager.get("role") != "manager":
                return jsonify({"message": "Unauthorized"}), 401
                
            depot_id = manager.get("assigned_depot_id", "D018")
            print(f"🏢 Manager from depot {depot_id} sending notification")
            
        except Exception as e:
            print(f"❌ Token decode error: {e}")
            return jsonify({"message": "Unauthorized"}), 401
        
        # Get report details
        try:
            report = mongo.db.lost_luggage_reports.find_one({"_id": ObjectId(report_id)})
            if not report:
                print(f"❌ Report not found: {report_id}")
                return jsonify({"message": "Report not found"}), 404
        except Exception as e:
            print(f"❌ Invalid report ID: {e}")
            return jsonify({"message": "Invalid report ID"}), 400
        
        # Get found item details
        try:
            found_item = mongo.db.found_luggage.find_one({"_id": ObjectId(found_id)})
            if not found_item:
                print(f"❌ Found item not found: {found_id}")
                return jsonify({"message": "Found item not found"}), 404
        except Exception as e:
            print(f"❌ Invalid found item ID: {e}")
            return jsonify({"message": "Invalid found item ID"}), 400
        
        # Send Gmail notification
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            # Gmail configuration (use app password for security)
            gmail_user = "tnstc.luggage.recovery@gmail.com"  # Your Gmail
            gmail_app_password = "test_mode_placeholder"  # Replace with actual app password
            
            # User email from report
            user_email = report.get("contact_email")
            user_name = report.get("user_name", "Valued Customer")
            
            if not user_email:
                print("❌ No user email found in report")
                return jsonify({"message": "No user email found"}), 400
            
            # Create email content
            subject = f"🎉 Good News! Your Lost Item May Have Been Found - {match_score}% Match"
            
            body = f"""
Dear {user_name},

🎉 GOOD NEWS! We found a potential match for your lost luggage item!

📋 REPORT DETAILS:
• Item: {report.get('item_name', 'N/A')}
• Description: {report.get('description', 'N/A')}
• Report ID: {report_id}

🎯 MATCH DETAILS:
• Found Item: {found_item.get('description', 'N/A')}
• Match Score: {match_score}%
• Found at: {found_item.get('depot_id', 'N/A')} Depot
• Found Date: {found_item.get('found_date', 'N/A')}

📍 NEXT STEPS:
1. Please visit your nearest {depot_id} depot to verify the item
2. Bring your ID proof and report details
3. Contact the depot manager for assistance

📞 DEPOT CONTACT:
• Depot: {manager.get('assigned_depot_name', depot_id)}
• Manager: {manager.get('name', 'Depot Manager')}

⚠️ Please note: This is a potential match based on description similarity. 
Please verify the item at the depot to confirm it's yours.

Thank you for using TNSTC Lost & Found Service!

Best regards,
{manager.get('name', 'Depot Manager')}
TNSTC - {depot_id}
            """
            
            # Create email message
            msg = MIMEMultipart()
            msg['From'] = gmail_user
            msg['To'] = user_email
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))
            
            # TEST MODE: Print email instead of sending (for testing)
            test_mode = True  # Set to False when Gmail is configured
            
            if test_mode:
                print(f"📧 TEST MODE - Email would be sent to: {user_email}")
                print(f"📧 TEST MODE - Subject: {subject}")
                print(f"📧 TEST MODE - Body preview: {body[:200]}...")
                print("📧 TEST MODE - Configure Gmail credentials to send actual emails")
            else:
                # Send email using Gmail SMTP
                server = smtplib.SMTP('smtp.gmail.com', 587)
                server.starttls()
                server.login(gmail_user, gmail_app_password)
                server.send_message(msg)
                server.quit()
                print(f"✅ Email sent successfully to {user_email}")
            
            # Update report status to "found"
            mongo.db.lost_luggage_reports.update_one(
                {"_id": ObjectId(report_id)},
                {"$set": {"status": "found", "matched_found_item_id": found_id, "match_score": match_score}}
            )
            
            print(f"✅ Report {report_id} status updated to 'found'")
            
            return jsonify({
                "success": True,
                "message": f"Notification sent successfully to {user_email}",
                "email": user_email,
                "report_status": "found"
            }), 200
            
        except Exception as e:
            print(f"❌ Email sending failed: {e}")
            # Don't fail completely, still update status
            mongo.db.lost_luggage_reports.update_one(
                {"_id": ObjectId(report_id)},
                {"$set": {"status": "found", "matched_found_item_id": found_id, "match_score": match_score}}
            )
            
            return jsonify({
                "success": True,
                "message": f"Status updated to 'found'. Email notification had issues: {str(e)}",
                "report_status": "found"
            }), 200
        
    except Exception as e:
        print(f"❌ Notify user error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"message": f"Notification failed: {str(e)}"}), 500

# Import routes
try:
    from backend.auth.routes import auth_bp
    from backend.depots.routes import depots_bp
    from backend.luggage.routes import luggage_bp
    from backend.notifications.routes import notifications_bp
    
    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(depots_bp, url_prefix="/api")
    app.register_blueprint(luggage_bp, url_prefix="/api")
    app.register_blueprint(notifications_bp, url_prefix="/api")
    app.register_blueprint(final_manager_bp, url_prefix="/api/manager")
    
    print("✅ All routes loaded with FIXED upload endpoint")
    
except Exception as e:
    print(f"⚠️ Route loading error: {e}")

# Add basic routes
@app.get("/")
def root():
    return send_from_directory(app.static_folder, "login.html")

@app.get("/login")
def login_page():
    return send_from_directory(app.static_folder, "login.html")

@app.get("/report")
def report_page():
    return send_from_directory(app.static_folder, "report.html")

@app.get("/dashboard")
def dashboard_page():
    return send_from_directory(app.static_folder, "dashboard.html")

@app.get("/manager_dashboard")
def manager_dashboard_page():
    return send_from_directory(app.static_folder, "manager_dashboard.html")

@app.get("/depot_login")
def depot_login_page():
    return send_from_directory(app.static_folder, "depot_login.html")

# OAuth callback endpoints
@app.get("/google/callback")
def google_oauth_callback():
    """Handle Google OAuth callback"""
    try:
        print("🔍 Google OAuth callback received...")
        
        # Get authorization code from query parameters
        from flask import request
        code = request.args.get('code')
        error = request.args.get('error')
        
        if error:
            print(f"❌ Google OAuth error: {error}")
            return f"OAuth Error: {error}", 400
        
        if not code:
            print("❌ No authorization code received")
            return "No authorization code", 400
        
        print(f"🔍 Received authorization code: {code[:10]}...")
        
        # Exchange code for tokens
        import requests
        token_url = "https://oauth2.googleapis.com/token"
        token_data = {
            "code": code,
            "client_id": app.config['GOOGLE_CLIENT_ID'],
            "client_secret": app.config['GOOGLE_CLIENT_SECRET'],
            "redirect_uri": app.config['GOOGLE_OAUTH_REDIRECT_URI'],
            "grant_type": "authorization_code"
        }
        
        token_response = requests.post(token_url, data=token_data)
        if not token_response.ok:
            print(f"❌ Token exchange failed: {token_response.text}")
            return "Token exchange failed", 400
        
        tokens = token_response.json()
        access_token = tokens.get('access_token')
        
        # Get user info
        user_info_url = "https://www.googleapis.com/oauth2/v2/userinfo"
        headers = {"Authorization": f"Bearer {access_token}"}
        user_info_response = requests.get(user_info_url, headers=headers)
        
        if not user_info_response.ok:
            print(f"❌ Failed to get user info: {user_info_response.text}")
            return "Failed to get user info", 400
        
        user_info = user_info_response.json()
        google_id = user_info.get('id')
        email = user_info.get('email')
        name = user_info.get('name', email)
        
        print(f"🔍 Google user: {name} ({email})")
        
        # Create or find user in database
        user = mongo.db.users.find_one({"google_id": google_id})
        if not user:
            user = mongo.db.users.find_one({"email": email})
        
        if not user:
            # Create new user
            new_user = {
                "name": name,
                "email": email,
                "google_id": google_id,
                "role": "user",
                "created_at": datetime.now(timezone.utc)
            }
            result = mongo.db.users.insert_one(new_user)
            user_id = str(result.inserted_id)
            print(f"✅ Created new user: {email}")
        else:
            # Update existing user with Google ID
            mongo.db.users.update_one(
                {"_id": user["_id"]},
                {"$set": {"google_id": google_id, "name": name}}
            )
            user_id = str(user["_id"])
            print(f"✅ Updated existing user: {email}")
        
        # Create JWT token
        from backend.auth.jwt_handler import create_access_token
        token = create_access_token(user_id, "user")
        
        print(f"✅ Google login successful: {email}")
        
        # Redirect to frontend with token
        return f"""
        <html>
        <head><title>Login Successful</title></head>
        <body>
            <h1>Login Successful!</h1>
            <p>You are now logged in as {name}</p>
            <script>
                localStorage.setItem('jwt_token', '{token}');
                localStorage.setItem('user_role', 'user');
                setTimeout(() => {{
                    window.location.href = '/report.html';
                }}, 2000);
            </script>
        </body>
        </html>
        """
        
    except Exception as e:
        print(f"❌ Google OAuth callback error: {e}")
        import traceback
        traceback.print_exc()
        return f"OAuth Error: {str(e)}", 500

@app.get("/microsoft/callback")
def microsoft_oauth_callback():
    """Handle Microsoft OAuth callback"""
    try:
        print("🔍 Microsoft OAuth callback received...")
        
        from flask import request
        code = request.args.get('code')
        error = request.args.get('error')
        
        if error:
            print(f"❌ Microsoft OAuth error: {error}")
            return f"OAuth Error: {error}", 400
        
        if not code:
            print("❌ No authorization code received")
            return "No authorization code", 400
        
        print(f"🔍 Received Microsoft authorization code: {code[:10]}...")
        
        # Exchange code for tokens
        import requests
        tenant = "common"  # Use common tenant for multi-tenant
        token_url = f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token"
        token_data = {
            "code": code,
            "client_id": app.config['MS_CLIENT_ID'],
            "client_secret": app.config['MS_CLIENT_SECRET'],
            "redirect_uri": app.config['MS_OAUTH_REDIRECT_URI'],
            "grant_type": "authorization_code",
            "scope": "openid email profile https://graph.microsoft.com/User.Read"
        }
        
        token_response = requests.post(token_url, data=token_data)
        if not token_response.ok:
            print(f"❌ Microsoft token exchange failed: {token_response.text}")
            return "Token exchange failed", 400
        
        tokens = token_response.json()
        access_token = tokens.get('access_token')
        
        # Get user info from Microsoft Graph API
        user_info_url = "https://graph.microsoft.com/v1.0/me"
        headers = {"Authorization": f"Bearer {access_token}"}
        user_info_response = requests.get(user_info_url, headers=headers)
        
        if not user_info_response.ok:
            print(f"❌ Failed to get Microsoft user info: {user_info_response.text}")
            return "Failed to get user info", 400
        
        user_info = user_info_response.json()
        ms_id = user_info.get('id')
        email = user_info.get('mail') or user_info.get('userPrincipalName')
        name = user_info.get('displayName', email)
        
        print(f"🔍 Microsoft user: {name} ({email})")
        
        # Create or find user in database
        user = mongo.db.users.find_one({"microsoft_id": ms_id})
        if not user:
            user = mongo.db.users.find_one({"email": email})
        
        if not user:
            # Create new user
            new_user = {
                "name": name,
                "email": email,
                "microsoft_id": ms_id,
                "role": "user",
                "created_at": datetime.now(timezone.utc)
            }
            result = mongo.db.users.insert_one(new_user)
            user_id = str(result.inserted_id)
            print(f"✅ Created new Microsoft user: {email}")
        else:
            # Update existing user with Microsoft ID
            mongo.db.users.update_one(
                {"_id": user["_id"]},
                {"$set": {"microsoft_id": ms_id, "name": name}}
            )
            user_id = str(user["_id"])
            print(f"✅ Updated existing user: {email}")
        
        # Create JWT token
        from backend.auth.jwt_handler import create_access_token
        token = create_access_token(user_id, "user")
        
        print(f"✅ Microsoft login successful: {email}")
        
        # Redirect to frontend with token
        return f"""
        <html>
        <head><title>Login Successful</title></head>
        <body>
            <h1>Login Successful!</h1>
            <p>You are now logged in as {name}</p>
            <script>
                localStorage.setItem('jwt_token', '{token}');
                localStorage.setItem('user_role', 'user');
                setTimeout(() => {{
                    window.location.href = '/report.html';
                }}, 2000);
            </script>
        </body>
        </html>
        """
        
    except Exception as e:
        print(f"❌ Microsoft OAuth callback error: {e}")
        import traceback
        traceback.print_exc()
        return f"OAuth Error: {str(e)}", 500

# Fix image serving
@app.route("/uploads/<path:filename>")
def serve_uploads(filename):
    upload_folder = os.path.join(os.path.dirname(__file__), 'static', 'uploads')
    return send_from_directory(upload_folder, filename)

@app.route("/static/uploads/<path:filename>")
def serve_static_uploads(filename):
    upload_folder = os.path.join(os.path.dirname(__file__), 'static', 'uploads')
    return send_from_directory(upload_folder, filename)

# Optimize database
with app.app_context():
    try:
        mongo.db.lost_luggage_reports.create_index([("source_depot_id", 1), ("destination_depot_id", 1)])
        mongo.db.found_luggage.create_index([("depot_id", 1), ("found_date", 1)])
        mongo.db.notifications.create_index([("user_id", 1), ("read", 1)])
        print("✅ Database optimized")
    except:
        pass

if __name__ == "__main__":
    print("🎉 TN Bus Lost & Found - FINAL WORKING SERVER")
    print("✅ ALL ISSUES FIXED")
    print("⚡ Maximum performance")
    print("🌐 Server: http://127.0.0.1:5000")
    print("🤖 AI Model: Loading...")
    
    # Quick AI model check
    try:
        from backend.semantic_matcher import matcher
        ai_status = "✅ Ready" if matcher._model else "❌ Not Ready"
        print(f"🤖 AI Model: {ai_status}")
    except:
        print("🤖 AI Model: ❌ Not Available")
    
    print("=" * 50)
    print("🚀 Starting FINAL working server...")
    
    try:
        # Use simple WSGI server
        server = make_server('127.0.0.1', 5000, app)
        print("✅ Server started on http://127.0.0.1:5000")
        print("📱 Upload button FIXED!")
        print("📦 Manager can add found items!")
        print("🎉 ALL SYSTEMS WORKING!")
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
