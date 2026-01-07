import os
import pandas as pd
from flask import Flask, jsonify, request, render_template
import requests

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'fallback-key')

# Simple prediction function
def predict_student_simple(data):
    perf = float(data.get('performance_overall', 50))
    attendance = float(data.get('attendance_pct', 75))
    
    if perf >= 80: perf_label = "high"
    elif perf >= 60: perf_label = "medium"
    else: perf_label = "low"
    
    if attendance < 60 or perf < 40: risk_label = "high"
    elif attendance < 75 or perf < 60: risk_label = "medium"
    else: risk_label = "low"
    
    if attendance < 50 or perf < 40: drop_label = "high"
    elif attendance < 70 or perf < 60: drop_label = "medium"
    else: drop_label = "low"
    
    return {
        "performance_label": perf_label,
        "risk_label": risk_label,
        "dropout_label": drop_label
    }

@app.route("/")
def index():
    return """
    <h1>EduMetric Analytics</h1>
    <p>System is running successfully!</p>
    <a href="/api/test">Test API</a>
    """

@app.route("/api/test")
def api_test():
    return jsonify({"success": True, "message": "API working!"})

@app.route("/api/analytics/preview")
def api_analytics_preview():
    sample_students = [
        {
            'RNO': '23G31A4790',
            'NAME': 'Mohan Patel',
            'YEAR': 1,
            'performance_label': 'medium',
            'risk_label': 'medium',
            'dropout_label': 'low'
        },
        {
            'RNO': '23G31A1368', 
            'NAME': 'Meera Rao',
            'YEAR': 1,
            'performance_label': 'high',
            'risk_label': 'low',
            'dropout_label': 'low'
        }
    ]
    
    return jsonify({
        "success": True,
        "stats": {"total_students": 2, "high_risk": 0, "high_dropout": 0},
        "students": sample_students
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)