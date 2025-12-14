import streamlit as st
import pandas as pd
import numpy as np
import joblib
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from fpdf import FPDF
import io
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import base64

# ==========================
# CONFIG & PATHS
# ==========================
DS1_PATH = r"C:\Users\Master\Desktop\Final Year\data\DS1.csv"
DS2_PATH = r"C:\Users\Master\Desktop\Final Year\data\DS2_ml_ready.csv"

PERF_MODEL_PATH = "performance_model.pkl"
PERF_ENC_PATH   = "performance_label_encoder.pkl"
RISK_MODEL_PATH = "risk_model.pkl"
RISK_ENC_PATH   = "risk_label_encoder.pkl"
DROP_MODEL_PATH = "dropout_model.pkl"
DROP_ENC_PATH   = "dropout_label_encoder.pkl"

# SMTP CONFIG (FILL YOURS)
SMTP_HOST = "smtp.yourmail.com"
SMTP_PORT = 587
SMTP_USER = "your_email@example.com"
SMTP_PASS = "your_password"
FROM_EMAIL = "your_email@example.com"

# ==========================
# HELPER FUNCTIONS
# ==========================

def safe(x, fallback=0.0):
    try:
        return float(str(x).replace("%", "").strip())
    except:
        return fallback

@st.cache_data
def load_data():
    ds1 = pd.read_csv(DS1_PATH)
    ds2 = pd.read_csv(DS2_PATH)
    return ds1, ds2

@st.cache_resource
def load_models():
    perf_model = joblib.load(PERF_MODEL_PATH)
    perf_enc   = joblib.load(PERF_ENC_PATH)
    risk_model = joblib.load(RISK_MODEL_PATH)
    risk_enc   = joblib.load(RISK_ENC_PATH)
    drop_model = joblib.load(DROP_MODEL_PATH)
    drop_enc   = joblib.load(DROP_ENC_PATH)
    return perf_model, perf_enc, risk_model, risk_enc, drop_model, drop_enc

def compute_features_from_row(row):
    curr_sem = int(safe(row.get("CURR_SEM", 1)))

    # past sems
    sems = []
    for i in range(1, curr_sem):
        sems.append(safe(row.get(f"SEM{i}", 0)))

    past_count = len(sems)
    past_avg = np.mean(sems) if past_count > 0 else 0
    performance_trend = sems[-1] - sems[-2] if past_count >= 2 else 0

    # internal %
    internal_pct = (safe(row.get("INTERNAL_MARKS", 0)) / 30) * 100

    # behavior %
    behavior_pct = safe(row.get("BEHAVIOR_SCORE_10", 0)) * 10

    # attendance
    tot = safe(row.get("TOTAL_DAYS_CURR", 0))
    att = safe(row.get("ATTENDED_DAYS_CURR", 0))
    prev_att = safe(row.get("PREV_ATTENDANCE_PERC", 0))

    present_att = (att / tot * 100) if tot > 0 else 0

    attendance_pct = (
        present_att * 0.70 +
        prev_att * 0.20 +
        behavior_pct * 0.10
    )

    return {
        "past_avg": past_avg,
        "past_count": past_count,
        "internal_pct": internal_pct,
        "attendance_pct": attendance_pct,
        "behavior_pct": behavior_pct,
        "performance_trend": performance_trend,
        "curr_sem": curr_sem,
        "present_att": present_att,
        "prev_att": prev_att
    }

def compute_overalls_and_labels(feat):
    past_avg = feat["past_avg"]
    internal_pct = feat["internal_pct"]
    attendance_pct = feat["attendance_pct"]
    behavior_pct = feat["behavior_pct"]

    perf_overall = (
        past_avg * 0.50 +
        internal_pct * 0.30 +
        attendance_pct * 0.15 +
        behavior_pct * 0.05
    )
    risk_overall = perf_overall
    risk_score = abs(100 - risk_overall)
    dropout_overall = (
        past_avg * 0.10 +
        internal_pct * 0.10 +
        attendance_pct * 0.70 +
        behavior_pct * 0.10
    )
    dropout_score = abs(100 - dropout_overall)

    # performance label
    if perf_overall >= 70:
        perf_label_rule = "high"
    elif perf_overall >= 50:
        perf_label_rule = "medium"
    else:
        perf_label_rule = "poor"

    # risk label
    if risk_score >= 70:
        risk_label_rule = "high"
    elif risk_score < 40:
        risk_label_rule = "low"
    else:
        risk_label_rule = "normal"

    # dropout label
    if dropout_score >= 75:
        drop_label_rule = "high"
    elif dropout_score < 45:
        drop_label_rule = "low"
    else:
        drop_label_rule = "medium"

    return {
        "performance_overall": perf_overall,
        "risk_overall": risk_overall,
        "risk_score": risk_score,
        "dropout_overall": dropout_overall,
        "dropout_score": dropout_score,
        "perf_label_rule": perf_label_rule,
        "risk_label_rule": risk_label_rule,
        "drop_label_rule": drop_label_rule
    }

def model_predict(features_vec, models):
    perf_model, perf_enc, risk_model, risk_enc, drop_model, drop_enc = models
    X = np.array(features_vec).reshape(1, -1)

    perf_raw = perf_model.predict(X)[0]
    risk_raw = risk_model.predict(X)[0]
    drop_raw = drop_model.predict(X)[0]

    perf_label = perf_enc.inverse_transform([perf_raw])[0]
    risk_label = risk_enc.inverse_transform([risk_raw])[0]
    drop_label = drop_enc.inverse_transform([drop_raw])[0]

    return perf_label, risk_label, drop_label

def kpi_color(label, metric_type="performance"):
    if label == "high":
        return "#ffcccc" if metric_type in ["risk", "dropout"] else "#ccffcc"
    if label in ["medium", "normal"]:
        return "#fff3cd"
    if label in ["low", "poor"]:
        return "#ffcccc" if metric_type == "performance" else "#ccffcc"
    return "#f0f0f0"

def send_email_alert(to_email, subject, body):
    try:
        msg = MIMEMultipart()
        msg["From"] = FROM_EMAIL
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)
        return True, "Alert email sent successfully."
    except Exception as e:
        return False, f"Failed to send email: {e}"

def generate_pdf_report(student_info, feat_dict, overalls_dict, model_labels):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Student Performance Report", ln=True, align="C")
    pdf.ln(5)

    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "Student Information:", ln=True)
    pdf.set_font("Arial", "", 11)
    for k, v in student_info.items():
        pdf.cell(0, 7, f"{k}: {v}", ln=True)

    pdf.ln(4)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "Computed Features:", ln=True)
    pdf.set_font("Arial", "", 11)
    for k, v in feat_dict.items():
        pdf.cell(0, 6, f"{k}: {round(v, 2)}", ln=True)

    pdf.ln(4)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "Scores & Predictions:", ln=True)
    pdf.set_font("Arial", "", 11)
    pdf.cell(0, 6, f"Performance Overall: {round(overalls_dict['performance_overall'],2)}", ln=True)
    pdf.cell(0, 6, f"Risk Score: {round(overalls_dict['risk_score'],2)}", ln=True)
    pdf.cell(0, 6, f"Dropout Score: {round(overalls_dict['dropout_score'],2)}", ln=True)
    pdf.cell(0, 6, f"Performance Label: {model_labels['perf'].upper()}", ln=True)
    pdf.cell(0, 6, f"Risk Label: {model_labels['risk'].upper()}", ln=True)
    pdf.cell(0, 6, f"Dropout Label: {model_labels['drop'].upper()}", ln=True)

    # Save to BytesIO
    buffer = io.BytesIO()
    pdf_output = pdf.output(dest='S').encode('latin1')
    buffer.write(pdf_output)
    buffer.seek(0)
    return buffer

