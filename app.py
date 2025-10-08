import streamlit as st
import pandas as pd
import altair as alt

# ---------------- Page Config ----------------
st.set_page_config(page_title="SmartWork.AI", page_icon="💡", layout="wide")

# ---------------- Helper Functions ----------------
def load_file(file):
    if file:
        try:
            if file.name.endswith(".csv"):
                df = pd.read_csv(file)
            else:
                df = pd.read_excel(file, engine='openpyxl')
            df.columns = df.columns.str.strip()  # Clean column names
            return df
        except Exception as e:
            st.error(f"Failed to load file: {e}")
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
    df['True_Utilization'] = (df['Activity_Score']/df['Activity_Score'].max())*100
    df['Bench_Status'] = df['True_Utilization'].apply(lambda x: "On Bench" if x<20 else ("Partially Utilized" if x<50 else "Fully Utilized"))
    return df

def ai_recommendations(df, proj_df):
    recs = []
    if df.empty: return recs

    # Clean column names
    df = df.rename(columns=lambda x: x.strip())
    proj_df = proj_df.rename(columns=lambda x: x.strip())

    emp_col = 'Employee' if 'Employee' in df.columns else df.columns[0]
    cost_col = 'Cost' if 'Cost' in df.columns else None

    # Underutilized employees
    if 'True_Utilization' in df.columns:
        low_util = df[df['True_Utilization']<20]
        for _, emp in low_util.iterrows():
            recs.append(f"Employee {emp.get(emp_col,'Unknown')} is underutilized. Assign to high-priority projects.")

    # High cost but low utilization
    if cost_col:
        high_cost_low_util = df[(df['True_Utilization']<40)&(df[cost_col]>df[cost_col].mean())]
        for _, emp in high_cost_low_util.iterrows():
            recs.append(f"Employee {emp.get(emp_col,'Unknown')} has high cost (${emp.get(cost_col,0)}) but low utilization. Consider reassignment or training.")

    # Critical projects
    if not proj_df.empty and 'Project_Name' in proj_df.columns:
        critical_projects = proj_df.head(3)
        available_emps = df[df.get('Bench_Status',"")!="Fully Utilized"] if 'Bench_Status' in df.columns else df
        for _, proj in critical_projects.iterrows():
            if not available_emps.empty:
                emp = available_emps.iloc[0]
                recs.append(f"Deploy {emp.get(emp_col,'Unknown')} to project '{proj.get('Project_Name','Unknown')}' for increased client satisfaction and billing.")

    return recs

# ---------------- Session State ----------------
for key in ['activity','skills','projects','reportees','role']:
    if key not in st.session_state:
        st.session_state[key] = pd.DataFrame() if key != 'role' else 'HR Head'

# ---------------- Layout: Top Bar ----------------
st.markdown("""
<style>
.topbar {display: flex; justify-content: space-between; align-items: center; padding: 10px;}
.logo {height: 80px;}
</style>
""", unsafe_allow_html=True)

topbar = st.container()
with topbar:
    st.markdown('<div class="topbar">', unsafe_allow_html=True)
    st.image("logo.png", width=120)
    selected_role = st.selectbox("Select Role:", ["HR Head", "Project Manager"], index=0)
    st.session_state['role'] = selected_role
    st.markdown('</div>', unsafe_allow_html=True)

# ---------------- Sidebar ----------------
st.sidebar.markdown("## Navigation")
pages = ["🏠 Homepage", "📤 Upload Data", "🏠📈 Dashboard & Analytics", "🪑 Bench Utilization",
         "🎯 Skill Recommendations", "🚀 Project Assignment"]
st.sidebar.radio("Go to:", pages, key="sidebar_page")

# ---------------- Pages ----------------
page = st.session_state["sidebar_page"]

