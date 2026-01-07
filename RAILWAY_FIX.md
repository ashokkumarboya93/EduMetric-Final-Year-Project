# RAILWAY DEPLOYMENT FIX

## CRITICAL: Update Environment Variables in Railway Dashboard

The logs show wrong Supabase URL. In Railway dashboard → Variables, set:

```
SUPABASE_URL = https://jxpsvsxyhfetqbdkszkz.supabase.co
SUPABASE_KEY = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imp4cHN2c3h5aGZldHFiZGtzemt6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjQ2ODgwODMsImV4cCI6MjA4MDI2NDA4M30.7LOJ9XDUaxR6mFGpsWjnLk8TZmEsmDWrddcu-kVc3hM
SECRET_KEY = d2a9e8b1c3f7a0e9d8c6b5a4d3e2f1a0
DEBUG = False
EMAIL_USER = ashokkumarboya93@gmail.com
EMAIL_PASSWORD = hctaatovfwfxfmrm
```

## STEPS:
1. Push updated code: `git add . && git commit -m "Fix versions" && git push`
2. In Railway dashboard → Variables → Delete all existing variables
3. Add the correct variables above
4. Redeploy

## Check Supabase Table:
Go to Supabase dashboard and ensure:
- Table name is exactly `students` (not `Students`)
- Table is in `public` schema
- RLS is disabled or properly configured