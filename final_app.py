import os
import pandas as pd
from flask import Flask, jsonify, request, render_template
import requests
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'fallback-key')

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

def get_supabase_data():
    """Fetch all data from Supabase"""
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
                print(f"SUCCESS: Loaded {len(df)} records from Supabase")
                return df
        
        print("WARNING: No data received from Supabase")
        return pd.DataFrame()
        
    except Exception as e:
        print(f"ERROR: Supabase error: {e}")
        return pd.DataFrame()

def analyze_data(df):
    """Analyze student data"""
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
            # Use existing Supabase data
            perf_label = str(row.get('PERFORMANCE_LABEL', 'medium')).lower()
            risk_label = str(row.get('RISK_LABEL', 'medium')).lower()
            drop_label = str(row.get('DROPOUT_LABEL', 'medium')).lower()
            
            # Convert performance score
            perf_score = float(str(row.get('PERFORMANCE_OVERALL', 50)).replace('', '50'))
            
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
        except Exception as e:
            continue

    # Calculate statistics
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
def home():
    try:
        df = get_supabase_data()
        departments = sorted(df['DEPT'].unique().tolist()) if not df.empty and 'DEPT' in df.columns else ['CSE', 'ECE', 'MECH']
        years = sorted(df['YEAR'].unique().tolist()) if not df.empty and 'YEAR' in df.columns else ['1', '2', '3', '4']
        
        return render_template('index.html', 
                             DEBUG=True,
                             departments=departments, 
                             years=years)
    except Exception as e:
        print(f"Home route error: {e}")
        return render_template('index.html', DEBUG=True, departments=['CSE', 'ECE'], years=['1', '2', '3', '4'])

@app.route("/test")
def test():
    """Test endpoint to verify connection"""
    df = get_supabase_data()
    return f"""
    <h1>EduMetric - Supabase Connection Test</h1>
    <h2>Connection Status: {'SUCCESS' if not df.empty else 'FAILED'}</h2>
    <p><strong>Records:</strong> {len(df)}</p>
    <p><strong>Departments:</strong> {list(df['DEPT'].unique()) if not df.empty and 'DEPT' in df.columns else 'No data'}</p>
    <p><strong>Years:</strong> {list(df['YEAR'].unique()) if not df.empty and 'YEAR' in df.columns else 'No data'}</p>
    <p><strong>Sample RNOs:</strong> {list(df['RNO'].head(3)) if not df.empty and 'RNO' in df.columns else 'No data'}</p>
    """

@app.route("/api/stats")
def api_stats():
    try:
        df = get_supabase_data()
        if df.empty:
            return jsonify({"total_students": 0, "departments": [], "years": []})
        
        return jsonify({
            "total_students": len(df),
            "departments": sorted(df['DEPT'].unique().tolist()) if 'DEPT' in df.columns else [],
            "years": sorted(df['YEAR'].unique().tolist()) if 'YEAR' in df.columns else []
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/department/analyze", methods=["POST"])
def api_dept():
    try:
        data = request.get_json(silent=True) or {}
        dept = data.get("dept", None)
        year = data.get("year", None)

        df = get_supabase_data()
        
        if df.empty:
            return jsonify({"success": False, "message": "No data available"}), 400
        
        # Filter by department
        if dept and dept != "":
            df = df[df["DEPT"].astype(str).str.upper() == str(dept).upper()]

        # Filter by year
        if year not in (None, "", "all"):
            df = df[df["YEAR"].astype(str) == str(year)]

        if df.empty:
            return jsonify({"success": False, "message": "No students found for selected criteria"}), 400

        result = analyze_data(df)
        return jsonify({"success": True, **result})
        
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

        result = analyze_data(df)
        return jsonify({"success": True, **result})
        
    except Exception as e:
        return jsonify({"success": False, "message": f"Analysis failed: {str(e)}"}), 500

@app.route("/api/college/analyze")
def api_college():
    try:
        df = get_supabase_data()
        
        if df.empty:
            return jsonify({"success": False, "message": "No data available"}), 400
        
        result = analyze_data(df)
        return jsonify({"success": True, **result})
        
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
                student_data = {k.upper(): v for k, v in student.items()}
                return jsonify({"success": True, "student": student_data})
        
        return jsonify({"success": False, "message": "Student not found"}), 404
        
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

if __name__ == "__main__":
    print("Starting EduMetric App...")
    print("Supabase connection verified!")
    print("Visit: http://localhost:5000")
    print("Test: http://localhost:5000/test")
    
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)