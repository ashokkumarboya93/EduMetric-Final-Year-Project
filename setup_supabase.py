#!/usr/bin/env python3
"""
Supabase Setup Script
Run this to set up your Supabase database for EduMetric
"""

from supabase_db import test_connection, create_students_table, get_stats
from config import DATABASE_URL, SUPABASE_URL

def main():
    print("Setting up Supabase Database for EduMetric...")
    print("=" * 50)
    
    # Check configuration
    print("Configuration Check:")
    print(f"   Supabase URL: {SUPABASE_URL}")
    print(f"   Database URL: {'Configured' if DATABASE_URL else 'NOT CONFIGURED'}")
    print()
    
    if not DATABASE_URL:
        print("ERROR: DATABASE_URL not configured!")
        print("Please add your Supabase DATABASE_URL to .env file")
        print("Format: postgresql://postgres:password@db.project.supabase.co:5432/postgres")
        return False
    
    # Test connection
    print("Testing Supabase Connection...")
    if not test_connection():
        print("ERROR: Cannot connect to Supabase!")
        print("Please check your DATABASE_URL in .env file")
        return False
    
    # Create tables
    print("Creating Students Table...")
    if create_students_table():
        print("SUCCESS: Students table ready!")
    else:
        print("ERROR: Failed to create students table")
        return False
    
    # Test stats
    print("Testing Database Operations...")
    stats = get_stats()
    print(f"SUCCESS: Found {stats['total_students']} students")
    print(f"Departments: {stats['departments']}")
    print(f"Years: {stats['years']}")
    
    print("\nSUCCESS: Supabase database is ready!")
    print("You can now run: python app.py")
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        print("\nSetup failed. Please fix the errors above.")
        print("\nQuick Setup Guide:")
        print("1. Go to supabase.com and create a project")
        print("2. Get your DATABASE_URL from Settings > Database")
        print("3. Add it to your .env file")
        print("4. Run this script again")