import streamlit as st
import duckdb
import pandas as pd
import plotly.express as px
import os

st.set_page_config(page_title="Subgroup Analysis", page_icon="📈", layout="wide")

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

st.title("📈 Subgroup Analysis")

# Filters
col1, col2 = st.columns(2)
with col1:
    years = conn.execute("SELECT DISTINCT school_year FROM mart_student_accountability ORDER BY school_year").fetchdf()
    selected_year = st.selectbox("School Year", years['school_year'].tolist(), index=len(years)-1)

with col2:
    subgroup_type = st.selectbox("Compare By", ["Gender", "Program", "Boarding"])

# Build query based on subgroup
if subgroup_type == "Gender":
    group_col = "gender"
    filter_col = "gender"
elif subgroup_type == "Program":
    group_col = "program_type"
    filter_col = "program_type"
else:
    group_col = "CASE WHEN is_boarding = 1 THEN 'Boarding' ELSE 'Non-Boarding' END"
    filter_col = "is_boarding"

# Get comparison data
comparison = conn.execute(f"""
    SELECT 
        {group_col} as subgroup,
        COUNT(*) as students,
        ROUND(AVG(absence_rate), 1) as avg_absence_rate,
        ROUND(SUM(is_chronically_absent) * 100.0 / COUNT(*), 1) as chronic_pct,
        ROUND(SUM(is_behavior_risk) * 100.0 / COUNT(*), 1) as behavior_pct,
        ROUND(SUM(is_failing_any) * 100.0 / COUNT(*), 1) as failing_pct,
        ROUND(SUM(is_at_risk) * 100.0 / COUNT(*), 1) as at_risk_pct,
        ROUND(AVG(avg_final_score), 1) as avg_gpa
    FROM mart_student_accountability
    WHERE school_year = '{selected_year}'
      AND {filter_col} IS NOT NULL
    GROUP BY {group_col}
    ORDER BY subgroup
""").fetchdf()

# Display table
st.subheader(f"Comparison by {subgroup_type} ({selected_year})")
st.dataframe(comparison, use_container_width=True, hide_index=True)

# Visualization
st.subheader("At-Risk Rate by Subgroup")
if len(comparison) > 0:
    fig = px.bar(comparison, x='subgroup', y='at_risk_pct',
                 color='at_risk_pct',
                 color_continuous_scale=['green', 'yellow', 'red'],
                 labels={'subgroup': subgroup_type, 'at_risk_pct': 'At-Risk %'})
    fig.update_layout(height=400, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

# Gap Analysis
st.subheader("Gap Analysis")
if len(comparison) >= 2:
    max_risk = comparison['at_risk_pct'].max()
    min_risk = comparison['at_risk_pct'].min()
    gap = max_risk - min_risk
    
    max_group = comparison[comparison['at_risk_pct'] == max_risk]['subgroup'].iloc[0]
    min_group = comparison[comparison['at_risk_pct'] == min_risk]['subgroup'].iloc[0]
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Highest Risk", f"{max_group}", f"{max_risk}%")
    col2.metric("Lowest Risk", f"{min_group}", f"{min_risk}%")
    col3.metric("Gap", f"{gap:.1f} pp", help="Percentage points difference")

# Download button
st.divider()
csv = comparison.to_csv(index=False)
st.download_button(
    label="📥 Download Data as CSV",
    data=csv,
    file_name=f"subgroup_analysis_{selected_year}_{subgroup_type}.csv",
    mime="text/csv"
)
