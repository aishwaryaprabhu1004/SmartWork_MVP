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

def ai_recommendations(df, proj_df, role="HR Head"):
    recs = []
    if df.empty or proj_df.empty:
        return ["Upload Employee and Project data for recommendations."]

    df = calculate_utilization(df.copy())

    # ---------------- HR Head Recommendations ----------------
    if role=="HR Head":
        # 1. Underutilized employees
        underutilized = df[df['True_Utilization'] < 50]
        for i, emp in underutilized.head(3).iterrows():
            recs.append(f"Employee {emp['Employee']} is underutilized. Reassigning can improve utilization by ~{round(100-emp['True_Utilization'],1)}%")

        # 2. Project skill gaps
        for _, proj in proj_df.iterrows():
            required_skills = set(str(proj.get('Required_Skills','')).split(","))
            available_skills = set(",".join(df['Skills'].dropna()).split(","))
            missing = required_skills - available_skills
            if missing:
                recs.append(f"Project {proj['Project_Name']} lacks {', '.join(missing)}. Upskilling/reallocation may improve delivery by ~10%")

        # 3. Bench cost optimization
        if 'Cost' in df.columns:
            bench_emps = df[df['True_Utilization']<20]
            total_saving = bench_emps['Cost'].sum() * 0.1
            recs.append(f"Reducing bench time could save ${total_saving:.2f} (~10% of bench costs).")
    
    # ---------------- Project Manager Recommendations ----------------
    if role=="Project Manager":
        # Check reportee utilization
        underutilized = df[df['True_Utilization']<50]
        for i, emp in underutilized.iterrows():
            recs.append(f"Reportee {emp['Employee']} is underutilized. Assigning to your projects can improve project delivery ~{round(100-emp['True_Utilization'],1)}%")

        # Skill match recommendations
        for _, proj in proj_df.iterrows():
            required_skills = set(str(proj.get('Required_Skills','')).split(","))
            for _, emp in df.iterrows():
                emp_skills = set(str(emp.get('Skills','')).split(","))
                missing = required_skills - emp_skills
                if missing:
                    recs.append(f"Upskill {emp['Employee']} with {', '.join(missing)} for project {proj['Project_Name']}")
    
    return recs[:5]

# ---------------- Sidebar ----------------
st.sidebar.title("SmartWork.AI 💡")
sidebar_page = st.sidebar.radio(
    "Navigation",
    ["🏠 Homepage","📤 Upload Data","Roles & Recommendations"]
)

# ---------------- Session State ----------------
if 'activity' not in st.session_state: st.session_state['activity'] = pd.DataFrame()
if 'skills' not in st.session_state: st.session_state['skills'] = pd.DataFrame()
if 'projects' not in st.session_state: st.session_state['projects'] = pd.DataFrame()
if 'reportees' not in st.session_state: st.session_state['reportees'] = pd.DataFrame()
if 'role_page' not in st.session_state: st.session_state['role_page'] = 'HR Head'

# ---------------- Homepage ----------------
if sidebar_page=="🏠 Homepage":
    st.image("logo.png", width=300)
    st.markdown("<h1 style='text-align:left'>SmartWork.AI</h1>", unsafe_allow_html=True)
    st.markdown("### The AI-powered tool for CHROs", unsafe_allow_html=True)
    st.markdown("""
    SmartWork.AI helps HR heads and project managers monitor employee utilization, skills, and project assignments.
    Gain actionable insights and AI-based recommendations to optimize resources, reduce bench costs, and improve project delivery.
    """, unsafe_allow_html=True)

# ---------------- Upload Data ----------------
elif sidebar_page=="📤 Upload Data":
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

