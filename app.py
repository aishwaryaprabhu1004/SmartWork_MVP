import streamlit as st
import pandas as pd
import altair as alt

# ---------------- Page Config ----------------
st.set_page_config(
    page_title="SmartWork.AI",
    page_icon="💡",
    layout="wide"
)

# ---------------- Custom Sidebar ----------------
st.markdown("""
<style>
[data-testid="stSidebar"] { width: 250px; }
.sidebar .sidebar-content { display: flex; flex-direction: column; align-items: center; }
.sidebar .sidebar-content div[role="radiogroup"] > label { font-size: 22px; padding: 15px 0; }
</style>
""", unsafe_allow_html=True)

# ---------------- Session State ----------------
for key in ['activity','skills','projects','reportees','role']:
    if key not in st.session_state:
        st.session_state[key] = pd.DataFrame() if key!='role' else 'HR Head'

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
    df['Bench_Status'] = df['True_Utilization'].apply(lambda x: "On Bench" if x<20 else ("Partially Utilized" if x<50 else "Fully Utilized"))
    return df

def ai_recommendations(df, proj_df):
    recs = []
    if df.empty: return recs

    low_util = df[df['True_Utilization']<20]
    for _, emp in low_util.iterrows():
        recs.append(f"Employee {emp['Employee']} is underutilized. Consider assigning to high-priority projects.")

    if 'Cost' in df.columns:
        high_cost_low_util = df[(df['True_Utilization']<40)&(df['Cost']>df['Cost'].mean())]
        for _, emp in high_cost_low_util.iterrows():
            recs.append(f"Employee {emp['Employee']} has high cost (${emp['Cost']}) but low utilization. Consider reassignment or training.")

    if not proj_df.empty:
        critical_projects = proj_df.head(3)
        for _, proj in critical_projects.iterrows():
            available_emps = df[df['Bench_Status']!="Fully Utilized"]
            if not available_emps.empty:
                emp = available_emps.iloc[0]
                recs.append(f"Deploy {emp['Employee']} to project '{proj['Project_Name']}' to increase client satisfaction and billing efficiency.")
    return recs

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

# ---------------- Top Role Selector ----------------
col1, col2 = st.columns([9,1])
with col1:
    pass
with col2:
    st.session_state['role'] = st.selectbox("Role", ["HR Head","Project Manager"], index=["HR Head","Project Manager"].index(st.session_state['role']))

# ---------------- Pages ----------------
if page=="🏠 Homepage":
    col1, col2 = st.columns([1,4])
    with col1: st.image("logo.png", width=250)
    with col2:
        st.title("SmartWork.AI")
        st.markdown("**AI-powered tool for CHROs**")
        st.write("Manage employee performance, skills, project assignments, and get actionable AI recommendations.")

elif page=="📤 Upload Data":
    st.subheader("Upload Data 📤")
    f1 = st.file_uploader("Employee Activity", type=["csv","xlsx"])
    f2 = st.file_uploader("Skill Training", type=["csv","xlsx"])
    f3 = st.file_uploader("Project Assignment", type=["csv","xlsx"])
    f4 = st.file_uploader("Reportees Mapping (for Project Manager)", type=["csv","xlsx"])
    if st.button("Submit Files"):
        if f1: st.session_state['activity'] = load_file(f1)
        if f2: st.session_state['skills'] = load_file(f2)
        if f3: st.session_state['projects'] = load_file(f3)
        if f4: st.session_state['reportees'] = load_file(f4)
        st.success("Files Uploaded Successfully!")

elif page=="🏠📈 Dashboard & Analytics":
    st.subheader("Dashboard & Analytics 🏠📈")
    df = calculate_utilization(st.session_state['activity'])
    proj_df = st.session_state['projects']
    reportees_df = st.session_state['reportees']

    if st.session_state['role']=="Project Manager" and not reportees_df.empty:
        df = df[df['Employee'].isin(reportees_df['Reportee'])]

    if df.empty:
        st.info("Upload Employee Activity first")
    else:
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
        chart1 = alt.Chart(bench_chart).mark_bar().encode(x='Bench_Status',y='Count',color='Bench_Status')
        st.altair_chart(chart1, use_container_width=True)

        # Dept Utilization
        if 'Dept' in df.columns:
            dept_util = df.groupby('Dept')['True_Utilization'].mean().reset_index()
            chart2 = alt.Chart(dept_util).mark_line(point=True).encode(x='Dept',y='True_Utilization',color='Dept')
            st.altair_chart(chart2, use_container_width=True)

        # AI Recommendations (HR Head only)
        if st.session_state['role']=="HR Head":
            recs = ai_recommendations(df, proj_df)
            if recs:
                st.subheader("AI Recommendations")
                for r in recs:
                    st.write(f"- {r}")

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

elif page=="🚀 Project Assignment":
    st.subheader("Project Assignment 🚀")
    df_emp = st.session_state['activity']
    df_proj = st.session_state['projects']
    if st.session_state['role']=="Project Manager" and not reportees_df.empty:
        df_emp = df_emp[df_emp['Employee'].isin(reportees_df['Reportee'])]

    if df_emp.empty or df_proj.empty:
        st.info("Upload Employee Activity and Project Assignment file first")
    else:
        assignments = []
        for _, emp in df_emp.iterrows():
            emp_skills = set(str(emp.get('Skills','')).split(","))
            for _, proj in df_proj.iterrows():
                proj_skills = set(str(proj.get('Required_Skills','')).split(","))
                if emp_skills & proj_skills:
                    assignments.append({'Employee': emp.get('Employee',''),'Project': proj.get('Project_Name',''),'Skill_Match': ", ".join(emp_skills & proj_skills)})
        st.dataframe(pd.DataFrame(assignments), height=400)









