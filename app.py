import streamlit as st
import pandas as pd
import altair as alt

# ---------------- Page Config ----------------
st.set_page_config(
    page_title="SmartWork.AI",
    page_icon="💡",
    layout="wide"
)

# ---------------- Session State ----------------
if 'activity' not in st.session_state: st.session_state['activity'] = pd.DataFrame()
if 'skills' not in st.session_state: st.session_state['skills'] = pd.DataFrame()
if 'projects' not in st.session_state: st.session_state['projects'] = pd.DataFrame()
if 'reportees' not in st.session_state: st.session_state['reportees'] = pd.DataFrame()
if 'role' not in st.session_state: st.session_state['role'] = None

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

def ai_recommendations(df, role):
    if df.empty:
        return []
    recs = []
    if role=="HR Head":
        low_util = df[df['True_Utilization']<50]
        for _, row in low_util.iterrows():
            recs.append(f"Upskill {row['Employee']} in missing skills to improve billing.")
    elif role=="Project Manager":
        low_util = df[df['True_Utilization']<50]
        for _, row in low_util.iterrows():
            recs.append(f"Assign tasks matching {row['Employee']}'s skills to increase project output.")
    return recs

# ---------------- File Upload ----------------
st.sidebar.subheader("1️⃣ Upload Data")
with st.sidebar.form("upload_form"):
    f1 = st.file_uploader("Employee Activity", type=["csv","xlsx"])
    f2 = st.file_uploader("Skill Training", type=["csv","xlsx"])
    f3 = st.file_uploader("Project Assignment", type=["csv","xlsx"])
    f4 = st.file_uploader("Reportees Mapping", type=["csv","xlsx"])
    submitted = st.form_submit_button("Upload Files")
    if submitted:
        if f1: st.session_state['activity'] = load_file(f1)
        if f2: st.session_state['skills'] = load_file(f2)
        if f3: st.session_state['projects'] = load_file(f3)
        if f4: st.session_state['reportees'] = load_file(f4)
        st.success("Files uploaded successfully!")

# ---------------- Role Selection ----------------
st.sidebar.subheader("2️⃣ Select Role")
role_options = ["HR Head", "Project Manager"]
role = st.sidebar.selectbox("Current Role:", role_options, index=role_options.index(st.session_state['role']) if st.session_state['role'] else 0)
st.session_state['role'] = role

# ---------------- Sidebar Navigation ----------------
available_pages = ["🏠 Dashboard & Analytics", "🪑 Bench Utilization", "🎯 Skill Recommendations", "🚀 Project Assignment"]
page = st.sidebar.radio("Navigation", options=available_pages)

# ---------------- Pages ----------------
df = calculate_utilization(st.session_state['activity'])
reportees_df = st.session_state['reportees']

# Filter for Project Manager
if role=="Project Manager" and not reportees_df.empty:
    pm_name = st.sidebar.selectbox("Select Your Name:", reportees_df['PM_Name'].unique())
    emp_list = reportees_df[reportees_df['PM_Name']==pm_name]['Employee'].tolist()
    df = df[df['Employee'].isin(emp_list)]

# ---------------- Dashboard & Analytics ----------------
if page=="🏠 Dashboard & Analytics":
    st.subheader("Dashboard & Analytics 🏠📈")
    if df.empty:
        st.info("Upload relevant data first")
    else:
        # Metrics
        total_emp = len(df)
        bench_count = len(df[df['Bench_Status']=="On Bench"])
        part_util = len(df[df['Bench_Status']=="Partially Utilized"])
        full_util = len(df[df['Bench_Status']=="Fully Utilized"])
        k1,k2,k3,k4 = st.columns([1,1,1,1])
        k1.metric("Total Employees", total_emp)
        k2.metric("On Bench", bench_count)
        k3.metric("Partial Utilization", part_util)
        k4.metric("Full Utilization", full_util)

        # Bench Bar Chart
        bench_chart = df['Bench_Status'].value_counts().reset_index()
        bench_chart.columns = ['Bench_Status','Count']
        st.altair_chart(
            alt.Chart(bench_chart).mark_bar().encode(
                x='Bench_Status', y='Count', color='Bench_Status'
            ),
            use_container_width=True
        )

        # Dept Util Line Chart
        dept_util = df.groupby('Dept')['True_Utilization'].mean().reset_index()
        st.altair_chart(
            alt.Chart(dept_util).mark_line(point=True).encode(
                x='Dept', y='True_Utilization', color='Dept'
            ),
            use_container_width=True
        )

        # Scatter Chart
        if 'Bench_Duration' in df.columns:
            st.altair_chart(
                alt.Chart(df).mark_circle(size=60).encode(
                    x='Bench_Duration', y='True_Utilization', color='Bench_Status',
                    tooltip=['Employee','Dept','Bench_Status','True_Utilization']
                ),
                use_container_width=True
            )

        # AI Recommendations
        recs = ai_recommendations(df, role)
        if recs:
            st.subheader("AI-based Recommendations")
            for r in recs[:10]:
                st.write("•", r)

        st.dataframe(df[['Employee','Dept','Bench_Status','True_Utilization']], height=400)

# ---------------- Bench Utilization ----------------
elif page=="🪑 Bench Utilization":
    st.subheader("Bench Utilization 🪑")
    if df.empty:
        st.info("Upload Employee Activity first")
    else:
        st.dataframe(df[['Employee','Dept','Bench_Status','True_Utilization']], height=400)

# ---------------- Skill Recommendations ----------------
elif page=="🎯 Skill Recommendations":
    st.subheader("Skill Recommendations 🎯")
    df_skills = st.session_state['skills']
    if df.empty or df_skills.empty:
        st.info("Upload both Employee Activity and Skills file first")
    else:
        required_skills = df_skills['Skill'].unique().tolist()
        def rec(skills_str):
            emp_skills = str(skills_str).split(",") if pd.notnull(skills_str) else []
            missing = list(set(required_skills) - set(emp_skills))
            return ", ".join(missing) if missing else "None"
        df['Recommended_Skills'] = df['Skills'].apply(rec)
        st.dataframe(df[['Employee','Skills','Recommended_Skills','Bench_Status']], height=400)

# ---------------- Project Assignment ----------------
elif page=="🚀 Project Assignment":
    st.subheader("Project Assignment 🚀")
    df_proj = st.session_state['projects']
    if df.empty or df_proj.empty:
        st.info("Upload Employee Activity and Project Assignment file first")
    else:
        assignments = []
        for _, emp in df.iterrows():
            emp_skills = set(str(emp.get('Skills','')).split(","))
            for _, proj in df_proj.iterrows():
                proj_skills = set(str(proj.get('Required_Skills','')).split(",")) if pd.notnull(proj.get('Required_Skills','')) else set()
                if emp_skills & proj_skills:
                    assignments.append({
                        'Employee': emp.get('Employee',''),
                        'Project': proj.get('Project_Name',''),
                        'Skill_Match': ", ".join(emp_skills & proj_skills)
                    })
        st.dataframe(pd.DataFrame(assignments), height=400)


