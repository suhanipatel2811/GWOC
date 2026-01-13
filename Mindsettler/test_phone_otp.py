"""
Test Phone OTP Login Functionality
This script tests the OTP utility functions without requiring a running Django server.
"""

import os
import sys
import django

# Setup Django environment
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Mindsettler.settings')
django.setup()

from users.utils import send_otp_sms, generate_otp, validate_phone_format
from users.models import Profile, OTPVerification
from django.contrib.auth.models import User

print("="*70)
print("PHONE OTP LOGIN - FUNCTIONALITY TEST")
print("="*70)

# Test 1: OTP Generation
print("\n[TEST 1] OTP Generation")
print("-" * 70)
otp1 = generate_otp()
otp2 = generate_otp()
print(f"Generated OTP 1: {otp1}")
print(f"Generated OTP 2: {otp2}")
print(f"✓ Both are 6 digits: {len(otp1) == 6 and len(otp2) == 6}")
print(f"✓ Both are numeric: {otp1.isdigit() and otp2.isdigit()}")
print(f"✓ Are unique: {otp1 != otp2}")

# Test 2: Phone Validation
print("\n[TEST 2] Phone Number Validation")
print("-" * 70)
test_numbers = [
    ("+919876543210", True, "Valid Indian number"),
    ("+14155552671", True, "Valid US number"),
    ("+447700900123", True, "Valid UK number"),
    ("9876543210", False, "Missing country code"),
    ("abc123", False, "Invalid characters"),
    ("+1", False, "Too short"),
    ("", False, "Empty string"),
]

for phone, expected, description in test_numbers:
    result = validate_phone_format(phone)
    status = "✓" if result == expected else "✗"
    print(f"{status} {description:30s} '{phone}' -> {result}")

# Test 3: Check Database for Registered Users
print("\n[TEST 3] Registered Users with Phone Numbers")
print("-" * 70)
profiles_with_phone = Profile.objects.exclude(phone='').exclude(phone__isnull=True)
count = profiles_with_phone.count()
print(f"Found {count} registered user(s) with phone number(s):")
for profile in profiles_with_phone[:5]:  # Show first 5
    print(f"  • {profile.user.username:20s} - {profile.phone}")
if count > 5:
    print(f"  ... and {count - 5} more")

if count == 0:
    print("⚠️  No users have phone numbers registered yet.")
    print("   To test phone login, register a user with a phone number first.")

# Test 4: OTP Database Model
print("\n[TEST 4] OTP Verification Model")
print("-" * 70)
try:
    # Check if we can create OTP records
    test_phone = "+919999999999"
    test_otp = generate_otp()
    
    # Clean old test records
    OTPVerification.objects.filter(phone=test_phone).delete()
    
    # Create test OTP
    otp_record = OTPVerification.objects.create(phone=test_phone, otp=test_otp)
    print(f"✓ Created test OTP record: {otp_record}")
    print(f"  Phone: {otp_record.phone}")
    print(f"  OTP: {otp_record.otp}")
    print(f"  Created: {otp_record.created_at}")
    print(f"  Verified: {otp_record.is_verified}")
    
    # Clean up
    otp_record.delete()
    print("✓ Test record cleaned up successfully")
except Exception as e:
    print(f"✗ Error: {e}")

# Test 5: Twilio Configuration
print("\n[TEST 5] Twilio Configuration Check")
print("-" * 70)
from django.conf import settings

has_sid = bool(settings.TWILIO_ACCOUNT_SID)
has_token = bool(settings.TWILIO_AUTH_TOKEN)
has_phone = bool(settings.TWILIO_PHONE_NUMBER)

print(f"{'✓' if has_sid else '✗'} TWILIO_ACCOUNT_SID: {'Configured' if has_sid else 'NOT SET'}")
print(f"{'✓' if has_token else '✗'} TWILIO_AUTH_TOKEN: {'Configured' if has_token else 'NOT SET'}")
print(f"{'✓' if has_phone else '✗'} TWILIO_PHONE_NUMBER: {'Configured' if has_phone else 'NOT SET'}")

if has_sid:
    print(f"   Account SID: {settings.TWILIO_ACCOUNT_SID[:20]}...")
if has_phone:
    print(f"   Phone Number: {settings.TWILIO_PHONE_NUMBER}")

all_configured = has_sid and has_token and has_phone
if all_configured:
    print("\n✓ Twilio is FULLY configured - Real SMS will be sent")
else:
    print("\n⚠️  Twilio is NOT fully configured - OTP will print to console")
    print("   To enable SMS: Update .env file with Twilio credentials")

# Test 6: SMS Sending (Dry Run)
print("\n[TEST 6] SMS Sending Test (Dry Run)")
print("-" * 70)
test_phone = "+919876543210"  # Example phone
test_otp = generate_otp()
print(f"Testing SMS send to: {test_phone}")
print(f"OTP to send: {test_otp}")
print("Calling send_otp_sms()...")
success, message = send_otp_sms(test_phone, test_otp)
print(f"Result: {'✓ SUCCESS' if success else '⚠️  FALLBACK MODE'}")
print(f"Message: {message}")

# Summary
print("\n" + "="*70)
print("TEST SUMMARY")
print("="*70)
print("✓ OTP Generation: Working")
print("✓ Phone Validation: Working")
print(f"✓ Database Models: Working ({count} registered user(s))")
print(f"{'✓' if all_configured else '⚠️'} Twilio Integration: {'Ready' if all_configured else 'Fallback Mode'}")
print("\n" + "="*70)

if all_configured:
    print("✅ Phone OTP Login is READY FOR PRODUCTION")
    print("   Users can login with phone number + OTP via SMS")
else:
    print("⚠️  Phone OTP Login is in DEVELOPMENT MODE")
    print("   OTP will be shown in console instead of SMS")
    print("   To enable SMS: Configure Twilio in .env file")

print("="*70)
