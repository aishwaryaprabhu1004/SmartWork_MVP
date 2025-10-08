import streamlit as st
import pandas as pd
import altair as alt
import os

# ---------------- Page Config ----------------
st.set_page_config(
    page_title="SmartWork.AI",
    page_icon="💡",
    layout="wide"
)

# ---------------- Session State ----------------
if 'activity' not in st.session_state: st.session_state['activity'] = pd.DataFrame()
if 'skills' not in st.session_state: st.session_state['skills'] = pd.DataFrame()
if 'projects' not in st.session_state: st.session_state['projects'] = pd.DataFrame()
if 'role' not in st.session_state: st.session_state['role'] = "HR Head"

# ---------------- Top Bar ----------------
top_col1, top_col2 = st.columns([1, 3])
with top_col1:
    logo_path = "logo.png"
    if os.path.exists(logo_path):
        st.image(logo_path, width=250)  # Bigger logo

# ---------------- Sidebar ----------------
sidebar_items = ["🏠 Homepage", "🏠 Dashboard & Analytics", "🎯 Skill Recommendations", "🚀 Project Assignment", "📤 Upload Data"]
if st.session_state['role'] == "Project Manager":
    sidebar_items = ["🏠 Homepage", "🏠 Dashboard & Analytics", "🚀 Project Assignment", "📤 Upload Data"]

page = st.sidebar.radio("Navigation", options=sidebar_items)

# ---------------- Helper Functions ----------------
def load_file(file):
    if file:
        try:
            if file.name.endswith(".csv"):
                return pd.read_csv(file)
            else:
                return pd.read_excel(file, engine='openpyxl')
        except ImportError:
            st.error("openpyxl not installed. Please upload CSV instead.")
            return pd.DataFrame()
    return pd.DataFrame()

def calculate_utilization(df):
    if df.empty: 
        return df
    df['Activity_Score'] = (
        0.4*df.get('Tasks_Completed',0) +
        0.3*df.get('Meetings_Duration',0) +
        0.2*df.get('Decisions_Made',0) +
        0.1*df.get('Docs_Updated',0)
    )
    df['True_Utilization'] = (df['Activity_Score'] / df['Activity_Score'].max()) * 100
    df['Bench_Status'] = df['True_Utilization'].apply(
        lambda x: "On Bench" if x<20 else ("Partially Utilized" if x<50 else "Fully Utilized")
    )
    return df

# ---------------- Pages ----------------
if page == "🏠 Homepage":
    st.markdown("<h1 style='text-align: center; color: #2E3A59;'>SmartWork.AI</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-size:20px; color: #4B4B4B;'>AI-powered tool for CHROs</p>", unsafe_allow_html=True)

    # Role selector below description
    st.session_state['role'] = st.selectbox("Select your role:", ["HR Head", "Project Manager"], index=0, label_visibility="visible")

    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Employees", "50")
    col2.metric("Projects Ongoing", "12")
    col3.metric("Bench Employees", "3")
    st.markdown("---")
    st.markdown("""
    ### Key Features
    - 📊 **Dashboard & Analytics**: Real-time insights on utilization & performance.
    - 🎯 **Skill Recommendations**: Identify skill gaps and upskilling suggestions.
    - 🚀 **Project Assignment**: Intelligent project-employee matching.
    - 📤 **Data Upload**: Manage employee, skill, and project data easily.
    """)

elif page == "📤 Upload Data":
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

elif page == "🏠 Dashboard & Analytics":
    st.subheader("Dashboard & Analytics 🏠📈")
    df = calculate_utilization(st.session_state['activity'])
    if df.empty:
        st.info("Upload Employee Activity first")
    else:
        # KPIs
        total_emp = len(df)
        bench_count = len(df[df['Bench_Status']=="On Bench"])
        part_util = len(df[df['Bench_Status']=="Partially Utilized"])
        full_util = len(df[df['Bench_Status']=="Fully Utilized"])
        k1,k2,k3,k4 = st.columns([1,1,1,1])
        k1.metric("Total Employees", total_emp)
        k2.metric("On Bench", bench_count)
        k3.metric("Partial Utilization", part_util)
        k4.metric("Full Utilization", full_util)

        # Bench Status Bar Chart
        bench_chart = df['Bench_Status'].value_counts().reset_index()
        bench_chart.columns = ['Bench_Status','Count']
        chart1 = alt.Chart(bench_chart).mark_bar().encode(
            x='Bench_Status',
            y='Count',
            color='Bench_Status'
        )
        st.altair_chart(chart1, use_container_width=True)

        # Dept Utilization Bar Chart
        dept_util = df.groupby('Dept')['True_Utilization'].mean().reset_index()
        chart2 = alt.Chart(dept_util).mark_bar().encode(
            x='Dept',
            y='True_Utilization',
            color='Dept'
        )
        st.altair_chart(chart2, use_container_width=True)

        # Line chart with connected points
        line_chart = alt.Chart(df).mark_line(point=True).encode(
            x='Employee',
            y='True_Utilization',
            color='Dept',
            tooltip=['Employee','Dept','True_Utilization']
        )
        st.altair_chart(line_chart, use_container_width=True)

        # AI Recommendations for HR Head
        if st.session_state['role'] == "HR Head":
            st.subheader("AI Recommendations 🔹")
            st.markdown("""
            - Reallocate underutilized employees to high-demand projects.
            - Upskill employees based on missing skills from upcoming projects.
            - Optimize bench duration to reduce idle costs.
            - Align project staffing to critical deadlines.
            - Deploy cost-efficient contractors where utilization is low.
            """)

        st.dataframe(df[['Employee','Dept','Bench_Status','True_Utilization']], height=300)

elif page == "🎯 Skill Recommendations":
    st.subheader("Skill Recommendations 🎯")
    df_emp = st.session_state['activity']
    df_skills = st.session_state['skills']
    if df_emp.empty or df_skills.empty: st.info("Upload both Employee Activity and Skills file first")
    else:
        required_skills = df_skills['Skill'].unique().tolist()
        def rec(skills_str):
            emp_skills = str(skills_str).split(",") if pd.notnull(skills_str) else []
            missing = list(set(required_skills) - set(emp_skills))
            return ", ".join(missing) if missing else "None"
        df_emp['Recommended_Skills'] = df_emp['Skills'].apply(rec)
        st.dataframe(df_emp[['Employee','Skills','Recommended_Skills','Bench_Status']], height=400)

elif page == "🚀 Project Assignment":
    st.subheader("Project Assignment 🚀")
    df_emp = st.session_state['activity']
    df_proj = st.session_state['projects']
    if df_emp.empty or df_proj.empty:
        st.info("Upload Employee Activity and Project Assignment file first")
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




