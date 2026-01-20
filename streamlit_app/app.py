"""
Student Accountability Dashboard - Home Page
Education Analytics Data Warehouse
"""
import streamlit as st
import duckdb

st.set_page_config(
    page_title="Student Accountability Dashboard", 
    page_icon="graduation_cap", 
    layout="wide"
)

DB_PATH = 'data/school_analytics.duckdb'

def run_query(query):
    conn = duckdb.connect(DB_PATH, read_only=True)
    result = conn.execute(query).fetchone()[0]
    conn.close()
    return result

# Header
st.title("Student Accountability Dashboard")
st.markdown("**Education Analytics Data Warehouse** - Xavier School for Gifted Youngsters")

st.divider()

# Key Metrics
try:
    students = run_query("SELECT COUNT(*) FROM dim_students")
    years = run_query("SELECT COUNT(DISTINCT school_year) FROM dim_terms")
    scorecards = run_query("SELECT COUNT(*) FROM mart_student_scorecard")
    assignments = run_query("SELECT COUNT(*) FROM fct_assignments")
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Students", f"{students:,}")
    col2.metric("School Years", years)
    col3.metric("Scorecard Records", f"{scorecards:,}")
    col4.metric("Assignments", f"{assignments:,}")
    
except Exception as e:
    st.error(f"Error loading metrics: {e}")

st.divider()

# Database Overview
st.subheader("Database Overview")

col1, col2 = st.columns(2)

with col1:
    st.markdown("**Dimension Tables**")
    st.markdown("""
    - `dim_students` - 636 students (231 active)
    - `dim_courses` - 1,080 courses
    - `dim_terms` - 8 terms (Fall/Spring x 4 years)
    """)
    
    st.markdown("**Reference Tables**")
    st.markdown("""
    - `ref_attendance_codes` - 46 codes
    - `ref_countries` - 34 countries
    """)

with col2:
    st.markdown("**Fact Tables**")
    st.markdown("""
    - `fct_enrollment` - 5,088 student-term records
    - `fct_grades` - 8,639 course grades
    - `fct_assignments` - 264,047 assignments
    - `fct_attendance_*` - Daily, course, quarter attendance
    """)
    
    st.markdown("**Mart Tables**")
    st.markdown("""
    - `mart_essa_accountability` - ESSA indicators by subgroup
    - `mart_student_abc_risk` - ABC Early Warning (231 students)
    - `mart_completion_tracking` - Graduation tracking
    - `mart_student_scorecard` - 971 student-year records
    """)

st.divider()

# Navigation Guide
st.subheader("Pages")

st.markdown("""
| Page | Description |
|------|-------------|
| **ESSA Scorecard** | 5 ESSA indicators with subgroup breakdowns and N-size suppression |
| **ABC Risk Dashboard** | Early warning system (Attendance, Behavior, Course performance) |
| **Student Lookup** | Individual student scorecards with trends |
| **Completion Tracker** | Graduation rates by cohort |
| **Defense Scenarios** | Templates for accountability responses |
""")

st.divider()

# Footer
st.caption("Built for Stride Research and Accountability Data Analyst portfolio")
st.caption("Data: 2022-23 through 2025-26 | 636 international students | 34 countries")
