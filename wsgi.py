from app import app

@app.route('/health')
def health_check():
    return {'status': 'healthy', 'message': 'EduMetric is running'}

if __name__ == '__main__':
    app.run()