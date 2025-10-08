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
if 'page' not in st.session_state: st.session_state['page'] = None

# ---------------- Helper Functions ----------------
def load_file(file):
    if file:
        if file.name.endswith(".csv"):
            return pd.read_csv(file)
        else:
            st.error("Upload CSV files only.")
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
    df['True_Utilization'] = (df['Activity_Score'] / df['Activity_Score'].max()) * 100
    df['Bench_Status'] = df['True_Utilization'].apply(
        lambda x: "On Bench" if x<20 else ("Partially Utilized" if x<50 else "Fully Utilized")
    )
    return df

# ---------------- Top-right Role Selector ----------------
col1, col2 = st.columns([8,1])
with col2:
    selected_role = st.selectbox("Role", ["HR Head","Project Manager"], index=0, key="role")
st.session_state['role'] = selected_role

# ---------------- Sidebar ----------------
sidebar_options_hr = ["🏠 Dashboard & Analytics","🪑 Bench Utilization","🎯 Skill Recommendations","🚀 Project Assignment","📤 Upload Data"]
sidebar_options_pm = ["🏠 Dashboard & Analytics","🚀 Project Assignment","📤 Upload Data"]

if st.session_state['role']=="HR Head":
    st.session_state['page'] = st.sidebar.radio("Navigation", sidebar_options_hr)
else:
    st.session_state['page'] = st.sidebar.radio("Navigation", sidebar_options_pm)

# ---------------- Homepage ----------------
if st.session_state['page'] is None:
    st.title("SmartWork.AI")
    st.image("logo.png", width=120)  # Add professional logo in your repo
    st.write("Welcome to SmartWork.AI – Optimize employee utilization, projects, and skills effortlessly.")

# ---------------- File Upload Section ----------------
if st.session_state['page']=="📤 Upload Data":
    st.subheader("Upload Data")
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

# ---------------- Dashboard & Analytics (combined) ----------------
if st.session_state['page']=="🏠 Dashboard & Analytics":
    st.subheader("Dashboard & Analytics")
    df_emp = calculate_utilization(st.session_state['activity'])
    df_proj = st.session_state['projects']
    df_costs = st.session_state['costs']
    if df_emp.empty:
        st.info("Upload Employee Activity first")
    else:
        # Display metrics
        total_emp = len(df_emp)
        bench_count = len(df_emp[df_emp['Bench_Status']=="On Bench"])
        part_util = len(df_emp[df_emp['Bench_Status']=="Partially Utilized"])
        full_util = len(df_emp[df_emp['Bench_Status']=="Fully Utilized"])
        k1,k2,k3,k4 = st.columns(4)
        k1.metric("Total Employees", total_emp)
        k2.metric("On Bench", bench_count)
        k3.metric("Partial Utilization", part_util)
        k4.metric("Full Utilization", full_util)

        # Charts
        # Bench Status
        bench_chart = df_emp['Bench_Status'].value_counts().reset_index()
        bench_chart.columns = ['Bench_Status','Count']
        st.altair_chart(alt.Chart(bench_chart).mark_bar().encode(
            x='Bench_Status', y='Count', color='Bench_Status'
        ), use_container_width=True)

        # Dept Utilization
        dept_util = df_emp.groupby('Dept')['True_Utilization'].mean().reset_index()
        st.altair_chart(alt.Chart(dept_util).mark_line(point=True).encode(
            x='Dept', y='True_Utilization', color='Dept'
        ), use_container_width=True)

        # Cost per Dept
        if not df_costs.empty:
            dept_cost = df_emp.merge(df_costs, on='Employee', how='left').groupby('Dept')['Cost'].sum().reset_index()
            st.altair_chart(alt.Chart(dept_cost).mark_arc().encode(
                theta='Cost', color='Dept'
            ), use_container_width=True)

        # AI Recommendations (HR Head only)
        if st.session_state['role']=="HR Head":
            st.subheader("💡 AI Recommendations")
            # Call the AI logic function
            # recommendations = generate_ai_recommendations(...) # Implement AI logic
            st.info("AI-driven cost optimization and skill recommendations here.")

# ---------------- Other pages: Bench Utilization, Skills, Project Assignment ----------------
# Implement similarly using st.session_state['role'] to show relevant content




