import os
import requests
import pandas as pd

SUPABASE_URL = os.environ.get('SUPABASE_URL', 'https://jxpsvsxyhfetqbdkszkz.supabase.co')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imp4cHN2c3h5aGZldHFiZGtzemt6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjQ2ODgwODMsImV4cCI6MjA4MDI2NDA4M30.7LOJ9XDUaxR6mFGpsWjnLk8TZmEsmDWrddcu-kVc3hM')

def load_students_df():
    try:
        url = f"{SUPABASE_URL}/rest/v1/students?select=*"
        headers = {
            'apikey': SUPABASE_KEY,
            'Authorization': f'Bearer {SUPABASE_KEY}',
            'Accept': 'application/json'
        }
        
        print(f"Connecting to: {url}")
        response = requests.get(url, headers=headers, timeout=15)
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Found {len(data)} records")
            
            if data and len(data) > 0:
                df = pd.DataFrame(data)
                # Convert column names to uppercase for consistency
                df.columns = df.columns.str.upper()
                print(f"Columns: {list(df.columns)}")
                return df
        else:
            print(f"Error response: {response.text}")
        
        return create_sample_data()
        
    except Exception as e:
        print(f"Supabase error: {e}")
        return create_sample_data()

def create_sample_data():
    print("Using sample data")
    sample_data = [
        {
            'RNO': '23G31A4790',
            'NAME': 'Mohan Patel',
            'DEPT': 'CSE',
            'YEAR': 1,
            'CURR_SEM': 1,
            'SEM1': 65,
            'INTERNAL_MARKS': 18,
            'TOTAL_DAYS_CURR': 90,
            'ATTENDED_DAYS_CURR': 65,
            'PREV_ATTENDANCE_PERC': 72,
            'BEHAVIOR_SCORE_10': 6
        },
        {
            'RNO': '23G31A1368',
            'NAME': 'Meera Rao',
            'DEPT': 'ECE',
            'YEAR': 1,
            'CURR_SEM': 2,
            'SEM1': 82,
            'SEM2': 85,
            'INTERNAL_MARKS': 25,
            'TOTAL_DAYS_CURR': 90,
            'ATTENDED_DAYS_CURR': 80,
            'PREV_ATTENDANCE_PERC': 88,
            'BEHAVIOR_SCORE_10': 8
        }
    ]
    
    return pd.DataFrame(sample_data)

def get_stats():
    try:
        df = load_students_df()
        departments = df['DEPT'].unique().tolist() if 'DEPT' in df.columns else ['CSE', 'ECE', 'MECH']
        years = df['YEAR'].unique().tolist() if 'YEAR' in df.columns else [1, 2, 3, 4]
        
        return {
            'total_students': len(df),
            'departments': sorted(departments),
            'years': sorted(years)
        }
    except:
        return {
            'total_students': 2,
            'departments': ['CSE', 'ECE', 'MECH', 'CIVIL', 'EEE'],
            'years': [1, 2, 3, 4]
        }