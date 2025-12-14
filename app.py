import os
import numpy as np
import pandas as pd

from flask import Flask, jsonify, request, render_template
import joblib

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ===========================================================
# PATH SETUP
# ===========================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, r"data")

app = Flask(__name__)

# ===========================================================
# UNIVERSAL FIX: NUMPY/PANDAS → PYTHON TYPES
# ===========================================================
def to_py(obj):
    """Convert numpy/pandas types → pure Python types for JSON."""
    # numpy / pandas integers
    if isinstance(obj, (np.integer, np.int64, np.int32, np.int16)):  # type: ignore
        return int(obj)

    # numpy / pandas floats  → handle NaN / inf safely
    if isinstance(obj, (np.floating, np.float64, np.float32, np.float16)):  # type: ignore
        val = float(obj)
        if np.isnan(val) or np.isinf(val):
            return None
        return val

    # plain Python float (just in case)
    if isinstance(obj, float):
        if np.isnan(obj) or np.isinf(obj):
            return None
        return obj

    # pandas Series → dict
    if isinstance(obj, pd.Series):
        return {k: to_py(v) for k, v in obj.to_dict().items()}

    # pandas DataFrame → list of dicts
    if isinstance(obj, pd.DataFrame):
        return [to_py(r) for _, r in obj.iterrows()]

    # dict / list recursion
    if isinstance(obj, dict):
        return {k: to_py(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [to_py(v) for v in obj]

    return obj

# ===========================================================
# SAFE CSV & MODEL LOADING
# ===========================================================
def safe_read_csv(path):
    if not os.path.exists(path):
        print(f"[WARN] CSV not found: {path}")
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except Exception as e:
        print(f"[WARN] Could not read {path}: {e}")
        return pd.DataFrame()

# Load DS3 as primary data source
DS3 = safe_read_csv(os.path.join(DATA_DIR, r"DS3_full_report.csv"))
DS1 = safe_read_csv(os.path.join(DATA_DIR, r"DS1.csv"))
DS2 = safe_read_csv(os.path.join(DATA_DIR, r"DS2_ml_ready.csv"))

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

# ===========================================================
# FEATURE ENGINEERING
# ===========================================================
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

# ===========================================================
# MODEL PREDICTION
# ===========================================================
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
        return {
            "performance_label": "unknown",
            "risk_label": "unknown",
            "dropout_label": "unknown",
        }

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

# ===========================================================
# LOAD DS3 FOR ANALYTICS
# ===========================================================
def load_ds3_data():
    """Load DS3 full report dataset as primary data source"""
    global DS3
    
    # Try to load DS3 if not already loaded
    if DS3.empty:
        ds3_path = os.path.join(DATA_DIR, "DS3_full_report.csv")
        if os.path.exists(ds3_path):
            DS3 = safe_read_csv(ds3_path)
    
    # Clean DS3 data if it has issues
    if not DS3.empty:
        try:
            # Remove duplicate columns if they exist
            DS3 = DS3.loc[:, ~DS3.columns.duplicated()]
            
            # Ensure required columns exist
            required_cols = ['RNO', 'NAME', 'DEPT', 'YEAR', 'CURR_SEM']
            missing_cols = [col for col in required_cols if col not in DS3.columns]
            
            if missing_cols:
                print(f"[WARN] Missing columns in DS3: {missing_cols}")
                # Try fallback to DS1
                if not DS1.empty:
                    return DS1
                return pd.DataFrame()
            
            # Clean data types
            DS3['YEAR'] = pd.to_numeric(DS3['YEAR'], errors='coerce').fillna(1)
            DS3['CURR_SEM'] = pd.to_numeric(DS3['CURR_SEM'], errors='coerce').fillna(1)
            DS3['RNO'] = DS3['RNO'].astype(str).str.strip()
            DS3['NAME'] = DS3['NAME'].astype(str).str.strip()
            DS3['DEPT'] = DS3['DEPT'].astype(str).str.strip()
            
            return DS3
        except Exception as e:
            print(f"[WARN] Error cleaning DS3 data: {e}")
    
    # Fallback to DS1 if DS3 is not available or corrupted
    if not DS1.empty:
        return DS1
    
    # Last resort - return empty DataFrame
    return pd.DataFrame()

# ===========================================================
# GROUP ANALYSIS
# ===========================================================
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
            
            # Check if predictions already exist in DS3 data
            if ('performance_label' in st and 'risk_label' in st and 'dropout_label' in st and
                st.get('performance_label') not in [None, '', 'nan'] and
                st.get('risk_label') not in [None, '', 'nan'] and
                st.get('dropout_label') not in [None, '', 'nan']):
                # Use existing predictions from DS3
                perf_label = str(st.get('performance_label', 'unknown')).lower()
                risk_label = str(st.get('risk_label', 'unknown')).lower()
                drop_label = str(st.get('dropout_label', 'unknown')).lower()
                perf_score = float(st.get('performance_overall', 0.0) or 0.0)
                risk_score = float(st.get('risk_score', 0.0) or 0.0)
                drop_score = float(st.get('dropout_score', 0.0) or 0.0)
            else:
                # Compute predictions if not available
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
                    perf_label = 'unknown'
                    risk_label = 'unknown'
                    drop_label = 'unknown'
                    perf_score = 0.0
                    risk_score = 0.0
                    drop_score = 0.0

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

# ===========================================================
# ROUTES
# ===========================================================
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/stats")
def api_stats():
    try:
        # Use DS3 as primary data source
        data_source = load_ds3_data()
        if data_source.empty:
            print("[WARN] No data available in DS3")
            return jsonify({"total_students": 0, "departments": [], "years": []})
        
        print(f"[INFO] DS3 data loaded: {len(data_source)} students")
        
        try:
            departments = sorted(data_source["DEPT"].dropna().astype(str).unique().tolist())
            print(f"[INFO] Departments found: {departments}")
        except Exception as e:
            print(f"[WARN] Error getting departments: {e}")
            departments = []
        
        try:
            years = sorted(
                [int(y) for y in data_source["YEAR"].dropna().astype(float).astype(int).unique()]
            )
            print(f"[INFO] Years found: {years}")
        except Exception as e:
            print(f"[WARN] Error getting years: {e}")
            years = []
        
        return jsonify(
            {
                "total_students": int(len(data_source)),
                "departments": departments,
                "years": years,
            }
        )
    except Exception as e:
        print(f"[ERR] Stats API error: {e}")
        return jsonify({"total_students": 0, "departments": [], "years": []}), 500

@app.route("/api/student/search", methods=["POST"])
def api_student_search():
    data = request.get_json(silent=True) or {}
    rno = data.get("rno", "").strip()

    if not rno:
        return jsonify(
            {"success": False, "message": "Please provide Register Number."}
        ), 400

    # Use DS3 as primary data source
    data_source = load_ds3_data()
    
    # Search for student by RNO
    df = data_source[data_source["RNO"].astype(str).str.strip() == rno]

    if df.empty:
        return jsonify({"success": False, "message": "Student not found."}), 200

    # Get the first matching student
    student_raw = df.iloc[0].to_dict()
    
    # Extract only the required fields for prediction
    student_data = {
        "NAME": student_raw.get("NAME", ""),
        "RNO": student_raw.get("RNO", ""),
        "EMAIL": student_raw.get("EMAIL", ""),
        "DEPT": student_raw.get("DEPT", ""),
        "YEAR": safe_int(student_raw.get("YEAR", 0)),
        "CURR_SEM": safe_int(student_raw.get("CURR_SEM", 0)),
        "MENTOR": student_raw.get("MENTOR", ""),
        "MENTOR_EMAIL": student_raw.get("MENTOR_EMAIL", ""),
        "SEM1": student_raw.get("SEM1", 0.0) or 0.0,
        "SEM2": student_raw.get("SEM2", 0.0) or 0.0,
        "SEM3": student_raw.get("SEM3", 0.0) or 0.0,
        "SEM4": student_raw.get("SEM4", 0.0) or 0.0,
        "SEM5": student_raw.get("SEM5", 0.0) or 0.0,
        "SEM6": student_raw.get("SEM6", 0.0) or 0.0,
        "SEM7": student_raw.get("SEM7", 0.0) or 0.0,
        "SEM8": student_raw.get("SEM8", 0.0) or 0.0,
        "INTERNAL_MARKS": student_raw.get("INTERNAL_MARKS", 0.0) or 0.0,
        "TOTAL_DAYS_CURR": student_raw.get("TOTAL_DAYS_CURR", 0.0) or 0.0,
        "ATTENDED_DAYS_CURR": student_raw.get("ATTENDED_DAYS_CURR", 0.0) or 0.0,
        "PREV_ATTENDANCE_PERC": student_raw.get("PREV_ATTENDANCE_PERC", 0.0) or 0.0,
        "BEHAVIOR_SCORE_10": student_raw.get("BEHAVIOR_SCORE_10", 0.0) or 0.0
    }
    
    student = to_py(student_data)
    return jsonify({"success": True, "student": student})


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

        df = load_ds3_data().copy()
        
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

        df = load_ds3_data().copy()
        
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
        df = load_ds3_data().copy()
        
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

@app.route("/api/batch/analyze", methods=["POST"])
def api_batch_analyze():
    """Analyze batch performance data"""
    try:
        data = request.get_json(silent=True) or {}
        batch_year = data.get("batch_year")
        
        if not batch_year:
            return jsonify({"success": False, "message": "Batch year is required"}), 400
        
        df = load_ds3_data().copy()
        if df.empty:
            return jsonify({"success": False, "message": "No data available"}), 400
        
        # Filter by batch_year
        batch_df = df[df["batch_year"].fillna(0).astype(int) == int(batch_year)]
        
        if batch_df.empty:
            return jsonify({"success": False, "message": f"No students found for batch {batch_year}"}), 400
        
        # Calculate KPIs
        total_students = len(batch_df)
        avg_performance = float(batch_df["performance_overall"].fillna(0).mean())
        high_risk_count = len(batch_df[batch_df["risk_score"].fillna(0) > 70])
        high_risk_pct = (high_risk_count / total_students * 100) if total_students > 0 else 0
        avg_dropout = float(batch_df["dropout_score"].fillna(0).mean())
        top_performers = len(batch_df[batch_df["performance_label"] == "high"])
        top_performers_pct = (top_performers / total_students * 100) if total_students > 0 else 0
        
        # Distribution counts
        perf_counts = batch_df["performance_label"].fillna("unknown").value_counts().to_dict()
        risk_counts = batch_df["risk_label"].fillna("unknown").value_counts().to_dict()
        dropout_counts = batch_df["dropout_label"].fillna("unknown").value_counts().to_dict()
        
        # Semester trend data
        sem_cols = [f"SEM{i}" for i in range(1, 9)]
        sem_averages = []
        for sem in sem_cols:
            if sem in batch_df.columns:
                avg_mark = float(batch_df[sem].fillna(0).replace('', 0).astype(float).mean())
                sem_averages.append(avg_mark if avg_mark > 0 else None)
            else:
                sem_averages.append(None)
        
        # Generate insights
        insights = generate_batch_insights(batch_year, total_students, high_risk_pct, avg_performance, top_performers_pct)
        
        return jsonify({
            "success": True,
            "batch_year": batch_year,
            "stats": {
                "total_students": total_students,
                "avg_performance": round(avg_performance, 2),
                "high_risk_pct": round(high_risk_pct, 1),
                "avg_dropout": round(avg_dropout, 2),
                "top_performers_pct": round(top_performers_pct, 1)
            },
            "distributions": {
                "performance": perf_counts,
                "risk": risk_counts,
                "dropout": dropout_counts
            },
            "semester_trend": sem_averages,
            "insights": insights
        })
        
    except Exception as e:
        print(f"[ERR] Batch analysis: {e}")
        return jsonify({"success": False, "message": f"Analysis failed: {str(e)}"}), 500

@app.route("/api/batch/students", methods=["POST"])
def api_batch_students():
    """Get filtered students for batch drill-down"""
    try:
        data = request.get_json(silent=True) or {}
        batch_year = data.get("scope_value")
        filter_type = data.get("filter_type")
        filter_value = data.get("filter_value")
        
        if not all([batch_year, filter_type, filter_value]):
            return jsonify({"success": False, "message": "Missing required parameters"}), 400
        
        df = load_ds3_data().copy()
        if df.empty:
            return jsonify({"success": False, "message": "No data available"}), 400
        
        # Filter by batch_year and category
        filtered_df = df[
            (df["batch_year"].fillna(0).astype(int) == int(batch_year)) &
            (df[filter_type].fillna("unknown") == filter_value)
        ]
        
        # Prepare student list
        students = []
        for _, row in filtered_df.iterrows():
            student = {
                "RNO": str(row.get("RNO", "")),
                "NAME": str(row.get("NAME", "")),
                "DEPT": str(row.get("DEPT", "")),
                "YEAR": safe_int(row.get("YEAR", 0)),
                "batch_year": safe_int(row.get("batch_year", 0)),
                "performance_label": str(row.get("performance_label", "unknown")),
                "risk_label": str(row.get("risk_label", "unknown")),
                "dropout_label": str(row.get("dropout_label", "unknown"))
            }
            students.append(student)
        
        return jsonify({
            "success": True,
            "students": to_py(students),
            "count": len(students),
            "filter_info": {
                "batch_year": batch_year,
                "category": filter_type,
                "value": filter_value
            }
        })
        
    except Exception as e:
        print(f"[ERR] Batch students: {e}")
        return jsonify({"success": False, "message": f"Failed to get students: {str(e)}"}), 500

def generate_batch_insights(batch_year, total, high_risk_pct, avg_perf, top_perf_pct):
    """Generate batch insights and recommendations"""
    insights = []
    
    if high_risk_pct > 30:
        insights.append(f"⚠️ Critical: {high_risk_pct:.1f}% of students are high-risk. Immediate intervention required.")
    elif high_risk_pct > 15:
        insights.append(f"⚠️ Warning: {high_risk_pct:.1f}% of students are high-risk. Enhanced monitoring recommended.")
    else:
        insights.append(f"✅ Good: Only {high_risk_pct:.1f}% of students are high-risk.")
    
    if avg_perf < 60:
        insights.append(f"📉 Batch {batch_year} shows below-average performance ({avg_perf:.1f}%). Academic support needed.")
    elif avg_perf > 80:
        insights.append(f"📈 Excellent: Batch {batch_year} shows strong performance ({avg_perf:.1f}%).")
    
    if top_perf_pct < 20:
        insights.append(f"🎯 Focus needed: Only {top_perf_pct:.1f}% are top performers. Consider advanced programs.")
    
    # Recommendations
    recommendations = []
    if high_risk_pct > 20:
        recommendations.append("📋 Schedule immediate counseling sessions for high-risk students")
        recommendations.append("👥 Implement peer mentoring programs")
    
    if avg_perf < 70:
        recommendations.append("📚 Provide additional academic resources and tutoring")
        recommendations.append("🔄 Review curriculum delivery methods")
    
    return {
        "summary": f"Batch {batch_year} analysis: {total} students with {avg_perf:.1f}% average performance.",
        "insights": insights,
        "recommendations": recommendations
    }

@app.route("/api/send-alert", methods=["POST"])
def api_send_alert():
    data = request.get_json(silent=True) or {}
    to_email = data.get("email", "ashokkumarboya999@gmail.com")  # Default mentor email
    subject = data.get("subject")
    body = data.get("body")

    if not (subject and body):
        return jsonify({"success": False, "message": "Missing subject/body"}), 400

    FROM = "ashokkumarboya93@gmail.com"
    PASS = "lubwbacntoubetxb"  # use env var in real project

    msg = MIMEMultipart()
    msg["From"] = FROM
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(FROM, PASS)
        server.send_message(msg)
        server.quit()
        return jsonify({"success": True})
    except Exception as e:
        print("[ERR] send alert:", e)
        return jsonify({"success": False, "message": str(e)}), 500

# ===========================================================
# DS3 NORMALIZATION FUNCTIONS
# ===========================================================
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

def create_ds3_dataset(df_raw):
    """Create DS3 analytics-ready dataset from raw data"""
    ds3_rows = []
    
    for _, row in df_raw.iterrows():
        st = row.to_dict()
        feats = compute_features(st)
        preds = predict_student(feats)
        
        # Merge raw data + features + predictions
        ds3_row = st.copy()
        ds3_row.update(feats)
        ds3_row.update(preds)
        
        ds3_rows.append(ds3_row)
    
    return pd.DataFrame(ds3_rows)

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
    
    if 'risk_label' in data_source.columns:
        high_risk = len(data_source[data_source['risk_label'] == 'high'])
    if 'dropout_label' in data_source.columns:
        high_dropout = len(data_source[data_source['dropout_label'] == 'high'])
    
    # Get sample students for preview
    sample_students = []
    for _, row in data_source.head(100).iterrows():
        student = {
            'RNO': row.get('RNO', ''),
            'NAME': row.get('NAME', ''),
            'DEPT': row.get('DEPT', ''),
            'YEAR': safe_int(row.get('YEAR', 0)),
            'performance_label': row.get('performance_label', 'unknown'),
            'risk_label': row.get('risk_label', 'unknown'),
            'dropout_label': row.get('dropout_label', 'unknown')
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

@app.route("/api/batch-upload", methods=["POST"])
def api_batch_upload():
    global DS1, DS2, DS3
    
    if "file" not in request.files:
        return jsonify({"success": False, "message": "No file uploaded"}), 400
    
    file = request.files["file"]
    mode = request.form.get("mode", "normalize")
    
    if file.filename == "":
        return jsonify({"success": False, "message": "Empty filename"}), 400
    
    if not file.filename.endswith((".csv", ".xlsx")):
        return jsonify({"success": False, "message": "Invalid file type. Only CSV/XLSX allowed"}), 400
    
    try:
        # Read uploaded file
        if file.filename.endswith(".csv"):
            df_uploaded = pd.read_csv(file)
        else:
            df_uploaded = pd.read_excel(file)
        
        if df_uploaded.empty:
            return jsonify({"success": False, "message": "Empty file"}), 400
        
        processed_rows = len(df_uploaded)
        
        if mode == "normalize":
            # NORMALIZE MODE: Process raw DS1-style data
            df_clean = clean_data(df_uploaded)
            
            # Ensure RNO column exists and is properly formatted
            if 'RNO' not in df_clean.columns and 'reg_number' in df_clean.columns:
                df_clean['RNO'] = df_clean['reg_number']
            
            # Update DS1
            ds1_path = os.path.join(DATA_DIR, "DS1.csv")
            df_old = safe_read_csv(ds1_path)
            
            # Remove duplicates based on RNO before concatenating
            if not df_old.empty:
                df_all = pd.concat([df_old, df_clean], ignore_index=True)
                df_all.drop_duplicates(subset=["RNO"], keep="last", inplace=True)
            else:
                df_all = df_clean.copy()
            
            df_all.to_csv(ds1_path, index=False)
            DS1 = df_all
            
            # Create DS3 full report dataset with proper normalization
            ds3_data = create_ds3_dataset(df_clean)
            
            # Update DS3 full report with proper column alignment
            ds3_path = os.path.join(DATA_DIR, "DS3_full_report.csv")
            if os.path.exists(ds3_path):
                df_existing_ds3 = safe_read_csv(ds3_path)
                
                # Ensure column alignment
                if not df_existing_ds3.empty:
                    # Align columns
                    common_cols = list(set(df_existing_ds3.columns) & set(ds3_data.columns))
                    df_existing_ds3 = df_existing_ds3[common_cols]
                    ds3_data = ds3_data[common_cols]
                    
                    ds3_combined = pd.concat([df_existing_ds3, ds3_data], ignore_index=True)
                    ds3_combined.drop_duplicates(subset=["RNO"], keep="last", inplace=True)
                else:
                    ds3_combined = ds3_data.copy()
                    
                ds3_combined.to_csv(ds3_path, index=False)
                DS3 = ds3_combined
            else:
                ds3_data.to_csv(ds3_path, index=False)
                DS3 = ds3_data
            
            # Update DS2 (ML-ready)
            ds2_cols = ['RNO', 'NAME', 'DEPT', 'YEAR', 'CURR_SEM', 'past_avg', 'past_count',
                       'internal_pct', 'attendance_pct', 'behavior_pct', 'performance_trend',
                       'performance_label', 'risk_label', 'dropout_label', 'performance_overall',
                       'risk_score', 'dropout_score']
            available_cols = [col for col in ds2_cols if col in ds3_data.columns]
            ds2_data = ds3_data[available_cols].copy()
            
            ds2_path = os.path.join(DATA_DIR, "DS2_ml_ready.csv")
            ds2_data.to_csv(ds2_path, index=False)
            DS2 = ds2_data
            
            # Count added and updated records
            added = len(ds3_data)
            updated = len(df_all) - len(df_old) if not df_old.empty else 0
            
            return jsonify({
                "success": True,
                "mode": "normalize",
                "processed_rows": processed_rows,
                "added": added,
                "updated": updated,
                "total_records": len(DS3) if not DS3.empty else 0,
                "message": "Data normalized and predictions generated successfully"
            })
            
        else:
            # ANALYTICS MODE: Process already normalized data
            # Auto-detect if predictions are missing and compute them
            if 'performance_label' not in df_uploaded.columns:
                # Need to compute predictions
                ds3_data = create_ds3_dataset(df_uploaded)
            else:
                ds3_data = df_uploaded.copy()
            
            # Update DS3 full report
            ds3_path = os.path.join(DATA_DIR, "DS3_full_report.csv")
            if os.path.exists(ds3_path):
                df_existing_ds3 = safe_read_csv(ds3_path)
                if not df_existing_ds3.empty:
                    ds3_combined = pd.concat([df_existing_ds3, ds3_data], ignore_index=True)
                    ds3_combined.drop_duplicates(subset=["RNO"], keep="last", inplace=True)
                else:
                    ds3_combined = ds3_data.copy()
                ds3_combined.to_csv(ds3_path, index=False)
                DS3 = ds3_combined
            else:
                ds3_data.to_csv(ds3_path, index=False)
                DS3 = ds3_data
            
            return jsonify({
                "success": True,
                "mode": "analytics",
                "processed_rows": processed_rows,
                "total_students": len(DS3) if not DS3.empty else 0,
                "message": "Analytics data processed successfully"
            })
        
    except Exception as e:
        print(f"[ERR] batch upload: {e}")
        return jsonify({"success": False, "message": f"Upload failed: {str(e)}"}), 500

def send_dropout_alerts(high_dropout_students):
    """Send email alerts for high dropout risk students"""
    alerts_sent = 0
    
    for student in high_dropout_students:
        try:
            FROM = "ashokkumarboya93@gmail.com"
            PASS = "lubwbacntoubetxb"
            
            msg = MIMEMultipart()
            msg["From"] = FROM
            msg["To"] = student["email"]
            msg["Subject"] = f"Alert: High Dropout Risk - {student['name']}"
            body = f"""Dear Mentor,

This is an automated alert regarding student {student['name']} (RNO: {student['rno']}).

The student has been identified as HIGH DROPOUT RISK with a dropout score of {student['dropout_score']}.

Please take immediate action to counsel and support the student.

Best regards,
Student Analytics System"""
            msg.attach(MIMEText(body, "plain"))
            
            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.starttls()
            server.login(FROM, PASS)
            server.send_message(msg)
            server.quit()
            alerts_sent += 1
        except Exception as e:
            print(f"[WARN] Email failed for {student['email']}: {e}")
    
    return alerts_sent

# ===========================================================
# CRUD API ENDPOINTS
# ===========================================================

@app.route("/api/student/create", methods=["POST"])
def api_create_student():
    """Create a new student record"""
    global DS1, DS3
    
    try:
        data = request.get_json(silent=True) or {}
        
        # Validate required fields
        required_fields = ['NAME', 'RNO', 'EMAIL', 'DEPT', 'YEAR', 'CURR_SEM']
        for field in required_fields:
            if not data.get(field):
                return jsonify({"success": False, "message": f"{field} is required"}), 400
        
        # Check if student already exists
        data_source = load_ds3_data()
        if not data_source.empty:
            existing = data_source[data_source["RNO"].astype(str).str.strip() == str(data.get("RNO")).strip()]
            if not existing.empty:
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
        
        # Add to DS1
        ds1_path = os.path.join(DATA_DIR, "DS1.csv")
        if os.path.exists(ds1_path):
            DS1 = safe_read_csv(ds1_path)
            new_ds1 = pd.concat([DS1, pd.DataFrame([student_data])], ignore_index=True)
        else:
            new_ds1 = pd.DataFrame([student_data])
        
        new_ds1.to_csv(ds1_path, index=False)
        DS1 = new_ds1
        
        # Add to DS3
        ds3_path = os.path.join(DATA_DIR, "DS3_full_report.csv")
        if os.path.exists(ds3_path):
            DS3 = safe_read_csv(ds3_path)
            new_ds3 = pd.concat([DS3, pd.DataFrame([full_record])], ignore_index=True)
        else:
            new_ds3 = pd.DataFrame([full_record])
        
        new_ds3.to_csv(ds3_path, index=False)
        DS3 = new_ds3
        
        return jsonify({
            "success": True,
            "message": "Student created successfully",
            "student": to_py(full_record)
        })
        
    except Exception as e:
        print(f"[ERR] Create student: {e}")
        return jsonify({"success": False, "message": f"Failed to create student: {str(e)}"}), 500

@app.route("/api/student/read", methods=["POST"])
def api_read_student():
    """Read/search student records"""
    try:
        data = request.get_json(silent=True) or {}
        rno = data.get("rno", "").strip()
        name = data.get("name", "").strip()
        
        if not rno and not name:
            return jsonify({"success": False, "message": "Please provide RNO or Name to search"}), 400
        
        data_source = load_ds3_data()
        if data_source.empty:
            return jsonify({"success": False, "message": "No student data available"}), 400
        
        # Search by RNO or Name
        if rno:
            results = data_source[data_source["RNO"].astype(str).str.strip().str.contains(rno, case=False, na=False)]
        else:
            results = data_source[data_source["NAME"].astype(str).str.strip().str.contains(name, case=False, na=False)]
        
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
    """Update existing student record"""
    global DS1, DS3
    
    try:
        data = request.get_json(silent=True) or {}
        rno = data.get("RNO", "").strip()
        
        if not rno:
            return jsonify({"success": False, "message": "RNO is required for update"}), 400
        
        # Find student in DS3
        data_source = load_ds3_data()
        if data_source.empty:
            return jsonify({"success": False, "message": "No student data available"}), 400
        
        student_idx = data_source[data_source["RNO"].astype(str).str.strip() == rno].index
        if len(student_idx) == 0:
            return jsonify({"success": False, "message": "Student not found"}), 404
        
        # Update student data
        idx = student_idx[0]
        updated_data = {
            'NAME': str(data.get('NAME', data_source.loc[idx, 'NAME'])).strip(),
            'EMAIL': str(data.get('EMAIL', data_source.loc[idx, 'EMAIL'])).strip(),
            'DEPT': str(data.get('DEPT', data_source.loc[idx, 'DEPT'])).strip(),
            'YEAR': safe_int(data.get('YEAR', data_source.loc[idx, 'YEAR'])),
            'CURR_SEM': safe_int(data.get('CURR_SEM', data_source.loc[idx, 'CURR_SEM'])),
            'MENTOR': str(data.get('MENTOR', data_source.loc[idx, 'MENTOR'] if 'MENTOR' in data_source.columns else '')).strip(),
            'MENTOR_EMAIL': str(data.get('MENTOR_EMAIL', data_source.loc[idx, 'MENTOR_EMAIL'] if 'MENTOR_EMAIL' in data_source.columns else '')).strip(),
            'SEM1': float(data.get('SEM1', data_source.loc[idx, 'SEM1'] if 'SEM1' in data_source.columns else 0) or 0),
            'SEM2': float(data.get('SEM2', data_source.loc[idx, 'SEM2'] if 'SEM2' in data_source.columns else 0) or 0),
            'SEM3': float(data.get('SEM3', data_source.loc[idx, 'SEM3'] if 'SEM3' in data_source.columns else 0) or 0),
            'SEM4': float(data.get('SEM4', data_source.loc[idx, 'SEM4'] if 'SEM4' in data_source.columns else 0) or 0),
            'SEM5': float(data.get('SEM5', data_source.loc[idx, 'SEM5'] if 'SEM5' in data_source.columns else 0) or 0),
            'SEM6': float(data.get('SEM6', data_source.loc[idx, 'SEM6'] if 'SEM6' in data_source.columns else 0) or 0),
            'SEM7': float(data.get('SEM7', data_source.loc[idx, 'SEM7'] if 'SEM7' in data_source.columns else 0) or 0),
            'SEM8': float(data.get('SEM8', data_source.loc[idx, 'SEM8'] if 'SEM8' in data_source.columns else 0) or 0),
            'INTERNAL_MARKS': float(data.get('INTERNAL_MARKS', data_source.loc[idx, 'INTERNAL_MARKS'] if 'INTERNAL_MARKS' in data_source.columns else 20) or 20),
            'TOTAL_DAYS_CURR': float(data.get('TOTAL_DAYS_CURR', data_source.loc[idx, 'TOTAL_DAYS_CURR'] if 'TOTAL_DAYS_CURR' in data_source.columns else 90) or 90),
            'ATTENDED_DAYS_CURR': float(data.get('ATTENDED_DAYS_CURR', data_source.loc[idx, 'ATTENDED_DAYS_CURR'] if 'ATTENDED_DAYS_CURR' in data_source.columns else 80) or 80),
            'PREV_ATTENDANCE_PERC': float(data.get('PREV_ATTENDANCE_PERC', data_source.loc[idx, 'PREV_ATTENDANCE_PERC'] if 'PREV_ATTENDANCE_PERC' in data_source.columns else 85) or 85),
            'BEHAVIOR_SCORE_10': float(data.get('BEHAVIOR_SCORE_10', data_source.loc[idx, 'BEHAVIOR_SCORE_10'] if 'BEHAVIOR_SCORE_10' in data_source.columns else 7) or 7)
        }
        
        # Recompute features and predictions
        feats = compute_features(updated_data)
        preds = predict_student(feats)
        
        # Update DS3
        for key, value in updated_data.items():
            if key in data_source.columns:
                data_source.loc[idx, key] = value
        
        for key, value in feats.items():
            if key in data_source.columns:
                data_source.loc[idx, key] = value
        
        for key, value in preds.items():
            if key in data_source.columns:
                data_source.loc[idx, key] = value
        
        # Save DS3
        ds3_path = os.path.join(DATA_DIR, "DS3_full_report.csv")
        data_source.to_csv(ds3_path, index=False)
        DS3 = data_source
        
        # Update DS1 if exists
        ds1_path = os.path.join(DATA_DIR, "DS1.csv")
        if os.path.exists(ds1_path):
            DS1 = safe_read_csv(ds1_path)
            ds1_idx = DS1[DS1["RNO"].astype(str).str.strip() == rno].index
            if len(ds1_idx) > 0:
                for key, value in updated_data.items():
                    if key in DS1.columns:
                        DS1.loc[ds1_idx[0], key] = value
                DS1.to_csv(ds1_path, index=False)
        
        # Prepare response
        full_record = updated_data.copy()
        full_record.update(feats)
        full_record.update(preds)
        full_record['RNO'] = rno
        
        return jsonify({
            "success": True,
            "message": "Student updated successfully",
            "student": to_py(full_record)
        })
        
    except Exception as e:
        print(f"[ERR] Update student: {e}")
        return jsonify({"success": False, "message": f"Failed to update student: {str(e)}"}), 500

@app.route("/api/student/delete", methods=["POST"])
def api_delete_student():
    """Delete student record"""
    global DS1, DS3
    
    try:
        data = request.get_json(silent=True) or {}
        rno = data.get("rno", "").strip()
        
        if not rno:
            return jsonify({"success": False, "message": "RNO is required for deletion"}), 400
        
        # Find and delete from DS3
        data_source = load_ds3_data()
        if data_source.empty:
            return jsonify({"success": False, "message": "No student data available"}), 400
        
        student_rows = data_source[data_source["RNO"].astype(str).str.strip() == rno]
        if student_rows.empty:
            return jsonify({"success": False, "message": "Student not found"}), 404
        
        # Get student info before deletion
        student_info = student_rows.iloc[0].to_dict()
        
        # Remove from DS3
        data_source = data_source[data_source["RNO"].astype(str).str.strip() != rno]
        ds3_path = os.path.join(DATA_DIR, "DS3_full_report.csv")
        data_source.to_csv(ds3_path, index=False)
        DS3 = data_source
        
        # Remove from DS1 if exists
        ds1_path = os.path.join(DATA_DIR, "DS1.csv")
        if os.path.exists(ds1_path):
            DS1 = safe_read_csv(ds1_path)
            DS1 = DS1[DS1["RNO"].astype(str).str.strip() != rno]
            DS1.to_csv(ds1_path, index=False)
        
        return jsonify({
            "success": True,
            "message": f"Student {student_info.get('NAME', '')} ({rno}) deleted successfully",
            "deleted_student": {
                "RNO": rno,
                "NAME": str(student_info.get('NAME', '')),
                "DEPT": str(student_info.get('DEPT', '')),
                "YEAR": safe_int(student_info.get('YEAR', 0))
            }
        })
        
    except Exception as e:
        print(f"[ERR] Delete student: {e}")
        return jsonify({"success": False, "message": f"Failed to delete student: {str(e)}"}), 500

@app.route("/api/students/list", methods=["GET"])
def api_list_students():
    """List all students with pagination"""
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 50))
        dept_filter = request.args.get('dept', '')
        year_filter = request.args.get('year', '')
        
        data_source = load_ds3_data()
        if data_source.empty:
            return jsonify({"success": False, "message": "No student data available"})
        
        # Apply filters
        filtered_data = data_source.copy()
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

@app.route("/api/batch-analytics", methods=["POST"])
def api_batch_analytics():
    data = request.get_json(silent=True) or {}
    batch_year = data.get("batch_year", "2025")
    
    try:
        ds2_path = os.path.join(DATA_DIR, "DS2_ml_ready.csv")
        if not os.path.exists(ds2_path):
            return jsonify({"success": False, "message": "No analytics data available"}), 400
        
        df = pd.read_csv(ds2_path)
        df['batch_year'] = df['YEAR'].apply(lambda x: 2022 + int(x) if pd.notna(x) else 2025)
        batch_df = df[df['batch_year'] == int(batch_year)]
        
        if batch_df.empty:
            return jsonify({"success": False, "message": f"No data found for batch {batch_year}"}), 400
        
        total_students = len(batch_df)
        avg_performance = batch_df['performance_overall'].mean()
        high_risk_count = len(batch_df[batch_df['risk_score'] > 70])
        high_risk_pct = (high_risk_count / total_students) * 100
        dropout_avg = batch_df['dropout_score'].mean()
        top_performers = len(batch_df[batch_df['performance_label'] == 'high'])
        top_performers_pct = (top_performers / total_students) * 100
        
        perf_dist = batch_df['performance_label'].value_counts().to_dict()
        risk_dist = batch_df['risk_label'].value_counts().to_dict()
        dropout_dist = batch_df['dropout_label'].value_counts().to_dict()
        
        sem_cols = ['SEM1', 'SEM2', 'SEM3', 'SEM4', 'SEM5', 'SEM6', 'SEM7', 'SEM8']
        sem_trends = []
        for sem in sem_cols:
            if sem in batch_df.columns:
                avg_marks = batch_df[sem].dropna().mean()
                sem_trends.append(avg_marks if not pd.isna(avg_marks) else 0)
            else:
                sem_trends.append(0)
        
        declining_students = 0
        for _, row in batch_df.iterrows():
            sem_marks = [row.get(f'SEM{i}', 0) for i in range(1, 9) if pd.notna(row.get(f'SEM{i}', 0)) and row.get(f'SEM{i}', 0) > 0]
            if len(sem_marks) >= 2 and sem_marks[-1] < sem_marks[0]:
                declining_students += 1
        
        declining_pct = (declining_students / total_students) * 100
        silent_risk = len(batch_df[(batch_df['performance_label'] == 'medium') & (batch_df['dropout_label'] == 'high')])
        low_att_high_risk = len(batch_df[(batch_df['attendance_pct'] < 75) & (batch_df['risk_label'] == 'high')])
        
        return jsonify({
            "success": True,
            "batch_year": batch_year,
            "kpis": {
                "total_students": total_students,
                "avg_performance": round(avg_performance, 1),
                "high_risk_pct": round(high_risk_pct, 1),
                "dropout_avg": round(dropout_avg, 1),
                "top_performers_pct": round(top_performers_pct, 1)
            },
            "distributions": {
                "performance": perf_dist,
                "risk": risk_dist,
                "dropout": dropout_dist
            },
            "trends": {
                "semesters": ['SEM1', 'SEM2', 'SEM3', 'SEM4', 'SEM5', 'SEM6', 'SEM7', 'SEM8'],
                "marks": sem_trends
            },
            "deep_analytics": {
                "declining_pct": round(declining_pct, 1),
                "silent_risk": silent_risk,
                "attendance_risk_correlation": low_att_high_risk
            }
        })
        
    except Exception as e:
        print(f"[ERR] batch analytics: {e}")
        return jsonify({"success": False, "message": f"Analysis failed: {str(e)}"}), 500

@app.route("/api/analytics/drilldown", methods=["POST"])
def api_analytics_drilldown():
    """Universal drill-down API for all analytics views"""
    try:
        data = request.get_json(silent=True) or {}
        filter_type = data.get("filter_type")
        filter_value = data.get("filter_value")
        scope = data.get("scope", "all")
        scope_value = data.get("scope_value")
        
        # Use DS3 as primary data source
        df = load_ds3_data()
        if df.empty:
            return jsonify({"success": False, "message": "No data available"}), 400
        
        # Apply scope filter first
        if scope != "all" and scope_value:
            if scope == "student":
                df = df[df["RNO"].astype(str).str.strip() == str(scope_value)]
            elif scope == "dept":
                df = df[df["DEPT"].astype(str).str.strip() == str(scope_value)]
            elif scope == "year":
                df = df[df["YEAR"].fillna(0).astype(int) == int(scope_value)]
            elif scope == "batch":
                df = df[df["batch_year"].fillna(0).astype(int) == int(scope_value)]
            elif scope == "college":
                # No additional filter for college-wide
                pass
        
        # Apply category filter
        if filter_type and filter_value and filter_type in df.columns:
            df = df[df[filter_type].fillna("unknown") == filter_value]
        
        # Prepare student list with required columns only
        students = []
        for _, row in df.iterrows():
            student = {
                "RNO": str(row.get("RNO", "")),
                "NAME": str(row.get("NAME", "")),
                "DEPT": str(row.get("DEPT", "")),
                "YEAR": safe_int(row.get("YEAR", 0)),
                "batch_year": safe_int(row.get("batch_year", 0)),
                "performance_label": str(row.get("performance_label", "unknown")),
                "risk_label": str(row.get("risk_label", "unknown")),
                "dropout_label": str(row.get("dropout_label", "unknown"))
            }
            students.append(student)
        
        return jsonify({
            "success": True,
            "students": to_py(students),
            "count": len(students),
            "filter_info": {
                "filter_type": filter_type,
                "filter_value": filter_value,
                "scope": scope,
                "scope_value": scope_value
            }
        })
        
    except Exception as e:
        print(f"[ERR] Universal drilldown: {e}")
        return jsonify({"success": False, "message": f"Drilldown failed: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(debug=True)
