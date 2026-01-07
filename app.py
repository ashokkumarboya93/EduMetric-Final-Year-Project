import os
from flask import Flask, jsonify, render_template
from simple_db import load_students_df, get_stats

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'fallback-key')

def compute_features(student_row):
    curr_sem = int(student_row.get("CURR_SEM", 1) or 1)
    
    # Past semester marks
    past = []
    for i in range(1, curr_sem):
        key = f"SEM{i}"
        v = student_row.get(key)
        if v not in (None, "", "nan") and str(v).replace('.','').isdigit():
            past.append(float(v))
    
    past_avg = float(sum(past) / len(past)) if past else 0.0
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
        past_avg * 0.50 + internal_pct * 0.30 + attendance_pct * 0.15 + behavior_pct * 0.05
    )
    
    risk_score = abs(100.0 - performance_overall)
    dropout_score = abs(100.0 - (past_avg * 0.10 + internal_pct * 0.10 + attendance_pct * 0.70 + behavior_pct * 0.10))
    
    return {
        "performance_overall": round(performance_overall, 2),
        "risk_score": round(risk_score, 2),
        "dropout_score": round(dropout_score, 2),
        "attendance_pct": round(attendance_pct, 2)
    }

def predict_student(features):
    perf = features["performance_overall"]
    attendance = features["attendance_pct"]
    
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

@app.route("/")
def index():
    stats = get_stats()
    return render_template('index.html', 
                         DEBUG=False,
                         departments=stats.get('departments', []), 
                         years=stats.get('years', []))

@app.route("/api/analytics/preview")
def api_analytics_preview():
    try:
        df = load_students_df()
        students = []
        
        for _, row in df.head(10).iterrows():
            student_dict = row.to_dict()
            
            # Compute features and predictions
            features = compute_features(student_dict)
            predictions = predict_student(features)
            
            students.append({
                "RNO": str(student_dict.get("RNO", "")),
                "Name": str(student_dict.get("NAME", "")),
                "Year": int(student_dict.get("YEAR", 0) or 0),
                "Sem": int(student_dict.get("CURR_SEM", 0) or 0),
                "Perf": predictions["performance_label"],
                "Risk": predictions["risk_label"],
                "Dropout": predictions["dropout_label"],
                "Perf%": f"{features['performance_overall']:.1f}%",
                "Risk%": f"{features['risk_score']:.1f}%",
                "Drop%": f"{features['dropout_score']:.1f}%"
            })
        
        return jsonify({
            "success": True,
            "stats": {
                "total_students": len(df),
                "high_risk": sum(1 for s in students if s["Risk"] == "HIGH"),
                "high_dropout": sum(1 for s in students if s["Dropout"] == "HIGH")
            },
            "students": students
        })
    except Exception as e:
        print(f"Analytics preview error: {e}")
        return jsonify({"success": False, "message": str(e)})

@app.route("/api/stats")
def api_stats():
    return jsonify(get_stats())

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)