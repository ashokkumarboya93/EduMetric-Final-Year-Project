import psycopg2
import pandas as pd
from config import DATABASE_URL
import os

# If DATABASE_URL (direct Postgres) isn't provided, fall back to the Supabase
# Python client implementation in `db.py` so the app can still operate with
# just `SUPABASE_URL` + `SUPABASE_KEY`.
try:
    from db import (
        load_students_df as client_load_students_df,
        get_student_by_rno as client_get_student_by_rno,
        insert_student as client_insert_student,
        update_student as client_update_student,
        delete_student as client_delete_student,
        get_stats as client_get_stats,
        test_connection as client_test_connection,
    )
    CLIENT_AVAILABLE = True
except Exception:
    CLIENT_AVAILABLE = False

def get_supabase_connection():
    """Get connection to Supabase PostgreSQL database"""
    # Try to use direct DATABASE_URL if provided (useful for server-side scripts).
    from config import DATABASE_URL
    if not DATABASE_URL or 'YOUR-PASSWORD' in DATABASE_URL:
        # Fall back to Supabase client usage
        print("[INFO] No valid DATABASE_URL provided; using Supabase API client instead.")
        return None

    try:
        # Use SSL for Supabase connections
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        return conn
    except Exception as e:
        print(f"[WARN] Direct Postgres connection failed: {e}")
        return None

