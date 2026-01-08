import os
import pandas as pd
from flask import Flask, jsonify, request, render_template
import requests
from dotenv import load_dotenv
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'fallback-key')

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

def get_supabase_data():
    try:
        url = f"{SUPABASE_URL}/rest/v1/students?select=*"
        headers = {
            'apikey': SUPABASE_KEY,
            'Authorization': f'Bearer {SUPABASE_KEY}',
            'Accept': 'application/json'
        }
        
        response = requests.get(url, headers=headers, timeout=20)
        
        if response.status_code == 200:
            data = response.json()
            if data:
                df = pd.DataFrame(data)
                df.columns = df.columns.str.upper()
                return df
        
        return pd.DataFrame()
        
    except Exception as e:
        print(f"Error: {e}")
        return pd.DataFrame()

def analyze_subset(df):
    if df.empty:
        return {
            "stats": {"total_students": 0, "high_performers": 0, "high_risk": 0, "high_dropout": 0, "avg_performance": 0.0},
            "label_counts": {"performance": {}, "risk": {}, "dropout": {}},
            "table": []
        }

    table = []
    perf_labels, risk_labels, drop_labels = [], [], []
    perf_scores = []

    for _, row in df.iterrows():
        try:
            perf_label = str(row.get('PERFORMANCE_LABEL', 'medium')).lower()
            risk_label = str(row.get('RISK_LABEL', 'medium')).lower()
            drop_label = str(row.get('DROPOUT_LABEL', 'medium')).lower()
            
            perf_score = float(str(row.get('PERFORMANCE_OVERALL', 50)))
            
            perf_labels.append(perf_label)
            risk_labels.append(risk_label)
            drop_labels.append(drop_label)
            perf_scores.append(perf_score)

            table.append({
                "RNO": str(row.get("RNO", "")),
                "NAME": str(row.get("NAME", "")),
                "DEPT": str(row.get("DEPT", "")),
                "YEAR": str(row.get("YEAR", "")),
                "performance_label": perf_label,
                "risk_label": risk_label,
                "dropout_label": drop_label,
                "performance_overall": perf_score
            })
        except:
            continue

    stats = {
        "total_students": len(table),
        "high_performers": perf_labels.count("high"),
        "high_risk": risk_labels.count("high"),
        "high_dropout": drop_labels.count("high"),
        "avg_performance": round(sum(perf_scores) / len(perf_scores), 2) if perf_scores else 0.0
    }

    label_counts = {
        "performance": {"high": perf_labels.count("high"), "medium": perf_labels.count("medium"), "low": perf_labels.count("low"), "poor": perf_labels.count("poor")},
        "risk": {"high": risk_labels.count("high"), "medium": risk_labels.count("medium"), "low": risk_labels.count("low")},
        "dropout": {"high": drop_labels.count("high"), "medium": drop_labels.count("medium"), "low": drop_labels.count("low")}
    }

    return {"stats": stats, "label_counts": label_counts, "table": table}

@app.route("/")
def index():
    try:
        df = get_supabase_data()
        # Include all departments from Supabase data
        departments = sorted(df['DEPT'].unique().tolist()) if not df.empty and 'DEPT' in df.columns else ['CSE', 'ECE', 'MECH', 'CIVIL', 'EEE', 'CSE(AI)', 'CDS']
        years = sorted(df['YEAR'].unique().tolist()) if not df.empty and 'YEAR' in df.columns else ['1', '2', '3', '4']
        
        return render_template('index.html', 
                             DEBUG=True,
                             departments=departments, 
                             years=years)
    except Exception as e:
        return render_template('index.html', DEBUG=True, departments=['CSE', 'ECE', 'MECH', 'CIVIL', 'EEE', 'CSE(AI)', 'CDS'], years=['1', '2', '3', '4'])

@app.route("/api/stats")
def api_stats():
    try:
        df = get_supabase_data()
        if df.empty:
            return jsonify({"total_students": 0, "departments": [], "years": []})
        
        return jsonify({
            'total_students': len(df),
            'departments': sorted(df['DEPT'].unique().tolist()) if 'DEPT' in df.columns else [],
            'years': sorted(df['YEAR'].unique().tolist()) if 'YEAR' in df.columns else []
        })
    except Exception as e:
        return jsonify({"total_students": 0, "departments": [], "years": []}), 500

