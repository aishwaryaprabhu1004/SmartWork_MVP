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
/* Make sidebar wider */
[data-testid="stSidebar"] {
    width: 250px;
}
/* Big icons, centered */
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
page = st.sidebar.radio(
    "Navigation",
    options=[
        "🏠 Dashboard & Analytics",
        "🪑 Bench Utilization",
        "🎯 Skill Recommendations",
        "🚀 Project Assignment",
        "📤 Upload Data"
    ]
)

# ---------------- Role Selection ----------------
role = st.sidebar.selectbox("Select Your Role", ["HR Head", "Project Manager"])

# ---------------- Session State ----------------
if 'activity' not in st.session_state: st.session_state['activity'] = pd.DataFrame()
if 'skills' not in st.session_state: st.session_state['skills'] = pd.DataFrame()
if 'projects' not in st.session_state: st.session_state['projects'] = pd.DataFrame()

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
    # Rule-based heuristic AI
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

# ---------------- Pages ----------------
if page=="📤 Upload Data":
    st.subheader("Upload Data 📤")
    col1, col2, col3 = st.columns([1,1,1])
    with col1:
        f1 = st.file_uploader("Employee Activity", type=["csv","xlsx"])
    with col2:
        f2 = st.file_uploader("Skill Training", type=["csv","xlsx"])
    with col3:
        f3 = st.file_uploader("Project Assignment", type=["csv","xlsx"])

    if st.button("Submit Uploads"):
        if f1: st.session_state['activity'] = load_file(f1)
        if f2: st.session_state['skills'] = load_file(f2)
        if f3: st.session_state['projects'] = load_file(f3)
        st.success("Files uploaded successfully!")

elif page=="🏠 Dashboard & Analytics":
    st.subheader("Dashboard & Analytics 🏠📈")
    df = calculate_utilization(st.session_state['activity'])
    if df.empty:
        st.info("Upload Employee Activity first")
    else:
        # Role-based filtering
        if role == "Project Manager" and 'Manager' in df.columns:
            df = df[df['Manager'] == 'Your Name']  # Replace with logic for PM view

        # KPI cards
        total_emp = len(df)
        bench_count = len(df[df['Bench_Status']=="On Bench"])
        part_util = len(df[df['Bench_Status']=="Partially Utilized"])
        full_util = len(df[df['Bench_Status']=="Fully Utilized"])
        k1,k2,k3,k4 = st.columns([1,1,1,1])
        k1.metric("Total Employees", total_emp)
        k2.metric("On Bench", bench_count)
        k3.metric("Partial Utilization", part_util)
        k4.metric("Full Utilization", full_util)

        # 1️⃣ Bench Status Bar Chart
        if 'Bench_Status' in df.columns:
            bench_chart = df['Bench_Status'].value_counts().reset_index()
            bench_chart.columns = ['Bench_Status','Count']
            chart1 = alt.Chart(bench_chart).mark_bar().encode(
                x='Bench_Status',
                y='Count',
                color='Bench_Status'
            )
            st.altair_chart(chart1, use_container_width=True)

        # 2️⃣ Department-wise Pie Chart
        if 'Dept' in df.columns:
            dept_counts = df['Dept'].value_counts().reset_index()
            dept_counts.columns = ['Dept','Count']
            chart2 = alt.Chart(dept_counts).mark_arc(innerRadius=50).encode(
                theta='Count',
                color='Dept',
                tooltip=['Dept','Count']
            )
            st.altair_chart(chart2, use_container_width=True)

        # 3️⃣ Department Utilization Line Chart
        if 'Dept' in df.columns:
            dept_util = df.groupby('Dept')['True_Utilization'].mean().reset_index()
            chart3 = alt.Chart(dept_util).mark_line(point=True).encode(
                x='Dept',
                y='True_Utilization',
                color='Dept'
            )
            st.altair_chart(chart3, use_container_width=True)

        # 4️⃣ Stacked Bar: Project vs Bench_Status (if project file exists)
        proj_df = st.session_state['projects']
        if not proj_df.empty and 'Assigned_Employee' in proj_df.columns and 'Project_Name' in proj_df.columns:
            merged = pd.merge(df, proj_df, left_on='Employee', right_on='Assigned_Employee', how='left')
            if not merged.empty:
                stacked = merged.groupby(['Project_Name','Bench_Status']).size().reset_index(name='Count')
                chart4 = alt.Chart(stacked).mark_bar().encode(
                    x='Project_Name',
                    y='Count',
                    color='Bench_Status',
                    tooltip=['Project_Name','Bench_Status','Count']
                )
                st.altair_chart(chart4, use_container_width=True)

        # Data Table
        st.dataframe(df[['Employee','Dept','Bench_Status','True_Utilization']], height=300)

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
    if df_emp.empty or df_proj.empty:
        st.info("Upload Employee Activity and Project Assignment file first")
    else:
        assignments = []
        for _, emp in df_emp.iterrows():
            emp_skills = set(str(emp.get('Skills','')).split(","))
            for _, proj in df_proj.iterrows():
                proj_skills = set(str(proj.get('Required_Skills','')).split(",")) if pd.notnull(proj.get('Required_Skills')) else set()
                if emp_skills & proj_skills:
                    assignments.append({
                        'Employee': emp.get('Employee',''),
                        'Project': proj.get('Project_Name',''),
                        'Skill_Match': ", ".join(emp_skills & proj_skills)
                    })
        st.dataframe(pd.DataFrame(assignments), height=400)
