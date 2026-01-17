# Render Deployment Checklist for MindSettler

## ✅ Files Created
- [x] `build.sh` - Build script for Render
- [x] `render.yaml` - Automated deployment configuration
- [x] `RENDER_DEPLOYMENT.md` - Complete deployment guide
- [x] Updated `settings.py` with production security settings

## 🚀 Quick Deployment Steps

### Step 1: Generate SECRET_KEY
Run this command to generate a secure secret key:
```bash
python -c "import secrets; print(secrets.token_urlsafe(50))"
```
**Save this key** - you'll need it in Step 4.

### Step 2: Commit & Push to GitHub
```bash
git add .
git commit -m "Add Render deployment configuration"
git push origin main
```

### Step 3: Deploy on Render
1. Go to https://render.com/dashboard
2. Sign up/login (use GitHub OAuth for easier access)
3. Click **"New +"** → **"Blueprint"**
4. Connect your GitHub repository
5. Render will detect `render.yaml` and show:
   - PostgreSQL Database: `mindsettler-db`
   - Web Service: `mindsettler`
6. Click **"Apply"**

### Step 4: Configure Environment Variables
After deployment starts, go to your web service settings and update:

**Required Variables:**
```
ALLOWED_HOSTS=your-app-name.onrender.com
SECRET_KEY=<paste-the-key-from-step-1>
```

**Optional Variables (add if you use these services):**
```
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
STRIPE_PUBLIC_KEY=pk_test_your_key
STRIPE_SECRET_KEY=sk_test_your_key
TWILIO_ACCOUNT_SID=your_sid
TWILIO_AUTH_TOKEN=your_token
TWILIO_PHONE_NUMBER=+1234567890
OPENAI_API_KEY=sk-your_key
```

### Step 5: Wait for Deployment
- First deployment takes 5-10 minutes
- Monitor progress in the **Logs** tab
- Look for "Build succeeded" and "Application started"

### Step 6: Test Your App
1. Click the URL at top of your service page (e.g., `https://mindsettler.onrender.com`)
2. Test key features:
   - Homepage loads
   - Static files (CSS/JS) work
   - User registration/login
   - Database operations

### Step 7: Create Admin User (Optional)
1. Go to your service → **Shell** tab
2. Run:
   ```bash
   cd Mindsettler
   python manage.py createsuperuser
   ```
3. Access admin at: `https://your-app.onrender.com/admin`

## 📝 Important Notes

### Free Tier Behavior
- Service sleeps after 15 min of inactivity
- First request after sleep takes 30-60 seconds to wake up
- Upgrade to paid plan ($7/month) for always-on service

### Environment Variable Order
After adding/changing environment variables:
1. Render automatically redeploys
2. Wait for new deployment to complete
3. Test the changes

### Updating Your App
Simply push to GitHub:
```bash
git add .
git commit -m "Your update message"
git push origin main
```
Render auto-deploys on push!

## 🔧 Troubleshooting

### Build Fails
- Check **Logs** tab for errors
- Verify `requirements.txt` has all dependencies
- Ensure `build.sh` has correct syntax

### Static Files Missing
- Check that `STATIC_ROOT` is set in settings
- Verify `collectstatic` runs in build.sh
- Check WhiteNoise is in `MIDDLEWARE`

### Database Errors
- Verify `DATABASE_URL` is set (auto-set by render.yaml)
- Check database and web service are in same region
- Ensure migrations ran successfully in build logs

### 500 Internal Server Error
- Check **Logs** tab for Python traceback
- Verify all required environment variables are set
- Check `DEBUG=False` is set
- Ensure `ALLOWED_HOSTS` includes your Render URL

## 📚 Resources
- Full Guide: See `RENDER_DEPLOYMENT.md`
- Render Docs: https://render.com/docs
- Django Deployment: https://docs.djangoproject.com/en/5.0/howto/deployment/

## 🎉 Your App Will Be Live At
```
https://your-app-name.onrender.com
```

Replace `your-app-name` with the actual name shown in Render dashboard.
