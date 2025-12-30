

WITH assignment_summary AS (
    SELECT
        student_key,
        school_year,
        COUNT(*) AS total_assignments,
        SUM(COALESCE(is_missing, 0)) AS missing_count,
        SUM(COALESCE(is_late, 0)) AS late_count
    FROM "school_analytics"."main"."stg_assignments"
    GROUP BY student_key, school_year
)

SELECT
    student_key,
    school_year,
    total_assignments,
    missing_count,
    late_count,
    CASE 
        WHEN total_assignments > 0 
        THEN ROUND(missing_count * 100.0 / total_assignments, 2)
        ELSE 0 
    END AS missing_rate,
    CASE 
        WHEN total_assignments > 0 
             AND (missing_count * 1.0 / total_assignments) >= 0.10 
        THEN 1 ELSE 0 
    END AS is_high_missing
FROM assignment_summary