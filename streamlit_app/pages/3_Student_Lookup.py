"""
Student Lookup
Individual student scorecards with demographics, metrics, and trends
"""
import streamlit as st
import duckdb
import plotly.graph_objects as go
import pandas as pd

st.set_page_config(page_title="Student Lookup", page_icon="👤", layout="wide")

DB_PATH = 'data/school_analytics.duckdb'

def get_connection():
    return duckdb.connect(DB_PATH, read_only=True)

# Load data
conn = get_connection()
scorecard_df = conn.execute("SELECT * FROM mart_student_scorecard ORDER BY last_name, first_name, school_year").fetchdf()
conn.close()

st.title("Student Lookup")
st.markdown("Individual student scorecards with academic history")

st.divider()

# Create student list for dropdown
student_list = scorecard_df.drop_duplicates(subset=['student_key'])[['student_key', 'first_name', 'last_name']].copy()
student_list['display_name'] = student_list['last_name'] + ', ' + student_list['first_name']
student_list = student_list.sort_values('display_name')

# Student selector
selected_display = st.selectbox(
    "Select Student",
    options=student_list['display_name'].tolist()
)

# Get student_key for selected student
selected_key = student_list[student_list['display_name'] == selected_display]['student_key'].values[0]

# Get all records for this student
student_records = scorecard_df[scorecard_df['student_key'] == selected_key].sort_values('school_year')

# Latest record for current stats
latest = student_records.iloc[-1]

st.divider()

# Student Header
st.subheader(f"{latest['first_name']} {latest['last_name']}")

col1, col2, col3, col4 = st.columns(4)
col1.markdown(f"**Country:** {latest['country']}")
col2.markdown(f"**Grade:** {int(latest['grade_level'])}")
col3.markdown(f"**ESL Level:** {latest['esl_level'] if pd.notna(latest['esl_level']) else 'N/A'}")
col4.markdown(f"**Housing:** {latest['housing'] if pd.notna(latest['housing']) else 'N/A'}")

st.divider()

# Current Year Metrics
st.subheader(f"Performance: {latest['school_year']}")

m1, m2, m3, m4 = st.columns(4)
m1.metric("GPA", f"{latest['avg_fnl']:.1f}" if pd.notna(latest['avg_fnl']) else "N/A")
m2.metric("Courses", int(latest['total_courses']) if pd.notna(latest['total_courses']) else "N/A")
m3.metric("Absence Rate", f"{latest['absence_rate']:.1f}%" if pd.notna(latest['absence_rate']) else "N/A")
m4.metric("vs School Avg", f"{latest['gpa_vs_school']:+.1f}" if pd.notna(latest['gpa_vs_school']) else "N/A")

st.divider()

# Two column layout
left_col, right_col = st.columns(2)

with left_col:
    # GPA Trend Chart
    st.subheader("GPA Trend")
    
    if len(student_records) > 1:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=student_records['school_year'],
            y=student_records['avg_fnl'],
            mode='lines+markers',
            name='GPA',
            line=dict(width=3)
        ))
        fig.update_layout(
            xaxis_title="School Year",
            yaxis_title="Average GPA",
            yaxis=dict(range=[60, 100]),
            height=300,
            showlegend=False
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Only one year of data available")

with right_col:
    # Risk Status
    st.subheader("Risk Status")
    
    risk_level = latest['risk_level'] if pd.notna(latest['risk_level']) else 'Unknown'
    
    # Calculate risk_score safely handling NA values
    a_val = 1 if pd.notna(latest['is_A_risk']) and latest['is_A_risk'] == 1 else 0
    b_val = 1 if pd.notna(latest['is_B_risk']) and latest['is_B_risk'] == 1 else 0
    c_val = 1 if pd.notna(latest['is_C_risk']) and latest['is_C_risk'] == 1 else 0
    risk_score = a_val + b_val + c_val
    
    if risk_level == 'Low':
        st.success(f"Low Risk - Score: {risk_score}/3")
    elif risk_level == 'Monitor':
        st.warning(f"Monitor - Score: {risk_score}/3")
    elif risk_level == 'High':
        st.error(f"High Risk - Score: {risk_score}/3")
    elif risk_level == 'Critical':
        st.error(f"Critical - Score: {risk_score}/3")
    else:
        st.info("Risk level not available")
    
    a_risk = "At Risk" if pd.notna(latest['is_A_risk']) and latest['is_A_risk'] == 1 else "OK"
    b_risk = "At Risk" if pd.notna(latest['is_B_risk']) and latest['is_B_risk'] == 1 else "OK"
    c_risk = "At Risk" if pd.notna(latest['is_C_risk']) and latest['is_C_risk'] == 1 else "OK"
    
    st.markdown(f"**A (Attendance):** {a_risk}")
    st.markdown(f"**B (Behavior):** {b_risk}")
    st.markdown(f"**C (Course):** {c_risk}")

st.divider()

# Year-by-Year History Table
st.subheader("Academic History")

history_df = student_records[[
    'school_year', 'grade_level', 'total_courses', 'avg_fnl',
    'failing_courses', 'absence_rate', 'risk_level'
]].copy()

history_df.columns = ['Year', 'Grade', 'Courses', 'GPA', 'Failing', 'Absence %', 'Risk']

# Format columns
history_df['Grade'] = history_df['Grade'].apply(lambda x: int(x) if pd.notna(x) else 'N/A')
history_df['Courses'] = history_df['Courses'].apply(lambda x: int(x) if pd.notna(x) else 'N/A')
history_df['GPA'] = history_df['GPA'].apply(lambda x: f"{x:.1f}" if pd.notna(x) else 'N/A')
history_df['Failing'] = history_df['Failing'].apply(lambda x: int(x) if pd.notna(x) else 'N/A')
history_df['Absence %'] = history_df['Absence %'].apply(lambda x: f"{x:.1f}%" if pd.notna(x) else 'N/A')

st.dataframe(history_df, use_container_width=True, hide_index=True)

st.caption(f"Student ID: {latest['school_id']} | Years Enrolled: {len(student_records)}")
