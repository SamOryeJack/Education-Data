{{ config(materialized='table') }}

WITH cohort_base AS (
    SELECT 
        g.cohort_year,
        g.expected_grad_year,
        g.student_key,
        g.in_graduation_cohort,
        g.final_status,
        d.gender,
        d.country,
        d.esl_level
    FROM {{ source('main', 'fct_graduation_outcomes') }} g
    JOIN {{ source('main', 'dim_students') }} d ON g.student_key = d.student_key
    WHERE g.in_graduation_cohort = 1
      AND g.expected_grad_year <= 2025
),

overall AS (
    SELECT 
        cohort_year, 'Overall' as subgroup_type, 'All Students' as subgroup_value,
        COUNT(*) as cohort_count,
        SUM(CASE WHEN final_status LIKE 'Graduated%' THEN 1 ELSE 0 END) as graduates,
        SUM(CASE WHEN final_status = 'Transferred (Documented)' THEN 1 ELSE 0 END) as transfers_out
    FROM cohort_base GROUP BY cohort_year
),

by_gender AS (
    SELECT 
        cohort_year, 'Gender' as subgroup_type, gender as subgroup_value,
        COUNT(*) as cohort_count,
        SUM(CASE WHEN final_status LIKE 'Graduated%' THEN 1 ELSE 0 END) as graduates,
        SUM(CASE WHEN final_status = 'Transferred (Documented)' THEN 1 ELSE 0 END) as transfers_out
    FROM cohort_base WHERE gender IS NOT NULL GROUP BY cohort_year, gender
),

by_country AS (
    SELECT 
        cohort_year, 'Country' as subgroup_type, country as subgroup_value,
        COUNT(*) as cohort_count,
        SUM(CASE WHEN final_status LIKE 'Graduated%' THEN 1 ELSE 0 END) as graduates,
        SUM(CASE WHEN final_status = 'Transferred (Documented)' THEN 1 ELSE 0 END) as transfers_out
    FROM cohort_base WHERE country IS NOT NULL GROUP BY cohort_year, country
),

by_esl AS (
    SELECT 
        cohort_year, 'ESL Level' as subgroup_type,
        CASE 
            WHEN esl_level IN ('3', 'Level III') THEN 'Level III'
            WHEN esl_level IN ('2', 'Level II') THEN 'Level II'
            WHEN esl_level IN ('1', 'Level I') THEN 'Level I'
            WHEN esl_level IN ('Direct', 'Direct Admission', 'D') THEN 'Direct'
            ELSE 'Unknown'
        END as subgroup_value,
        COUNT(*) as cohort_count,
        SUM(CASE WHEN final_status LIKE 'Graduated%' THEN 1 ELSE 0 END) as graduates,
        SUM(CASE WHEN final_status = 'Transferred (Documented)' THEN 1 ELSE 0 END) as transfers_out
    FROM cohort_base
    GROUP BY cohort_year, 
        CASE 
            WHEN esl_level IN ('3', 'Level III') THEN 'Level III'
            WHEN esl_level IN ('2', 'Level II') THEN 'Level II'
            WHEN esl_level IN ('1', 'Level I') THEN 'Level I'
            WHEN esl_level IN ('Direct', 'Direct Admission', 'D') THEN 'Direct'
            ELSE 'Unknown'
        END
),

combined AS (
    SELECT * FROM overall UNION ALL 
    SELECT * FROM by_gender UNION ALL 
    SELECT * FROM by_country UNION ALL 
    SELECT * FROM by_esl
)

SELECT 
    cohort_year,
    cohort_year + 4 as expected_grad_year,
    subgroup_type,
    subgroup_value,
    cohort_count,
    graduates,
    transfers_out,
    cohort_count - transfers_out as adjusted_cohort,
    ROUND(graduates * 100.0 / NULLIF(cohort_count - transfers_out, 0), 1) as acgr,
    CASE WHEN cohort_count < 10 THEN 1 ELSE 0 END as is_suppressed,
    CASE WHEN cohort_count < 10 THEN NULL 
         ELSE ROUND(graduates * 100.0 / NULLIF(cohort_count - transfers_out, 0), 1) 
    END as acgr_suppressed
FROM combined
