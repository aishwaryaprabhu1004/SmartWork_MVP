# ---------------- Sidebar Navigation ----------------
page = st.sidebar.radio(
    "Navigation",
    options=[
        "🏠 Dashboard & Analytics",
        "🪑 Bench Utilization",
        "🎯 Skill Recommendations",
        "🚀 Project Assignment",
        "📤 Upload Data"
    ]
)

# ---------------- Role Selection ----------------
role = st.sidebar.selectbox("Select Your Role", ["HR Head", "Project Manager"])

# ---------------- Project Manager reportee upload ----------------
if role == "Project Manager":
    reportees_file = st.sidebar.file_uploader("Upload Your Reportees", type=["csv","xlsx"])
    reportees_list = []
    if reportees_file:
        try:
            if reportees_file.name.endswith(".csv"):
                reportees_list = pd.read_csv(reportees_file)['Employee'].tolist()
            else:
                reportees_list = pd.read_excel(reportees_file, engine='openpyxl')['Employee'].tolist()
        except Exception as e:
            st.sidebar.error(f"Error reading reportees file: {e}")

# ---------------- Dashboard & Analytics ----------------
elif page=="🏠 Dashboard & Analytics":
    st.subheader("Dashboard & Analytics 🏠📈")
    df = calculate_utilization(st.session_state['activity'])
    if df.empty:
        st.info("Upload Employee Activity first")
    else:
        # Filter for PM role
        if role == "Project Manager" and reportees_list:
            df = df[df['Employee'].isin(reportees_list)]

        # ---------------- AI Recommendations ----------------
        recommendations = []
        if role == "HR Head":
            if df['Bench_Status'].value_counts().get("On Bench",0) > 0:
                recommendations.append("Some employees are on bench. Consider reassigning or reskilling them.")
            if df['True_Utilization'].mean() < 50:
                recommendations.append("Overall utilization is low. Identify underperforming departments.")
        elif role == "Project Manager":
            low_util = df[df['True_Utilization'] < 50]
            if not low_util.empty:
                recommendations.append(f"{len(low_util)} of your reportees are underutilized. Consider reskilling or reassigning.")

        if recommendations:
            st.markdown("### ⚡ Quick Recommendations")
            for r in recommendations:
                st.info(r)

        # ---------------- KPI Cards ----------------
        total_emp = len(df)
        bench_count = len(df[df['Bench_Status']=="On Bench"])
        part_util = len(df[df['Bench_Status']=="Partially Utilized"])
        full_util = len(df[df['Bench_Status']=="Fully Utilized"])
        k1,k2,k3,k4 = st.columns([1,1,1,1])
        k1.metric("Total Employees", total_emp)
        k2.metric("On Bench", bench_count)
        k3.metric("Partial Utilization", part_util)
        k4.metric("Full Utilization", full_util)

        # ---------------- Line Graph with connected points ----------------
        if 'Dept' in df.columns:
            dept_util = df.groupby('Dept')['True_Utilization'].mean().reset_index()
            chart_line = alt.Chart(dept_util).mark_line(point=True).encode(
                x='Dept',
                y='True_Utilization',
                color='Dept'
            )
            st.altair_chart(chart_line, use_container_width=True)
