import streamlit as st
import duckdb
import pandas as pd
import os

st.set_page_config(
    page_title="Student Accountability Dashboard",
    page_icon="🎓",
    layout="wide"
)

# Find database - works locally and on Streamlit Cloud
@st.cache_resource
def get_connection():
    # Try multiple paths
    paths = [
        "data/school_analytics.duckdb",           # Local from streamlit_app/
        "../data/school_analytics.duckdb",        # Local from root
        "school_analytics.duckdb",                # Same directory
    ]
    
    for path in paths:
        if os.path.exists(path):
            return duckdb.connect(path, read_only=True)
    
    # For Streamlit Cloud - relative to repo root
    return duckdb.connect("data/school_analytics.duckdb", read_only=True)

st.title("🎓 Student Accountability Dashboard")
st.markdown("### ABC Early Warning Framework")
st.markdown("""
This dashboard tracks student risk using the **ABC Framework**:
- **A**ttendance: Chronic absence (≥10% days missed)
- **B**ehavior: Discipline incidents (ISS, OSS, cuts, truancy)
- **C**ourse Performance: Failing grades (any course <75)

Students with **2+ risk factors** are flagged as **At-Risk**.
""")

st.divider()

# Quick stats
try:
    conn = get_connection()
    stats = conn.execute("""
        SELECT 
            COUNT(DISTINCT student_key) as total_students,
            COUNT(DISTINCT school_year) as years_covered,
            SUM(CASE WHEN is_at_risk = 1 THEN 1 ELSE 0 END) as at_risk_count
        FROM mart_student_accountability
    """).fetchdf()

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Student-Years", f"{stats['total_students'].iloc[0]:,}")
    col2.metric("School Years", stats['years_covered'].iloc[0])
    col3.metric("At-Risk Records", f"{stats['at_risk_count'].iloc[0]:,}")

except Exception as e:
    st.error(f"Database connection error: {e}")
    st.info("Make sure school_analytics.duckdb is in the data/ folder")

st.divider()
st.markdown("👈 **Select a page from the sidebar to explore the data.**")
st.markdown("---")
st.markdown("*Built with DuckDB, dbt, and Streamlit | [GitHub Repo](https://github.com/SamOryeJack/Education-Data)*")
