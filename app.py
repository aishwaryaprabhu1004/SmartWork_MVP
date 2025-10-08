import streamlit as st
import pandas as pd
import altair as alt

# ---------------- Page Config ----------------
st.set_page_config(
    page_title="SmartWork.AI",
    page_icon="💡",
    layout="wide"
)

# ---------------- Role Selection ----------------
if 'role' not in st.session_state:
    st.session_state['role'] = None

if st.session_state['role'] is None:
    st.title("Welcome to SmartWork.AI")
    role = st.radio("Select Your Role:", ["HR Head", "Project Manager"])
    if st.button("Proceed"):
        st.session_state['role'] = role
    st.stop()  # Stop app until role is selected

role = st.session_state['role']

# ---------------- Session State ----------------
if 'activity' not in st.session_state: st.session_state['activity'] = pd.DataFrame()
if 'skills' not in st.session_state: st.session_state['skills'] = pd.DataFrame()
if 'projects' not in st.session_state: st.session_state['projects'] = pd.DataFrame()
if 'reportees' not in st.session_state: st.session_state['reportees'] = pd.DataFrame()

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

def ai_recommendations(df, role):
    if df.empty:
        return []
    recs = []
    if role=="HR Head":
        low_util = df[df['True_Utilization']<50]
        for _, row in low_util.iterrows():
            recs.append(f"Upskill {row['Employee']} in missing skills to improve billing.")
    elif role=="Project Manager":
        low_util = df[df['True_Utilization']<50]
        for _, row in low_util.iterrows():
            recs.append(f"Assign tasks matching {row['Employee']}'s skills to increase project output.")
    return recs

# ---------------- Sidebar Pages ----------------
available_pages = ["🏠 Dashboard & Analytics", "🪑 Bench Utilization", "🎯 Skill Recommendations", "🚀 Project Assignment", "📤 Upload Data"]

if role=="Project Manager":
    # PMs can't upload all files except reportees
    available_pages = ["🏠 Dashboard & Analytics", "🪑 Bench Utilization", "🎯 Skill Recommendations", "🚀 Project Assignment", "📤 Upload Reportees"]

page = st.sidebar.radio("Navigation", options=available_pages)

# ---------------- Pages ----------------
if page=="📤 Upload Data" or page=="📤 Upload Reportees":
    st.subheader("Upload Data 📤")
    with st.form("upload_form"):
        if role=="HR Head":
            f1 = st.file_uploader("Employee Activity", type=["csv","xlsx"])
            f2 = st.file_uploader("Skill Training", type=["csv","xlsx"])
            f3 = st.file_uploader("Project Assignment", type=["csv","xlsx"])
            f4 = st.file_uploader("Reportees Mapping (for PM)", type=["csv","xlsx"])
        else:
            f4 = st.file_uploader("Reportees Mapping", type=["csv","xlsx"])
        submitted = st.form_submit_button("Submit")
        if submitted:
            if role=="HR Head":
                if f1: st.session_state['activity'] = load_file(f1)
                if f2: st.session_state['skills'] = load_file(f2)
                if f3: st.session_state['projects'] = load_file(f3)
                if f4: st.session_state['reportees'] = load_file(f4)
            else:
                if f4: st.session_state['reportees'] = load_file(f4)
            st.success("Files uploaded successfully!")

elif page=="🏠 Dashboard & Analytics":
    st.subheader("Dashboard & Analytics 🏠📈")
    df = calculate_utilization(st.session_state['activity'])
    reportees_df = st.session_state['reportees']

    if role=="Project Manager" and not reportees_df.empty:
        pm_name = st.selectbox("Select Your Name:", reportees_df['PM_Name'].unique())
        emp_list = reportees_df[reportees_df['PM_Name']==pm_name]['Employee'].tolist()
        df = df[df['Employee'].isin(emp_list)]

    if df.empty:
        st.info("Upload relevant data first")
    else:
        # Metrics
        total_emp = len(df)
        bench_count = len(df[df['Bench_Status']=="On Bench"])
        part_util = len(df[df['Bench_Status']=="Partially Utilized"])
        full_util = len(df[df['Bench_Status']=="Fully Utilized"])
        k1,k2,k3,k4 = st.columns([1,1,1,1])
        k1.metric("Total Employees", total_emp)
        k2.metric("On Bench", bench_count)
        k3.metric("Partial Utilization", part_util)
        k4.metric("Full Utilization", full_util)

        # Bench Bar Chart
        bench_chart = df['Bench_Status'].value_counts().reset_index()
        bench_chart.columns = ['Bench_Status','Count']
        st.altair_chart(
            alt.Chart(bench_chart).mark_bar().encode(
                x='Bench_Status', y='Count', color='Bench_Status'
            ),
            use_container_width=True
        )

        # Dept Util Line Chart
        dept_util = df.groupby('Dept')['True_Utilization'].mean().reset_index()
        st.altair_chart(
            alt.Chart(dept_util).mark_line(point=True).encode(
                x='Dept', y='True_Utilization', color='Dept'
            ),
            use_container_width=True
        )

        # Scatter Chart
        if 'Bench_Duration' in df.columns:
            st.altair_chart(
                alt.Chart(df).mark_circle(size=60).encode(
                    x='Bench_Duration', y='True_Utilization', color='Bench_Status',
                    tooltip=['Employee','Dept','Bench_Status','True_Utilization']
                ),
                use_container_width=True
            )

        # AI Recommendations
        recs = ai_recommendations(df, role)
        if recs:
            st.subheader("AI-based Recommendations")
            for r in recs[:10]:
                st.write("•", r)

        st.dataframe(df[['Employee','Dept','Bench_Status','True_Utilization']], height=400)

# Other pages (Bench Utilization, Skill Recommendations, Project Assignment) remain same as before.
