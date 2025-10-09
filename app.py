import streamlit as st
import pandas as pd
import altair as alt

# ---------------- Page Config ----------------
st.set_page_config(
    page_title="SmartWork.AI",
    page_icon="💡",
    layout="wide"
)

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

def ai_recommendations(activity_df, project_df, role="HR Head"):
    recs = []
    if activity_df.empty or project_df.empty:
        return ["Upload Employee and Project data for recommendations."]
    
    df = calculate_utilization(activity_df.copy())
    
    # Underutilized employees
    underutilized = df[df['True_Utilization'] < 50]
    for i, emp in underutilized.head(3).iterrows():
        improvement = round(100 - emp['True_Utilization'],2)
        recs.append(f"Employee {emp['Employee']} is underutilized. Reassigning could improve utilization by ~{improvement}%.")
    
    # Project skill gaps
    for _, proj in project_df.iterrows():
        required_skills = set(str(proj.get('Required_Skills','')).split(","))
        available_skills = set(",".join(df['Skills'].dropna()).split(","))
        missing = required_skills - available_skills
        if missing:
            recs.append(f"Project {proj['Project_Name']} lacks employees with {', '.join(missing)}. Upskilling can improve project delivery by ~10%.")
    
    # Bench cost optimization
    if 'Cost' in df.columns:
        bench_emps = df[df['True_Utilization']<20]
        total_saving = bench_emps['Cost'].sum() * 0.1
        recs.append(f"Reducing bench time for underutilized employees can save ~${total_saving:.2f}.")
    
    return recs[:5]

def assign_complementary_skills(df_emp, df_proj):
    if df_emp.empty or df_proj.empty:
        return pd.DataFrame()
    df_emp = df_emp.copy()
    project_skills = {}
    for _, proj in df_proj.iterrows():
        project_skills[proj['Project_Name']] = set(str(proj.get('Required_Skills','')).split(","))
    assignments = []
    for _, emp in df_emp.iterrows():
        emp_skills = set(str(emp.get('Skills','')).split(","))
        for proj_name, skills in project_skills.items():
            available_skills = skills - emp_skills
            if available_skills:
                assigned_skill = list(available_skills)[0]
                emp_skills.add(assigned_skill)
        assignments.append({
            'Employee': emp['Employee'],
            'Skills_Assigned': ", ".join(emp_skills)
        })
    return pd.DataFrame(assignments)

# ---------------- Session State ----------------
if 'activity' not in st.session_state: st.session_state['activity'] = pd.DataFrame()
if 'skills' not in st.session_state: st.session_state['skills'] = pd.DataFrame()
if 'projects' not in st.session_state: st.session_state['projects'] = pd.DataFrame()
if 'reportees' not in st.session_state: st.session_state['reportees'] = pd.DataFrame()
if 'selected_pm' not in st.session_state: st.session_state['selected_pm'] = None

# ---------------- Sidebar ----------------
st.sidebar.title("Navigation")
sidebar_pages = ["Homepage","Upload Data","Project Manager","HR Head"]
page_selection = st.sidebar.radio("", sidebar_pages)

# ---------- Homepage ----------
if page_selection=="Homepage":
    st.image("logo.png", width=250)
    st.markdown("<h1>SmartWork.AI 💡</h1>", unsafe_allow_html=True)
    st.markdown("### AI-powered tool for CHROs")
    st.markdown("""
        SmartWork.AI helps HR heads and Project Managers monitor employee utilization, skills, and project assignments.
        Gain actionable insights and AI-based recommendations to optimize resources, reduce bench costs, and improve project delivery.
    """)

# ---------- Upload Data ----------
elif page_selection=="Upload Data":
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

# ---------- Project Manager ----------
elif page_selection=="Project Manager":
    st.subheader("Project Manager Dashboard")
    df_pm = st.session_state['reportees']
    if df_pm.empty:
        st.info("Upload Project Manager Reportees data first.")
    else:
        pm_list = df_pm['Project_Manager'].unique().tolist()
        selected_pm = st.selectbox("Select Project Manager", pm_list)
        st.session_state['selected_pm'] = selected_pm
        reportees_df = df_pm[df_pm['Project_Manager']==selected_pm]
        emp_df = st.session_state['activity']
        if not emp_df.empty:
            pm_emp = emp_df[emp_df['Employee'].isin(reportees_df['Employee'])]
            df = calculate_utilization(pm_emp)
            
            # Metrics
            k1,k2,k3,k4 = st.columns(4)
            k1.metric("Total Employees", len(df))
            k2.metric("On Bench", len(df[df['Bench_Status']=="On Bench"]))
            k3.metric("Partial Utilization", len(df[df['Bench_Status']=="Partially Utilized"]))
            k4.metric("Full Utilization", len(df[df['Bench_Status']=="Fully Utilized"]))
            
            # Line chart per employee utilization
            line_chart = alt.Chart(df.reset_index()).mark_line(point=True).encode(
                x='index',
                y='True_Utilization',
                color='Employee',
                tooltip=['Employee','Dept','True_Utilization']
            )
            st.altair_chart(line_chart, use_container_width=True)
            
            # Data Table
            st.dataframe(df[['Employee','Dept','Bench_Status','True_Utilization']], height=300)
            
            # AI Recommendations
            st.subheader("AI Recommendations 🤖")
            recs = ai_recommendations(df, st.session_state['projects'], role="Project Manager")
            for i, rec in enumerate(recs,1):
                st.markdown(f"**{i}.** {rec}")

# ---------- HR Head ----------
elif page_selection=="HR Head":
    st.subheader("HR Head Dashboard")
    df_hr = st.session_state['activity']
    proj_df = st.session_state['projects']
    if df_hr.empty:
        st.info("Upload Employee Activity first")
    else:
        df = calculate_utilization(df_hr)
        
        # Metrics
        k1,k2,k3,k4 = st.columns(4)
        k1.metric("Total Employees", len(df))
        k2.metric("On Bench", len(df[df['Bench_Status']=="On Bench"]))
        k3.metric("Partial Utilization", len(df[df['Bench_Status']=="Partially Utilized"]))
        k4.metric("Full Utilization", len(df[df['Bench_Status']=="Fully Utilized"]))
        
        # Dept-wise average utilization
        dept_util = df.groupby('Dept')['True_Utilization'].mean().reset_index()
        chart1 = alt.Chart(dept_util).mark_bar().encode(
            x='Dept',
            y='True_Utilization',
            color='Dept'
        )
        st.altair_chart(chart1, use_container_width=True)
        
        # AI Recommendations
        st.subheader("AI Recommendations 🤖")
        recs = ai_recommendations(df, proj_df, role="HR Head")
        for i, rec in enumerate(recs,1):
            st.markdown(f"**{i}.** {rec}")
        
        # Skill Recommendations
        st.subheader("Skill Recommendations 🎯")
        df_skills = st.session_state['skills']
        if df_skills.empty:
            st.info("Upload Skills file first")
        else:
            top_skills = df_skills['Skill'].value_counts().head(2).index.tolist()
            def rec(emp_skills):
                emp_skills_set = set(str(emp_skills).split(",")) if pd.notnull(emp_skills) else set()
                missing = list(set(top_skills) - emp_skills_set)
                return ", ".join(missing) if missing else "None"
            df['Recommended_Skills'] = df['Skills'].apply(rec)
            st.dataframe(df[['Employee','Skills','Recommended_Skills','Bench_Status']], height=400)
        
        # Project Assignment with complementary skills
        st.subheader("Project Assignment 🚀")
        assigned_skills_df = assign_complementary_skills(df, proj_df)
        st.dataframe(assigned_skills_df, height=400)








