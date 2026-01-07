#!/usr/bin/env python3
"""
Create sample data for EduMetric application
This script creates sample student data that can be used for testing
"""

import pandas as pd
import numpy as np
import os

def create_sample_csv():
    """Create a sample CSV file with student data"""
    
    departments = ['CSE', 'ECE', 'MECH', 'CIVIL', 'EEE', 'IT', 'CDS']
    sample_students = []
    
    for i in range(50):
        dept = departments[i % len(departments)]
        year = (i % 4) + 1
        
        student = {
            'S.NO': i + 1,
            'NAME': f"Student {i+1}",
            'RNO': f"22{dept}{str(i+1).zfill(3)}",
            'EMAIL': f"student{i+1}@college.edu",
            'DEPT': dept,
            'YEAR': year,
            'CURR_SEM': (year * 2) - 1,
            'BATCH_YEAR': 2022,
            'SEM1': np.random.randint(60, 95),
            'SEM2': np.random.randint(60, 95),
            'SEM3': np.random.randint(60, 95) if year >= 2 else 0,
            'SEM4': np.random.randint(60, 95) if year >= 2 else 0,
            'SEM5': np.random.randint(60, 95) if year >= 3 else 0,
            'SEM6': np.random.randint(60, 95) if year >= 3 else 0,
            'SEM7': np.random.randint(60, 95) if year >= 4 else 0,
            'SEM8': np.random.randint(60, 95) if year >= 4 else 0,
            'INTERNAL_MARKS': np.random.randint(15, 30),
            'TOTAL_DAYS_CURR': 90,
            'ATTENDED_DAYS_CURR': np.random.randint(70, 90),
            'PREV_ATTENDANCE_PERC': np.random.randint(75, 95),
            'BEHAVIOR_SCORE_10': np.random.randint(6, 10),
            'MENTOR': f"Dr. Mentor {i+1}",
            'MENTOR_EMAIL': f"mentor{i+1}@college.edu"
        }
        sample_students.append(student)
    
    # Create DataFrame
    df = pd.DataFrame(sample_students)
    
    # Save to CSV
    csv_path = os.path.join(os.path.dirname(__file__), 'sample_students.csv')
    df.to_csv(csv_path, index=False)
    
    print(f"[OK] Created sample data: {csv_path}")
    print(f"[OK] Generated {len(sample_students)} sample students")
    print(f"[OK] Departments: {', '.join(departments)}")
    print(f"[OK] Years: 1-4")
    
    return csv_path

def main():
    print("EduMetric Sample Data Generator")
    print("=" * 40)
    
    csv_path = create_sample_csv()
    
    print("\n" + "=" * 40)
    print("Sample data created successfully!")
    print("\nNext steps:")
    print("1. Run: python app.py")
    print("2. Open: http://localhost:5000")
    print("3. Use the Batch Upload feature to upload sample_students.csv")
    print("4. Or manually create the students table in Supabase and upload data")
    
    return True

if __name__ == "__main__":
    main()