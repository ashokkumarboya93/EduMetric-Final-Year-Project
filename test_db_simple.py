#!/usr/bin/env python3
"""
Database Connection Test Script
Run this to verify your MySQL connection is working
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from db import test_connection, get_stats, load_students_df
from config import DB_CONFIG

def main():
    print("Testing EduMetric Database Connection...")
    print("=" * 50)
    
    # Test 1: Database Configuration
    print("Database Configuration:")
    print(f"   Host: {DB_CONFIG['host']}")
    print(f"   Database: {DB_CONFIG['database']}")
    print(f"   User: {DB_CONFIG['user']}")
    print(f"   Port: {DB_CONFIG['port']}")
    print(f"   Password: {'*' * len(str(DB_CONFIG['password']))}")
    print()
    
    # Test 2: Connection Test
    print("Testing Database Connection...")
    if test_connection():
        print("   SUCCESS: Database connection successful!")
    else:
        print("   ERROR: Database connection failed!")
        print("   TIP: Check your MySQL server is running and credentials are correct")
        return False
    print()
    
    # Test 3: Statistics
    print("Testing Statistics Query...")
    try:
        stats = get_stats()
        print(f"   SUCCESS: Total Students: {stats['total_students']}")
        print(f"   SUCCESS: Departments: {stats['departments']}")
        print(f"   SUCCESS: Years: {stats['years']}")
    except Exception as e:
        print(f"   ERROR: Statistics query failed: {e}")
        return False
    print()
    
    # Test 4: Load Students DataFrame
    print("Testing Student Data Loading...")
    try:
        df = load_students_df()
        if df.empty:
            print("   WARNING: No student data found in database")
            print("   TIP: You may need to upload student data first")
        else:
            print(f"   SUCCESS: Loaded {len(df)} students successfully")
            print(f"   SUCCESS: Columns: {list(df.columns)}")
    except Exception as e:
        print(f"   ERROR: Student data loading failed: {e}")
        return False
    print()
    
    print("Database tests completed!")
    return True

if __name__ == "__main__":
    success = main()
    if success:
        print("\nSUCCESS: Your database is ready for EduMetric!")
        print("TIP: You can now start the Flask server with: python app.py")
    else:
        print("\nERROR: Database issues detected. Please fix the above errors.")
        print("Common solutions:")
        print("   - Start MySQL server")
        print("   - Check database credentials in config.py")
        print("   - Create 'edumetric_db' database if it doesn't exist")
        print("   - Run database setup script if tables are missing")