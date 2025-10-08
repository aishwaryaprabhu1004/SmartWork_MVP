import streamlit as st
import pandas as pd
import altair as alt

# ---------------- Page Config ----------------
st.set_page_config(
    page_title="SmartWork.AI",
    page_icon="💡",
    layout="wide"
)

st.title("SmartWork.AI MVP")

# ---------------- Sidebar ----------------
page = st.sidebar.radio(
    "Navigation",
    options=[
        "🏠 Dashboard",
        "📤 Upload Data"
    ]
)

# ---------------- Session State ----------------
if 'activity' not in st.session_state:
    st.session_state['activity'] = pd.DataFrame()

# ---------------- Helper Functions ----------------
def load_file(file):
    if file:
        return pd.read_csv(file) if file.name.endswith(".csv") else pd.read_excel(file)
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
    df['True_Utilization'] = (df['Activity_Score']/df['Activity_Score'].max())*100
    df['Bench_Status'] = df['True_Utilization'].apply(
        lambda x: "On Bench" if x<20 else ("Partially Utilized" if x<50 else "Fully Utilized")
    )
    return df

# ---------------- Pages ----------------
if page == "📤 Upload Data":
    st.subheader("Upload Data 📤")
    uploaded_file = st.file_uploader("Upload Employee Activity CSV/XLSX", type=["csv","xlsx"])
    if uploaded_file:
        st.session_state['activity'] = load_file(uploaded_file)
        st.success("File uploaded successfully!")

elif page == "🏠 Dashboard":
    st.subheader("Dashboard 🏠")
    df = calculate_utilization(st.session_state['activity'])
    if df.empty:
        st.info("Upload Employee Activity first")
    else:
        # KPI metrics
        total_emp = len(df)
        bench_count = len(df[df['Bench_Status']=="On Bench"])
        part_util = len(df[df['Bench_Status']=="Partially Utilized"])
        full_util = len(df[df['Bench_Status']=="Fully Utilized"])

        k1,k2,k3,k4 = st.columns(4)
        k1.metric("Total Employees", total_emp)
        k2.metric("On Bench", bench_count)
        k3.metric("Partial Utilization", part_util)
        k4.metric("Full Utilization", full_util)

        # Bench Status chart using Altair
        bench_chart_data = df['Bench_Status'].value_counts().reset_index()
        bench_chart_data.columns = ['Bench_Status', 'Count']
        chart = alt.Chart(bench_chart_data).mark_bar().encode(
            x='Bench_Status',
            y='Count',
            color='Bench_Status'
        ).properties(width=400, height=300)
        st.altair_chart(chart, use_container_width=True)

        # Table
        st.dataframe(df[['Employee','Dept','Bench_Status','True_Utilization']], height=300)
