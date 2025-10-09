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

    # Underutilized employees
    underutilized = df[df['True_Utilization'] < 50]
    for i, emp in underutilized.head(3).iterrows():
        impact = np.random.randint(5,15)  # example % improvement
        recs.append(f"Employee {emp['Employee']} is underutilized. Reassigning to high-priority projects could increase utilization by ~{impact}%.")

    # Project skill gaps
    for _, proj in project_df.iterrows():
        required_skills = set(str(proj.get('Required_Skills','')).split(","))
        available_skills = set(",".join(df['Skills'].dropna()).split(","))
        missing = required_skills - available_skills
        if missing:
            recs.append(f"Project {proj['Project_Name']} lacks employees with {', '.join(missing)}. Upskilling or reallocating could improve project delivery by ~10%.")

    # Bench cost optimization
    if 'Cost' in df.columns:
        bench_emps = df[df['True_Utilization']<20]
        total_saving = bench_emps['Cost'].sum() * 0.1
        recs.append(f"Reducing bench time could save approximately ${total_saving:.2f}, increasing overall productivity by ~8%.")

    return recs[:5]

def get_top_skills(employee_skills, team_skills, top_n=2):
    """Select top complementary skills not already in team."""
    all_skills = set(skill for skills in team_skills for skill in skills.split(","))
    emp_skills = set(str(employee_skills).split(","))
    possible_skills = all_skills - emp_skills
    return ", ".join(list(possible_skills)[:top_n]) if possible_skills else "None"

# ---------------- Session State ----------------
if 'activity' not in st.session_state: st.session_state['activity'] = pd.DataFrame()
if 'skills' not in st.session_state: st.session_state['skills'] = pd.DataFrame()
if 'projects' not in st.session_state: st.session_state['projects'] = pd.DataFrame()
if 'reportees' not in st.session_state: st.session_state['reportees'] = pd.DataFrame()
if 'selected_pm' not in st.session_state: st.session_state['selected_pm'] = None

# ---------------- Sidebar ----------------
st.sidebar.markdown("## Navigation")
page = st.sidebar.selectbox(
    "",
    options=[
        "🏠 Homepage",
        "📤 Upload Data",
        "Project Manager",
        "HR Head"
    ]
)

# Indent role-specific functionalities
if page == "Project Manager":
    sub_page = st.sidebar.selectbox("Project Manager Options", ["Dashboard & Analytics","Reportees Performance","AI Recommendations"])
elif page == "HR Head":
    sub_page = st.sidebar.selectbox("HR Head Options", ["Dashboard & Analytics","Skill Recommendations","Project Assignment","AI Recommendations"])
else:
    sub_page = None

# ---------------- Homepage ----------------
if page=="🏠 Homepage":
    st.image("logo.png", width=300)
    st.markdown("<h1 style='text-align:left'>SmartWork.AI 💡</h1>", unsafe_allow_html=True)
    st.markdown("### The AI-powered tool for CHROs", unsafe_allow_html=True)
    st.markdown("""
        SmartWork.AI helps HR Heads and Project Managers monitor employee utilization, skills, and project assignments.
        Gain actionable insights and AI-based recommendations to optimize resources, reduce bench costs, and improve project delivery.
    """, unsafe_allow_html=True)

# ---------------- Upload Data ----------------
elif page=="📤 Upload Data":
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

