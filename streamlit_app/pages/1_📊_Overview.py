import streamlit as st
import duckdb
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Overview", page_icon="📊", layout="wide")

@st.cache_resource
def get_connection():
    return duckdb.connect("data/school_analytics_v3.duckdb", read_only=True)

conn = get_connection()

st.title("📊 Overview")

# Year selector
years = conn.execute("SELECT DISTINCT school_year FROM mart_student_accountability ORDER BY school_year").fetchdf()
selected_year = st.sidebar.selectbox("School Year", ["All Years"] + years['school_year'].tolist())

# Filter data
if selected_year == "All Years":
    year_filter = "1=1"
else:
    year_filter = f"school_year = '{selected_year}'"

# KPI Cards
kpis = conn.execute(f"""
    SELECT 
        COUNT(*) as students,
        ROUND(SUM(is_chronically_absent) * 100.0 / COUNT(*), 1) as chronic_pct,
        ROUND(SUM(is_behavior_risk) * 100.0 / COUNT(*), 1) as behavior_pct,
        ROUND(SUM(is_failing_any) * 100.0 / COUNT(*), 1) as failing_pct,
        ROUND(SUM(is_at_risk) * 100.0 / COUNT(*), 1) as at_risk_pct
    FROM mart_student_accountability
    WHERE {year_filter}
""").fetchdf()

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Students", f"{kpis['students'].iloc[0]:,}")
col2.metric("Chronic Absent", f"{kpis['chronic_pct'].iloc[0]}%")
col3.metric("Behavior Risk", f"{kpis['behavior_pct'].iloc[0]}%")
col4.metric("Failing Any", f"{kpis['failing_pct'].iloc[0]}%")
col5.metric("At-Risk", f"{kpis['at_risk_pct'].iloc[0]}%", 
            help="Students with 2+ ABC risk factors")

st.divider()

# Trend Chart
st.subheader("ABC Metrics Over Time")
trend_data = conn.execute("""
    SELECT 
        school_year,
        ROUND(SUM(is_chronically_absent) * 100.0 / COUNT(*), 1) as "Chronic Absent",
        ROUND(SUM(is_behavior_risk) * 100.0 / COUNT(*), 1) as "Behavior Risk",
        ROUND(SUM(is_failing_any) * 100.0 / COUNT(*), 1) as "Failing Any",
        ROUND(SUM(is_at_risk) * 100.0 / COUNT(*), 1) as "At-Risk"
    FROM mart_student_accountability
    GROUP BY school_year
    ORDER BY school_year
""").fetchdf()

fig = px.line(trend_data, x='school_year', 
              y=['Chronic Absent', 'Behavior Risk', 'Failing Any', 'At-Risk'],
              markers=True,
              labels={'value': 'Percentage', 'school_year': 'School Year', 'variable': 'Metric'})
fig.update_layout(height=400, legend_title_text='')
st.plotly_chart(fig, use_container_width=True)

# Risk Factor Distribution
st.subheader("Risk Score Distribution")
col1, col2 = st.columns(2)

with col1:
    risk_dist = conn.execute(f"""
        SELECT 
            abc_risk_score as "Risk Factors",
            COUNT(*) as "Students"
        FROM mart_student_accountability
        WHERE {year_filter}
        GROUP BY abc_risk_score
        ORDER BY abc_risk_score
    """).fetchdf()
    
    fig2 = px.bar(risk_dist, x='Risk Factors', y='Students', 
                  color='Risk Factors',
                  color_continuous_scale=['green', 'yellow', 'orange', 'red'])
    fig2.update_layout(height=300, showlegend=False)
    st.plotly_chart(fig2, use_container_width=True)

with col2:
    st.markdown("""
    **Risk Score Interpretation:**
    - **0**: No risk factors - student is on track
    - **1**: One risk factor - monitor closely  
    - **2**: Two risk factors - **AT-RISK**, intervention needed
    - **3**: All three factors - **HIGH PRIORITY**
    """)
