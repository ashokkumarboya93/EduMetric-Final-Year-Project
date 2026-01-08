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

def get_data():
    try:
        url = f"{SUPABASE_URL}/rest/v1/students?select=*"
        headers = {
            'apikey': SUPABASE_KEY,
            'Authorization': f'Bearer {SUPABASE_KEY}',
            'Accept': 'application/json'
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            if data:
                df = pd.DataFrame(data)
                df.columns = df.columns.str.upper()
                return df
        
        return pd.DataFrame()
        
    except Exception as e:
        print(f"Data fetch error: {e}")
        return pd.DataFrame()

@app.route("/")
def home():
    return "<h1>EduMetric App Running!</h1><p>Supabase connection working</p>"

@app.route("/test")
def test():
    df = get_data()
    return f"<h2>Data Test</h2><p>Records: {len(df)}</p><p>Columns: {list(df.columns) if not df.empty else 'No data'}</p>"

@app.route("/api/stats")
def stats():
    try:
        df = get_data()
        if df.empty:
            return jsonify({"total_students": 0, "message": "No data"})
        
        return jsonify({
            "total_students": len(df),
            "departments": df['DEPT'].unique().tolist() if 'DEPT' in df.columns else [],
            "years": df['YEAR'].unique().tolist() if 'YEAR' in df.columns else []
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/analyze", methods=["POST"])
def analyze():
    try:
        df = get_data()
        if df.empty:
            return jsonify({"success": False, "message": "No data available"})
        
        # Simple analysis using existing Supabase data
        total = len(df)
        high_perf = len(df[df['PERFORMANCE_LABEL'].str.lower() == 'high']) if 'PERFORMANCE_LABEL' in df.columns else 0
        high_risk = len(df[df['RISK_LABEL'].str.lower() == 'high']) if 'RISK_LABEL' in df.columns else 0
        
        return jsonify({
            "success": True,
            "stats": {
                "total_students": total,
                "high_performers": high_perf,
                "high_risk": high_risk
            }
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

if __name__ == "__main__":
    print("Starting EduMetric App...")
    app.run(host="0.0.0.0", port=5000, debug=True)
