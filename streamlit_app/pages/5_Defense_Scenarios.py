"""
Defense Scenarios
Templates for accountability responses
"""
import streamlit as st
import duckdb
import plotly.graph_objects as go
import pandas as pd

st.set_page_config(page_title="Defense Scenarios", page_icon="🛡️", layout="wide")

DB_PATH = 'data/school_analytics.duckdb'

def get_connection():
    return duckdb.connect(DB_PATH, read_only=True)

# Load data
conn = get_connection()
essa_df = conn.execute("SELECT * FROM mart_essa_accountability WHERE subgroup_type = 'Overall' ORDER BY school_year").fetchdf()
abc_df = conn.execute("SELECT * FROM mart_student_abc_risk").fetchdf()
completion_df = conn.execute("SELECT * FROM mart_completion_tracking").fetchdf()
conn.close()

# Get current year dynamically
current_year = essa_df['school_year'].max()
latest = essa_df[essa_df['school_year'] == current_year].iloc[0]

st.title("Defense Scenarios")
st.markdown("Data packages for accountability responses and stakeholder communications")

st.divider()

# Scenario Selector
scenario = st.selectbox(
    "Select Scenario",
    options=[
        "A: High Chronic Absenteeism",
        "B: Course Failure Concerns",
        "C: Overall Accountability Summary"
    ]
)

st.divider()

