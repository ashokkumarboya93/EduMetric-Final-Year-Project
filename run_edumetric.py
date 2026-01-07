#!/usr/bin/env python3
"""
Final Setup and Launch Script for EduMetric
"""

import sys
import os
import subprocess
import time

def print_header():
    print("=" * 60)
    print("EduMetric - Intelligent Student Performance Analytics")
    print("=" * 60)

def check_environment():
    """Check if environment is properly configured"""
    print("\n[CHECK] Checking Environment...")
    
    try:
        from config import SUPABASE_URL, SUPABASE_KEY
        if SUPABASE_URL and SUPABASE_KEY:
            print("[OK] Environment variables configured")
            return True
        else:
            print("[ERROR] Missing Supabase credentials")
            return False
    except Exception as e:
        print(f"[ERROR] Configuration error: {e}")
        return False

def check_dependencies():
    """Check if all required packages are installed"""
    print("\n[PACKAGES] Checking Dependencies...")
    
    required_packages = [
        ('flask', 'flask'),
        ('pandas', 'pandas'), 
        ('numpy', 'numpy'),
        ('supabase', 'supabase'),
        ('joblib', 'joblib'),
        ('sklearn', 'scikit-learn'),
        ('dotenv', 'python-dotenv'),
        ('psycopg2', 'psycopg2'),
        ('fpdf', 'fpdf2')
    ]
    
    missing = []
    for import_name, package_name in required_packages:
        try:
            __import__(import_name)
        except ImportError:
            missing.append(package_name)
    
    if missing:
        print(f"[ERROR] Missing packages: {', '.join(missing)}")
        print("Run: pip install -r requirements.txt")
        return False
    else:
        print("[OK] All dependencies installed")
        return True

def test_database():
    """Test database connection"""
    print("\n[DATABASE] Testing Database Connection...")
    
    try:
        from db import test_connection, get_stats
        
        if test_connection():
            print("[OK] Supabase connection successful")
            stats = get_stats()
            print(f"[INFO] Found {stats['total_students']} students in database")
            return True
        else:
            print("[WARNING] Database connection failed - table may not exist")
            print("[INFO] You can create the table manually using create_students_table.sql")
            return True  # Continue anyway
    except Exception as e:
        print(f"[WARNING] Database test failed: {e}")
        print("[INFO] You can still run the app and create data later")
        return True  # Continue anyway

def create_sample_data_if_needed():
    """Create sample data if no data exists"""
    print("\n[DATA] Checking Sample Data...")
    
    if not os.path.exists('sample_students.csv'):
        print("[INFO] Creating sample data...")
        try:
            subprocess.run([sys.executable, 'create_sample_data.py'], check=True, capture_output=True)
            print("[OK] Sample data created: sample_students.csv")
        except Exception as e:
            print(f"[WARNING] Could not create sample data: {e}")
    else:
        print("[OK] Sample data file exists")

def launch_application():
    """Launch the Flask application"""
    print("\n[LAUNCH] Launching EduMetric Application...")
    print("=" * 60)
    print("Application URL: http://localhost:5000")
    print("Admin Login: admin / admin123")
    print("Sample Data: sample_students.csv (use Batch Upload)")
    print("Press Ctrl+C to stop the server")
    print("=" * 60)
    
    try:
        # Import and run the Flask app
        from app import app
        app.run(debug=True, host='0.0.0.0', port=5000)
    except KeyboardInterrupt:
        print("\n\n[STOP] Server stopped by user")
        print("Thank you for using EduMetric!")
    except Exception as e:
        print(f"\n[ERROR] Application error: {e}")
        return False
    
    return True

def main():
    """Main setup and launch function"""
    print_header()
    
    # Check environment
    if not check_environment():
        print("\n[ERROR] Environment check failed")
        return False
    
    # Check dependencies
    if not check_dependencies():
        print("\n[ERROR] Dependency check failed")
        return False
    
    # Test database
    test_database()
    
    # Create sample data if needed
    create_sample_data_if_needed()
    
    # Launch application
    print("\n[SUCCESS] Setup completed successfully!")
    print("[INFO] If database is empty, use the Batch Upload feature to upload sample_students.csv")
    
    input("\nPress Enter to launch the application...")
    
    return launch_application()

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n[CANCEL] Setup cancelled by user")
        sys.exit(0)