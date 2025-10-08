import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
from io import BytesIO

st.set_page_config(page_title="SmartWork.AI", page_icon="💡", layout="wide")

REQUIRED_EMP = ["Employee","Dept","Tasks_Completed","Meetings_Duration","Decisions_Made","Docs_Updated","Skills","Cost"]
REQUIRED_PROJ = ["Project_Name","Required_Skills","Num_Employees_Required"]
REQUIRED_REP  = ["Project_Manager","Employee"]

def load_file(file):
    if not file: return pd.DataFrame()
    try:
        if file.name.lower().endswith(".csv"):
            return pd.read_csv(file)
        return pd.read_excel(file, engine="openpyxl")
    except Exception:
        return pd.DataFrame()

def validate(df, cols):
    return all(c in df.columns for c in cols)

def norm_skill_set(s):
    if pd.isna(s): return set()
    return {x.strip().lower() for x in str(s).replace(";", ",").split(",") if x.strip()}

def utilization(df):
    if df.empty: return df
    df = df.copy()
    for c in ["Tasks_Completed","Meetings_Duration","Decisions_Made","Docs_Updated"]:
        if c not in df: df[c] = 0
    score = (0.4*df["Tasks_Completed"] + 0.3*df["Meetings_Duration"] +
             0.2*df["Decisions_Made"] + 0.1*df["Docs_Updated"]).fillna(0)
    scale = np.percentile(score, 95) if score.max() > 0 else 0
    util = (score/scale*100).clip(0,100) if scale>0 else 0
    df["Activity_Score"] = score.round(1)
    df["True_Utilization"] = util.round(1)
    df["Bench_Status"] = np.select(
        [df["True_Utilization"]<20, df["True_Utilization"]<50],
        ["On Bench","Partially Utilized"], default="Fully Utilized"
    )
    return df

def assign_projects(emp_df, proj_df, threshold=50):
    if emp_df.empty or proj_df.empty: return pd.DataFrame(), pd.DataFrame()
    e = emp_df.copy()
    e["skills_norm"] = e["Skills"].apply(norm_skill_set)
    p = proj_df.copy()
    p["req_skills_norm"] = p["Required_Skills"].apply(norm_skill_set)

    pool = e[(e["Bench_Status"]=="On Bench") | (e["True_Utilization"]<threshold)].copy()
    pool["assigned"] = False

    out, gaps = [], []
    for _, pr in p.iterrows():
        need = int(pr["Num_Employees_Required"])
        if need <= 0: continue
        req = pr["req_skills_norm"]
        cand = pool[~pool["assigned"]].copy()
        if cand.empty:
            gaps.append({"Project_Name": pr["Project_Name"], "Unfilled_Positions": need, "Reason":"No candidates"})
            continue

        scores = []
        for idx, r in cand.iterrows():
            ov = r["skills_norm"].intersection(req)
            scores.append((idx, ov, len(ov), r["True_Utilization"], r.get("Cost", 0)))
        # sort by overlap desc, util asc, cost asc
        scores.sort(key=lambda t: (-t[2], t[3], t[4]))

        filled = 0
        for idx, ov, _, _, _ in scores:
            if len(ov)==0 or pool.at[idx,"assigned"]: continue
            out.append({
                "Project_Name": pr["Project_Name"],
                "Employee": pool.at[idx,"Employee"],
                "Dept": pool.at[idx,"Dept"],
                "Bench_Status": pool.at[idx,"Bench_Status"],
                "True_Utilization": pool.at[idx,"True_Utilization"],
                "Skill_Match": ", ".join(sorted(ov))
            })
            pool.at[idx,"assigned"] = True
            filled += 1
            if filled >= need: break

        if filled < need:
            gaps.append({"Project_Name": pr["Project_Name"], "Unfilled_Positions": need-filled,
                         "Reason":"Insufficient skill-aligned underutilized/bench candidates"})
    return pd.DataFrame(out), pd.DataFrame(gaps)

def download_csv(df, name):
    if df.empty: return
    buf = BytesIO(); df.to_csv(buf, index=False); buf.seek(0)
    st.download_button(f"Download {name}", buf, file_name=name, mime="text/csv")

# state
if "activity" not in st.session_state: st.session_state["activity"]=pd.DataFrame()
if "skills"   not in st.session_state: st.session_state["skills"]=pd.DataFrame()
if "projects" not in st.session_state: st.session_state["projects"]=pd.DataFrame()
if "reportees"not in st.session_state: st.session_state["reportees"]=pd.DataFrame()
if "role"     not in st.session_state: st.session_state["role"]="HR Head"

# top bar
c1, c2 = st.columns([8,2])
with c1: st.markdown("## SmartWork.AI")
with c2:
    st.selectbox("Role", ["HR Head","Project Manager"],
                 index=["HR Head","Project Manager"].index(st.session_state["role"]),
                 key="role")

