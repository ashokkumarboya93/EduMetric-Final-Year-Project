#!/usr/bin/env python3
"""
Quick test script to verify chat functionality
"""
import requests
import json

def test_chat_api():
    """Test the chat API endpoint"""
    base_url = "http://localhost:5000"
    
    # Test 1: Check if server is running
    try:
        response = requests.get(f"{base_url}/api/stats", timeout=5)
        print(f"✅ Server is running: {response.status_code}")
    except Exception as e:
        print(f"❌ Server not accessible: {e}")
        return
    
    # Test 2: Test chat functionality
    test_message = "Who are the top performers?"
    
    try:
        response = requests.post(
            f"{base_url}/api/chat",
            json={"message": test_message},
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"\n📤 Sent: {test_message}")
        print(f"📥 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success: {data.get('success', False)}")
            print(f"💬 Response: {data.get('response', 'No response')}")
            print(f"🔧 Type: {data.get('type', 'unknown')}")
            
            if data.get('data'):
                print(f"📊 Data available: {len(data['data'].get('students', []))} students")
        else:
            print(f"❌ Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Chat API error: {e}")

if __name__ == "__main__":
    print("🧪 Testing EduMetric Chat System...")
    test_chat_api()