import os
import requests
import pandas as pd

SUPABASE_URL = os.environ.get('SUPABASE_URL', 'https://jxpsvsxyhfetqbdkszkz.supabase.co')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imp4cHN2c3h5aGZldHFiZGtzemt6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjQ2ODgwODMsImV4cCI6MjA4MDI2NDA4M30.7LOJ9XDUaxR6mFGpsWjnLk8TZmEsmDWrddcu-kVc3hM')

def load_students_df():
    try:
        headers = {
            'apikey': SUPABASE_KEY,
            'Authorization': f'Bearer {SUPABASE_KEY}',
            'Accept': 'application/json'
        }
        
        # Try different table names
        table_names = ['students', 'student_data', 'edumetric_students', 'analytics_data']
        
        for table_name in table_names:
            try:
                url = f"{SUPABASE_URL}/rest/v1/{table_name}?select=*&limit=100"
                response = requests.get(url, headers=headers, timeout=10)
                
                print(f"Trying table '{table_name}': Status {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    if data and len(data) > 0:
                        print(f"Found {len(data)} records in table '{table_name}'")
                        df = pd.DataFrame(data)
                        df.columns = df.columns.str.upper()
                        return df
                else:
                    print(f"Table '{table_name}' response: {response.text[:200]}")
            except Exception as e:
                print(f"Error with table '{table_name}': {e}")
                continue
        
        print("No valid tables found, using sample data")
        return create_sample_data()
        
    except Exception as e:
        print(f"Supabase connection error: {e}")
        return create_sample_data()

def create_sample_data():
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
        },
        {
            'RNO': '22G31A3167',
            'NAME': 'Raj Kumar',
            'DEPT': 'MECH',
            'YEAR': 2,
            'CURR_SEM': 3,
            'SEM1': 75,
            'SEM2': 78,
            'SEM3': 72,
            'INTERNAL_MARKS': 22,
            'TOTAL_DAYS_CURR': 90,
            'ATTENDED_DAYS_CURR': 75,
            'PREV_ATTENDANCE_PERC': 80,
            'BEHAVIOR_SCORE_10': 7
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
            'total_students': 3,
            'departments': ['CSE', 'ECE', 'MECH', 'CIVIL', 'EEE'],
            'years': [1, 2, 3, 4]
        }