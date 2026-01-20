"""
ESSA Accountability Scorecard
"""
import streamlit as st
import duckdb
import plotly.graph_objects as go
import pandas as pd

st.set_page_config(page_title="ESSA Scorecard", page_icon="chart", layout="wide")

DB_PATH = 'data/school_analytics.duckdb'

def get_connection():
    return duckdb.connect(DB_PATH, read_only=True)

# Load data
conn = get_connection()
df = conn.execute("SELECT * FROM mart_essa_accountability").fetchdf()
conn.close()

st.title("ESSA Accountability Scorecard")
st.markdown("Five indicators aligned with Every Student Succeeds Act framework")

# Filters
col1, col2 = st.columns(2)
years = sorted(df['school_year'].unique(), reverse=True)
selected_year = col1.selectbox("Select Year", years)

subgroup_types = df['subgroup_type'].unique().tolist()
selected_subgroup = col2.selectbox("Select Subgroup Type", subgroup_types)

st.divider()

# Display 5 ESSA metrics (for selected year, Overall)
st.subheader(f"ESSA Indicators: {selected_year}")

current = df[(df['school_year'] == selected_year) & (df['subgroup_type'] == 'Overall')].iloc[0]

m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Avg GPA", f"{current['ind1_avg_gpa']:.1f}", help="Indicator 1: Academic Achievement")
m2.metric("Pass Rate", f"{current['ind1_course_pass_rate']:.1f}%", help="Indicator 1: Course Pass Rate")
m3.metric("% Improved", f"{current['ind2_pct_improved']:.1f}%" if pd.notna(current['ind2_pct_improved']) else "N/A", help="Indicator 2: Academic Progress")
m4.metric("Grad Rate", f"{current['ind3_graduation_rate']:.1f}%", help="Indicator 3: Graduation Rate")
m5.metric("Chronic Absence", f"{current['ind5_chronic_absent_rate']:.1f}%", help="Indicator 5: School Quality")

st.divider()

# 4-Year Trend Chart - responds to subgroup selector
st.subheader(f"4-Year Trend: {selected_subgroup}")

trend_data = df[df['subgroup_type'] == selected_subgroup].sort_values('school_year')

fig = go.Figure()

# Get unique subgroup values for this type
subgroup_values = trend_data['subgroup_value'].unique()

# Add a line for each subgroup value
for sg_value in subgroup_values:
    sg_data = trend_data[trend_data['subgroup_value'] == sg_value]
    
    # Skip if suppressed (N < 10) for most years
    if sg_data['is_suppressed'].sum() > 2:
        continue
    
    fig.add_trace(go.Scatter(
        x=sg_data['school_year'], 
        y=sg_data['ind1_avg_gpa'],
        name=sg_value,
        mode='lines+markers'
    ))

fig.update_layout(
    xaxis_title="School Year",
    yaxis_title="Average GPA",
    legend=dict(orientation="h", yanchor="bottom", y=1.02),
    height=400
)
st.plotly_chart(fig, use_container_width=True)

st.divider()

# Subgroup Breakdown Table
st.subheader(f"Subgroup Breakdown: {selected_subgroup} ({selected_year})")

subgroup_data = df[(df['school_year'] == selected_year) & (df['subgroup_type'] == selected_subgroup)]

# Prepare display dataframe
display_df = subgroup_data[['subgroup_value', 'student_count', 'is_suppressed',
                            'ind1_avg_gpa', 'ind1_course_pass_rate', 
                            'ind2_pct_improved', 'ind3_graduation_rate',
                            'ind5_chronic_absent_rate']].copy()

display_df.columns = ['Subgroup', 'N', 'Suppressed', 'Avg GPA', 'Pass Rate', 
                      '% Improved', 'Grad Rate', 'Chronic Abs']

# Apply suppression display
for col in ['Avg GPA', 'Pass Rate', '% Improved', 'Grad Rate', 'Chronic Abs']:
    display_df[col] = display_df.apply(
        lambda row: '***' if row['Suppressed'] == 1 else f"{row[col]:.1f}" if pd.notna(row[col]) else 'N/A', 
        axis=1
    )

display_df = display_df.drop('Suppressed', axis=1)
st.dataframe(display_df, use_container_width=True, hide_index=True)

# FERPA note
suppressed_count = subgroup_data['is_suppressed'].sum()
if suppressed_count > 0:
    st.caption(f"*** = Suppressed (N < 10) for FERPA compliance. {suppressed_count} subgroup(s) suppressed.")

st.divider()

# ESSA Reference
with st.expander("ESSA Indicator Reference"):
    st.markdown("""
    | # | Indicator | Our Measure | Notes |
    |---|-----------|-------------|-------|
    | 1 | Academic Achievement | Avg GPA, Course Pass Rate | Proxy for state test proficiency |
    | 2 | Academic Progress | % with GPA improvement YoY | Proxy for Student Growth Percentile |
    | 3 | Graduation Rate | Seniors completing = graduated | ACGR-style calculation |
    | 4 | EL Proficiency | (Not yet implemented) | Need ESL level progression data |
    | 5 | School Quality (SQSS) | Chronic Absence Rate (>=10%) | Aligns with common SQSS measure |
    """)