page = st.sidebar.radio("Navigation", ["Homepage","Upload Data","Dashboard","Skill Recommendations","Project Assignment"])

if page=="Homepage":
    st.markdown("Minimal, fast, and role-aware workforce intelligence.")

elif page=="Upload Data":
    col1,col2,col3,col4 = st.columns(4)
    with col1:
        f = st.file_uploader("Employee Activity", type=["csv","xlsx"])
        if f:
            df = load_file(f)
            if validate(df, REQUIRED_EMP): st.session_state["activity"]=df; st.success("Loaded")
            else: st.error(f"Missing columns: {set(REQUIRED_EMP)-set(df.columns)}")
    with col2:
        f = st.file_uploader("Skill Training", type=["csv","xlsx"])
        if f: st.session_state["skills"]=load_file(f); st.success("Loaded")
    with col3:
        f = st.file_uploader("Project Assignment", type=["csv","xlsx"])
        if f:
            df = load_file(f)
            if validate(df, REQUIRED_PROJ): st.session_state["projects"]=df; st.success("Loaded")
            else: st.error(f"Missing columns: {set(REQUIRED_PROJ)-set(df.columns)}")
    with col4:
        f = st.file_uploader("PM Reportees", type=["csv","xlsx"])
        if f:
            df = load_file(f)
            if validate(df, REQUIRED_REP): st.session_state["reportees"]=df; st.success("Loaded")
            else: st.error(f"Missing columns: {set(REQUIRED_REP)-set(df.columns)}")

elif page=="Dashboard":
    df = st.session_state["activity"]
    if df.empty:
        st.info("Upload Employee Activity.")
    else:
        df = utilization(df)
        if st.session_state["role"]=="Project Manager" and not st.session_state["reportees"].empty:
            allowed = set(st.session_state["reportees"]["Employee"])
            df = df[df["Employee"].isin(allowed)]

        k1,k2,k3,k4 = st.columns(4)
        k1.metric("Employees", len(df))
        k2.metric("On Bench", (df["Bench_Status"]=="On Bench").sum())
        k3.metric("Partial", (df["Bench_Status"]=="Partially Utilized").sum())
        k4.metric("Full", (df["Bench_Status"]=="Fully Utilized").sum())

        bench = df["Bench_Status"].value_counts().rename_axis("Bench_Status").reset_index(name="Count")
        st.altair_chart(alt.Chart(bench).mark_bar().encode(x=alt.X("Bench_Status", sort=None), y="Count"), use_container_width=True)

        dept = df.groupby("Dept",as_index=False)["True_Utilization"].mean()
        st.altair_chart(alt.Chart(dept).mark_bar().encode(x=alt.X("Dept", sort="-y"), y="True_Utilization"), use_container_width=True)

        st.dataframe(df[["Employee","Dept","Bench_Status","True_Utilization","Skills","Cost"]], height=420)

elif page=="Skill Recommendations":
    emp = st.session_state["activity"]
    skl = st.session_state["skills"]
    if emp.empty or skl.empty:
        st.info("Upload Employee Activity and Skill Training.")
    else:
        emp = utilization(emp)
        universe = sorted({str(x).strip().lower() for x in skl["Skill"].dropna()})
        def rec(s):
            have = norm_skill_set(s)
            miss = [x for x in universe if x not in have]
            return ", ".join(miss) if miss else "None"
        emp["Recommended_Skills"] = emp["Skills"].apply(rec)
        st.dataframe(emp[["Employee","Dept","Bench_Status","True_Utilization","Skills","Recommended_Skills"]], height=480)

elif page=="Project Assignment":
    emp0 = st.session_state["activity"]
    proj0 = st.session_state["projects"]
    reps  = st.session_state["reportees"]
    if emp0.empty or proj0.empty:
        st.info("Upload Employee Activity and Project Assignment.")
    else:
        emp = utilization(emp0)
        proj = proj0.copy()
        if st.session_state["role"]=="Project Manager" and not reps.empty:
            allowed = set(reps["Employee"])
            emp = emp[emp["Employee"].isin(allowed)]

        thr = st.slider("Under-utilization threshold", 20, 70, 50, 5)
        assigns, unfilled = assign_projects(emp, proj, threshold=thr)

        st.markdown("#### Suggested Assignments")
        if assigns.empty: st.warning("No feasible assignments from bench/under-utilized pool.")
        else:
            st.dataframe(assigns, height=420)
            download_csv(assigns, "project_assignments.csv")

        st.markdown("#### Unfilled Requirements")
        if unfilled.empty: st.success("All project positions satisfied for current constraints.")
        else:
            st.dataframe(unfilled, height=240)
            download_csv(unfilled, "unfilled_requirements.csv")


