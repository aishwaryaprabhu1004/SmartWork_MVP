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
if 'selected_pm' not in st.session_state: st.session_state['selected_pm'] = None
if 'page' not in st.session_state: st.session_state['page'] = 'Homepage'

# ---------------- Helper Functions ----------------
def load_file(file):
    if file:
        try:
            if file.name.endswith(".csv"):
                return pd.read_csv(file)
            else:
                return pd.read_excel(file, engine='openpyxl')
        except Exception:
            st.error("Error reading file. Please upload CSV or XLSX.")
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

def ai_recommendations(activity_df, project_df, role='HR Head'):
    recs = []
    if activity_df.empty or project_df.empty:
        return ["Upload Employee and Project data for recommendations."]
    
    df = calculate_utilization(activity_df.copy())
    
    underutilized = df[df['True_Utilization'] < 50]
    for i, emp in underutilized.head(3).iterrows():
        recs.append(f"Employee {emp['Employee']} is underutilized. Reassignment could improve utilization by ~{round(50-emp['True_Utilization'],1)}%")
    
    for _, proj in project_df.iterrows():
        required_skills = set(str(proj.get('Required_Skills','')).split(","))
        available_skills = set(",".join(df['Skills'].dropna()).split(","))
        missing = required_skills - available_skills
        if missing:
            recs.append(f"Project {proj['Project_Name']} missing skills: {', '.join(missing)}. Upskilling could improve project delivery by 15-20%")
    
    if 'Cost' in df.columns:
        bench_emps = df[df['True_Utilization']<20]
        total_saving = bench_emps['Cost'].sum() * 0.1
        recs.append(f"Reducing bench time could save ~${total_saving:.2f}")
    
    return recs[:5]

def assign_complementary_skills(emp_df, proj_df):
    assignments = []
    if emp_df.empty or proj_df.empty:
        return pd.DataFrame()
    
    df = emp_df.copy()
    for _, proj in proj_df.iterrows():
        proj_name = proj['Project_Name']
        required_skills = proj.get('Required_Skills','').split(",")
        employees = df.sample(n=min(len(df), len(required_skills)), random_state=42)
        for idx, emp in employees.iterrows():
            skill_to_assign = required_skills[idx % len(required_skills)]
            assignments.append({
                "Employee": emp['Employee'],
                "Project": proj_name,
                "Assigned_Skill": skill_to_assign
            })
    return pd.DataFrame(assignments)

# ---------------- Sidebar ----------------
st.sidebar.image("logo.png", width=200)
st.sidebar.markdown("### Navigation")

# Top-level pages
pages = ["Homepage", "Upload Data", "Project Manager", "HR Head"]
selected_page = st.sidebar.radio("", pages)

# Role-specific features
pm_features = ["Dashboard & Analytics", "AI Recommendations", "Project Assignment"]
hr_features = ["Dashboard & Analytics", "AI Recommendations", "Skill Recommendations", "Project Assignment"]

if selected_page == "Project Manager":
    st.sidebar.markdown("Project Manager Features")
    selected_feature = st.sidebar.radio("", pm_features, key="pm_features")
elif selected_page == "HR Head":
    st.sidebar.markdown("HR Head Features")
    selected_feature = st.sidebar.radio("", hr_features, key="hr_features")
else:
    selected_feature = selected_page

# ---------------- Pages ----------------

# Homepage
if selected_feature == "Homepage":
    st.markdown("<h1>SmartWork.AI 💡</h1>", unsafe_allow_html=True)
    st.markdown("### The AI-powered tool for CHROs")
    st.markdown("""
    SmartWork.AI helps HR Heads and Project Managers monitor employee utilization, skills, and project assignments.
    Gain actionable insights and AI-based recommendations to optimize resources, reduce bench costs, and improve project delivery.
    """)

# Upload Data
elif selected_feature == "Upload Data":
    st.subheader("Upload Data 📤")
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
        f4 = st.file_uploader("Project Manager Reportees", type=["csv","xlsx"])
        if f4: st.session_state['reportees'] = load_file(f4)

