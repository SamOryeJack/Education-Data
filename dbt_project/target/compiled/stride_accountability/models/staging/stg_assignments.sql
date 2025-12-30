

WITH source AS (
    SELECT 
        a.*,
        t.school_year
    FROM "school_analytics"."main"."fct_assignments" a
    JOIN "school_analytics"."main"."dim_terms" t ON a.term_key = t.term_key
)

SELECT
    assignment_key,
    student_key,
    course_key,
    term_key,
    school_year,
    quarter,
    category,
    assignment_name,
    due_date,
    points_earned,
    points_possible,
    is_missing,
    is_late,
    CASE 
        WHEN points_possible > 0 
        THEN ROUND(points_earned / points_possible * 100, 2)
        ELSE NULL 
    END AS score_pct
FROM source