# ---------- Homepage ----------
if page=="🏠 Homepage":
    st.title("SmartWork.AI")
    st.subheader("The AI-powered tool for CHROs")
    st.markdown("""
    **SmartWork.AI** helps HR Heads and Project Managers make data-driven decisions,
    optimize employee utilization, recommend skills, and assign employees to projects efficiently.
    """)
    st.image("logo.png", width=300)

# ---------- Upload Data ----------
elif page=="📤 Upload Data":
    st.subheader("Upload Data Files")
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
        f4 = st.file_uploader("Reportees Mapping (for PMs)", type=["csv","xlsx"])
        if f4: st.session_state['reportees'] = load_file(f4)

# ---------- Dashboard & Analytics ----------
elif page=="🏠📈 Dashboard & Analytics":
    st.subheader("Dashboard & Analytics")
    df = calculate_utilization(st.session_state['activity'])
    proj_df = st.session_state['projects']

    if df.empty:
        st.info("Upload Employee Activity first")
    else:
        # Role-based view
        if st.session_state['role']=="Project Manager" and not st.session_state['reportees'].empty:
            reportees_list = st.session_state['reportees']['Employee'].tolist()
            df = df[df['Employee'].isin(reportees_list)]

        total_emp = len(df)
        bench_count = len(df[df['Bench_Status']=="On Bench"])
        part_util = len(df[df['Bench_Status']=="Partially Utilized"])
        full_util = len(df[df['Bench_Status']=="Fully Utilized"])

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Employees", total_emp)
        col2.metric("On Bench", bench_count)
        col3.metric("Partial Utilization", part_util)
        col4.metric("Full Utilization", full_util)

        # Bench Status Bar
        bench_chart = df['Bench_Status'].value_counts().reset_index()
        bench_chart.columns = ['Bench_Status','Count']
        chart1 = alt.Chart(bench_chart).mark_bar().encode(
            x='Bench_Status', y='Count', color='Bench_Status'
        )
        st.altair_chart(chart1, use_container_width=True)

        # Dept Utilization
        dept_util = df.groupby('Dept')['True_Utilization'].mean().reset_index()
        chart2 = alt.Chart(dept_util).mark_line(point=True).encode(
            x='Dept', y='True_Utilization', color='Dept'
        )
        st.altair_chart(chart2, use_container_width=True)

        # Data Table
        st.dataframe(df[['Employee','Dept','Bench_Status','True_Utilization']], height=300)

        # AI Recommendations only for HR Head
        if st.session_state['role']=="HR Head":
            recs = ai_recommendations(df, proj_df)
            if recs:
                st.markdown("### AI Recommendations")
                for r in recs:
                    st.info(r)

# ---------- Bench Utilization ----------
elif page=="🪑 Bench Utilization":
    st.subheader("Bench Utilization")
    df = calculate_utilization(st.session_state['activity'])
    if df.empty:
        st.info("Upload Employee Activity first")
    else:
        st.dataframe(df[['Employee','Dept','Bench_Status','True_Utilization']], height=400)

# ---------- Skill Recommendations ----------
elif page=="🎯 Skill Recommendations":
    st.subheader("Skill Recommendations")
    df_emp = st.session_state['activity']
    df_skills = st.session_state['skills']
    if df_emp.empty or df_skills.empty:
        st.info("Upload both Employee Activity and Skills file first")
    else:
        required_skills = df_skills['Skill'].unique().tolist() if 'Skill' in df_skills.columns else []
        def rec(skills_str):
            emp_skills = str(skills_str).split(",") if pd.notnull(skills_str) else []
            missing = list(set(required_skills)-set(emp_skills))
            return ", ".join(missing) if missing else "None"
        df_emp['Recommended_Skills'] = df_emp.get('Skills','').apply(rec)
        st.dataframe(df_emp[['Employee','Skills','Recommended_Skills','Bench_Status']], height=400)

# ---------- Project Assignment ----------
elif page=="🚀 Project Assignment":
    st.subheader("Project Assignment")
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










