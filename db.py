from supabase import create_client, Client
import pandas as pd
from config import SUPABASE_URL, SUPABASE_KEY
import requests

def get_supabase_client():
    """Get Supabase client"""
    try:
        if not SUPABASE_KEY or SUPABASE_KEY == 'PUT_YOUR_ACTUAL_SUPABASE_KEY_HERE':
            print("[WARN] Using sample data - Please set your actual Supabase API key in .env file")
            return None
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        # Test connection
        supabase.table('students').select('*').limit(1).execute()
        return supabase
    except Exception as e:
        print(f"[WARN] Supabase connection failed, using sample data: {e}")
        return None

def load_students_df():
    """Load all students from Supabase"""
    try:
        supabase = get_supabase_client()
        if supabase is None:
            # Return sample data for testing
            return get_sample_data()
        
        response = supabase.table('students').select('*').execute()
        if response.data:
            df = pd.DataFrame(response.data)
            return df
        return get_sample_data()
    except Exception as e:
        print(f"[ERR] Load students: {e}")
        return get_sample_data()

def get_sample_data():
    """Return sample student data for testing"""
    sample_data = {
        'RNO': ['22G31A3167', '22G31A3168', '22G31A3169'],
        'NAME': ['John Doe', 'Jane Smith', 'Bob Johnson'],
        'EMAIL': ['john@example.com', 'jane@example.com', 'bob@example.com'],
        'DEPT': ['CSE', 'CSE', 'ECE'],
        'YEAR': [3, 3, 3],
        'CURR_SEM': [5, 5, 5],
        'SEM1': [85, 90, 78],
        'SEM2': [88, 92, 80],
        'SEM3': [82, 89, 75],
        'SEM4': [86, 91, 79],
        'INTERNAL_MARKS': [25, 28, 22],
        'TOTAL_DAYS_CURR': [90, 90, 90],
        'ATTENDED_DAYS_CURR': [85, 88, 70],
        'PREV_ATTENDANCE_PERC': [90, 95, 75],
        'BEHAVIOR_SCORE_10': [8, 9, 7]
    }
    return pd.DataFrame(sample_data)

def get_student_by_rno(rno):
    """Get student by roll number from Supabase"""
    try:
        supabase = get_supabase_client()
        if supabase is None:
            # Return sample student for testing
            df = get_sample_data()
            student_row = df[df['RNO'] == rno]
            if not student_row.empty:
                return student_row.iloc[0].to_dict()
            return None
        
        response = supabase.table('students').select('*').eq('RNO', rno).execute()
        if response.data:
            return response.data[0]
        return None
    except Exception as e:
        print(f"[ERR] Get student: {e}")
        return None

def insert_student(student_data):
    """Insert new student into Supabase"""
    try:
        supabase = get_supabase_client()
        if supabase is None:
            return False
        
        response = supabase.table('students').insert(student_data).execute()
        return len(response.data) > 0
    except Exception as e:
        print(f"[ERR] Insert student: {e}")
        return False

def update_student(rno, update_data):
    """Update student in Supabase"""
    try:
        supabase = get_supabase_client()
        if supabase is None:
            return False
        
        response = supabase.table('students').update(update_data).eq('RNO', rno).execute()
        return len(response.data) > 0
    except Exception as e:
        print(f"[ERR] Update student: {e}")
        return False

def delete_student(rno):
    """Delete student from Supabase"""
    try:
        supabase = get_supabase_client()
        if supabase is None:
            return False
        
        response = supabase.table('students').delete().eq('RNO', rno).execute()
        return len(response.data) > 0
    except Exception as e:
        print(f"[ERR] Delete student: {e}")
        return False

def batch_insert_students(df):
    """Batch insert students into Supabase"""
    try:
        supabase = get_supabase_client()
        if supabase is None:
            return False
        
        # Convert DataFrame to list of dictionaries
        records = df.to_dict('records')
        
        # Insert in batches of 100
        batch_size = 100
        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]
            response = supabase.table('students').insert(batch).execute()
            if not response.data:
                return False
        
        return True
    except Exception as e:
        print(f"[ERR] Batch insert: {e}")
        return False

def get_stats():
    """Get database statistics from Supabase"""
    try:
        supabase = get_supabase_client()
        if supabase is None:
            # Return sample stats
            return {
                'total_students': 3,
                'departments': ['CSE', 'ECE'],
                'years': [3]
            }
        
        # Get all students
        response = supabase.table('students').select('DEPT, YEAR').execute()
        
        if not response.data:
            return {'total_students': 0, 'departments': [], 'years': []}
        
        df = pd.DataFrame(response.data)
        
        total_students = len(df)
        departments = sorted(df['DEPT'].dropna().unique().tolist())
        years = sorted(df['YEAR'].dropna().unique().tolist())
        
        return {
            'total_students': total_students,
            'departments': departments,
            'years': years
        }
    except Exception as e:
        print(f"[ERR] Get stats: {e}")
        return {'total_students': 0, 'departments': [], 'years': []}