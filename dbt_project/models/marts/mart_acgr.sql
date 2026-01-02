{{ config(materialized='table') }}

WITH graduates AS (
    SELECT 
        g.graduation_year,
        g.student_key,
        d.gender,
        d.country,
        d.esl_level
    FROM {{ source('main', 'fct_graduation_outcomes') }} g
    JOIN {{ source('main', 'dim_students') }} d ON g.student_key = d.student_key
    WHERE g.final_status = 'Graduated'
      AND g.in_graduation_cohort = 1
),

overall AS (
    SELECT graduation_year, 'Overall' as subgroup_type, 'All Students' as subgroup_value,
        COUNT(*) as graduates
    FROM graduates GROUP BY graduation_year
),

by_gender AS (
    SELECT graduation_year, 'Gender' as subgroup_type, gender as subgroup_value,
        COUNT(*) as graduates
    FROM graduates WHERE gender IS NOT NULL GROUP BY graduation_year, gender
),

by_country AS (
    SELECT graduation_year, 'Country' as subgroup_type, country as subgroup_value,
        COUNT(*) as graduates
    FROM graduates WHERE country IS NOT NULL GROUP BY graduation_year, country
),

by_esl AS (
    SELECT graduation_year, 'ESL Level' as subgroup_type,
        CASE 
            WHEN esl_level IN ('3', 'Level III') THEN 'Level III'
            WHEN esl_level IN ('2', 'Level II') THEN 'Level II'
            WHEN esl_level IN ('1', 'Level I') THEN 'Level I'
            WHEN esl_level IN ('Direct', 'Direct Admission', 'D') THEN 'Direct'
            ELSE 'Unknown'
        END as subgroup_value,
        COUNT(*) as graduates
    FROM graduates
    GROUP BY graduation_year, 
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
    graduation_year,
    subgroup_type,
    subgroup_value,
    graduates,
    graduates as cohort_count,
    100.0 as acgr,
    CASE WHEN graduates < 10 THEN 1 ELSE 0 END as is_suppressed,
    CASE WHEN graduates < 10 THEN NULL ELSE 100.0 END as acgr_suppressed
FROM combined
