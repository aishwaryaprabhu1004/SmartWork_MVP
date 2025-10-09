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

# AI Recommendations for HR Head
def ai_recommendations_hr(activity_df, project_df):
    recs = []
    if activity_df.empty or project_df.empty:
        return ["Upload Employee and Project data for recommendations."]
    
    df = calculate_utilization(activity_df.copy())
    
    # Underutilized employees
    underutilized = df[df['True_Utilization'] < 50]
    for i, emp in underutilized.head(3).iterrows():
        impact = 50 - emp['True_Utilization']
        recs.append(f"Employee {emp['Employee']} is underutilized. Assigning to projects could increase utilization by ~{impact:.1f}%")
    
    # Project skill gaps
    for _, proj in project_df.iterrows():
        required_skills = set(str(proj.get('Required_Skills','')).split(","))
        available_skills = set(",".join(df['Skills'].dropna()).split(","))
        missing = required_skills - available_skills
        if missing:
            recs.append(f"Project {proj['Project_Name']} lacks skills: {', '.join(missing)}. Upskilling employees may improve project delivery by ~15%")
    
    # Bench cost optimization
    if 'Cost' in df.columns:
        bench_emps = df[df['True_Utilization']<20]
        total_saving = bench_emps['Cost'].sum() * 0.1
        recs.append(f"Reducing bench time can save ~${total_saving:.2f}, potentially improving revenue by 5-10%")
    
    return recs[:5]

# AI Recommendations for Project Manager
def ai_recommendations_pm(pm_name, reportees_df, activity_df, project_df):
    recs = []
    if reportees_df.empty or activity_df.empty or project_df.empty:
        return ["Upload data to generate PM-specific recommendations."]
    
    pm_reportees = reportees_df[reportees_df['Project_Manager']==pm_name]['Employee'].tolist()
    df = activity_df[activity_df['Employee'].isin(pm_reportees)]
    df = calculate_utilization(df.copy())
    
    underutilized = df[df['True_Utilization'] < 50]
    for i, emp in underutilized.head(3).iterrows():
        impact = 50 - emp['True_Utilization']
        recs.append(f"Reportee {emp['Employee']} is underutilized. Assigning them can boost team utilization by ~{impact:.1f}%")
    
    for _, proj in project_df.iterrows():
        proj_emps = df[df['Skills'].apply(lambda x: bool(set(str(x).split(",")).intersection(set(str(proj.get('Required_Skills','')).split(",")))))]
        if len(proj_emps)<proj.get('Num_Employees_Required',0):
            recs.append(f"Project {proj['Project_Name']} is understaffed. Allocating reportees could increase project efficiency by ~10-15%")
    
    if 'Cost' in df.columns:
        bench_emps = df[df['True_Utilization']<20]
        total_saving = bench_emps['Cost'].sum() * 0.1
        recs.append(f"Optimizing reportees' bench time can save ~${total_saving:.2f}, improving team productivity")
    
    return recs[:5]

# ---------------- Session State ----------------
if 'activity' not in st.session_state: st.session_state['activity'] = pd.DataFrame()
if 'skills' not in st.session_state: st.session_state['skills'] = pd.DataFrame()
if 'projects' not in st.session_state: st.session_state['projects'] = pd.DataFrame()
if 'reportees' not in st.session_state: st.session_state['reportees'] = pd.DataFrame()

# ---------------- Sidebar ----------------
st.sidebar.markdown("### Roles & Features")

page_options = [
    "🏠 Homepage",
    "📤 Upload Data",
    "👨‍💼 Project Manager Dashboard",
    "👨‍💼 Project Manager Reportees",
    "👨‍💼 Project Manager AI Recommendations",
    "👩‍💼 HR Head Dashboard & Analytics",
    "👩‍💼 HR Head Skill Recommendations",
    "👩‍💼 HR Head Project Assignment",
    "👩‍💼 HR Head AI Recommendations"
]

page = st.sidebar.radio("", options=page_options, index=0)

# ---------------- Pages ----------------
# ---------- Homepage ----------
if page=="🏠 Homepage":
    st.markdown("<h1 style='text-align:left'>SmartWork.AI 💡</h1>", unsafe_allow_html=True)
    st.image("logo.png", width=300)
    st.markdown("### The AI-powered tool for CHROs", unsafe_allow_html=True)
    st.markdown("""
        SmartWork.AI helps HR heads and project managers monitor **employee utilization, skills, and project assignments**.
        Gain actionable insights and AI-based recommendations to optimize resources, reduce bench costs, and improve project delivery.
    """, unsafe_allow_html=True)

# ---------- Upload Data ----------
elif page=="📤 Upload Data":
    st.subheader("Upload Data 📤")
    col1, col2, col3, col4 = st.columns([1,1,1,1])
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

