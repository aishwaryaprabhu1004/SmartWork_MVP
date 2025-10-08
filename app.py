import streamlit as st
import pandas as pd
import altair as alt
import io
import tempfile
import os
import importlib.util

st.set_page_config(page_title="SmartWork.AI", page_icon="💡", layout="wide")

# Sidebar
page = st.sidebar.radio(
    "Navigation",
    options=[
        "🏠 Dashboard",
        "📤 Upload Data",
        "🪑 Bench Utilization",
        "🎯 Skill Recommendations",
        "🚀 Project Assignment",
        "📈 Analytics"
    ]
)

# Ensure session data
if 'activity' not in st.session_state:
    st.session_state['activity'] = pd.DataFrame()
if 'skills' not in st.session_state:
    st.session_state['skills'] = pd.DataFrame()
if 'projects' not in st.session_state:
    st.session_state['projects'] = pd.DataFrame()

# ✅ Universal Safe Loader
def load_file(file):
    if not file:
        return pd.DataFrame()
    try:
        if file.name.endswith(".csv"):
            return pd.read_csv(file)
        elif file.name.endswith((".xls", ".xlsx")):
            # Write to temp file to ensure openpyxl can read it
            with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
                tmp.write(file.read())
                tmp_path = tmp.name
            try:
                return pd.read_excel(tmp_path, engine="openpyxl")
            except Exception as e:
                st.warning(f"openpyxl failed, fallback mode: {e}")
                try:
                    return pd.read_excel(tmp_path, engine="xlrd")
                except:
                    st.error("Unable to read Excel file. Please upload as CSV instead.")
                    return pd.DataFrame()
            finally:
                os.remove(tmp_path)
        else:
            st.error("Unsupported file format.")
            return pd.DataFrame()
    except Exception as e:
        st.error(f"Error reading file: {e}")
        return pd.DataFrame()

# ✅ AI Logic
def calculate_utilization(df):
    if df.empty:
        return df
    df['Activity_Score'] = (
        0.4 * df.get('Tasks_Completed', 0) +
        0.3 * df.get('Meetings_Duration', 0) +
        0.2 * df.get('Decisions_Made', 0) +
        0.1 * df.get('Docs_Updated', 0)
    )
    df['True_Utilization'] = (df['Activity_Score'] / df['Activity_Score'].max()) * 100
    df['Bench_Status'] = df['True_Utilization'].apply(
        lambda x: "On Bench" if x < 20 else ("Partially Utilized" if x < 50 else "Fully Utilized")
    )
    return df

# ✅ Upload Page
if page == "📤 Upload Data":
    st.header("📤 Upload Data")
    c1, c2, c3 = st.columns(3)
    with c1:
        f1 = st.file_uploader("Employee Activity (.csv or .xlsx)", type=["csv", "xlsx"])
        if f1:
            st.session_state['activity'] = load_file(f1)
    with c2:
        f2 = st.file_uploader("Skill Training (.csv or .xlsx)", type=["csv", "xlsx"])
        if f2:
            st.session_state['skills'] = load_file(f2)
    with c3:
        f3 = st.file_uploader("Project Assignment (.csv or .xlsx)", type=["csv", "xlsx"])
        if f3:
            st.session_state['projects'] = load_file(f3)

# ✅ Dashboard Page
elif page == "🏠 Dashboard":
    st.header("🏠 Dashboard")
    df = calculate_utilization(st.session_state['activity'])
    if df.empty:
        st.info("Upload Employee Activity first.")
    else:
        total = len(df)
        on_bench = len(df[df['Bench_Status'] == "On Bench"])
        partial = len(df[df['Bench_Status'] == "Partially Utilized"])
        full = len(df[df['Bench_Status'] == "Fully Utilized"])

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Employees", total)
        c2.metric("On Bench", on_bench)
        c3.metric("Partially Utilized", partial)
        c4.metric("Fully Utilized", full)

        bench_chart = df['Bench_Status'].value_counts().reset_index()
        bench_chart.columns = ['Bench_Status', 'Count']
        st.altair_chart(
            alt.Chart(bench_chart).mark_bar().encode(
                x='Bench_Status',
                y='Count',
                color='Bench_Status'
            ), use_container_width=True
        )

        st.dataframe(df[['Employee', 'Dept', 'Bench_Status', 'True_Utilization']], height=400)

# ✅ Other Pages
elif page == "🪑 Bench Utilization":
    df = calculate_utilization(st.session_state['activity'])
    if df.empty:
        st.info("Upload Employee Activity first.")
    else:
        st.dataframe(df[['Employee', 'Dept', 'Bench_Status', 'True_Utilization']], height=400)

elif page == "🎯 Skill Recommendations":
    df_emp = st.session_state['activity']
    df_skills = st.session_state['skills']
    if df_emp.empty or df_skills.empty:
        st.info("Upload Employee Activity and Skills data first.")
    else:
        req_skills = df_skills['Skill'].unique().tolist()
        df_emp['Recommended_Skills'] = df_emp['Skills'].apply(
            lambda s: ", ".join(set(req_skills) - set(str(s).split(","))) if pd.notnull(s) else ", ".join(req_skills)
        )
        st.dataframe(df_emp[['Employee', 'Skills', 'Recommended_Skills']], height=400)

elif page == "🚀 Project Assignment":
    df_emp = st.session_state['activity']
    df_proj = st.session_state['projects']
    if df_emp.empty or df_proj.empty:
        st.info("Upload both Employee Activity and Project Assignment.")
    else:
        assign = []
        for _, e in df_emp.iterrows():
            e_skills = set(str(e.get('Skills', '')).split(","))
            for _, p in df_proj.iterrows():
                p_skills = set(str(p.get('Required_Skills', '')).split(","))
                if e_skills & p_skills:
                    assign.append({
                        'Employee': e.get('Employee', ''),
                        'Project': p.get('Project_Name', ''),
                        'Skill_Match': ", ".join(e_skills & p_skills)
                    })
        st.dataframe(pd.DataFrame(assign), height=400)

elif page == "📈 Analytics":
    df = calculate_utilization(st.session_state['activity'])
    if df.empty:
        st.info("Upload Employee Activity first.")
    else:
        if 'Bench_Duration' in df.columns:
            scatter = alt.Chart(df).mark_circle(size=60).encode(
                x='Bench_Duration', y='True_Utilization', color='Bench_Status'
            )
            st.altair_chart(scatter, use_container_width=True)