def student_summary_text(perf_label, risk_label, drop_label):
    parts = []
    if perf_label == "high":
        parts.append("📊 Overall academic performance is strong.")
    elif perf_label == "medium":
        parts.append("📊 Academic performance is moderate; there is room to improve.")
    else:
        parts.append("📊 Academic performance is low and needs attention.")

    if risk_label == "high":
        parts.append("⚠️ Risk indicators are high; immediate mentor intervention is recommended.")
    elif risk_label == "normal":
        parts.append("✅ Risk indicators are within a normal range.")
    else:
        parts.append("✅ Risk is low and stable.")

    if drop_label == "high":
        parts.append("🚨 Dropout risk is high; start preventive counselling and parental communication.")
    elif drop_label == "medium":
        parts.append("⚡ There is some dropout risk; monitor the student closely.")
    else:
        parts.append("✅ Dropout risk is low.")

    return " ".join(parts)


# ==========================
# STREAMLIT UI
# ==========================
st.set_page_config(
    page_title="Student Performance Analytics",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Modern Pale Red Theme CSS
st.markdown("""
<style>
    /* Main theme */
    .main {
        background: linear-gradient(135deg, #fff5f5 0%, #ffe8e8 100%);
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #ffebee 0%, #ffcdd2 100%);
    }

    /* Cards */
    .metric-card {
        background: rgba(255, 255, 255, 0.95);
        border-radius: 16px;
        padding: 24px;
        margin: 12px 0;
        box-shadow: 0 8px 32px rgba(255, 100, 100, 0.15);
        border: 1px solid rgba(255, 200, 200, 0.3);
        transition: all 0.3s ease;
    }

    .metric-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 48px rgba(255, 100, 100, 0.25);
    }

    /* KPI Pills */
    .kpi-pill {
        border-radius: 20px;
        padding: 20px 28px;
        margin: 8px;
        text-align: center;
        font-weight: 600;
        font-size: 18px;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
        transition: all 0.3s ease;
        border: 2px solid transparent;
    }

    .kpi-pill:hover {
        transform: scale(1.05);
        border-color: #ff6b6b;
    }

    .kpi-value {
        font-size: 14px;
        opacity: 0.8;
        margin-top: 4px;
    }

    /* Headers */
    .main-header {
        text-align: center;
        color: #d32f2f;
        font-size: 42px;
        font-weight: 800;
        margin-bottom: 20px;
        text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.1);
        letter-spacing: -0.5px;
    }

    .section-header {
        color: #c62828;
        font-size: 28px;
        font-weight: 700;
        margin: 24px 0 16px 0;
        border-left: 5px solid #ef5350;
        padding-left: 16px;
    }

    /* Buttons */
    .stButton>button {
        background: linear-gradient(135deg, #ef5350 0%, #e53935 100%);
        color: white;
        border-radius: 12px;
        padding: 12px 32px;
        font-weight: 600;
        border: none;
        box-shadow: 0 4px 12px rgba(239, 83, 80, 0.3);
        transition: all 0.3s ease;
    }

    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(239, 83, 80, 0.4);
    }

    /* Download buttons */
    .stDownloadButton>button {
        background: linear-gradient(135deg, #ff8a80 0%, #ff5252 100%);
        color: white;
        border-radius: 10px;
        padding: 10px 24px;
        font-weight: 500;
        border: none;
    }

    /* Info boxes */
    .stInfo {
        background-color: rgba(255, 235, 238, 0.8);
        border-left: 4px solid #ef5350;
        border-radius: 8px;
    }

    /* Dataframe */
    .dataframe {
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
    }

    /* Form */
    .stForm {
        background: rgba(255, 255, 255, 0.9);
        border-radius: 16px;
        padding: 24px;
        box-shadow: 0 4px 24px rgba(0, 0, 0, 0.08);
    }

    /* Radio buttons */
    .stRadio > div {
        background: white;
        border-radius: 12px;
        padding: 12px;
    }

    /* Select boxes */
    .stSelectbox > div > div {
        border-radius: 10px;
    }

    /* Metrics */
    [data-testid="stMetricValue"] {
        font-size: 32px;
        font-weight: 700;
        color: #c62828;
    }

    /* Icons */
    .icon {
        font-size: 24px;
        margin-right: 8px;
    }
</style>
""", unsafe_allow_html=True)

# Load data and models
ds1, ds2 = load_data()
models = load_models()

# -------- SIDEBAR --------
st.sidebar.markdown("### 🎓 Navigation Panel")
mode = st.sidebar.radio(
    "📊 Select View Mode",
    ["👤 Student", "🏢 Department", "📅 Year-wise", "🏫 Total College"],
    label_visibility="collapsed"
)

st.sidebar.markdown("---")
st.sidebar.markdown("### 📌 Quick Stats")
st.sidebar.metric("Total Students", len(ds1))
st.sidebar.metric("Departments", ds1["DEPT"].nunique())
st.sidebar.metric("Years", ds1["YEAR"].nunique())

# -------------------------
# MAIN HEADER
# -------------------------
st.markdown(
    "<h1 class='main-header'>🎓 INTELLIGENT STUDENT PERFORMANCE ANALYTICS</h1>",
    unsafe_allow_html=True
)
st.markdown("<p style='text-align:center; font-size:18px; color:#666; margin-bottom:30px;'>Powered by Machine Learning & Predictive Analytics</p>", unsafe_allow_html=True)

# =====================================================
# MODE 1: STUDENT
# =====================================================
if mode == "👤 Student":
    st.markdown("<h2 class='section-header'>👤 Student-wise Prediction & Analysis</h2>", unsafe_allow_html=True)

    sub_mode = st.radio("📝 Select Input Mode", ["🔍 Existing Student", "➕ New Student"], horizontal=True)

    if "show_form" not in st.session_state:
        st.session_state.show_form = True

    if st.session_state.show_form:
        if sub_mode == "🔍 Existing Student":
            with st.form("existing_student_form"):
                st.markdown("### 🔍 Search Student")
                col1, col2, col3 = st.columns(3)
                with col1:
                    rno = st.text_input("📋 Register Number")
                with col2:
                    dept = st.selectbox("🏢 Department", sorted(ds1["DEPT"].dropna().unique()))
                with col3:
                    year = st.selectbox("📅 Year", sorted(ds1["YEAR"].dropna().unique()))

                submit = st.form_submit_button("🔎 Get Prediction", use_container_width=True)

            if submit:
                mask = (
                    (ds1["RNO"].astype(str) == rno) &
                    (ds1["DEPT"] == dept) &
                    (ds1["YEAR"] == year)
                )
                if mask.sum() == 0:
                    st.error("❌ No matching student found in database.")
                else:
                    row = ds1[mask].iloc[0].to_dict()
                    st.session_state.student_row = row
                    st.session_state.show_form = False
                    st.rerun()

        else:  # New Student
            with st.form("new_student_form"):
                st.markdown("### ➕ Add New Student")
                c1, c2 = st.columns(2)
                with c1:
                    name = st.text_input("👤 Name")
                    rno = st.text_input("📋 Register Number")
                    dept = st.selectbox("🏢 Department", sorted(ds1["DEPT"].dropna().unique()))
                    year = st.selectbox("📅 Year", sorted(ds1["YEAR"].dropna().unique()))
                with c2:
                    curr_sem = st.number_input("📚 Current Semester", 1, 8, 1)
                    prev_att = st.number_input("📊 Previous Attendance %", 0.0, 100.0, 80.0)
                    total_days = st.number_input("📆 Total Days (Current Sem)", 0.0, 200.0, 100.0)
                    attended_days = st.number_input("✅ Attended Days (Current Sem)", 0.0, 200.0, 90.0)

                behavior = st.number_input("⭐ Behavior Score (out of 10)", 0.0, 10.0, 8.0)

                st.markdown("#### 📖 Semester Marks")
                sem_marks = {}
                sem_cols = st.columns(4)
                for i in range(1, 9):
                    col = sem_cols[(i-1) % 4]
                    with col:
                        sem_marks[f"SEM{i}"] = st.number_input(f"SEM{i}", 0.0, 100.0, 0.0, key=f"sem{i}")

                internal_marks = st.number_input("📝 Internal Marks (out of 30)", 0.0, 30.0, 20.0)

                submit_new = st.form_submit_button("🎯 Predict Performance", use_container_width=True)

            if submit_new:
                row = {
                    "NAME": name,
                    "RNO": rno,
                    "DEPT": dept,
                    "YEAR": year,
                    "CURR_SEM": curr_sem,
                    "INTERNAL_MARKS": internal_marks,
                    "TOTAL_DAYS_CURR": total_days,
                    "ATTENDED_DAYS_CURR": attended_days,
                    "PREV_ATTENDANCE_PERC": prev_att,
                    "BEHAVIOR_SCORE_10": behavior,
                    "MENTOR_EMAIL": ""
                }
                row.update(sem_marks)
                st.session_state.student_row = row
                st.session_state.show_form = False
                st.rerun()

    else:
        # ---------- Show report ----------
        row = st.session_state.student_row
        feat = compute_features_from_row(row)
        over = compute_overalls_and_labels(feat)

        feature_vec = [
            feat["past_avg"],
            feat["past_count"],
            feat["internal_pct"],
            feat["attendance_pct"],
            feat["behavior_pct"],
            feat["performance_trend"]
        ]

        perf_label, risk_label, drop_label = model_predict(feature_vec, models)

        # Student info header in card
        st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown(f"### 👤 {row.get('NAME','N/A')}")
            st.markdown(f"**📋 RNO:** {row.get('RNO','N/A')} &nbsp;&nbsp;|&nbsp;&nbsp; **🏢 Dept:** {row.get('DEPT','N/A')} &nbsp;&nbsp;|&nbsp;&nbsp; **📅 Year:** {row.get('YEAR','N/A')}")
        with col2:
            st.metric("📚 Current Semester", feat['curr_sem'])
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("---")

        # KPIs
        st.markdown("<h3 class='section-header'>🎯 Prediction KPIs</h3>", unsafe_allow_html=True)
        k1, k2, k3 = st.columns(3)

        with k1:
            bg = kpi_color(perf_label)
            st.markdown(
                f"""<div class='kpi-pill' style='background-color:{bg};'>
                    <div style='font-size:16px;'>📊 PERFORMANCE</div>
                    <div style='font-size:24px; font-weight:700; margin:8px 0;'>{perf_label.upper()}</div>
                    <div class='kpi-value'>Score: {over['performance_overall']:.1f}%</div>
                </div>""",
                unsafe_allow_html=True
            )

        with k2:
            bg = kpi_color(risk_label, "risk")
            st.markdown(
                f"""<div class='kpi-pill' style='background-color:{bg};'>
                    <div style='font-size:16px;'>⚠️ RISK</div>
                    <div style='font-size:24px; font-weight:700; margin:8px 0;'>{risk_label.upper()}</div>
                    <div class='kpi-value'>Risk Score: {over['risk_score']:.1f}%</div>
                </div>""",
                unsafe_allow_html=True
            )

        with k3:
            bg = kpi_color(drop_label, "dropout")
            st.markdown(
                f"""<div class='kpi-pill' style='background-color:{bg};'>
                    <div style='font-size:16px;'>🚨 DROPOUT RISK</div>
                    <div style='font-size:24px; font-weight:700; margin:8px 0;'>{drop_label.upper()}</div>
                    <div class='kpi-value'>Dropout Score: {over['dropout_score']:.1f}%</div>
                </div>""",
                unsafe_allow_html=True
            )

        st.markdown("---")

        # Visual Insights
        st.markdown("<h3 class='section-header'>📊 Visual Insights & Analytics</h3>", unsafe_allow_html=True)

        # Row 1: Marks trend + Attendance radar
        col1, col2 = st.columns(2)

        with col1:
            # Semester marks trend
            marks = []
            sem_labels = []
            curr_sem = feat["curr_sem"]
            for i in range(1, curr_sem):
                val = safe(row.get(f"SEM{i}", 0))
                marks.append(val)
                sem_labels.append(f"SEM{i}")
            if len(marks) == 0:
                marks = [0]
                sem_labels = ["No Data"]

            df_marks = pd.DataFrame({"Semester": sem_labels, "Marks": marks})
            fig_marks = px.line(
                df_marks, x="Semester", y="Marks", markers=True,
                title="📈 Semester-wise Marks Trend",
                color_discrete_sequence=["#ef5350"]
            )
            fig_marks.update_traces(line=dict(width=3), marker=dict(size=10))
            fig_marks.update_layout(
                plot_bgcolor='rgba(255,245,245,0.5)',
                paper_bgcolor='rgba(255,255,255,0.9)',
                title_font=dict(size=18, color='#c62828'),
                hovermode='x unified'
            )
            st.plotly_chart(fig_marks, use_container_width=True)

        with col2:
            # Attendance components radar
            categories = ['Present Attendance', 'Previous Attendance', 'Behavior Impact']
            values = [feat["present_att"], feat["prev_att"], feat["behavior_pct"]]

            fig_radar = go.Figure()
            fig_radar.add_trace(go.Scatterpolar(
                r=values,
                theta=categories,
                fill='toself',
                fillcolor='rgba(239, 83, 80, 0.3)',
                line=dict(color='#ef5350', width=2),
                marker=dict(size=8)
            ))
            fig_radar.update_layout(
                polar=dict(
                    radialaxis=dict(visible=True, range=[0, 100]),
                    bgcolor='rgba(255,245,245,0.5)'
                ),
                title="🎯 Attendance & Behavior Profile",
                title_font=dict(size=18, color='#c62828'),
                paper_bgcolor='rgba(255,255,255,0.9)'
            )
            st.plotly_chart(fig_radar, use_container_width=True)

        # Row 2: Score comparison + Component breakdown
        col3, col4 = st.columns(2)

        with col3:
            # Overall scores comparison
            fig_scores = go.Figure()
            scores = [over["performance_overall"], over["risk_score"], over["dropout_score"]]
            labels = ["Performance", "Risk", "Dropout"]
            colors = ['#66bb6a', '#ffa726', '#ef5350']

            fig_scores.add_trace(go.Bar(
                x=labels,
                y=scores,
                marker=dict(
                    color=colors,
                    line=dict(color='#c62828', width=2)
                ),
                text=[f"{s:.1f}%" for s in scores],
                textposition='auto',
                textfont=dict(size=14, color='white', family='Arial Black')
            ))
            fig_scores.update_layout(
                title="📊 Overall Performance Indicators",
                title_font=dict(size=18, color='#c62828'),
                plot_bgcolor='rgba(255,245,245,0.5)',
                paper_bgcolor='rgba(255,255,255,0.9)',
                yaxis=dict(title="Score (%)", range=[0, 100])
            )
            st.plotly_chart(fig_scores, use_container_width=True)

        with col4:
            # Component contribution pie
            components = {
                "Past Average": feat["past_avg"],
                "Internal Marks": feat["internal_pct"],
                "Attendance": feat["attendance_pct"],
                "Behavior": feat["behavior_pct"]
            }

            fig_pie = px.pie(
                values=list(components.values()),
                names=list(components.keys()),
                title="🎯 Performance Component Distribution",
                color_discrete_sequence=px.colors.sequential.Reds_r,
                hole=0.4
            )
            fig_pie.update_traces(textposition='inside', textinfo='percent+label')
            fig_pie.update_layout(
                title_font=dict(size=18, color='#c62828'),
                paper_bgcolor='rgba(255,255,255,0.9)'
            )
            st.plotly_chart(fig_pie, use_container_width=True)

        # Row 3: Gauge charts for key metrics
        st.markdown("#### 🎚️ Performance Gauges")
        gauge_col1, gauge_col2, gauge_col3 = st.columns(3)

        with gauge_col1:
            fig_gauge1 = go.Figure(go.Indicator(
                mode="gauge+number+delta",
                value=over["performance_overall"],
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': "Performance", 'font': {'size': 20, 'color': '#c62828'}},
                delta={'reference': 70},
                gauge={
                    'axis': {'range': [None, 100], 'tickwidth': 1},
                    'bar': {'color': "#ef5350"},
                    'steps': [
                        {'range': [0, 50], 'color': "#ffcdd2"},
                        {'range': [50, 70], 'color': "#fff9c4"},
                        {'range': [70, 100], 'color': "#c8e6c9"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 70
                    }
                }
            ))
            fig_gauge1.update_layout(height=250, margin=dict(l=20, r=20, t=40, b=20))
            st.plotly_chart(fig_gauge1, use_container_width=True)

        with gauge_col2:
            fig_gauge2 = go.Figure(go.Indicator(
                mode="gauge+number",
                value=feat["attendance_pct"],
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': "Attendance", 'font': {'size': 20, 'color': '#c62828'}},
                gauge={
                    'axis': {'range': [None, 100]},
                    'bar': {'color': "#ff8a80"},
                    'steps': [
                        {'range': [0, 75], 'color': "#ffcdd2"},
                        {'range': [75, 100], 'color': "#c8e6c9"}
                    ],
                }
            ))
            fig_gauge2.update_layout(height=250, margin=dict(l=20, r=20, t=40, b=20))
            st.plotly_chart(fig_gauge2, use_container_width=True)

        with gauge_col3:
            fig_gauge3 = go.Figure(go.Indicator(
                mode="gauge+number",
                value=feat["internal_pct"],
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': "Internal Marks", 'font': {'size': 20, 'color': '#c62828'}},
                gauge={
                    'axis': {'range': [None, 100]},
                    'bar': {'color': "#ff5252"},
                    'steps': [
                        {'range': [0, 60], 'color': "#ffcdd2"},
                        {'range': [60, 100], 'color': "#c8e6c9"}
                    ],
                }
            ))
            fig_gauge3.update_layout(height=250, margin=dict(l=20, r=20, t=40, b=20))
            st.plotly_chart(fig_gauge3, use_container_width=True)

        st.markdown("---")

        # Summary & Alerts
        st.markdown("<h3 class='section-header'>📝 Summary & AI Insights</h3>", unsafe_allow_html=True)

        summary = student_summary_text(perf_label, risk_label, drop_label)
        st.info(summary)

        # Show alert button only if risk or dropout is high
        need_alert = (risk_label == "high") or (drop_label == "high")
        mentor_email = row.get("MENTOR_EMAIL", "")

        if need_alert:
            st.warning("⚠️ **ALERT:** This student requires immediate attention!")
            if mentor_email:
                if st.button("📩 Send Mentor Alert Email", type="primary"):
                    subject = f"⚠️ Alert: {row.get('NAME','')} ({row.get('RNO','')}) - High Risk/Dropout Notification"
                    body = f"""Dear Mentor,

This is an automated alert regarding student {row.get('NAME','')} (RNO: {row.get('RNO','')}).

PERFORMANCE SUMMARY:
- Performance Label: {perf_label.upper()}
- Risk Label: {risk_label.upper()}
- Dropout Label: {drop_label.upper()}

SCORES:
- Performance Overall: {over['performance_overall']:.2f}%
- Risk Score: {over['risk_score']:.2f}%
- Dropout Score: {over['dropout_score']:.2f}%

RECOMMENDATION:
{summary}

Please take immediate action and contact the student for counselling.

Best regards,
Student Performance Analytics System"""

                    ok, msg = send_email_alert(mentor_email, subject, body)
                    if ok:
                        st.success(f"✅ {msg}")
                    else:
                        st.error(f"❌ {msg}")
            else:
                st.caption("⚠️ Mentor email not available in records.")

        # AI Suggestions
        st.markdown("### 🤖 AI-based Recommendations")
        sugg_list = []
        if perf_label in ["poor", "medium"]:
            sugg_list.append("• 📚 **Academic Support**: Arrange regular revision sessions and provide targeted remedial classes in weak subjects.")
        if risk_label == "high":
            sugg_list.append("• 👨‍🏫 **Mentor Intervention**: Schedule immediate one-on-one discussion with mentor to identify and address underlying issues.")
        if drop_label in ["medium", "high"]:
            sugg_list.append("• 👨‍👩‍👧 **Family Engagement**: Initiate parental communication and arrange counselling sessions to prevent dropout.")
        if feat["attendance_pct"] < 75:
            sugg_list.append("• ⏰ **Attendance Improvement**: Create personalized attendance improvement plan with regular monitoring.")
        if feat["internal_pct"] < 60:
            sugg_list.append("• 📝 **Internal Assessment Focus**: Provide additional practice materials and conduct mock tests.")
        if not sugg_list:
            sugg_list.append("• ✅ **Maintain Excellence**: Student is performing well. Continue providing positive reinforcement and academic support.")

        for sugg in sugg_list:
            st.markdown(f"<div class='metric-card'>{sugg}</div>", unsafe_allow_html=True)

        st.markdown("---")

        # Export & Actions
        st.markdown("<h3 class='section-header'>📥 Export & Actions</h3>", unsafe_allow_html=True)

        student_info = {
            "Name": row.get("NAME", ""),
            "RNO": row.get("RNO", ""),
            "DEPT": row.get("DEPT", ""),
            "YEAR": row.get("YEAR", ""),
            "Current Semester": feat["curr_sem"]
        }

        # Export student details CSV
        detail_df = pd.DataFrame([{
            **student_info,
            **feat,
            **over,
            "performance_label": perf_label,
            "risk_label": risk_label,
            "dropout_label": drop_label
        }])
        csv_bytes = detail_df.to_csv(index=False).encode("utf-8")

        c1, c2, c3 = st.columns(3)
        with c1:
            st.download_button(
                "📊 Export Details (CSV)",
                data=csv_bytes,
                file_name=f"{row.get('RNO','student')}_details.csv",
                mime="text/csv",
                use_container_width=True
            )

        # PDF report
        with c2:
            pdf_buf = generate_pdf_report(
                student_info, feat, over,
                {"perf": perf_label, "risk": risk_label, "drop": drop_label}
            )
            st.download_button(
                "📄 Export Report (PDF)",
                data=pdf_buf,
                file_name=f"{row.get('RNO','student')}_report.pdf",
                mime="application/pdf",
                use_container_width=True
            )

        with c3:
            if st.button("🔄 Predict Another Student", use_container_width=True):
                st.session_state.show_form = True
                st.rerun()

# =====================================================
# MODE 2: DEPARTMENT
# =====================================================
elif mode == "🏢 Department":
    st.markdown("<h2 class='section-header'>🏢 Department-wise Analysis & Predictions</h2>", unsafe_allow_html=True)

    opt = st.radio("🎯 Department View", ["📊 Department Only", "📊 Department + Year"], horizontal=True)

    depts = sorted(ds1["DEPT"].dropna().unique())
    dept_sel = st.selectbox("🏢 Select Department", depts)

    if opt == "📊 Department + Year":
        years = sorted(ds1["YEAR"].dropna().unique())
        year_sel = st.selectbox("📅 Select Year", years)
        mask = (ds1["DEPT"] == dept_sel) & (ds1["YEAR"] == year_sel)
        title_suffix = f" - {dept_sel} (Year {year_sel})"
    else:
        mask = (ds1["DEPT"] == dept_sel)
        title_suffix = f" - {dept_sel}"

    subset = ds1[mask].copy()

    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("👥 Total Students", len(subset))

    if len(subset) == 0:
        st.warning("⚠️ No students found for this selection.")
    else:
        # Compute predictions
        perf_labels = []
        risk_labels = []
        drop_labels = []
        perf_scores = []
        risk_scores = []
        drop_scores = []

        for _, r in subset.iterrows():
            f = compute_features_from_row(r)
            o = compute_overalls_and_labels(f)
            fv = [f["past_avg"], f["past_count"], f["internal_pct"],
                  f["attendance_pct"], f["behavior_pct"], f["performance_trend"]]
            pl, rl, dl = model_predict(fv, models)
            perf_labels.append(pl)
            risk_labels.append(rl)
            drop_labels.append(dl)
            perf_scores.append(o["performance_overall"])
            risk_scores.append(o["risk_score"])
            drop_scores.append(o["dropout_score"])

        subset["perf_label"] = perf_labels
        subset["risk_label"] = risk_labels
        subset["drop_label"] = drop_labels
        subset["perf_score"] = perf_scores
        subset["risk_score"] = risk_scores
        subset["drop_score"] = drop_scores

        # Additional metrics
        col2.metric("🎓 High Performers", (subset["perf_label"] == "high").sum())
        col3.metric("⚠️ High Risk", (subset["risk_label"] == "high").sum())
        col4.metric("🚨 High Dropout Risk", (subset["drop_label"] == "high").sum())

        st.markdown("---")

        # Data table
        st.markdown("### 📋 Student Data Table")
        display_df = subset[["RNO","NAME","DEPT","YEAR","CURR_SEM","perf_label","risk_label","drop_label","perf_score","risk_score","drop_score"]].copy()
        st.dataframe(display_df, use_container_width=True, height=400)

        st.markdown("---")

        # Visualizations
        st.markdown("### 📊 Department Analytics Dashboard")

        # Row 1: Label distributions
        col1, col2, col3 = st.columns(3)

        with col1:
            perf_counts = subset["perf_label"].value_counts()
            fig1 = px.pie(
                values=perf_counts.values,
                names=perf_counts.index,
                title=f"📊 Performance Distribution{title_suffix}",
                color_discrete_sequence=["#66bb6a", "#ffa726", "#ef5350"],
                hole=0.4
            )
            fig1.update_traces(textposition='inside', textinfo='percent+label')
            fig1.update_layout(
                title_font=dict(size=16, color='#c62828'),
                paper_bgcolor='rgba(255,255,255,0.9)'
            )
            st.plotly_chart(fig1, use_container_width=True)

        with col2:
            risk_counts = subset["risk_label"].value_counts()
            fig2 = px.pie(
                values=risk_counts.values,
                names=risk_counts.index,
                title=f"⚠️ Risk Distribution{title_suffix}",
                color_discrete_sequence=["#66bb6a", "#ffa726", "#ef5350"],
                hole=0.4
            )
            fig2.update_traces(textposition='inside', textinfo='percent+label')
            fig2.update_layout(
                title_font=dict(size=16, color='#c62828'),
                paper_bgcolor='rgba(255,255,255,0.9)'
            )
            st.plotly_chart(fig2, use_container_width=True)

        with col3:
            drop_counts = subset["drop_label"].value_counts()
            fig3 = px.pie(
                values=drop_counts.values,
                names=drop_counts.index,
                title=f"🚨 Dropout Risk{title_suffix}",
                color_discrete_sequence=["#66bb6a", "#ffa726", "#ef5350"],
                hole=0.4
            )
            fig3.update_traces(textposition='inside', textinfo='percent+label')
            fig3.update_layout(
                title_font=dict(size=16, color='#c62828'),
                paper_bgcolor='rgba(255,255,255,0.9)'
            )
            st.plotly_chart(fig3, use_container_width=True)

        # Row 2: Score distributions
        col4, col5 = st.columns(2)

        with col4:
            fig_box = px.box(
                subset,
                y=["perf_score", "risk_score", "drop_score"],
                title=f"📊 Score Distribution Analysis{title_suffix}",
                labels={"value": "Score", "variable": "Metric"},
                color_discrete_sequence=["#ef5350", "#ff8a80", "#ff5252"]
            )
            fig_box.update_layout(
                plot_bgcolor='rgba(255,245,245,0.5)',
                paper_bgcolor='rgba(255,255,255,0.9)',
                title_font=dict(size=16, color='#c62828')
            )
            st.plotly_chart(fig_box, use_container_width=True)

        with col5:
            fig_violin = px.violin(
                subset,
                y="perf_score",
                x="perf_label",
                title=f"🎻 Performance Score by Label{title_suffix}",
                color="perf_label",
                color_discrete_sequence=["#ef5350", "#ffa726", "#66bb6a"],
                box=True
            )
            fig_violin.update_layout(
                plot_bgcolor='rgba(255,245,245,0.5)',
                paper_bgcolor='rgba(255,255,255,0.9)',
                title_font=dict(size=16, color='#c62828')
            )
            st.plotly_chart(fig_violin, use_container_width=True)

        # Row 3: Treemap and sunburst
        col6, col7 = st.columns(2)

        with col6:
            fig_tree = px.treemap(
                subset,
                path=['YEAR', 'perf_label'],
                title=f"🌳 Year-wise Performance Breakdown{title_suffix}",
                color='perf_label',
                color_discrete_map={'high': '#66bb6a', 'medium': '#ffa726', 'poor': '#ef5350'}
            )
            fig_tree.update_layout(
                title_font=dict(size=16, color='#c62828'),
                paper_bgcolor='rgba(255,255,255,0.9)'
            )
            st.plotly_chart(fig_tree, use_container_width=True)

        with col7:
            fig_sun = px.sunburst(
                subset,
                path=['perf_label', 'risk_label', 'drop_label'],
                title=f"☀️ Multi-level Risk Analysis{title_suffix}",
                color='perf_label',
                color_discrete_map={'high': '#66bb6a', 'medium': '#ffa726', 'poor': '#ef5350'}
            )
            fig_sun.update_layout(
                title_font=dict(size=16, color='#c62828'),
                paper_bgcolor='rgba(255,255,255,0.9)'
            )
            st.plotly_chart(fig_sun, use_container_width=True)

        st.markdown("---")

        # Summary
        st.markdown("### 📝 Department Summary")
        summary_text = f"""
        **{dept_sel}** department analysis reveals:
        - **Total Students**: {len(subset)}
        - **High Performers**: {(subset['perf_label'] == 'high').sum()} ({(subset['perf_label'] == 'high').sum()/len(subset)*100:.1f}%)
        - **Students at Risk**: {(subset['risk_label'] == 'high').sum()} ({(subset['risk_label'] == 'high').sum()/len(subset)*100:.1f}%)
        - **Dropout Risk**: {(subset['drop_label'] == 'high').sum()} ({(subset['drop_label'] == 'high').sum()/len(subset)*100:.1f}%)
        - **Average Performance Score**: {subset['perf_score'].mean():.2f}%
        """
        st.info(summary_text)

        # Export options
        st.markdown("### 📥 Export Department Data")
        col1, col2 = st.columns(2)

        with col1:
            csv_export = subset.to_csv(index=False).encode('utf-8')
            st.download_button(
                "📊 Export Full Data (CSV)",
                data=csv_export,
                file_name=f"department_{dept_sel}_analysis.csv",
                mime="text/csv",
                use_container_width=True
            )

        with col2:
            summary_df = pd.DataFrame({
                'Metric': ['Total Students', 'High Performers', 'High Risk', 'High Dropout Risk', 'Avg Performance'],
                'Value': [
                    len(subset),
                    (subset['perf_label'] == 'high').sum(),
                    (subset['risk_label'] == 'high').sum(),
                    (subset['drop_label'] == 'high').sum(),
                    f"{subset['perf_score'].mean():.2f}%"
                ]
            })
            summary_csv = summary_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                "📄 Export Summary (CSV)",
                data=summary_csv,
                file_name=f"department_{dept_sel}_summary.csv",
                mime="text/csv",
                use_container_width=True
            )

# =====================================================
# MODE 3: YEAR-WISE
# =====================================================
elif mode == "📅 Year-wise":
    st.markdown("<h2 class='section-header'>📅 Year-wise Comprehensive Analysis</h2>", unsafe_allow_html=True)

    years = sorted(ds1["YEAR"].dropna().unique())
    year_sel = st.selectbox("📅 Select Year", years)

    mask = ds1["YEAR"] == year_sel
    subset = ds1[mask].copy()

    if len(subset) == 0:
        st.warning("⚠️ No students found for this year.")
    else:
        # Compute predictions
        perf_labels = []
        risk_labels = []
        drop_labels = []
        perf_scores = []

        for _, r in subset.iterrows():
            f = compute_features_from_row(r)
            o = compute_overalls_and_labels(f)
            fv = [f["past_avg"], f["past_count"], f["internal_pct"],
                  f["attendance_pct"], f["behavior_pct"], f["performance_trend"]]
            pl, rl, dl = model_predict(fv, models)
            perf_labels.append(pl)
            risk_labels.append(rl)
            drop_labels.append(dl)
            perf_scores.append(o["performance_overall"])

        subset["perf_label"] = perf_labels
        subset["risk_label"] = risk_labels
        subset["drop_label"] = drop_labels
        subset["perf_score"] = perf_scores

        # Metrics
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("👥 Total Students", len(subset))
        col2.metric("🏢 Departments", subset["DEPT"].nunique())
        col3.metric("📈 Avg Performance", f"{subset['perf_score'].mean():.1f}%")
        col4.metric("⚠️ High Risk Count", (subset["risk_label"] == "high").sum())

        st.markdown("---")

        # Data table
        st.markdown("### 📋 Year-wise Student Records")
        display_df = subset[["RNO","NAME","DEPT","CURR_SEM","perf_label","risk_label","drop_label","perf_score"]]
        st.dataframe(display_df, use_container_width=True, height=400)

        st.markdown("---")

        # Visualizations
        st.markdown("### 📊 Year-wise Analytics Dashboard")

        # Row 1: Department comparison
        col1, col2 = st.columns(2)

        with col1:
            dept_perf = subset.groupby(['DEPT', 'perf_label']).size().reset_index(name='count')
            fig1 = px.bar(
                dept_perf,
                x="DEPT",
                y="count",
                color="perf_label",
                title=f"🏢 Department vs Performance (Year {year_sel})",
                barmode="group",
                color_discrete_map={'high': '#66bb6a', 'medium': '#ffa726', 'poor': '#ef5350'}
            )
            fig1.update_layout(
                plot_bgcolor='rgba(255,245,245,0.5)',
                paper_bgcolor='rgba(255,255,255,0.9)',
                title_font=dict(size=16, color='#c62828')
            )
            st.plotly_chart(fig1, use_container_width=True)

        with col2:
            dept_avg = subset.groupby('DEPT')['perf_score'].mean().reset_index()
            fig2 = px.bar(
                dept_avg,
                x="DEPT",
                y="perf_score",
                title=f"📊 Average Performance by Department (Year {year_sel})",
                color="perf_score",
                color_continuous_scale=["#ef5350", "#ffa726", "#66bb6a"]
            )
            fig2.update_layout(
                plot_bgcolor='rgba(255,245,245,0.5)',
                paper_bgcolor='rgba(255,255,255,0.9)',
                title_font=dict(size=16, color='#c62828')
            )
            st.plotly_chart(fig2, use_container_width=True)

        # Row 2: Risk analysis
        col3, col4 = st.columns(2)

        with col3:
            risk_dept = subset.groupby(['DEPT', 'risk_label']).size().reset_index(name='count')
            fig3 = px.sunburst(
                risk_dept,
                path=['DEPT', 'risk_label'],
                values='count',
                title=f"🎯 Department-wise Risk Distribution (Year {year_sel})",
                color='count',
                color_continuous_scale='Reds'
            )
            fig3.update_layout(
                title_font=dict(size=16, color='#c62828'),
                paper_bgcolor='rgba(255,255,255,0.9)'
            )
            st.plotly_chart(fig3, use_container_width=True)

        with col4:
            fig4 = px.histogram(
                subset,
                x="perf_score",
                color="DEPT",
                title=f"📈 Performance Score Distribution (Year {year_sel})",
                nbins=20,
                barmode='overlay',
                opacity=0.7
            )
            fig4.update_layout(
                plot_bgcolor='rgba(255,245,245,0.5)',
                paper_bgcolor='rgba(255,255,255,0.9)',
                title_font=dict(size=16, color='#c62828')
            )
            st.plotly_chart(fig4, use_container_width=True)

        # Row 3: Scatter and heatmap
        col5, col6 = st.columns(2)

        with col5:
            fig5 = px.scatter(
                subset,
                x="perf_score",
                y="DEPT",
                color="perf_label",
                size=[10]*len(subset),
                title=f"🔍 Department Performance Scatter (Year {year_sel})",
                color_discrete_map={'high': '#66bb6a', 'medium': '#ffa726', 'poor': '#ef5350'}
            )
            fig5.update_layout(
                plot_bgcolor='rgba(255,245,245,0.5)',
                paper_bgcolor='rgba(255,255,255,0.9)',
                title_font=dict(size=16, color='#c62828')
            )
            st.plotly_chart(fig5, use_container_width=True)

        with col6:
            # Create cross-tab for heatmap
            crosstab = pd.crosstab(subset['DEPT'], subset['perf_label'])
            fig6 = px.imshow(
                crosstab,
                title=f"🔥 Performance Heatmap (Year {year_sel})",
                color_continuous_scale='Reds',
                labels=dict(x="Performance Label", y="Department", color="Count")
            )
            fig6.update_layout(
                title_font=dict(size=16, color='#c62828'),
                paper_bgcolor='rgba(255,255,255,0.9)'
            )
            st.plotly_chart(fig6, use_container_width=True)

        st.markdown("---")

        # Summary
        st.markdown("### 📝 Year Summary & Insights")
        dept_summary = subset.groupby('DEPT').agg({
            'perf_score': 'mean',
            'RNO': 'count'
        }).round(2)
        dept_summary.columns = ['Avg Performance', 'Student Count']
        dept_summary = dept_summary.sort_values('Avg Performance', ascending=False)

        col1, col2 = st.columns([2, 1])
        with col1:
            st.dataframe(dept_summary, use_container_width=True)
        with col2:
            best_dept = dept_summary.index[0]
            best_score = dept_summary.iloc[0]['Avg Performance']
            st.metric("🏆 Top Department", best_dept)
            st.metric("📊 Best Avg Score", f"{best_score:.1f}%")

        # Export
        st.markdown("### 📥 Export Year Data")
        col1, col2 = st.columns(2)

        with col1:
            csv_export = subset.to_csv(index=False).encode('utf-8')
            st.download_button(
                "📊 Export Year Data (CSV)",
                data=csv_export,
                file_name=f"year_{year_sel}_analysis.csv",
                mime="text/csv",
                use_container_width=True
            )

        with col2:
            summary_export = dept_summary.to_csv().encode('utf-8')
            st.download_button(
                "📄 Export Summary (CSV)",
                data=summary_export,
                file_name=f"year_{year_sel}_summary.csv",
                mime="text/csv",
                use_container_width=True
            )

# =====================================================
# MODE 4: TOTAL COLLEGE
# =====================================================
elif mode == "🏫 Total College":
    st.markdown("<h2 class='section-header'>🏫 Overall College Analytics & Insights</h2>", unsafe_allow_html=True)

    subset = ds1.copy()

    # Compute predictions for all students
    perf_labels = []
    risk_labels = []
    drop_labels = []
    perf_scores = []
    risk_scores = []
    drop_scores = []

    progress_bar = st.progress(0)
    status_text = st.empty()

    for idx, (_, r) in enumerate(subset.iterrows()):
        f = compute_features_from_row(r)
        o = compute_overalls_and_labels(f)
        fv = [f["past_avg"], f["past_count"], f["internal_pct"],
              f["attendance_pct"], f["behavior_pct"], f["performance_trend"]]
        pl, rl, dl = model_predict(fv, models)
        perf_labels.append(pl)
        risk_labels.append(rl)
        drop_labels.append(dl)
        perf_scores.append(o["performance_overall"])
        risk_scores.append(o["risk_score"])
        drop_scores.append(o["dropout_score"])

        # Update progress
        progress = (idx + 1) / len(subset)
        progress_bar.progress(progress)
        status_text.text(f"Processing: {idx + 1}/{len(subset)} students")

    progress_bar.empty()
    status_text.empty()

    subset["perf_label"] = perf_labels
    subset["risk_label"] = risk_labels
    subset["drop_label"] = drop_labels
    subset["perf_score"] = perf_scores
    subset["risk_score"] = risk_scores
    subset["drop_score"] = drop_scores

    # Top metrics
    st.markdown("### 🎯 College-wide Key Performance Indicators")
    col1, col2, col3, col4, col5 = st.columns(5)

    col1.metric("👥 Total Students", len(subset))
    col2.metric("🏢 Departments", subset["DEPT"].nunique())
    col3.metric("📊 Avg Performance", f"{subset['perf_score'].mean():.1f}%")
    col4.metric("⚠️ High Risk", (subset["risk_label"] == "high").sum())
    col5.metric("🚨 Dropout Risk", (subset["drop_label"] == "high").sum())

    st.markdown("---")

    # Data table with filters
    st.markdown("### 📋 Complete Student Database")

    # Filters
    filter_col1, filter_col2, filter_col3 = st.columns(3)
    with filter_col1:
        dept_filter = st.multiselect("Filter by Department", options=sorted(subset["DEPT"].unique()), default=[])
    with filter_col2:
        year_filter = st.multiselect("Filter by Year", options=sorted(subset["YEAR"].unique()), default=[])
    with filter_col3:
        perf_filter = st.multiselect("Filter by Performance", options=sorted(subset["perf_label"].unique()), default=[])

    # Apply filters
    filtered_df = subset.copy()
    if dept_filter:
        filtered_df = filtered_df[filtered_df["DEPT"].isin(dept_filter)]
    if year_filter:
        filtered_df = filtered_df[filtered_df["YEAR"].isin(year_filter)]
    if perf_filter:
        filtered_df = filtered_df[filtered_df["perf_label"].isin(perf_filter)]

    st.dataframe(
        filtered_df[["RNO","NAME","DEPT","YEAR","CURR_SEM","perf_label","risk_label","drop_label","perf_score","risk_score","drop_score"]],
        use_container_width=True,
        height=400
    )

    st.markdown("---")

    # Comprehensive visualizations
    st.markdown("### 📊 College-wide Analytics Dashboard")

    # Row 1: Global distributions
    st.markdown("#### 🌐 Global Label Distributions")
    col1, col2, col3 = st.columns(3)

    with col1:
        perf_counts = subset["perf_label"].value_counts()
        fig1 = px.pie(
            values=perf_counts.values,
            names=perf_counts.index,
            title="📊 Overall Performance Distribution",
            color_discrete_sequence=["#66bb6a", "#ffa726", "#ef5350"],
            hole=0.4
        )
        fig1.update_traces(textposition='inside', textinfo='percent+label', textfont_size=14)
        fig1.update_layout(
            title_font=dict(size=18, color='#c62828', family='Arial Black'),
            paper_bgcolor='rgba(255,255,255,0.9)',
            showlegend=True
        )
        st.plotly_chart(fig1, use_container_width=True)

    with col2:
        risk_counts = subset["risk_label"].value_counts()
        fig2 = px.pie(
            values=risk_counts.values,
            names=risk_counts.index,
            title="⚠️ Overall Risk Distribution",
            color_discrete_sequence=["#66bb6a", "#ffa726", "#ef5350"],
            hole=0.4
        )
        fig2.update_traces(textposition='inside', textinfo='percent+label', textfont_size=14)
        fig2.update_layout(
            title_font=dict(size=18, color='#c62828', family='Arial Black'),
            paper_bgcolor='rgba(255,255,255,0.9)'
        )
        st.plotly_chart(fig2, use_container_width=True)

    with col3:
        drop_counts = subset["drop_label"].value_counts()
        fig3 = px.pie(
            values=drop_counts.values,
            names=drop_counts.index,
            title="🚨 Overall Dropout Risk",
            color_discrete_sequence=["#66bb6a", "#ffa726", "#ef5350"],
            hole=0.4
        )
        fig3.update_traces(textposition='inside', textinfo='percent+label', textfont_size=14)
        fig3.update_layout(
            title_font=dict(size=18, color='#c62828', family='Arial Black'),
            paper_bgcolor='rgba(255,255,255,0.9)'
        )
        st.plotly_chart(fig3, use_container_width=True)

    # Row 2: Department analysis
    st.markdown("#### 🏢 Department-wise Analysis")
    col4, col5 = st.columns(2)

    with col4:
        dept_perf = subset.groupby(['DEPT', 'perf_label']).size().reset_index(name='count')
        fig4 = px.bar(
            dept_perf,
            x="DEPT",
            y="count",
            color="perf_label",
            title="🏢 Department vs Performance Labels",
            barmode="stack",
            color_discrete_map={'high': '#66bb6a', 'medium': '#ffa726', 'poor': '#ef5350'}
        )
        fig4.update_layout(
            plot_bgcolor='rgba(255,245,245,0.5)',
            paper_bgcolor='rgba(255,255,255,0.9)',
            title_font=dict(size=18, color='#c62828'),
            xaxis_title="Department",
            yaxis_title="Number of Students"
        )
        st.plotly_chart(fig4, use_container_width=True)

    with col5:
        dept_avg = subset.groupby('DEPT')['perf_score'].mean().sort_values(ascending=False).reset_index()
        fig5 = px.bar(
            dept_avg,
            x="DEPT",
            y="perf_score",
            title="📈 Average Performance Score by Department",
            color="perf_score",
            color_continuous_scale=["#ef5350", "#ffa726", "#66bb6a"],
            text="perf_score"
        )
        fig5.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
        fig5.update_layout(
            plot_bgcolor='rgba(255,245,245,0.5)',
            paper_bgcolor='rgba(255,255,255,0.9)',
            title_font=dict(size=18, color='#c62828'),
            yaxis_title="Average Score (%)"
        )
        st.plotly_chart(fig5, use_container_width=True)

    # Row 3: Year-wise analysis
    st.markdown("#### 📅 Year-wise Trends")
    col6, col7 = st.columns(2)

    with col6:
        year_perf = subset.groupby(['YEAR', 'perf_label']).size().reset_index(name='count')
        fig6 = px.bar(
            year_perf,
            x="YEAR",
            y="count",
            color="perf_label",
            title="📅 Year-wise Performance Distribution",
            barmode="group",
            color_discrete_map={'high': '#66bb6a', 'medium': '#ffa726', 'poor': '#ef5350'}
        )
        fig6.update_layout(
            plot_bgcolor='rgba(255,245,245,0.5)',
            paper_bgcolor='rgba(255,255,255,0.9)',
            title_font=dict(size=18, color='#c62828')
        )
        st.plotly_chart(fig6, use_container_width=True)

    with col7:
        year_avg = subset.groupby('YEAR')['perf_score'].mean().reset_index()
        fig7 = px.line(
            year_avg,
            x="YEAR",
            y="perf_score",
            title="📈 Average Performance Trend by Year",
            markers=True,
            line_shape='spline'
        )
        fig7.update_traces(line=dict(color='#ef5350', width=4), marker=dict(size=12))
        fig7.update_layout(
            plot_bgcolor='rgba(255,245,245,0.5)',
            paper_bgcolor='rgba(255,255,255,0.9)',
            title_font=dict(size=18, color='#c62828'),
            yaxis_title="Average Score (%)",
            yaxis_range=[0, 100]
        )
        st.plotly_chart(fig7, use_container_width=True)

    # Row 4: Advanced visualizations
    st.markdown("#### 🔬 Advanced Analytics")
    col8, col9 = st.columns(2)

    with col8:
        # Department-Year heatmap
        dept_year_pivot = subset.groupby(['DEPT', 'YEAR']).size().reset_index(name='count')
        dept_year_matrix = dept_year_pivot.pivot(index='DEPT', columns='YEAR', values='count').fillna(0)
        fig8 = px.imshow(
            dept_year_matrix,
            title="🔥 Department-Year Heatmap (Student Count)",
            color_continuous_scale='Reds',
            labels=dict(x="Year", y="Department", color="Students"),
            aspect="auto"
        )
        fig8.update_layout(
            title_font=dict(size=18, color='#c62828'),
            paper_bgcolor='rgba(255,255,255,0.9)'
        )
        st.plotly_chart(fig8, use_container_width=True)

    with col9:
        # Treemap: Dept -> Year -> Performance
        fig9 = px.treemap(
            subset,
            path=['DEPT', 'YEAR', 'perf_label'],
            title="🌳 Hierarchical Performance View",
            color='perf_label',
            color_discrete_map={'high': '#66bb6a', 'medium': '#ffa726', 'poor': '#ef5350'}
        )
        fig9.update_layout(
            title_font=dict(size=18, color='#c62828'),
            paper_bgcolor='rgba(255,255,255,0.9)'
        )
        st.plotly_chart(fig9, use_container_width=True)

    # Row 5: Score distributions
    st.markdown("#### 📊 Score Distribution Analysis")
    col10, col11 = st.columns(2)

    with col10:
        fig10 = px.histogram(
            subset,
            x="perf_score",
            nbins=30,
            title="📊 Performance Score Distribution",
            color_discrete_sequence=['#ef5350'],
            marginal="box"
        )
        fig10.update_layout(
            plot_bgcolor='rgba(255,245,245,0.5)',
            paper_bgcolor='rgba(255,255,255,0.9)',
            title_font=dict(size=18, color='#c62828'),
            xaxis_title="Performance Score",
            yaxis_title="Frequency"
        )
        st.plotly_chart(fig10, use_container_width=True)

    with col11:
        fig11 = px.box(
            subset,
            x="DEPT",
            y="perf_score",
            title="📦 Performance Score Distribution by Department",
            color="DEPT",
            points="outliers"
        )
        fig11.update_layout(
            plot_bgcolor='rgba(255,245,245,0.5)',
            paper_bgcolor='rgba(255,255,255,0.9)',
            title_font=dict(size=18, color='#c62828'),
            showlegend=False
        )
        st.plotly_chart(fig11, use_container_width=True)

    # Row 6: 3D Scatter and Parallel coordinates
    st.markdown("#### 🎨 Multi-dimensional Analysis")
    col12, col13 = st.columns(2)

    with col12:
        fig12 = px.scatter_3d(
            subset.sample(min(500, len(subset))),  # Sample for performance
            x="perf_score",
            y="risk_score",
            z="drop_score",
            color="perf_label",
            title="🎯 3D Performance Analysis",
            color_discrete_map={'high': '#66bb6a', 'medium': '#ffa726', 'poor': '#ef5350'},
            size=[5]*min(500, len(subset))
        )
        fig12.update_layout(
            title_font=dict(size=18, color='#c62828'),
            paper_bgcolor='rgba(255,255,255,0.9)',
            scene=dict(
                xaxis_title="Performance",
                yaxis_title="Risk",
                zaxis_title="Dropout"
            )
        )
        st.plotly_chart(fig12, use_container_width=True)

    with col13:
        # Parallel coordinates
        parallel_df = subset[['perf_score', 'risk_score', 'drop_score', 'perf_label']].copy()
        parallel_df['label_code'] = parallel_df['perf_label'].map({'high': 2, 'medium': 1, 'poor': 0})

        fig13 = px.parallel_coordinates(
            parallel_df.sample(min(200, len(parallel_df))),
            dimensions=['perf_score', 'risk_score', 'drop_score'],
            color='label_code',
            title="🌈 Parallel Coordinates Analysis",
            color_continuous_scale=[(0, '#ef5350'), (0.5, '#ffa726'), (1, '#66bb6a')],
            labels={'perf_score': 'Performance', 'risk_score': 'Risk', 'drop_score': 'Dropout'}
        )
        fig13.update_layout(
            title_font=dict(size=18, color='#c62828'),
            paper_bgcolor='rgba(255,255,255,0.9)'
        )
        st.plotly_chart(fig13, use_container_width=True)

    st.markdown("---")

    # College Summary
    st.markdown("### 📝 College Performance Summary & Insights")

    summary_col1, summary_col2 = st.columns([2, 1])

    with summary_col1:
        st.markdown("#### 📊 Department Rankings")
        dept_summary = subset.groupby('DEPT').agg({
            'perf_score': 'mean',
            'RNO': 'count',
            'risk_score': 'mean',
            'drop_score': 'mean'
        }).round(2)
        dept_summary.columns = ['Avg Performance', 'Total Students', 'Avg Risk', 'Avg Dropout Risk']
        dept_summary = dept_summary.sort_values('Avg Performance', ascending=False)
        dept_summary['Rank'] = range(1, len(dept_summary) + 1)
        dept_summary = dept_summary[['Rank', 'Total Students', 'Avg Performance', 'Avg Risk', 'Avg Dropout Risk']]
        st.dataframe(dept_summary, use_container_width=True)

    with summary_col2:
        st.markdown("#### 🏆 Key Highlights")
        best_dept = dept_summary.index[0]
        best_score = dept_summary.iloc[0]['Avg Performance']
        high_risk_pct = (subset['risk_label'] == 'high').sum() / len(subset) * 100
        high_perf_pct = (subset['perf_label'] == 'high').sum() / len(subset) * 100

        st.metric("🥇 Top Department", best_dept)
        st.metric("📈 Best Avg Score", f"{best_score:.1f}%")
        st.metric("⭐ High Performers", f"{high_perf_pct:.1f}%")
        st.metric("⚠️ High Risk %", f"{high_risk_pct:.1f}%")

    # Actionable insights
    st.markdown("#### 💡 Actionable Insights & Recommendations")

    insights = []

    # Performance insights
    if high_perf_pct < 30:
        insights.append("🔴 **Critical**: Less than 30% students are high performers. Immediate academic intervention required across all departments.")
    elif high_perf_pct < 50:
        insights.append("🟡 **Warning**: Only {:.1f}% students are high performers. Consider implementing mentorship programs.".format(high_perf_pct))
    else:
        insights.append("🟢 **Excellent**: {:.1f}% students are high performers. Continue current academic strategies.".format(high_perf_pct))

    # Risk insights
    if high_risk_pct > 20:
        insights.append("🚨 **Alert**: {:.1f}% students are at high risk. Deploy counselors and mentors immediately.".format(high_risk_pct))
    elif high_risk_pct > 10:
        insights.append("⚠️ **Caution**: {:.1f}% students show high risk indicators. Monitor closely.".format(high_risk_pct))

    # Department insights
    worst_dept = dept_summary.index[-1]
    worst_score = dept_summary.iloc[-1]['Avg Performance']
    if worst_score < 50:
        insights.append(f"📉 **Department Focus**: {worst_dept} department needs urgent attention (Avg: {worst_score:.1f}%).")

    # Dropout insights
    high_dropout = (subset['drop_label'] == 'high').sum()
    if high_dropout > len(subset) * 0.15:
        insights.append(f"🚨 **Dropout Alert**: {high_dropout} students at high dropout risk. Initiate retention programs.")

    for insight in insights:
        st.markdown(f"<div class='metric-card'>{insight}</div>", unsafe_allow_html=True)

    st.markdown("---")

    # Export options
    st.markdown("### 📥 Export College-wide Data & Reports")

    export_col1, export_col2, export_col3 = st.columns(3)

    with export_col1:
        full_csv = subset.to_csv(index=False).encode('utf-8')
        st.download_button(
            "📊 Export Full Database (CSV)",
            data=full_csv,
            file_name="college_complete_data.csv",
            mime="text/csv",
            use_container_width=True
        )

    with export_col2:
        summary_csv = dept_summary.to_csv().encode('utf-8')
        st.download_button(
            "📄 Export Department Summary (CSV)",
            data=summary_csv,
            file_name="college_department_summary.csv",
            mime="text/csv",
            use_container_width=True
        )

    with export_col3:
        # Create executive summary
        exec_summary = pd.DataFrame({
            'Metric': [
                'Total Students',
                'Total Departments',
                'Average Performance',
                'High Performers',
                'Students at Risk',
                'High Dropout Risk',
                'Top Department',
                'Top Dept Score'
            ],
            'Value': [
                len(subset),
                subset['DEPT'].nunique(),
                f"{subset['perf_score'].mean():.2f}%",
                f"{(subset['perf_label'] == 'high').sum()} ({high_perf_pct:.1f}%)",
                f"{(subset['risk_label'] == 'high').sum()} ({high_risk_pct:.1f}%)",
                f"{high_dropout} ({high_dropout/len(subset)*100:.1f}%)",
                best_dept,
                f"{best_score:.2f}%"
            ]
        })
        exec_csv = exec_summary.to_csv(index=False).encode('utf-8')
        st.download_button(
            "📋 Export Executive Summary (CSV)",
            data=exec_csv,
            file_name="college_executive_summary.csv",
            mime="text/csv",
            use_container_width=True
        )

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; padding: 20px; background: rgba(255,255,255,0.8); border-radius: 10px;'>
    <p style='color: #c62828; font-size: 16px; font-weight: 600;'>
        🎓 Intelligent Student Performance Analytics System
    </p>
    <p style='color: #666; font-size: 14px;'>
        Powered by Machine Learning | Built with Streamlit & Plotly
    </p>
</div>
""", unsafe_allow_html=True)
