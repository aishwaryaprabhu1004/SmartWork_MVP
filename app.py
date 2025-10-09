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

def ai_recommendations(activity_df, project_df):
    recs = []
    if activity_df.empty or project_df.empty:
        return ["Upload Employee and Project data for recommendations."]
    
    df = calculate_utilization(activity_df.copy())
    
    # Underutilized employees
    underutilized = df[df['True_Utilization'] < 50]
    for i, emp in underutilized.head(3).iterrows():
        recs.append(f"Employee {emp['Employee']} is underutilized. Assign to high-priority projects to increase utilization by ~{50 - emp['True_Utilization']:.1f}%.")

    # Project skill gaps
    for _, proj in project_df.iterrows():
        required_skills = set(str(proj.get('Required_Skills','')).split(","))
        available_skills = set(",".join(df['Skills'].dropna()).split(","))
        missing = required_skills - available_skills
        if missing:
            recs.append(f"Project {proj['Project_Name']} lacks employees with {', '.join(missing)}. Upskill or reallocate to improve project coverage by ~{len(missing)/len(required_skills)*100:.1f}%.")

    # Bench cost optimization
    if 'Cost' in df.columns:
        bench_emps = df[df['True_Utilization']<20]
        total_saving = bench_emps['Cost'].sum() * 0.1
        recs.append(f"Reassign underutilized employees to reduce bench costs; potential savings: ${total_saving:.2f} (~10% of bench cost).")
    
    return recs[:5]

# ---------------- Sidebar ----------------
page = st.sidebar.selectbox(
    "Navigation",
    options=[
        "🏠 Homepage",
        "📤 Upload Data",
        "Project Manager → Dashboard & Analytics",
        "Project Manager → Reportees Performance",
        "Project Manager → AI Recommendations",
        "HR Head → Dashboard & Analytics",
        "HR Head → Skill Recommendations",
        "HR Head → Project Assignment",
        "HR Head → AI Recommendations"
    ]
)

# ---------------- Session State ----------------
if 'activity' not in st.session_state: st.session_state['activity'] = pd.DataFrame()
if 'skills' not in st.session_state: st.session_state['skills'] = pd.DataFrame()
if 'projects' not in st.session_state: st.session_state['projects'] = pd.DataFrame()
if 'reportees' not in st.session_state: st.session_state['reportees'] = pd.DataFrame()

# ---------------- Top Logo ----------------
st.image("logo.png", width=250)

# ---------------- Upload Data ----------------
if page == "📤 Upload Data":
    st.header("Upload Data 📤")
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

# ---------- Homepage ----------
elif page == "🏠 Homepage":
    st.markdown("<h1 style='text-align:left'>SmartWork.AI 💡</h1>", unsafe_allow_html=True)
    st.markdown("### The AI-powered tool for CHROs", unsafe_allow_html=True)
    st.markdown("""
        SmartWork.AI helps HR heads and project managers monitor employee utilization, skills, and project assignments.
        Gain actionable insights and AI-based recommendations to optimize resources, reduce bench costs, and improve project delivery.
    """, unsafe_allow_html=True)

# ---------------- Helper: Get Project Manager Selection ----------------
def select_pm(reportees_df):
    if reportees_df.empty:
        st.info("Upload Project Manager reportees file first.")
        return None
    pm_list = reportees_df['Project_Manager'].unique().tolist()
    selected_pm = st.selectbox("Select Project Manager", options=pm_list)
    return selected_pm

# ---------------- Project Manager Pages ----------------
df = st.session_state['activity']
proj_df = st.session_state['projects']
reportees_df = st.session_state['reportees']

