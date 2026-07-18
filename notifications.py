import os
import logging
from twilio.rest import Client

logger = logging.getLogger(__name__)

class NotificationService:
    def __init__(self):
        self.account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
        self.auth_token = os.environ.get("TWILIO_AUTH_TOKEN")
        self.twilio_number = os.environ.get("TWILIO_PHONE_NUMBER")
        
        # Ensure 'YOUR_' placeholder is not considered valid
        if self.account_sid and "YOUR_" in self.account_sid:
            self.account_sid = None
            
        self.enabled = False
        
        if self.account_sid and self.auth_token and self.twilio_number:
            try:
                self.client = Client(self.account_sid, self.auth_token)
                self.enabled = True
                logger.info("Twilio NotificationService initialized successfully.")
            except Exception as e:
                logger.error(f"Failed to initialize Twilio client: {e}")
        else:
            logger.warning("Twilio credentials missing. NotificationService is disabled.")

    def send_whatsapp(self, to_phone_number: str, message: str) -> bool:
        """
        Send a WhatsApp message using Twilio.
        Ensure to_phone_number includes the country code (e.g., +919000000000).
        """
        if not self.enabled:
            logger.warning(f"Could not send WhatsApp to {to_phone_number}. Twilio is not configured.")
            return False
            
        # Ensure it has a + symbol, mostly for India (+91) but simple formatting for now
        if not to_phone_number.startswith('+'):
            to_phone_number = f"+91{to_phone_number}"
            
        try:
            message_obj = self.client.messages.create(
                body=message,
                from_=f"whatsapp:{self.twilio_number}",
                to=f"whatsapp:{to_phone_number}"
            )
            logger.info(f"WhatsApp sent successfully to {to_phone_number}. SID: {message_obj.sid}")
            return True
        except Exception as e:
            logger.error(f"Failed to send WhatsApp to {to_phone_number}. Error: {e}")
            return False

# Create a singleton instance to be used across the app
notification_service = NotificationService()
