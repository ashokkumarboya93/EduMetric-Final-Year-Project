import os
import numpy as np
import pandas as pd
from flask import Flask, jsonify, request, render_template
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'fallback-key')

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

def get_supabase_data():
    """Get data directly from Supabase"""
    try:
        url = f"{SUPABASE_URL}/rest/v1/students?select=*"
        headers = {
            'apikey': SUPABASE_KEY,
            'Authorization': f'Bearer {SUPABASE_KEY}',
            'Accept': 'application/json'
        }
        
        print(f"Fetching data from: {url}")
        response = requests.get(url, headers=headers, timeout=10)
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Found {len(data)} records")
            if data:
                df = pd.DataFrame(data)
                df.columns = df.columns.str.upper()
                print(f"DataFrame shape: {df.shape}")
                print(f"Columns: {list(df.columns)[:10]}...")  # Show first 10 columns
                return df
        else:
            print(f"Error response: {response.text[:200]}")
        
        print("Returning empty DataFrame")
        return pd.DataFrame()
        
    except Exception as e:
        print(f"Connection error: {e}")
        return pd.DataFrame()

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
            st = row.to_dict()
            
            # Skip if missing essential data
            if not st.get('RNO') or not st.get('NAME'):
                continue
            
            # Use existing predictions if available, otherwise compute
            if (st.get('PERFORMANCE_LABEL') and st.get('RISK_LABEL') and st.get('DROPOUT_LABEL') and
                st.get('PERFORMANCE_OVERALL') is not None):
                # Use existing data
                perf_label = str(st.get('PERFORMANCE_LABEL', 'medium')).lower()
                risk_label = str(st.get('RISK_LABEL', 'medium')).lower()
                drop_label = str(st.get('DROPOUT_LABEL', 'medium')).lower()
                perf_score = float(st.get('PERFORMANCE_OVERALL', 50) or 50)
                risk_score = float(st.get('RISK_SCORE', 50) or 50)
                drop_score = float(st.get('DROPOUT_SCORE', 50) or 50)
            else:
                # Compute new predictions
                try:
                    features = compute_features(st)
                    predictions = predict_student(features)
                    perf_label = predictions["performance_label"]
                    risk_label = predictions["risk_label"]
                    drop_label = predictions["dropout_label"]
                    perf_score = features["performance_overall"]
                    risk_score = features["risk_score"]
                    drop_score = features["dropout_score"]
                except Exception as e:
                    print(f"Prediction error for {st.get('RNO')}: {e}")
                    # Use safe defaults
                    perf_label, risk_label, drop_label = 'medium', 'medium', 'medium'
                    perf_score, risk_score, drop_score = 50.0, 50.0, 50.0
            
            perf_labels.append(perf_label)
            risk_labels.append(risk_label)
            drop_labels.append(drop_label)
            perf_scores.append(float(perf_score))

            table.append({
                "RNO": str(st.get("RNO", "")),
                "NAME": str(st.get("NAME", "")),
                "DEPT": str(st.get("DEPT", "")),
                "YEAR": int(st.get("YEAR", 0) or 0),
                "CURR_SEM": int(st.get("CURR_SEM", 0) or 0),
                "performance_label": perf_label,
                "risk_label": risk_label,
                "dropout_label": drop_label,
                "performance_overall": float(perf_score),
                "risk_score": float(risk_score),
                "dropout_score": float(drop_score)
            })
        except Exception as e:
            print(f"Error processing student row: {e}")
            continue

    if not table:
        return {
            "stats": {"total_students": 0, "high_performers": 0, "high_risk": 0, "high_dropout": 0, "avg_performance": 0.0},
            "label_counts": {"performance": {}, "risk": {}, "dropout": {}},
            "table": []
        }

    try:
        stats = {
            "total_students": len(table),
            "high_performers": perf_labels.count("high"),
            "high_risk": risk_labels.count("high"),
            "high_dropout": drop_labels.count("high"),
            "avg_performance": round(float(np.mean(perf_scores)) if perf_scores else 0.0, 2)
        }

        label_counts = {
            "performance": {k: perf_labels.count(k) for k in set(perf_labels) if k},
            "risk": {k: risk_labels.count(k) for k in set(risk_labels) if k},
            "dropout": {k: drop_labels.count(k) for k in set(drop_labels) if k}
        }

        return {"stats": stats, "label_counts": label_counts, "table": table}
    except Exception as e:
        print(f"Stats computation error: {e}")
        return {
            "stats": {"total_students": len(table), "high_performers": 0, "high_risk": 0, "high_dropout": 0, "avg_performance": 0.0},
            "label_counts": {"performance": {}, "risk": {}, "dropout": {}},
            "table": table
        }

@app.route("/")
def index():
    try:
        df = get_supabase_data()
        departments = df['DEPT'].unique().tolist() if not df.empty and 'DEPT' in df.columns else ['CSE', 'ECE', 'MECH']
        years = df['YEAR'].unique().tolist() if not df.empty and 'YEAR' in df.columns else [1, 2, 3, 4]
        
        return render_template('index.html', 
                             DEBUG=True,
                             departments=sorted(departments), 
                             years=sorted([int(y) for y in years if str(y).isdigit()]))
    except Exception as e:
        print(f"Index error: {e}")
        return render_template('index.html', DEBUG=True, departments=['CSE', 'ECE'], years=[1, 2, 3, 4])

