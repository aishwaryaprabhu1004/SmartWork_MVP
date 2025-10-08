import streamlit as st
import pandas as pd
import altair as alt

# ---------------- Page Config ----------------
st.set_page_config(page_title="SmartWork.AI", page_icon="💡", layout="wide")

# ---------------- Session State ----------------
if 'activity' not in st.session_state: st.session_state['activity'] = pd.DataFrame()
if 'skills' not in st.session_state: st.session_state['skills'] = pd.DataFrame()
if 'projects' not in st.session_state: st.session_state['projects'] = pd.DataFrame()
if 'costs' not in st.session_state: st.session_state['costs'] = pd.DataFrame()
if 'role' not in st.session_state: st.session_state['role'] = 'HR Head'

# ---------------- Helper Functions ----------------
def load_file(file):
    if file:
        try:
            if file.name.endswith(".csv"):
                return pd.read_csv(file)
            else:
                st.error("Please upload CSV file for compatibility.")
                return pd.DataFrame()
        except Exception as e:
            st.error(f"File load error: {e}")
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

def generate_ai_recommendations(df_activity, df_costs, df_projects):
    """AI recommendations for HR Head."""
    if df_activity.empty or df_costs.empty:
        return ["Upload activity and costs data to generate recommendations"]
    
    df = df_activity.copy()
    if 'Employee' not in df.columns or 'Employee' not in df_costs.columns:
        return ["Employee column missing in data."]
    
    df = pd.merge(df, df_costs[['Employee','Cost']], on='Employee', how='left')
    df['Cost_per_Utilization'] = df['Cost'] / (df['True_Utilization'] + 1e-5)
    
    # Rank employees by cost per utilization
    df_sorted = df.sort_values(by='Cost_per_Utilization', ascending=False)
    
    recommendations = []
    
    # Top 3 high-cost low-utilization employees
    high_cost_low_util = df_sorted[df_sorted['True_Utilization']<50].head(3)
    for idx, row in high_cost_low_util.iterrows():
        recommendations.append(
            f"Consider reassigning or upskilling {row['Employee']} (Cost per Utilization: {row['Cost_per_Utilization']:.2f})"
        )
    
    # Check project skill matches
    if not df_projects.empty:
        for _, proj in df_projects.iterrows():
            required_skills = set(str(proj.get('Required_Skills','')).split(","))
            for _, emp in df.iterrows():
                emp_skills = set(str(emp.get('Skills','')).split(","))
                missing = required_skills - emp_skills
                if len(missing)/len(required_skills) > 0.5:
                    recommendations.append(
                        f"Consider training {emp['Employee']} on skills {', '.join(missing)} for project {proj['Project_Name']}"
                    )
    if not recommendations:
        recommendations.append("No immediate recommendations. Team is optimized.")
    
    return recommendations

# ---------------- File Upload Section ----------------
st.title("SmartWork.AI Data Upload 📤")
col1, col2, col3, col4 = st.columns(4)

with col1:
    f1 = st.file_uploader("Employee Activity CSV", type=["csv"])
with col2:
    f2 = st.file_uploader("Skill Training CSV", type=["csv"])
with col3:
    f3 = st.file_uploader("Project Assignment CSV", type=["csv"])
with col4:
    f4 = st.file_uploader("Employee Costs CSV", type=["csv"])

if st.button("Submit Files"):
    if f1: st.session_state['activity'] = load_file(f1)
    if f2: st.session_state['skills'] = load_file(f2)
    if f3: st.session_state['projects'] = load_file(f3)
    if f4: st.session_state['costs'] = load_file(f4)
    st.success("Files uploaded successfully!")

# ---------------- Role Selection ----------------
role = st.selectbox("Select Role", ["HR Head","Project Manager"], index=0, key="role")

# ---------------- Sidebar ----------------
page = st.sidebar.radio(
    "",
    options=[
        "🏠 Dashboard & Analytics",
        "🪑 Bench Utilization",
        "🎯 Skill Recommendations",
        "🚀 Project Assignment"
    ]
)

# ---------------- Pages ----------------
df_emp = calculate_utilization(st.session_state['activity'])
df_skills = st.session_state['skills']
df_proj = st.session_state['projects']
df_costs = st.session_state['costs']

if page=="🏠 Dashboard & Analytics":
    st.subheader("Dashboard & Analytics 🏠📈")
    if df_emp.empty:
        st.info("Upload Employee Activity first")
    else:
        total_emp = len(df_emp)
        bench_count = len(df_emp[df_emp['Bench_Status']=="On Bench"])
        part_util = len(df_emp[df_emp['Bench_Status']=="Partially Utilized"])
        full_util = len(df_emp[df_emp['Bench_Status']=="Fully Utilized"])
        k1,k2,k3,k4 = st.columns(4)
        k1.metric("Total Employees", total_emp)
        k2.metric("On Bench", bench_count)
        k3.metric("Partial Utilization", part_util)
        k4.metric("Full Utilization", full_util)

        # Bench Status Bar
        bench_chart = df_emp['Bench_Status'].value_counts().reset_index()
        bench_chart.columns = ['Bench_Status','Count']
        st.altair_chart(
            alt.Chart(bench_chart).mark_bar().encode(
                x='Bench_Status',
                y='Count',
                color='Bench_Status'
            ), use_container_width=True
        )

        # Dept Utilization Line Chart
        dept_util = df_emp.groupby('Dept')['True_Utilization'].mean().reset_index()
        st.altair_chart(
            alt.Chart(dept_util).mark_line(point=True).encode(
                x='Dept',
                y='True_Utilization',
                color='Dept'
            ), use_container_width=True
        )

        # Cost per Dept Pie Chart
        if not df_costs.empty:
            dept_cost = df_emp.merge(df_costs, on='Employee', how='left').groupby('Dept')['Cost'].sum().reset_index()
            st.altair_chart(
                alt.Chart(dept_cost).mark_arc().encode(
                    theta='Cost',
                    color='Dept'
                ), use_container_width=True
            )

        st.dataframe(df_emp[['Employee','Dept','Bench_Status','True_Utilization']], height=300)

        # AI Recommendations (HR Head only)
        if role=="HR Head":
            st.subheader("💡 AI Recommendations")
            recommendations = generate_ai_recommendations(df_emp, df_costs, df_proj)
            for rec in recommendations:
                st.info(rec)

elif page=="🪑 Bench Utilization":
    st.subheader("Bench Utilization 🪑")
    if df_emp.empty:
        st.info("Upload Employee Activity first")
    else:
        st.dataframe(df_emp[['Employee','Dept','Bench_Status','True_Utilization']], height=400)

elif page=="🎯 Skill Recommendations":
    st.subheader("Skill Recommendations 🎯")
    if df_emp.empty or df_skills.empty:
        st.info("Upload Employee Activity and Skills first")
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
    if df_emp.empty or df_proj.empty:
        st.info("Upload Employee Activity and Project Assignment first")
    else:
        assignments = []
        if role=="Project Manager":
            st.subheader("Viewing your reportees")
            pm_file = st.file_uploader("Upload your reportees CSV (Employee,Project)", type=["csv"])
            if pm_file:
                pm_df = load_file(pm_file)
                df_proj = df_proj[df_proj['Assigned_Employee'].isin(pm_df['Employee'])]
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