@app.route("/api/department/analyze", methods=["POST"])
def api_dept():
    try:
        data = request.get_json(silent=True) or {}
        dept = data.get("dept", None)
        year = data.get("year", None)

        df = get_supabase_data()
        
        if df.empty:
            return jsonify({"success": False, "message": "No data available"}), 400
        
        if dept and dept != "":
            df = df[df["DEPT"].astype(str).str.upper() == str(dept).upper()]

        if year not in (None, "", "all"):
            df = df[df["YEAR"].astype(str) == str(year)]

        if df.empty:
            return jsonify({"success": False, "message": "No students found"}), 400

        res = analyze_subset(df)
        return jsonify({"success": True, **res})
    except Exception as e:
        return jsonify({"success": False, "message": f"Analysis failed: {str(e)}"}), 500

@app.route("/api/year/analyze", methods=["POST"])
def api_year():
    try:
        data = request.get_json(silent=True) or {}
        year = data.get("year", None)
        
        if not year:
            return jsonify({"success": False, "message": "Year is required"}), 400

        df = get_supabase_data()
        
        if df.empty:
            return jsonify({"success": False, "message": "No data available"}), 400
        
        df = df[df["YEAR"].astype(str) == str(year)]

        if df.empty:
            return jsonify({"success": False, "message": f"No students found for year {year}"}), 400

        res = analyze_subset(df)
        return jsonify({"success": True, **res})
    except Exception as e:
        return jsonify({"success": False, "message": f"Analysis failed: {str(e)}"}), 500

@app.route("/api/college/analyze")
def api_college():
    try:
        df = get_supabase_data()
        
        if df.empty:
            return jsonify({"success": False, "message": "No data available"}), 400
        
        res = analyze_subset(df)
        return jsonify({"success": True, **res})
    except Exception as e:
        return jsonify({"success": False, "message": f"Analysis failed: {str(e)}"}), 500

