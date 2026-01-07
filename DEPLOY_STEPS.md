# VERCEL DEPLOYMENT - STEP BY STEP

## 1. PUSH TO GITHUB
```bash
git init
git add .
git commit -m "EduMetric app for Vercel"
git remote add origin https://github.com/YOUR_USERNAME/edumetric.git
git push -u origin main
```

## 2. DEPLOY ON VERCEL
1. Go to https://vercel.com
2. Sign in with GitHub
3. Click "New Project"
4. Select your GitHub repository
5. Click "Deploy"

## 3. ADD ENVIRONMENT VARIABLES
After deployment, go to:
Project → Settings → Environment Variables

Add these ONE BY ONE:

**Name:** SUPABASE_URL
**Value:** https://jxpsvsxyhfetqbdkszkz.supabase.co

**Name:** SUPABASE_KEY  
**Value:** eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imp4cHN2c3h5aGZldHFiZGtzemt6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjQ2ODgwODMsImV4cCI6MjA4MDI2NDA4M30.7LOJ9XDUaxR6mFGpsWjnLk8TZmEsmDWrddcu-kVc3hM

**Name:** SECRET_KEY
**Value:** d2a9e8b1c3f7a0e9d8c6b5a4d3e2f1a0

**Name:** DEBUG
**Value:** False

**Name:** EMAIL_USER
**Value:** ashokkumarboya93@gmail.com

**Name:** EMAIL_PASSWORD
**Value:** hctaatovfwfxfmrm

## 4. REDEPLOY
Click "Redeploy" after adding environment variables

## 5. TEST
Your app will be live at: https://your-project-name.vercel.app

## TROUBLESHOOTING
If deployment fails:
1. Check Vercel logs
2. Ensure all files are committed to GitHub
3. Verify environment variables are set correctly