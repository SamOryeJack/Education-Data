import streamlit as st
import duckdb
import pandas as pd
import os

st.set_page_config(page_title="Student Detail", page_icon="👤", layout="wide")

@st.cache_resource
def get_connection():
    paths = [
        "data/school_analytics.duckdb",
        "../data/school_analytics.duckdb",
    ]
    for path in paths:
        if os.path.exists(path):
            return duckdb.connect(path, read_only=True)
    return duckdb.connect("data/school_analytics.duckdb", read_only=True)

conn = get_connection()

st.title("👤 Student Detail")

# Get student list
students = conn.execute("""
    SELECT DISTINCT student_key, full_name, school_id
    FROM mart_student_accountability
    ORDER BY full_name
""").fetchdf()

# Student selector
selected_student = st.sidebar.selectbox(
    "Select Student",
    students['full_name'].tolist(),
    index=0
)

student_key = students[students['full_name'] == selected_student]['student_key'].iloc[0]

# Get student data across all years
student_data = conn.execute(f"""
    SELECT *
    FROM mart_student_accountability
    WHERE student_key = {student_key}
    ORDER BY school_year
""").fetchdf()

# Profile Card
st.subheader(f"📋 {selected_student}")
latest = student_data.iloc[-1]

col1, col2, col3, col4 = st.columns(4)
col1.metric("School ID", latest['school_id'])
col2.metric("Gender", latest['gender'] or "N/A")
col3.metric("Country", latest['country'] or "N/A")
col4.metric("Program", latest['program_type'] or "N/A")

st.divider()

# ABC Scorecard for each year
st.subheader("📊 ABC Risk Profile by Year")

for _, row in student_data.iterrows():
    risk_emoji = "🔴" if row['is_at_risk'] else "🟢"
    with st.expander(f"**{row['school_year']}** - Risk Score: {int(row['abc_risk_score'])}/3 {risk_emoji}"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**Attendance**")
            chronic = "🔴 Yes" if row['is_chronically_absent'] else "🟢 No"
            st.write(f"Chronic Absent: {chronic}")
            st.write(f"Absence Rate: {row['absence_rate']:.1f}%")
            absent_days = row['total_absent_days'] if row['total_absent_days'] else 0
            st.write(f"Days Absent: {absent_days:.1f}")
            tardies = int(row['total_tardies']) if row['total_tardies'] else 0
            st.write(f"Tardies: {tardies}")
        
        with col2:
            st.markdown("**Behavior**")
            behavior = "🔴 Yes" if row['is_behavior_risk'] else "🟢 No"
            st.write(f"Behavior Risk: {behavior}")
            st.write(f"ISS Days: {int(row['iss_days'] or 0)}")
            st.write(f"OSS Days: {int(row['oss_days'] or 0)}")
            st.write(f"Cut Incidents: {int(row['cut_incidents'] or 0)}")
        
        with col3:
            st.markdown("**Course Performance**")
            failing = "🔴 Yes" if row['is_failing_any'] else "🟢 No"
            st.write(f"Failing Any: {failing}")
            st.write(f"Courses: {int(row['courses_taken'] or 0)}")
            st.write(f"Passed: {int(row['courses_passed'] or 0)}")
            avg = row['avg_final_score']
            st.write(f"Avg Grade: {avg:.1f}" if avg else "N/A")

# Course grades for latest year
st.divider()
st.subheader(f"📚 Course Grades ({latest['school_year']})")

grades = conn.execute(f"""
    SELECT 
        c.course_name,
        c.course_rigor,
        g.teacher,
        g.q1_score,
        g.q2_score,
        g.q3_score,
        g.q4_score,
        g.final_score
    FROM fct_grades g
    JOIN dim_courses c ON g.course_key = c.course_key
    JOIN dim_terms t ON g.term_key = t.term_key
    WHERE g.student_key = {student_key}
      AND t.school_year = '{latest['school_year']}'
    ORDER BY c.course_name
""").fetchdf()

if len(grades) > 0:
    st.dataframe(grades, use_container_width=True, hide_index=True)
else:
    st.info("No course grades found for this year.")
