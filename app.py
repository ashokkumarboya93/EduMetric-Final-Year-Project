import os
from flask import Flask, jsonify

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'fallback-key')

def predict_student(perf, attendance):
    if perf >= 80: perf_label = "HIGH"
    elif perf >= 60: perf_label = "MEDIUM"
    else: perf_label = "LOW"
    
    if attendance < 60 or perf < 40: risk_label = "HIGH"
    elif attendance < 75 or perf < 60: risk_label = "MEDIUM"
    else: risk_label = "LOW"
    
    if attendance < 50 or perf < 40: drop_label = "HIGH"
    elif attendance < 70 or perf < 60: drop_label = "MEDIUM"
    else: drop_label = "LOW"
    
    return perf_label, risk_label, drop_label

@app.route("/")
def index():
    return """
    <h1>🎓 EduMetric Analytics</h1>
    <p>✅ System Running!</p>
    <a href="/api/analytics/preview">View Analytics</a>
    """

@app.route("/api/analytics/preview")
def api_analytics_preview():
    students = []
    
    # Sample data with predictions
    data = [
        ("23G31A4790", "Mohan Patel", 1, 1, 65.0, 72.0),
        ("23G31A1368", "Meera Rao", 1, 2, 82.0, 88.0)
    ]
    
    for rno, name, year, sem, perf, att in data:
        perf_label, risk_label, drop_label = predict_student(perf, att)
        
        students.append({
            "RNO": rno,
            "Name": name,
            "Year": year,
            "Sem": sem,
            "Perf": perf_label,
            "Risk": risk_label,
            "Dropout": drop_label,
            "Perf%": f"{perf}%",
            "Risk%": f"{100-perf}%",
            "Drop%": f"{100-att}%"
        })
    
    return jsonify({
        "success": True,
        "students": students
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)