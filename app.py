import streamlit as st
import pandas as pd
import altair as alt

# ---------------- Page Config ----------------
st.set_page_config(
    page_title="SmartWork.AI",
    page_icon="💡",
    layout="wide"
)

# ---------------- Increase Upload Limit ----------------
st.set_option('server.maxUploadSize', 512)  # in MB

# ---------------- Custom Sidebar ----------------
st.markdown("""
<style>
/* Make sidebar wider */
[data-testid="stSidebar"] {
    width: 250px;
}

/* Big icons, centered */
.sidebar .sidebar-content {
    display: flex;
    flex-direction: column;
    align-items: center;
}
.sidebar .sidebar-content div[role="radiogroup"] > label {
    font-size: 22px;
    padding: 15px 0;
}
</style>
""", unsafe_allow_html=True)

# ---------------- Sidebar Icons ----------------
page = st.sidebar.radio(
    "Navigation",
    options=[
        "🏠 Dashboard",
        "🪑 Bench Utilization",
        "🎯 Skill Recommendations",
        "🚀 Project Assignment",
        "📤 Upload Data",
        "📈 Analytics"
    ]
)

# ---------------- Session State ----------------
if 'activity' not in st.session_state: st.session_state['activity'] = pd.DataFrame()
if 'skills' not in st.session_state: st.session_state['skills'] = pd.DataFrame()
if 'projects' not in st.session_state: st.session_state['projects'] = pd.DataFrame()

# ---------------- Helper Functions ----------------
def load_file(file):
    if not file:
        return pd.DataFrame()
    try:
        if file.name.endswith(".csv"):
            return pd.read_csv(file)
        else:
            return pd.read_excel(file, engine='openpyxl')
    except Exception as e:
        st.error(f"File loading failed: {e}")
        return pd.DataFrame()

def calculate_utilization(df):
    if df.empty:
        return df
    # AI: Rule-based heuristic scoring
    df['Activity_Score'] = (
        0.4*df.get('Tasks_Completed',0) +
        0.3*df.get('Meetings_Duration',0) +
        0.2*df.get('Decisions_Made',0) +
        0.1*df.get('Docs_Updated',0)
    )
    # Manual normalization
    df['True_Utilization'] = (df['Activity_Score'] / df['Activity_Score'].max()) * 100
    df['Bench_Status'] = df['True_Utilization'].apply(
        lambda x: "On Bench" if x<20 else ("Partially Utilized" if x<50 else "Fully Utilized")
    )
    return df

# ---------------- Pages ----------------
if page=="📤 Upload Data":
    st.subheader("Upload Data 📤")
    col

