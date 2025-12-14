#!/usr/bin/env python3
"""
Simple test script to verify CRUD operations are working
"""

import requests
import json

BASE_URL = "http://localhost:5000"

def test_create_student():
    """Test creating a new student"""
    student_data = {
        "NAME": "Test Student",
        "RNO": "TEST001",
        "EMAIL": "test@example.com",
        "DEPT": "CSE",
        "YEAR": 2,
        "CURR_SEM": 3,
        "MENTOR": "Dr. Test Mentor",
        "MENTOR_EMAIL": "mentor@example.com",
        "SEM1": 85.5,
        "SEM2": 78.0,
        "INTERNAL_MARKS": 25,
        "TOTAL_DAYS_CURR": 90,
        "ATTENDED_DAYS_CURR": 85,
        "PREV_ATTENDANCE_PERC": 88.0,
        "BEHAVIOR_SCORE_10": 8.5
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/student/create", json=student_data)
        result = response.json()
        
        if result.get("success"):
            print("✅ CREATE: Student created successfully")
            print(f"   Name: {result['student']['NAME']}")
            print(f"   RNO: {result['student']['RNO']}")
            print(f"   Performance: {result['student']['performance_label']}")
            return True
        else:
            print(f"❌ CREATE: Failed - {result.get('message')}")
            return False
    except Exception as e:
        print(f"❌ CREATE: Error - {e}")
        return False

def test_read_student():
    """Test reading/searching for a student"""
    try:
        response = requests.post(f"{BASE_URL}/api/student/read", json={"rno": "TEST001"})
        result = response.json()
        
        if result.get("success") and result.get("count", 0) > 0:
            print("✅ READ: Student found successfully")
            student = result["students"][0]
            print(f"   Name: {student['NAME']}")
            print(f"   RNO: {student['RNO']}")
            print(f"   Department: {student['DEPT']}")
            return True
        else:
            print(f"❌ READ: Failed - {result.get('message')}")
            return False
    except Exception as e:
        print(f"❌ READ: Error - {e}")
        return False

def test_update_student():
    """Test updating a student"""
    update_data = {
        "RNO": "TEST001",
        "NAME": "Updated Test Student",
        "EMAIL": "updated@example.com",
        "DEPT": "ECE",
        "YEAR": 3,
        "CURR_SEM": 5,
        "INTERNAL_MARKS": 28,
        "SEM3": 92.0
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/student/update", json=update_data)
        result = response.json()
        
        if result.get("success"):
            print("✅ UPDATE: Student updated successfully")
            print(f"   Name: {result['student']['NAME']}")
            print(f"   Department: {result['student']['DEPT']}")
            print(f"   Performance: {result['student']['performance_label']}")
            return True
        else:
            print(f"❌ UPDATE: Failed - {result.get('message')}")
            return False
    except Exception as e:
        print(f"❌ UPDATE: Error - {e}")
        return False

def test_delete_student():
    """Test deleting a student"""
    try:
        response = requests.post(f"{BASE_URL}/api/student/delete", json={"rno": "TEST001"})
        result = response.json()
        
        if result.get("success"):
            print("✅ DELETE: Student deleted successfully")
            print(f"   Deleted: {result['deleted_student']['NAME']} ({result['deleted_student']['RNO']})")
            return True
        else:
            print(f"❌ DELETE: Failed - {result.get('message')}")
            return False
    except Exception as e:
        print(f"❌ DELETE: Error - {e}")
        return False

def test_stats():
    """Test getting dashboard stats"""
    try:
        response = requests.get(f"{BASE_URL}/api/stats")
        result = response.json()
        
        print("📊 DASHBOARD STATS:")
        print(f"   Total Students: {result.get('total_students', 0)}")
        print(f"   Departments: {len(result.get('departments', []))}")
        print(f"   Years: {result.get('years', [])}")
        return True
    except Exception as e:
        print(f"❌ STATS: Error - {e}")
        return False

def main():
    """Run all CRUD tests"""
    print("🚀 Starting CRUD Operations Test")
    print("=" * 50)
    
    # Test dashboard stats first
    test_stats()
    print()
    
    # Run CRUD tests in sequence
    tests = [
        ("CREATE", test_create_student),
        ("READ", test_read_student),
        ("UPDATE", test_update_student),
        ("DELETE", test_delete_student)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"Testing {test_name}...")
        success = test_func()
        results.append((test_name, success))
        print()
    
    # Summary
    print("=" * 50)
    print("📋 TEST SUMMARY:")
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"   {test_name}: {status}")
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All CRUD operations are working correctly!")
    else:
        print("⚠️  Some tests failed. Check the Flask app logs for details.")

if __name__ == "__main__":
    main()