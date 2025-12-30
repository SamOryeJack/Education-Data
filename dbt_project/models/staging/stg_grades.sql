{{ config(materialized='view') }}

WITH source AS (
    SELECT 
        g.*,
        t.school_year
    FROM {{ source('main', 'fct_grades') }} g
    JOIN {{ source('main', 'dim_terms') }} t ON g.term_key = t.term_key
)

SELECT
    grade_key,
    student_key,
    course_key,
    term_key,
    school_year,
    teacher,
    q1_score,
    q2_score,
    q3_score,
    q4_score,
    final_score,
    CASE WHEN final_score >= 75 THEN 1 ELSE 0 END AS is_passing,
    CASE WHEN final_score < 75 THEN 1 ELSE 0 END AS is_failing
FROM source
