"""
Course Analysis
Department and course-level performance analysis
"""
import streamlit as st
import duckdb
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

st.set_page_config(page_title="Course Analysis", page_icon="book", layout="wide")

DB_PATH = 'data/school_analytics.duckdb'

def get_connection():
    return duckdb.connect(DB_PATH, read_only=True)

conn = get_connection()

# Department performance
dept_df = conn.execute("""
    SELECT 
        c.department,
        COUNT(*) as enrollments,
        ROUND(AVG(g.fnl), 1) as avg_grade,
        ROUND(100.0 * SUM(CASE WHEN g.fnl >= 75 THEN 1 ELSE 0 END) / COUNT(*), 1) as pass_rate,
        ROUND(100.0 * SUM(CASE WHEN g.fnl >= 90 THEN 1 ELSE 0 END) / COUNT(*), 1) as a_rate
    FROM fct_grades g
    JOIN dim_courses c ON g.course_key = c.course_key
    WHERE g.fnl IS NOT NULL
      AND c.is_lab = 0 AND c.is_homeroom = 0 AND c.is_admin = 0
    GROUP BY c.department
    ORDER BY avg_grade DESC
""").fetchdf()

# Course-level performance (top/bottom)
course_df = conn.execute("""
    SELECT 
        c.course_name,
        c.department,
        c.course_rigor,
        COUNT(*) as enrollments,
        ROUND(AVG(g.fnl), 1) as avg_grade,
        ROUND(100.0 * SUM(CASE WHEN g.fnl >= 75 THEN 1 ELSE 0 END) / COUNT(*), 1) as pass_rate
    FROM fct_grades g
    JOIN dim_courses c ON g.course_key = c.course_key
    WHERE g.fnl IS NOT NULL
      AND c.is_lab = 0 AND c.is_homeroom = 0 AND c.is_admin = 0
    GROUP BY c.course_key, c.course_name, c.department, c.course_rigor
    HAVING COUNT(*) >= 10
    ORDER BY avg_grade DESC
""").fetchdf()

# Rigor level performance
rigor_df = conn.execute("""
    SELECT 
        c.course_rigor,
        COUNT(*) as enrollments,
        ROUND(AVG(g.fnl), 1) as avg_grade,
        ROUND(100.0 * SUM(CASE WHEN g.fnl >= 75 THEN 1 ELSE 0 END) / COUNT(*), 1) as pass_rate
    FROM fct_grades g
    JOIN dim_courses c ON g.course_key = c.course_key
    WHERE g.fnl IS NOT NULL
      AND c.is_lab = 0 AND c.is_homeroom = 0 AND c.is_admin = 0
      AND c.course_rigor IS NOT NULL
    GROUP BY c.course_rigor
    ORDER BY avg_grade DESC
""").fetchdf()

# Failure rate by department
failure_df = conn.execute("""
    SELECT 
        c.department,
        COUNT(*) as total,
        SUM(CASE WHEN g.fnl < 75 THEN 1 ELSE 0 END) as failing,
        ROUND(100.0 * SUM(CASE WHEN g.fnl < 75 THEN 1 ELSE 0 END) / COUNT(*), 1) as fail_rate
    FROM fct_grades g
    JOIN dim_courses c ON g.course_key = c.course_key
    WHERE g.fnl IS NOT NULL
      AND c.is_lab = 0 AND c.is_homeroom = 0 AND c.is_admin = 0
    GROUP BY c.department
    ORDER BY fail_rate DESC
""").fetchdf()

conn.close()

st.title("Course Analysis")
st.markdown("Department and course-level performance metrics")

st.divider()

# Department Overview
st.subheader("Performance by Department")

col1, col2 = st.columns(2)