# ---------------- Project Manager Pages ----------------
elif selected_page == "Project Manager":
    df = calculate_utilization(st.session_state['activity'])
    proj_df = st.session_state['projects']
    reportees_df = st.session_state['reportees']
    
    if df.empty or reportees_df.empty:
        st.info("Upload Employee Activity and Reportees first")
    else:
        pm_list = reportees_df['Project_Manager'].unique().tolist()
        selected_pm = st.selectbox("Select Project Manager", pm_list)
        reportees = reportees_df[reportees_df['Project_Manager']==selected_pm]
        df_pm = df[df['Employee'].isin(reportees['Employee'])]
        
        if selected_feature=="Dashboard & Analytics":
            st.subheader(f"{selected_pm} Dashboard")
            total_emp = len(df_pm)
            bench_count = len(df_pm[df_pm['Bench_Status']=="On Bench"])
            part_util = len(df_pm[df_pm['Bench_Status']=="Partially Utilized"])
            full_util = len(df_pm[df_pm['Bench_Status']=="Fully Utilized"])
            k1,k2,k3,k4 = st.columns([1,1,1,1])
            k1.metric("Total Employees", total_emp)
            k2.metric("On Bench", bench_count)
            k3.metric("Partial Utilization", part_util)
            k4.metric("Full Utilization", full_util)
            
            bench_chart = df_pm['Bench_Status'].value_counts().reset_index()
            bench_chart.columns = ['Bench_Status','Count']
            chart = alt.Chart(bench_chart).mark_bar().encode(
                x='Bench_Status', y='Count', color='Bench_Status'
            )
            st.altair_chart(chart, use_container_width=True)
        
        elif selected_feature=="AI Recommendations":
            st.subheader(f"{selected_pm} AI Recommendations")
            recs = ai_recommendations(df_pm, proj_df, role='Project Manager')
            for i, rec in enumerate(recs,1):
                st.markdown(f"**{i}.** {rec}")
        
        elif selected_feature=="Project Assignment":
            st.subheader(f"{selected_pm} Project Assignment")
            assignment_df = assign_complementary_skills(df_pm, proj_df)
            st.dataframe(assignment_df, height=400)

# ---------------- HR Head Pages ----------------
elif selected_page == "HR Head":
    df = calculate_utilization(st.session_state['activity'])
    proj_df = st.session_state['projects']
    df_skills = st.session_state['skills']
    
    if df.empty:
        st.info("Upload Employee Activity first")
    else:
        if selected_feature=="Dashboard & Analytics":
            st.subheader("HR Dashboard")
            total_emp = len(df)
            bench_count = len(df[df['Bench_Status']=="On Bench"])
            part_util = len(df[df['Bench_Status']=="Partially Utilized"])
            full_util = len(df[df['Bench_Status']=="Fully Utilized"])
            k1,k2,k3,k4 = st.columns([1,1,1,1])
            k1.metric("Total Employees", total_emp)
            k2.metric("On Bench", bench_count)
            k3.metric("Partial Utilization", part_util)
            k4.metric("Full Utilization", full_util)
            
            dept_util = df.groupby('Dept')['True_Utilization'].mean().reset_index()
            chart = alt.Chart(dept_util).mark_bar().encode(
                x='Dept', y='True_Utilization', color='Dept'
            )
            st.altair_chart(chart, use_container_width=True)
        
        elif selected_feature=="AI Recommendations":
            st.subheader("HR AI Recommendations")
            recs = ai_recommendations(df, proj_df, role='HR Head')
            for i, rec in enumerate(recs,1):
                st.markdown(f"**{i}.** {rec}")
        
        elif selected_feature=="Skill Recommendations":
            st.subheader("HR Skill Recommendations")
            if df_skills.empty:
                st.info("Upload Skills file first")
            else:
                top_skills = df_skills['Skill'].unique().tolist()[:2]
                def rec(skills_str):
                    emp_skills = str(skills_str).split(",") if pd.notnull(skills_str) else []
                    missing = list(set(top_skills)-set(emp_skills))
                    return ", ".join(missing) if missing else "None"
                df['Recommended_Skills'] = df['Skills'].apply(rec)
                st.dataframe(df[['Employee','Skills','Recommended_Skills','Bench_Status']], height=400)
        
        elif selected_feature=="Project Assignment":
            st.subheader("HR Project Assignment")
            assignment_df = assign_complementary_skills(df, proj_df)
            st.dataframe(assignment_df, height=400)














