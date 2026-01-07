import os
import numpy as np
import pandas as pd
from flask import Flask, jsonify, request, render_template, send_file
import requests
import joblib
import io
import smtplib
from email.mime.text import MIMEText
from supabase_db import (
    load_students_df, get_student_by_rno, insert_student, 
    get_stats, create_students_table, test_connection
)
from db import update_student
from config import SECRET_KEY, DEBUG, EMAIL_USER, EMAIL_PASSWORD, PORT

try:
    from fpdf2 import FPDF
    FPDF_AVAILABLE = True
except ImportError:
    FPDF_AVAILABLE = False
    print("[WARN] fpdf not available - PDF export disabled")

try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    print("[WARN] matplotlib not available - PDF charts disabled")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

app = Flask(__name__)
app.secret_key = SECRET_KEY
app.config['DEBUG'] = DEBUG

def to_py(obj):
    """Convert numpy/pandas types to Python types for JSON."""
    if isinstance(obj, (np.integer, np.int64, np.int32, np.int16)):
        return int(obj)
    if isinstance(obj, (np.floating, np.float64, np.float32, np.float16)):
        val = float(obj)
        return None if np.isnan(val) or np.isinf(val) else val
    if isinstance(obj, float) and (np.isnan(obj) or np.isinf(obj)):
        return None
    if isinstance(obj, pd.Series):
        return {k: to_py(v) for k, v in obj.to_dict().items()}
    if isinstance(obj, pd.DataFrame):
        return [to_py(r) for _, r in obj.iterrows()]
    if isinstance(obj, dict):
        return {k: to_py(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [to_py(v) for v in obj]
    return obj

def safe_load(name):
    path = os.path.join(DATA_DIR, name)
    if not os.path.exists(path):
        print(f"[WARN] Model missing: {path}")
        return None
    try:
        return joblib.load(path)
    except Exception as e:
        print(f"[WARN] Failed to load {path}: {e}")
        return None

performance_model = safe_load("performance_model.pkl")
performance_encoder = safe_load("performance_label_encoder.pkl")
risk_model = safe_load("risk_model.pkl")
risk_encoder = safe_load("risk_label_encoder.pkl")
dropout_model = safe_load("dropout_model.pkl")
dropout_encoder = safe_load("dropout_label_encoder.pkl")

# Feature Engineering
def compute_features(student_row):
    curr_sem = int(student_row.get("CURR_SEM", 1) or 1)

    # past semester marks
    past = []
    for i in range(1, curr_sem):
        key = f"SEM{i}"
        v = student_row.get(key)
        if v not in (None, "", "nan") and not pd.isna(v):
            past.append(float(v))

    past_count = len(past)
    past_avg = float(np.mean(past)) if past_count > 0 else 0.0
    trend = float(past[-1] - past[-2]) if past_count >= 2 else 0.0

    internal_marks = float(student_row.get("INTERNAL_MARKS", 0) or 0)
    internal_pct = internal_marks / 30.0 * 100.0

    behavior_score = float(student_row.get("BEHAVIOR_SCORE_10", 0) or 0)
    behavior_pct = behavior_score * 10.0

    total_days = float(student_row.get("TOTAL_DAYS_CURR", 0) or 0)
    attended_days = float(student_row.get("ATTENDED_DAYS_CURR", 0) or 0)
    prev_att = float(student_row.get("PREV_ATTENDANCE_PERC", 0) or 0)

    present_att = (attended_days / total_days * 100.0) if total_days > 0 else 0.0

    attendance_pct = present_att * 0.70 + prev_att * 0.20 + behavior_pct * 0.10

    performance_overall = (
        past_avg * 0.50
        + internal_pct * 0.30
        + attendance_pct * 0.15
        + behavior_pct * 0.05
    )

    risk_score = abs(100.0 - performance_overall)

    dropout_overall = (
        past_avg * 0.10
        + internal_pct * 0.10
        + attendance_pct * 0.70
        + behavior_pct * 0.10
    )
    dropout_score = abs(100.0 - dropout_overall)

    return {
        "past_avg": round(past_avg, 2),
        "past_count": int(past_count),
        "internal_pct": round(internal_pct, 2),
        "attendance_pct": round(attendance_pct, 2),
        "behavior_pct": round(behavior_pct, 2),
        "performance_trend": round(trend, 2),
        "performance_overall": round(performance_overall, 2),
        "risk_score": round(risk_score, 2),
        "dropout_score": round(dropout_score, 2),
        "present_att": round(present_att, 2),
        "prev_att": round(prev_att, 2),
    }

# Model Prediction
def predict_student(f):
    if not all(
        [
            performance_model,
            performance_encoder,
            risk_model,
            risk_encoder,
            dropout_model,
            dropout_encoder,
        ]
    ):
        print("[WARN] One or more models not loaded, using fallback predictions")
        # Return reasonable fallback predictions based on performance score
        perf_score = f.get("performance_overall", 50)
        if perf_score >= 75:
            return {
                "performance_label": "high",
                "risk_label": "low",
                "dropout_label": "low",
            }
        elif perf_score >= 60:
            return {
                "performance_label": "medium",
                "risk_label": "medium",
                "dropout_label": "medium",
            }
        else:
            return {
                "performance_label": "low",
                "risk_label": "high",
                "dropout_label": "high",
            }

    try:
        X = np.array(
            [
                f["past_avg"],
                f["past_count"],
                f["internal_pct"],
                f["attendance_pct"],
                f["behavior_pct"],
                f["performance_trend"],
            ]
        ).reshape(1, -1)

        perf_raw = performance_model.predict(X)[0] # type: ignore
        risk_raw = risk_model.predict(X)[0] # type: ignore
        drop_raw = dropout_model.predict(X)[0] # type: ignore

        perf = performance_encoder.inverse_transform([perf_raw])[0] # type: ignore
        risk = risk_encoder.inverse_transform([risk_raw])[0] # type: ignore
        drop = dropout_encoder.inverse_transform([drop_raw])[0] # type: ignore

        return {
            "performance_label": str(perf),
            "risk_label": str(risk),
            "dropout_label": str(drop),
        }
    except Exception as e:
        print(f"[WARN] Model prediction failed: {e}")
        # Fallback based on performance score
        perf_score = f.get("performance_overall", 50)
        if perf_score >= 75:
            return {
                "performance_label": "high",
                "risk_label": "low",
                "dropout_label": "low",
            }
        elif perf_score >= 60:
            return {
                "performance_label": "medium",
                "risk_label": "medium",
                "dropout_label": "medium",
            }
        else:
            return {
                "performance_label": "low",
                "risk_label": "high",
                "dropout_label": "high",
            }

def load_ds3_data():
    return load_students_df()

# Group Analysis
def safe_int(v, default=0):
    try:
        if v is None or (isinstance(v, float) and np.isnan(v)):
            return default
        return int(v)
    except Exception:
        return default

def analyze_subset(df):
    if df.empty:
        return {
            "stats": {
                "total_students": 0,
                "high_performers": 0,
                "high_risk": 0,
                "high_dropout": 0,
                "avg_performance": 0.0,
            },
            "label_counts": {"performance": {}, "risk": {}, "dropout": {}},
            "scores": {"performance": [], "risk": [], "dropout": []},
            "table": [],
        }

    table = []
    perf_labels, risk_labels, drop_labels = [], [], []
    perf_scores, risk_scores, drop_scores = [], [], []

    for _, row in df.iterrows():
        try:
            st = row.to_dict()
            
            # Ensure required fields exist
            if not st.get('RNO') or not st.get('NAME'):
                continue
            
            # Always compute fresh predictions to ensure accuracy
            try:
                feats = compute_features(st)
                preds = predict_student(feats)
                perf_label = preds["performance_label"]
                risk_label = preds["risk_label"]
                drop_label = preds["dropout_label"]
                perf_score = feats["performance_overall"]
                risk_score = feats["risk_score"]
                drop_score = feats["dropout_score"]
            except Exception as e:
                print(f"[WARN] Prediction failed for student {st.get('RNO', 'unknown')}: {e}")
                # Fallback to default values
                perf_label = 'medium'
                risk_label = 'medium'
                drop_label = 'medium'
                perf_score = 50.0
                risk_score = 50.0
                drop_score = 50.0

            perf_labels.append(perf_label)
            risk_labels.append(risk_label)
            drop_labels.append(drop_label)
            perf_scores.append(float(perf_score))
            risk_scores.append(float(risk_score))
            drop_scores.append(float(drop_score))

            table.append(
                {
                    "RNO": str(st.get("RNO", "")),
                    "NAME": str(st.get("NAME", "")),
                    "DEPT": str(st.get("DEPT", "")),
                    "YEAR": safe_int(st.get("YEAR", 0)),
                    "CURR_SEM": safe_int(st.get("CURR_SEM", 0)),
                    "performance_label": perf_label,
                    "risk_label": risk_label,
                    "dropout_label": drop_label,
                    "performance_overall": float(perf_score),
                    "risk_score": float(risk_score),
                    "dropout_score": float(drop_score),
                }
            )
        except Exception as e:
            print(f"[WARN] Error processing student row: {e}")
            continue

    if not table:
        return {
            "stats": {
                "total_students": 0,
                "high_performers": 0,
                "high_risk": 0,
                "high_dropout": 0,
                "avg_performance": 0.0,
            },
            "label_counts": {"performance": {}, "risk": {}, "dropout": {}},
            "scores": {"performance": [], "risk": [], "dropout": []},
            "table": [],
        }

    stats = {
        "total_students": len(table),
        "high_performers": perf_labels.count("high"),
        "high_risk": risk_labels.count("high"),
        "high_dropout": drop_labels.count("high"),
        "avg_performance": round(float(np.mean(perf_scores)) if perf_scores else 0.0, 2),
    }

    # Create label counts with safe handling
    all_perf_labels = set(perf_labels) if perf_labels else set()
    all_risk_labels = set(risk_labels) if risk_labels else set()
    all_drop_labels = set(drop_labels) if drop_labels else set()

    label_counts = {
        "performance": {k: perf_labels.count(k) for k in all_perf_labels},
        "risk": {k: risk_labels.count(k) for k in all_risk_labels},
        "dropout": {k: drop_labels.count(k) for k in all_drop_labels},
    }

    scores = {
        "performance": perf_scores,
        "risk": risk_scores,
        "dropout": drop_scores,
    }

    return {
        "stats": stats,
        "label_counts": label_counts,
        "scores": scores,
        "table": table,
    }

# API Routes
@app.route("/favicon.ico")
def favicon():
    return "", 204  # No Content

@app.route("/")
def index():
    stats = get_stats()
    return render_template(
        "index.html", 
        DEBUG=app.config.get('DEBUG', False),
        departments=stats.get('departments', []),
        years=stats.get('years', [])
    )



@app.route("/api/stats")
def api_stats():
    try:
        stats = get_stats()
        return jsonify(stats)
    except Exception as e:
        print(f"[ERR] Stats API error: {e}")
        return jsonify({"total_students": 0, "departments": [], "years": []}), 500


@app.route("/api/test-connection")
def api_test_connection():
    try:
        ok = test_connection()
        return jsonify({"success": ok})
    except Exception as e:
        print(f"[ERR] Test connection API: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/diag/supabase')
def api_diag_supabase():
    """Diagnostics: call Supabase REST directly and return raw response."""
    try:
        from config import SUPABASE_URL, SUPABASE_KEY
        url = SUPABASE_URL.rstrip('/') + '/rest/v1/students?select=*&limit=1'
        headers = {
            'apikey': SUPABASE_KEY,
            'Authorization': f'Bearer {SUPABASE_KEY}',
            'Accept': 'application/json'
        }
        resp = requests.get(url, headers=headers, timeout=15)
        text = resp.text
        try:
            data = resp.json()
        except Exception:
            data = None
        return jsonify({
            'status_code': resp.status_code,
            'ok': resp.ok,
            'text': text[:1000],
            'json': data
        }), 200
    except Exception as e:
        print(f"[ERR] diag supabase: {e}")
        return jsonify({'error': str(e)}), 500


@app.route("/api/raw-students")
def api_raw_students():
    """Diagnostic: call Supabase REST directly and return status/body."""
    try:
        from db import raw_rest_check
        res = raw_rest_check(limit=1)
        return jsonify({'success': True, 'result': res})
    except Exception as e:
        print(f"[ERR] raw-students: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route("/api/student/search", methods=["POST"])
def api_student_search():
    data = request.get_json(silent=True) or {}
    rno = data.get("rno", "").strip()

    if not rno:
        return jsonify(
            {"success": False, "message": "Please provide Register Number."}
        ), 400

    # Search student in Supabase
    student = get_student_by_rno(rno)
    
    if not student:
        return jsonify({"success": False, "message": "Student not found."}), 404

    # Return student data with proper field mapping from uppercase to uppercase (already converted in db.py)
    student_data = {
        "NAME": student.get("NAME", ""),
        "RNO": student.get("RNO", ""),
        "EMAIL": student.get("EMAIL", ""),
        "DEPT": student.get("DEPT", ""),
        "YEAR": safe_int(student.get("YEAR", 0)),
        "CURR_SEM": safe_int(student.get("CURR_SEM", 0)),
        "MENTOR": student.get("MENTOR", ""),
        "MENTOR_EMAIL": student.get("MENTOR_EMAIL", ""),
        "SEM1": float(student.get("SEM1", 0) or 0),
        "SEM2": float(student.get("SEM2", 0) or 0),
        "SEM3": float(student.get("SEM3", 0) or 0),
        "SEM4": float(student.get("SEM4", 0) or 0),
        "SEM5": float(student.get("SEM5", 0) or 0),
        "SEM6": float(student.get("SEM6", 0) or 0),
        "SEM7": float(student.get("SEM7", 0) or 0),
        "SEM8": float(student.get("SEM8", 0) or 0),
        "INTERNAL_MARKS": float(student.get("INTERNAL_MARKS", 20) or 20),
        "TOTAL_DAYS_CURR": float(student.get("TOTAL_DAYS_CURR", 90) or 90),
        "ATTENDED_DAYS_CURR": float(student.get("ATTENDED_DAYS_CURR", 80) or 80),
        "PREV_ATTENDANCE_PERC": float(student.get("PREV_ATTENDANCE_PERC", 85) or 85),
        "BEHAVIOR_SCORE_10": float(student.get("BEHAVIOR_SCORE_10", 7) or 7)
    }
    
    return jsonify({"success": True, "student": to_py(student_data)})


@app.route("/api/student/predict", methods=["POST"])
def api_student_predict():
    student = request.get_json(silent=True) or {}
    feats = compute_features(student)
    preds = predict_student(feats)

    # Check if student needs mentor alert (poor or medium performance)
    need_alert = (preds["performance_label"] in ["poor", "medium"] or 
                 preds["risk_label"] == "high" or 
                 preds["dropout_label"] == "high")

    payload = {
        "success": True,
        "student": student,
        "features": feats,
        "predictions": preds,
        "need_alert": need_alert,
    }
    return jsonify(to_py(payload))

@app.route("/api/department/analyze", methods=["POST"])
def api_dept():
    try:
        data = request.get_json(silent=True) or {}
        dept = data.get("dept", None)
        year = data.get("year", None)

        df = load_students_df().copy()
        
        if df.empty:
            return jsonify({"success": False, "message": "No data available"}), 400
        
        # Filter by department
        if dept and dept != "":
            df = df[df["DEPT"].astype(str).str.strip() == str(dept).strip()]

        # Filter by year
        if year not in (None, "", "all"):
            try:
                year_int = int(year)
                df = df[df["YEAR"].fillna(0).astype(int) == year_int]
            except Exception as e:
                print("[WARN] dept year filter:", e)
                return jsonify({"success": False, "message": "Invalid year filter"}), 400

        if df.empty:
            return jsonify({"success": False, "message": "No students found for the selected criteria"}), 400

        res = analyze_subset(df)
        return jsonify(to_py({"success": True, **res}))
    except Exception as e:
        print(f"[ERR] Department analysis: {e}")
        return jsonify({"success": False, "message": f"Analysis failed: {str(e)}"}), 500

@app.route("/api/year/analyze", methods=["POST"])
def api_year():
    try:
        data = request.get_json(silent=True) or {}
        year = data.get("year", None)
        
        if not year:
            return jsonify({"success": False, "message": "Year is required"}), 400
            
        try:
            year_int = int(year)
        except Exception:
            return jsonify({"success": False, "message": "Invalid year format"}), 400

        df = load_students_df().copy()
        
        if df.empty:
            return jsonify({"success": False, "message": "No data available"}), 400
        
        try:
            df = df[df["YEAR"].fillna(0).astype(int) == year_int]
        except Exception as e:
            print("[WARN] year filter:", e)
            return jsonify({"success": False, "message": "Error filtering by year"}), 500

        if df.empty:
            return jsonify({"success": False, "message": f"No students found for year {year_int}"}), 400

        res = analyze_subset(df)
        return jsonify(to_py({"success": True, **res}))
    except Exception as e:
        print(f"[ERR] Year analysis: {e}")
        return jsonify({"success": False, "message": f"Analysis failed: {str(e)}"}), 500

@app.route("/api/college/analyze")
def api_college():
    try:
        df = load_students_df()
        
        if df.empty:
            return jsonify({"success": False, "message": "No data available"}), 400
        
        # Sample data if too large
        original_size = len(df)
        if len(df) > 500:
            df = df.sample(min(500, len(df)), random_state=42)

        res = analyze_subset(df)
        res["sample_size"] = int(len(df))
        res["total_size"] = int(original_size)
        return jsonify(to_py({"success": True, **res}))
    except Exception as e:
        print(f"[ERR] College analysis: {e}")
        return jsonify({"success": False, "message": f"Analysis failed: {str(e)}"}), 500





@app.route("/api/send-alert", methods=["POST"])
def api_send_alert():
    data = request.get_json(silent=True) or {}
    to_email = data.get("email", "ashokkumarboya999@gmail.com")  # Default mentor email
    
    # Extract student data for HTML email
    student_data = data.get("student", {})
    predictions = data.get("predictions", {})
    features = data.get("features", {})
    
    # Generate reason for alert based on predictions
    reasons = []
    if predictions.get("performance_label") == "poor":
        reasons.append("Poor academic performance detected")
    elif predictions.get("performance_label") == "medium":
        reasons.append("Below-average academic performance")
    
    if predictions.get("risk_label") == "high":
        reasons.append("High academic risk identified")
    
    if predictions.get("dropout_label") == "high":
        reasons.append("High dropout probability detected")
    
    if features.get("attendance_pct", 100) < 75:
        reasons.append("Low attendance rate")
    
    if features.get("internal_pct", 100) < 60:
        reasons.append("Poor internal assessment performance")
    
    alert_reason = "; ".join(reasons) if reasons else "Academic performance requires attention"
    
    # Create HTML email content
    subject = "Student Performance Alert – EduMetric"
    
    html_body = f"""
<div style="font-family: Arial, sans-serif; background: #f4f6fb; padding: 20px;">
  <div style="max-width: 600px; margin: auto; background: white; border-radius: 10px; padding: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
    <h2 style="color: #6a11cb; margin-bottom: 20px;">🚨 EduMetric – Student Alert</h2>
    
    <div style="background: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin-bottom: 20px;">
      <p style="margin: 0; font-weight: bold; color: #856404;">Immediate Mentor Attention Required</p>
    </div>
    
    <h3 style="color: #495057; border-bottom: 2px solid #e9ecef; padding-bottom: 10px;">Student Details</h3>
    <table style="width: 100%; margin-bottom: 20px;">
      <tr><td style="padding: 5px 0; font-weight: bold;">Name:</td><td style="padding: 5px 0;">{student_data.get('NAME', 'N/A')}</td></tr>
      <tr><td style="padding: 5px 0; font-weight: bold;">Register Number:</td><td style="padding: 5px 0;">{student_data.get('RNO', 'N/A')}</td></tr>
      <tr><td style="padding: 5px 0; font-weight: bold;">Department:</td><td style="padding: 5px 0;">{student_data.get('DEPT', 'N/A')}</td></tr>
      <tr><td style="padding: 5px 0; font-weight: bold;">Year:</td><td style="padding: 5px 0;">{student_data.get('YEAR', 'N/A')}</td></tr>
    </table>
    
    <h3 style="color: #495057; border-bottom: 2px solid #e9ecef; padding-bottom: 10px;">Academic Summary</h3>
    <table style="width: 100%; margin-bottom: 20px;">
      <tr><td style="padding: 5px 0; font-weight: bold;">Performance Level:</td><td style="padding: 5px 0; color: #dc3545; font-weight: bold;">{predictions.get('performance_label', 'unknown').upper()}</td></tr>
      <tr><td style="padding: 5px 0; font-weight: bold;">Risk Level:</td><td style="padding: 5px 0; color: #fd7e14; font-weight: bold;">{predictions.get('risk_label', 'unknown').upper()}</td></tr>
      <tr><td style="padding: 5px 0; font-weight: bold;">Dropout Probability:</td><td style="padding: 5px 0; color: #dc3545; font-weight: bold;">{predictions.get('dropout_label', 'unknown').upper()}</td></tr>
      <tr><td style="padding: 5px 0; font-weight: bold;">Attendance:</td><td style="padding: 5px 0;">{features.get('attendance_pct', 0):.1f}%</td></tr>
      <tr><td style="padding: 5px 0; font-weight: bold;">Internal Marks:</td><td style="padding: 5px 0;">{features.get('internal_pct', 0):.1f}%</td></tr>
    </table>
    
    <div style="background: #f8d7da; border-left: 4px solid #dc3545; padding: 15px; margin-bottom: 20px;">
      <p style="margin: 0; font-weight: bold; color: #721c24;">Reason for Alert:</p>
      <p style="margin: 5px 0 0 0; color: #721c24;">{alert_reason}</p>
    </div>
    
    <div style="background: #d1ecf1; border-left: 4px solid #17a2b8; padding: 15px; margin-bottom: 20px;">
      <p style="margin: 0; font-weight: bold; color: #0c5460;">Suggested Action:</p>
      <p style="margin: 5px 0 0 0; color: #0c5460;">Please review the student's academic progress and consider appropriate mentoring or intervention.</p>
    </div>
    
    <hr style="border: none; border-top: 1px solid #e9ecef; margin: 20px 0;">
    
    <p style="color: #6c757d; font-size: 14px; margin: 0;">Regards,<br><strong>EduMetric Analytics System</strong><br><em>(Automated Notification – Do Not Reply)</em></p>
  </div>
</div>
"""

    FROM = EMAIL_USER
    PASS = EMAIL_PASSWORD

    # Use MIMEText with "html" for proper HTML email rendering
    msg = MIMEText(html_body, "html")
    msg["From"] = FROM
    msg["To"] = to_email
    msg["Subject"] = subject

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(FROM, PASS)
        server.send_message(msg)
        server.quit()
        return jsonify({"success": True, "message": "Alert sent successfully"})
    except Exception as e:
        print("[ERR] send alert:", e)
        return jsonify({"success": False, "message": str(e)}), 500

# Data Processing
def clean_data(df):
    """Clean and normalize raw dataset"""
    df_clean = df.copy()
    
    # Handle different column name variations
    column_mapping = {
        'reg_number': 'RNO',
        'student_id': 'STUDENT_ID', 
        'name': 'NAME',
        'email': 'EMAIL',
        'department': 'DEPT',
        'year': 'YEAR',
        'semester': 'CURR_SEM',
        'mentor_name': 'MENTOR',
        'mentor_email': 'MENTOR_EMAIL',
        'sem1': 'SEM1', 'sem2': 'SEM2', 'sem3': 'SEM3', 'sem4': 'SEM4',
        'sem5': 'SEM5', 'sem6': 'SEM6', 'sem7': 'SEM7', 'sem8': 'SEM8',
        'age': 'AGE',
        'total_marks': 'TOTAL_MARKS',
        'attendance': 'ATTENDANCE',
        'cgpa': 'CGPA',
        'backlog_count': 'BACKLOG_COUNT'
    }
    
    # Rename columns to standard format
    for old_name, new_name in column_mapping.items():
        if old_name in df_clean.columns:
            df_clean.rename(columns={old_name: new_name}, inplace=True)
    
    # Replace empty strings and NaN with appropriate defaults
    numeric_cols = ['SEM1', 'SEM2', 'SEM3', 'SEM4', 'SEM5', 'SEM6', 'SEM7', 'SEM8', 
                   'INTERNAL_MARKS', 'TOTAL_DAYS_CURR', 'ATTENDED_DAYS_CURR', 
                   'PREV_ATTENDANCE_PERC', 'BEHAVIOR_SCORE_10', 'YEAR', 'CURR_SEM',
                   'AGE', 'TOTAL_MARKS', 'ATTENDANCE', 'CGPA', 'BACKLOG_COUNT', 'STUDENT_ID']
    
    for col in numeric_cols:
        if col in df_clean.columns:
            df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce').fillna(0)
    
    # Fill string columns
    string_cols = ['NAME', 'RNO', 'EMAIL', 'DEPT', 'MENTOR', 'MENTOR_EMAIL']
    for col in string_cols:
        if col in df_clean.columns:
            df_clean[col] = df_clean[col].fillna('')
    
    # Add missing columns with default values if not present
    required_cols = {
        'INTERNAL_MARKS': 20.0,
        'TOTAL_DAYS_CURR': 90.0,
        'ATTENDED_DAYS_CURR': 80.0,
        'PREV_ATTENDANCE_PERC': 85.0,
        'BEHAVIOR_SCORE_10': 7.0,
        'AGE': 20.0
    }
    
    for col, default_val in required_cols.items():
        if col not in df_clean.columns:
            df_clean[col] = default_val
    
    return df_clean



@app.route("/api/analytics/preview", methods=["GET"])
def api_analytics_preview():
    """Preview analytics data from DS3"""
    data_source = load_ds3_data()
    if data_source.empty:
        return jsonify({"success": False, "message": "No analytics data available"})
    
    # Get basic stats
    total_students = len(data_source)
    
    # Count high risk and high dropout students
    high_risk = 0
    high_dropout = 0
    
    # Get sample students for preview with predictions
    sample_students = []
    for _, row in data_source.head(100).iterrows():
        student_dict = row.to_dict()
        
        # Check if predictions exist, if not compute them
        if (not student_dict.get('performance_label') or 
            student_dict.get('performance_label') in ['', 'nan', 'unknown']):
            try:
                feats = compute_features(student_dict)
                preds = predict_student(feats)
                student_dict.update(preds)
            except Exception as e:
                print(f"[WARN] Prediction failed for {student_dict.get('RNO')}: {e}")
                student_dict.update({
                    'performance_label': 'medium',
                    'risk_label': 'medium', 
                    'dropout_label': 'medium'
                })
        
        # Count risk levels
        if student_dict.get('risk_label') == 'high':
            high_risk += 1
        if student_dict.get('dropout_label') == 'high':
            high_dropout += 1
            
        student = {
            'RNO': student_dict.get('RNO', ''),
            'NAME': student_dict.get('NAME', ''),
            'DEPT': student_dict.get('DEPT', ''),
            'YEAR': safe_int(student_dict.get('YEAR', 0)),
            'performance_label': student_dict.get('performance_label', 'medium'),
            'risk_label': student_dict.get('risk_label', 'medium'),
            'dropout_label': student_dict.get('dropout_label', 'medium')
        }
        sample_students.append(student)
    
    return jsonify({
        "success": True,
        "stats": {
            "total_students": total_students,
            "high_risk": high_risk,
            "high_dropout": high_dropout
        },
        "students": sample_students
    })

@app.route("/api/analytics/drilldown", methods=["POST"])
def api_analytics_drilldown():
    """Get filtered students based on chart segment click"""
    try:
        data = request.get_json(silent=True) or {}
        
        filter_type = data.get("filter_type", "")  # e.g., "performance_label", "risk_label", "dropout_label"
        filter_value = data.get("filter_value", "")  # e.g., "high", "medium", "low"
        scope = data.get("scope", "")  # e.g., "department", "year", "college", "batch"
        scope_value = data.get("scope_value", "")  # e.g., "CSE" or "3"
        
        if not filter_type or not filter_value:
            return jsonify({"success": False, "message": "Filter type and value are required"}), 400
        
        # Load data
        df = load_students_df().copy()
        
        if df.empty:
            return jsonify({"success": False, "message": "No data available"}), 400
        
        # Apply scope filter first
        if scope == "department" and scope_value:
            df = df[df["DEPT"].astype(str).str.strip() == str(scope_value).strip()]
        elif scope == "year" and scope_value:
            try:
                year_val = int(scope_value)
                df = df[df["YEAR"].fillna(0).astype(int) == year_val]
            except:
                pass
        
        # If predictions are missing, compute them
        results = []
        for _, row in df.iterrows():
            st = row.to_dict()
            
            # Check if predictions exist
            if ('performance_label' not in st or st.get('performance_label') in [None, '', 'nan', 'unknown']):
                feats = compute_features(st)
                preds = predict_student(feats)
                st.update(feats)
                st.update(preds)
            
            # Apply filter
            label_value = str(st.get(filter_type, 'unknown')).lower()
            if label_value == str(filter_value).lower():
                results.append({
                    "RNO": str(st.get("RNO", "")),
                    "NAME": str(st.get("NAME", "")),
                    "DEPT": str(st.get("DEPT", "")),
                    "YEAR": safe_int(st.get("YEAR", 0)),
                    "CURR_SEM": safe_int(st.get("CURR_SEM", 0)),
                    "performance_label": str(st.get("performance_label", "unknown")),
                    "risk_label": str(st.get("risk_label", "unknown")),
                    "dropout_label": str(st.get("dropout_label", "unknown")),
                    "performance_overall": round(float(st.get("performance_overall", 0) or 0), 2),
                    "risk_score": round(float(st.get("risk_score", 0) or 0), 2),
                    "dropout_score": round(float(st.get("dropout_score", 0) or 0), 2),
                })
        
        return jsonify({
            "success": True,
            "count": len(results),
            "students": to_py(results),
            "filter_info": {
                "type": filter_type,
                "value": filter_value,
                "scope": scope,
                "scope_value": scope_value
            }
        })
        
    except Exception as e:
        print(f"[ERR] Drilldown API: {e}")
        return jsonify({"success": False, "message": f"Drilldown failed: {str(e)}"}), 500

@app.route("/api/batch-upload", methods=["POST"])
def api_batch_upload():
    if "file" not in request.files:
        return jsonify({"success": False, "message": "No file uploaded"}), 400
    
    file = request.files["file"]
    mode = request.form.get("mode", "normalize")
    
    if file.filename == "":
        return jsonify({"success": False, "message": "Empty filename"}), 400
    
    if not file.filename.endswith((".csv", ".xlsx")):
        return jsonify({"success": False, "message": "Invalid file type. Only CSV/XLSX allowed"}), 400
    
    try:
        # Read uploaded file temporarily
        if file.filename.endswith(".csv"):
            df_uploaded = pd.read_csv(file)
        else:
            df_uploaded = pd.read_excel(file)
        
        if df_uploaded.empty:
            return jsonify({"success": False, "message": "Empty file"}), 400
        
        processed_rows = len(df_uploaded)
        
        if mode == "normalize":
            # Clean and normalize data
            df_clean = clean_data(df_uploaded)
            
            # Compute features and predictions for each student
            enhanced_students = []
            for _, row in df_clean.iterrows():
                student_dict = row.to_dict()
                feats = compute_features(student_dict)
                preds = predict_student(feats)
                
                # Merge all data
                full_record = student_dict.copy()
                full_record.update(feats)
                full_record.update(preds)
                enhanced_students.append(full_record)
            
            # Convert to DataFrame and insert into MySQL
            df_enhanced = pd.DataFrame(enhanced_students)
            success = batch_insert_students(df_enhanced)
            
            if success:
                return jsonify({
                    "success": True,
                    "mode": "normalize",
                    "processed_rows": processed_rows,
                    "message": "Data normalized, predictions generated, and saved to MySQL successfully"
                })
            else:
                return jsonify({"success": False, "message": "Failed to save data to MySQL"}), 500
                
        else:
            # Analytics mode - data already has predictions
            success = batch_insert_students(df_uploaded)
            
            if success:
                return jsonify({
                    "success": True,
                    "mode": "analytics",
                    "processed_rows": processed_rows,
                    "message": "Analytics data saved to MySQL successfully"
                })
            else:
                return jsonify({"success": False, "message": "Failed to save data to MySQL"}), 500
        
    except Exception as e:
        print(f"[ERR] batch upload: {e}")
        return jsonify({"success": False, "message": f"Upload failed: {str(e)}"}), 500



# CRUD Operations

@app.route("/api/student/create", methods=["POST"])
def api_create_student():
    """Create a new student record in MySQL"""
    try:
        data = request.get_json(silent=True) or {}
        
        # Validate required fields
        required_fields = ['NAME', 'RNO', 'EMAIL', 'DEPT', 'YEAR', 'CURR_SEM']
        for field in required_fields:
            if not data.get(field):
                return jsonify({"success": False, "message": f"{field} is required"}), 400
        
        # Check if student already exists
        existing = get_student_by_rno(data.get("RNO"))
        if existing:
            return jsonify({"success": False, "message": "Student with this RNO already exists"}), 400
        
        # Create student record with defaults
        student_data = {
            'NAME': str(data.get('NAME', '')).strip(),
            'RNO': str(data.get('RNO', '')).strip(),
            'EMAIL': str(data.get('EMAIL', '')).strip(),
            'DEPT': str(data.get('DEPT', '')).strip(),
            'YEAR': safe_int(data.get('YEAR', 1)),
            'CURR_SEM': safe_int(data.get('CURR_SEM', 1)),
            'MENTOR': str(data.get('MENTOR', '')).strip(),
            'MENTOR_EMAIL': str(data.get('MENTOR_EMAIL', '')).strip(),
            'SEM1': float(data.get('SEM1', 0) or 0),
            'SEM2': float(data.get('SEM2', 0) or 0),
            'SEM3': float(data.get('SEM3', 0) or 0),
            'SEM4': float(data.get('SEM4', 0) or 0),
            'SEM5': float(data.get('SEM5', 0) or 0),
            'SEM6': float(data.get('SEM6', 0) or 0),
            'SEM7': float(data.get('SEM7', 0) or 0),
            'SEM8': float(data.get('SEM8', 0) or 0),
            'INTERNAL_MARKS': float(data.get('INTERNAL_MARKS', 20) or 20),
            'TOTAL_DAYS_CURR': float(data.get('TOTAL_DAYS_CURR', 90) or 90),
            'ATTENDED_DAYS_CURR': float(data.get('ATTENDED_DAYS_CURR', 80) or 80),
            'PREV_ATTENDANCE_PERC': float(data.get('PREV_ATTENDANCE_PERC', 85) or 85),
            'BEHAVIOR_SCORE_10': float(data.get('BEHAVIOR_SCORE_10', 7) or 7)
        }
        
        # Compute features and predictions
        feats = compute_features(student_data)
        preds = predict_student(feats)
        
        # Merge all data
        full_record = student_data.copy()
        full_record.update(feats)
        full_record.update(preds)
        
        # Insert into MySQL
        success = insert_student(full_record)
        
        if success:
            return jsonify({
                "success": True,
                "message": "Student created successfully",
                "student": to_py(full_record)
            })
        else:
            return jsonify({"success": False, "message": "Failed to create student"}), 500
        
    except Exception as e:
        print(f"[ERR] Create student: {e}")
        return jsonify({"success": False, "message": f"Failed to create student: {str(e)}"}), 500

@app.route("/api/student/read", methods=["POST"])
def api_read_student():
    """Read/search student records from MySQL"""
    try:
        data = request.get_json(silent=True) or {}
        rno = data.get("rno", "").strip()
        name = data.get("name", "").strip()
        
        if not rno and not name:
            return jsonify({"success": False, "message": "Please provide RNO or Name to search"}), 400
        
        # Load all students from MySQL
        df = load_students_df()
        if df.empty:
            return jsonify({"success": False, "message": "No student data available"}), 400
        
        # Search by RNO or Name
        if rno:
            results = df[df["RNO"].astype(str).str.strip().str.contains(rno, case=False, na=False)]
        else:
            results = df[df["NAME"].astype(str).str.strip().str.contains(name, case=False, na=False)]
        
        if results.empty:
            return jsonify({"success": False, "message": "No students found matching the search criteria"})
        
        # Convert to list of dictionaries
        students = []
        for _, row in results.iterrows():
            student = {
                'RNO': str(row.get('RNO', '')),
                'NAME': str(row.get('NAME', '')),
                'EMAIL': str(row.get('EMAIL', '')),
                'DEPT': str(row.get('DEPT', '')),
                'YEAR': safe_int(row.get('YEAR', 0)),
                'CURR_SEM': safe_int(row.get('CURR_SEM', 0)),
                'performance_label': str(row.get('performance_label', 'unknown')),
                'risk_label': str(row.get('risk_label', 'unknown')),
                'dropout_label': str(row.get('dropout_label', 'unknown')),
                'performance_overall': float(row.get('performance_overall', 0) or 0),
                'risk_score': float(row.get('risk_score', 0) or 0),
                'dropout_score': float(row.get('dropout_score', 0) or 0)
            }
            students.append(student)
        
        return jsonify({
            "success": True,
            "students": to_py(students),
            "count": len(students)
        })
        
    except Exception as e:
        print(f"[ERR] Read student: {e}")
        return jsonify({"success": False, "message": f"Search failed: {str(e)}"}), 500

@app.route("/api/student/update", methods=["POST"])
def api_update_student():
    """Update existing student record in MySQL"""
    try:
        data = request.get_json(silent=True) or {}
        rno = data.get("RNO", "").strip()
        
        if not rno:
            return jsonify({"success": False, "message": "RNO is required for update"}), 400
        
        # Check if student exists
        existing = get_student_by_rno(rno)
        if not existing:
            return jsonify({"success": False, "message": "Student not found"}), 404
        
        # Update student data
        updated_data = {
            'NAME': str(data.get('NAME', existing.get('NAME', ''))).strip(),
            'EMAIL': str(data.get('EMAIL', existing.get('EMAIL', ''))).strip(),
            'DEPT': str(data.get('DEPT', existing.get('DEPT', ''))).strip(),
            'YEAR': safe_int(data.get('YEAR', existing.get('YEAR', 0))),
            'CURR_SEM': safe_int(data.get('CURR_SEM', existing.get('CURR_SEM', 0))),
            'MENTOR': str(data.get('MENTOR', existing.get('MENTOR', ''))).strip(),
            'MENTOR_EMAIL': str(data.get('MENTOR_EMAIL', existing.get('MENTOR_EMAIL', ''))).strip(),
            'SEM1': float(data.get('SEM1', existing.get('SEM1', 0)) or 0),
            'SEM2': float(data.get('SEM2', existing.get('SEM2', 0)) or 0),
            'SEM3': float(data.get('SEM3', existing.get('SEM3', 0)) or 0),
            'SEM4': float(data.get('SEM4', existing.get('SEM4', 0)) or 0),
            'SEM5': float(data.get('SEM5', existing.get('SEM5', 0)) or 0),
            'SEM6': float(data.get('SEM6', existing.get('SEM6', 0)) or 0),
            'SEM7': float(data.get('SEM7', existing.get('SEM7', 0)) or 0),
            'SEM8': float(data.get('SEM8', existing.get('SEM8', 0)) or 0),
            'INTERNAL_MARKS': float(data.get('INTERNAL_MARKS', existing.get('INTERNAL_MARKS', 20)) or 20),
            'TOTAL_DAYS_CURR': float(data.get('TOTAL_DAYS_CURR', existing.get('TOTAL_DAYS_CURR', 90)) or 90),
            'ATTENDED_DAYS_CURR': float(data.get('ATTENDED_DAYS_CURR', existing.get('ATTENDED_DAYS_CURR', 80)) or 80),
            'PREV_ATTENDANCE_PERC': float(data.get('PREV_ATTENDANCE_PERC', existing.get('PREV_ATTENDANCE_PERC', 85)) or 85),
            'BEHAVIOR_SCORE_10': float(data.get('BEHAVIOR_SCORE_10', existing.get('BEHAVIOR_SCORE_10', 7)) or 7)
        }
        
        # Recompute features and predictions
        feats = compute_features(updated_data)
        preds = predict_student(feats)
        
        # Merge all updates
        full_update = updated_data.copy()
        full_update.update(feats)
        full_update.update(preds)
        
        # Update in MySQL
        success = update_student(rno, full_update)
        
        if success:
            full_record = full_update.copy()
            full_record['RNO'] = rno
            return jsonify({
                "success": True,
                "message": "Student updated successfully",
                "student": to_py(full_record)
            })
        else:
            return jsonify({"success": False, "message": "Failed to update student"}), 500
        
    except Exception as e:
        print(f"[ERR] Update student: {e}")
        return jsonify({"success": False, "message": f"Failed to update student: {str(e)}"}), 500

@app.route("/api/student/delete", methods=["POST"])
def api_delete_student():
    """Delete student record from MySQL"""
    try:
        data = request.get_json(silent=True) or {}
        rno = data.get("rno", "").strip()
        
        if not rno:
            return jsonify({"success": False, "message": "RNO is required for deletion"}), 400
        
        # Get student info before deletion
        student = get_student_by_rno(rno)
        if not student:
            return jsonify({"success": False, "message": "Student not found"}), 404
        
        # Delete from MySQL
        success = delete_student(rno)
        
        if success:
            return jsonify({
                "success": True,
                "message": f"Student {student.get('NAME', '')} ({rno}) deleted successfully",
                "deleted_student": {
                    "RNO": rno,
                    "NAME": str(student.get('NAME', '')),
                    "DEPT": str(student.get('DEPT', '')),
                    "YEAR": safe_int(student.get('YEAR', 0))
                }
            })
        else:
            return jsonify({"success": False, "message": "Failed to delete student"}), 500
        
    except Exception as e:
        print(f"[ERR] Delete student: {e}")
        return jsonify({"success": False, "message": f"Failed to delete student: {str(e)}"}), 500

@app.route("/api/students/list", methods=["GET"])
def api_list_students():
    """List all students with pagination from MySQL"""
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 50))
        dept_filter = request.args.get('dept', '')
        year_filter = request.args.get('year', '')
        
        # Load from MySQL
        df = load_students_df()
        if df.empty:
            return jsonify({"success": False, "message": "No student data available"})
        
        # Apply filters
        filtered_data = df.copy()
        if dept_filter:
            filtered_data = filtered_data[filtered_data["DEPT"].astype(str).str.strip() == dept_filter]
        if year_filter:
            filtered_data = filtered_data[filtered_data["YEAR"].astype(int) == int(year_filter)]
        
        total_students = len(filtered_data)
        
        # Pagination
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_data = filtered_data.iloc[start_idx:end_idx]
        
        # Convert to list
        students = []
        for _, row in paginated_data.iterrows():
            student = {
                'RNO': str(row.get('RNO', '')),
                'NAME': str(row.get('NAME', '')),
                'EMAIL': str(row.get('EMAIL', '')),
                'DEPT': str(row.get('DEPT', '')),
                'YEAR': safe_int(row.get('YEAR', 0)),
                'CURR_SEM': safe_int(row.get('CURR_SEM', 0)),
                'performance_label': str(row.get('performance_label', 'unknown')),
                'risk_label': str(row.get('risk_label', 'unknown')),
                'dropout_label': str(row.get('dropout_label', 'unknown'))
            }
            students.append(student)
        
        return jsonify({
            "success": True,
            "students": to_py(students),
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": total_students,
                "pages": (total_students + per_page - 1) // per_page
            }
        })
        
    except Exception as e:
        print(f"[ERR] List students: {e}")
        return jsonify({"success": False, "message": f"Failed to list students: {str(e)}"}), 500





if FPDF_AVAILABLE:
    class EnhancedPDF(FPDF):
        def header(self):
            self.set_font('Arial', 'B', 15)
            self.cell(0, 10, 'EduMetric Analytics Report', 0, 1, 'C')
            self.ln(5)
        
        def footer(self):
            self.set_y(-15)
            self.set_font('Arial', 'I', 8)
            self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')
else:
    class EnhancedPDF:
        def __init__(self):
            pass

def create_kpi_chart(kpis, title):
    """Create KPI visualization chart"""
    if not MATPLOTLIB_AVAILABLE:
        return io.BytesIO()
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    fig.suptitle(title, fontsize=16, fontweight='bold')
    
    # Extract numeric values
    numeric_kpis = {}
    for key, value in kpis.items():
        if isinstance(value, (int, float)):
            numeric_kpis[key.replace('_', ' ').title()] = value
    
    if numeric_kpis:
        keys = list(numeric_kpis.keys())
        values = list(numeric_kpis.values())
        
        # KPI Bar Chart
        colors = ['#2196F3', '#4CAF50', '#FF9800', '#F44336', '#9C27B0'][:len(keys)]
        bars = ax1.bar(keys, values, color=colors, alpha=0.8)
        ax1.set_title('Key Performance Indicators', fontweight='bold')
        ax1.set_ylabel('Values', fontweight='bold')
        ax1.grid(True, alpha=0.3)
        
        # Add value labels
        for bar, value in zip(bars, values):
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height + max(values)*0.01,
                   f'{value:.1f}', ha='center', va='bottom', fontweight='bold')
        
        plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45, ha='right')
        
        # Donut chart for top KPIs
        if len(values) >= 3:
            top_3_keys = keys[:3]
            top_3_values = values[:3]
            
            wedges, texts = ax2.pie(top_3_values, labels=top_3_keys, colors=colors[:3], 
                                   startangle=90, textprops={'fontweight': 'bold'})
            
            centre_circle = plt.Circle((0,0), 0.60, fc='white')
            ax2.add_artist(centre_circle)
            ax2.text(0, 0, 'TOP\nKPIs', ha='center', va='center', fontsize=12, fontweight='bold')
            ax2.set_title('Top Performance Metrics', fontweight='bold')
    
    plt.tight_layout()
    
    # Save to bytes
    img_buffer = io.BytesIO()
    plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight', facecolor='white')
    img_buffer.seek(0)
    plt.close()
    return img_buffer

