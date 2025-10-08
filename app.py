import streamlit as st
import pandas as pd
import altair as alt

# ---------------- Page Config ----------------
st.set_page_config(
    page_title="SmartWork.AI",
    page_icon="💡",
    layout="wide"
)

# ---------------- SESSION STATE ----------------
if 'activity' not in st.session_state: st.session_state['activity'] = pd.DataFrame()
if 'skills' not in st.session_state: st.session_state['skills'] = pd.DataFrame()
if 'projects' not in st.session_state: st.session_state['projects'] = pd.DataFrame()
if 'role' not in st.session_state: st.session_state['role'] = "HR Head"
if 'reportees' not in st.session_state: st.session_state['reportees'] = pd.DataFrame()

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
    if df.empty: return df
    df['Activity_Score'] = (
        0.4*df.get('Tasks_Completed',0) +
        0.3*df.get('Meetings_Duration',0) +
        0.2*df.get('Decisions_Made',0) +
        0.1*df.get('Docs_Updated',0)
    )
    df['True_Utilization'] = (df['Activity_Score']/df['Activity_Score'].max())*100
    df['Bench_Status'] = df['True_Utilization'].apply(
        lambda x: "On Bench" if x<20 else ("Partially Utilized" if x<50 else "Fully Utilized")
    )
    return df

# ---------------- CUSTOM CSS ----------------
st.markdown("""
<style>
/* Sidebar Width */
[data-testid="stSidebar"] { width: 250px; }
/* Sidebar Labels */
.sidebar .sidebar-content div[role="radiogroup"] > label { font-size: 20px; padding: 12px 0; }
/* Logo Styling */
.logo {width: 180px; display:block; margin-bottom: 20px;}
/* Homepage Styling */
.homepage-title {font-size: 36px; font-weight: bold; margin-bottom: 5px;}
.homepage-desc {font-size: 18px; color: #555; margin-bottom: 20px;}
/* Role Selector Positioning */
.role-selector {position: absolute; top: 20px; right: 50px;}
</style>
""", unsafe_allow_html=True)

# ---------------- SIDEBAR ----------------
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

# ---------------- ROLE SELECTOR ----------------
with st.container():
    role = st.selectbox(
        "Select Role", 
        ["HR Head", "Project Manager"], 
        index=0 if st.session_state['role']=="HR Head" else 1
    )
    st.session_state['role'] = role

# ---------------- HOMEPAGE ----------------
if page == "🏠 Homepage":
    st.image("logo.png", width=220)
    st.markdown('<div class="homepage-title">SmartWork.AI</div>', unsafe_allow_html=True)
    st.markdown('<div class="homepage-desc">The AI-powered tool for CHROs</div>', unsafe_allow_html=True)

# ---------------- DATA UPLOAD ----------------
elif page == "📤 Upload Data":
    st.image("logo.png", width=220)
    st.subheader("Upload Data 📤")
    f1 = st.file_uploader("Employee Activity", type=["csv","xlsx"])
    f2 = st.file_uploader("Skill Training", type=["csv","xlsx"])
    f3 = st.file_uploader("Project Assignment", type=["csv","xlsx"])
    f4 = st.file_uploader("Reportees (Project Manager Only)", type=["csv","xlsx"])

    if st.button("Submit Uploads"):
        if f1: st.session_state['activity'] = load_file(f1)
        if f2: st.session_state['skills'] = load_file(f2)
        if f3: st.session_state['projects'] = load_file(f3)
        if f4: st.session_state['reportees'] = load_file(f4)
        st.success("Files uploaded successfully!")

# ---------------- DASHBOARD & ANALYTICS ----------------
elif page == "🏠📈 Dashboard & Analytics":
    st.image("logo.png", width=220)
    st.markdown(f"**Current Role:** {st.session_state['role']}", unsafe_allow_html=True)
    
    df = calculate_utilization(st.session_state['activity'])
    proj_df = st.session_state['projects']
    
    if df.empty:
        st.info("Upload Employee Activity first")
    else:
        role = st.session_state['role']
        if role == "Project Manager" and not st.session_state['reportees'].empty:
            df = df[df['Employee'].isin(st.session_state['reportees']['Employee'])]
        
        # Key Metrics
        total_emp = len(df)
        bench_count = len(df[df['Bench_Status']=="On Bench"])
        part_util = len(df[df['Bench_Status']=="Partially Utilized"])
        full_util = len(df[df['Bench_Status']=="Fully Utilized"])
        k1,k2,k3,k4 = st.columns([1,1,1,1])
        k1.metric("Total Employees", total_emp)
        k2.metric("On Bench", bench_count)
        k3.metric("Partial Utilization", part_util)
        k4.metric("Full Utilization", full_util)
        
        # Bench Status Bar
        bench_chart = df['Bench_Status'].value_counts().reset_index()
        bench_chart.columns = ['Bench_Status','Count']
        st.altair_chart(
            alt.Chart(bench_chart).mark_bar().encode(
                x='Bench_Status', y='Count', color='Bench_Status'
            ), use_container_width=True
        )
        
        # Department Utilization
        dept_util = df.groupby('Dept')['True_Utilization'].mean().reset_index()
        st.altair_chart(
            alt.Chart(dept_util).mark_line(point=True).encode(
                x='Dept', y='True_Utilization', color='Dept'
            ), use_container_width=True
        )
        
        # HR Only AI Recommendations
        if role == "HR Head":
            st.subheader("AI Recommendations for HR Head 🔥")
            recommendations = [
                "Reallocate underutilized employees to high-priority projects.",
                "Upskill employees with missing critical skills for upcoming projects.",
                "Consider temporary bench reduction strategies to optimize billing.",
                "Review high-cost projects and redistribute resources for efficiency."
            ]
            for rec in recommendations:
                st.markdown(f"- {rec}")
        
        # Show Data Table
        st.dataframe(df[['Employee','Dept','Bench_Status','True_Utilization']], height=300)

# ---------------- SKILL RECOMMENDATIONS ----------------
elif page == "🎯 Skill Recommendations":
    st.image("logo.png", width=220)
    st.markdown(f"**Current Role:** {st.session_state['role']}", unsafe_allow_html=True)
    df_emp = st.session_state['activity']
    df_skills = st.session_state['skills']
    if df_emp.empty or df_skills.empty: st.info("Upload both Employee Activity and Skills file first")
    else:
        required_skills = df_skills['Skill'].unique().tolist()
        def rec(skills_str):
            emp_skills = str(skills_str).split(",") if pd.notnull(skills_str) else []
            missing = list(set(required_skills)-set(emp_skills))
            return ", ".join(missing) if missing else "None"
        df_emp['Recommended_Skills'] = df_emp['Skills'].apply(rec)
        st.dataframe(df_emp[['Employee','Skills','Recommended_Skills','Bench_Status']], height=400)

# ---------------- PROJECT ASSIGNMENT ----------------
elif page == "🚀 Project Assignment":
    st.image("logo.png", width=220)
    st.markdown(f"**Current Role:** {st.session_state['role']}", unsafe_allow_html=True)
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







