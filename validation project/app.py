import os
from datetime import datetime
import pandas as pd
import streamlit as st
from validation import run_all_validations
from anomaly_detection import run_anomaly_detection
from summary_report import generate_summary_report
from error_log import build_error_log

# 1. Page Configuration
st.set_page_config(
    page_title="Bank Currency Report Validation System",
    layout="wide",
)

# 2. Color Palette Variables (Corporate & High-Visibility)
PRIMARY_NAVY = "#0B3D62"       
LIGHT_BG = "#F4F7FC"           
SIDEBAR_BG = "#E1E8F0"         
TEXT_DARK = "#1E293B"          

# 3. Comprehensive CSS Injection — EVERY text element forced dark and visible
st.markdown(
    f"""
    <style>
    /* Main Canvas Background */
    [data-testid="stAppViewContainer"] {{
        background-color: {LIGHT_BG};
    }}
    
    /* Sidebar Layout & Styling */
    [data-testid="stSidebar"] {{
        background-color: {SIDEBAR_BG} !important;
        border-right: 1px solid #CBD5E1;
    }}
    
    /* Headings, Titles, Subheadings */
    h1, h2, h3, h4, h5, h6, 
    .stHeadingContainer *, 
    [data-testid="stMarkdownContainer"] h1,
    [data-testid="stMarkdownContainer"] h2,
    [data-testid="stMarkdownContainer"] h3 {{
        color: {PRIMARY_NAVY} !important;
        font-family: 'Segoe UI', Helvetica, Arial, sans-serif;
    }}

    /* FORCE ALL Paragraphs, Bold Text (**text**), Labels, and Text Elements to be Dark Slate */
    p, span, label, strong, b,
    [data-testid="stMarkdownContainer"] *,
    [data-testid="stText"] * {{
        color: {TEXT_DARK} !important;
    }}

    /* FORCE Captions and Subtext to be clearly visible */
    [data-testid="stCaptionContainer"] *,
    .stCaption * {{
        color: #334155 !important;
    }}

    /* === FIX: Tab Buttons Visibility (Upload & Validate, History, Branch Tabs) === */
    button[data-baseweb="tab"] {{
        background-color: transparent !important;
        opacity: 1 !important;
    }}
    button[data-baseweb="tab"] * {{
        color: {TEXT_DARK} !important;
        font-weight: 600 !important;
    }}
    button[data-baseweb="tab"][aria-selected="true"] * {{
        color: {PRIMARY_NAVY} !important;
        font-weight: bold !important;
    }}

    /* === FIX: Sidebar Text Elements === */
    [data-testid="stSidebar"] * {{
        color: {TEXT_DARK} !important;
    }}
    div[data-baseweb="select"] * {{
        color: {TEXT_DARK} !important;
    }}

    /* === FIX: Password & Text Input Fields === */
    div[data-testid="stTextInput"] input {{
        color: #000000 !important;
        background-color: #FFFFFF !important;
        border: 1px solid #CBD5E1 !important;
    }}

    /* === FIX: Alert & Notification Boxes === */
    [data-testid="stNotification"] * {{
        color: #000000 !important;
    }}
    </style>
    """,
    unsafe_allow_html=True
)

HISTORY_DIR = "history"
REPORTS_DIR = "reports"
os.makedirs(HISTORY_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)

HQ_PASSWORD = os.environ.get("HQ_DASHBOARD_PASSWORD", "crdb-hq-2025")

BRANCH_CODES = {
    "DSM Branch": "DSM",
    "MWZ Branch": "MWZ",
    "DDM Branch": "DDM",
}

def sort_chronologically(df):
    out = df.copy()
    out["_sort_date"] = pd.to_datetime(out["report_date"], errors="coerce")
    out = out.sort_values("_sort_date", na_position="last").drop(columns="_sort_date")
    return out


def save_to_history(branch_label, df, kind):
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    branch_dir = os.path.join(HISTORY_DIR, branch_label)
    os.makedirs(branch_dir, exist_ok=True)
    path = os.path.join(branch_dir, f"{branch_label}_{kind}_{timestamp}.csv")
    df.to_csv(path, index=False)
    return path


def show_history(branch_label):
    branch_dir = os.path.join(HISTORY_DIR, branch_label)
    if not os.path.exists(branch_dir) or not os.listdir(branch_dir):
        st.caption("No upload history yet for this branch.")
        return
    files = sorted(os.listdir(branch_dir), reverse=True)
    for fname in files[:15]:
        fpath = os.path.join(branch_dir, fname)
        with open(fpath, "rb") as f:
            st.download_button(label=f"⬇ {fname}", data=f.read(), file_name=fname, key=fpath)


def save_branch_report(branch_code, report):
    path = os.path.join(REPORTS_DIR, f"{branch_code}_report.csv")
    report.to_csv(path, index=False)
    return path


