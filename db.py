import os
import requests
import pandas as pd
from config import SUPABASE_URL, SUPABASE_KEY

def get_supabase_headers():
    """Get headers for Supabase API requests"""
    return {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}',
        'Content-Type': 'application/json',
        'Prefer': 'return=representation'
    }

def load_students_df():
    """Load all students from Supabase via REST API"""
    try:
        url = f"{SUPABASE_URL}/rest/v1/students?select=*"
        headers = get_supabase_headers()
        
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            if data:
                df = pd.DataFrame(data)
                # Convert column names to uppercase for consistency
                df.columns = df.columns.str.upper()
                return df
            else:
                print("[WARN] No data returned from Supabase")
                return pd.DataFrame()
        else:
            print(f"[ERR] Supabase API error: {response.status_code} - {response.text}")
            return pd.DataFrame()
            
    except Exception as e:
        print(f"[ERR] Failed to load students: {e}")
        return pd.DataFrame()

def get_student_by_rno(rno):
    """Get a single student by register number"""
    try:
        url = f"{SUPABASE_URL}/rest/v1/students?rno=eq.{rno}&select=*"
        headers = get_supabase_headers()
        
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            if data:
                student = data[0]
                # Convert keys to uppercase
                return {k.upper(): v for k, v in student.items()}
        
        return None
        
    except Exception as e:
        print(f"[ERR] Failed to get student {rno}: {e}")
        return None

def insert_student(student_data):
    """Insert a new student record"""
    try:
        url = f"{SUPABASE_URL}/rest/v1/students"
        headers = get_supabase_headers()
        
        # Convert keys to lowercase for Supabase
        payload = {k.lower(): v for k, v in student_data.items()}
        
        response = requests.post(url, headers=headers, json=payload, timeout=15)
        
        return response.status_code in [200, 201]
        
    except Exception as e:
        print(f"[ERR] Failed to insert student: {e}")
        return False

def update_student(rno, student_data):
    """Update an existing student record"""
    try:
        url = f"{SUPABASE_URL}/rest/v1/students?rno=eq.{rno}"
        headers = get_supabase_headers()
        
        # Convert keys to lowercase for Supabase
        payload = {k.lower(): v for k, v in student_data.items()}
        
        response = requests.patch(url, headers=headers, json=payload, timeout=15)
        
        return response.status_code == 200
        
    except Exception as e:
        print(f"[ERR] Failed to update student {rno}: {e}")
        return False

def delete_student(rno):
    """Delete a student record"""
    try:
        url = f"{SUPABASE_URL}/rest/v1/students?rno=eq.{rno}"
        headers = get_supabase_headers()
        
        response = requests.delete(url, headers=headers, timeout=15)
        
        return response.status_code == 200
        
    except Exception as e:
        print(f"[ERR] Failed to delete student {rno}: {e}")
        return False

def get_stats():
    """Get basic statistics about the data"""
    try:
        df = load_students_df()
        
        if df.empty:
            return {
                'total_students': 0,
                'departments': [],
                'years': [],
                'sample_rnos': []
            }
        
        # Get unique departments and years
        departments = sorted(df['DEPT'].dropna().unique().tolist())
        years = sorted([int(y) for y in df['YEAR'].dropna().unique() if str(y).isdigit()])
        sample_rnos = df['RNO'].head(5).tolist()
        
        return {
            'total_students': len(df),
            'departments': departments,
            'years': years,
            'sample_rnos': sample_rnos
        }
        
    except Exception as e:
        print(f"[ERR] Failed to get stats: {e}")
        return {
            'total_students': 0,
            'departments': [],
            'years': [],
            'sample_rnos': []
        }

def test_connection():
    """Test the Supabase connection"""
    try:
        url = f"{SUPABASE_URL}/rest/v1/students?select=count&limit=1"
        headers = get_supabase_headers()
        
        response = requests.get(url, headers=headers, timeout=10)
        
        return response.status_code == 200
        
    except Exception as e:
        print(f"[ERR] Connection test failed: {e}")
        return False

def raw_rest_check(limit=1):
    """Raw REST API check for diagnostics"""
    try:
        url = f"{SUPABASE_URL}/rest/v1/students?select=*&limit={limit}"
        headers = get_supabase_headers()
        
        response = requests.get(url, headers=headers, timeout=15)
        
        return {
            'status_code': response.status_code,
            'ok': response.ok,
            'text': response.text[:500],
            'headers': dict(response.headers)
        }
        
    except Exception as e:
        return {'error': str(e)}