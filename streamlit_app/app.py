import streamlit as st
import duckdb
import pandas as pd

st.set_page_config(
    page_title="Student Accountability Dashboard",
    page_icon="🎓",
    layout="wide"
)

@st.cache_resource
def get_connection():
    return duckdb.connect("data/school_analytics_v3.duckdb", read_only=True)

st.title("🎓 Student Accountability Dashboard")
st.markdown("### ABC Early Warning Framework + ESSA Alignment")
st.markdown("""
This dashboard tracks student risk using the **ABC Framework** and **ESSA Accountability Indicators**:

**ABC Framework:**
- **A**ttendance: Chronic absence (≥10% days missed)
- **B**ehavior: Discipline incidents (ISS, OSS, cuts, truancy)
- **C**ourse Performance: Failing grades (any course <75)

**ESSA Indicators:**
- Indicator 1: Academic Achievement (GPA, Pass Rate)
- Indicator 2: Academic Growth (Year-over-Year)
- Indicator 3: Graduation Rate (ACGR)
- Indicator 4: English Learner Progress
- Indicator 5: School Quality (Chronic Absenteeism)
""")

st.divider()

# Quick stats
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

st.divider()
st.markdown("👈 **Select a page from the sidebar to explore the data.**")
