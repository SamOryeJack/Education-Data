"""
Completion Tracker
Graduation rates by cohort and program type
"""
import streamlit as st
import duckdb
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

st.set_page_config(page_title="Completion Tracker", page_icon="graduation", layout="wide")

DB_PATH = 'data/school_analytics.duckdb'

def get_connection():
    return duckdb.connect(DB_PATH, read_only=True)

# Load data
conn = get_connection()
df = conn.execute("SELECT * FROM mart_completion_tracking").fetchdf()
conn.close()

st.title("Completion Tracker")
st.markdown("Graduation rates and completion status by cohort")

st.divider()

# Summary Metrics
graduated = len(df[df['completion_status'] == 'Graduated'])
current = len(df[df['completion_status'] == 'Current'])
departed = len(df[df['completion_status'] == 'Departed'])
total = len(df)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Students", total)
col2.metric("Graduated", graduated)
col3.metric("Current", current)
col4.metric("Departed", departed)

st.divider()

# Two column layout
left_col, right_col = st.columns(2)

with left_col:
    # Status Pie Chart
    st.subheader("Completion Status")
    
    status_counts = df['completion_status'].value_counts()
    
    fig_pie = px.pie(
        values=status_counts.values,
        names=status_counts.index,
        color=status_counts.index,
        color_discrete_map={
            'Graduated': '#2ca02c',
            'Current': '#1f77b4',
            'Departed': '#d62728'
        }
    )
    fig_pie.update_layout(height=350)
    st.plotly_chart(fig_pie, use_container_width=True)

with right_col:
    # Graduation Rate by Expected Year
    st.subheader("Graduation Rate by Cohort")
    
    # Only completed cohorts (expected grad <= 2025)
    completed = df[df['expected_grad_year'] <= 2025].copy()
    
    cohort_stats = completed.groupby('expected_grad_year').agg(
        total=('student_key', 'count'),
        graduated=('is_graduated', 'sum')
    ).reset_index()
    
    cohort_stats['grad_rate'] = (cohort_stats['graduated'] / cohort_stats['total'] * 100).round(1)
    
    fig_bar = go.Figure(data=[
        go.Bar(
            x=cohort_stats['expected_grad_year'].astype(str),
            y=cohort_stats['grad_rate'],
            text=cohort_stats['grad_rate'].apply(lambda x: f"{x:.0f}%"),
            textposition='auto',
            marker_color='#1f77b4'
        )
    ])
    fig_bar.update_layout(
        xaxis_title="Expected Graduation Year",
        yaxis_title="Graduation Rate (%)",
        yaxis=dict(range=[0, 100]),
        height=350
    )
    st.plotly_chart(fig_bar, use_container_width=True)

st.divider()

# Graduation Rate by Program Type
st.subheader("Graduation Rate by Program Type")

# Only completed cohorts
completed = df[df['expected_grad_year'] <= 2025].copy()

program_stats = completed.groupby('program_type').agg(
    total=('student_key', 'count'),
    graduated=('is_graduated', 'sum')
).reset_index()

program_stats['grad_rate'] = (program_stats['graduated'] / program_stats['total'] * 100).round(1)
program_stats = program_stats.sort_values('grad_rate', ascending=True)

fig_program = go.Figure(data=[
    go.Bar(
        x=program_stats['grad_rate'],
        y=program_stats['program_type'],
        text=program_stats.apply(lambda r: f"{r['grad_rate']:.0f}% ({int(r['graduated'])}/{int(r['total'])})", axis=1),
        textposition='auto',
        orientation='h',
        marker_color='#2ca02c'
    )
])
fig_program.update_layout(
    xaxis_title="Graduation Rate (%)",
    xaxis=dict(range=[0, 100]),
    height=300
)
st.plotly_chart(fig_program, use_container_width=True)

st.divider()

# Detailed Cohort Table
st.subheader("Cohort Details")

cohort_detail = df.groupby('expected_grad_year').agg(
    total=('student_key', 'count'),
    graduated=('is_graduated', 'sum'),
    current=('completion_status', lambda x: (x == 'Current').sum()),
    departed=('completion_status', lambda x: (x == 'Departed').sum())
).reset_index()

cohort_detail['grad_rate'] = (cohort_detail['graduated'] / cohort_detail['total'] * 100).round(1)
cohort_detail.columns = ['Expected Grad Year', 'Total', 'Graduated', 'Current', 'Departed', 'Grad Rate %']

# Format grad rate - show N/A for future cohorts
cohort_detail['Grad Rate %'] = cohort_detail.apply(
    lambda r: f"{r['Grad Rate %']:.1f}%" if r['Expected Grad Year'] <= 2025 else 'In Progress',
    axis=1
)

st.dataframe(cohort_detail, use_container_width=True, hide_index=True)

st.divider()

# Notes
with st.expander("Methodology Notes"):
    st.markdown("""
    **Definitions:**
    - **Graduated:** Students who reached Grade 12 with 4+ courses having final grades
    - **Current:** Students still enrolled
    - **Departed:** Students who left before graduation
    
    **Expected Graduation Year:** Calculated as intake_year + (12 - first_grade)
    
    **Graduation Rate:** Graduated / (Graduated + Departed) for completed cohorts only
    
    **Note:** This is an ACGR-style calculation. Exchange students (Semester/Full Year) are included 
    but their expected grad year may not reflect their actual program duration.
    """)
