import os
import pandas as pd
from flask import Flask, jsonify, request, render_template_string
import requests

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'fallback-key')

# Simple prediction function
def predict_student(data):
    perf = float(data.get('performance_overall', 50))
    attendance = float(data.get('attendance_pct', 75))
    
    if perf >= 80: perf_label = "HIGH"
    elif perf >= 60: perf_label = "MEDIUM"
    else: perf_label = "LOW"
    
    if attendance < 60 or perf < 40: risk_label = "HIGH"
    elif attendance < 75 or perf < 60: risk_label = "MEDIUM"
    else: risk_label = "LOW"
    
    if attendance < 50 or perf < 40: drop_label = "HIGH"
    elif attendance < 70 or perf < 60: drop_label = "MEDIUM"
    else: drop_label = "LOW"
    
    return {
        "performance_label": perf_label,
        "risk_label": risk_label,
        "dropout_label": drop_label
    }

# Sample data for demo
sample_students = [
    {
        'RNO': '23G31A4790',
        'NAME': 'Mohan Patel',
        'YEAR': 1,
        'SEM': 1,
        'performance_overall': 65.0,
        'attendance_pct': 72.0,
        'risk_score': 35.0,
        'dropout_score': 28.0
    },
    {
        'RNO': '23G31A1368', 
        'NAME': 'Meera Rao',
        'YEAR': 1,
        'SEM': 2,
        'performance_overall': 82.0,
        'attendance_pct': 88.0,
        'risk_score': 18.0,
        'dropout_score': 12.0
    }
]

@app.route("/")
def index():
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>EduMetric Analytics</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .header { color: #2c3e50; }
            .status { color: #27ae60; font-weight: bold; }
            .link { color: #3498db; text-decoration: none; }
        </style>
    </head>
    <body>
        <h1 class="header">🎓 EduMetric Analytics</h1>
        <p class="status">✅ System is running successfully!</p>
        <p><a href="/api/analytics/preview" class="link">View Analytics Preview</a></p>
        <p><a href="/api/test" class="link">Test API</a></p>
    </body>
    </html>
    """
    return html

@app.route("/api/test")
def api_test():
    return jsonify({"success": True, "message": "EduMetric API is working!"})

@app.route("/api/analytics/preview")
def api_analytics_preview():
    # Add predictions to sample data
    for student in sample_students:
        predictions = predict_student(student)
        student.update(predictions)
    
    return jsonify({
        "success": True,
        "stats": {
            "total_students": len(sample_students),
            "high_risk": sum(1 for s in sample_students if predict_student(s)["risk_label"] == "HIGH"),
            "high_dropout": sum(1 for s in sample_students if predict_student(s)["dropout_label"] == "HIGH")
        },
        "students": sample_students
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)