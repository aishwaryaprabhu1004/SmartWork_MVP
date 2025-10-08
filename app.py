import streamlit as st
import pandas as pd

# ---------------- Page Config ----------------
st.set_page_config(
    page_title="SmartWork.AI",
    page_icon="💡",
    layout="wide"
)

# ---------------- Sidebar Icons ----------------
st.sidebar.markdown("## 💡 SmartWork.AI")
page = st.sidebar.radio(
    "",
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
if 'activity' not in st.session_state:
    st.session_state['activity'] = pd.DataFrame()
if 'skills' not in st.session_state:
    st.session_state['skills'] = pd.DataFrame()
if 'projects' not in st.session_state:
    st.session_state['projects'] = pd.DataFrame()

# ---------------- Helper Functions ----------------
def load_file(file):
    if file is not None:
        return pd.read_csv(file) if file.name.endswith(".csv") else pd.read_excel(file)
    return pd.DataFrame()

def calculate_utilization(df):
    if df.empty: return df
    df['Activity_Score'] = (
        0.4*df.get('Tasks_Completed',0) +
        0.3*df.get('Meetings_Duration',0) +
        0.2*df.get('Decisions_Made',0) +
        0.1*df.get('Docs_Updated',0)
    )
    df['True_Utilization'] = (df['Activity_Score'] / df['Activity_Score'].max())*100
    df['Bench_Status'] = df['True_Utilization'].apply(
        lambda x: "On Bench" if x<20 else ("Partially Utilized" if x<50 else "Fully Utilized")
    )
    return df

def recommend_skills(df_emp, df_skills):
    if df_emp.empty or df_skills.empty: return df_emp
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

# ---------------- Lazy Plotly Imports ----------------
def plot_bar(df, x, y, color):
    import plotly.express as px
    return px.bar(df, x=x, y=y, color=color, template="plotly_white")

def plot_scatter(df, x, y, color):
    import plotly.express as px
    return px.scatter(df, x=x, y=y, color=color, template="plotly_white", hover_data=['Employee'])

# ---------------- Pages ----------------
if page=="📤 Upload Data":
    st.header("Upload Data 📤")
    col1, col2, col3 = st.columns(3)
    with col1:
        activity_file = st.file_uploader("Employee Activity", type=["csv","xlsx"])
        if activity_file:
            st.session_state['activity'] = load_file(activity_file)
            st.success("✅ Employee Activity uploaded")
    with col2:
        skills_file = st.file_uploader("Skill Training", type=["csv","xlsx"])
        if skills_file:
            st.session_state['skills'] = load_file(skills_file)
            st.success("✅ Skill Training uploaded")
    with col3:
        projects_file = st.file_uploader("Project Assignment", type=["csv","xlsx"])
        if projects_file:
            st.session_state['projects'] = load_file(projects_file)
            st.success("✅ Project Assignments uploaded")

elif page=="🏠 Dashboard":
    st.header("Dashboard 🏠")
    df = calculate_utilization(st.session_state['activity'])
    if df.empty:
        st.info("Upload Employee Activity first")
    else:
        # KPI Cards compact layout
        total_emp = len(df)
        bench_count = len(df[df['Bench_Status']=="On Bench"])
        part_util = len(df[df['Bench_Status']=="Partially Utilized"])
        full_util = len(df[df['Bench_Status']=="Fully Utilized"])
        kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)
        kpi_col1.metric("Total Employees", total_emp)
        kpi_col2.metric("On Bench", bench_count)
        kpi_col3.metric("Partial Utilization", part_util)
        kpi_col4.metric("Full Utilization", full_util)
        
        # Charts side by side
        bench_chart = df['Bench_Status'].value_counts().reset_index()
        bench_chart.columns = ['Bench Status','Count']
        chart_col1, chart_col2 = st.columns(2)
        chart_col1.plotly_chart(plot_bar(bench_chart,'Bench Status','Count','Bench Status'), use_container_width=True)
        dept_util = df.groupby('Dept')['True_Utilization'].mean().reset_index()
        chart_col2.plotly_chart(plot_bar(dept_util,'Dept','True_Utilization','Dept'), use_container_width=True)

elif page=="🪑 Bench Utilization":
    st.header("Bench Utilization 🪑")
    df = calculate_utilization(st.session_state['activity'])
    if df.empty:
        st.info("Upload Employee Activity first")
    else:
        st.dataframe(df[['Employee','Dept','Bench_Status','True_Utilization']], height=450)

elif page=="🎯 Skill Recommendations":
    st.header("Skill Recommendations 🎯")
    df = recommend_skills(st.session_state['activity'], st.session_state['skills'])
    if df.empty:
        st.info("Upload Employee Activity and Skills file first")
    else:
        st.dataframe(df[['Employee','Skills','Recommended_Skills','Bench_Status']], height=450)

elif page=="🚀 Project Assignment":
    st.header("Project Assignment 🚀")
    df = assign_projects(st.session_state['activity'], st.session_state['projects'])
    if df.empty:
        st.info("Upload Employee Activity and Projects file first")
    else:
        st.dataframe(df, height=450)

elif page=="📈 Analytics":
    st.header("Analytics 📈")
    df = calculate_utilization(st.session_state['activity'])
    if df.empty:
        st.info("Upload Employee Activity first")
    else:
        # Grid layout for analytics
        col1, col2 = st.columns(2)
        col1.plotly_chart(plot_scatter(df,'Bench_Duration','True_Utilization','Bench_Status'), use_container_width=True)
        dept_util = df.groupby('Dept')['True_Utilization'].mean().reset_index()
        col2.plotly_chart(plot_bar(dept_util,'Dept','True_Utilization','Dept'), use_container_width=True)
