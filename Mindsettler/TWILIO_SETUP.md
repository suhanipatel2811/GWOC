# Twilio SMS Setup Guide

## How to Get Real SMS OTP Working

### Step 1: Create Twilio Account
1. Go to https://www.twilio.com/
2. Sign up for a free account
3. Verify your email address

### Step 2: Get Your Credentials
1. Log in to Twilio Console: https://console.twilio.com/
2. From the dashboard, copy:
   - **Account SID**
   - **Auth Token**
3. **IMPORTANT**: Get a Twilio Phone Number:
   - Go to Phone Numbers → Manage → Buy a number
   - For trial accounts, you get one free phone number
   - Click "Buy a Number" and select a number from your country
   - **DO NOT use your personal phone number** - use the Twilio-provided number
4. Copy your **Twilio Phone Number** (format: +12345678901)
   - This is the number that will appear as the sender of SMS messages
   - Find it under: Phone Numbers → Manage → Active Numbers

### Step 3: Configure Your Application
1. Create a `.env` file in `Mindsettler/` directory (copy from `.env.example`)
2. Add your Twilio credentials:
   ```
   TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   TWILIO_AUTH_TOKEN=your_auth_token_here
   TWILIO_PHONE_NUMBER=+12345678901
   ```

### Step 4: Important Notes

#### Phone Number Format
- **MUST include country code** (e.g., `+911234567890` for India, `+12345678901` for USA)
- Users should register with phone numbers in international format: `+[country code][number]`

#### Free Trial Limitations
- Twilio free trial only sends SMS to **verified phone numbers**
- To verify a number:
  1. Go to Console → Phone Numbers → Verified Caller IDs
  2. Click "+" to add a new number
  3. Enter the phone number you want to test
  4. Twilio will send a verification code to that number
  5. Enter the code to verify

#### Production Use
- Upgrade Twilio account to send SMS to any number
- Free trial credits: ~$15-20 worth
- Cost: ~$0.0075 per SMS in USA, varies by country

### Step 5: Testing

1. Make sure server is running
2. Go to login page: http://127.0.0.1:8001/users/login/
3. Click "Phone Number" button
4. Enter a registered phone number with country code
5. Click "Send OTP"
6. Check your phone for the SMS!

### Fallback Mode
If Twilio credentials are not configured:
- OTP will be printed to console (terminal output)
- A warning message will show the OTP on screen
- This allows testing without SMS service

### Alternative SMS Services (if you prefer)
- **AWS SNS**: Good for large scale
- **Firebase**: Easy to set up
- **Fast2SMS**: India-specific
- **MSG91**: India-specific
- **Nexmo (Vonage)**: Global coverage

### Troubleshooting

**SMS not received?**
1. Check phone number format (must have country code with +)
2. Verify the number is verified in Twilio console (if using trial)
3. Check Twilio console logs for errors
4. Ensure .env file is loaded correctly
5. Check console output for error messages

**OTP shows in console but not SMS?**
- Twilio credentials not configured or incorrect
- Check .env file exists and has correct values
- Restart Django server after updating .env

**"Phone not registered" error?**
- User must register first with that phone number
- Phone number in database must match the format used for login
