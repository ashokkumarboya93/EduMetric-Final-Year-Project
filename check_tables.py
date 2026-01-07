from supabase import create_client
from config import SUPABASE_URL, SUPABASE_KEY
import requests

print("Checking Supabase tables...")

try:
    # Method 1: Try to list tables using REST API
    url = f"{SUPABASE_URL}/rest/v1/"
    headers = {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}',
        'Accept': 'application/json'
    }
    
    print(f"Supabase URL: {SUPABASE_URL}")
    print(f"API Key: {SUPABASE_KEY[:20]}...")
    
    # Try to access the students table directly
    students_url = f"{SUPABASE_URL}/rest/v1/students?select=*&limit=1"
    response = requests.get(students_url, headers=headers, timeout=10)
    
    print(f"Students table response status: {response.status_code}")
    print(f"Response: {response.text[:200]}...")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Found {len(data)} records in students table")
        if data:
            print("Sample record keys:", list(data[0].keys()))
    else:
        print("Students table not accessible")
        
    # Try other common table names
    for table_name in ['student', 'Student', 'STUDENTS', 'public.students']:
        try:
            test_url = f"{SUPABASE_URL}/rest/v1/{table_name}?select=*&limit=1"
            test_response = requests.get(test_url, headers=headers, timeout=5)
            if test_response.status_code == 200:
                print(f"Found table: {table_name}")
                break
        except:
            continue
            
except Exception as e:
    print(f"Error: {e}")

# Method 2: Try using Supabase client
try:
    print("\nTrying Supabase client...")
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    # Try to query students table
    result = supabase.table('students').select('*').limit(1).execute()
    print(f"Client result: {result}")
    
except Exception as e:
    print(f"Client error: {e}")