# ---------------- Roles & Recommendations ----------------
elif sidebar_page=="Roles & Recommendations":
    role_option = st.selectbox("Select Role", ["HR Head","Project Manager"], index=["HR Head","Project Manager"].index(st.session_state['role_page']))
    st.session_state['role_page'] = role_option

    if role_option=="HR Head":
        st.subheader("HR Head Dashboard & Analytics")
        df = calculate_utilization(st.session_state['activity'])
        proj_df = st.session_state['projects']

        if df.empty:
            st.info("Upload Employee Activity first")
        else:
            # Metrics
            total_emp = len(df)
            bench_count = len(df[df['Bench_Status']=="On Bench"])
            part_util = len(df[df['Bench_Status']=="Partially Utilized"])
            full_util = len(df[df['Bench_Status']=="Fully Utilized"])
            c1,c2,c3,c4 = st.columns(4)
            c1.metric("Total Employees", total_emp)
            c2.metric("On Bench", bench_count)
            c3.metric("Partial Utilization", part_util)
            c4.metric("Full Utilization", full_util)

            # Dept avg utilization
            dept_util = df.groupby('Dept')['True_Utilization'].mean().reset_index()
            chart1 = alt.Chart(dept_util).mark_bar().encode(
                x='Dept', y='True_Utilization', color='Dept'
            )
            st.altair_chart(chart1, use_container_width=True)

            # Connected line chart
            df_trend = df.groupby(['Dept','Employee']).agg({'True_Utilization':'mean'}).reset_index()
            line_chart = alt.Chart(df_trend).mark_line(point=True).encode(
                x='Employee', y='True_Utilization', color='Dept', tooltip=['Employee','Dept','True_Utilization']
            )
            st.altair_chart(line_chart, use_container_width=True)

            # Top 2 Skill Recommendations
            df_skills = st.session_state['skills']
            if not df_skills.empty:
                def top_skills(emp_skills):
                    emp_skills_set = set(str(emp_skills).split(",") if pd.notnull(emp_skills) else [])
                    all_skills = df_skills['Skill'].dropna().unique().tolist()
                    missing_skills = [s for s in all_skills if s not in emp_skills_set]
                    return ", ".join(missing_skills[:2]) if missing_skills else "None"
                df['Recommended_Skills'] = df['Skills'].apply(top_skills)
                st.dataframe(df[['Employee','Skills','Recommended_Skills','Bench_Status']], height=300)
            
            # AI Recommendations
            st.subheader("AI Recommendations 🤖")
            recs = ai_recommendations(df, proj_df, role="HR Head")
            for i, rec in enumerate(recs,1):
                st.markdown(f"**{i}.** {rec}")

    elif role_option=="Project Manager":
        st.subheader("Project Manager Dashboard & Analytics")
        df = calculate_utilization(st.session_state['activity'])
        proj_df = st.session_state['projects']
        reportees_df = st.session_state['reportees']

        if df.empty or proj_df.empty:
            st.info("Upload Employee Activity, Project Assignment, and Reportees files first")
        else:
            # Filter only reportees
            if not reportees_df.empty:
                df = df[df['Employee'].isin(reportees_df['Employee'])]
            
            # Metrics
            total_emp = len(df)
            bench_count = len(df[df['Bench_Status']=="On Bench"])
            part_util = len(df[df['Bench_Status']=="Partially Utilized"])
            full_util = len(df[df['Bench_Status']=="Fully Utilized"])
            c1,c2,c3,c4 = st.columns(4)
            c1.metric("Total Reportees", total_emp)
            c2.metric("On Bench", bench_count)
            c3.metric("Partial Utilization", part_util)
            c4.metric("Full Utilization", full_util)

            # Dept avg utilization
            dept_util = df.groupby('Dept')['True_Utilization'].mean().reset_index()
            chart1 = alt.Chart(dept_util).mark_bar().encode(
                x='Dept', y='True_Utilization', color='Dept'
            )
            st.altair_chart(chart1, use_container_width=True)

            # Connected line chart
            df_trend = df.groupby(['Dept','Employee']).agg({'True_Utilization':'mean'}).reset_index()
            line_chart = alt.Chart(df_trend).mark_line(point=True).encode(
                x='Employee', y='True_Utilization', color='Dept', tooltip=['Employee','Dept','True_Utilization']
            )
            st.altair_chart(line_chart, use_container_width=True)

            # AI Recommendations
            st.subheader("AI Recommendations 🤖")
            recs = ai_recommendations(df, proj_df, role="Project Manager")
            for i, rec in enumerate(recs,1):
                st.markdown(f"**{i}.** {rec}")



