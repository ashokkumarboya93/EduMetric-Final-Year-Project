#!/usr/bin/env python3
"""
Setup script to create the students table in Supabase and insert sample data
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from supabase import create_client
from config import SUPABASE_URL, SUPABASE_KEY
import pandas as pd
import numpy as np

def create_students_table():
    """Create the students table using Supabase SQL"""
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # Create table SQL
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
        
        # Execute using RPC call
        result = supabase.rpc('exec_sql', {'sql': create_table_sql}).execute()
        print("[OK] Students table created successfully")
        return True
        
    except Exception as e:
        print(f"[INFO] Table creation via RPC failed: {e}")
        print("[INFO] Table may already exist or need to be created manually")
        return True  # Continue anyway

def create_sample_students():
    """Create sample student data"""
    departments = ['CSE', 'ECE', 'MECH', 'CIVIL', 'EEE', 'IT', 'CDS']
    sample_students = []
    
    for i in range(20):
        dept = departments[i % len(departments)]
        year = (i % 4) + 1
        
        student = {
            'rno': f"22{dept}{str(i+1).zfill(3)}",
            'name': f"Student {i+1}",
            'email': f"student{i+1}@college.edu",
            'dept': dept,
            'year': year,
            'curr_sem': (year * 2) - 1,
            'batch_year': 2022,
            'sem1': float(np.random.randint(60, 95)),
            'sem2': float(np.random.randint(60, 95)),
            'sem3': float(np.random.randint(60, 95)) if year >= 2 else 0,
            'sem4': float(np.random.randint(60, 95)) if year >= 2 else 0,
            'sem5': float(np.random.randint(60, 95)) if year >= 3 else 0,
            'sem6': float(np.random.randint(60, 95)) if year >= 3 else 0,
            'sem7': float(np.random.randint(60, 95)) if year >= 4 else 0,
            'sem8': float(np.random.randint(60, 95)) if year >= 4 else 0,
            'internal_marks': float(np.random.randint(15, 30)),
            'total_days_curr': 90.0,
            'attended_days_curr': float(np.random.randint(70, 90)),
            'prev_attendance_perc': float(np.random.randint(75, 95)),
            'behavior_score_10': float(np.random.randint(6, 10)),
            'mentor': f"Dr. Mentor {i+1}",
            'mentor_email': f"mentor{i+1}@college.edu",
            'performance_overall': float(np.random.randint(60, 90)),
            'performance_label': np.random.choice(['high', 'medium', 'low']),
            'risk_score': float(np.random.randint(10, 50)),
            'risk_label': np.random.choice(['high', 'medium', 'low']),
            'dropout_score': float(np.random.randint(10, 40)),
            'dropout_label': np.random.choice(['high', 'medium', 'low'])
        }
        sample_students.append(student)
    
    return sample_students

def insert_sample_data():
    """Insert sample data into Supabase"""
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # Check if data already exists
        existing = supabase.table('students').select('rno').limit(1).execute()
        if existing.data:
            print("[INFO] Sample data already exists, skipping insertion")
            return True
        
        sample_students = create_sample_students()
        
        # Insert in batches
        batch_size = 10
        for i in range(0, len(sample_students), batch_size):
            batch = sample_students[i:i + batch_size]
            result = supabase.table('students').insert(batch).execute()
            if not result.data:
                print(f"[ERROR] Failed to insert batch {i//batch_size + 1}")
                return False
        
        print(f"[OK] Inserted {len(sample_students)} sample students")
        return True
        
    except Exception as e:
        print(f"[ERROR] Failed to insert sample data: {e}")
        return False

def main():
    print("EduMetric Database Setup")
    print("=" * 40)
    
    # Test connection first
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("[OK] Connected to Supabase")
    except Exception as e:
        print(f"[ERROR] Failed to connect to Supabase: {e}")
        return False
    
    # Create table
    print("\n1. Creating students table...")
    create_students_table()
    
    # Insert sample data
    print("\n2. Inserting sample data...")
    if insert_sample_data():
        print("[OK] Sample data inserted successfully")
    else:
        print("[ERROR] Failed to insert sample data")
        return False
    
    print("\n" + "=" * 40)
    print("Database setup completed!")
    print("You can now run: python app.py")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)