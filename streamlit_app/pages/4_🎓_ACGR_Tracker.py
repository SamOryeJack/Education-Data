import streamlit as st
import duckdb
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="ACGR Tracker", page_icon="🎓", layout="wide")

@st.cache_resource
def get_connection():
    return duckdb.connect("data/school_analytics_v3.duckdb", read_only=True)

conn = get_connection()

st.title("🎓 ACGR Tracker")
st.markdown("**Adjusted Cohort Graduation Rate** - ESSA Indicator 3")

st.divider()

# Overall ACGR trend
st.subheader("Overall ACGR by Cohort")
overall = conn.execute("""
    SELECT cohort_year, expected_grad_year, cohort_count, graduates, 
           adjusted_cohort, acgr
    FROM mart_acgr
    WHERE subgroup_type = 'Overall'
    ORDER BY cohort_year
""").fetchdf()

col1, col2 = st.columns([2, 1])

with col1:
    fig = px.bar(overall, x='cohort_year', y='acgr',
                 text='acgr',
                 labels={'cohort_year': 'Cohort Year', 'acgr': 'ACGR %'},
                 color='acgr',
                 color_continuous_scale=['red', 'yellow', 'green'])
    fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
    fig.update_layout(height=400, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.dataframe(overall[['cohort_year', 'cohort_count', 'graduates', 'acgr']], 
                 hide_index=True, use_container_width=True)

st.divider()

# Subgroup Analysis
st.subheader("ACGR by Subgroup")

col1, col2 = st.columns(2)
with col1:
    cohort = st.selectbox("Select Cohort Year", overall['cohort_year'].tolist(), index=len(overall)-1)
with col2:
    subgroup = st.selectbox("Select Subgroup", ['Gender', 'ESL Level', 'Country'])

# Get subgroup data
subgroup_data = conn.execute(f"""
    SELECT subgroup_value, cohort_count as n, graduates, acgr, 
           is_suppressed, acgr_suppressed
    FROM mart_acgr
    WHERE cohort_year = {cohort}
      AND subgroup_type = '{subgroup}'
    ORDER BY acgr DESC
""").fetchdf()

# Display with suppression indicator
st.markdown(f"**{subgroup} Breakdown - Cohort {cohort}**")
st.caption("⚠️ Values suppressed (--) where N < 10 for FERPA compliance")

# Format display
display_df = subgroup_data.copy()
display_df['ACGR'] = display_df.apply(
    lambda x: '--' if x['is_suppressed'] == 1 else f"{x['acgr']:.1f}%", axis=1
)
st.dataframe(display_df[['subgroup_value', 'n', 'graduates', 'ACGR']], 
             hide_index=True, use_container_width=True)

# Visualization (non-suppressed only)
non_suppressed = subgroup_data[subgroup_data['is_suppressed'] == 0]
if len(non_suppressed) > 0:
    fig2 = px.bar(non_suppressed, x='subgroup_value', y='acgr',
                  color='acgr', color_continuous_scale=['red', 'yellow', 'green'],
                  labels={'subgroup_value': subgroup, 'acgr': 'ACGR %'})
    fig2.update_layout(height=350, showlegend=False)
    st.plotly_chart(fig2, use_container_width=True)

st.divider()

# Gap Analysis
st.subheader("Equity Gap Analysis")
gaps = conn.execute(f"""
    SELECT subgroup_type, 
           MAX(acgr) - MIN(acgr) as gap,
           MAX(acgr) as highest,
           MIN(acgr) as lowest
    FROM mart_acgr
    WHERE cohort_year = {cohort}
      AND is_suppressed = 0
      AND subgroup_type != 'Overall'
    GROUP BY subgroup_type
""").fetchdf()

for _, row in gaps.iterrows():
    st.metric(f"{row['subgroup_type']} Gap", 
              f"{row['gap']:.1f} pp",
              help=f"Highest: {row['highest']:.1f}% | Lowest: {row['lowest']:.1f}%")
