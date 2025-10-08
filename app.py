import streamlit as st
import pandas as pd

# ---------------- Page Config ----------------
st.set_page_config(page_title="SmartWork.AI", layout="wide")
st.title("💡 SmartWork.AI — AI-Driven Bench & Utilization Platform")

# ---------------- Session State ----------------
if 'activity' not in st.session_state:
    st.session_state['activity'] = pd.DataFrame()
if 'skills' not in st.session_state:
    st.session_state['skills'] = pd.DataFrame()
if 'projects' not in st.session_state:
    st.session_state['projects'] = pd.DataFrame()

# ---------------- Helper Functions ----------------
def load_file(file):
    if file is not None:
        if file.name.endswith(".csv"):
            return pd.read_csv(file)
        else:
            return pd.read_excel(file)
    return pd.DataFrame()

def calculate_utilization(df):
    if df.empty:
        return df
    # AI-like scoring
    df['Activity_Score'] = (
        0.4 * df.get('Tasks_Completed',0) +
        0.3 * df.get('Meetings_Duration',0) +
        0.2 * df.get('Decisions_Made',0) +
        0.1 * df.get('Docs_Updated',0)
    )
    df['True_Utilization'] = (df['Activity_Score'] / df['Activity_Score'].max())*100
    df['Bench_Status'] = df['True_Utilization'].apply(
        lambda x: "On Bench" if x<20 else ("Partially Utilized" if x<50 else "Fully Utilized")
    )
    return df

def recommend_skills(df_emp, df_skills):
    if df_emp.empty or df_skills.empty:
        return df_emp
    required_skills = df_skills['Skill'].unique().tolist()
    def rec(skills_str):
        emp_skills = str(skills_str).split(",") if pd.notnull(skills_str) else []
        missing = list(set(required_skills) - set(emp_skills))
        return ", ".join(missing) if missing else "None"
    df_emp['Recommended_Skills'] = df_emp['Skills'].apply(rec)
    return df_emp

def assign_projects(df_emp, df_proj):
    if df_emp.empty or df_proj.empty:
        return pd.DataFrame()
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
    return pd.DataFrame(assignments)

# ---------------- Lazy Import for Plotly ----------------
def plot_bar_chart(df, x_col, y_col, color_col):
    import plotly.express as px
    fig = px.bar(df, x=x_col, y=y_col, color=color_col)
    return fig

def plot_scatter_chart(df, x_col, y_col, color_col):
    import plotly.express as px
    fig = px.scatter(df, x=x_col, y=y_col, color=color_col, hover_data=['Employee'])
    return fig

# ---------------- Sidebar Navigation ----------------
page = st.sidebar.selectbox("Navigate", [
    "Upload Data", "Dashboard", "Bench Utilization", 
    "Skill Recommendations", "Project Assignment", "Analytics"
])

# ---------------- Pages ----------------
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

elif page=="Dashboard":
    st.header("📊 SmartWork.AI Dashboard")
    df = calculate_utilization(st.session_state['activity'])
    if not df.empty:
        bench_count = df['Bench_Status'].value_counts().reset_index()
        bench_count.columns = ['Bench Status', 'Count']
        st.plotly_chart(plot_bar_chart(bench_count, 'Bench Status', 'Count', 'Bench Status'))
        st.dataframe(df[['Employee','Dept','Bench_Status','True_Utilization']])
    else:
        st.info("Upload Employee Activity first.")

elif page=="Bench Utilization":
    st.header("🪑 Bench Identification & True Utilization")
    df = calculate_utilization(st.session_state['activity'])
    if not df.empty:
        st.dataframe(df[['Employee','Dept','Bench_Status','True_Utilization']])
    else:
        st.info("Upload Employee Activity first.")

elif page=="Skill Recommendations":
    st.header("🎯 Skill Training Recommendations")
    df = recommend_skills(st.session_state['activity'], st.session_state['skills'])
    if not df.empty:
        st.dataframe(df[['Employee','Skills','Recommended_Skills','Bench_Status']])
    else:
        st.info("Upload Employee Activity and Skill Training data first.")

elif page=="Project Assignment":
    st.header("🚀 Project Assignment Suggestions")
    df = assign_projects(st.session_state['activity'], st.session_state['projects'])
    if not df.empty:
        st.dataframe(df)
    else:
        st.info("Upload Employee Activity and Project Assignment data first.")

elif page=="Analytics":
    st.header("📈 Analytics & Insights")
    df = calculate_utilization(st.session_state['activity'])
    if not df.empty:
        st.plotly_chart(plot_scatter_chart(df, 'Bench_Duration', 'True_Utilization', 'Bench_Status'))
        dept_util = df.groupby('Dept')['True_Utilization'].mean().reset_index()
        st.plotly_chart(plot_bar_chart(dept_util, 'Dept','True_Utilization','Dept'))
    else:
        st.info("Upload Employee Activity first.")
