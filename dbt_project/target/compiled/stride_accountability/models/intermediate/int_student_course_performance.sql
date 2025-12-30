

WITH course_summary AS (
    SELECT
        student_key,
        school_year,
        COUNT(*) AS courses_taken,
        SUM(is_passing) AS courses_passed,
        SUM(is_failing) AS courses_failed,
        ROUND(AVG(final_score), 2) AS avg_final_score
    FROM "school_analytics"."main"."stg_grades"
    WHERE final_score IS NOT NULL
    GROUP BY student_key, school_year
)

SELECT
    student_key,
    school_year,
    courses_taken,
    courses_passed,
    courses_failed,
    CASE 
        WHEN courses_taken > 0 
        THEN ROUND(courses_passed * 100.0 / courses_taken, 2)
        ELSE 0 
    END AS pass_rate,
    avg_final_score,
    CASE WHEN courses_failed > 0 THEN 1 ELSE 0 END AS is_failing_any
FROM course_summary