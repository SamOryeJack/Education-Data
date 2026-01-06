import streamlit as st
import duckdb
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="ACGR Tracker", page_icon="🎓", layout="wide")

@st.cache_resource
def get_connection():
    return duckdb.connect("data/school_analytics.duckdb", read_only=True)

conn = get_connection()

st.title("🎓 ACGR Tracker")
st.markdown("**Adjusted Cohort Graduation Rate** - ESSA Indicator 3")
st.caption("Students who completed senior year with Q4 grades = Graduated (100% rate)")

st.divider()

# Overall ACGR trend
st.subheader("Graduates by Year")
overall = conn.execute("""
    SELECT graduation_year, graduates, acgr
    FROM mart_acgr
    WHERE subgroup_type = 'Overall'
    ORDER BY graduation_year
""").fetchdf()

col1, col2 = st.columns([2, 1])

with col1:
    fig = px.bar(overall, x='graduation_year', y='graduates',
                 text='graduates',
                 labels={'graduation_year': 'Graduation Year', 'graduates': 'Graduates'},
                 color='graduates',
                 color_continuous_scale='greens')
    fig.update_traces(textposition='outside')
    fig.update_layout(height=400, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.dataframe(overall[['graduation_year', 'graduates', 'acgr']], 
                 hide_index=True, use_container_width=True)
    st.metric("Total Graduates", overall['graduates'].sum())

st.divider()

# Subgroup Analysis
st.subheader("Graduates by Subgroup")

col1, col2 = st.columns(2)
with col1:
    grad_year = st.selectbox("Select Graduation Year", overall['graduation_year'].tolist(), index=len(overall)-2)
with col2:
    subgroup = st.selectbox("Select Subgroup", ['Gender', 'ESL Level', 'Country'])

# Get subgroup data
subgroup_data = conn.execute(f"""
    SELECT subgroup_value, graduates as n, acgr, is_suppressed
    FROM mart_acgr
    WHERE graduation_year = '{grad_year}'
      AND subgroup_type = '{subgroup}'
    ORDER BY graduates DESC
""").fetchdf()

# Display with suppression indicator
st.markdown(f"**{subgroup} Breakdown - {grad_year} Graduates**")
st.caption("⚠️ Values suppressed (--) where N < 10 for FERPA compliance")

# Format display
display_df = subgroup_data.copy()
display_df['Count'] = display_df.apply(
    lambda x: '--' if x['is_suppressed'] == 1 else str(x['n']), axis=1
)
st.dataframe(display_df[['subgroup_value', 'Count']], 
             hide_index=True, use_container_width=True)

# Visualization (non-suppressed only)
non_suppressed = subgroup_data[subgroup_data['is_suppressed'] == 0]
if len(non_suppressed) > 0:
    fig2 = px.bar(non_suppressed, x='subgroup_value', y='n',
                  color='n', color_continuous_scale='greens',
                  labels={'subgroup_value': subgroup, 'n': 'Graduates'})
    fig2.update_layout(height=350, showlegend=False)
    st.plotly_chart(fig2, use_container_width=True)

st.divider()

# Summary
st.subheader("Summary")
st.info("""
**Note:** All diploma-seeking seniors who completed Q4/final grades are counted as graduates.  
This represents a 100% graduation rate for students who reach senior year and complete the program.
""")
