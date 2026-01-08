import os
import requests
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

def test_student_fetch():
    print("Testing student data fetch...")
    
    # Test 1: Get sample RNOs
    url = f"{SUPABASE_URL}/rest/v1/students?select=rno,name&limit=5"
    headers = {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}',
        'Accept': 'application/json'
    }
    
    response = requests.get(url, headers=headers, timeout=10)
    print(f"Sample RNOs response: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Sample students: {data}")
        
        if data:
            test_rno = data[0]['rno']
            print(f"\nTesting with RNO: {test_rno}")
            
            # Test 2: Fetch specific student
            url2 = f"{SUPABASE_URL}/rest/v1/students?rno=eq.{test_rno}&select=*"
            response2 = requests.get(url2, headers=headers, timeout=10)
            print(f"Student fetch response: {response2.status_code}")
            
            if response2.status_code == 200:
                student_data = response2.json()
                print(f"Student data: {student_data}")
                
                if student_data:
                    student = student_data[0]
                    print(f"\nStudent fields:")
                    for key, value in student.items():
                        print(f"  {key}: {value}")
                else:
                    print("No student data returned")
            else:
                print(f"Error fetching student: {response2.text}")
    else:
        print(f"Error getting sample data: {response.text}")

if __name__ == "__main__":
    test_student_fetch()