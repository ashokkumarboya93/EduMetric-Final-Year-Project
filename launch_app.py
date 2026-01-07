#!/usr/bin/env python3
"""
Simple EduMetric Application Launcher
"""

import os
import sys

def main():
    print("=" * 60)
    print("EduMetric - Student Performance Analytics")
    print("=" * 60)
    print()
    print("🌐 Starting application at: http://localhost:5000")
    print("👤 Login credentials: admin / admin123")
    print("📊 Make sure your Supabase 'students' table is created")
    print("🛑 Press Ctrl+C to stop")
    print("=" * 60)
    print()
    
    try:
        # Import and run Flask app
        from app import app
        app.run(debug=True, host='localhost', port=5000)
    except KeyboardInterrupt:
        print("\n\n✅ Application stopped successfully!")
    except Exception as e:
        print(f"\n❌ Error starting application: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure Supabase 'students' table exists")
        print("2. Check your .env file has correct credentials")
        print("3. Verify internet connection")

if __name__ == "__main__":
    main()