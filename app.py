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

def ai_recommendations_hr(activity_df, project_df):
    recs = []
    if activity_df.empty or project_df.empty:
        return ["Upload Employee and Project data for recommendations."]
    
    df = calculate_utilization(activity_df.copy())
    
    # Underutilized employees
    underutilized = df[df['True_Utilization'] < 50]
    for i, emp in underutilized.head(3).iterrows():
        recs.append(f"Employee {emp['Employee']} is underutilized. Consider reassigning to high-priority projects.")
    
    # Project skill gaps
    for _, proj in project_df.iterrows():
        required_skills = set(str(proj.get('Required_Skills','')).split(","))
        available_skills = set(",".join(df['Skills'].dropna()).split(","))
        missing = required_skills - available_skills
        if missing:
            recs.append(f"Project {proj['Project_Name']} lacks employees with {', '.join(missing)}. Upskill or reallocate employees.")
    
    # Bench cost optimization
    if 'Cost' in df.columns:
        bench_emps = df[df['True_Utilization']<20]
        total_saving = bench_emps['Cost'].sum() * 0.1
        recs.append(f"Reduce bench time by reassigning underutilized employees; potential savings: ${total_saving:.2f}.")
    
    return recs[:5]

def ai_recommendations_pm(pm_name, reportees_df, activity_df, project_df):
    recs = []
    if reportees_df.empty or activity_df.empty or project_df.empty:
        return ["Upload data to generate PM-specific recommendations."]
    reportee_list = reportees_df[reportees_df['Project_Manager']==pm_name]['Employee'].tolist()
    df = activity_df[activity_df['Employee'].isin(reportee_list)]
    df = calculate_utilization(df.copy())
    
    # Underutilized reportees
    underutilized = df[df['True_Utilization'] < 50]
    for i, emp in underutilized.head(3).iterrows():
        recs.append(f"Reportee {emp['Employee']} is underutilized. Assign to active projects for better productivity.")
    
    # Suggest project allocation
    for _, proj in project_df.iterrows():
        proj_emps = df[df['Skills'].apply(lambda x: bool(set(str(x).split(",")).intersection(set(str(proj.get('Required_Skills','')).split(",")))))]
        if len(proj_emps)<proj.get('Num_Employees_Required',0):
            recs.append(f"Project {proj['Project_Name']} is understaffed for required skills. Consider reallocating reportees.")
    
    # Bench optimization for PM team
    if 'Cost' in df.columns:
        bench_emps = df[df['True_Utilization']<20]
        total_saving = bench_emps['Cost'].sum() * 0.1
        recs.append(f"Optimize your reportees' bench time; potential savings: ${total_saving:.2f}.")
    
    return recs[:5]

# ---------------- Session State ----------------
if 'activity' not in st.session_state: st.session_state['activity'] = pd.DataFrame()
if 'skills' not in st.session_state: st.session_state['skills'] = pd.DataFrame()
if 'projects' not in st.session_state: st.session_state['projects'] = pd.DataFrame()
if 'reportees' not in st.session_state: st.session_state['reportees'] = pd.DataFrame()
if 'role' not in st.session_state: st.session_state['role'] = 'HR Head'

# ---------------- Sidebar ----------------
page = st.sidebar.radio(
    "Navigation",
    options=[
        "🏠 Homepage",
        "📤 Upload Data",
        "👨‍💼 Project Manager",
        "👩‍💼 HR Head"
    ]
)

# ---------------- Top Right Role Selector ----------------
with st.container():
    col1, col2 = st.columns([9,1])
    with col1:
        st.markdown("")  # placeholder for spacing
    with col2:
        selected_role = st.selectbox("Role", options=["HR Head","Project Manager"], index=["HR Head","Project Manager"].index(st.session_state['role']))
        st.session_state['role'] = selected_role

# ---------------- Pages ----------------

# ---------- Homepage ----------
if page=="🏠 Homepage":
    st.markdown("<h1 style='text-align:left'>SmartWork.AI 💡</h1>", unsafe_allow_html=True)
    st.image("logo.png", width=300)
    st.markdown("### The AI-powered tool for CHROs", unsafe_allow_html=True)
    st.markdown("""
        SmartWork.AI helps HR heads and project managers monitor employee utilization, skills, and project assignments.
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

# ---------- Project Manager ----------
elif page=="👨‍💼 Project Manager":
    st.subheader("Project Manager Dashboard 👨‍💼")
    reportees_df = st.session_state['reportees']
    df_emp = st.session_state['activity']
    df_proj = st.session_state['projects']
    
    if reportees_df.empty:
        st.info("Upload Project Manager Reportees file first")
    else:
        pm_list = reportees_df['Project_Manager'].unique().tolist()
        selected_pm = st.selectbox("Select Project Manager", pm_list)
        pm_reportees = reportees_df[reportees_df['Project_Manager']==selected_pm]['Employee'].tolist()
        st.markdown(f"### Projects for {selected_pm}")
        st.dataframe(df_proj, height=200)
        
        st.markdown(f"### Reportees for {selected_pm}")
        st.dataframe(df_emp[df_emp['Employee'].isin(pm_reportees)], height=300)
        
        st.markdown("### AI Recommendations 🤖")
        recs = ai_recommendations_pm(selected_pm, reportees_df, df_emp, df_proj)
        for i, rec in enumerate(recs,1):
            st.markdown(f"**{i}.** {rec}")

# ---------- HR Head ----------
elif page=="👩‍💼 HR Head":
    st.subheader("HR Head Dashboard 👩‍💼")
    df = calculate_utilization(st.session_state['activity'])
    proj_df = st.session_state['projects']
    
    if df.empty:
        st.info("Upload Employee Activity first")
    else:
        total_emp = len(df)
        bench_count = len(df[df['Bench_Status']=="On Bench"])
        part_util = len(df[df['Bench_Status']=="Partially Utilized"])
        full_util = len(df[df['Bench_Status']=="Fully Utilized"])
        k1,k2,k3,k4 = st.columns([1,1,1,1])
        k1.metric("Total Employees", total_emp)
        k2.metric("On Bench", bench_count)
        k3.metric("Partial Utilization", part_util)
        k4.metric("Full Utilization", full_util)

        # Bench Status Chart
        bench_chart = df['Bench_Status'].value_counts().reset_index()
        bench_chart.columns = ['Bench_Status','Count']
        chart1 = alt.Chart(bench_chart).mark_bar().encode(
            x='Bench_Status',
            y='Count',
            color='Bench_Status'
        )
        st.altair_chart(chart1, use_container_width=True)

        # Department Utilization Chart
        dept_util = df.groupby('Dept')['True_Utilization'].mean().reset_index()
        chart2 = alt.Chart(dept_util).mark_bar().encode(
            x='Dept',
            y='True_Utilization',
            color='Dept'
        )
        st.altair_chart(chart2, use_container_width=True)

        # Connected Line Chart
        line_chart = alt.Chart(df.reset_index()).mark_line(point=True).encode(
            x='index',
            y='True_Utilization',
            color='Dept',
            tooltip=['Employee','Dept','True_Utilization']
        )
        st.altair_chart(line_chart, use_container_width=True)

        # Data Table
        st.dataframe(df[['Employee','Dept','Bench_Status','True_Utilization']], height=300)

        # AI Recommendations
        st.subheader("AI Recommendations 🤖")
        recs = ai_recommendations_hr(df, proj_df)
        for i, rec in enumerate(recs,1):
            st.markdown(f"**{i}.** {rec}")

