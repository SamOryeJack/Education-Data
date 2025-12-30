{{ config(materialized='table') }}

WITH daily_flags AS (
    SELECT
        student_key,
        school_year,
        SUM(has_iss) AS iss_days,
        SUM(has_oss) AS oss_days,
        SUM(has_cut) AS cut_incidents,
        SUM(has_tru) AS truancy_incidents
    FROM {{ ref('stg_attendance_daily') }}
    GROUP BY student_key, school_year
)

SELECT
    student_key,
    school_year,
    COALESCE(iss_days, 0) AS iss_days,
    COALESCE(oss_days, 0) AS oss_days,
    COALESCE(cut_incidents, 0) AS cut_incidents,
    COALESCE(truancy_incidents, 0) AS truancy_incidents,
    CASE 
        WHEN iss_days >= 1 OR oss_days >= 1 OR cut_incidents >= 2 OR truancy_incidents >= 1 
        THEN 1 ELSE 0 
    END AS is_behavior_risk
FROM daily_flags
