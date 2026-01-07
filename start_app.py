#!/usr/bin/env python3
"""
EduMetric Application Launcher
"""

import os
import sys

def main():
    print("=" * 60)
    print("EduMetric - Student Performance Analytics")
    print("=" * 60)
    print()
    print("Starting at: http://localhost:5000")
    print("Login: admin / admin123")
    print("Make sure Supabase 'students' table exists")
    print("Press Ctrl+C to stop")
    print("=" * 60)
    print()
    
    try:
        # Test connection first
        print("Testing database connection...")
        from db import test_connection, get_stats
        
        if test_connection():
            stats = get_stats()
            print("[OK] Connected! Found", stats['total_students'], "students")
        else:
            print("[WARNING] Database connection failed")
            print("Make sure you created the 'students' table in Supabase")
            print("Use the SQL from 'create_table_with_data.sql'")
            
        print("\nStarting Flask application...")
        
        # Import and run Flask app
        from app import app
        app.run(debug=True, host='localhost', port=5000)
        
    except KeyboardInterrupt:
        print("\n\nApplication stopped!")
    except Exception as e:
        print(f"\nError: {e}")
        print("\nTroubleshooting:")
        print("1. Create 'students' table in Supabase using create_table_with_data.sql")
        print("2. Check .env file has correct Supabase credentials")
        print("3. Verify internet connection")

if __name__ == "__main__":
    main()