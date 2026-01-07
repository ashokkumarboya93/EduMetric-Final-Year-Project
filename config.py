import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Supabase configuration
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
DATABASE_URL = os.getenv('DATABASE_URL')

# Flask configuration
SECRET_KEY = os.getenv('SECRET_KEY', 'edumetric-secret-key-2024-final-year-project-secure')
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

# Email configuration
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USER = os.getenv('EMAIL_USER', 'ashokkumarboya999@gmail.com')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD', 'ashok123@')

# Backwards-compatible DB config placeholder (used by some test scripts)
DB_CONFIG = {
	'host': os.getenv('DB_HOST', 'localhost'),
	'database': os.getenv('DB_NAME', "ashokkumarboya93's Project"),
	'user': os.getenv('DB_USER', 'root'),
	'port': int(os.getenv('DB_PORT', '3306')) if os.getenv('DB_PORT') else 3306,
	'password': os.getenv('DB_PASSWORD', 'A$hok3117')
}