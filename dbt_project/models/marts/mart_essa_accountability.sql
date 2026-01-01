{{ config(materialized='table') }}

WITH student_year_base AS (
    SELECT 
        m.student_key,
        m.school_year,
        m.gender,
        m.country,
        m.is_chronically_absent,
        m.avg_final_score,
        m.pass_rate,
        e.esl_level_end as esl_level,
        e.progressed as esl_progressed
    FROM {{ ref('mart_student_accountability') }} m
    LEFT JOIN {{ source('main', 'fct_esl_progression') }} e 
        ON m.student_key = e.student_key AND m.school_year = e.school_year
),

with_growth AS (
    SELECT 
        s.*,
        LAG(s.avg_final_score) OVER (PARTITION BY s.student_key ORDER BY s.school_year) as prior_year_gpa,
        s.avg_final_score - LAG(s.avg_final_score) OVER (PARTITION BY s.student_key ORDER BY s.school_year) as gpa_change
    FROM student_year_base s
),

overall AS (
    SELECT school_year, 'Overall' as subgroup_type, 'All Students' as subgroup_value,
        COUNT(*) as student_count,
        ROUND(AVG(avg_final_score), 1) as avg_gpa,
        ROUND(AVG(pass_rate), 1) as avg_pass_rate,
        COUNT(gpa_change) as students_with_prior,
        SUM(CASE WHEN gpa_change > 0 THEN 1 ELSE 0 END) as improved_count,
        COUNT(CASE WHEN esl_level != 'Direct' THEN 1 END) as el_students,
        SUM(COALESCE(esl_progressed, 0)) as el_progressed,
        SUM(is_chronically_absent) as chronic_absent_count
    FROM with_growth GROUP BY school_year
),

by_gender AS (
    SELECT school_year, 'Gender' as subgroup_type, gender as subgroup_value,
        COUNT(*) as student_count,
        ROUND(AVG(avg_final_score), 1) as avg_gpa,
        ROUND(AVG(pass_rate), 1) as avg_pass_rate,
        COUNT(gpa_change) as students_with_prior,
        SUM(CASE WHEN gpa_change > 0 THEN 1 ELSE 0 END) as improved_count,
        COUNT(CASE WHEN esl_level != 'Direct' THEN 1 END) as el_students,
        SUM(COALESCE(esl_progressed, 0)) as el_progressed,
        SUM(is_chronically_absent) as chronic_absent_count
    FROM with_growth WHERE gender IS NOT NULL GROUP BY school_year, gender
),

by_esl AS (
    SELECT school_year, 'ESL Level' as subgroup_type, COALESCE(esl_level, 'Unknown') as subgroup_value,
        COUNT(*) as student_count,
        ROUND(AVG(avg_final_score), 1) as avg_gpa,
        ROUND(AVG(pass_rate), 1) as avg_pass_rate,
        COUNT(gpa_change) as students_with_prior,
        SUM(CASE WHEN gpa_change > 0 THEN 1 ELSE 0 END) as improved_count,
        COUNT(CASE WHEN esl_level != 'Direct' THEN 1 END) as el_students,
        SUM(COALESCE(esl_progressed, 0)) as el_progressed,
        SUM(is_chronically_absent) as chronic_absent_count
    FROM with_growth GROUP BY school_year, COALESCE(esl_level, 'Unknown')
),

combined AS (
    SELECT * FROM overall UNION ALL 
    SELECT * FROM by_gender UNION ALL 
    SELECT * FROM by_esl
)

SELECT 
    school_year,
    subgroup_type,
    subgroup_value,
    student_count,
    CASE WHEN student_count < 10 THEN 1 ELSE 0 END as is_suppressed,
    -- Indicator 1: Achievement
    avg_gpa,
    avg_pass_rate,
    CASE WHEN student_count < 10 THEN NULL ELSE avg_gpa END as avg_gpa_suppressed,
    -- Indicator 2: Growth
    students_with_prior,
    improved_count,
    ROUND(improved_count * 100.0 / NULLIF(students_with_prior, 0), 1) as pct_improved,
    CASE WHEN students_with_prior < 10 THEN NULL 
         ELSE ROUND(improved_count * 100.0 / NULLIF(students_with_prior, 0), 1) END as pct_improved_suppressed,
    -- Indicator 4: EL Progress
    el_students,
    el_progressed,
    ROUND(el_progressed * 100.0 / NULLIF(el_students, 0), 1) as el_progress_rate,
    CASE WHEN el_students < 10 THEN NULL 
         ELSE ROUND(el_progressed * 100.0 / NULLIF(el_students, 0), 1) END as el_progress_rate_suppressed,
    -- Indicator 5: Chronic Absence
    chronic_absent_count,
    ROUND(chronic_absent_count * 100.0 / student_count, 1) as chronic_absent_rate,
    CASE WHEN student_count < 10 THEN NULL 
         ELSE ROUND(chronic_absent_count * 100.0 / student_count, 1) END as chronic_absent_rate_suppressed
FROM combined