@app.route("/api/stats")
def api_stats():
    try:
        df = get_supabase_data()
        if df.empty:
            return jsonify({"total_students": 0, "departments": [], "years": []})
        
        departments = df['DEPT'].unique().tolist() if 'DEPT' in df.columns else []
        years = df['YEAR'].unique().tolist() if 'YEAR' in df.columns else []
        
        return jsonify({
            'total_students': len(df),
            'departments': sorted(departments),
            'years': sorted([int(y) for y in years if str(y).isdigit()])
        })
    except Exception as e:
        print(f"Stats error: {e}")
        return jsonify({"total_students": 0, "departments": [], "years": []}), 500

@app.route("/api/department/analyze", methods=["POST"])
def api_dept():
    try:
        data = request.get_json(silent=True) or {}
        dept = data.get("dept", None)
        year = data.get("year", None)

        print(f"Department analysis request: dept={dept}, year={year}")
        
        df = get_supabase_data()
        print(f"Loaded {len(df)} total records")
        
        if df.empty:
            return jsonify({"success": False, "message": "No data available"}), 400
        
        # Filter by department
        if dept and dept != "":
            print(f"Filtering by department: {dept}")
            df = df[df["DEPT"].astype(str).str.strip().str.upper() == str(dept).strip().upper()]
            print(f"After dept filter: {len(df)} records")

        # Filter by year
        if year not in (None, "", "all"):
            try:
                year_int = int(year)
                print(f"Filtering by year: {year_int}")
                df = df[df["YEAR"].fillna(0).astype(str).astype(int) == year_int]
                print(f"After year filter: {len(df)} records")
            except Exception as e:
                print(f"Year filter error: {e}")
                return jsonify({"success": False, "message": "Invalid year filter"}), 400

        if df.empty:
            return jsonify({"success": False, "message": "No students found for the selected criteria"}), 400

        print("Starting analysis...")
        res = analyze_subset(df)
        print("Analysis completed successfully")
        return jsonify({"success": True, **res})
    except Exception as e:
        print(f"Department analysis error: {e}")
        import traceback
        traceback.print_exc()
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

        df = get_supabase_data()
        
        if df.empty:
            return jsonify({"success": False, "message": "No data available"}), 400
        
        df = df[df["YEAR"].fillna(0).astype(int) == year_int]

        if df.empty:
            return jsonify({"success": False, "message": f"No students found for year {year_int}"}), 400

        res = analyze_subset(df)
        return jsonify({"success": True, **res})
    except Exception as e:
        print(f"Year analysis error: {e}")
        return jsonify({"success": False, "message": f"Analysis failed: {str(e)}"}), 500

@app.route("/api/college/analyze")
def api_college():
    try:
        df = get_supabase_data()
        
        if df.empty:
            return jsonify({"success": False, "message": "No data available"}), 400
        
        # Sample data if too large
        original_size = len(df)
        if len(df) > 500:
            df = df.sample(min(500, len(df)), random_state=42)

        res = analyze_subset(df)
        res["sample_size"] = int(len(df))
        res["total_size"] = int(original_size)
        return jsonify({"success": True, **res})
    except Exception as e:
        print(f"College analysis error: {e}")
        return jsonify({"success": False, "message": f"Analysis failed: {str(e)}"}), 500

@app.route("/api/student/search", methods=["POST"])
def api_student_search():
    try:
        data = request.get_json(silent=True) or {}
        rno = data.get("rno", "").strip()

        if not rno:
            return jsonify({"success": False, "message": "Please provide Register Number."}), 400

        # Get student from Supabase
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
                # Convert keys to uppercase
                student_data = {k.upper(): v for k, v in student.items()}
                
                # Ensure all required fields exist
                required_fields = {
                    "NAME": "", "RNO": "", "EMAIL": "", "DEPT": "", "YEAR": 0, "CURR_SEM": 0,
                    "MENTOR": "", "MENTOR_EMAIL": "", "SEM1": 0, "SEM2": 0, "SEM3": 0, "SEM4": 0,
                    "SEM5": 0, "SEM6": 0, "SEM7": 0, "SEM8": 0, "INTERNAL_MARKS": 20,
                    "TOTAL_DAYS_CURR": 90, "ATTENDED_DAYS_CURR": 80, "PREV_ATTENDANCE_PERC": 85,
                    "BEHAVIOR_SCORE_10": 7
                }
                
                for field, default in required_fields.items():
                    if field not in student_data or student_data[field] is None:
                        student_data[field] = default
                
                return jsonify({"success": True, "student": student_data})
        
        return jsonify({"success": False, "message": "Student not found."}), 404
        
    except Exception as e:
        print(f"Student search error: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

@app.route("/api/student/predict", methods=["POST"])
def api_student_predict():
    try:
        student = request.get_json(silent=True) or {}
        
        # Compute features and predictions
        features = compute_features(student)
        predictions = predict_student(features)

        # Check if student needs mentor alert
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
        print(f"Student prediction error: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)