def render_branch_page(label, branch_code):
    st.header(f"{label} Validation")
    tab_upload, tab_history = st.tabs(["Upload & Validate", "History"])
    with tab_upload:
        uploaded_file = st.file_uploader(f"Upload {branch_code} Raw Report", type=["csv"])
        if uploaded_file:
            df = pd.read_csv(uploaded_file, dtype={"branch_code": str})
            df_sorted = sort_chronologically(df)
            save_to_history(label, df, "raw")

            st.write("**Uploaded Dataset** (sorted chronologically)")
            st.dataframe(df_sorted, use_container_width=True)

            errors = run_all_validations(df)
            anomalies = run_anomaly_detection(df)
            all_flags = pd.concat([errors, anomalies], ignore_index=True)
            report = generate_summary_report(all_flags)
            log = build_error_log(df)

            st.write(f"**{len(df)} records checked — {len(all_flags)} flagged entries found "
                     f"(validation rules + anomaly detection).**")

            chart_col1, chart_col2 = st.columns(2)
            with chart_col1:
                st.write("**Error Breakdown**")
                if not all_flags.empty:
                    st.bar_chart(all_flags["error_type"].value_counts())
                else:
                    st.caption("No errors found.")

            with chart_col2:
                st.write("**Monthly Submission Volume**")
                trend = df_sorted.copy()
                trend["report_month"] = pd.to_datetime(trend["report_date"], errors="coerce").dt.to_period("M").astype(str)
                st.bar_chart(trend["report_month"].value_counts().sort_index())

            st.subheader(f"{branch_code} Summary Report")
            st.caption("Error type and how many times it occurred.")
            st.dataframe(report, use_container_width=True)

            st.subheader(f"{branch_code} Detailed Error Log")
            st.caption(
                "One row per flagged issue — shows the exact row number, "
                "which field is wrong, and what the bad value is, "
                "so the DQO can find and fix it directly in the source file."
            )
            st.dataframe(log, use_container_width=True)

            dl_col1, dl_col2 = st.columns(2)
            with dl_col1:
                st.download_button(
                    f"⬇ Download {branch_code} Summary Report",
                    report.to_csv(index=False),
                    f"{branch_code}_summary_report.csv",
                )
            with dl_col2:
                st.download_button(
                    f"⬇ Download {branch_code} Detailed Error Log",
                    log.to_csv(index=False),
                    f"{branch_code}_error_log.csv",
                )

            save_branch_report(branch_code, report)
            save_to_history(label, report, "summary_report")
            save_to_history(label, log, "error_log")

    with tab_history:
        st.write(f"Past uploads and reports for **{label}**:")
        show_history(label)


def render_hq_page():
    st.header("HQ Dashboard — Admin Access")
    if "hq_authenticated" not in st.session_state:
        st.session_state.hq_authenticated = False
    if not st.session_state.hq_authenticated:
        pw = st.text_input("Enter HQ admin password", type="password")
        if st.button("Login"):
            if pw == HQ_PASSWORD:
                st.session_state.hq_authenticated = True
                st.rerun()
            else:
                st.error("Incorrect password.")
        st.stop()

    col_logout, _ = st.columns([1, 5])
    with col_logout:
        if st.button("Logout"):
            st.session_state.hq_authenticated = False
            st.rerun()

    st.success("Authenticated as HQ Data Quality Officer.")

    found_any = False
    branch_reports = {}

    for label, code in BRANCH_CODES.items():
        path = os.path.join(REPORTS_DIR, f"{code}_report.csv")
        if os.path.exists(path):
            branch_reports[code] = pd.read_csv(path, dtype={"branch_code": str})
            found_any = True

    if not found_any:
        st.info("No branch reports are available yet. Reports will appear here once a branch uploads and validates its data.")
        return

    st.subheader("All Branch Reports")

    tabs = st.tabs(list(branch_reports.keys()))
    for tab, (code, report) in zip(tabs, branch_reports.items()):
        with tab:
            st.write(f"**{code} Branch Report**")
            st.dataframe(report, use_container_width=True)
            if not report.empty:
                st.bar_chart(report.groupby("error_type")["flagged_count"].sum())

    st.subheader("Side-by-Side Comparison")
    combined = pd.concat(
        [report.assign(branch=code) for code, report in branch_reports.items()],
        ignore_index=True,
    )
    if not combined.empty:
        pivot = combined.pivot_table(
            index="error_type", columns="branch", values="flagged_count", aggfunc="sum", fill_value=0
        )
        st.dataframe(pivot, use_container_width=True)
        st.bar_chart(pivot)

    st.download_button(
        "⬇ Download Combined View of All Branch Reports",
        combined.to_csv(index=False),
        "all_branches_combined_view.csv",
    )

# 4. App Headers and Navigation Controls
st.sidebar.title("Bank Currency Report Validation System")
st.sidebar.caption("Secured Data Quality Dashboard")

page = st.sidebar.selectbox("Select Location", ["DSM Branch", "MWZ Branch", "DDM Branch", "HQ"])

st.title("Bank Currency Report Validation System")

if page in BRANCH_CODES:
    render_branch_page(page, BRANCH_CODES[page])
elif page == "HQ":
    render_hq_page()
