import streamlit as st
import duckdb
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="ESSA Scorecard", page_icon="📋", layout="wide")

@st.cache_resource
def get_connection():
    return duckdb.connect("data/school_analytics.duckdb", read_only=True)

conn = get_connection()

st.title("📋 ESSA Accountability Scorecard")
st.markdown("**Every Student Succeeds Act** - 5 Indicator Framework")

# Year selector
years = conn.execute("""
    SELECT DISTINCT school_year FROM mart_essa_accountability ORDER BY school_year
""").fetchdf()
selected_year = st.sidebar.selectbox("School Year", years['school_year'].tolist(), index=len(years)-1)

st.divider()

# Get overall data for selected year
overall = conn.execute(f"""
    SELECT * FROM mart_essa_accountability
    WHERE school_year = '{selected_year}' AND subgroup_type = 'Overall'
""").fetchdf().iloc[0]

# Scorecard
st.subheader(f"School Scorecard - {selected_year}")

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.markdown("**Indicator 1**")
    st.markdown("*Achievement*")
    st.metric("Avg GPA", f"{overall['avg_gpa']:.1f}")
    st.metric("Pass Rate", f"{overall['avg_pass_rate']:.1f}%")

with col2:
    st.markdown("**Indicator 2**")
    st.markdown("*Growth*")
    pct_improved = overall['pct_improved'] if pd.notna(overall['pct_improved']) else 'N/A'
    st.metric("% Improved", f"{pct_improved}%" if pct_improved != 'N/A' else pct_improved)
    st.caption(f"n={overall['students_with_prior']}")

with col3:
    st.markdown("**Indicator 3**")
    st.markdown("*Graduation*")
    # Get latest ACGR
    acgr = conn.execute("""
        SELECT acgr FROM mart_acgr 
        WHERE subgroup_type = 'Overall' 
        ORDER BY graduation_year DESC LIMIT 1
    """).fetchdf()
    acgr_val = acgr['acgr'].iloc[0] if len(acgr) > 0 else 'N/A'
    st.metric("ACGR", f"{acgr_val:.1f}%" if acgr_val != 'N/A' else acgr_val)
    st.caption("Latest cohort")

with col4:
    st.markdown("**Indicator 4**")
    st.markdown("*EL Progress*")
    el_rate = overall['el_progress_rate'] if pd.notna(overall['el_progress_rate']) else 'N/A'
    st.metric("% Progressed", f"{el_rate}%" if el_rate != 'N/A' else el_rate)
    st.caption(f"n={overall['el_students']} EL students")

with col5:
    st.markdown("**Indicator 5**")
    st.markdown("*School Quality*")
    st.metric("Chronic Absent", f"{overall['chronic_absent_rate']:.1f}%", 
              delta=None, delta_color="inverse")
    st.caption("Lower is better")

st.divider()

# Trend Analysis
st.subheader("Indicator Trends Over Time")

trend = conn.execute("""
    SELECT school_year, avg_gpa, pct_improved, el_progress_rate, chronic_absent_rate
    FROM mart_essa_accountability
    WHERE subgroup_type = 'Overall'
    ORDER BY school_year
""").fetchdf()

fig = go.Figure()
fig.add_trace(go.Scatter(x=trend['school_year'], y=trend['avg_gpa'], name='GPA', mode='lines+markers'))
fig.add_trace(go.Scatter(x=trend['school_year'], y=trend['pct_improved'], name='Growth %', mode='lines+markers'))
fig.add_trace(go.Scatter(x=trend['school_year'], y=trend['el_progress_rate'], name='EL Progress %', mode='lines+markers'))
fig.add_trace(go.Scatter(x=trend['school_year'], y=trend['chronic_absent_rate'], name='Chronic Absent %', mode='lines+markers'))
fig.update_layout(height=400, legend_title_text='Indicator')
st.plotly_chart(fig, use_container_width=True)

st.divider()

# Subgroup Comparison
st.subheader("Subgroup Performance")

subgroup_type = st.selectbox("Compare By", ['Gender', 'ESL Level'])

subgroup_data = conn.execute(f"""
    SELECT subgroup_value, student_count as n, 
           avg_gpa_suppressed as gpa,
           pct_improved_suppressed as growth,
           el_progress_rate_suppressed as el_progress,
           chronic_absent_rate_suppressed as chronic_absent,
           is_suppressed
    FROM mart_essa_accountability
    WHERE school_year = '{selected_year}'
      AND subgroup_type = '{subgroup_type}'
    ORDER BY subgroup_value
""").fetchdf()

st.caption("⚠️ Values suppressed (--) where N < 10 for FERPA compliance")

# Format for display
display_df = subgroup_data.copy()
for col in ['gpa', 'growth', 'el_progress', 'chronic_absent']:
    display_df[col] = display_df[col].apply(lambda x: '--' if pd.isna(x) else f"{x:.1f}")

st.dataframe(display_df[['subgroup_value', 'n', 'gpa', 'growth', 'el_progress', 'chronic_absent']], 
             hide_index=True, use_container_width=True,
             column_config={
                 'subgroup_value': subgroup_type,
                 'n': 'Students',
                 'gpa': 'GPA',
                 'growth': 'Growth %',
                 'el_progress': 'EL Progress %',
                 'chronic_absent': 'Chronic Absent %'
             })

# Gap highlights
st.divider()
st.subheader("Equity Highlights")

non_suppressed = subgroup_data[subgroup_data['is_suppressed'] == 0]
if len(non_suppressed) >= 2:
    col1, col2 = st.columns(2)
    
    with col1:
        if non_suppressed['gpa'].notna().any():
            max_gpa = non_suppressed.loc[non_suppressed['gpa'].idxmax()]
            min_gpa = non_suppressed.loc[non_suppressed['gpa'].idxmin()]
            st.markdown(f"**GPA Gap:** {max_gpa['gpa'] - min_gpa['gpa']:.1f} points")
            st.caption(f"Highest: {max_gpa['subgroup_value']} ({max_gpa['gpa']:.1f}) | Lowest: {min_gpa['subgroup_value']} ({min_gpa['gpa']:.1f})")
    
    with col2:
        if non_suppressed['chronic_absent'].notna().any():
            max_abs = non_suppressed.loc[non_suppressed['chronic_absent'].idxmax()]
            min_abs = non_suppressed.loc[non_suppressed['chronic_absent'].idxmin()]
            st.markdown(f"**Chronic Absence Gap:** {max_abs['chronic_absent'] - min_abs['chronic_absent']:.1f} pp")
            st.caption(f"Highest: {max_abs['subgroup_value']} ({max_abs['chronic_absent']:.1f}%) | Lowest: {min_abs['subgroup_value']} ({min_abs['chronic_absent']:.1f}%)")
