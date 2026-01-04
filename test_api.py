#!/usr/bin/env python3
"""
API Endpoint Test Script
Test the /api/student/search endpoint directly
"""

import requests
import json

def test_api_endpoint():
    print("Testing API Endpoint...")
    print("=" * 40)
    
    # Test URL
    url = "http://localhost:5000/api/student/search"
    
    # Test data - using a sample RNO
    test_data = {
        "rno": "22G31A3167"  # Sample RNO from your database
    }
    
    try:
        print(f"Making POST request to: {url}")
        print(f"Request data: {test_data}")
        print()
        
        # Make the request
        response = requests.post(
            url, 
            json=test_data,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        print(f"Response Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print()
        
        # Check if response is JSON
        try:
            response_json = response.json()
            print("Response JSON:")
            print(json.dumps(response_json, indent=2))
            return True
        except json.JSONDecodeError as e:
            print(f"ERROR: Response is not valid JSON!")
            print(f"JSON Decode Error: {e}")
            print(f"Raw Response Text: {response.text[:500]}...")
            return False
            
    except requests.exceptions.ConnectionError:
        print("ERROR: Could not connect to Flask server!")
        print("Make sure Flask server is running with: python app.py")
        return False
    except requests.exceptions.Timeout:
        print("ERROR: Request timed out!")
        return False
    except Exception as e:
        print(f"ERROR: Unexpected error: {e}")
        return False

def test_stats_endpoint():
    print("\nTesting Stats Endpoint...")
    print("=" * 40)
    
    url = "http://localhost:5000/api/stats"
    
    try:
        response = requests.get(url, timeout=10)
        print(f"Stats Response Status: {response.status_code}")
        
        if response.status_code == 200:
            stats = response.json()
            print("Stats Response:")
            print(json.dumps(stats, indent=2))
            return True
        else:
            print(f"Stats endpoint failed with status: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"Stats endpoint error: {e}")
        return False

if __name__ == "__main__":
    print("EduMetric API Endpoint Test")
    print("=" * 50)
    
    # Test stats endpoint first
    stats_success = test_stats_endpoint()
    
    # Test student search endpoint
    search_success = test_api_endpoint()
    
    print("\n" + "=" * 50)
    if stats_success and search_success:
        print("SUCCESS: All API endpoints are working correctly!")
        print("The INVALID_JSON error might be a frontend issue.")
    else:
        print("ERROR: API endpoints have issues.")
        print("Check Flask server logs for more details.")