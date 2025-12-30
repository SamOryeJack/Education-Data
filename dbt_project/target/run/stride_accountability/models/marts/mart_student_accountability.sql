
  
    
    

    create  table
      "school_analytics"."main"."mart_student_accountability__dbt_tmp"
  
    as (
      

WITH students AS (
    SELECT * FROM "school_analytics"."main"."stg_students"
),

enrollment AS (
    SELECT 
        e.student_key,
        t.school_year,
        e.grade_level,
        e.is_boarding,
        e.housing_type
    FROM "school_analytics"."main"."fct_student_term_enrollment" e
    JOIN "school_analytics"."main"."dim_terms" t ON e.term_key = t.term_key
    WHERE t.term_name LIKE 'Fall%'
),

attendance AS (
    SELECT * FROM "school_analytics"."main"."int_student_attendance"
),

behavior AS (
    SELECT * FROM "school_analytics"."main"."int_student_behavior"
),

courses AS (
    SELECT * FROM "school_analytics"."main"."int_student_course_performance"
),

assignments AS (
    SELECT * FROM "school_analytics"."main"."int_student_assignments"
)

SELECT
    -- Student info
    s.student_key,
    s.school_id,
    s.full_name,
    e.school_year,
    s.gender,
    s.country,
    s.program_type,
    e.grade_level,
    e.is_boarding,
    e.housing_type,
    
    -- Attendance metrics
    a.total_instructional_days,
    a.total_present_days,
    a.total_absent_days,
    a.absence_rate,
    a.total_tardies,
    a.is_chronically_absent,
    a.is_excessive_tardy,
    
    -- Behavior metrics
    COALESCE(b.iss_days, 0) AS iss_days,
    COALESCE(b.oss_days, 0) AS oss_days,
    COALESCE(b.cut_incidents, 0) AS cut_incidents,
    COALESCE(b.truancy_incidents, 0) AS truancy_incidents,
    COALESCE(b.is_behavior_risk, 0) AS is_behavior_risk,
    
    -- Course metrics
    c.courses_taken,
    c.courses_passed,
    c.courses_failed,
    c.pass_rate,
    c.avg_final_score,
    c.is_failing_any,
    
    -- Assignment metrics
    asn.total_assignments,
    asn.missing_count,
    asn.late_count,
    asn.missing_rate,
    asn.is_high_missing,
    
    -- ABC Risk Score
    COALESCE(a.is_chronically_absent, 0) 
        + COALESCE(b.is_behavior_risk, 0) 
        + COALESCE(c.is_failing_any, 0) AS abc_risk_score,
    
    CASE 
        WHEN (COALESCE(a.is_chronically_absent, 0) 
              + COALESCE(b.is_behavior_risk, 0) 
              + COALESCE(c.is_failing_any, 0)) >= 2 
        THEN 1 ELSE 0 
    END AS is_at_risk

FROM enrollment e
JOIN students s ON e.student_key = s.student_key
LEFT JOIN attendance a ON e.student_key = a.student_key AND e.school_year = a.school_year
LEFT JOIN behavior b ON e.student_key = b.student_key AND e.school_year = b.school_year
LEFT JOIN courses c ON e.student_key = c.student_key AND e.school_year = c.school_year
LEFT JOIN assignments asn ON e.student_key = asn.student_key AND e.school_year = asn.school_year
    );
  
  