if "Project Manager →" in page:
    selected_pm = select_pm(reportees_df)
    if selected_pm:
        pm_reportees = reportees_df[reportees_df['Project_Manager']==selected_pm]['Employee'].tolist()
        df_pm = df[df['Employee'].isin(pm_reportees)]
        proj_pm = proj_df.copy()  # PM sees all projects if needed
    else:
        df_pm = pd.DataFrame()
        proj_pm = pd.DataFrame()

    # ---------- PM Dashboard & Analytics ----------
    if page == "Project Manager → Dashboard & Analytics":
        st.subheader(f"{selected_pm} - Dashboard & Analytics")
        if df_pm.empty:
            st.info("No reportees data available.")
        else:
            total_emp = len(df_pm)
            bench_count = len(df_pm[df_pm['Bench_Status']=="On Bench"])
            part_util = len(df_pm[df_pm['Bench_Status']=="Partially Utilized"])
            full_util = len(df_pm[df_pm['Bench_Status']=="Fully Utilized"])

            k1,k2,k3,k4 = st.columns(4)
            k1.metric("Total Employees", total_emp)
            k2.metric("On Bench", bench_count)
            k3.metric("Partial Utilization", part_util)
            k4.metric("Full Utilization", full_util)

            # Line chart: Employee Utilization
            line_chart = alt.Chart(df_pm.reset_index()).mark_line(point=True).encode(
                x='index',
                y='True_Utilization',
                color='Employee',
                tooltip=['Employee','Dept','True_Utilization']
            )
            st.altair_chart(line_chart, use_container_width=True)

    # ---------- PM Reportees Performance ----------
    elif page == "Project Manager → Reportees Performance":
        st.subheader(f"{selected_pm} - Reportees Performance")
        if df_pm.empty:
            st.info("No reportees data available.")
        else:
            st.dataframe(df_pm[['Employee','Dept','Bench_Status','True_Utilization']], height=400)

    # ---------- PM AI Recommendations ----------
    elif page == "Project Manager → AI Recommendations":
        st.subheader(f"{selected_pm} - AI Recommendations")
        if df_pm.empty or proj_pm.empty:
            st.info("Upload data first")
        else:
            recs = ai_recommendations(df_pm, proj_pm)
            for i, rec in enumerate(recs,1):
                st.markdown(f"**{i}.** {rec}")

# ---------------- HR Head Pages ----------------
if "HR Head →" in page:
    # ---------- HR Dashboard & Analytics ----------
    if page == "HR Head → Dashboard & Analytics":
        st.subheader("HR Head - Dashboard & Analytics")
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

            # Bench Status Chart
            bench_chart = df['Bench_Status'].value_counts().reset_index()
            bench_chart.columns = ['Bench_Status','Count']
            chart1 = alt.Chart(bench_chart).mark_bar().encode(
                x='Bench_Status',
                y='Count',
                color='Bench_Status'
            )
            st.altair_chart(chart1, use_container_width=True)

            # Department Utilization Chart (Dept Avg)
            dept_util = df.groupby('Dept')['True_Utilization'].mean().reset_index()
            chart2 = alt.Chart(dept_util).mark_bar().encode(
                x='Dept',
                y='True_Utilization',
                color='Dept'
            )
            st.altair_chart(chart2, use_container_width=True)

            # Line chart: Employee Utilization
            line_chart = alt.Chart(df.reset_index()).mark_line(point=True).encode(
                x='index',
                y='True_Utilization',
                color='Employee',
                tooltip=['Employee','Dept','True_Utilization']
            )
            st.altair_chart(line_chart, use_container_width=True)

    # ---------- HR Skill Recommendations ----------
    elif page == "HR Head → Skill Recommendations":
        st.subheader("HR Head - Skill Recommendations")
        df_emp = df
        df_skills = st.session_state['skills']
        if df_emp.empty or df_skills.empty:
            st.info("Upload Employee Activity and Skills file first")
        else:
            required_skills = df_skills['Skill'].unique().tolist()
            def rec(skills_str):
                emp_skills = str(skills_str).split(",") if pd.notnull(skills_str) else []
                missing = list(set(required_skills) - set(emp_skills))
                return ", ".join(missing[:2]) if missing else "None"  # top 2 only
            df_emp['Recommended_Skills'] = df_emp['Skills'].apply(rec)
            st.dataframe(df_emp[['Employee','Skills','Recommended_Skills','Bench_Status']], height=400)

    # ---------- HR Project Assignment ----------
    elif page == "HR Head → Project Assignment":
        st.subheader("HR Head - Project Assignment")
        df_emp = df
        df_proj = proj_df
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

    # ---------- HR AI Recommendations ----------
    elif page == "HR Head → AI Recommendations":
        st.subheader("HR Head - AI Recommendations")
        recs = ai_recommendations(df, proj_df)
        for i, rec in enumerate(recs,1):
            st.markdown(f"**{i}.** {rec}")