@app.route("/api/student/search", methods=["POST"])
def api_student_search():
    try:
        data = request.get_json(silent=True) or {}
        rno = data.get("rno", "").strip()

        if not rno:
            return jsonify({"success": False, "message": "Please provide Register Number"}), 400

        url = f"{SUPABASE_URL}/rest/v1/students?rno=eq.{rno}&select=*"
        headers = {
            'apikey': SUPABASE_KEY,
            'Authorization': f'Bearer {SUPABASE_KEY}',
            'Accept': 'application/json'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data:
                student = data[0]
                # Convert to proper format with correct data types
                student_data = {
                    "NAME": str(student.get("name", "")),
                    "RNO": str(student.get("rno", "")),
                    "EMAIL": str(student.get("email", "")),
                    "DEPT": str(student.get("dept", "")),
                    "YEAR": int(student.get("year", 1)),
                    "CURR_SEM": int(student.get("curr_sem", 1)),
                    "MENTOR": str(student.get("mentor") or ""),
                    "MENTOR_EMAIL": str(student.get("mentor_email") or ""),
                    "SEM1": float(student.get("sem1", 0)),
                    "SEM2": float(student.get("sem2", 0)),
                    "SEM3": float(student.get("sem3", 0)),
                    "SEM4": float(student.get("sem4", 0)),
                    "SEM5": float(student.get("sem5", 0)),
                    "SEM6": float(student.get("sem6", 0)),
                    "SEM7": float(student.get("sem7", 0)),
                    "SEM8": float(student.get("sem8", 0)),
                    "INTERNAL_MARKS": float(student.get("internal_marks", 20)),
                    "TOTAL_DAYS_CURR": float(student.get("total_days_curr", 90)),
                    "ATTENDED_DAYS_CURR": float(student.get("attended_days_curr", 80)),
                    "PREV_ATTENDANCE_PERC": float(student.get("prev_attendance_perc", 85)),
                    "BEHAVIOR_SCORE_10": float(student.get("behavior_score_10", 7)),
                    "PERFORMANCE_OVERALL": float(student.get("performance_overall", 50)),
                    "PERFORMANCE_LABEL": str(student.get("performance_label", "medium")),
                    "RISK_SCORE": float(student.get("risk_score", 50)),
                    "RISK_LABEL": str(student.get("risk_label", "medium")),
                    "DROPOUT_SCORE": float(student.get("dropout_score", 50)),
                    "DROPOUT_LABEL": str(student.get("dropout_label", "medium")),
                    "ATTENDANCE_PCT": float(student.get("attendance_pct", 75)),
                    "BEHAVIOR_PCT": float(student.get("behavior_pct", 70)),
                    "INTERNAL_PCT": float(student.get("internal_pct", 66))
                }
                return jsonify({"success": True, "student": student_data})
        
        return jsonify({"success": False, "message": "Student not found"}), 404
        
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route("/api/student/predict", methods=["POST"])
def api_student_predict():
    try:
        student = request.get_json(silent=True) or {}
        rno = student.get("RNO", "").strip()
        
        # If RNO exists, fetch from Supabase database
        if rno:
            url = f"{SUPABASE_URL}/rest/v1/students?rno=eq.{rno}&select=*"
            headers = {
                'apikey': SUPABASE_KEY,
                'Authorization': f'Bearer {SUPABASE_KEY}',
                'Accept': 'application/json'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data:
                    db_student = data[0]
                    
                    # Use exact data from database
                    features = {
                        "performance_overall": float(db_student.get("performance_overall", 50)),
                        "risk_score": float(db_student.get("risk_score", 50)),
                        "dropout_score": float(db_student.get("dropout_score", 50)),
                        "attendance_pct": float(db_student.get("attendance_pct", 75)),
                        "behavior_pct": float(db_student.get("behavior_pct", 70)),
                        "internal_pct": float(db_student.get("internal_pct", 66)),
                        "present_att": (float(db_student.get("attended_days_curr", 80)) / float(db_student.get("total_days_curr", 90))) * 100,
                        "prev_att": float(db_student.get("prev_attendance_perc", 85)),
                        "past_avg": float(db_student.get("sem1", 0)) if float(db_student.get("sem1", 0)) > 0 else 70
                    }
                    
                    # Use exact predictions from database
                    predictions = {
                        "performance_label": str(db_student.get("performance_label", "medium")).lower(),
                        "risk_label": str(db_student.get("risk_label", "medium")).lower(),
                        "dropout_label": str(db_student.get("dropout_label", "medium")).lower()
                    }
                    
                    # Alert check
                    need_alert = (predictions["performance_label"] in ["poor", "low"] or 
                                 predictions["risk_label"] == "high" or 
                                 predictions["dropout_label"] == "high")
                    
                    return jsonify({
                        "success": True,
                        "student": student,
                        "features": features,
                        "predictions": predictions,
                        "need_alert": need_alert
                    })
        
        # Fallback for new students - calculate from input
        behavior_score = float(student.get("BEHAVIOR_SCORE_10", 5))
        internal_marks = float(student.get("INTERNAL_MARKS", 15))
        attended_days = float(student.get("ATTENDED_DAYS_CURR", 45))
        total_days = float(student.get("TOTAL_DAYS_CURR", 90))
        prev_att = float(student.get("PREV_ATTENDANCE_PERC", 75))
        
        behavior_pct = (behavior_score / 10.0) * 100
        internal_pct = (internal_marks / 30.0) * 100
        present_att = (attended_days / total_days) * 100 if total_days > 0 else 0
        
        perf_overall = (internal_pct * 0.4 + present_att * 0.4 + behavior_pct * 0.2)
        risk_score = 100 - perf_overall
        dropout_score = risk_score
        
        def get_performance_label(score):
            if score >= 75: return "high"
            elif score >= 50: return "medium"
            elif score >= 25: return "low"
            else: return "poor"
        
        def get_risk_label(score):
            if score >= 70: return "high"
            elif score >= 40: return "medium"
            else: return "low"
        
        sems = [float(student.get(f"SEM{i}", 0)) for i in range(1, 9)]
        past_avg = sum(s for s in sems if s > 0) / len([s for s in sems if s > 0]) if any(s > 0 for s in sems) else 0
        
        features = {
            "performance_overall": round(perf_overall, 1),
            "risk_score": round(risk_score, 1),
            "dropout_score": round(dropout_score, 1),
            "attendance_pct": round(present_att, 1),
            "behavior_pct": round(behavior_pct, 1),
            "internal_pct": round(internal_pct, 1),
            "present_att": round(present_att, 1),
            "prev_att": round(prev_att, 1),
            "past_avg": round(past_avg, 1)
        }
        
        predictions = {
            "performance_label": get_performance_label(perf_overall),
            "risk_label": get_risk_label(risk_score),
            "dropout_label": get_risk_label(dropout_score)
        }
        
        need_alert = (predictions["performance_label"] in ["poor", "low"] or 
                     predictions["risk_label"] == "high" or 
                     predictions["dropout_label"] == "high")
        
        return jsonify({
            "success": True,
            "student": student,
            "features": features,
            "predictions": predictions,
            "need_alert": need_alert
        })
        
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route("/api/send-alert", methods=["POST"])
def send_alert():
    try:
        data = request.get_json(silent=True) or {}
        mentor_email = data.get("mentor_email", "").strip()
        student_name = data.get("student_name", "Student")
        student_rno = data.get("student_rno", "N/A")
        performance = data.get("performance", "N/A")
        risk = data.get("risk", "N/A")
        dropout = data.get("dropout", "N/A")
        
        if not mentor_email:
            return jsonify({"success": False, "message": "Mentor email is required"}), 400
        
        # Email configuration
        smtp_server = "smtp.gmail.com"
        smtp_port = 587
        sender_email = os.getenv('EMAIL_USER')
        sender_password = os.getenv('EMAIL_PASSWORD')
        
        if not sender_email or not sender_password:
            return jsonify({"success": False, "message": "Email configuration missing"}), 500
        
        # Create message
        msg = MIMEMultipart('alternative')
        msg['From'] = sender_email
        msg['To'] = mentor_email
        msg['Subject'] = f"🚨 EduMetric Alert: {student_name} ({student_rno}) - Immediate Attention Required"
        
        # HTML email body with professional styling
        html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Student Alert</title>
</head>
<body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f5f5f5;">
    <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
        <!-- Header -->
        <div style="background: linear-gradient(135deg, #1976d2, #42a5f5); color: white; padding: 30px 20px; text-align: center;">
            <h1 style="margin: 0; font-size: 28px; font-weight: 600;">🚨 STUDENT ALERT</h1>
            <p style="margin: 10px 0 0 0; font-size: 16px; opacity: 0.9;">EduMetric - Intelligent Student Performance Analytics</p>
        </div>
        
        <!-- Alert Banner -->
        <div style="background-color: #fff3cd; border-left: 5px solid #ffc107; padding: 15px 20px; margin: 0;">
            <h2 style="margin: 0; color: #856404; font-size: 18px;">⚠️ IMMEDIATE ATTENTION REQUIRED</h2>
        </div>
        
        <!-- Student Information -->
        <div style="padding: 30px 20px;">
            <h3 style="color: #1976d2; margin: 0 0 20px 0; font-size: 20px; border-bottom: 2px solid #e3f2fd; padding-bottom: 10px;">👨‍🎓 Student Details</h3>
            
            <table style="width: 100%; border-collapse: collapse; margin-bottom: 25px;">
                <tr>
                    <td style="padding: 12px 0; border-bottom: 1px solid #e0e0e0; font-weight: 600; color: #424242; width: 40%;">📝 Student Name:</td>
                    <td style="padding: 12px 0; border-bottom: 1px solid #e0e0e0; color: #1976d2; font-weight: 600;">{student_name}</td>
                </tr>
                <tr>
                    <td style="padding: 12px 0; border-bottom: 1px solid #e0e0e0; font-weight: 600; color: #424242;">🆔 Register Number:</td>
                    <td style="padding: 12px 0; border-bottom: 1px solid #e0e0e0; color: #1976d2; font-weight: 600;">{student_rno}</td>
                </tr>
                <tr>
                    <td style="padding: 12px 0; border-bottom: 1px solid #e0e0e0; font-weight: 600; color: #424242;">📊 Performance Level:</td>
                    <td style="padding: 12px 0; border-bottom: 1px solid #e0e0e0;"><span style="background-color: #ffebee; color: #c62828; padding: 6px 12px; border-radius: 20px; font-weight: 600; text-transform: uppercase;">{performance.upper()}</span></td>
                </tr>
                <tr>
                    <td style="padding: 12px 0; border-bottom: 1px solid #e0e0e0; font-weight: 600; color: #424242;">⚠️ Risk Level:</td>
                    <td style="padding: 12px 0; border-bottom: 1px solid #e0e0e0;"><span style="background-color: #fff3e0; color: #ef6c00; padding: 6px 12px; border-radius: 20px; font-weight: 600; text-transform: uppercase;">{risk.upper()}</span></td>
                </tr>
                <tr>
                    <td style="padding: 12px 0; font-weight: 600; color: #424242;">🚪 Dropout Risk:</td>
                    <td style="padding: 12px 0;"><span style="background-color: #fce4ec; color: #ad1457; padding: 6px 12px; border-radius: 20px; font-weight: 600; text-transform: uppercase;">{dropout.upper()}</span></td>
                </tr>
            </table>
            
            <!-- Action Items -->
            <h3 style="color: #1976d2; margin: 30px 0 20px 0; font-size: 20px; border-bottom: 2px solid #e3f2fd; padding-bottom: 10px;">🎯 Recommended Actions</h3>
            
            <div style="background-color: #f8f9fa; border-radius: 8px; padding: 20px; margin-bottom: 25px;">
                <ul style="margin: 0; padding-left: 20px; line-height: 1.8;">
                    <li style="margin-bottom: 10px; color: #424242;"><strong>📅 Schedule an immediate one-on-one meeting</strong> within 24 hours</li>
                    <li style="margin-bottom: 10px; color: #424242;"><strong>📋 Review academic performance and attendance</strong> patterns</li>
                    <li style="margin-bottom: 10px; color: #424242;"><strong>🎓 Provide additional academic support</strong> and resources</li>
                    <li style="margin-bottom: 10px; color: #424242;"><strong>👥 Contact parents/guardians</strong> if necessary</li>
                    <li style="color: #424242;"><strong>📈 Monitor progress closely</strong> with weekly check-ins</li>
                </ul>
            </div>
            
            <!-- Urgency Notice -->
            <div style="background: linear-gradient(135deg, #f44336, #ef5350); color: white; padding: 20px; border-radius: 8px; text-align: center; margin-bottom: 25px;">
                <h4 style="margin: 0 0 10px 0; font-size: 18px;">⏰ TIME SENSITIVE</h4>
                <p style="margin: 0; font-size: 16px;">Please take appropriate action as soon as possible to support this student's academic success.</p>
            </div>
        </div>
        
        <!-- Footer -->
        <div style="background-color: #263238; color: white; padding: 25px 20px; text-align: center;">
            <p style="margin: 0 0 10px 0; font-size: 16px; font-weight: 600;">EduMetric System</p>
            <p style="margin: 0; font-size: 14px; opacity: 0.8;">Intelligent Student Performance Analytics Using Machine Learning</p>
            <p style="margin: 15px 0 0 0; font-size: 12px; opacity: 0.6;">This is an automated alert. Please do not reply to this email.</p>
        </div>
    </div>
</body>
</html>
        """
        
        # Plain text version for compatibility
        text_body = f"""
STUDENT ALERT - IMMEDIATE ATTENTION REQUIRED

Dear Mentor,

This is an automated alert from EduMetric regarding one of your mentees who requires immediate attention.

STUDENT DETAILS:
• Name: {student_name}
• Register Number: {student_rno}
• Performance Level: {performance.upper()}
• Risk Level: {risk.upper()}
• Dropout Risk: {dropout.upper()}

RECOMMENDED ACTIONS:
• Schedule an immediate one-on-one meeting within 24 hours
• Review academic performance and attendance patterns
• Provide additional academic support and resources
• Contact parents/guardians if necessary
• Monitor progress closely with weekly check-ins

Please take appropriate action as soon as possible to support this student's academic success.

Best regards,
EduMetric System
Intelligent Student Performance Analytics Using Machine Learning
        """
        
        # Attach both versions
        msg.attach(MIMEText(text_body, 'plain'))
        msg.attach(MIMEText(html_body, 'html'))
        
        # Send email
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        
        return jsonify({"success": True, "message": "Alert sent successfully"})
        
    except Exception as e:
        return jsonify({"success": False, "message": f"Failed to send alert: {str(e)}"}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)