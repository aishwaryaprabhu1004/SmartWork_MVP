import streamlit as st
import pandas as pd
import altair as alt
from itertools import cycle

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

def assign_complementary_skills(df_emp, df_proj):
    """
    Assign complementary skills to employees based on project requirements.
    Each employee gets up to 2 skills; skills are unique per project team.
    """
    assigned_skills = {}
    for _, proj in df_proj.iterrows():
        proj_name = proj['Project_Name']
        req_skills = list(filter(None, map(str.strip, str(proj.get('Required_Skills','')).split(","))))
        employees = df_emp[df_emp['Project']==proj_name]['Employee'].tolist()
        skill_cycle = cycle(req_skills)
        for emp in employees:
            assigned = []
            while len(assigned) < 2 and req_skills:
                skill = next(skill_cycle)
                if skill not in assigned:
                    assigned.append(skill)
            assigned_skills[emp] = ", ".join(assigned)
    return assigned_skills

def ai_recommendations(activity_df, project_df, reportees_df=None, role="HR Head"):
    recs = []
    if activity_df.empty or project_df.empty:
        return ["Upload Employee and Project data for recommendations."]
    
    df = calculate_utilization(activity_df.copy())
    if reportees_df is not None:
        df = df[df['Employee'].isin(reportees_df['Employee'])]
    
    # Underutilized employees
    underutilized = df[df['True_Utilization'] < 50]
    for i, emp in enumerate(underutilized.head(3).itertuples(), 1):
        recs.append(f"{i}. Employee {emp.Employee} is underutilized. Reassigning to high-priority projects could improve utilization by ~{50 - emp.True_Utilization:.1f}%.")

    # Project skill gaps
    for _, proj in project_df.iterrows():
        required_skills = set(filter(None, map(str.strip, str(proj.get('Required_Skills','')).split(","))))
        available_skills = set(",".join(df['Skills'].dropna()).split(","))
        missing = required_skills - available_skills
        if missing:
            recs.append(f"Project {proj['Project_Name']} lacks employees with {', '.join(missing)} skills. Upskilling or reallocating employees could improve project delivery success by ~10-15%.")

    # Bench cost optimization
    if 'Cost' in df.columns:
        bench_emps = df[df['True_Utilization']<20]
        total_saving = bench_emps['Cost'].sum() * 0.1
        recs.append(f"Reducing bench time for underutilized employees can save approximately ${total_saving:.2f} (10% of current bench costs).")
    
    return recs[:5]

# ---------------- Session State ----------------
if 'activity' not in st.session_state: st.session_state['activity'] = pd.DataFrame()
if 'skills' not in st.session_state: st.session_state['skills'] = pd.DataFrame()
if 'projects' not in st.session_state: st.session_state['projects'] = pd.DataFrame()
if 'reportees' not in st.session_state: st.session_state['reportees'] = pd.DataFrame()

# ---------------- Sidebar ----------------
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["🏠 Homepage","📤 Upload Data","Project Manager","HR Head"])

# Features under each role (indented)
if page == "Project Manager":
    st.sidebar.markdown("    Dashboard & Analytics")
    st.sidebar.markdown("    Reportees")
    st.sidebar.markdown("    AI Recommendations")
elif page == "HR Head":
    st.sidebar.markdown("    Dashboard & Analytics")
    st.sidebar.markdown("    Skill Recommendations")
    st.sidebar.markdown("    Project Assignment")
    st.sidebar.markdown("    AI Recommendations")
    st.sidebar.markdown("    Select Project Manager")

# ---------------- Pages ----------------

# ---------- Homepage ----------
if page=="🏠 Homepage":
    st.markdown("<h1 style='text-align:left'>SmartWork.AI 💡</h1>", unsafe_allow_html=True)
    st.image("logo.png", width=300)
    st.markdown("### The AI-powered tool for CHROs", unsafe_allow_html=True)
    st.markdown("""
        SmartWork.AI helps HR heads and project managers monitor employee utilization, skills, and project assignments.
        Gain actionable insights and AI-based recommendations to optimize resources, reduce bench costs, and improve project delivery.
    """, unsafe_allow_html=True)

# ---------- Upload Data ----------
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

# ---------- Project Manager ----------
if page=="Project Manager":
    st.subheader("Project Manager Dashboard")
    reportees_df = st.session_state['reportees']
    activity_df = st.session_state['activity']
    proj_df = st.session_state['projects']

    if reportees_df.empty or activity_df.empty:
        st.info("Upload Project Manager Reportees and Employee Activity first")
    else:
        df = activity_df[activity_df['Employee'].isin(reportees_df['Employee'])]
        df = calculate_utilization(df)
        st.dataframe(df[['Employee','Bench_Status','True_Utilization']], height=300)

        st.subheader("AI Recommendations 🤖")
        recs = ai_recommendations(df, proj_df, reportees_df, role="Project Manager")
        for rec in recs:
            st.markdown(f"- {rec}")

# ---------- HR Head ----------
if page=="HR Head":
    st.subheader("HR Head Dashboard")
    df = calculate_utilization(st.session_state['activity'])
    proj_df = st.session_state['projects']
    reportees_df = st.session_state['reportees']
    skills_df = st.session_state['skills']

    if df.empty or proj_df.empty:
        st.info("Upload Employee and Project data first")
    else:
        # Department average utilization
        dept_util = df.groupby('Dept')['True_Utilization'].mean().reset_index()
        bar_chart = alt.Chart(dept_util).mark_bar().encode(
            x='Dept',
            y='True_Utilization',
            color='Dept'
        )
        st.altair_chart(bar_chart, use_container_width=True)

        # Line chart for utilization trend
        line_chart = alt.Chart(df.reset_index()).mark_line(point=True).encode(
            x='index',
            y='True_Utilization',
            color='Dept',
            tooltip=['Employee','Dept','True_Utilization']
        )
        st.altair_chart(line_chart, use_container_width=True)

        # Select Project Manager dropdown
        pm_list = reportees_df['Manager'].unique().tolist() if not reportees_df.empty else []
        selected_pm = None
        if pm_list:
            selected_pm = st.selectbox("Select Project Manager to view team", pm_list)
            df_pm_team = df[df['Employee'].isin(reportees_df[reportees_df['Manager']==selected_pm]['Employee'])]
            st.subheader(f"{selected_pm}'s Team Dashboard")
            st.dataframe(df_pm_team[['Employee','Dept','Bench_Status','True_Utilization']], height=300)

        # Skill Recommendations (Top 2 relevant skills)
        if not skills_df.empty:
            required_skills = skills_df['Skill'].value_counts().head(2).index.tolist()
            def rec(skills_str):
                emp_skills = str(skills_str).split(",") if pd.notnull(skills_str) else []
                missing = list(set(required_skills) - set(emp_skills))
                return ", ".join(missing) if missing else "None"
            df['Recommended_Skills'] = df['Skills'].apply(rec)
            st.subheader("Top Skill Recommendations")
            st.dataframe(df[['Employee','Skills','Recommended_Skills','Bench_Status']], height=400)

        # AI Recommendations
        st.subheader("AI Recommendations 🤖")
        recs = ai_recommendations(df, proj_df)
        for rec in recs:
            st.markdown(f"- {rec}")



