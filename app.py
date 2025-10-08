import streamlit as st
import pandas as pd
import plotly.express as px

# -------------------- Page Config --------------------
st.set_page_config(page_title="SmartWork.AI", layout="wide")
st.title("💡 SmartWork.AI — Bench & Utilization Intelligence Platform")

# -------------------- Session State for Uploaded Files --------------------
if 'activity' not in st.session_state:
    st.session_state['activity'] = pd.DataFrame()
if 'skills' not in st.session_state:
    st.session_state['skills'] = pd.DataFrame()
if 'projects' not in st.session_state:
    st.session_state['projects'] = pd.DataFrame()

# -------------------- Helper Functions --------------------
def load_file(file):
    if file is not None:
        if file.name.endswith(".csv"):
            return pd.read_csv(file)
        else:
            return pd.read_excel(file)
    return pd.DataFrame()

def process_utilization(df):
    df['Effective_Meeting_Hours'] = df['Meetings_Duration']*0.8 + df['Decisions_Made']*0.2
    df['Activity_Score'] = (
        0.35*df['Tasks_Completed'] +
        0.25*df['Effective_Meeting_Hours'] +
        0.2*df['Docs_Updated'] +
        0.2*df['Decisions_Made']
    )
    df['True_Utilization'] = (df['Activity_Score']/df['Activity_Score'].max())*100
    df['Bench_Status'] = df['True_Utilization'].apply(lambda x: "On Bench" if x<20 else ("Partially Utilized" if x<50 else "Fully Utilized"))
    return df

def recommend_skills(df_emp, df_skills):
    high_demand_skills = df_skills['Skill'].tolist()
    def rec(skills_str):
        emp_skills = [s.strip() for s in str(skills_str).split(",")]
        missing = list(set(high_demand_skills)-set(emp_skills))
        return ", ".join(missing) if missing else "None"
    df_emp['Recommended_Skills'] = df_emp['Skills'].apply(rec)
    return df_emp

def assign_projects(df_emp, df_proj):
    assignments = []
    for idx, emp in df_emp.iterrows():
        emp_skills = set(str(emp['Skills']).split(","))
        for _, proj in df_proj.iterrows():
            proj_skills = set(str(proj['Required_Skills']).split(","))
            if emp_skills & proj_skills:
                assignments.append({
                    'Employee': emp['Employee'],
                    'Project': proj['Project_Name'],
                    'Skill_Match': ", ".join(emp_skills & proj_skills)
                })
    return pd.DataFrame(assignments)

# -------------------- Sidebar Navigation --------------------
page = st.sidebar.selectbox("Navigate", ["Upload Data", "Dashboard", "Bench Utilization", "Skill Recommendations", "Project Assignment", "Analytics"])

# -------------------- Page: Upload Data --------------------
if page=="Upload Data":
    st.header("📤 Upload Excel / CSV Files")
    
    activity_file = st.file_uploader("Employee Activity", type=["csv","xlsx"])
    skills_file = st.file_uploader("Skill Training Requirements", type=["csv","xlsx"])
    projects_file = st.file_uploader("Project Assignment Requirements", type=["csv","xlsx"])
    
    if activity_file:
        st.session_state['activity'] = load_file(activity_file)
        st.success("Employee Activity uploaded!")
    if skills_file:
        st.session_state['skills'] = load_file(skills_file)
        st.success("Skill Training uploaded!")
    if projects_file:
        st.session_state['projects'] = load_file(projects_file)
        st.success("Project Assignments uploaded!")

# -------------------- Page: Dashboard --------------------
elif page=="Dashboard":
    st.header("📊 SmartWork.AI Dashboard Overview")
    df_activity = st.session_state['activity']
    if not df_activity.empty:
        df_activity = process_utilization(df_activity)
        st.subheader("Bench Status Distribution")
        bench_chart = df_activity['Bench_Status'].value_counts().reset_index()
        bench_chart.columns = ['Bench Status','Count']
        fig = px.bar(bench_chart, x='Bench Status', y='Count', color='Bench Status')
        st.plotly_chart(fig)
        st.subheader("Employee Utilization Table")
        st.dataframe(df_activity[['Employee','Dept','Bench_Status','True_Utilization','Bench_Duration']])
    else:
        st.info("Upload Employee Activity first.")

# -------------------- Page: Bench Utilization --------------------
elif page=="Bench Utilization":
    st.header("🪑 Bench Identification & True Utilization")
    df_activity = st.session_state['activity']
    if not df_activity.empty:
        df_activity = process_utilization(df_activity)
        st.dataframe(df_activity[['Employee','Dept','Bench_Status','True_Utilization','Bench_Duration']])
    else:
        st.info("Upload Employee Activity first.")

# -------------------- Page: Skill Recommendations --------------------
elif page=="Skill Recommendations":
    st.header("🎯 Skill Training Recommendations")
    df_activity = st.session_state['activity']
    df_skills = st.session_state['skills']
    if not df_activity.empty and not df_skills.empty:
        df_activity = recommend_skills(df_activity, df_skills)
        st.dataframe(df_activity[['Employee','Skills','Recommended_Skills','Bench_Status']])
    else:
        st.info("Upload Employee Activity and Skill Training data first.")

# -------------------- Page: Project Assignment --------------------
elif page=="Project Assignment":
    st.header("🚀 Project Assignment Suggestions")
    df_activity = st.session_state['activity']
    df_projects = st.session_state['projects']
    if not df_activity.empty and not df_projects.empty:
        df_assignments = assign_projects(df_activity, df_projects)
        if not df_assignments.empty:
            st.dataframe(df_assignments)
        else:
            st.info("No project matches found.")
    else:
        st.info("Upload Employee Activity and Project Assignment data first.")

# -------------------- Page: Analytics --------------------
elif page=="Analytics":
    st.header("📈 Analytics & Insights")
    df_activity = st.session_state['activity']
    if not df_activity.empty:
        df_activity = process_utilization(df_activity)
        st.subheader("Bench vs Utilization")
        fig = px.scatter(df_activity, x='Bench_Duration', y='True_Utilization', color='Bench_Status', hover_data=['Employee'])
        st.plotly_chart(fig)
        st.subheader("Department-wise Utilization")
        dept_chart = df_activity.groupby('Dept')['True_Utilization'].mean().reset_index()
        fig2 = px.bar(dept_chart, x='Dept', y='True_Utilization', color='Dept')
        st.plotly_chart(fig2)
    else:
        st.info("Upload Employee Activity first.")
