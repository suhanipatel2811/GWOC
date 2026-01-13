"""
Test Twilio SMS Configuration
Run this to verify your Twilio setup is working correctly
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER')

print("="*60)
print("TWILIO CONFIGURATION CHECK")
print("="*60)

print(f"\n1. Account SID: {TWILIO_ACCOUNT_SID[:20]}..." if TWILIO_ACCOUNT_SID else "❌ NOT SET")
print(f"2. Auth Token: {TWILIO_AUTH_TOKEN[:20]}..." if TWILIO_AUTH_TOKEN else "❌ NOT SET")
print(f"3. Phone Number: {TWILIO_PHONE_NUMBER}" if TWILIO_PHONE_NUMBER else "❌ NOT SET")

if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN and TWILIO_PHONE_NUMBER:
    print("\n✅ All Twilio credentials are configured!")
    print("\n" + "="*60)
    print("TESTING TWILIO CONNECTION...")
    print("="*60)
    
    try:
        from twilio.rest import Client
        
        # Initialize client
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        
        # Test by fetching account info
        account = client.api.accounts(TWILIO_ACCOUNT_SID).fetch()
        print(f"\n✅ Connection successful!")
        print(f"   Account Status: {account.status}")
        print(f"   Account Type: {account.type}")
        
        # Check phone number
        print(f"\n📱 Your Twilio Phone Number: {TWILIO_PHONE_NUMBER}")
        
        # Now ask user if they want to send a test SMS
        print("\n" + "="*60)
        print("SEND TEST SMS")
        print("="*60)
        
        test_phone = input("\nEnter YOUR phone number to receive test SMS (with country code, e.g., +919876543210): ").strip()
        
        if test_phone:
            print(f"\n📤 Sending test SMS to {test_phone}...")
            
            message = client.messages.create(
                body='Test SMS from MindSettler! Your OTP system is working correctly. 🎉',
                from_=TWILIO_PHONE_NUMBER,
                to=test_phone
            )
            
            print(f"\n✅ SMS SENT SUCCESSFULLY!")
            print(f"   Message SID: {message.sid}")
            print(f"   Status: {message.status}")
            print(f"   To: {message.to}")
            print(f"   From: {message.from_}")
            print(f"\n🎉 Check your phone! You should receive the SMS shortly.")
            
        else:
            print("\n⚠️ No phone number entered. Skipping test SMS.")
            
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        print("\nPossible issues:")
        print("1. Check if credentials are correct in .env file")
        print("2. Make sure your Twilio account is active")
        print("3. For trial accounts, verify the recipient phone number in Twilio console")
        print("4. Check if you have sufficient credits")
        
else:
    print("\n❌ Twilio credentials are NOT properly configured!")
    print("\nPlease update your .env file with:")
    print("TWILIO_ACCOUNT_SID=your_account_sid")
    print("TWILIO_AUTH_TOKEN=your_auth_token")
    print("TWILIO_PHONE_NUMBER=+1234567890")

print("\n" + "="*60)