# ---------------- Project Manager Pages ----------------
elif page=="Project Manager":
    df_emp = st.session_state['activity']
    proj_df = st.session_state['projects']
    reportees_df = st.session_state['reportees']

    if reportees_df.empty:
        st.warning("Upload Reportees data to view project manager info.")
    else:
        pm_list = reportees_df['Project_Manager'].unique().tolist()
        selected_pm = st.selectbox("Select Project Manager", pm_list, index=0)
        st.session_state['selected_pm'] = selected_pm
        pm_reportees = reportees_df[reportees_df['Project_Manager']==selected_pm]['Employee'].tolist()
        df_emp = df_emp[df_emp['Employee'].isin(pm_reportees)]
        proj_df = proj_df[proj_df['Project_Manager']==selected_pm]

    if sub_page=="Dashboard & Analytics":
        st.subheader(f"{selected_pm}'s Dashboard & Analytics")
        if df_emp.empty:
            st.info("No data for this project manager yet.")
        else:
            df_emp = calculate_utilization(df_emp)
            total_emp = len(df_emp)
            bench_count = len(df_emp[df_emp['Bench_Status']=="On Bench"])
            part_util = len(df_emp[df_emp['Bench_Status']=="Partially Utilized"])
            full_util = len(df_emp[df_emp['Bench_Status']=="Fully Utilized"])
            c1,c2,c3,c4 = st.columns(4)
            c1.metric("Total Employees", total_emp)
            c2.metric("On Bench", bench_count)
            c3.metric("Partial Utilization", part_util)
            c4.metric("Full Utilization", full_util)

            # Employee utilization line chart
            line_chart = alt.Chart(df_emp.reset_index()).mark_line(point=True).encode(
                x='index',
                y='True_Utilization',
                color='Employee',
                tooltip=['Employee','True_Utilization']
            )
            st.altair_chart(line_chart, use_container_width=True)
            st.dataframe(df_emp[['Employee','Bench_Status','True_Utilization']], height=300)

    elif sub_page=="Reportees Performance":
        st.subheader(f"{selected_pm}'s Reportees Performance")
        if df_emp.empty:
            st.info("No reportees data available.")
        else:
            selected_emp = st.selectbox("Select Employee", df_emp['Employee'].tolist())
            emp_df = df_emp[df_emp['Employee']==selected_emp]
            st.dataframe(emp_df[['Employee','Dept','Tasks_Completed','Meetings_Duration','Decisions_Made','Docs_Updated','True_Utilization','Bench_Status']])

    elif sub_page=="AI Recommendations":
        st.subheader(f"{selected_pm}'s AI Recommendations")
        recs = ai_recommendations(df_emp, proj_df, role="Project Manager")
        for i, rec in enumerate(recs,1):
            st.markdown(f"**{i}.** {rec}")

# ---------------- HR Head Pages ----------------
elif page=="HR Head":
    df_emp = st.session_state['activity']
    df_skills = st.session_state['skills']
    proj_df = st.session_state['projects']

    if sub_page=="Dashboard & Analytics":
        st.subheader("HR Head Dashboard & Analytics")
        if df_emp.empty:
            st.info("Upload Employee Activity data first.")
        else:
            df_emp = calculate_utilization(df_emp)
            # Bench chart
            bench_chart = df_emp['Bench_Status'].value_counts().reset_index()
            bench_chart.columns = ['Bench_Status','Count']
            st.altair_chart(alt.Chart(bench_chart).mark_bar().encode(
                x='Bench_Status', y='Count', color='Bench_Status'
            ), use_container_width=True)
            # Dept-wise avg utilization
            dept_util = df_emp.groupby('Dept')['True_Utilization'].mean().reset_index()
            st.altair_chart(alt.Chart(dept_util).mark_bar().encode(
                x='Dept', y='True_Utilization', color='Dept'
            ), use_container_width=True)

            # Utilization line per dept
            st.altair_chart(alt.Chart(df_emp.reset_index()).mark_line(point=True).encode(
                x='index',
                y='True_Utilization',
                color='Dept',
                tooltip=['Employee','Dept','True_Utilization']
            ), use_container_width=True)
            st.dataframe(df_emp[['Employee','Dept','Bench_Status','True_Utilization']], height=300)

    elif sub_page=="Skill Recommendations":
        st.subheader("Skill Recommendations")
        if df_emp.empty or df_skills.empty:
            st.info("Upload Employee Activity and Skills data first.")
        else:
            team_skills = df_emp['Skills'].dropna().tolist()
            df_emp['Recommended_Skills'] = df_emp['Skills'].apply(lambda s: get_top_skills(s, team_skills, top_n=2))
            st.dataframe(df_emp[['Employee','Skills','Recommended_Skills']], height=400)

    elif sub_page=="Project Assignment":
        st.subheader("Project Assignment")
        if df_emp.empty or proj_df.empty:
            st.info("Upload Employee Activity and Project Assignment data first.")
        else:
            assignments = []
            team_skills = df_emp['Skills'].dropna().tolist()
            for _, emp in df_emp.iterrows():
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

    elif sub_page=="AI Recommendations":
        st.subheader("AI Recommendations 🤖")
        recs = ai_recommendations(df_emp, proj_df, role="HR Head")
        for i, rec in enumerate(recs,1):
            st.markdown(f"**{i}.** {rec}")





