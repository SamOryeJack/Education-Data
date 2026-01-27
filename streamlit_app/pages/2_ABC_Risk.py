"""
ABC Risk Dashboard
Early Warning System: Attendance, Behavior, Course Performance
"""
import streamlit as st
import duckdb
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

st.set_page_config(page_title="ABC Risk Dashboard", page_icon="⚠️", layout="wide")

DB_PATH = 'data/school_analytics.duckdb'

def get_connection():
    return duckdb.connect(DB_PATH, read_only=True)

# Load data
conn = get_connection()
df = conn.execute("SELECT * FROM mart_student_abc_risk").fetchdf()
conn.close()

st.title("ABC Risk Dashboard")
st.markdown("Early Warning System: **A**ttendance, **B**ehavior, **C**ourse Performance")

st.divider()

# Summary Metrics
current_year = df['school_year'].iloc[0]
st.subheader(f"Risk Level Summary ({current_year})")

col1, col2, col3, col4 = st.columns(4)

critical = len(df[df['risk_level'] == 'Critical'])
high = len(df[df['risk_level'] == 'High'])
monitor = len(df[df['risk_level'] == 'Monitor'])
low = len(df[df['risk_level'] == 'Low'])

col1.metric("Critical", critical, help="3 risk factors")
col2.metric("High", high, help="2 risk factors")
col3.metric("Monitor", monitor, help="1 risk factor")
col4.metric("Low", low, help="0 risk factors")

st.divider()

# Two column layout for charts
left_col, right_col = st.columns(2)

with left_col:
    st.subheader("Risk Distribution")
    
    risk_counts = df['risk_level'].value_counts().reindex(['Critical', 'High', 'Monitor', 'Low'])
    
    fig_pie = px.pie(
        values=risk_counts.values, 
        names=risk_counts.index,
        color=risk_counts.index,
        color_discrete_map={
            'Critical': '#d62728',
            'High': '#ff7f0e', 
            'Monitor': '#ffbb78',
            'Low': '#2ca02c'
        }
    )
    fig_pie.update_layout(height=350)
    st.plotly_chart(fig_pie, use_container_width=True)

with right_col:
    st.subheader("Risk Factors Breakdown")
    
    a_risk = df['is_A_risk'].sum()
    b_risk = df['is_B_risk'].sum()
    c_risk = df['is_C_risk'].sum()
    
    fig_bar = go.Figure(data=[
        go.Bar(
            x=['A: Attendance', 'B: Behavior', 'C: Course'],
            y=[a_risk, b_risk, c_risk],
            text=[a_risk, b_risk, c_risk],
            textposition='auto',
            marker_color=['#1f77b4', '#ff7f0e', '#2ca02c']
        )
    ])
    fig_bar.update_layout(
        yaxis_title="Students at Risk",
        height=350,
        showlegend=False
    )
    st.plotly_chart(fig_bar, use_container_width=True)

st.divider()

# Risk by Grade Level
st.subheader("Risk Level by Grade")

grade_risk = df.groupby(['grade_level', 'risk_level']).size().unstack(fill_value=0)
grade_risk = grade_risk.reindex(columns=['Critical', 'High', 'Monitor', 'Low'], fill_value=0)

fig_stack = go.Figure()
colors = {'Critical': '#d62728', 'High': '#ff7f0e', 'Monitor': '#ffbb78', 'Low': '#2ca02c'}

for level in ['Low', 'Monitor', 'High', 'Critical']:
    if level in grade_risk.columns:
        fig_stack.add_trace(go.Bar(
            name=level,
            x=[f"Grade {g}" for g in grade_risk.index],
            y=grade_risk[level],
            marker_color=colors[level]
        ))

fig_stack.update_layout(
    barmode='stack',
    xaxis_title="Grade Level",
    yaxis_title="Number of Students",
    height=400,
    legend=dict(orientation="h", yanchor="bottom", y=1.02)
)
st.plotly_chart(fig_stack, use_container_width=True)

st.divider()

# Filterable Student List
st.subheader("Student Intervention List")

# Filters
filter_col1, filter_col2, filter_col3 = st.columns(3)

risk_filter = filter_col1.multiselect(
    "Risk Level",
    options=['Critical', 'High', 'Monitor', 'Low'],
    default=['Critical', 'High']
)

grade_filter = filter_col2.multiselect(
    "Grade Level",
    options=sorted(df['grade_level'].unique()),
    default=sorted(df['grade_level'].unique())
)

factor_filter = filter_col3.multiselect(
    "Risk Factor",
    options=['A: Attendance', 'B: Behavior', 'C: Course'],
    default=[]
)

# Apply filters
filtered_df = df[
    (df['risk_level'].isin(risk_filter)) &
    (df['grade_level'].isin(grade_filter))
]

# Apply factor filter if selected
if 'A: Attendance' in factor_filter:
    filtered_df = filtered_df[filtered_df['is_A_risk'] == 1]
if 'B: Behavior' in factor_filter:
    filtered_df = filtered_df[filtered_df['is_B_risk'] == 1]
if 'C: Course' in factor_filter:
    filtered_df = filtered_df[filtered_df['is_C_risk'] == 1]

# Prepare display table
display_df = filtered_df[[
    'first_name', 'last_name', 'grade_level', 'risk_level', 'risk_score',
    'absence_rate', 'is_A_risk', 'is_B_risk', 'is_C_risk',
    'failing_courses', 'current_gpa'
]].copy()

display_df.columns = [
    'First Name', 'Last Name', 'Grade', 'Risk Level', 'Score',
    'Absence %', 'A Risk', 'B Risk', 'C Risk',
    'Failing', 'GPA'
]

display_df['Absence %'] = display_df['Absence %'].apply(lambda x: f"{x:.1f}%")
display_df['GPA'] = display_df['GPA'].apply(lambda x: f"{x:.1f}")

# Sort by risk score descending
display_df = display_df.sort_values('Score', ascending=False)

st.dataframe(display_df, use_container_width=True, hide_index=True)
st.caption(f"Showing {len(display_df)} of {len(df)} students")

st.divider()

# Risk Factor Definitions
with st.expander("ABC Risk Factor Definitions"):
    st.markdown("""
    | Factor | Metric | Threshold | Flag |
    |--------|--------|-----------|------|
    | **A** (Attendance) | Chronic Absence Rate | >= 10% of instructional days | is_A_risk |
    | **B** (Behavior) | Discipline Events | ISS >= 1 OR OSS >= 1 OR Cut >= 2 OR TRU >= 1 | is_B_risk |
    | **C** (Course) | Failing Grades | Any course with grade < 75 | is_C_risk |
    
    **Risk Levels:**
    - **Critical:** 3 risk factors (all ABC flags)
    - **High:** 2 risk factors
    - **Monitor:** 1 risk factor
    - **Low:** 0 risk factors
    """)
