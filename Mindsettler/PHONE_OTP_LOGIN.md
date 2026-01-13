# Phone Number OTP Login Feature

## Overview
MindSettler now supports **phone number-based authentication with OTP (One-Time Password) verification** for all registered users. This provides a secure, password-free login option using SMS verification.

## Features
✅ **Universal Access** - Available for ALL registered users (not just specific ones)
✅ **Secure OTP Delivery** - Real SMS sent via Twilio service
✅ **Multiple Login Options** - Users can login with:
  - Username + Password
  - Email + Password
  - Phone Number + OTP (SMS)
✅ **10-Minute Validity** - OTPs expire after 10 minutes for security
✅ **Automatic Fallback** - Shows OTP in console if Twilio is not configured (for development)

## How It Works

### User Flow
1. **Registration**: User provides phone number during account creation
2. **Login**: User enters phone number at login page
3. **OTP Generation**: System generates 6-digit OTP and sends via SMS
4. **Verification**: User enters OTP received on their phone
5. **Access Granted**: User is logged in successfully

### Technical Flow
```
User enters phone → Validate format → Check if registered → 
Generate OTP → Send via Twilio SMS → Store in database → 
User enters OTP → Verify against database → Login user
```

## Setup Instructions

### 1. Twilio Account Setup
1. Go to [https://www.twilio.com/](https://www.twilio.com/) and sign up
2. Get a phone number from Twilio Console
3. Copy your credentials:
   - **Account SID**
   - **Auth Token**
   - **Phone Number** (with country code)

### 2. Configure Environment Variables
Update your `.env` file in the Mindsettler directory:

```env
# Twilio SMS Configuration
TWILIO_ACCOUNT_SID=your_account_sid_here
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_PHONE_NUMBER=+1234567890
TWILIO_MESSAGING_SERVICE_SID=MGXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
# Optional (recommended): Use a Twilio Messaging Service to send SMS at scale.
# When set, `send_otp_sms` prefers this and will not send a `From` number.
```

**Important Notes:**
- Phone number must include country code (e.g., `+918735952744` for India)
- Keep credentials secret - never commit `.env` to version control
- For trial accounts, verify recipient numbers in Twilio Console

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

This will install the `twilio` package along with other dependencies.

### 4. Test Twilio Connection
Run the test script to verify your Twilio setup:
```bash
cd Mindsettler
python test_twilio.py
```

This will:
- Check if credentials are configured
- Test Twilio connection
- Optionally send a test SMS to your phone

## Usage

### For Users

#### Method 1: Direct Phone Login
1. Go to login page
2. Click "Phone Number" button
3. Enter phone number with country code (e.g., `+919876543210`)
4. Click "Send OTP"
5. Enter the 6-digit code received via SMS
6. Click "Verify & Login"

#### Method 2: Phone Entry in Main Login
1. Go to main login page
2. Enter phone number in the username/email field
3. Leave password field empty or enter any value
4. System detects phone number and redirects to OTP verification

### For Developers

#### Key Files Modified
- **`users/utils.py`** - New utility module with:
  - `send_otp_sms()` - Sends OTP via Twilio
  - `generate_otp()` - Generates 6-digit OTP
  - `validate_phone_format()` - Validates phone format

- **`users/views.py`** - Updated views:
  - `login_view()` - Detects phone numbers and triggers OTP flow
  - `send_otp_view()` - Generates and sends OTP via Twilio
  - `verify_otp_view()` - Verifies OTP and logs user in

- **`users/models.py`** - OTPVerification model:
  - Stores temporary OTP codes
  - Tracks verification status
  - Automatic cleanup of old OTPs

#### API Endpoints
- **POST `/users/send-otp/`** - Generate and send OTP
- **POST `/users/verify-otp/`** - Verify OTP and login
- **GET `/users/loginph/`** - Phone login page

## Security Features

### OTP Generation
- **6-digit random code** (100,000 to 999,999)
- **Cryptographically secure** random generation
- **Single-use** - OTP is deleted after successful verification

### Validation
- **Format validation** - Ensures valid international phone format
- **Registration check** - Only registered phone numbers can receive OTP
- **Time-based expiry** - OTPs valid for only 10 minutes
- **Old OTP cleanup** - Previous OTPs are deleted when new one is generated

### Session Management
- Phone number stored in session during OTP flow
- Session cleared after successful login
- Automatic timeout protection

## Troubleshooting

### OTP Not Received
1. **Check Twilio credentials** in `.env` file
2. **Verify phone number format** includes country code (e.g., `+91` for India)
3. **Trial account limitation** - Verify recipient number in Twilio Console
4. **Check Twilio balance** - Ensure you have credits
5. **Look in console** - During development, OTP is printed to console

### Common Errors

#### "Phone number not registered"
- User must create account first with that phone number
- Phone must be entered during registration

#### "Invalid or expired OTP"
- OTP is only valid for 10 minutes
- Request a new OTP if expired
- Ensure correct 6-digit code

#### "Twilio not configured"
- Check `.env` file has all three Twilio variables
- Restart Django server after updating `.env`
- OTP will be printed to console in development mode

### Using a Twilio Messaging Service

- Create a Messaging Service in the Twilio Console and add a phone number (or multiple numbers) to the service.
- Copy the Messaging Service SID (starts with `MG...`) into `TWILIO_MESSAGING_SERVICE_SID` in your `.env`.
- When configured, the app will send messages via the Messaging Service which avoids the "From equals To" restriction and improves deliverability.

### Development Mode
If Twilio is not configured, the system automatically falls back to console output:
- OTP is printed to terminal
- User sees warning message with the OTP
- Perfect for local testing without Twilio account

## Testing

### Manual Testing Steps
1. **Register a new user** with phone number
2. **Try phone login** from login page
3. **Check SMS** on your phone for OTP
4. **Enter OTP** and verify successful login
5. **Test expiry** - Wait 10 minutes and try old OTP (should fail)
6. **Test invalid OTP** - Enter wrong code (should fail)

### Automated Testing
```python
# Example test case
from django.test import TestCase
from users.models import Profile, OTPVerification

class PhoneLoginTest(TestCase):
    def test_otp_generation(self):
        # Test OTP is generated for registered phone
        # Test OTP is sent via Twilio
        # Test OTP verification
        pass
```

## Best Practices

### For Production
1. **Use real Twilio account** with proper credits
2. **Enable HTTPS** for secure transmission
3. **Rate limiting** - Limit OTP requests per phone/IP
4. **Monitor Twilio usage** - Track SMS costs
5. **Backup verification** - Consider email backup if SMS fails

### For Security
1. **Never log OTP** in production logs
2. **Use strong random generation** (already implemented)
3. **Short validity window** (10 minutes is good)
4. **One-time use only** (already implemented)
5. **HTTPS only** in production

## Cost Considerations

### Twilio Pricing (approximate)
- **SMS to India**: ~$0.0054 per message
- **SMS to US**: ~$0.0079 per message
- **Trial account**: Free credits for testing
- **Estimate**: 1000 logins ≈ $5-8 USD

### Optimization Tips
- Cache OTP for retry requests (same OTP for 2 minutes)
- Implement rate limiting to prevent abuse
- Monitor failed attempts
- Consider email OTP as free alternative

## Future Enhancements

### Possible Improvements
- [ ] WhatsApp OTP delivery (free via Twilio)
- [ ] Email OTP as backup option
- [ ] Remember device for 30 days
- [ ] SMS templates with branding
- [ ] Multi-language SMS support
- [ ] Phone number verification on registration

## Support

### Resources
- [Twilio Documentation](https://www.twilio.com/docs/sms)
- [Django Authentication](https://docs.djangoproject.com/en/stable/topics/auth/)
- MindSettler Documentation (this file)

### Contact
For issues or questions:
1. Check terminal console for OTP (development)
2. Review Twilio Console logs
3. Check Django error logs
4. Contact development team

---

**Version**: 1.0  
**Last Updated**: January 2026  
**Status**: ✅ Production Ready
