{{ config(materialized='view') }}

WITH source AS (
    SELECT 
        q.*,
        t.school_year
    FROM {{ source('main', 'fct_attendance_quarter') }} q
    JOIN {{ source('main', 'dim_terms') }} t ON q.term_key = t.term_key
)

SELECT
    att_quarter_key,
    student_key,
    term_key,
    school_year,
    quarter,
    instructional_days,
    present_days,
    total_absent,
    total_tardy,
    instructional_days - present_days AS absent_days,
    CASE 
        WHEN instructional_days > 0 
        THEN ROUND((instructional_days - present_days) / instructional_days * 100, 2)
        ELSE 0 
    END AS absence_rate
FROM source
