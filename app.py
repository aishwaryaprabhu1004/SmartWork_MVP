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
        recs.append(f"Employee {emp['Employee']} is underutilized. Consider reassigning to high-priority projects.")
    
    # Project skill gaps
    for _, proj in project_df.iterrows():
        required_skills = set(str(proj.get('Required_Skills','')).split(","))
        available_skills = set(",".join(df['Skills'].dropna()).split(","))
        missing = required_skills - available_skills
        if missing:
            recs.append(f"Project {proj['Project_Name']} lacks employees with {', '.join(missing)}. Upskill or reallocate employees.")
    
    # Bench cost optimization
    if 'Cost' in df.columns:
        bench_emps = df[df['True_Utilization']<20]
        total_saving = bench_emps['Cost'].sum() * 0.1
        recs.append(f"Reduce bench time by reassigning underutilized employees; potential savings: ${total_saving:.2f}.")
    
    return recs[:5]

# ---------------- Sidebar ----------------
page = st.sidebar.radio(
    "Navigation",
    options=[
        "🏠 Homepage",
        "📤 Upload Data",
        "🏠📈 Dashboard & Analytics",
        "🎯 Skill Recommendations",
        "🚀 Project Assignment"
    ]
)

# ---------------- Session State ----------------
if 'activity' not in st.session_state: st.session_state['activity'] = pd.DataFrame()
if 'skills' not in st.session_state: st.session_state['skills'] = pd.DataFrame()
if 'projects' not in st.session_state: st.session_state['projects'] = pd.DataFrame()
if 'reportees' not in st.session_state: st.session_state['reportees'] = pd.DataFrame()
if 'role' not in st.session_state: st.session_state['role'] = 'HR Head'

# ---------------- Top Right Role Selector ----------------
with st.container():
    col1, col2 = st.columns([9,1])
    with col1:
        pass  # placeholder for logo or spacing
    with col2:
        selected_role = st.selectbox("Role", options=["HR Head","Project Manager"], index=["HR Head","Project Manager"].index(st.session_state['role']))
        st.session_state['role'] = selected_role

# ---------------- Pages ----------------

# ---------- Homepage ----------
if page=="🏠 Homepage":
    st.markdown("<h1 style='text-align:left'>SmartWork.AI 💡</h1>", unsafe_allow_html=True)
    st.image("logo.png", width=250)
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

# ---------- Dashboard & Analytics ----------
elif page=="🏠📈 Dashboard & Analytics":
    st.subheader("Dashboard & Analytics 🏠📈")
    df = calculate_utilization(st.session_state['activity'])
    proj_df = st.session_state['projects']
    reportees_df = st.session_state['reportees']

    if df.empty:
        st.info("Upload Employee Activity first")
    else:
        if st.session_state['role']=="Project Manager" and not reportees_df.empty:
            df = df[df['Employee'].isin(reportees_df['Employee'])]
        
        total_emp = len(df)
        bench_count = len(df[df['Bench_Status']=="On Bench"])
        part_util = len(df[df['Bench_Status']=="Partially Utilized"])
        full_util = len(df[df['Bench_Status']=="Fully Utilized"])

        k1,k2,k3,k4 = st.columns([1,1,1,1])
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

        # Department Utilization Chart
        dept_util = df.groupby('Dept')['True_Utilization'].mean().reset_index()
        chart2 = alt.Chart(dept_util).mark_bar().encode(
            x='Dept',
            y='True_Utilization',
            color='Dept'
        )
        st.altair_chart(chart2, use_container_width=True)

        # Connected Line Chart for Utilization Trend
        line_chart = alt.Chart(df.reset_index()).mark_line(point=True).encode(
            x='index',
            y='True_Utilization',
            color='Dept',
            tooltip=['Employee','Dept','True_Utilization']
        )
        st.altair_chart(line_chart, use_container_width=True)

        # Data Table
        st.dataframe(df[['Employee','Dept','Bench_Status','True_Utilization']], height=300)

        # AI Recommendations only for HR Head
        if st.session_state['role']=="HR Head":
            st.subheader("AI Recommendations 🤖")
            recs = ai_recommendations(df, proj_df)
            for i, rec in enumerate(recs,1):
                st.markdown(f"**{i}.** {rec}")

# ---------- Skill Recommendations ----------
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

# ---------- Project Assignment ----------
elif page=="🚀 Project Assignment":
    st.subheader("Project Assignment 🚀")
    df_emp = st.session_state['activity']
    df_proj = st.session_state['projects']
    reportees_df = st.session_state['reportees']
    if df_emp.empty or df_proj.empty:
        st.info("Upload Employee Activity and Project Assignment file first")
    else:
        if st.session_state['role']=="Project Manager" and not reportees_df.empty:
            df_emp = df_emp[df_emp['Employee'].isin(reportees_df['Employee'])]
        
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
