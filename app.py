import streamlit as st
import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler

# ---------------- Page Config ----------------
st.set_page_config(
    page_title="SmartWork.AI",
    page_icon="💡",
    layout="wide"
)

# ---------------- Sidebar ----------------
st.markdown("""
<style>
[data-testid="stSidebar"] { width: 200px; }
.sidebar .sidebar-content { display: flex; flex-direction: column; align-items: center; }
.sidebar .sidebar-content div[role="radiogroup"] > label { font-size: 20px; padding: 10px 0; }
</style>
""", unsafe_allow_html=True)

page = st.sidebar.radio(
    "",
    ["🏠 Dashboard", "🪑 Bench Utilization", "🎯 Skill Recommendations", "🚀 Project Assignment", "📤 Upload Data", "📈 Analytics"]
)

# ---------------- Session State ----------------
if 'activity' not in st.session_state: st.session_state['activity'] = pd.DataFrame()
if 'skills' not in st.session_state: st.session_state['skills'] = pd.DataFrame()
if 'projects' not in st.session_state: st.session_state['projects'] = pd.DataFrame()

# ---------------- Helper Functions ----------------
def load_file(file):
    if file: 
        return pd.read_csv(file) if file.name.endswith(".csv") else pd.read_excel(file)
    return pd.DataFrame()

def calculate_utilization(df):
    if df.empty: return df
    # Activity score weighted by real-world metrics
    df['Activity_Score'] = (
        0.4*df.get('Tasks_Completed',0) +
        0.3*df.get('Meetings_Duration',0) +
        0.2*df.get('Decisions_Made',0) +
        0.1*df.get('Docs_Updated',0)
    )
    # Normalize score to 0-100
    scaler = MinMaxScaler()
    df['True_Utilization'] = scaler.fit_transform(df[['Activity_Score']])*100
    
    # AI-based Bench Prediction
    df['Bench_Probability'] = 100 - df['True_Utilization']
    
    df['Bench_Status'] = df['True_Utilization'].apply(
        lambda x: "On Bench" if x<20 else ("Partially Utilized" if x<50 else "Fully Utilized")
    )
    return df

def recommend_skills(df_emp, df_skills):
    if df_emp.empty or df_skills.empty: return pd.DataFrame()
    required_skills = df_skills['Skill'].unique().tolist()
    def rec(skills_str):
        emp_skills = str(skills_str).split(",") if pd.notnull(skills_str) else []
        missing = list(set(required_skills) - set(emp_skills))
        return ", ".join(missing) if missing else "None"
    df_emp['Recommended_Skills'] = df_emp['Skills'].apply(rec)
    return df_emp

def assign_projects(df_emp, df_proj):
    if df_emp.empty or df_proj.empty: return pd.DataFrame()
    assignments = []
    for _, emp in df_emp.iterrows():
        emp_skills = set(str(emp.get('Skills','')).split(","))
        for _, proj in df_proj.iterrows():
            proj_skills = set(str(proj.get('Required_Skills','')).split(","))
            if emp_skills & proj_skills:
                assignments.append({
                    'Employee': emp.get('Employee',''),
                    'Project': proj.get('Project_Name',''),
                    'Skill_Match': ", ".join(emp_skills & proj_skills)
                })
    return pd.DataFrame(assignments)

# ---------------- Pages ----------------
if page=="📤 Upload Data":
    st.subheader("Upload Data 📤")
    col1, col2, col3 = st.columns([1,1,1])
    with col1:
        f1 = st.file_uploader("Employee Activity", type=["csv","xlsx"])
        if f1: st.session_state['activity'] = load_file(f1)
    with col2:
        f2 = st.file_uploader("Skill Training", type=["csv","xlsx"])
        if f2: st.session_state['skills'] = load_file(f2)
    with col3:
        f3 = st.file_uploader("Project Assignment", type=["csv","xlsx"])
        if f3: st.session_state['projects'] = load_file(f3)
    st.info("Upload all three files to enable full functionality")

elif page=="🏠 Dashboard":
    st.subheader("Dashboard 🏠")
    df = calculate_utilization(st.session_state['activity'])
    if df.empty: st.info("Upload Employee Activity first")
    else:
        total_emp = len(df)
        bench_count = len(df[df['Bench_Status']=="On Bench"])
        part_util = len(df[df['Bench_Status']=="Partially Utilized"])
        full_util = len(df[df['Bench_Status']=="Fully Utilized"])

        k1,k2,k3,k4 = st.columns(4)
        k1.metric("Total Employees", total_emp)
        k2.metric("On Bench", bench_count)
        k3.metric("Partial Utilization", part_util)
        k4.metric("Full Utilization", full_util)

        col1, col2 = st.columns(2)
        col1.dataframe(df[['Employee','Dept','Bench_Status','True_Utilization','Bench_Probability']], height=400)

elif page=="🪑 Bench Utilization":
    st.subheader("Bench Utilization 🪑")
    df = calculate_utilization(st.session_state['activity'])
    if df.empty: st.info("Upload Employee Activity first")
    else:
        st.dataframe(df[['Employee','Dept','Bench_Status','True_Utilization','Bench_Probability']], height=400)

elif page=="🎯 Skill Recommendations":
    st.subheader("Skill Recommendations 🎯")
    df_emp = recommend_skills(st.session_state['activity'], st.session_state['skills'])
    if df_emp.empty: st.info("Upload both Employee Activity and Skills file first")
    else:
        st.dataframe(df_emp[['Employee','Skills','Recommended_Skills','Bench_Status']], height=400)

elif page=="🚀 Project Assignment":
    st.subheader("Project Assignment 🚀")
    df_assign = assign_projects(st.session_state['activity'], st.session_state['projects'])
    if df_assign.empty: st.info("Upload Employee Activity and Project Assignment files first")
    else:
        st.dataframe(df_assign, height=400)

elif page=="📈 Analytics":
    st.subheader("Analytics 📈")
    df = calculate_utilization(st.session_state['activity'])
    if df.empty: st.info("Upload Employee Activity first")
    else:
        c1, c2 = st.columns(2)
        # Bench probability analysis
        bench_dist = df['Bench_Status'].value_counts().reset_index()
        bench_dist.columns = ['Bench','Count']
        c1.bar_chart(bench_dist.set_index('Bench'))
        
        dept_util = df.groupby('Dept')['True_Utilization'].mean().reset_index()
        c2.bar_chart(dept_util.set_index('Dept'))
