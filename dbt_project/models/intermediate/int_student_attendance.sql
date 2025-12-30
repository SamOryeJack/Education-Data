{{ config(materialized='table') }}

WITH quarterly AS (
    SELECT
        student_key,
        school_year,
        SUM(instructional_days) AS total_instructional_days,
        SUM(present_days) AS total_present_days,
        SUM(absent_days) AS total_absent_days,
        SUM(total_tardy) AS total_tardies
    FROM {{ ref('stg_attendance_quarter') }}
    GROUP BY student_key, school_year
)

SELECT
    student_key,
    school_year,
    total_instructional_days,
    total_present_days,
    total_absent_days,
    total_tardies,
    CASE 
        WHEN total_instructional_days > 0 
        THEN ROUND(total_absent_days / total_instructional_days * 100, 2)
        ELSE 0 
    END AS absence_rate,
    CASE 
        WHEN total_instructional_days > 0 
             AND (total_absent_days / total_instructional_days) >= 0.10 
        THEN 1 ELSE 0 
    END AS is_chronically_absent,
    CASE WHEN total_tardies >= 10 THEN 1 ELSE 0 END AS is_excessive_tardy
FROM quarterly