def create_performance_chart(data, chart_type='student'):
    """Create performance visualization charts"""
    if not MATPLOTLIB_AVAILABLE:
        return io.BytesIO()
    
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(14, 12))
    fig.suptitle(f'{chart_type.title()} Performance Analytics', fontsize=16, fontweight='bold')
    
    if chart_type == 'student' and 'features' in data:
        features = data['features']
        predictions = data.get('predictions', {})
        
        # Performance Metrics
        metrics = ['Performance', 'Risk Score', 'Dropout Risk']
        values = [features.get('performance_overall', 0), 
                 features.get('risk_score', 0), 
                 features.get('dropout_score', 0)]
        colors = ['#4CAF50', '#FF9800', '#F44336']
        
        bars1 = ax1.bar(metrics, values, color=colors, alpha=0.8)
        ax1.set_title('Performance Metrics', fontweight='bold')
        ax1.set_ylabel('Score (%)', fontweight='bold')
        ax1.set_ylim(0, 100)
        ax1.grid(True, alpha=0.3)
        
        for bar, value in zip(bars1, values):
            ax1.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 2,
                    f'{value:.1f}%', ha='center', va='bottom', fontweight='bold')
        
        # Detailed Metrics
        categories = ['Attendance', 'Behavior', 'Internal Marks']
        values2 = [features.get('attendance_pct', 0), 
                  features.get('behavior_pct', 0), 
                  features.get('internal_pct', 0)]
        
        bars2 = ax2.barh(categories, values2, color=['#2196F3', '#9C27B0', '#FF5722'], alpha=0.8)
        ax2.set_title('Detailed Breakdown', fontweight='bold')
        ax2.set_xlabel('Score (%)', fontweight='bold')
        ax2.set_xlim(0, 100)
        ax2.grid(True, alpha=0.3)
        
        # AI Predictions
        pred_labels = [f"Perf: {predictions.get('performance_label', 'unknown').upper()}",
                      f"Risk: {predictions.get('risk_label', 'unknown').upper()}",
                      f"Drop: {predictions.get('dropout_label', 'unknown').upper()}"]
        
        ax3.pie([1, 1, 1], labels=pred_labels, colors=colors, 
               startangle=90, textprops={'fontweight': 'bold'})
        ax3.set_title('AI Predictions', fontweight='bold')
        
        # Semester Trend
        if 'student' in data:
            student = data['student']
            sems, marks = [], []
            for i in range(1, 9):
                sem_key = f'SEM{i}'
                if sem_key in student and student[sem_key] and float(student[sem_key]) > 0:
                    sems.append(f'S{i}')
                    marks.append(float(student[sem_key]))
            
            if marks:
                ax4.plot(sems, marks, marker='o', linewidth=3, markersize=8, 
                        color='#1976D2', markerfacecolor='#FFEB3B')
                ax4.fill_between(sems, marks, alpha=0.3, color='#1976D2')
                ax4.set_title('Semester Trend', fontweight='bold')
                ax4.set_ylabel('Marks (%)', fontweight='bold')
                ax4.grid(True, alpha=0.3)
    
    elif chart_type in ['department', 'year', 'college']:
        if 'label_counts' in data:
            label_counts = data['label_counts']
            
            # Performance Distribution
            if 'performance' in label_counts:
                perf_data = label_counts['performance']
                colors1 = ['#4CAF50', '#FF9800', '#F44336']
                ax1.pie(perf_data.values(), labels=perf_data.keys(), 
                       autopct='%1.1f%%', colors=colors1, textprops={'fontweight': 'bold'})
                ax1.set_title('Performance Distribution', fontweight='bold')
            
            # Risk Distribution
            if 'risk' in label_counts:
                risk_data = label_counts['risk']
                ax2.pie(risk_data.values(), labels=risk_data.keys(), 
                       autopct='%1.1f%%', colors=colors1, textprops={'fontweight': 'bold'})
                ax2.set_title('Risk Distribution', fontweight='bold')
            
            # Dropout Distribution
            if 'dropout' in label_counts:
                drop_data = label_counts['dropout']
                ax3.pie(drop_data.values(), labels=drop_data.keys(), 
                       autopct='%1.1f%%', colors=colors1, textprops={'fontweight': 'bold'})
                ax3.set_title('Dropout Distribution', fontweight='bold')
        
        # Statistics
        if 'stats' in data:
            stats = data['stats']
            stat_names, stat_values = [], []
            
            for key, value in stats.items():
                if isinstance(value, (int, float)) and key != 'total_students':
                    stat_names.append(key.replace('_', ' ').title())
                    stat_values.append(value)
            
            if stat_names:
                bars4 = ax4.bar(stat_names, stat_values, color='#2196F3', alpha=0.8)
                ax4.set_title('Key Statistics', fontweight='bold')
                ax4.set_ylabel('Values', fontweight='bold')
                ax4.grid(True, alpha=0.3)
                plt.setp(ax4.xaxis.get_majorticklabels(), rotation=45, ha='right')
    
    plt.tight_layout()
    
    # Save to bytes
    img_buffer = io.BytesIO()
    plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight', facecolor='white')
    img_buffer.seek(0)
    plt.close()
    return img_buffer

