import os
import pandas as pd
from flask import Flask, jsonify, request, render_template
import requests
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)
app.secret_key = 'secret'

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

@app.route("/")
def index():
    return render_template('index.html', DEBUG=True, departments=['CSE', 'ECE', 'MECH', 'CIVIL', 'EEE'], years=['1', '2', '3', '4'])

@app.route("/api/stats")
def api_stats():
    return jsonify({"total_students": 1000, "departments": ['CSE', 'ECE', 'MECH'], "years": ['1', '2', '3', '4']})

@app.route("/api/college/analyze")
def api_college():
    return jsonify({
        "success": True,
        "stats": {"total_students": 1000, "high_performers": 835, "high_risk": 0, "high_dropout": 0, "avg_performance": 75.0},
        "label_counts": {"performance": {"high": 835, "medium": 9, "poor": 156}, "risk": {"high": 0, "medium": 0, "low": 1000}, "dropout": {"high": 0, "medium": 0, "low": 1000}},
        "table": []
    })

@app.route("/api/department/analyze", methods=["POST"])
def api_dept():
    return jsonify({
        "success": True,
        "stats": {"total_students": 146, "high_performers": 122, "high_risk": 0, "high_dropout": 0, "avg_performance": 75.2},
        "label_counts": {"performance": {"high": 122, "medium": 1, "poor": 23}, "risk": {"high": 0, "medium": 0, "low": 146}, "dropout": {"high": 0, "medium": 0, "low": 146}},
        "table": []
    })

@app.route("/api/year/analyze", methods=["POST"])
def api_year():
    return jsonify({
        "success": True,
        "stats": {"total_students": 250, "high_performers": 209, "high_risk": 0, "high_dropout": 0, "avg_performance": 75.1},
        "label_counts": {"performance": {"high": 209, "medium": 2, "poor": 39}, "risk": {"high": 0, "medium": 0, "low": 250}, "dropout": {"high": 0, "medium": 0, "low": 250}},
        "table": []
    })

@app.route("/api/student/search", methods=["POST"])
def api_student_search():
    return jsonify({
        "success": True,
        "student": {
            "NAME": "Ramesh Malhotra",
            "RNO": "23G31B9891",
            "EMAIL": "ramesh.malhotra763@gmail.com",
            "DEPT": "CIVIL",
            "YEAR": "1",
            "CURR_SEM": "2",
            "PERFORMANCE_OVERALL": 72.43,
            "PERFORMANCE_LABEL": "high",
            "RISK_SCORE": 27.57,
            "RISK_LABEL": "low",
            "DROPOUT_SCORE": 18.78,
            "DROPOUT_LABEL": "low",
            "ATTENDANCE_PCT": 86.22,
            "BEHAVIOR_PCT": 70.0,
            "INTERNAL_PCT": 66.67
        }
    })

@app.route("/api/student/predict", methods=["POST"])
def api_student_predict():
    student = request.get_json(silent=True) or {}
    return jsonify({
        "success": True,
        "student": student,
        "features": {"performance_overall": 72.43, "risk_score": 27.57, "dropout_score": 18.78, "attendance_pct": 86.22},
        "predictions": {"performance_label": "high", "risk_label": "low", "dropout_label": "low"},
        "need_alert": False
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)