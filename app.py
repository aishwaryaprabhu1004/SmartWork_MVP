import streamlit as st
import pandas as pd
import altair as alt

# ---------------- Page Config ----------------
st.set_page_config(
    page_title="SmartWork.AI",
    page_icon="💡",
    layout="wide"
)

# ---------------- Sidebar ----------------
with st.sidebar:
    st.title("Navigation")
    page = st.radio(
        "",
        options=[
            "🏠 Homepage",
            "📤 Upload Data",
            "🏠 Dashboard & Analytics",
            "🪑 Bench Utilization",
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

# ---------------- Top-Right Role Selector ----------------
st.markdown(
    """
    <style>
    .role-container {
        position: fixed;
        top: 80px;
        right: 20px;
        z-index: 1000;
    }
    </style>
    """,
    unsafe_allow_html=True
)

roles = ['HR Head', 'Project Manager']
selected_role = st.selectbox('Select Role', roles, index=roles.index(st.session_state['role']), key='role_select', help="Change role to switch view")
st.session_state['role'] = selected_role

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

def ai_recommendations(activity_df, proj_df):
    recs = []
    if activity_df.empty or proj_df.empty:
        return ["No data to generate recommendations."]
    for _, emp in activity_df.iterrows():
        utilization = emp.get('True_Utilization',0)
        if utilization < 50:
            recs.append(f"Employee {emp.get('Employee','')} is underutilized. Consider reassigning to high-priority projects.")
    return recs if recs else ["All employees are optimally utilized."]

# ---------------- Pages ----------------
if page=="🏠 Homepage":
    col1, col2 = st.columns([1,3])
    with col1:
        st.image("logo.png", width=250)  # Ensure logo.png is in repo
    with col2:
        st.title("SmartWork.AI")
        st.subheader("The AI-powered tool for CHROs")
        st.write("Analyze employee activity, optimize project assignments, and get actionable AI-driven recommendations to improve utilization and billing.")

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
        f4 = st.file_uploader("Reportees (for Project Managers)", type=["csv","xlsx"])
        if f4: st.session_state['reportees'] = load_file(f4)

elif page=="🏠 Dashboard & Analytics":
    st.subheader("Dashboard & Analytics 🏠📈")
    df = calculate_utilization(st.session_state['activity'])
    proj_df = st.session_state['projects']
    
    if df.empty:
        st.info("Upload Employee Activity first")
    else:
        # Filter based on role
        if st.session_state['role']=='Project Manager' and not st.session_state['reportees'].empty:
            reportees_list = st.session_state['reportees']['Employee'].tolist()
            df = df[df['Employee'].isin(reportees_list)]
        
        # KPIs
        total_emp = len(df)
        bench_count = len(df[df['Bench_Status']=="On Bench"])
        part_util = len(df[df['Bench_Status']=="Partially Utilized"])
        full_util = len(df[df['Bench_Status']=="Fully Utilized"])
        k1,k2,k3,k4 = st.columns(4)
        k1.metric("Total Employees", total_emp)
        k2.metric("On Bench", bench_count)
        k3.metric("Partial Utilization", part_util)
        k4.metric("Full Utilization", full_util)
        
        # Bench Status Bar Chart
        bench_chart = df['Bench_Status'].value_counts().reset_index()
        bench_chart.columns = ['Bench_Status','Count']
        st.altair_chart(
            alt.Chart(bench_chart).mark_bar().encode(
                x='Bench_Status',
                y='Count',
                color='Bench_Status'
            ),
            use_container_width=True
        )
        
        # Dept Utilization Line Chart
        dept_util = df.groupby('Dept')['True_Utilization'].mean().reset_index()
        st.altair_chart(
            alt.Chart(dept_util).mark_line(point=True).encode(
                x=alt.X('Dept', sort=None),
                y='True_Utilization',
                color='Dept',
                tooltip=['Dept','True_Utilization']
            ).interactive(),
            use_container_width=True
        )

        # Data Table
        st.dataframe(df[['Employee','Dept','Bench_Status','True_Utilization']], height=300)
        
        # AI Recommendations (HR Head only)
        if st.session_state['role']=='HR Head':
            st.subheader("AI Recommendations for HR Head")
            recs = ai_recommendations(df, proj_df)
            for r in recs:
                st.info(r)

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
        if 'Skill' in df_skills.columns:
            required_skills = df_skills['Skill'].unique().tolist()
            def rec(skills_str):
                emp_skills = str(skills_str).split(",") if pd.notnull(skills_str) else []
                missing = list(set(required_skills) - set(emp_skills))
                return ", ".join(missing) if missing else "None"
            df_emp['Recommended_Skills'] = df_emp['Skills'].apply(rec)
            st.dataframe(df_emp[['Employee','Skills','Recommended_Skills','Bench_Status']], height=400)
        else:
            st.warning("Skill column not found in Skills file")

elif page=="🚀 Project Assignment":
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
