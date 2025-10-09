import streamlit as st
import pandas as pd
import altair as alt

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
    
    # Underutilized employees
    underutilized = df[df['True_Utilization'] < 50]
    for i, emp in underutilized.head(3).iterrows():
        recs.append(f"Employee {emp['Employee']} is underutilized. Reassigning could improve utilization by ~{50 - emp['True_Utilization']:.1f}%")
    
    # Project skill gaps
    for _, proj in project_df.iterrows():
        required_skills = set(str(proj.get('Required_Skills','')).split(","))
        available_skills = set(",".join(df['Skills'].dropna()).split(","))
        missing = required_skills - available_skills
        if missing:
            recs.append(f"Project {proj['Project_Name']} lacks {', '.join(missing)}. Upskilling could improve project delivery efficiency by ~10%")
    
    # Bench cost optimization
    if 'Cost' in df.columns:
        bench_emps = df[df['True_Utilization']<20]
        total_saving = bench_emps['Cost'].sum() * 0.1
        recs.append(f"Reducing bench time can save approximately ${total_saving:.2f} for the company.")
    
    return recs[:5]

# ---------------- Session State ----------------
if 'activity' not in st.session_state: st.session_state['activity'] = pd.DataFrame()
if 'skills' not in st.session_state: st.session_state['skills'] = pd.DataFrame()
if 'projects' not in st.session_state: st.session_state['projects'] = pd.DataFrame()
if 'reportees' not in st.session_state: st.session_state['reportees'] = pd.DataFrame()
if 'role' not in st.session_state: st.session_state['role'] = 'HR Head'

# ---------------- Sidebar ----------------
st.sidebar.markdown("# SmartWork.AI 💡")
sidebar_pages = ["🏠 Homepage","📤 Upload Data","Role-Based Pages"]
page = st.sidebar.radio("Navigation", sidebar_pages)

# Role selection for Role-Based Pages
if page=="Role-Based Pages":
    role = st.sidebar.selectbox("Select Role", ["HR Head","Project Manager"], index=["HR Head","Project Manager"].index(st.session_state['role']))
    st.session_state['role'] = role
    st.sidebar.markdown("### Options")
    if role=="Project Manager":
        role_option = st.sidebar.radio("", ["Dashboard & Analytics","Reportees Dashboard","AI Recommendations"], index=0)
    elif role=="HR Head":
        role_option = st.sidebar.radio("", ["Dashboard & Analytics","Skill Recommendations","Project Assignment","AI Recommendations"], index=0)

# ---------------- Homepage ----------------
if page=="🏠 Homepage":
    st.image("logo.png", width=250)
    st.markdown("<h1 style='text-align:left'>SmartWork.AI</h1>", unsafe_allow_html=True)
    st.markdown("### The AI-powered tool for CHROs", unsafe_allow_html=True)
    st.markdown("""
        SmartWork.AI helps HR heads and project managers monitor employee utilization, skills, project assignments, 
        and generate AI-driven recommendations to optimize resources, reduce bench costs, and improve project delivery.
    """, unsafe_allow_html=True)

# ---------------- Upload Data ----------------
elif page=="📤 Upload Data":
    st.subheader("Upload Data 📤")
    col1, col2, col3, col4 = st.columns([1,1,1,1])
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

# ---------------- Role-Based Pages ----------------
if page=="Role-Based Pages":
    df = calculate_utilization(st.session_state['activity'])
    proj_df = st.session_state['projects']
    reportees_df = st.session_state['reportees']
    df_skills = st.session_state['skills']

    # ---------- Project Manager ----------
    if st.session_state['role']=="Project Manager":
        if role_option=="Dashboard & Analytics":
            st.subheader("Project Manager Dashboard & Analytics")
            if df.empty:
                st.info("Upload Employee Activity first")
            else:
                if not reportees_df.empty:
                    df_pm = df[df['Employee'].isin(reportees_df['Employee'])]
                else:
                    df_pm = df.copy()
                dept_util = df_pm.groupby('Dept')['True_Utilization'].mean().reset_index()
                chart1 = alt.Chart(dept_util).mark_bar().encode(
                    x='Dept', y='True_Utilization', color='Dept'
                )
                st.altair_chart(chart1, use_container_width=True)

        elif role_option=="Reportees Dashboard":
            st.subheader("Reportees Dashboard & Analytics")
            if reportees_df.empty or df.empty:
                st.info("Upload reportees file and Employee Activity first")
            else:
                df_rep = df[df['Employee'].isin(reportees_df['Employee'])]
                st.dataframe(df_rep[['Employee','Dept','Bench_Status','True_Utilization']], height=300)

        elif role_option=="AI Recommendations":
            st.subheader("AI Recommendations for Project Manager")
            recs = ai_recommendations(df, proj_df, role="Project Manager")
            for i, rec in enumerate(recs,1):
                st.markdown(f"**{i}.** {rec}")

    # ---------- HR Head ----------
    if st.session_state['role']=="HR Head":
        if role_option=="Dashboard & Analytics":
            st.subheader("HR Head Dashboard & Analytics")
            if df.empty:
                st.info("Upload Employee Activity first")
            else:
                dept_util = df.groupby('Dept')['True_Utilization'].mean().reset_index()
                chart1 = alt.Chart(dept_util).mark_bar().encode(
                    x='Dept', y='True_Utilization', color='Dept'
                )
                st.altair_chart(chart1, use_container_width=True)

        elif role_option=="Skill Recommendations":
            st.subheader("Skill Recommendations 🎯")
            if df.empty or df_skills.empty:
                st.info("Upload both Employee Activity and Skills file first")
            else:
                def top_skills(emp_skills):
                    emp_skills_set = set(str(emp_skills).split(",") if pd.notnull(emp_skills) else [])
                    skill_priority_ordered = df_skills.sort_values("Priority")['Skill'].tolist()
                    missing_skills = [s for s in skill_priority_ordered if s not in emp_skills_set]
                    return ", ".join(missing_skills[:2]) if missing_skills else "None"
                df['Recommended_Skills'] = df['Skills'].apply(top_skills)
                st.dataframe(df[['Employee','Skills','Recommended_Skills','Bench_Status']], height=400)

        elif role_option=="Project Assignment":
            st.subheader("Project Assignment 🚀")
            if df.empty or proj_df.empty:
                st.info("Upload Employee Activity and Project Assignment file first")
            else:
                assignments = []
                for _, emp in df.iterrows():
                    emp_skills = set(str(emp.get('Skills','')).split(","))
                    for _, proj in proj_df.iterrows():
                        proj_skills = set(str(proj.get('Required_Skills','')).split(","))
                        if emp_skills & proj_skills:
                            assignments.append({
                                'Employee': emp.get('Employee',''),
                                'Project': proj.get('Project_Name',''),
                                'Skill_Match': ", ".join(emp_skills & proj_skills)
                            })
                st.dataframe(pd.DataFrame(assignments), height=400)

        elif role_option=="AI Recommendations":
            st.subheader("AI Recommendations for HR Head")
            recs = ai_recommendations(df, proj_df, role="HR Head")
            for i, rec in enumerate(recs,1):
                st.markdown(f"**{i}.** {rec}")


