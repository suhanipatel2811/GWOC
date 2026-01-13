"""
Utility functions for user authentication and OTP handling.
"""
import os
from django.conf import settings


def send_otp_sms(phone_number, otp_code):
    """
    Send OTP via SMS using Twilio.
    
    Args:
        phone_number (str): The recipient's phone number (with country code, e.g., +919876543210)
        otp_code (str): The 6-digit OTP code to send
        
    Returns:
        tuple: (success: bool, message: str)
    """
    # Get Twilio credentials from settings
    account_sid = settings.TWILIO_ACCOUNT_SID
    auth_token = settings.TWILIO_AUTH_TOKEN
    twilio_phone = settings.TWILIO_PHONE_NUMBER
    messaging_service_sid = getattr(settings, 'TWILIO_MESSAGING_SERVICE_SID', '')
    
    # Check if Twilio is properly configured
    # At minimum we need account SID and auth token. We can use either a
    # `TWILIO_MESSAGING_SERVICE_SID` (preferred) or a `TWILIO_PHONE_NUMBER`.
    if not all([account_sid, auth_token]) or not (messaging_service_sid or twilio_phone):
        # Fallback: print to console for development
        print(f"\n{'='*60}")
        print(f"🔐 OTP for {phone_number}: {otp_code}")
        print(f"{'='*60}\n")
        return (False, f"Twilio not configured. OTP for testing: {otp_code}")

    # Prevent sending where From and To are identical (Twilio error 21266)
    # Only applicable when using a fixed Twilio phone number (not Messaging Service)
    if twilio_phone and phone_number and twilio_phone == phone_number and not messaging_service_sid:
        msg = (
            "Configured TWILIO_PHONE_NUMBER is the same as the recipient number. "
            "Set `TWILIO_PHONE_NUMBER` to a valid Twilio number (or use a Messaging Service SID). "
            "See: https://www.twilio.com/docs/errors/21266"
        )
        print(f"\n{'='*60}")
        print(f"❌ SMS configuration error: {msg}")
        print(f"🔐 OTP for {phone_number}: {otp_code}")
        print(f"{'='*60}\n")
        return (False, f"{msg}. OTP for testing: {otp_code}")
    
    try:
        from twilio.rest import Client
        
        # Initialize Twilio client
        client = Client(account_sid, auth_token)
        
        # Compose SMS message
        message_body = f"Your MindSettler verification code is: {otp_code}. Valid for 10 minutes. Do not share this code with anyone."
        
        # Send SMS. Prefer Messaging Service SID if configured (it avoids
        # the 'From equals To' restriction and supports scaling/spam-handling).
        if messaging_service_sid:
            message = client.messages.create(
                body=message_body,
                messaging_service_sid=messaging_service_sid,
                to=phone_number
            )
        else:
            message = client.messages.create(
                body=message_body,
                from_=twilio_phone,
                to=phone_number
            )
        
        # Check if message was sent successfully
        if message.sid:
            print(f"✅ SMS sent successfully to {phone_number}. SID: {message.sid}")
            return (True, f"OTP sent successfully to {phone_number}")
        else:
            return (False, "Failed to send SMS")
            
    except ImportError:
        # Twilio library not installed
        print(f"\n{'='*60}")
        print(f"⚠️ Twilio library not installed")
        print(f"🔐 OTP for {phone_number}: {otp_code}")
        print(f"{'='*60}\n")
        return (False, f"Twilio library not installed. OTP for testing: {otp_code}")
        
    except Exception as e:
        # Any other error (invalid credentials, network issues, etc.)
        error_msg = str(e)

        # Detect common Twilio errors and give actionable guidance
        user_msg = None
        try:
            lower = error_msg.lower()
        except Exception:
            lower = ''

        if '21659' in error_msg or 'from' in lower and 'not a twilio' in lower:
            user_msg = (
                "The 'From' number in your Twilio config is invalid for sending SMS. "
                "Ensure `TWILIO_PHONE_NUMBER` is a Twilio-provisioned number (with country code), "
                "or configure `TWILIO_MESSAGING_SERVICE_SID` and add a Twilio number to that service. "
                "See: https://www.twilio.com/docs/errors/21659"
            )
        elif '21266' in error_msg or 'to' in lower and 'from' in lower and 'cannot be the same' in lower:
            user_msg = (
                "The recipient and sender numbers are the same. Configure a Twilio number or a Messaging Service. "
                "See: https://www.twilio.com/docs/errors/21266"
            )

        print(f"\n{'='*60}")
        print(f"❌ Error sending SMS: {error_msg}")
        print(f"🔐 OTP for {phone_number}: {otp_code}")
        print(f"{'='*60}\n")

        if user_msg:
            return (False, f"{user_msg} OTP for testing: {otp_code}")

        return (False, f"Error sending SMS: {error_msg}. OTP for testing: {otp_code}")


def generate_otp():
    """
    Generate a random 6-digit OTP code.
    
    Returns:
        str: A 6-digit OTP code
    """
    import random
    return str(random.randint(100000, 999999))


def validate_phone_format(phone_number):
    """
    Validate phone number format.
    
    Args:
        phone_number (str): Phone number to validate
        
    Returns:
        bool: True if valid format, False otherwise
    """
    import re
    # Remove spaces and dashes
    clean_phone = phone_number.replace(' ', '').replace('-', '')
    
    # Must start with + for international format
    # Should have 7-15 digits after country code
    if re.match(r'^\+[1-9]\d{6,14}$', clean_phone):
        return True
    return False
