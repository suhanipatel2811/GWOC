# Deploy MindSettler to Render

## Prerequisites
- GitHub account with your project repository
- Render account (sign up at https://render.com)

## Step-by-Step Deployment

### 1. Commit and Push Changes
```bash
cd D:\projects\GWOC-1
git add .
git commit -m "Add Render deployment configuration"
git push origin main
```

### 2. Create Render Account
1. Go to https://render.com
2. Sign up using your GitHub account
3. Grant Render access to your repositories

### 3. Create PostgreSQL Database
1. In Render Dashboard, click **"New +"** → **"PostgreSQL"**
2. Fill in details:
   - **Name**: `mindsettler-db`
   - **Database**: `mindsettler`
   - **User**: `mindsettler`
   - **Region**: Choose closest to you
   - **Plan**: Free
3. Click **"Create Database"**
4. Wait for database to be created (takes ~2 minutes)
5. **Copy the Internal Database URL** (you'll need this)

### 4. Create Web Service
1. Click **"New +"** → **"Web Service"**
2. Connect your GitHub repository: `suhanipatel2811/GWOC`
3. Fill in details:
   - **Name**: `mindsettler`
   - **Region**: Same as database
   - **Branch**: `main`
   - **Root Directory**: Leave blank
   - **Runtime**: `Python 3`
   - **Build Command**: `./build.sh`
   - **Start Command**: `cd Mindsettler && gunicorn Mindsettler.wsgi:application`
   - **Plan**: Free

### 5. Configure Environment Variables
In the **Environment** section, add these variables:

**Required:**
```
SECRET_KEY=<generate-a-random-secret-key>
DEBUG=False
ALLOWED_HOSTS=your-app-name.onrender.com
DATABASE_URL=<paste-internal-database-url-from-step-3>
```

**Optional (add as needed):**
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

### 6. Deploy
1. Click **"Create Web Service"**
2. Render will automatically:
   - Clone your repository
   - Install dependencies
   - Run migrations
   - Collect static files
   - Start your application
3. Wait 5-10 minutes for first deployment

### 7. Access Your App
Once deployed, your app will be available at:
```
https://your-app-name.onrender.com
```

## Generate SECRET_KEY
Run this in Python to generate a secure key:
```python
import secrets
print(secrets.token_urlsafe(50))
```

## Troubleshooting

### Check Logs
- In Render Dashboard → Your Service → **Logs** tab
- Look for errors during build or runtime

### Common Issues

**Build fails:**
- Check `build.sh` has execute permissions
- Verify all dependencies in `requirements.txt`

**Static files not loading:**
- Ensure `STATIC_ROOT` is set correctly
- Run `collectstatic` is in `build.sh`

**Database connection errors:**
- Verify `DATABASE_URL` is set correctly
- Check database is in same region as web service

**Application crashes:**
- Check logs for Python errors
- Verify all environment variables are set
- Ensure migrations ran successfully

### Manual Commands
If needed, you can run commands via Render Shell:
1. Go to your service → **Shell** tab
2. Run Django commands:
```bash
cd Mindsettler
python manage.py migrate
python manage.py createsuperuser
python manage.py collectstatic --noinput
```

## Important Notes

### Free Tier Limitations
- Service spins down after 15 minutes of inactivity
- First request after spin-down takes 30-60 seconds
- Database limited to 90 days for free tier
- Upgrade to paid plan for always-on service

### Database Backups
Free tier databases are automatically backed up daily
Download backups from Render Dashboard

### Custom Domain
To use your own domain:
1. Go to service Settings → Custom Domain
2. Add your domain
3. Update DNS records as shown
4. Add domain to `ALLOWED_HOSTS`

## Updating Your App
Push changes to GitHub:
```bash
git add .
git commit -m "Update description"
git push origin main
```

Render will automatically rebuild and redeploy!

## Support
- Render Docs: https://render.com/docs
- Django Deployment: https://docs.djangoproject.com/en/5.0/howto/deployment/
