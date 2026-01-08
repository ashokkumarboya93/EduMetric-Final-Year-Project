import os
import requests
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

print("Loading data from Supabase...")

try:
    url = f"{SUPABASE_URL}/rest/v1/students?select=*"
    headers = {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}',
        'Accept': 'application/json'
    }
    
    response = requests.get(url, headers=headers, timeout=20)
    
    if response.status_code == 200:
        data = response.json()
        df = pd.DataFrame(data)
        
        print(f"SUCCESS: Loaded {len(df)} records")
        print(f"Departments: {list(df['dept'].unique())}")
        print(f"Years: {list(df['year'].unique())}")
        print(f"Sample student: {df.iloc[0]['name']} ({df.iloc[0]['rno']})")
        
        print("\n" + "="*50)
        print("DATA LOADED SUCCESSFULLY!")
        print("="*50)
        print("\nTO RUN YOUR APP:")
        print("1. Open command prompt")
        print("2. Navigate to your folder:")
        print(f"   cd \"c:\\Users\\Master\\Documents\\Final Year\\Final Year\"")
        print("3. Run the app:")
        print("   python final_app.py")
        print("4. Open browser and go to:")
        print("   http://localhost:5000")
        print("5. Test connection at:")
        print("   http://localhost:5000/test")
        print("\nYour Supabase connection is working perfectly!")
        
    else:
        print(f"ERROR: {response.status_code} - {response.text}")
        
except Exception as e:
    print(f"ERROR: {e}")