with col1:
    # Average Grade by Department
    fig_dept = go.Figure(data=[
        go.Bar(
            x=dept_df['avg_grade'],
            y=dept_df['department'],
            orientation='h',
            text=dept_df['avg_grade'],
            textposition='auto',
            marker_color='#1f77b4'
        )
    ])
    fig_dept.update_layout(
        title="Average Grade by Department",
        xaxis_title="Average Final Grade",
        xaxis=dict(range=[70, 100]),
        yaxis=dict(autorange="reversed"),
        height=400
    )
    st.plotly_chart(fig_dept, use_container_width=True)

with col2:
    # Failure Rate by Department
    fig_fail = go.Figure(data=[
        go.Bar(
            x=failure_df['fail_rate'],
            y=failure_df['department'],
            orientation='h',
            text=failure_df['fail_rate'].apply(lambda x: f"{x}%"),
            textposition='auto',
            marker_color='#d62728'
        )
    ])
    fig_fail.update_layout(
        title="Failure Rate by Department",
        xaxis_title="Failure Rate (%)",
        yaxis=dict(autorange="reversed"),
        height=400
    )
    st.plotly_chart(fig_fail, use_container_width=True)

st.divider()

# Department Table
st.subheader("Department Summary")

dept_display = dept_df.copy()
dept_display.columns = ['Department', 'Enrollments', 'Avg Grade', 'Pass Rate %', 'A Rate %']
st.dataframe(dept_display, use_container_width=True, hide_index=True)

st.divider()

# Rigor Level Analysis
st.subheader("Performance by Course Rigor")

col1, col2 = st.columns([1, 2])

with col1:
    rigor_display = rigor_df.copy()
    rigor_display.columns = ['Rigor Level', 'Enrollments', 'Avg Grade', 'Pass Rate %']
    st.dataframe(rigor_display, use_container_width=True, hide_index=True)

with col2:
    fig_rigor = go.Figure()
    fig_rigor.add_trace(go.Bar(
        x=rigor_df['course_rigor'],
        y=rigor_df['avg_grade'],
        name='Avg Grade',
        marker_color='#1f77b4'
    ))
    fig_rigor.add_trace(go.Bar(
        x=rigor_df['course_rigor'],
        y=rigor_df['pass_rate'],
        name='Pass Rate %',
        marker_color='#2ca02c'
    ))
    fig_rigor.update_layout(
        barmode='group',
        xaxis_title="Course Rigor",
        yaxis_title="Score / Percentage",
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        height=300
    )
    st.plotly_chart(fig_rigor, use_container_width=True)

st.divider()

# Top/Bottom Courses
st.subheader("Course-Level Analysis")

tab1, tab2 = st.tabs(["Highest Performing", "Lowest Performing"])

with tab1:
    top_courses = course_df.nlargest(15, 'avg_grade')[['course_name', 'department', 'course_rigor', 'enrollments', 'avg_grade', 'pass_rate']]
    top_courses.columns = ['Course', 'Department', 'Rigor', 'Enrollments', 'Avg Grade', 'Pass Rate %']
    st.dataframe(top_courses, use_container_width=True, hide_index=True)

with tab2:
    bottom_courses = course_df.nsmallest(15, 'avg_grade')[['course_name', 'department', 'course_rigor', 'enrollments', 'avg_grade', 'pass_rate']]
    bottom_courses.columns = ['Course', 'Department', 'Rigor', 'Enrollments', 'Avg Grade', 'Pass Rate %']
    st.dataframe(bottom_courses, use_container_width=True, hide_index=True)

st.divider()

# Filter by Department
st.subheader("Courses by Department")

selected_dept = st.selectbox("Select Department", sorted(course_df['department'].unique()))

dept_courses = course_df[course_df['department'] == selected_dept].sort_values('avg_grade', ascending=False)
dept_courses_display = dept_courses[['course_name', 'course_rigor', 'enrollments', 'avg_grade', 'pass_rate']].copy()
dept_courses_display.columns = ['Course', 'Rigor', 'Enrollments', 'Avg Grade', 'Pass Rate %']

st.dataframe(dept_courses_display, use_container_width=True, hide_index=True)
