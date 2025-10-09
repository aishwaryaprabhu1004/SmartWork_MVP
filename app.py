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

def ai_recommendations(activity_df, project_df, role="HR Head"):
    recs = []
    if activity_df.empty or project_df.empty:
        return ["Upload Employee and Project data for recommendations."]
    
    df = calculate_utilization(activity_df.copy())
    
    if role=="HR Head":
        # Underutilized employees
        underutilized = df[df['True_Utilization'] < 50]
        for i, emp in underutilized.head(3).iterrows():
            impact = round((50-emp['True_Utilization'])*2,2)
            recs.append(f"Employee {emp['Employee']} is underutilized. Reassigning could improve utilization by ~{impact}%.")

        # Project skill gaps
        for _, proj in project_df.iterrows():
            required_skills = set(str(proj.get('Required_Skills','')).split(","))
            available_skills = set(",".join(df['Skills'].dropna()).split(","))
            missing = required_skills - available_skills
            if missing:
                recs.append(f"Project {proj['Project_Name']} lacks employees with {', '.join(missing)}. Upskilling could improve project coverage by {len(missing)*10}%.")

        # Bench cost optimization
        if 'Cost' in df.columns:
            bench_emps = df[df['True_Utilization']<20]
            total_saving = bench_emps['Cost'].sum() * 0.1
            recs.append(f"Reducing bench time could save ~${total_saving:.2f} and improve overall efficiency by 10%.")

    elif role=="Project Manager":
        for _, emp in df.iterrows():
            if emp['True_Utilization'] < 50:
                impact = round((50-emp['True_Utilization'])*2,2)
                recs.append(f"Reportee {emp['Employee']} underutilized. Reassigning could improve utilization by ~{impact}%.")

    return recs[:5]

def recommend_skills(df_emp, df_skills, df_proj):
    if df_emp.empty or df_skills.empty or df_proj.empty:
        return pd.DataFrame()
    recommended = []
    for _, emp in df_emp.iterrows():
        emp_skills = set(str(emp.get('Skills','')).split(",")) if pd.notnull(emp.get('Skills')) else set()
        # Find projects assigned to employee
        assigned_projects = df_proj[df_proj['Assigned_Employee']==emp['Employee']]
        project_skills = set()
        for _, proj in assigned_projects.iterrows():
            proj_skills = set(str(proj.get('Required_Skills','')).split(","))
            project_skills.update(proj_skills)
        # Complementary skills: top 2 missing skills from project requirements
        missing_skills = list(project_skills - emp_skills)
        top_skills = missing_skills[:2] if missing_skills else []
        recommended.append(", ".join(top_skills))
    df_emp['Recommended_Skills'] = recommended
    return df_emp

# ---------------- Session State ----------------
for key in ['activity','skills','projects','reportees']:
    if key not in st.session_state: st.session_state[key] = pd.DataFrame()
if 'role' not in st.session_state: st.session_state['role'] = 'HR Head'
if 'feature' not in st.session_state: st.session_state['feature'] = 'Homepage'

# ---------------- Sidebar ----------------
st.sidebar.title("Navigation")
sidebar_selection = st.sidebar.radio(
    "",
    options=[
        "Homepage",
        "Upload Data",
        "Project Manager",
        "HR Head"
    ]
)

# Features based on role
if sidebar_selection=="Project Manager":
    st.session_state['role'] = "Project Manager"
    feature = st.sidebar.radio(
        "Select Feature",
        options=[
            "Dashboard & Analytics",
            "Reportees",
            "AI Recommendations"
        ]
    )
elif sidebar_selection=="HR Head":
    st.session_state['role'] = "HR Head"
    feature = st.sidebar.radio(
        "Select Feature",
        options=[
            "Dashboard & Analytics",
            "Skill Recommendations",
            "Project Assignment",
            "AI Recommendations"
        ]
    )
else:
    feature = sidebar_selection  # Homepage or Upload Data

st.session_state['feature'] = feature

