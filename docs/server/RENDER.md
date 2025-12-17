# Render.com Deployment Guide

## Quick Setup (5 minutes):

1. **Push to GitHub:**
   ```bash
   git add .
   git commit -m "Add Render deployment config"
   git push origin main
   ```

2. **Deploy on Render:**
   - Go to https://render.com
   - Sign up with GitHub (free)
   - Click "New Web Service"
   - Connect your GitHub repo
   - Render will auto-detect the Flask app
   - Deploy automatically!

3. **Your API will be live at:**
   `https://imagewave-license-api.onrender.com`

## Free Tier Limits:
- 500 hours/month (plenty for an API)
- Sleeps after 15 minutes of inactivity
- Wakes up automatically when accessed

## Environment Variables (auto-generated):
- `ADMIN_PASSWORD` - for admin API access
- `SECRET_KEY` - Flask security key
- `FLASK_ENV` - set to production

## Next Steps:
1. Update your ImageWave Converter app to use the production URL
2. Test the license validation
3. Ready for commercial use!