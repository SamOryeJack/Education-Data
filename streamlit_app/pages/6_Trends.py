"""
Trends
Historical performance analysis across years
"""
import streamlit as st
import duckdb
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

st.set_page_config(page_title="Trends", page_icon="📈", layout="wide")

DB_PATH = 'data/school_analytics.duckdb'

def get_connection():
    return duckdb.connect(DB_PATH, read_only=True)

conn = get_connection()

# Load ESSA data for overall trends
essa_df = conn.execute("""
    SELECT * FROM mart_essa_accountability 
    WHERE subgroup_type = 'Overall' 
    ORDER BY school_year
""").fetchdf()

# Load enrollment by year
enrollment_df = conn.execute("""
    SELECT 
        t.school_year,
        COUNT(DISTINCT e.student_key) as students
    FROM fct_enrollment e
    JOIN dim_terms t ON e.term_key = t.term_key
    WHERE e.is_enrolled = 1
    GROUP BY t.school_year
    ORDER BY t.school_year
""").fetchdf()

# Load grade distribution by year (valid completions only)
grades_df = conn.execute("""
    SELECT 
        t.school_year,
        CASE 
            WHEN g.fnl >= 90 THEN 'A (90-100)'
            WHEN g.fnl >= 80 THEN 'B (80-89)'
            WHEN g.fnl >= 75 THEN 'C (75-79)'
            WHEN g.fnl >= 65 THEN 'D (65-74)'
            ELSE 'F (<65)'
        END as grade_band,
        COUNT(*) as count
    FROM fct_grades g
    JOIN dim_terms t ON g.term_key = t.term_key
    WHERE g.fnl IS NOT NULL AND g.is_valid_completion = 1
    GROUP BY t.school_year, grade_band
    ORDER BY t.school_year
""").fetchdf()

# Load country trends
country_df = conn.execute("""
    SELECT 
        t.school_year,
        s.country,
        COUNT(DISTINCT e.student_key) as students
    FROM fct_enrollment e
    JOIN dim_terms t ON e.term_key = t.term_key
    JOIN dim_students s ON e.student_key = s.student_key
    WHERE e.is_enrolled = 1
    GROUP BY t.school_year, s.country
    ORDER BY t.school_year, students DESC
""").fetchdf()

conn.close()

st.title("Trends")
st.markdown("Historical performance analysis across school years")

st.divider()

# Enrollment Trend
st.subheader("Enrollment by Year")

fig_enroll = go.Figure()
fig_enroll.add_trace(go.Bar(
    x=enrollment_df['school_year'],
    y=enrollment_df['students'],
    text=enrollment_df['students'],
    textposition='auto',
    marker_color='#1f77b4'
))
fig_enroll.update_layout(
    xaxis_title="School Year",
    yaxis_title="Students Enrolled",
    height=300
)
st.plotly_chart(fig_enroll, use_container_width=True)

st.divider()

# Key Metrics Trends
st.subheader("Key Metrics Over Time")

col1, col2 = st.columns(2)

with col1:
    # GPA and Pass Rate
    fig_academic = go.Figure()
    fig_academic.add_trace(go.Scatter(
        x=essa_df['school_year'], 
        y=essa_df['ind1_avg_gpa'],
        name='Avg GPA',
        mode='lines+markers',
        line=dict(width=3)
    ))
    fig_academic.add_trace(go.Scatter(
        x=essa_df['school_year'], 
        y=essa_df['ind1_course_pass_rate'],
        name='Pass Rate %',
        mode='lines+markers',
        line=dict(width=3)
    ))
    fig_academic.update_layout(
        title="Academic Performance",
        xaxis_title="School Year",
        yaxis_title="Score / Percentage",
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        height=350
    )
    st.plotly_chart(fig_academic, use_container_width=True)

with col2:
    # Chronic Absence
    fig_absence = go.Figure()
    fig_absence.add_trace(go.Scatter(
        x=essa_df['school_year'],
        y=essa_df['ind5_chronic_absent_rate'],
        name='Chronic Absence %',
        mode='lines+markers',
        line=dict(width=3, color='#d62728'),
        fill='tozeroy',
        fillcolor='rgba(214, 39, 40, 0.2)'
    ))
    fig_absence.add_hline(y=10, line_dash="dash", line_color="green",
                          annotation_text="10% Target")
    fig_absence.update_layout(
        title="Chronic Absenteeism",
        xaxis_title="School Year",
        yaxis_title="Rate (%)",
        height=350
    )
    st.plotly_chart(fig_absence, use_container_width=True)

st.divider()

# Grade Distribution Trend
st.subheader("Grade Distribution by Year")

# Pivot for stacked bar
grade_pivot = grades_df.pivot(index='school_year', columns='grade_band', values='count').fillna(0)

# Reorder columns
grade_order = ['A (90-100)', 'B (80-89)', 'C (75-79)', 'D (65-74)', 'F (<65)']
grade_pivot = grade_pivot[[c for c in grade_order if c in grade_pivot.columns]]

fig_grades = go.Figure()
colors = {'A (90-100)': '#2ca02c', 'B (80-89)': '#98df8a', 'C (75-79)': '#ffbb78', 
          'D (65-74)': '#ff7f0e', 'F (<65)': '#d62728'}

for col in grade_pivot.columns:
    fig_grades.add_trace(go.Bar(
        x=grade_pivot.index,
        y=grade_pivot[col],
        name=col,
        marker_color=colors.get(col, '#1f77b4')
    ))

fig_grades.update_layout(
    barmode='stack',
    xaxis_title="School Year",
    yaxis_title="Course Grades",
    legend=dict(orientation="h", yanchor="bottom", y=1.02),
    height=400
)
st.plotly_chart(fig_grades, use_container_width=True)

st.divider()

# Top Countries by Year
st.subheader("Top 10 Countries by Year")

year_select = st.selectbox("Select Year", sorted(country_df['school_year'].unique(), reverse=True))

year_countries = country_df[country_df['school_year'] == year_select].nlargest(10, 'students')

fig_country = go.Figure(data=[
    go.Bar(
        x=year_countries['students'],
        y=year_countries['country'],
        orientation='h',
        marker_color='#1f77b4'
    )
])
fig_country.update_layout(
    xaxis_title="Students",
    yaxis=dict(autorange="reversed"),
    height=400
)
st.plotly_chart(fig_country, use_container_width=True)

st.divider()

# Summary Table
st.subheader("Year-Over-Year Summary")

summary_df = essa_df[['school_year', 'student_count', 'ind1_avg_gpa', 'ind1_course_pass_rate',
                      'ind2_pct_improved', 'ind3_graduation_rate', 'ind5_chronic_absent_rate']].copy()

summary_df.columns = ['Year', 'N', 'Avg GPA', 'Pass Rate', '% Improved', 'Grad Rate', 'Chronic Abs']

# Format numeric columns
for col in ['Avg GPA', 'Pass Rate', '% Improved', 'Grad Rate', 'Chronic Abs']:
    summary_df[col] = summary_df[col].apply(lambda x: f"{x:.1f}" if pd.notna(x) else 'N/A')

st.dataframe(summary_df, use_container_width=True, hide_index=True)
