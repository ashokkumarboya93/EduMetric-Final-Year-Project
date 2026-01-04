import os

# Flask configuration for Vercel
SECRET_KEY = os.getenv('SECRET_KEY', 'edumetric-vercel-deployment-key')
DEBUG = False

# Email configuration (optional for Vercel)
EMAIL_USER = os.getenv('EMAIL_USER', 'demo@example.com')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD', 'demo-password')