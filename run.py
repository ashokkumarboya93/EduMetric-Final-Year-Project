import os
import sys

print("Starting EduMetric Application...")
print("URL: http://localhost:5000")
print("Login: admin / admin123")
print("Press Ctrl+C to stop")
print("-" * 40)

try:
    from app import app
    app.run(debug=True, host='0.0.0.0', port=5000)
except Exception as e:
    print(f"Error: {e}")
    input("Press Enter to exit...")