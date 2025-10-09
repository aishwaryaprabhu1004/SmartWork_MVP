import streamlit as st
import pandas as pd
import altair as alt
import numpy as np

# ---------------- Page Config ----------------
st.set_page_config(
    page_title="SmartWork.AI",
    page_icon="💡",
    layout="wide"
)

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

def ai_recommendations(activity_df, project_df, role='HR Head'):
    recs = []
    if activity_df.empty or project_df.empty:
        return ["Upload Employee and Project data for recommendations."]
    
    df = calculate_utilization(activity_df.copy())
    
    # Underutilized employees
    underutilized = df[df['True_Utilization'] < 50]
    for i, emp in underutilized.head(3).iterrows():
        recs.append(f"Employee {emp['Employee']} is underutilized. Reassigning could improve utilization by 15-20%.")

    # Project skill gaps
    for _, proj in project_df.iterrows():
        required_skills = set(str(proj.get('Required_Skills','')).split(","))
        available_skills = set(",".join(df['Skills'].dropna()).split(","))
        missing = required_skills - available_skills
        if missing:
            recs.append(f"Project {proj['Project_Name']} lacks {', '.join(missing)}. Upskilling or reallocating employees may improve project delivery efficiency by ~10%.")

    # Bench cost optimization (only HR Head)
    if role=='HR Head' and 'Cost' in df.columns:
        bench_emps = df[df['True_Utilization']<20]
        total_saving = bench_emps['Cost'].sum() * 0.1
        recs.append(f"Reducing bench time for underutilized employees can save approx ${total_saving:.2f}, improving overall utilization by 8-12%.")
    
    return recs[:5]

def skill_recommendations(df_emp, df_skills, top_n=2):
    required_skills = df_skills['Skill'].unique().tolist()
    def rec(skills_str):
        emp_skills = str(skills_str).split(",") if pd.notnull(skills_str) else []
        missing = list(set(required_skills) - set(emp_skills))
        return ", ".join(missing[:top_n]) if missing else "None"
    df_emp['Recommended_Skills'] = df_emp['Skills'].apply(rec)
    return df_emp

# ---------------- Session State ----------------
for key in ['activity','skills','projects','reportees','selected_manager']:
    if key not in st.session_state:
        st.session_state[key] = pd.DataFrame()

if 'role' not in st.session_state:
    st.session_state['role'] = 'HR Head'

# ---------------- Sidebar ----------------
st.sidebar.title("Navigation")
sidebar_pages = ["Homepage","Upload Data","Project Manager","HR Head"]
page = st.sidebar.selectbox("Select Page", sidebar_pages)

# Display sub-features under roles (indent visually)
if page=="Project Manager":
    st.sidebar.markdown(" Dashboard & Analytics")
    st.sidebar.markdown(" Reportees & Individual Performance")
    st.sidebar.markdown(" AI Recommendations")
elif page=="HR Head":
    st.sidebar.markdown(" Dashboard & Analytics")
    st.sidebar.markdown(" Skill Recommendations")
    st.sidebar.markdown(" Project Assignment")
    st.sidebar.markdown(" AI Recommendations")

# ---------------- Top: Logo and Description ----------------
st.image("logo.png", width=300)
st.markdown("<h2 style='text-align:left'>SmartWork.AI 💡</h2>", unsafe_allow_html=True)
st.markdown("<h4 style='text-align:left'>The AI-powered tool for CHROs</h4>", unsafe_allow_html=True)
st.markdown("Optimize employee utilization, project assignments, and skills with actionable AI-based recommendations.", unsafe_allow_html=True)
st.markdown("---")

# ---------------- Pages ----------------

# ---------- Homepage ----------
if page=="Homepage":
    st.write("Welcome to SmartWork.AI. Navigate through the sidebar to upload data, view dashboards, assign projects, and get AI recommendations.")

# ---------- Upload Data ----------
elif page=="Upload Data":
    st.subheader("Upload Data 📤")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        f1 = st.file_uploader("Employee Activity", type=["csv","xlsx"])
        if f1: st.session_state['activity'] = load_file(f1)
    with col2:
        f2 = st.file_uploader("Skill Training", type=["csv","xlsx"])
        if f2: st.session_state['skills'] = load_file(f2)
    with col3:
        f3 = st.file_uploader("Project Assignment", type=["csv","xlsx"])
        if f3: st.session_state['projects'] = load_file(f3)
    with col4:
        f4 = st.file_uploader("Project Manager Reportees", type=["csv","xlsx"])
        if f4: st.session_state['reportees'] = load_file(f4)