@app.route("/api/export-report", methods=["POST"])
def api_export_report():
    """Export comprehensive analytics report with charts as PDF"""
    if not FPDF_AVAILABLE:
        return jsonify({"success": False, "message": "PDF export not available - fpdf package missing"}), 500
    
    try:
        data = request.get_json(silent=True) or {}
        report_type = data.get("report_type", "student")
        report_data = data.get("report_data", {})
        
        # Create enhanced PDF
        pdf = EnhancedPDF()
        pdf.add_page()
        
        # Title
        title_map = {
            "student": "Student Performance Report",
            "department": "Department Analytics Report", 
            "year": "Year Analytics Report",
            "college": "College Analytics Report"
        }
        
        pdf.set_font('Arial', 'B', 18)
        pdf.cell(0, 15, title_map.get(report_type, "Analytics Report"), 0, 1, 'C')
        pdf.ln(10)
        
        # Report metadata
        pdf.set_font('Arial', '', 11)
        pdf.cell(0, 8, f"Generated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}", 0, 1)
        pdf.cell(0, 8, "Report Type: Comprehensive Analytics with Visual Charts", 0, 1)
        pdf.ln(10)
        
        # Executive Summary
        pdf.set_font('Arial', 'B', 14)
        pdf.set_fill_color(240, 248, 255)
        pdf.cell(0, 10, "EXECUTIVE SUMMARY", 1, 1, 'C', True)
        pdf.set_font('Arial', '', 10)
        
        if 'summary' in report_data:
            summary_lines = [report_data['summary'][i:i+85] for i in range(0, len(report_data['summary']), 85)]
            for line in summary_lines:
                pdf.cell(0, 6, line, 0, 1)
        else:
            pdf.cell(0, 6, f"Comprehensive {report_type} analytics report with performance insights and predictions.", 0, 1)
        pdf.ln(5)
        
        # KPIs Section with Chart
        if 'kpis' in report_data or 'stats' in report_data:
            kpis = report_data.get('kpis', report_data.get('stats', {}))
            
            pdf.set_font('Arial', 'B', 14)
            pdf.cell(0, 10, "KEY PERFORMANCE INDICATORS & VISUAL ANALYTICS", 0, 1)
            pdf.ln(5)
            
            # Create and embed KPI chart
            kpi_chart = create_kpi_chart(kpis, "Performance Metrics Dashboard")
            
            # Save chart as temporary file
            temp_kpi_path = os.path.join(DATA_DIR, "temp_kpi_chart.png")
            with open(temp_kpi_path, 'wb') as f:
                f.write(kpi_chart.getvalue())
            
            pdf.image(temp_kpi_path, x=10, y=pdf.get_y(), w=190)
            pdf.ln(85)
            
            # KPI Table
            pdf.set_font('Arial', 'B', 10)
            pdf.cell(60, 8, "KPI Metric", 1, 0, 'C')
            pdf.cell(40, 8, "Value", 1, 0, 'C')
            pdf.cell(90, 8, "Description", 1, 1, 'C')
            
            pdf.set_font('Arial', '', 9)
            kpi_descriptions = {
                'total_students': 'Total number of students analyzed',
                'avg_performance': 'Average performance score across all students',
                'high_performers': 'Number of high-performing students',
                'high_risk': 'Number of students at high risk',
                'high_risk_pct': 'Percentage of high-risk students',
                'top_performers_pct': 'Percentage of top performers'
            }
            
            for key, value in kpis.items():
                if isinstance(value, (int, float)):
                    pdf.cell(60, 6, key.replace('_', ' ').title(), 1, 0, 'L')
                    pdf.cell(40, 6, f"{value:.1f}" + ('%' if 'pct' in key else ''), 1, 0, 'C')
                    pdf.cell(90, 6, kpi_descriptions.get(key, 'Performance metric'), 1, 1, 'L')
            
            # Clean up temp file
            if os.path.exists(temp_kpi_path):
                os.remove(temp_kpi_path)
        
        # Student Details
        if 'student' in report_data:
            student = report_data['student']
            pdf.ln(5)
            pdf.set_font('Arial', 'B', 12)
            pdf.set_fill_color(245, 245, 245)
            pdf.cell(0, 8, "STUDENT INFORMATION", 1, 1, 'L', True)
            pdf.set_font('Arial', '', 10)
            
            student_info = [
                f"Name: {student.get('NAME', 'N/A')}",
                f"Register Number: {student.get('RNO', 'N/A')}",
                f"Department: {student.get('DEPT', 'N/A')}",
                f"Year: {student.get('YEAR', 'N/A')}",
                f"Current Semester: {student.get('CURR_SEM', 'N/A')}"
            ]
            
            for info in student_info:
                pdf.cell(0, 6, info, 0, 1)
        
        # Performance Analytics Charts
        pdf.add_page()
        pdf.set_font('Arial', 'B', 16)
        pdf.cell(0, 10, "PERFORMANCE ANALYTICS & VISUAL INSIGHTS", 0, 1)
        pdf.ln(5)
        
        # Create and embed performance charts
        perf_chart = create_performance_chart(report_data, report_type)
        
        temp_perf_path = os.path.join(DATA_DIR, "temp_perf_chart.png")
        with open(temp_perf_path, 'wb') as f:
            f.write(perf_chart.getvalue())
        
        pdf.image(temp_perf_path, x=5, y=pdf.get_y(), w=200)
        pdf.ln(120)
        
        # Clean up temp file
        if os.path.exists(temp_perf_path):
            os.remove(temp_perf_path)
        
        # Detailed Analysis
        if 'features' in report_data:
            feats = report_data['features']
            pdf.set_font('Arial', 'B', 12)
            pdf.cell(0, 8, "DETAILED PERFORMANCE ANALYSIS", 0, 1)
            pdf.set_font('Arial', '', 9)
            
            analysis_data = [
                ["Performance Score", f"{feats.get('performance_overall', 0):.1f}%", "Overall academic performance"],
                ["Risk Assessment", f"{feats.get('risk_score', 0):.1f}%", "Academic difficulty probability"],
                ["Dropout Risk", f"{feats.get('dropout_score', 0):.1f}%", "Study discontinuation likelihood"],
                ["Attendance Rate", f"{feats.get('attendance_pct', 0):.1f}%", "Combined attendance performance"],
                ["Internal Marks", f"{feats.get('internal_pct', 0):.1f}%", "Continuous assessment score"]
            ]
            
            # Analysis table
            pdf.set_font('Arial', 'B', 9)
            pdf.cell(45, 6, "Metric", 1, 0, 'C')
            pdf.cell(25, 6, "Value", 1, 0, 'C')
            pdf.cell(120, 6, "Description", 1, 1, 'C')
            
            pdf.set_font('Arial', '', 8)
            for row in analysis_data:
                pdf.cell(45, 5, row[0], 1, 0, 'L')
                pdf.cell(25, 5, row[1], 1, 0, 'C')
                pdf.cell(120, 5, row[2], 1, 1, 'L')
        
        # AI Predictions
        if 'predictions' in report_data:
            preds = report_data['predictions']
            pdf.ln(5)
            pdf.set_font('Arial', 'B', 12)
            pdf.set_fill_color(255, 248, 220)
            pdf.cell(0, 8, "AI PREDICTIONS & RECOMMENDATIONS", 1, 1, 'C', True)
            pdf.set_font('Arial', '', 10)
            
            pred_info = [
                f"Performance Level: {preds.get('performance_label', 'N/A').upper()}",
                f"Risk Level: {preds.get('risk_label', 'N/A').upper()}",
                f"Dropout Risk: {preds.get('dropout_label', 'N/A').upper()}"
            ]
            
            for info in pred_info:
                pdf.cell(0, 6, info, 0, 1)
        
        # Recommendations
        pdf.ln(5)
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 8, "ACTIONABLE RECOMMENDATIONS", 0, 1)
        pdf.set_font('Arial', '', 9)
        
        # Generate recommendations based on data
        recommendations = []
        if 'features' in report_data:
            feats = report_data['features']
            if feats.get('performance_overall', 0) < 60:
                recommendations.append("• Immediate academic intervention required - performance below threshold")
            if feats.get('risk_score', 0) > 70:
                recommendations.append("• High-risk student - schedule counseling sessions")
            if feats.get('attendance_pct', 0) < 75:
                recommendations.append("• Attendance improvement needed - implement monitoring system")
        
        if not recommendations:
            recommendations = [
                "• Continue monitoring student progress regularly",
                "• Maintain current academic support systems",
                "• Encourage participation in enhancement programs"
            ]
        
        for rec in recommendations:
            pdf.cell(0, 5, rec, 0, 1)
        
        # Footer
        pdf.ln(10)
        pdf.set_font('Arial', 'B', 10)
        pdf.cell(0, 6, "EDUMETRIC ANALYTICS SYSTEM - COMPREHENSIVE REPORT", 0, 1, 'C')
        pdf.set_font('Arial', '', 8)
        pdf.cell(0, 5, "This report contains AI-powered insights with visual analytics and performance predictions.", 0, 1, 'C')
        
        # Save PDF
        pdf_output = io.BytesIO()
        pdf_content = pdf.output(dest='S').encode('latin-1')
        pdf_output.write(pdf_content)
        pdf_output.seek(0)
        
        # Generate filename
        timestamp = pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{report_type}_visual_report_{timestamp}.pdf"
        
        return send_file(
            pdf_output,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        print(f"[ERR] PDF export: {e}")
        return jsonify({"success": False, "message": f"PDF export failed: {str(e)}"}), 500

# NLP Intent Detection for Chat Assistant
def detect_intent(user_prompt):
    """Convert user natural language to structured analytics instruction"""
    prompt = user_prompt.lower().strip()
    
    intent = {
        "action": "unknown",
        "metric": "performance",
        "scope": "college",
        "filters": {},
        "order": "desc",
        "limit": 10
    }
    
    import re
    
    # Enhanced roll number detection - highest priority
    roll_patterns = [
        r'\b(\d{2}[a-z]\d{2}[a-z]\d{4})\b',      # 22G31A3167
        r'\b([a-z]{2,4}\d{4}[a-z]?\d{3,4})\b',   # CSE2021001, ECE21A001
        r'\b(\d{2}[a-z]{2,4}\d{3,4})\b',          # 21CSE001
        r'\b([a-z]\d{8,10})\b',                    # A2021001234
        r'\b(\d{10,12})\b',                        # 202100123456
        r'\b([a-z]{3}\d{6,8})\b',                  # CSE2021001
        r'\b(\d{4}[a-z]{2,4}\d{3,4})\b',          # 2021CSE001
        r'\b([a-z]{2,4}\d{2}[a-z]\d{3,4})\b'      # CSE21A001
    ]
    
    # Check for roll numbers in any context
    for pattern in roll_patterns:
        roll_match = re.search(pattern, prompt, re.IGNORECASE)
        if roll_match:
            roll_number = roll_match.group(1).upper()
            intent["action"] = "student_analytics"
            intent["filters"]["roll_number"] = roll_number
            intent["scope"] = "student"
            return intent
    
    # Check for roll numbers with common keywords
    roll_keywords = ["analytics", "analysis", "performance", "report", "details", "info", "show", "student", "for"]
    if any(word in prompt for word in roll_keywords):
        # More flexible roll number detection
        flexible_patterns = [
            r'\b(\d{2}[a-z]\d{2}[a-z]\d{4})\b',      # 22G31A3167
            r'\b([a-z]{2,4}\d{4}[a-z]?\d{3,4})\b',   # CSE2021001
            r'\b(\d{2}[a-z]{2,4}\d{3,4})\b',          # 21CSE001
            r'\b(\d{4}[a-z]{2,4}\d{3,4})\b'           # 2021CSE001
        ]
        
        for pattern in flexible_patterns:
            roll_match = re.search(pattern, prompt, re.IGNORECASE)
            if roll_match:
                roll_number = roll_match.group(1).upper()
                intent["action"] = "student_analytics"
                intent["filters"]["roll_number"] = roll_number
                intent["scope"] = "student"
                return intent
    
    # Action detection - order matters for priority
    if any(word in prompt for word in ["risk", "danger", "at-risk", "risky"]) and any(word in prompt for word in ["high", "students"]):
        intent["action"] = "high_risk"
        intent["metric"] = "risk"
    elif any(word in prompt for word in ["dropout", "drop", "leave", "quit"]) and any(word in prompt for word in ["high", "students"]):
        intent["action"] = "high_dropout"
        intent["metric"] = "dropout"
    elif any(word in prompt for word in ["top", "best", "high"]) and any(word in prompt for word in ["perform", "student"]):
        intent["action"] = "top_performers"
    elif any(word in prompt for word in ["weak", "low", "poor", "bad", "worst"]) and any(word in prompt for word in ["perform", "student"]):
        intent["action"] = "low_performers"
    elif any(word in prompt for word in ["attendance", "attend", "absent"]):
        intent["action"] = "attendance_analysis"
    elif any(word in prompt for word in ["compare", "comparison", "vs", "versus"]):
        intent["action"] = "comparison"
    elif any(word in prompt for word in ["department", "dept", "analytics", "analysis"]):
        intent["action"] = "department_analysis"
    
    # Scope detection
    if "department" in prompt or "dept" in prompt:
        intent["scope"] = "department"
    elif "year" in prompt:
        intent["scope"] = "year"
    elif "batch" in prompt:
        intent["scope"] = "batch"
    
    # Enhanced filter detection
    dept_match = re.search(r'\b(cse|ece|mech|civil|eee|it|cds|cai|ai|ml|ds|cyber|auto|aero|bio|chem)\b', prompt, re.IGNORECASE)
    if dept_match:
        dept_code = dept_match.group(1).upper()
        dept_mapping = {'AI': 'CAI', 'ML': 'CAI', 'DS': 'CDS'}
        intent["filters"]["dept"] = dept_mapping.get(dept_code, dept_code)
    
    year_match = re.search(r'\b(1st|2nd|3rd|4th|first|second|third|fourth|1|2|3|4)\s*year\b|\byear\s*(1|2|3|4)\b', prompt, re.IGNORECASE)
    if year_match:
        year_text = year_match.group(0).lower()
        year_map = {"1st": 1, "2nd": 2, "3rd": 3, "4th": 4, "first": 1, "second": 2, "third": 3, "fourth": 4, "1": 1, "2": 2, "3": 3, "4": 4}
        for key, val in year_map.items():
            if key in year_text:
                intent["filters"]["year"] = val
                break
    
    batch_match = re.search(r'\b(20\d{2})\b', prompt)
    if batch_match:
        intent["filters"]["batch_year"] = int(batch_match.group(1))
    
    num_match = re.search(r'\b(\d+)\b', prompt)
    if num_match:
        intent["limit"] = min(int(num_match.group(1)), 50)
    
    return intent

def execute_analytics_query(intent):
    """Execute analytics based on detected intent"""
    try:
        df = load_ds3_data()
        if df.empty:
            return {"error": "No student data available in the database. Please upload student data first."}
        
        print(f"[DEBUG] Loaded {len(df)} students for analysis")
        print(f"[DEBUG] Available departments: {sorted(df['DEPT'].dropna().unique().tolist())}")
        print(f"[DEBUG] Available years: {sorted(df['YEAR'].dropna().unique().tolist())}")
        print(f"[DEBUG] Intent filters: {intent['filters']}")
        
        # Handle student-specific analytics (roll number query)
        if intent["action"] == "student_analytics" and "roll_number" in intent["filters"]:
            roll_number = intent["filters"]["roll_number"]
            print(f"[DEBUG] Searching for student with roll number: {roll_number}")
            
            # Enhanced flexible matching for roll numbers
            student_row = None
            for _, row in df.iterrows():
                student_rno = str(row.get('RNO', '')).upper().strip()
                # Multiple matching strategies
                if (student_rno == roll_number or 
                    roll_number in student_rno or 
                    student_rno in roll_number or
                    student_rno.replace(' ', '') == roll_number.replace(' ', '') or
                    ''.join(filter(str.isalnum, student_rno)) == ''.join(filter(str.isalnum, roll_number))):
                    student_row = row
                    break
            
            if student_row is None:
                return {
                    "error": f"Student with roll number '{roll_number}' not found. Please check the roll number and try again.",
                    "suggestion": "Try entering the complete roll number or check for typos. Examples: 22G31A3167, CSE2021001, 21CSE001"
                }
            
            # Get comprehensive student data
            student_dict = student_row.to_dict()
            
            # Compute features and predictions
            try:
                feats = compute_features(student_dict)
                preds = predict_student(feats)
            except Exception as e:
                print(f"[WARN] Feature computation failed: {e}")
                feats = {
                    "past_avg": 0.0, "past_count": 0, "internal_pct": 0.0,
                    "attendance_pct": 0.0, "behavior_pct": 0.0, "performance_trend": 0.0,
                    "performance_overall": 0.0, "risk_score": 0.0, "dropout_score": 0.0,
                    "present_att": 0.0, "prev_att": 0.0
                }
                preds = {
                    "performance_label": "unknown",
                    "risk_label": "unknown", 
                    "dropout_label": "unknown"
                }
            
            # Create comprehensive student analytics response
            student_name = student_dict.get('NAME', 'Student')
            student_rno = student_dict.get('RNO', roll_number)
            
            # Generate detailed KPIs
            kpis = {
                "performance_score": feats["performance_overall"],
                "risk_score": feats["risk_score"],
                "dropout_score": feats["dropout_score"],
                "attendance_rate": feats["attendance_pct"],
                "internal_marks": feats["internal_pct"],
                "behavior_score": feats["behavior_pct"],
                "semester_trend": feats["performance_trend"]
            }
            
            # Generate recommendations
            recommendations = generate_student_recommendations(feats, preds)
            
            return {
                "action": "student_analytics",
                "title": f"Complete Analytics for {student_name} ({student_rno})",
                "student_info": {
                    "name": student_name,
                    "rno": student_rno,
                    "dept": student_dict.get('DEPT', 'N/A'),
                    "year": student_dict.get('YEAR', 'N/A'),
                    "semester": student_dict.get('CURR_SEM', 'N/A'),
                    "email": student_dict.get('EMAIL', 'N/A'),
                    "mentor": student_dict.get('MENTOR', 'N/A')
                },
                "kpis": kpis,
                "predictions": preds,
                "features": feats,
                "recommendations": recommendations,
                "semester_data": {
                    f"SEM{i}": student_dict.get(f"SEM{i}", 0) for i in range(1, 9)
                },
                "insight": f"Comprehensive analytics for {student_name}: Performance is {preds['performance_label'].upper()} ({feats['performance_overall']:.1f}%), Risk level is {preds['risk_label'].upper()}, Attendance at {feats['attendance_pct']:.1f}%. {'⚠️ Requires immediate attention!' if preds['risk_label'] == 'high' or preds['dropout_label'] == 'high' else '✅ Student is performing well.' if preds['performance_label'] == 'high' else '📊 Moderate performance - monitor closely.'}"
            }
        
        # Handle group analytics
        filtered_df = df.copy()
        
        # Apply filters with debugging
        if "dept" in intent["filters"]:
            dept_filter = intent["filters"]["dept"]
            print(f"[DEBUG] Filtering by department: {dept_filter}")
            # Try exact match first, then partial match
            exact_match = filtered_df[filtered_df["DEPT"].astype(str).str.upper() == dept_filter]
            if not exact_match.empty:
                filtered_df = exact_match
            else:
                # Try partial match
                partial_match = filtered_df[filtered_df["DEPT"].astype(str).str.upper().str.contains(dept_filter, na=False)]
                if not partial_match.empty:
                    filtered_df = partial_match
                else:
                    available_depts = sorted(df["DEPT"].dropna().unique().tolist())
                    return {"error": f"No students found for department '{dept_filter}'. Available departments: {', '.join(available_depts)}"}
            print(f"[DEBUG] After dept filter: {len(filtered_df)} students")
        
        if "year" in intent["filters"]:
            year_filter = intent["filters"]["year"]
            print(f"[DEBUG] Filtering by year: {year_filter}")
            filtered_df = filtered_df[filtered_df["YEAR"].fillna(0).astype(int) == year_filter]
            print(f"[DEBUG] After year filter: {len(filtered_df)} students")
        
        if "batch_year" in intent["filters"]:
            batch_filter = intent["filters"]["batch_year"]
            if "BATCH_YEAR" in filtered_df.columns:
                filtered_df = filtered_df[filtered_df["BATCH_YEAR"].fillna(0).astype(int) == batch_filter]
                print(f"[DEBUG] Filtered by batch {batch_filter}: {len(filtered_df)} students")
        
        if filtered_df.empty:
            available_depts = sorted(df["DEPT"].dropna().unique().tolist())
            available_years = sorted(df["YEAR"].dropna().unique().tolist())
            filters_used = []
            if "dept" in intent["filters"]:
                filters_used.append(f"Department: {intent['filters']['dept']}")
            if "year" in intent["filters"]:
                filters_used.append(f"Year: {intent['filters']['year']}")
            
            return {
                "error": f"No students found for {', '.join(filters_used) if filters_used else 'your criteria'}.",
                "suggestion": f"Available departments: {', '.join(available_depts)}. Available years: {', '.join(map(str, available_years))}. Try: 'CSE department analytics' or '2nd year analytics'"
            }
        
        # Analyze the filtered data
        analysis = analyze_subset(filtered_df)
        action = intent["action"]
        limit = intent["limit"]
        
        print(f"[DEBUG] Analysis complete. Action: {action}, Students: {len(analysis['table'])}")
        
        if action == "top_performers":
            sorted_students = sorted(analysis["table"], key=lambda x: x.get("performance_overall", 0), reverse=True)[:limit]
            return {
                "action": "top_performers",
                "title": f"Top {len(sorted_students)} Performers",
                "students": sorted_students,
                "stats": analysis["stats"],
                "insight": f"Found {len(sorted_students)} top performing students with average performance of {analysis['stats']['avg_performance']:.1f}%"
            }
        
        elif action == "low_performers":
            sorted_students = sorted(analysis["table"], key=lambda x: x.get("performance_overall", 0))[:limit]
            return {
                "action": "low_performers",
                "title": f"Students Needing Support ({len(sorted_students)})",
                "students": sorted_students,
                "stats": analysis["stats"],
                "insight": f"Found {len(sorted_students)} students who may need additional academic support"
            }
        
        elif action == "high_risk":
            high_risk_students = [s for s in analysis["table"] if s.get("risk_label") == "high"][:limit]
            return {
                "action": "high_risk",
                "title": f"High-Risk Students ({len(high_risk_students)})",
                "students": high_risk_students,
                "stats": analysis["stats"],
                "insight": f"These {len(high_risk_students)} students require immediate mentoring and intervention"
            }
        
        elif action == "high_dropout":
            high_dropout_students = [s for s in analysis["table"] if s.get("dropout_label") == "high"][:limit]
            return {
                "action": "high_dropout",
                "title": f"Dropout Risk Students ({len(high_dropout_students)})",
                "students": high_dropout_students,
                "stats": analysis["stats"],
                "insight": f"These {len(high_dropout_students)} students have high dropout probability and need retention support"
            }
        
        elif action == "department_analysis":
            # Check if we have department and year filters
            dept_filter = intent["filters"].get("dept")
            year_filter = intent["filters"].get("year")
            
            if dept_filter and year_filter:
                # Specific department and year analysis
                dept_df = filtered_df[filtered_df["DEPT"].astype(str).str.upper() == dept_filter]
                year_df = dept_df[dept_df["YEAR"].fillna(0).astype(int) == year_filter]
                
                if year_df.empty:
                    return {"error": f"No students found for {dept_filter} department, year {year_filter}"}
                
                dept_analysis = analyze_subset(year_df)
                return {
                    "action": "department_analysis",
                    "title": f"{dept_filter} Department Year {year_filter} Analytics",
                    "stats": dept_analysis["stats"],
                    "label_counts": dept_analysis["label_counts"],
                    "scores": dept_analysis["scores"],
                    "students": dept_analysis["table"],
                    "insight": f"{dept_filter} Department Year {year_filter}: {dept_analysis['stats']['total_students']} students analyzed, Average Performance: {dept_analysis['stats']['avg_performance']:.1f}%, High Risk: {dept_analysis['stats']['high_risk']} students"
                }
            elif dept_filter:
                # Department-only analysis
                dept_df = filtered_df[filtered_df["DEPT"].astype(str).str.upper() == dept_filter]
                
                if dept_df.empty:
                    return {"error": f"No students found for {dept_filter} department"}
                
                dept_analysis = analyze_subset(dept_df)
                return {
                    "action": "department_analysis",
                    "title": f"{dept_filter} Department Analytics",
                    "stats": dept_analysis["stats"],
                    "label_counts": dept_analysis["label_counts"],
                    "scores": dept_analysis["scores"],
                    "students": dept_analysis["table"],
                    "insight": f"{dept_filter} Department: {dept_analysis['stats']['total_students']} students analyzed, Average Performance: {dept_analysis['stats']['avg_performance']:.1f}%, High Risk: {dept_analysis['stats']['high_risk']} students"
                }
            else:
                # General department comparison
                dept_stats = {}
                for dept in df["DEPT"].dropna().unique():
                    dept_df = df[df["DEPT"] == dept]
                    if not dept_df.empty:
                        dept_analysis = analyze_subset(dept_df)
                        dept_stats[dept] = dept_analysis["stats"]
                
                return {
                    "action": "department_analysis",
                    "title": "Department Performance Comparison",
                    "department_stats": dept_stats,
                    "stats": analysis["stats"],
                    "insight": f"Department-wise analysis shows performance variation across {len(dept_stats)} departments"
                }
        
        elif action == "attendance_analysis":
            # Get students with attendance data
            students_with_attendance = [s for s in analysis["table"] if s.get("attendance_pct", 0) > 0]
            if students_with_attendance:
                attendance_data = [(s["attendance_pct"], s["performance_overall"]) for s in students_with_attendance]
                avg_attendance = np.mean([a[0] for a in attendance_data])
                avg_performance = np.mean([a[1] for a in attendance_data])
                return {
                    "action": "attendance_analysis",
                    "title": "Attendance Impact Analysis",
                    "attendance_data": attendance_data,
                    "avg_attendance": round(avg_attendance, 2),
                    "avg_performance": round(avg_performance, 2),
                    "stats": analysis["stats"],
                    "insight": f"Average attendance is {avg_attendance:.1f}% with corresponding performance of {avg_performance:.1f}%"
                }
            else:
                return {"error": "No attendance data available for analysis"}
        
        # Default: general stats
        return {
            "action": "general_stats",
            "title": "Analytics Overview",
            "stats": analysis["stats"],
            "students": analysis["table"][:limit],
            "insight": f"Analyzed {analysis['stats']['total_students']} students with {analysis['stats']['high_risk']} high-risk cases identified"
        }
    
    except Exception as e:
        print(f"[ERR] Analytics query execution: {e}")
        import traceback
        traceback.print_exc()
        return {"error": f"Analytics processing failed: {str(e)}"}

@app.route("/api/chat/test", methods=["GET"])
def api_chat_test():
    """Test chat functionality"""
    try:
        # Test data loading
        df = load_ds3_data()
        if df.empty:
            return jsonify({"success": False, "message": "No student data available for chat"})
        
        # Test basic analytics
        sample_size = min(len(df), 10)
        return jsonify({
            "success": True,
            "message": f"Chat system ready! Found {len(df)} students in database. Sample size: {sample_size}",
            "data_available": True,
            "total_students": len(df)
        })
    except Exception as e:
        return jsonify({"success": False, "message": f"Chat test failed: {str(e)}"})

@app.route("/api/test", methods=["GET"])
def api_test():
    """Simple test endpoint"""
    return jsonify({
        "success": True,
        "message": "API is working!",
        "timestamp": pd.Timestamp.now().isoformat()
    })
def generate_student_recommendations(features, predictions):
    """Generate personalized recommendations for a student"""
    recommendations = []
    
    # Performance-based recommendations
    perf_score = features.get('performance_overall', 0)
    perf_label = predictions.get('performance_label', 'unknown')
    if perf_score < 40:
        recommendations.append("🚨 CRITICAL: Immediate academic intervention required - schedule emergency counseling within 24 hours")
        recommendations.append("📚 Enroll in intensive remedial program with daily tutoring sessions")
        recommendations.append("👨🏫 Assign dedicated faculty mentor for personalized guidance")
        recommendations.append("📞 Urgent parent/guardian meeting to discuss academic support strategy")
    elif perf_score < 60:
        recommendations.append("⚠️ Academic support needed - schedule counseling session within 48 hours")
        recommendations.append("📖 Provide targeted study materials and practice tests")
        recommendations.append("👥 Arrange peer tutoring with high-performing students")
    elif perf_score < 75:
        recommendations.append("📈 Focus on improving study habits and time management skills")
        recommendations.append("🎯 Set specific academic goals with weekly progress reviews")
        recommendations.append("💡 Consider study skills workshops and learning techniques training")
    
    # Attendance-based recommendations
    attendance = features.get('attendance_pct', 0)
    if attendance < 60:
        recommendations.append("🚨 CRITICAL ATTENDANCE ISSUE: Investigate underlying causes immediately")
        recommendations.append("📋 Implement daily attendance monitoring with immediate follow-up")
        recommendations.append("🏥 Check for health, transportation, or family issues affecting attendance")
    elif attendance < 75:
        recommendations.append("⏰ Attendance improvement plan required - below minimum 75% requirement")
        recommendations.append("📱 Set up automated attendance alerts for parents/guardians")
        recommendations.append("🎁 Implement attendance incentive program with rewards")
    elif attendance < 85:
        recommendations.append("📅 Monitor attendance trends and provide gentle reminders")
        recommendations.append("🌟 Encourage consistent attendance with positive reinforcement")
    
    # Risk-based recommendations
    risk_label = predictions.get('risk_label', 'unknown')
    if risk_label == 'high':
        recommendations.append("🔴 HIGH RISK ALERT: Weekly one-on-one mentor sessions mandatory")
        recommendations.append("🧠 Conduct learning style assessment to customize teaching approach")
        recommendations.append("📊 Implement weekly progress tracking with measurable goals")
        recommendations.append("🤝 Connect with student counseling services for comprehensive support")
    elif risk_label == 'medium':
        recommendations.append("🟡 Moderate risk - bi-weekly check-ins with academic advisor")
        recommendations.append("📚 Provide additional learning resources and study guides")
    
    # Dropout prevention
    dropout_label = predictions.get('dropout_label', 'unknown')
    if dropout_label == 'high':
        recommendations.append("⚠️ HIGH DROPOUT RISK: Implement comprehensive retention strategy immediately")
        recommendations.append("👨👩👧👦 Engage family support system - schedule parent conference within 48 hours")
        recommendations.append("💰 Explore financial aid options and scholarship opportunities")
        recommendations.append("🎯 Create personalized retention plan with clear milestones")
        recommendations.append("🏆 Highlight student's strengths and celebrate small achievements")
    elif dropout_label == 'medium':
        recommendations.append("📈 Monitor closely for early warning signs of disengagement")
        recommendations.append("💪 Focus on building student confidence and motivation")
    
    # Internal marks improvement
    internal_pct = features.get('internal_pct', 0)
    if internal_pct < 40:
        recommendations.append("📝 URGENT: Intensive subject-specific tutoring required")
        recommendations.append("🔍 Conduct diagnostic assessment to identify knowledge gaps")
        recommendations.append("📖 Provide concept-building materials and visual learning aids")
    elif internal_pct < 60:
        recommendations.append("📊 Increase frequency of internal assessments with immediate feedback")
        recommendations.append("🎯 Focus on concept clarity through practical examples")
    
    # Behavior recommendations
    behavior_score = features.get('behavior_pct', 0)
    if behavior_score < 50:
        recommendations.append("🤝 Behavioral counseling and social skills development urgently needed")
        recommendations.append("👥 Implement peer mentoring program for social integration")
    elif behavior_score < 70:
        recommendations.append("🌱 Encourage participation in extracurricular activities")
        recommendations.append("🗣️ Provide communication skills training")
    
    # Positive reinforcement for good performers
    if perf_score >= 85 and attendance >= 90:
        recommendations.append("🌟 OUTSTANDING PERFORMANCE! Consider advanced learning opportunities")
        recommendations.append("🏆 Nominate for academic excellence awards and scholarships")
        recommendations.append("👨🏫 Encourage student to mentor struggling peers")
        recommendations.append("🚀 Explore research projects and internship opportunities")
    elif perf_score >= 75 and attendance >= 85:
        recommendations.append("✅ Good performance - maintain current study routine")
        recommendations.append("📈 Set higher academic goals for continued improvement")
        recommendations.append("🎯 Consider leadership roles in student activities")
    
    # Semester trend analysis
    trend = features.get('performance_trend', 0)
    if trend < -10:
        recommendations.append("📉 Declining performance trend detected - investigate causes immediately")
        recommendations.append("🔄 Review and adjust current study strategies")
    elif trend > 10:
        recommendations.append("📈 Excellent improvement trend - continue current approach")
        recommendations.append("🎉 Acknowledge and celebrate the positive progress")
    
    return recommendations if recommendations else ["✅ Continue current academic path with regular monitoring and support"]

@app.route("/api/chat", methods=["POST"])
def api_chat():
    """Process chat message and return analytics"""
    try:
        data = request.get_json(silent=True) or {}
        user_message = data.get("message", "").strip()
        
        if not user_message:
            return jsonify({"success": False, "message": "Please provide a message"}), 400
        
        if len(user_message) > 500:
            return jsonify({"success": False, "message": "Message too long. Please keep it under 500 characters."}, 400)
        
        print(f"[DEBUG] Processing chat message: {user_message}")
        
        # Detect intent
        intent = detect_intent(user_message)
        print(f"[DEBUG] Detected intent: {intent}")
        
        if intent["action"] == "unknown":
            return jsonify({
                "success": True,
                "response": "Please ask about performance, risk, attendance, or dropout analytics. You can also provide a roll number for individual student analytics. Examples: 'CSE2021001', 'give analytics for 21CSE001', or 'Show top performers in CSE'",
                "type": "error"
            })
        
        # Execute query
        result = execute_analytics_query(intent)
        print(f"[DEBUG] Query result keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
        
        if "error" in result:
            error_response = result["error"]
            if "suggestion" in result:
                error_response += f" {result['suggestion']}"
            return jsonify({
                "success": True,
                "response": error_response,
                "type": "error"
            })
        
        return jsonify({
            "success": True,
            "response": result.get("insight", "Analytics completed successfully"),
            "data": to_py(result),
            "type": "analytics"
        })
        
    except Exception as e:
        print(f"[ERR] Chat API: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": True,
            "response": f"I encountered an issue processing your request: {str(e)}. Please try a simpler query like 'show top students' or provide a roll number for individual analytics.",
            "type": "error"
        })

# Remove the if __name__ == "__main__" block for Vercel
# Vercel uses the api/index.py entry point instead

if __name__ == "__main__":
    app.run(debug=DEBUG, host='0.0.0.0', port=PORT)
else:
    # For Railway deployment
    application = app

@app.route("/test-db")
def test_db_connection():
    from supabase_db import test_connection
    if test_connection():
        return "Supabase connection successful!"
    else:
        return "Supabase connection failed. Check your .env file and credentials.", 500