# ---------- Project Manager Dashboard ----------
elif page=="👨‍💼 Project Manager Dashboard":
    st.subheader("Project Manager Dashboard 👨‍💼")
    reportees_df = st.session_state['reportees']
    df_emp = st.session_state['activity']
    if reportees_df.empty or df_emp.empty:
        st.info("Upload required files first")
    else:
        pm_list = reportees_df['Project_Manager'].unique().tolist()
        selected_pm = st.selectbox("Select Project Manager", pm_list)
        pm_reportees = reportees_df[reportees_df['Project_Manager']==selected_pm]['Employee'].tolist()
        df_pm = df_emp[df_emp['Employee'].isin(pm_reportees)]
        df_pm = calculate_utilization(df_pm)
        
        # Utilization metrics
        total_emp = len(df_pm)
        bench_count = len(df_pm[df_pm['Bench_Status']=="On Bench"])
        part_util = len(df_pm[df_pm['Bench_Status']=="Partially Utilized"])
        full_util = len(df_pm[df_pm['Bench_Status']=="Fully Utilized"])
        k1,k2,k3,k4 = st.columns([1,1,1,1])
        k1.metric("Total Employees", total_emp)
        k2.metric("On Bench", bench_count)
        k3.metric("Partial Utilization", part_util)
        k4.metric("Full Utilization", full_util)

        # Connected Line Chart for reportees utilization
        line_chart = alt.Chart(df_pm.reset_index()).mark_line(point=True).encode(
            x='index',
            y='True_Utilization',
            color='Dept',
            tooltip=['Employee','Dept','True_Utilization']
        )
        st.altair_chart(line_chart, use_container_width=True)

        st.dataframe(df_pm[['Employee','Dept','Bench_Status','True_Utilization']], height=300)

# ---------- Project Manager Reportees ----------
elif page=="👨‍💼 Project Manager Reportees":
    st.subheader("Project Manager Reportees")
    reportees_df = st.session_state['reportees']
    df_emp = st.session_state['activity']
    if reportees_df.empty or df_emp.empty:
        st.info("Upload required files first")
    else:
        pm_list = reportees_df['Project_Manager'].unique().tolist()
        selected_pm = st.selectbox("Select Project Manager", pm_list)
        pm_reportees = reportees_df[reportees_df['Project_Manager']==selected_pm]['Employee'].tolist()
        df_pm = df_emp[df_emp['Employee'].isin(pm_reportees)]
        st.dataframe(df_pm[['Employee','Dept','Skills']], height=400)

# ---------- Project Manager AI Recommendations ----------
elif page=="👨‍💼 Project Manager AI Recommendations":
    st.subheader("Project Manager AI Recommendations")
    reportees_df = st.session_state['reportees']
    df_emp = st.session_state['activity']
    df_proj = st.session_state['projects']
    if reportees_df.empty or df_emp.empty or df_proj.empty:
        st.info("Upload required files first")
    else:
        pm_list = reportees_df['Project_Manager'].unique().tolist()
        selected_pm = st.selectbox("Select Project Manager", pm_list)
        recs = ai_recommendations_pm(selected_pm, reportees_df, df_emp, df_proj)
        for i, rec in enumerate(recs,1):
            st.markdown(f"**{i}.** {rec}")

# ---------- HR Head Dashboard & Analytics ----------
elif page=="👩‍💼 HR Head Dashboard & Analytics":
    st.subheader("HR Head Dashboard & Analytics 👩‍💼")
    df_emp = calculate_utilization(st.session_state['activity'])
    if df_emp.empty:
        st.info("Upload Employee Activity first")
    else:
        dept_avg = df_emp.groupby('Dept')['True_Utilization'].mean().reset_index()
        line_chart = alt.Chart(dept_avg.reset_index()).mark_line(point=True).encode(
            x='Dept',
            y='True_Utilization',
            tooltip=['Dept','True_Utilization']
        )
        st.altair_chart(line_chart, use_container_width=True)
        st.dataframe(dept_avg, height=300)

# ---------- HR Head Skill Recommendations ----------
elif page=="👩‍💼 HR Head Skill Recommendations":
    st.subheader("HR Head Skill Recommendations")
    df_emp = st.session_state['activity']
    df_skills = st.session_state['skills']
    df_proj = st.session_state['projects']
    if df_emp.empty or df_skills.empty or df_proj.empty:
        st.info("Upload all required files first")
    else:
        # Assign top 2 relevant skills per employee considering project skill needs
        required_skills = set()
        for _, proj in df_proj.iterrows():
            skills = str(proj.get('Required_Skills','')).split(",")
            required_skills.update(skills)
        required_skills = list(required_skills)

        def rec(skills_str):
            emp_skills = set(str(skills_str).split(",")) if pd.notnull(skills_str) else set()
            missing = list(set(required_skills) - emp_skills)
            return ", ".join(missing[:2]) if missing else "None"
        
        df_emp['Recommended_Skills'] = df_emp['Skills'].apply(rec)
        st.dataframe(df_emp[['Employee','Skills','Recommended_Skills','Bench_Status']], height=400)

# ---------- HR Head Project Assignment ----------
elif page=="👩‍💼 HR Head Project Assignment":
    st.subheader("HR Head Project Assignment")
    df_emp = st.session_state['activity']
    df_proj = st.session_state['projects']
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

# ---------- HR Head AI Recommendations ----------
elif page=="👩‍💼 HR Head AI Recommendations":
    st.subheader("HR Head AI Recommendations")
    df_emp = st.session_state['activity']
    df_proj = st.session_state['projects']
    if df_emp.empty or df_proj.empty:
        st.info("Upload Employee Activity and Project Assignment file first")
    else:
        recs = ai_recommendations_hr(df_emp, df_proj)
        for i, rec in enumerate(recs,1):
            st.markdown(f"**{i}.** {rec}")






