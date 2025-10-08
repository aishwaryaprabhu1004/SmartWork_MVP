import streamlit as st
import pandas as pd
import altair as alt
import numpy as np

# ---------------- Page Config ----------------
st.set_page_config(
    page_title="SmartWork.AI",
    page_icon="💡",
    layout="wide"
)

# ---------------- Session State ----------------
for key in ['activity', 'skills', 'projects', 'reportees', 'role']:
    if key not in st.session_state:
        if key == 'role':
            st.session_state[key] = 'HR Head'
        else:
            st.session_state[key] = pd.DataFrame()

# ---------------- Custom CSS Sidebar ----------------
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
.top-right-role {
    position: fixed;
    top: 10px;
    right: 20px;
    z-index: 1000;
}
</style>
""", unsafe_allow_html=True)

# ---------------- Role Selection ----------------
roles = ['HR Head', 'Project Manager']
selected_role = st.selectbox("Select Role", roles, index=roles.index(st.session_state['role']), key='role_select', label_visibility="collapsed")
st.session_state['role'] = selected_role

# ---------------- Sidebar Pages ----------------
pages_hr = ["🏠 Homepage", "📤 Upload Data", "🏠📈 Dashboard & Analytics", "🪑 Bench Utilization", "🎯 Skill Recommendations", "🚀 Project Assignment"]
pages_pm = ["🏠 Homepage", "📤 Upload Data", "🏠📈 Dashboard & Analytics", "🪑 Bench Utilization", "🎯 Skill Recommendations", "🚀 Project Assignment"]

page_options = pages_hr if st.session_state['role']=='HR Head' else pages_pm
page = st.sidebar.radio("", options=page_options)

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

def ai_recommendations(df, cost_df=None):
    # Simple heuristic AI for illustration
    recommendations = []
    if df.empty: return ["Upload employee data to get AI recommendations."]
    underutilized = df[df['Bench_Status']!="Fully Utilized"]
    if not underutilized.empty:
        for idx, row in underutilized.iterrows():
            recommendations.append(f"Consider reassigning {row['Employee']} to high-priority projects to improve utilization.")
    if cost_df is not None and not cost_df.empty:
        high_cost_proj = cost_df.loc[cost_df['Cost'].idxmax()]['Project_Name']
        recommendations.append(f"Review cost for project {high_cost_proj}, may reduce overhead or reallocate resources.")
    if not recommendations:
        recommendations = ["All employees optimally utilized. Focus on upskilling."]
    return recommendations[:5]  # limit top 5

# ---------------- Pages ----------------

if page=="🏠 Homepage":
    st.title("💡 SmartWork.AI")
    st.image("https://i.imgur.com/3G5H4gA.png", width=150)  # Example logo
    st.write("""
    SmartWork.AI helps IT organizations maximize employee productivity,
    optimize project assignments, and provide actionable AI-driven recommendations
    for HR Heads and Project Managers.
    """)
    st.info("Use the sidebar to navigate through the application.")

elif page=="📤 Upload Data":
    st.subheader("Upload Data 📤")
    col1, col2, col3, col4 = st.columns([1,1,1,1])
    with col1:
        f1 = st.file_uploader("Employee Activity", type=["csv","xlsx"])
    with col2:
        f2 = st.file_uploader("Skill Training", type=["csv","xlsx"])
    with col3:
        f3 = st.file_uploader("Project Assignment", type=["csv","xlsx"])
    with col4:
        f4 = st.file_uploader("Reportees (PM Only)", type=["csv","xlsx"])
    submit_upload = st.button("Submit Uploads")
    if submit_upload:
        if f1: st.session_state['activity'] = load_file(f1)
        if f2: st.session_state['skills'] = load_file(f2)
        if f3: st.session_state['projects'] = load_file(f3)
        if f4: st.session_state['reportees'] = load_file(f4)
        st.success("Files uploaded successfully.")

elif page=="🏠📈 Dashboard & Analytics":
    st.subheader("Dashboard & Analytics 🏠📈")
    df = calculate_utilization(st.session_state['activity'])
    if df.empty:
        st.info("Upload Employee Activity first")
    else:
        # Role-based view
        if st.session_state['role']=="Project Manager":
            reportees_df = st.session_state['reportees']
            if not reportees_df.empty:
                df = df[df['Employee'].isin(reportees_df['Employee'].tolist())]

        total_emp = len(df)
        bench_count = len(df[df['Bench_Status']=="On Bench"])
        part_util = len(df[df['Bench_Status']=="Partially Utilized"])
        full_util = len(df[df['Bench_Status']=="Fully Utilized"])
        k1,k2,k3,k4 = st.columns([1,1,1,1])
        k1.metric("Total Employees", total_emp)
        k2.metric("On Bench", bench_count)
        k3.metric("Partial Utilization", part_util)
        k4.metric("Full Utilization", full_util)

        # Bench Status
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
            alt.Chart(dept_util).mark_bar().encode(
                x='Dept', y='True_Utilization', color='Dept'
            ), use_container_width=True
        )

        # Line chart for trends
        st.altair_chart(
            alt.Chart(df).mark_line(point=True).encode(
                x='Employee', y='True_Utilization', color='Dept'
            ), use_container_width=True
        )

        # Scatter chart: Bench Duration vs Utilization
        if 'Bench_Duration' in df.columns:
            st.altair_chart(
                alt.Chart(df).mark_circle(size=60).encode(
                    x='Bench_Duration', y='True_Utilization', color='Bench_Status',
                    tooltip=['Employee','Dept','Bench_Status','True_Utilization']
                ), use_container_width=True
            )

        # AI Recommendations for HR Head only
        if st.session_state['role']=="HR Head":
            st.subheader("AI Recommendations 🔥")
            cost_df = st.session_state.get('projects', pd.DataFrame())
            recs = ai_recommendations(df, cost_df)
            for r in recs:
                st.info(r)

elif page=="🪑 Bench Utilization":
    st.subheader("Bench Utilization 🪑")
    df = calculate_utilization(st.session_state['activity'])
    if df.empty:
        st.info("Upload Employee Activity first")
    else:
        if st.session_state['role']=="Project Manager":
            reportees_df = st.session_state['reportees']
            if not reportees_df.empty:
                df = df[df['Employee'].isin(reportees_df['Employee'].tolist())]
        st.dataframe(df[['Employee','Dept','Bench_Status','True_Utilization']], height=400)

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
            # Assign max 2 new skills
            missing = missing[:2]  
            return ", ".join(missing) if missing else "None"
        df_emp['Recommended_Skills'] = df_emp['Skills'].apply(rec)
        if st.session_state['role']=="Project Manager":
            reportees_df = st.session_state['reportees']
            if not reportees_df.empty:
                df_emp = df_emp[df_emp['Employee'].isin(reportees_df['Employee'].tolist())]
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
            emp_skills = set(str(emp.get('
