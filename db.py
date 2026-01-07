import psycopg2
from supabase import create_client, Client
import pandas as pd
from config import SUPABASE_URL, SUPABASE_KEY, DATABASE_URL
import os

def _apply_rls_policy():
    """Connect to the database and apply the RLS policy for the students table."""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        # Get the absolute path to the SQL file
        dir_path = os.path.dirname(os.path.realpath(__file__))
        sql_file_path = os.path.join(dir_path, 'enable_rls_for_students.sql')

        with open(sql_file_path, 'r') as f:
            sql = f.read()
        
        cur.execute(sql)
        conn.commit()
        cur.close()
        conn.close()
        print("[INFO] RLS policy for students table applied successfully.")
    except Exception as e:
        # It's possible the policy already exists, or the table doesn't, so we can ignore some errors.
        if "already exists" in str(e) or "does not exist" in str(e):
            pass
        else:
            print(f"[WARN] Could not apply RLS policy: {e}")

# Apply the RLS policy when the module is loaded
_apply_rls_policy()

def get_supabase_client():
    """Get Supabase client"""
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        return supabase
    except Exception as e:
        print(f"[ERR] Supabase connection failed: {e}")
        return None


def test_connection():
    """Lightweight connectivity check for Supabase (keeps backward compatibility with tests expecting this function)."""
    try:
        supabase = get_supabase_client()
        if supabase is None:
            return False

        # Try a lightweight request to verify connectivity
        try:
            resp = supabase.table('students').select('rno').limit(1).execute()
            return True if resp is not None else False
        except Exception as e:
            print(f"Error connecting to Supabase: {e}")
            return False
    except Exception as e:
        print(f"[ERR] test_connection: {e}")
        return False

def load_students_df():
    """Load all students from Supabase"""
    try:
        supabase = get_supabase_client()
        if supabase is None:
            return pd.DataFrame()
        
        response = supabase.table('students').select('*').execute()
        if response.data:
            df = pd.DataFrame(response.data)
            # Convert column names to uppercase to match app expectations
            df.columns = df.columns.str.upper()
            return df
        return pd.DataFrame()
    except Exception as e:
        print(f"[ERR] Load students: {e}")
        return pd.DataFrame()

def get_student_by_rno(rno):
    """Get student by roll number from Supabase"""
    try:
        supabase = get_supabase_client()
        if supabase is None:
            return None
        
        response = supabase.table('students').select('*').eq('rno', rno).execute()
        if response.data:
            student = response.data[0]
            # Convert keys to uppercase to match app expectations
            return {k.upper(): v for k, v in student.items()}
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
        
        # Convert uppercase keys to lowercase for Supabase
        lowercase_data = {k.lower(): v for k, v in student_data.items()}
        response = supabase.table('students').insert(lowercase_data).execute()
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
        
        # Convert uppercase keys to lowercase for Supabase
        lowercase_data = {k.lower(): v for k, v in update_data.items()}
        response = supabase.table('students').update(lowercase_data).eq('rno', rno).execute()
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
        
        response = supabase.table('students').delete().eq('rno', rno).execute()
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
        
        # Convert DataFrame to list of dictionaries with lowercase keys
        records = df.to_dict('records')
        lowercase_records = [{k.lower(): v for k, v in record.items()} for record in records]
        
        # Insert in batches of 100
        batch_size = 100
        for i in range(0, len(lowercase_records), batch_size):
            batch = lowercase_records[i:i + batch_size]
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
            return {'total_students': 0, 'departments': [], 'years': [], 'sample_rnos': []}
        
        # Get all students
        response = supabase.table('students').select('dept, year, rno').execute()
        
        if not response.data:
            return {'total_students': 0, 'departments': [], 'years': [], 'sample_rnos': []}
        
        df = pd.DataFrame(response.data)
        
        total_students = len(df)
        departments = sorted(df['dept'].dropna().unique().tolist())
        years = sorted(df['year'].dropna().unique().tolist())
        sample_rnos = df['rno'].head(10).tolist()
        
        return {
            'total_students': total_students,
            'departments': departments,
            'years': years,
            'sample_rnos': sample_rnos
        }
    except Exception as e:
        print(f"[ERR] Get stats: {e}")
        return {'total_students': 0, 'departments': [], 'years': [], 'sample_rnos': []}


def get_all_students():
    """Get all students from Supabase (alias for load_students_df)"""
    try:
        supabase = get_supabase_client()
        if supabase is None:
            return []
        
        response = supabase.table('students').select('*').execute()
        if response.data:
            return response.data
        return []
    except Exception as e:
        print(f"[ERR] Get all students: {e}")
        return []

def search_student(rno):
    """Search student by RNO (alias for get_student_by_rno)"""
    student = get_student_by_rno(rno)
    if student:
        # Ensure uppercase keys
        return {k.upper(): v for k, v in student.items()}
    return None

def raw_rest_check(limit=1):
    """Direct HTTP check against Supabase REST endpoint for `students` table."""
    try:
        import requests
        from config import SUPABASE_URL, SUPABASE_KEY

        url = SUPABASE_URL.rstrip('/') + f"/rest/v1/students?select=*&limit={limit}"
        headers = {
            'apikey': SUPABASE_KEY,
            'Authorization': f'Bearer {SUPABASE_KEY}',
            'Accept': 'application/json'
        }
        resp = requests.get(url, headers=headers, timeout=10)
        try:
            body = resp.json()
        except Exception:
            body = resp.text
        return {'status_code': resp.status_code, 'body': body, 'url': url}
    except Exception as e:
        return {'error': str(e)}