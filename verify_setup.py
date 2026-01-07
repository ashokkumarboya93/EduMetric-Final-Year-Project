#!/usr/bin/env python3
"""
Simple verification script to test Supabase connection and basic functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from db import test_connection, get_stats, load_students_df
from config import SUPABASE_URL, SUPABASE_KEY

def main():
    print("EduMetric Setup Verification")
    print("=" * 50)
    
    # Test 1: Environment Variables
    print("\n1. Testing Environment Variables...")
    if SUPABASE_URL and SUPABASE_KEY:
        print("[OK] Supabase credentials found")
        print(f"   URL: {SUPABASE_URL[:30]}...")
        print(f"   Key: {SUPABASE_KEY[:20]}...")
    else:
        print("[ERROR] Missing Supabase credentials in .env file")
        return False
    
    # Test 2: Database Connection
    print("\n2. Testing Database Connection...")
    try:
        if test_connection():
            print("[OK] Supabase connection successful")
        else:
            print("[ERROR] Supabase connection failed")
            return False
    except Exception as e:
        print(f"[ERROR] Connection error: {e}")
        return False
    
    # Test 3: Load Statistics
    print("\n3. Testing Database Statistics...")
    try:
        stats = get_stats()
        print(f"[OK] Statistics loaded: {stats['total_students']} students")
        print(f"   Departments: {len(stats['departments'])}")
        print(f"   Years: {stats['years']}")
    except Exception as e:
        print(f"[ERROR] Stats error: {e}")
        return False
    
    # Test 4: Load Student Data
    print("\n4. Testing Student Data Loading...")
    try:
        df = load_students_df()
        print(f"[OK] Student data loaded: {len(df)} records")
        if not df.empty:
            print(f"   Columns: {list(df.columns)[:5]}...")
        else:
            print("[WARNING] No student data found - you may need to upload data")
    except Exception as e:
        print(f"[ERROR] Data loading error: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("Setup verification completed successfully!")
    print("[OK] Your EduMetric application is ready to run")
    print("\nNext steps:")
    print("1. Run: python app.py")
    print("2. Open: http://localhost:5000")
    print("3. Upload student data if needed")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)