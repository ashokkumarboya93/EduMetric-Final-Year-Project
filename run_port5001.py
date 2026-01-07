from app import app

if __name__ == '__main__':
    print("Starting EduMetric on port 5001...")
    print("Open: http://localhost:5001")
    app.run(debug=True, host='0.0.0.0', port=5001)