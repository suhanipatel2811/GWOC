# Setup Instructions After Code Refinements

## 🔧 Required Actions

### 1. **Create .env File**
Copy `.env.example` to `.env` and fill in your actual credentials:

```bash
cp .env.example .env
```

**IMPORTANT**: Generate a new SECRET_KEY:
```python
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 2. **Create Database Migrations**
The new indexes need to be applied:

```bash
python manage.py makemigrations
python manage.py migrate
```

### 3. **Install Updated Dependencies**
```bash
pip install -r requirements.txt
```

### 4. **Create Logs Directory** (Already created)
Logs directory exists at `logs/` with `.gitignore`

### 5. **Environment Variables Setup**
Ensure these are set in your `.env` file:

- ✅ `SECRET_KEY` - Generate new one (see step 1)
- ✅ `DEBUG` - Set to `False` for production
- ✅ `ALLOWED_HOSTS` - Add your domain(s)
- ✅ `EMAIL_HOST_USER` - Your email
- ✅ `EMAIL_HOST_PASSWORD` - App password
- ✅ `OPENAI_API_KEY` - Your OpenAI key
- ✅ `TWILIO_*` - Twilio credentials

## 🎯 What Was Fixed

### Critical Security (Priority 1)
- ✅ SECRET_KEY moved to environment variable
- ✅ DEBUG configurable via environment
- ✅ ALLOWED_HOSTS configurable
- ✅ Hardcoded email removed

### Performance & Scalability
- ✅ Database indexes added (OTPVerification, Appointment)
- ✅ Comprehensive logging configured
- ✅ Rate limiting for OTP (3 attempts per 10 minutes)

### Code Quality
- ✅ Print statements replaced with logging
- ✅ Utility functions extracted for Google Calendar
- ✅ OTP cleanup function added
- ✅ Comprehensive requirements.txt with versions

## 📋 Next Steps (Recommended)

### Medium Priority
1. Run migrations to apply new indexes
2. Test OTP rate limiting functionality
3. Review logs regularly in `logs/` directory
4. Consider adding Celery for async tasks
5. Add unit tests

### Optional Enhancements
- Set up Redis for caching
- Configure Sentry for error monitoring
- Use cloud storage (AWS S3) for media files
- Add API rate limiting middleware
- Implement database backups

## 🔄 Migration Commands

```bash
# Create migrations for new indexes
python manage.py makemigrations users appointment

# Apply migrations
python manage.py migrate

# Optional: Create superuser if needed
python manage.py createsuperuser
```

## 🧪 Testing Changes

1. **Test OTP Rate Limiting**:
   - Try sending OTP 4 times within 10 minutes
   - Should see rate limit error on 4th attempt

2. **Check Logging**:
   - Run the app and check `logs/mindsettler.log`
   - Errors should appear in `logs/errors.log`

3. **Verify Environment Variables**:
   - Ensure app fails to start without SECRET_KEY
   - Check DEBUG mode works correctly

## ⚠️ Important Notes

- Never commit `.env` file to version control
- Always use `.env.example` as template
- Rotate SECRET_KEY before production deployment
- Enable HTTPS in production
- Set DEBUG=False in production
- Configure proper ALLOWED_HOSTS for production domain
