

WITH source AS (
    SELECT 
        d.*,
        t.school_year
    FROM "school_analytics"."main"."fct_attendance_daily" d
    JOIN "school_analytics"."main"."dim_terms" t ON d.term_key = t.term_key
)

SELECT
    att_daily_key,
    student_key,
    term_key,
    school_year,
    date,
    day_of_week,
    cycle_day,
    -- Period codes
    period_0820,
    period_0905,
    homeroom,
    period_1005,
    period_1050,
    period_1135,
    period_1220,
    period_0105,
    period_0150,
    -- Behavior flags
    CASE WHEN period_0820 = 'ISS' OR period_0905 = 'ISS' OR homeroom = 'ISS' 
         OR period_1005 = 'ISS' OR period_1050 = 'ISS' OR period_1135 = 'ISS'
         OR period_1220 = 'ISS' OR period_0105 = 'ISS' OR period_0150 = 'ISS' 
         THEN 1 ELSE 0 END AS has_iss,
    CASE WHEN period_0820 = 'OSS' OR period_0905 = 'OSS' OR homeroom = 'OSS'
         OR period_1005 = 'OSS' OR period_1050 = 'OSS' OR period_1135 = 'OSS'
         OR period_1220 = 'OSS' OR period_0105 = 'OSS' OR period_0150 = 'OSS'
         THEN 1 ELSE 0 END AS has_oss,
    CASE WHEN period_0820 = 'Cut' OR period_0905 = 'Cut' OR homeroom = 'Cut'
         OR period_1005 = 'Cut' OR period_1050 = 'Cut' OR period_1135 = 'Cut'
         OR period_1220 = 'Cut' OR period_0105 = 'Cut' OR period_0150 = 'Cut'
         THEN 1 ELSE 0 END AS has_cut,
    CASE WHEN period_0820 = 'TRU' OR period_0905 = 'TRU' OR homeroom = 'TRU'
         OR period_1005 = 'TRU' OR period_1050 = 'TRU' OR period_1135 = 'TRU'
         OR period_1220 = 'TRU' OR period_0105 = 'TRU' OR period_0150 = 'TRU'
         THEN 1 ELSE 0 END AS has_tru
FROM source