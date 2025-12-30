{{ config(materialized='table') }}

WITH base AS (
    SELECT * FROM {{ ref('mart_student_accountability') }}
),

-- Overall by year
overall AS (
    SELECT
        school_year,
        'Overall' AS subgroup_type,
        'All Students' AS subgroup_value,
        COUNT(*) AS student_count,
        ROUND(AVG(absence_rate), 2) AS avg_absence_rate,
        ROUND(SUM(is_chronically_absent) * 100.0 / COUNT(*), 2) AS pct_chronically_absent,
        ROUND(SUM(is_behavior_risk) * 100.0 / COUNT(*), 2) AS pct_behavior_risk,
        ROUND(SUM(is_failing_any) * 100.0 / COUNT(*), 2) AS pct_failing_any,
        ROUND(SUM(is_at_risk) * 100.0 / COUNT(*), 2) AS pct_at_risk,
        ROUND(AVG(avg_final_score), 2) AS avg_gpa
    FROM base
    GROUP BY school_year
),

-- By gender
by_gender AS (
    SELECT
        school_year,
        'Gender' AS subgroup_type,
        gender AS subgroup_value,
        COUNT(*) AS student_count,
        ROUND(AVG(absence_rate), 2) AS avg_absence_rate,
        ROUND(SUM(is_chronically_absent) * 100.0 / COUNT(*), 2) AS pct_chronically_absent,
        ROUND(SUM(is_behavior_risk) * 100.0 / COUNT(*), 2) AS pct_behavior_risk,
        ROUND(SUM(is_failing_any) * 100.0 / COUNT(*), 2) AS pct_failing_any,
        ROUND(SUM(is_at_risk) * 100.0 / COUNT(*), 2) AS pct_at_risk,
        ROUND(AVG(avg_final_score), 2) AS avg_gpa
    FROM base
    WHERE gender IS NOT NULL
    GROUP BY school_year, gender
),

-- By program type
by_program AS (
    SELECT
        school_year,
        'Program' AS subgroup_type,
        program_type AS subgroup_value,
        COUNT(*) AS student_count,
        ROUND(AVG(absence_rate), 2) AS avg_absence_rate,
        ROUND(SUM(is_chronically_absent) * 100.0 / COUNT(*), 2) AS pct_chronically_absent,
        ROUND(SUM(is_behavior_risk) * 100.0 / COUNT(*), 2) AS pct_behavior_risk,
        ROUND(SUM(is_failing_any) * 100.0 / COUNT(*), 2) AS pct_failing_any,
        ROUND(SUM(is_at_risk) * 100.0 / COUNT(*), 2) AS pct_at_risk,
        ROUND(AVG(avg_final_score), 2) AS avg_gpa
    FROM base
    WHERE program_type IS NOT NULL
    GROUP BY school_year, program_type
),

-- By boarding status
by_boarding AS (
    SELECT
        school_year,
        'Boarding' AS subgroup_type,
        CASE WHEN is_boarding = 1 THEN 'Boarding' ELSE 'Non-Boarding' END AS subgroup_value,
        COUNT(*) AS student_count,
        ROUND(AVG(absence_rate), 2) AS avg_absence_rate,
        ROUND(SUM(is_chronically_absent) * 100.0 / COUNT(*), 2) AS pct_chronically_absent,
        ROUND(SUM(is_behavior_risk) * 100.0 / COUNT(*), 2) AS pct_behavior_risk,
        ROUND(SUM(is_failing_any) * 100.0 / COUNT(*), 2) AS pct_failing_any,
        ROUND(SUM(is_at_risk) * 100.0 / COUNT(*), 2) AS pct_at_risk,
        ROUND(AVG(avg_final_score), 2) AS avg_gpa
    FROM base
    WHERE is_boarding IS NOT NULL
    GROUP BY school_year, is_boarding
)

SELECT * FROM overall
UNION ALL
SELECT * FROM by_gender
UNION ALL
SELECT * FROM by_program
UNION ALL
SELECT * FROM by_boarding
ORDER BY school_year, subgroup_type, subgroup_value
