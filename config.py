import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Supabase configuration
SUPABASE_URL = os.getenv('SUPABASE_URL', 'https://jxpsvsxyhfetqbdkszkz.supabase.co')
SUPABASE_KEY = os.getenv('SUPABASE_KEY', '')

# Flask configuration
SECRET_KEY = os.getenv('SECRET_KEY', 'edumetric-secret-key-2024-final-year-project-secure')
DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'

# Email configuration
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USER = os.getenv('EMAIL_USER', 'ashokkumarboya999@gmail.com')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD', '')