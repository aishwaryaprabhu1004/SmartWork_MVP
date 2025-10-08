import streamlit as st
import pandas as pd
import plotly.express as px

# ---------------- Page Config ----------------
st.set_page_config(
    page_title="SmartWork.AI",
    page_icon="💡",
    layout="wide"
)

# ---------------- Custom Sidebar ----------------
st.markdown("""
<style>
[data-testid="stSidebar"] {width: 220px;}
.sidebar .sidebar-content {display: flex; flex-direction: column; align-items: flex-start;}
.sidebar .sidebar-content div[role="radiogroup"] > label {font-size: 20px; padding: 10px 0;}
</style>
""", unsafe_allow_html=True)

# ---------------- Sidebar ----------------
page = st.sidebar.radio(
    "Navigation",
    options=[
        "🏠 Dashboard",
        "🪑 Bench Utilization",
        "🎯 Skill Recommendations",
        "🚀 Project Assignment",
        "📤 Upload Data",
        "📈 Analytics"
    ]
)

# ---------------- Session State ----------------
if 'activity' not in st.session_state: st.session_state['activity'] = pd.DataFrame()
if 'skills' not in st.session_state: st.session_state['skills'] = pd.DataFrame()
if 'projects' not in st.session_state: st.session_state['projects'] = pd.DataFrame()

# ---------------- Helper Functions ----------------
def load_file(file):
    if file:
        if file.name.endswith(".csv"):
            return pd.read_csv(file)
        else:
            return pd.read_excel(file)
    return pd.DataFrame()

def calculate_utilization(df):
    if df.empty: return df
    df['Activity_Score'] = (
        0.4*df.get('Tasks_Completed',0) +
        0.3*df.get('Meetings_Duration',0) +
        0.2*df.get('Decisions_Made',0) +
        0.1*df.get('Docs_Updated',0)
    )
    df['True_Utilization'] = (df['Activity_Score']/df['Activity_Score'].max())*100
    df['Bench_Status'] = df['True_Utilization'].apply(
        lambda x: "On Bench" if x<20 else ("Partially Utilized" if x<50 else "Fully Utilized")
    )
    return df

# ---------------- Pages ----------------
if page=="📤 Upload Data":
    st.subheader("Upload Data 📤")
    col1, col2, col3 = st.columns(3)
    with col1:
        f1 = st.file_uploader("Employee Activity", type=["csv","xlsx"])
        if f1: st.session_state['activity'] = load_file(f1)
    with col2:
        f2 = st.file_uploader("Skill Training", type=["csv","xlsx"])
        if f2: st.session_state['skills'] = load_file(f2)
    with col3:
        f3 = st.file_uploader("Project Assignment", type=["csv","xlsx"])
        if f3: st.session_state['projects'] = load_file(f3)

elif page=="🏠 Dashboard":
    st.subheader("Dashboard 🏠")
    df = calculate_utilization(st.session_state['activity'])
    if df.empty:
        st.info("Upload Employee Activity first")
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

        col1, col2, col3 = st.columns(3)
        bench_chart = df['Bench_Status'].value_counts().reset_index()
        bench_chart.columns = ['Bench','Count']
        col1.plotly_chart(px.bar(bench_chart,'Bench','Count',color='Bench',height=300,template="plotly_white"), use_container_width=True)

        dept_util = df.groupby('Dept')['True_Utilization'].mean().reset_index()
        col2.plotly_chart(px.bar(dept_util,'Dept','True_Utilization','Dept',height=300,template="plotly_white"), use_container_width=True)

        col3.dataframe(df[['Employee','Dept','Bench_Status','True_Utilization']], height=300)

elif page=="🪑 Bench Utilization":
    st.subheader("Bench Utilization 🪑")
    df = calculate_utilization(st.session_state['activity'])
    if df.empty:
        st.info("Upload Employee Activity first")
    else:
        st.dataframe(df[['Employee','Dept','Bench_Status','True_Utilization']], height=400)

elif page=="🎯 Skill Recommendations":
    st.subheader("Skill Recommendations 🎯")
    df_emp = st.session_state['activity']
    df_skills = st.session_state['skills']
    if df_emp.empty or df_skills.empty:
        st.info("Upload both Employee Activity and Skills file first")
    else:
        required_skills = df_skills['Skill'].unique().tolist()
        def rec(skills_str):
            emp_skills = str(skills_str).split(",") if pd.notnull(skills_str) else []
            missing = list(set(required_skills) - set(emp_skills))
            return ", ".join(missing) if missing else "None"
        df_emp['Recommended_Skills'] = df_emp['Skills'].apply(rec)
        st.dataframe(df_emp[['Employee','Skills','Recommended_Skills','Bench_Status']], height=400)

elif page=="🚀 Project Assignment":
    st.subheader("Project Assignment 🚀")
    df_emp = st.session_state['activity']
    df_proj = st.session_state['projects']
    if df_emp.empty or df_proj.empty:
        st.info("Upload both Employee Activity and Project files first")
    else:
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
        st.dataframe(pd.DataFrame(assignments), height=400)

elif page=="📈 Analytics":
    st.subheader("Analytics 📈")
    df = calculate_utilization(st.session_state['activity'])
    if df.empty:
        st.info("Upload Employee Activity first")
    else:
        c1,c2 = st.columns(2)
        if 'Bench_Duration' in df.columns:
            c1.plotly_chart(px.scatter(df,'Bench_Duration','True_Utilization','Bench_Status',hover_data=['Employee'],height=300,template="plotly_white"), use_container_width=True)
        dept_util = df.groupby('Dept')['True_Utilization'].mean().reset_index()
        c2.plotly_chart(px.bar(dept_util,'Dept','True_Utilization','Dept',height=300,template="plotly_white"), use_container_width=True)