# ---------------- Header ----------------
col1, col2 = st.columns([6,4])
with col1:
    st.image("logo.png", width=250)
    st.markdown("<h1>SmartWork.AI 💡</h1>", unsafe_allow_html=True)
with col2:
    st.markdown(f"**Role:** {st.session_state['role']}", unsafe_allow_html=True)

# ---------------- Pages ----------------

# ---------- Homepage ----------
if feature=="Homepage":
    st.markdown("### The AI-powered tool for CHROs")
    st.markdown("""
        SmartWork.AI helps HR heads and project managers monitor employee utilization, skills, and project assignments.
        Gain actionable insights and AI-based recommendations to optimize resources, reduce bench costs, and improve project delivery.
    """)

# ---------- Upload Data ----------
elif feature=="Upload Data":
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
    st.success("Files uploaded successfully!")

# ---------- Project Manager Pages ----------
elif st.session_state['role']=="Project Manager":
    df = st.session_state['activity']
    df_proj = st.session_state['projects']
    reportees_df = st.session_state['reportees']
    if df.empty or df_proj.empty or reportees_df.empty:
        st.info("Upload all relevant files first (Activity, Projects, Reportees).")
    else:
        df = df[df['Employee'].isin(reportees_df['Employee'])]
        if feature=="Dashboard & Analytics":
            st.subheader("Dashboard & Analytics")
            df = calculate_utilization(df)
            total_emp = len(df)
            bench_count = len(df[df['Bench_Status']=="On Bench"])
            part_util = len(df[df['Bench_Status']=="Partially Utilized"])
            full_util = len(df[df['Bench_Status']=="Fully Utilized"])
            k1,k2,k3,k4 = st.columns(4)
            k1.metric("Total Employees", total_emp)
            k2.metric("On Bench", bench_count)
            k3.metric("Partial Utilization", part_util)
            k4.metric("Full Utilization", full_util)

            line_chart = alt.Chart(df.reset_index()).mark_line(point=True).encode(
                x='index',
                y='True_Utilization',
                color='Employee',
                tooltip=['Employee','True_Utilization']
            )
            st.altair_chart(line_chart, use_container_width=True)
            st.dataframe(df[['Employee','Bench_Status','True_Utilization']], height=300)

        elif feature=="Reportees":
            st.subheader("Reportees Details")
            st.dataframe(df, height=400)

        elif feature=="AI Recommendations":
            st.subheader("AI Recommendations 🤖")
            recs = ai_recommendations(df, df_proj, role="Project Manager")
            for i, rec in enumerate(recs,1):
                st.markdown(f"**{i}.** {rec}")

# ---------- HR Head Pages ----------
elif st.session_state['role']=="HR Head":
    df = st.session_state['activity']
    df_proj = st.session_state['projects']
    df_skills = st.session_state['skills']
    if df.empty or df_proj.empty or df_skills.empty:
        st.info("Upload all relevant files first (Activity, Skills, Projects).")
    else:
        if feature=="Dashboard & Analytics":
            st.subheader("Dashboard & Analytics")
            df = calculate_utilization(df)
            dept_util = df.groupby('Dept')['True_Utilization'].mean().reset_index()
            chart1 = alt.Chart(dept_util).mark_bar().encode(
                x='Dept',
                y='True_Utilization',
                color='Dept'
            )
            st.altair_chart(chart1, use_container_width=True)
            st.dataframe(dept_util, height=300)

        elif feature=="Skill Recommendations":
            st.subheader("Skill Recommendations")
            df_rec = recommend_skills(df.copy(), df_skills, df_proj)
            st.dataframe(df_rec[['Employee','Skills','Recommended_Skills','Bench_Status']], height=400)

        elif feature=="Project Assignment":
            st.subheader("Project Assignment")
            assignments = []
            for _, emp in df.iterrows():
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

        elif feature=="AI Recommendations":
            st.subheader("AI Recommendations 🤖")
            recs = ai_recommendations(df, df_proj, role="HR Head")
            for i, rec in enumerate(recs,1):
                st.markdown(f"**{i}.** {rec}")