# ============================================
# SCENARIO A: High Chronic Absenteeism
# ============================================
if scenario == "A: High Chronic Absenteeism":
    st.subheader("Scenario A: High Chronic Absenteeism Defense")
    
    # Current concern
    current_rate = latest['ind5_chronic_absent_rate']
    st.error(f"Current Concern: Chronic absenteeism rate is {current_rate:.1f}%")
    
    st.markdown("---")
    
    # 1. Historical Trend
    st.markdown("**1. Historical Trend (Improvement Trajectory)**")
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=essa_df['school_year'],
        y=essa_df['ind5_chronic_absent_rate'],
        mode='lines+markers',
        line=dict(width=3),
        marker=dict(size=10)
    ))
    fig.update_layout(
        xaxis_title="School Year",
        yaxis_title="Chronic Absence Rate (%)",
        height=300
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Trend narrative
    peak_year = essa_df.loc[essa_df['ind5_chronic_absent_rate'].idxmax(), 'school_year']
    peak_rate = essa_df['ind5_chronic_absent_rate'].max()
    
    st.info(f"Peak was {peak_rate:.1f}% in {peak_year}. Current rate of {current_rate:.1f}% shows {'improvement' if current_rate < peak_rate else 'concern'}.")
    
    st.markdown("---")
    
    # 2. Context Factors
    st.markdown("**2. Context Factors**")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        **Population Characteristics:**
        - 100% international students
        - Students from 34 countries
        - Many first-time US students
        - Cultural adjustment period expected
        """)
    with col2:
        st.markdown("""
        **Structural Factors:**
        - Visa/travel requirements
        - Family visits abroad
        - Medical appointments for international students
        - Time zone adjustment issues
        """)
    
    st.markdown("---")
    
    # 3. Offsetting Strengths
    st.markdown("**3. Offsetting Strengths**")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("GPA", f"{latest['ind1_avg_gpa']:.1f}")
    col2.metric("Pass Rate", f"{latest['ind1_course_pass_rate']:.1f}%")
    col3.metric("Graduation Rate", f"{latest['ind3_graduation_rate']:.1f}%")
    
    st.success(f"Despite attendance challenges, academic performance remains strong with {latest['ind1_avg_gpa']:.1f} GPA and {latest['ind1_course_pass_rate']:.1f}% course pass rate.")

# ============================================
# SCENARIO B: Course Failure Concerns
# ============================================
elif scenario == "B: Course Failure Concerns":
    st.subheader("Scenario B: Course Failure Concerns Defense")
    
    # Current concern
    c_risk_count = len(abc_df[abc_df['is_C_risk'] == 1])
    c_risk_pct = c_risk_count / len(abc_df) * 100
    st.error(f"Current Concern: {c_risk_count} students ({c_risk_pct:.1f}%) have at least one failing course")
    
    st.markdown("---")
    
    # 1. Historical Trend
    st.markdown("**1. Historical Pass Rate Trend**")
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=essa_df['school_year'],
        y=essa_df['ind1_course_pass_rate'],
        mode='lines+markers',
        line=dict(width=3),
        marker=dict(size=10)
    ))
    fig.update_layout(
        xaxis_title="School Year",
        yaxis_title="Course Pass Rate (%)",
        yaxis=dict(range=[80, 100]),
        height=300
    )
    st.plotly_chart(fig, use_container_width=True)
    
    latest_pass = latest['ind1_course_pass_rate']
    st.info(f"Current pass rate of {latest_pass:.1f}% is above 90% threshold.")
    
    st.markdown("---")
    
    # 2. Risk Distribution
    st.markdown("**2. At-Risk Student Distribution**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # By grade level
        grade_risk = abc_df[abc_df['is_C_risk'] == 1].groupby('grade_level').size().reset_index(name='count')
        
        fig_grade = go.Figure(data=[
            go.Bar(x=[f"Grade {int(g)}" for g in grade_risk['grade_level']], y=grade_risk['count'])
        ])
        fig_grade.update_layout(title="Failing Students by Grade", height=250)
        st.plotly_chart(fig_grade, use_container_width=True)
    
    with col2:
        # By ESL level
        esl_risk = abc_df[abc_df['is_C_risk'] == 1].groupby('esl_level').size().reset_index(name='count')
        
        fig_esl = go.Figure(data=[
            go.Bar(x=esl_risk['esl_level'], y=esl_risk['count'])
        ])
        fig_esl.update_layout(title="Failing Students by ESL Level", height=250)
        st.plotly_chart(fig_esl, use_container_width=True)
    
    st.markdown("---")
    
    # 3. Intervention Response - calculated from data
    st.markdown("**3. Intervention Framework**")
    
    critical_count = len(abc_df[abc_df['risk_level'] == 'Critical'])
    high_count = len(abc_df[abc_df['risk_level'] == 'High'])
    monitor_count = len(abc_df[abc_df['risk_level'] == 'Monitor'])
    low_count = len(abc_df[abc_df['risk_level'] == 'Low'])
    
    st.markdown(f"""
    | Risk Level | Count | Intervention |
    |------------|-------|--------------|
    | Critical (3 factors) | {critical_count} | Immediate support team meeting |
    | High (2 factors) | {high_count} | Weekly check-ins with advisor |
    | Monitor (1 factor) | {monitor_count} | Bi-weekly progress monitoring |
    | Low (0 factors) | {low_count} | Standard support |
    """)

# ============================================
# SCENARIO C: Overall Accountability Summary
# ============================================
else:
    st.subheader("Scenario C: Overall Accountability Summary")
    
    st.markdown("**ESSA-Aligned Performance Summary**")
    
    # Full scorecard
    display_df = essa_df[['school_year', 'student_count', 'ind1_avg_gpa', 'ind1_course_pass_rate',
                          'ind2_pct_improved', 'ind3_graduation_rate', 'ind5_chronic_absent_rate']].copy()
    
    display_df.columns = ['Year', 'N', 'Avg GPA', 'Pass Rate', '% Improved', 'Grad Rate', 'Chronic Abs']
    
    for col in ['Avg GPA', 'Pass Rate', '% Improved', 'Grad Rate', 'Chronic Abs']:
        display_df[col] = display_df[col].apply(lambda x: f"{x:.1f}" if pd.notna(x) else 'N/A')
    
    st.dataframe(display_df, use_container_width=True, hide_index=True)
    
    st.markdown("---")
    
    # Key Strengths - calculated from data
    st.markdown("**Key Strengths**")
    
    min_grad_rate = essa_df['ind3_graduation_rate'].min()
    min_gpa = essa_df['ind1_avg_gpa'].min()
    min_pass_rate = essa_df['ind1_course_pass_rate'].min()
    
    col1, col2, col3 = st.columns(3)
    col1.success(f"Graduation Rate {min_grad_rate:.0f}%+ (all years)")
    col2.success(f"GPA consistently above {min_gpa:.0f}")
    col3.success(f"Pass rate above {min_pass_rate:.0f}% every year")
    
    st.markdown("---")
    
    # Areas for Improvement - calculated from data
    st.markdown("**Areas for Improvement**")
    
    peak_absence_year = essa_df.loc[essa_df['ind5_chronic_absent_rate'].idxmax(), 'school_year']
    peak_absence_rate = essa_df['ind5_chronic_absent_rate'].max()
    current_absence_rate = latest['ind5_chronic_absent_rate']
    
    st.warning(f"Chronic absenteeism peaked at {peak_absence_rate:.1f}% in {peak_absence_year}, now at {current_absence_rate:.1f}%")
    
    st.markdown("---")
    
    # Completion Summary
    st.markdown("**Completion Summary**")
    
    graduated = len(completion_df[completion_df['completion_status'] == 'Graduated'])
    departed = len(completion_df[completion_df['completion_status'] == 'Departed'])
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Students (4 years)", len(completion_df))
    col2.metric("Graduated", graduated)
    col3.metric("Departed Early", departed)
    
    overall_rate = graduated / (graduated + departed) * 100
    st.info(f"Overall completion rate: {overall_rate:.1f}% of non-active students graduated")

st.divider()

# Export Note
st.caption("Use browser print function (Ctrl+P) to export this page as PDF for stakeholder communications.")
