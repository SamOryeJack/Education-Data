# Test a simpler mermaid first
test_mermaid = '''```mermaid
erDiagram
    dim_students ||--o{ fct_grades : has
    dim_students ||--o{ fct_enrollment : has
    dim_terms ||--o{ fct_grades : has
    dim_courses ||--o{ fct_grades : has
````'''
print(test_mermaid)
````

Let me try a cleaner version that focuses on the core schema:
````python
%%writefile /content/Education-Data/README.md
# Education Data Analytics Portfolio

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://education-data-bvqfw2xtdke5dfugzzh3x3.streamlit.app/)

## Overview

Education data warehouse for 636 students across 4 years, demonstrating:
- ESSA 5-indicator accountability framework (including EL Progress tracking)
- FERPA-compliant subgroup reporting (N<10 suppression)
- ABC Early Warning System (Attendance, Behavior, Course performance)
- Cohort-based graduation tracking

*All data anonymized using Marvel character names.*

---

## Tech Stack

| Component | Technology |
|-----------|------------|
| Database | DuckDB (V2.5) |
| Dashboard | Streamlit + Plotly |
| Data Model | Star schema (dimensions + facts + marts) |
| Languages | Python, SQL |

---

## ESSA Indicators

| # | Indicator | Implementation |
|---|-----------|----------------|
| 1 | Academic Achievement | Course pass rate (≥75), Avg GPA |
| 2 | Academic Progress | Year-over-year GPA change |
| 3 | Graduation Rate | Cohort tracking (ACGR-style) |
| 4 | EL Progress | ESL level progression (intake → current) |
| 5 | School Quality | Chronic absenteeism rate (≥10%) |

---

## Database Schema
```mermaid
erDiagram
    dim_students {
        bigint student_key PK
        varchar school_id
        varchar first_name
        varchar last_name
        varchar country
        varchar esl_level
        varchar last_esl_level
        bigint is_active
    }
    dim_terms {
        bigint term_key PK
        varchar school_year
        varchar semester
    }
    dim_courses {
        bigint course_key PK
        varchar course_name
        varchar department
        varchar course_rigor
    }
    fct_grades {
        bigint student_key FK
        bigint term_key FK
        bigint course_key FK
        double fnl
        bigint is_valid_completion
    }
    fct_enrollment {
        bigint student_key FK
        bigint term_key FK
        double grade_level
        bigint is_enrolled
    }
    fct_attendance_quarter {
        bigint student_key FK
        bigint term_key FK
        double present_days
        double instructional_days
    }
    mart_essa_accountability {
        varchar school_year
        varchar subgroup_type
        double ind1_avg_gpa
        double ind4_pct_progressed
        double ind5_chronic_absent_rate
    }
    mart_student_abc_risk {
        bigint student_key FK
        bigint is_A_risk
        bigint is_B_risk
        bigint is_C_risk
        varchar risk_level
    }
    mart_completion_tracking {
        bigint student_key FK
        varchar completion_status
        bigint is_graduated
    }

    dim_students ||--o{ fct_grades : has
    dim_students ||--o{ fct_enrollment : has
    dim_students ||--o{ fct_attendance_quarter : has
    dim_students ||--o{ mart_student_abc_risk : has
    dim_students ||--o{ mart_completion_tracking : has
    dim_terms ||--o{ fct_grades : has
    dim_terms ||--o{ fct_enrollment : has
    dim_courses ||--o{ fct_grades : has
```

### Table Summary

| Layer | Tables | Rows |
|-------|--------|------|
| Dimensions | dim_students, dim_terms, dim_courses | 1,942 |
| Reference | ref_countries, ref_attendance_codes | 80 |
| Facts | fct_enrollment, fct_grades, fct_assignments, fct_attendance_* | 314,436 |
| Marts | mart_essa, mart_abc_risk, mart_completion, mart_scorecard | 2,074 |
| **Total** | **17 tables** | **318,532** |

---

## Dashboard Pages

| Page | Description |
|------|-------------|
| **ESSA Scorecard** | All 5 ESSA indicators with 4-year trends and subgroup breakdown |
| **ABC Risk** | Early warning dashboard with risk distribution and student list |
| **Student Lookup** | Individual profiles with GPA trends and risk factors |
| **Completion** | Graduation rates by cohort and program type |
| **Defense Scenarios** | Accountability response templates with trend analysis |
| **Trends** | Historical enrollment, performance, and demographic analysis |
| **Course Analysis** | Department and course-level performance metrics |

---

## Quick Start
```bash
pip install streamlit duckdb plotly pandas
cd streamlit_app
streamlit run app.py
```

---

## Project Structure
````
Education-Data/
├── README.md
├── requirements.txt
├── data/
│   └── school_analytics.duckdb
└── streamlit_app/
    ├── app.py
    └── pages/
        ├── 1_ESSA_Scorecard.py
        ├── 2_ABC_Risk.py
        ├── 3_Student_Lookup.py
        ├── 4_Completion.py
        ├── 5_Defense_Scenarios.py
        ├── 6_Trends.py
        └── 7_Course_Analysis.py
