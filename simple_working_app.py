import os
from flask import Flask, jsonify, request, render_template
import requests
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = 'test-key'

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

@app.route("/")
def index():
    return render_template('index.html', DEBUG=True, departments=['CSE', 'ECE', 'CIVIL'], years=[1, 2, 3, 4])

@app.route("/api/student/search", methods=["POST"])
def api_student_search():
    try:
        data = request.get_json() or {}
        rno = data.get("rno", "").strip()
        
        if not rno:
            return jsonify({"success": False, "message": "Please provide Register Number"})
        
        # Direct Supabase call
        url = f"{SUPABASE_URL}/rest/v1/students?rno=eq.{rno}"
        headers = {
            'apikey': SUPABASE_KEY,
            'Authorization': f'Bearer {SUPABASE_KEY}'
        }
        
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            students = response.json()
            if students:
                student = students[0]
                
                # Simple field mapping
                result = {
                    "NAME": student.get("name", ""),
                    "RNO": student.get("rno", ""),
                    "EMAIL": student.get("email", ""),
                    "DEPT": student.get("dept", ""),
                    "YEAR": int(student.get("year", 1)),
                    "CURR_SEM": int(student.get("curr_sem", 1)),
                    "SEM1": float(student.get("sem1", 0)),
                    "SEM2": float(student.get("sem2", 0)),
                    "SEM3": float(student.get("sem3", 0)),
                    "SEM4": float(student.get("sem4", 0)),
                    "INTERNAL_MARKS": float(student.get("internal_marks", 20)),
                    "TOTAL_DAYS_CURR": float(student.get("total_days_curr", 90)),
                    "ATTENDED_DAYS_CURR": float(student.get("attended_days_curr", 80)),
                    "PREV_ATTENDANCE_PERC": float(student.get("prev_attendance_perc", 85)),
                    "BEHAVIOR_SCORE_10": float(student.get("behavior_score_10", 7))
                }
                
                return jsonify({"success": True, "student": result})
        
        return jsonify({"success": False, "message": "Student not found"})
        
    except Exception as e:
        return jsonify({"success": False, "message": f"Error: {str(e)}"})

@app.route("/api/student/predict", methods=["POST"])
def api_student_predict():
    try:
        student = request.get_json() or {}
        
        # Simple prediction logic
        perf = 70.0  # Default performance
        if student.get("SEM1"):
            perf = float(student.get("SEM1", 70))
        
        # Generate predictions
        if perf >= 80:
            perf_label = "high"
            risk_label = "low"
            drop_label = "low"
        elif perf >= 60:
            perf_label = "medium"
            risk_label = "medium"
            drop_label = "medium"
        else:
            perf_label = "low"
            risk_label = "high"
            drop_label = "high"
        
        features = {
            "performance_overall": perf,
            "risk_score": 100 - perf,
            "dropout_score": 100 - perf,
            "attendance_pct": float(student.get("PREV_ATTENDANCE_PERC", 85))
        }
        
        predictions = {
            "performance_label": perf_label,
            "risk_label": risk_label,
            "dropout_label": drop_label
        }
        
        return jsonify({
            "success": True,
            "student": student,
            "features": features,
            "predictions": predictions,
            "need_alert": risk_label == "high"
        })
        
    except Exception as e:
        return jsonify({"success": False, "message": f"Error: {str(e)}"})

if __name__ == "__main__":
    app.run(debug=True, port=5000)