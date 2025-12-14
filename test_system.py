#!/usr/bin/env python3
"""
Quick test script to verify the Student Performance Prediction System is working
"""

import os
import sys
import pandas as pd

# Add the project directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import DS3, load_ds3_data, compute_features, predict_student, safe_int

def test_data_loading():
    """Test if DS3 data is loaded correctly"""
    print("Testing data loading...")
    
    data = load_ds3_data()
    if data.empty:
        print("DS3 data is empty")
        return False
    
    print(f"DS3 data loaded: {len(data)} students")
    print(f"   Columns: {list(data.columns[:10])}...")  # Show first 10 columns
    return True

def test_student_search():
    """Test student search functionality"""
    print("\nTesting student search...")
    
    data = load_ds3_data()
    if data.empty:
        print("No data available for search")
        return False
    
    # Get first student RNO
    first_rno = str(data.iloc[0]['RNO']).strip()
    print(f"   Searching for RNO: {first_rno}")
    
    # Search for student
    df = data[data["RNO"].astype(str).str.strip() == first_rno]
    
    if df.empty:
        print("Student search failed")
        return False
    
    student = df.iloc[0].to_dict()
    print(f"Found student: {student.get('NAME', 'Unknown')}")
    return True

def test_prediction():
    """Test prediction functionality"""
    print("\nTesting prediction...")
    
    data = load_ds3_data()
    if data.empty:
        print("No data available for prediction")
        return False
    
    # Get first student
    student_raw = data.iloc[0].to_dict()
    
    # Extract required fields
    student_data = {
        "NAME": student_raw.get("NAME", ""),
        "RNO": student_raw.get("RNO", ""),
        "DEPT": student_raw.get("DEPT", ""),
        "YEAR": safe_int(student_raw.get("YEAR", 0)),
        "CURR_SEM": safe_int(student_raw.get("CURR_SEM", 0)),
        "SEM1": student_raw.get("SEM1", 0.0) or 0.0,
        "SEM2": student_raw.get("SEM2", 0.0) or 0.0,
        "SEM3": student_raw.get("SEM3", 0.0) or 0.0,
        "SEM4": student_raw.get("SEM4", 0.0) or 0.0,
        "SEM5": student_raw.get("SEM5", 0.0) or 0.0,
        "SEM6": student_raw.get("SEM6", 0.0) or 0.0,
        "SEM7": student_raw.get("SEM7", 0.0) or 0.0,
        "SEM8": student_raw.get("SEM8", 0.0) or 0.0,
        "INTERNAL_MARKS": student_raw.get("INTERNAL_MARKS", 0.0) or 0.0,
        "TOTAL_DAYS_CURR": student_raw.get("TOTAL_DAYS_CURR", 0.0) or 0.0,
        "ATTENDED_DAYS_CURR": student_raw.get("ATTENDED_DAYS_CURR", 0.0) or 0.0,
        "PREV_ATTENDANCE_PERC": student_raw.get("PREV_ATTENDANCE_PERC", 0.0) or 0.0,
        "BEHAVIOR_SCORE_10": student_raw.get("BEHAVIOR_SCORE_10", 0.0) or 0.0
    }
    
    try:
        # Compute features
        features = compute_features(student_data)
        print(f"   Features computed: performance_overall = {features['performance_overall']:.2f}")
        
        # Make predictions
        predictions = predict_student(features)
        print(f"   Predictions: {predictions}")
        
        print("Prediction system working")
        return True
        
    except Exception as e:
        print(f"Prediction failed: {e}")
        return False

def test_analytics():
    """Test analytics functionality"""
    print("\nTesting analytics...")
    
    data = load_ds3_data()
    if data.empty:
        print("No data available for analytics")
        return False
    
    # Check if predictions exist in data
    has_predictions = all(col in data.columns for col in ['performance_label', 'risk_label', 'dropout_label'])
    
    if has_predictions:
        print("Pre-computed predictions found in DS3")
        
        # Count predictions
        perf_counts = data['performance_label'].value_counts().to_dict()
        risk_counts = data['risk_label'].value_counts().to_dict()
        dropout_counts = data['dropout_label'].value_counts().to_dict()
        
        print(f"   Performance: {perf_counts}")
        print(f"   Risk: {risk_counts}")
        print(f"   Dropout: {dropout_counts}")
    else:
        print("No pre-computed predictions in DS3, will compute on-the-fly")
    
    return True

def main():
    """Run all tests"""
    print("Testing Student Performance Prediction System")
    print("=" * 50)
    
    tests = [
        test_data_loading,
        test_student_search,
        test_prediction,
        test_analytics
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"Test failed with exception: {e}")
    
    print("\n" + "=" * 50)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("All tests passed! System is ready to use.")
        print("\nTo start the application, run: python app.py")
    else:
        print("Some tests failed. Please check the issues above.")
    
    return passed == total

if __name__ == "__main__":
    main()