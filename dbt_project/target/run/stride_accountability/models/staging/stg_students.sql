
  
  create view "school_analytics"."main"."stg_students__dbt_tmp" as (
    

WITH source AS (
    SELECT * FROM "school_analytics"."main"."dim_students"
)

SELECT
    student_key,
    school_id,
    first_name,
    last_name,
    CASE 
        WHEN first_name = '' THEN last_name 
        ELSE first_name || ' ' || last_name 
    END AS full_name,
    pref_name,
    gender,
    country,
    first_intake,
    accepted_grade,
    program_type,
    esl_level,
    status
FROM source
  );
