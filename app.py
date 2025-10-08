import streamlit as st
import pandas as pd
import altair as alt

# ---------------- Page Config ----------------
st.set_page_config(
    page_title="SmartWork.AI",
    page_icon="💡",
    layout="wide"
)

# ---------------- Session State Defaults ----------------
if 'activity' not in st.session_state: st.session_state['activity'] = pd.DataFrame()
if 'skills' not in st.session_state: st.session_state['skills'] = pd.DataFrame()
if 'projects' not in st.session_state: st.session_state['projects'] = pd.DataFrame()
if 'reportees' not in st.session_state: st.session_state['reportees'] = pd.DataFrame()
if 'role' not in st.session_state: st.session_state['role'] = 'HR Head'

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

def ai_recommendations(df):
    # Placeholder AI logic: analyze costs and utilization
    if df.empty: return ["No data to generate AI recommendations."]
    recs = []
    low_util = df[df['True_Utilization']<30]
    if not low_util.empty:
        recs.append(f"Consider reskilling or reassigning {len(low_util)} low-utilization employees.")
    high_cost = df.get('Cost', pd.Series([0]*len(df)))
    if high_cost.sum()>100000:  # Example threshold
        recs.append("High costs detected: consider reviewing expensive projects or vendors.")
    recs.append("Focus on projects with high utilization for increased billing efficiency.")
    return recs

# ---------------- Top-right Role Selector ----------------
_, col_role = st.columns([8,1])
with col_role:
    st.selectbox("Role", ["HR Head","Project Manager"], index=0, key="role")

# ---------------- Custom Sidebar ----------------
st.markdown("""
<style>
[data-testid="stSidebar"] {
    width: 250px;
}
.sidebar .sidebar-content {
    display: flex;
    flex-direction: column;
    align-items: center;
}
.sidebar .sidebar-content div[role="radiogroup"] > label {
    font-size: 22px;
    padding: 15px 0;
}
</style>
""", unsafe_allow_html=True)

# ---------------- Sidebar Navigation ----------------
if st.session_state['role']=="HR Head":
    page = st.sidebar.radio(
        "",
        options=[
            " Dashboard & Analytics",
            " Upload Data",
            " Bench Utilization",
            " Skill Recommendations",
            " Project Assignment"
        ]
    )
else:  # Project Manager
    page = st.sidebar.radio(
        "",
        options=[
            "Dashboard & Analytics",
            " Upload Data",
            "My Team Utilization",
            "My Team Skills",
            " Project Assignment"
        ]
    )

# ---------------- Pages ----------------
if page=="📤 Upload Data":
    st.subheader("Upload Data 📤")
    col1, col2, col3, col4 = st.columns([1,1,1,1])
    with col1:
        f1 = st.file_uploader("Employee Activity", type=["csv","xlsx"])
    with col2:
        f2 = st.file_uploader("Skill Training", type=["csv","xlsx"])
    with col3:
        f3 = st.file_uploader("Project Assignment", type=["csv","xlsx"])
    with col4:
        f4 = st.file_uploader("Reportees Mapping (Project Manager only)", type=["csv","xlsx"])
    
    if st.button("Submit"):
        if f1: st.session_state['activity'] = load_file(f1)
        if f2: st.session_state['skills'] = load_file(f2)
        if f3: st.session_state['projects'] = load_file(f3)
        if f4 and st.session_state['role']=="Project Manager": st.session_state['reportees'] = load_file(f4)
        st.success("Files uploaded successfully!")

# ---------------- Dashboard & Analytics ----------------
elif page=="🏠 Dashboard & Analytics":
    st.subheader("Dashboard & Analytics 🏠📈")
    df = calculate_utilization(st.session_state['activity'])
    if df.empty:
        st.info("Upload Employee Activity first")
    else:
        # Role-based view
        if st.session_state['role']=="Project Manager" and not st.session_state['reportees'].empty:
            df = df[df['Employee'].isin(st.session_state['reportees']['Employee'].tolist())]
        
        # KPIs
        total_emp = len(df)
        bench_count = len(df[df['Bench_Status']=="On Bench"])
        part_util = len(df[df['Bench_Status']=="Partially Utilized"])
        full_util = len(df[df['Bench_Status']=="Fully Utilized"])
        k1,k2,k3,k4 = st.columns([1,1,1,1])
        k1.metric("Total Employees", total_emp)
        k2.metric("On Bench", bench_count)
        k3.metric("Partial Utilization", part_util)
        k4.metric("Full Utilization", full_util)

        # Bench Status Bar Chart
        bench_chart = df['Bench_Status'].value_counts().reset_index()
        bench_chart.columns = ['Bench_Status','Count']
        chart1 = alt.Chart(bench_chart).mark_bar().encode(
            x='Bench_Status',
            y='Count',
            color='Bench_Status'
        )
        st.altair_chart(chart1, use_container_width=True)

        # Department Utilization Line Chart
        dept_util = df.groupby('Dept')['True_Utilization'].mean().reset_index()
        line_chart = alt.Chart(dept_util).mark_line(point=True).encode(
            x='Dept',
            y='True_Utilization',
            color='Dept'
        )
        st.altair_chart(line_chart, use_container_width=True)

        # Scatter: Utilization vs Bench Duration if available
        if 'Bench_Duration' in df.columns:
            scatter_chart = alt.Chart(df).mark_circle(size=60).encode(
                x='Bench_Duration',
                y='True_Utilization',
                color='Bench_Status',
                tooltip=['Employee','Dept','Bench_Status','True_Utilization']
            )
            st.altair_chart(scatter_chart, use_container_width=True)

        # Data Table
        st.dataframe(df[['Employee','Dept','Bench_Status','True_Utilization']], height=300)

        # AI Recommendations (HR Head only)
        if st.session_state['role']=="HR Head":
            st.subheader("AI Recommendations 🔥")
            recs = ai_recommendations(df)
            for r in recs:
                st.write("- " + r)

# ---------------- Bench / Skills / Projects for HR or PM ----------------
elif page in ["🪑 Bench Utilization","My Team Utilization"]:
    st.subheader("Bench Utilization 🪑")
    df = calculate_utilization(st.session_state['activity'])
    if st.session_state['role']=="Project Manager" and not st.session_state['reportees'].empty:
        df = df[df['Employee'].isin(st.session_state['reportees']['Employee'].tolist())]
    if df.empty:
        st.info("Upload Employee Activity first")
    else:
        st.dataframe(df[['Employee','Dept','Bench_Status','True_Utilization']], height=400)

elif page in ["🎯 Skill Recommendations","My Team Skills"]:
    st.subheader("Skill Recommendations 🎯")
    df_emp = st.session_state['activity']
    df_skills = st.session_state['skills']
    if st.session_state['role']=="Project Manager" and not st.session_state['reportees'].empty:
        df_emp = df_emp[df_emp['Employee'].isin(st.session_state['reportees']['Employee'].tolist())]
    if df_emp.empty or df_skills.empty: st.info("Upload both Employee Activity and Skills file first")
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
    if st.session_state['role']=="Project Manager" and not st.session_state['reportees'].empty:
        df_emp = df_emp[df_emp['Employee'].isin(st.session_state['reportees']['Employee'].tolist())]
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





