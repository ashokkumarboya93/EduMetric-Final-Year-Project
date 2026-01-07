# EduMetric Vercel Deployment Guide

## Prerequisites
1. GitHub account
2. Vercel account (free)
3. Your Supabase credentials

## Deployment Steps

### 1. Push to GitHub
```bash
git init
git add .
git commit -m "Initial commit - EduMetric app"
git branch -M main
git remote add origin https://github.com/yourusername/edumetric.git
git push -u origin main
```

### 2. Deploy on Vercel
1. Go to https://vercel.com
2. Sign in with GitHub
3. Click "New Project"
4. Import your GitHub repository
5. Configure environment variables:

### 3. Environment Variables (Add in Vercel Dashboard)
```
SUPABASE_URL = https://jxpsvsxyhfetqbdkszkz.supabase.co
SUPABASE_KEY = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imp4cHN2c3h5aGZldHFiZGtzemt6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjQ2ODgwODMsImV4cCI6MjA4MDI2NDA4M30.7LOJ9XDUaxR6mFGpsWjnLk8TZmEsmDWrddcu-kVc3hM
SECRET_KEY = edumetric-secret-key-2024-final-year-project-secure
DEBUG = False
EMAIL_USER = ashokkumarboya999@gmail.com
EMAIL_PASSWORD = ashok123@
```

### 4. Deploy
- Click "Deploy"
- Wait for build to complete
- Your app will be live at: https://your-project-name.vercel.app

## Files Created for Deployment
- `vercel.json` - Vercel configuration
- `requirements.txt` - Python dependencies
- `api/index.py` - Vercel entry point

## Features Preserved
✅ Student analytics and predictions
✅ Supabase database integration
✅ Department/Year analytics
✅ Email alerts
✅ All existing functionality

## Post-Deployment
1. Test all features on live URL
2. Update any hardcoded localhost URLs
3. Monitor Vercel logs for any issues