# ---------- Project Manager Pages ----------
elif page=="Project Manager":
    st.subheader("Project Manager Dashboard")
    df = calculate_utilization(st.session_state['activity'])
    proj_df = st.session_state['projects']
    reportees_df = st.session_state['reportees']
    
    if reportees_df.empty:
        st.info("Upload Project Manager Reportees file first")
    else:
        managers = reportees_df['Project_Manager'].unique().tolist()
        selected_manager = st.selectbox("Select Project Manager", managers)
        st.session_state['selected_manager'] = selected_manager
        mgr_reportees = reportees_df[reportees_df['Project_Manager']==selected_manager]['Employee'].tolist()
        df_pm = df[df['Employee'].isin(mgr_reportees)]

        # Dashboard Charts
        st.subheader("Dashboard & Analytics")
        total_emp = len(df_pm)
        bench_count = len(df_pm[df_pm['Bench_Status']=="On Bench"])
        part_util = len(df_pm[df_pm['Bench_Status']=="Partially Utilized"])
        full_util = len(df_pm[df_pm['Bench_Status']=="Fully Utilized"])
        k1,k2,k3,k4 = st.columns(4)
        k1.metric("Total Employees", total_emp)
        k2.metric("On Bench", bench_count)
        k3.metric("Partial Utilization", part_util)
        k4.metric("Full Utilization", full_util)

        # Individual Performance Line Chart
        line_chart = alt.Chart(df_pm.reset_index()).mark_line(point=True).encode(
            x='index',
            y='True_Utilization',
            color='Employee',
            tooltip=['Employee','True_Utilization']
        )
        st.altair_chart(line_chart, use_container_width=True)

        st.dataframe(df_pm[['Employee','Bench_Status','True_Utilization']], height=300)

        # AI Recommendations
        st.subheader("AI Recommendations 🤖")
        recs = ai_recommendations(df_pm, proj_df, role='Project Manager')
        for i, rec in enumerate(recs,1):
            st.markdown(f"**{i}.** {rec}")

# ---------- HR Head Pages ----------
elif page=="HR Head":
    df = calculate_utilization(st.session_state['activity'])
    proj_df = st.session_state['projects']
    df_skills = st.session_state['skills']

    # --- Dashboard & Analytics ---
    st.subheader("Dashboard & Analytics")
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

        # Dept vs Average Utilization
        dept_util = df.groupby('Dept')['True_Utilization'].mean().reset_index()
        chart2 = alt.Chart(dept_util).mark_bar().encode(
            x='Dept',
            y='True_Utilization',
            color='Dept'
        )
        st.altair_chart(chart2, use_container_width=True)

        # Line chart for trends (dept avg)
        line_chart = alt.Chart(dept_util.reset_index()).mark_line(point=True).encode(
            x='index',
            y='True_Utilization',
            color='Dept',
            tooltip=['Dept','True_Utilization']
        )
        st.altair_chart(line_chart, use_container_width=True)

        st.dataframe(df[['Employee','Dept','Bench_Status','True_Utilization']], height=300)

    # --- Skill Recommendations ---
    st.subheader("Skill Recommendations 🎯")
    if df.empty or df_skills.empty:
        st.info("Upload both Employee Activity and Skills file first")
    else:
        df_rec = skill_recommendations(df, df_skills, top_n=2)
        st.dataframe(df_rec[['Employee','Skills','Recommended_Skills','Bench_Status']], height=400)

    # --- Project Assignment ---
    st.subheader("Project Assignment 🚀")
    if df.empty or proj_df.empty:
        st.info("Upload Employee Activity and Project Assignment file first")
    else:
        assignments = []
        for _, emp in df.iterrows():
            emp_skills = set(str(emp.get('Skills','')).split(","))
            for _, proj in proj_df.iterrows():
                proj_skills = set(str(proj.get('Required_Skills','')).split(","))
                # Assign complementary skills only
                matched_skills = emp_skills & proj_skills
                if matched_skills:
                    assignments.append({
                        'Employee': emp.get('Employee',''),
                        'Project': proj.get('Project_Name',''),
                        'Skill_Match': ", ".join(matched_skills)
                    })
        st.dataframe(pd.DataFrame(assignments), height=400)

    # --- AI Recommendations ---
    st.subheader("AI Recommendations 🤖")
    recs = ai_recommendations(df, proj_df, role='HR Head')
    for i, rec in enumerate(recs,1):
        st.markdown(f"**{i}.** {rec}")