def create_students_table():
    """Create students table in Supabase if it doesn't exist"""
    try:
        conn = get_supabase_connection()
        if not conn:
            return False
        
        cursor = conn.cursor()
        
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS students (
            id SERIAL PRIMARY KEY,
            rno VARCHAR(50) UNIQUE NOT NULL,
            name VARCHAR(255) NOT NULL,
            email VARCHAR(255),
            dept VARCHAR(100),
            year INTEGER,
            curr_sem INTEGER,
            batch_year INTEGER,
            sem1 DECIMAL(5,2) DEFAULT 0,
            sem2 DECIMAL(5,2) DEFAULT 0,
            sem3 DECIMAL(5,2) DEFAULT 0,
            sem4 DECIMAL(5,2) DEFAULT 0,
            sem5 DECIMAL(5,2) DEFAULT 0,
            sem6 DECIMAL(5,2) DEFAULT 0,
            sem7 DECIMAL(5,2) DEFAULT 0,
            sem8 DECIMAL(5,2) DEFAULT 0,
            internal_marks DECIMAL(5,2) DEFAULT 20,
            total_days_curr DECIMAL(5,2) DEFAULT 90,
            attended_days_curr DECIMAL(5,2) DEFAULT 80,
            prev_attendance_perc DECIMAL(5,2) DEFAULT 85,
            behavior_score_10 DECIMAL(5,2) DEFAULT 7,
            mentor VARCHAR(255),
            mentor_email VARCHAR(255),
            performance_overall DECIMAL(5,2),
            performance_label VARCHAR(20),
            risk_score DECIMAL(5,2),
            risk_label VARCHAR(20),
            dropout_score DECIMAL(5,2),
            dropout_label VARCHAR(20),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        cursor.execute(create_table_sql)
        conn.commit()
        cursor.close()
        conn.close()
        print("Students table created successfully")
        return True
        
    except Exception as e:
        print(f"Error creating students table: {e}")
        return False

def load_students_df():
    """Load all students from Supabase as DataFrame and clean data types."""
    try:
        conn = get_supabase_connection()
        if conn:
            df = pd.read_sql("SELECT * FROM students", conn)
            conn.close()
        # Fallback to Supabase client if direct connection is not available
        elif CLIENT_AVAILABLE:
            df = client_load_students_df()
            if not isinstance(df, pd.DataFrame):
                return create_sample_data()
        else:
            return create_sample_data()

        if df.empty:
            print("[WARN] No students found in Supabase, using sample data")
            return create_sample_data()

        # Data type correction for analytics
        numeric_cols = [
            'id', 'year', 'curr_sem', 'batch_year', 'sem1', 'sem2', 'sem3', 'sem4', 
            'sem5', 'sem6', 'sem7', 'sem8', 'internal_pct', 'attendance_pct', 
            'behavior_pct', 'performance_overall', 'risk_score', 'dropout_score', 
            'past_avg', 'past_count', 'performance_trend', 'present_att', 'prev_att', 
            'internal_marks', 'total_days_curr', 'attended_days_curr', 
            'prev_attendance_perc', 'behavior_score_10'
        ]
        
        # Ensure column names are uppercase to match the rest of the app
        df.columns = df.columns.str.upper()

        for col in numeric_cols:
            # Check if the column exists (case-insensitive) before trying to convert
            if col.upper() in df.columns:
                df[col.upper()] = pd.to_numeric(df[col.upper()], errors='coerce').fillna(0)

        # Convert specific columns to integer type where appropriate
        int_cols = ['ID', 'YEAR', 'CURR_SEM', 'BATCH_YEAR', 'PAST_COUNT']
        for col in int_cols:
            if col in df.columns:
                df[col] = df[col].astype(int)

        return df

    except Exception as e:
        print(f"Error loading and cleaning students from Supabase: {e}")
        return create_sample_data()

def get_student_by_rno(rno):
    """Get single student by RNO from Supabase"""
    try:
        conn = get_supabase_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM students WHERE rno = %s", (rno,))
            columns = [desc[0] for desc in cursor.description]
            row = cursor.fetchone()
            if row:
                student = dict(zip(columns, row))
                student = {k.upper(): v for k, v in student.items()}
            else:
                student = None
            cursor.close()
            conn.close()
            return student

        # Fallback to client
        if CLIENT_AVAILABLE:
            student = client_get_student_by_rno(rno)
            if student:
                return {k.upper(): v for k, v in student.items()}
        return None
    except Exception as e:
        print(f"Error fetching student {rno}: {e}")
        return None

def insert_student(student_data):
    """Insert new student into Supabase"""
    try:
        conn = get_supabase_connection()
        if conn:
            cursor = conn.cursor()
            pg_data = {k.lower(): v for k, v in student_data.items()}
            columns = list(pg_data.keys())
            values = list(pg_data.values())
            placeholders = ', '.join(['%s'] * len(values))
            columns_str = ', '.join(columns)
            query = f"INSERT INTO students ({columns_str}) VALUES ({placeholders})"
            cursor.execute(query, values)
            conn.commit()
            cursor.close()
            conn.close()
            return True

        # Fallback to client
        if CLIENT_AVAILABLE:
            return client_insert_student(student_data)

        return False
    except Exception as e:
        print(f"Error inserting student: {e}")
        return False

def get_stats():
    """Get basic statistics from Supabase"""
    try:
        conn = get_supabase_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM students")
            total_students = cursor.fetchone()[0]
            cursor.execute("SELECT DISTINCT dept FROM students WHERE dept IS NOT NULL ORDER BY dept")
            departments = [row[0] for row in cursor.fetchall()]
            cursor.execute("SELECT DISTINCT year FROM students WHERE year IS NOT NULL ORDER BY year")
            years = []
            for row in cursor.fetchall():
                try:
                    # Safely convert to int, ignoring non-numeric values
                    years.append(int(row[0]))
                except (ValueError, TypeError):
                    continue
            cursor.close()
            conn.close()
            return {
                'total_students': total_students,
                'departments': departments,
                'years': years,
                'sample_rnos': []
            }

        # Fallback to client
        if CLIENT_AVAILABLE:
            stats = client_get_stats()
            # Ensure keys exist and match expected shape
            return {
                'total_students': stats.get('total_students', 0),
                'departments': stats.get('departments', []),
                'years': stats.get('years', []),
                'sample_rnos': stats.get('sample_rnos', [])
            }

        return {'total_students': 0, 'departments': [], 'years': [], 'sample_rnos': []}
    except Exception as e:
        print(f"Error getting stats: {e}")
        return {'total_students': 0, 'departments': [], 'years': []}

def create_sample_data():
    """Create sample data when database is not available"""
    import numpy as np
    
    departments = ['CSE', 'ECE', 'MECH', 'CIVIL', 'EEE']
    sample_data = []
    
    for i in range(50):
        student = {
            'ID': i + 1,
            'RNO': f"21{departments[i % len(departments)]}{str(i+1).zfill(3)}",
            'NAME': f"Student {i+1}",
            'EMAIL': f"student{i+1}@college.edu",
            'DEPT': departments[i % len(departments)],
            'YEAR': (i % 4) + 1,
            'CURR_SEM': ((i % 4) * 2) + 1,
            'SEM1': np.random.randint(60, 95),
            'SEM2': np.random.randint(60, 95),
            'SEM3': np.random.randint(60, 95),
            'SEM4': np.random.randint(60, 95),
            'INTERNAL_MARKS': np.random.randint(15, 30),
            'TOTAL_DAYS_CURR': 90,
            'ATTENDED_DAYS_CURR': np.random.randint(70, 90),
            'PREV_ATTENDANCE_PERC': np.random.randint(75, 95),
            'BEHAVIOR_SCORE_10': np.random.randint(6, 10),
            'PERFORMANCE_OVERALL': np.random.randint(60, 90),
            'PERFORMANCE_LABEL': np.random.choice(['high', 'medium', 'low']),
            'RISK_SCORE': np.random.randint(10, 50),
            'RISK_LABEL': np.random.choice(['high', 'medium', 'low']),
            'DROPOUT_SCORE': np.random.randint(10, 40),
            'DROPOUT_LABEL': np.random.choice(['high', 'medium', 'low'])
        }
        sample_data.append(student)
    
    return pd.DataFrame(sample_data)

def test_connection():
    """Test Supabase connection"""
    conn = get_supabase_connection()
    if conn:
        print("Supabase connection successful!")
        conn.close()
        return True
    else:
        print("Supabase connection failed!")
        return False