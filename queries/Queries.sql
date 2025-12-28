-- ============================================================================
-- AMERIGO STUDENT ANALYTICS - SAMPLE QUERIES
-- Database: amerigo_analytics.db (SQLite)
-- Records: 312,439 across 10 tables
-- Coverage: 636 students, 4 school years (2022-2026)
-- ============================================================================


-- ============================================================================
-- YEAR-OVER-YEAR PERFORMANCE METRICS
-- ============================================================================

-- Average Q1 Grade by School Year
-- Shows academic performance trends across 4 years
SELECT 
    t.school_year,
    ROUND(AVG(g.q1_score), 1) as avg_q1
FROM fct_grades g
JOIN dim_terms t ON g.term_key = t.term_key
WHERE g.q1_score IS NOT NULL
GROUP BY t.school_year
ORDER BY t.term_order;


-- Pass Rate by School Year (≥75 threshold)
-- Accountability metric: percentage of grades meeting passing standard
SELECT 
    t.school_year,
    ROUND(100.0 * SUM(CASE WHEN g.q1_score >= 75 THEN 1 ELSE 0 END) / COUNT(*), 1) as pass_rate
FROM fct_grades g
JOIN dim_terms t ON g.term_key = t.term_key
WHERE g.q1_score IS NOT NULL
GROUP BY t.school_year
ORDER BY t.term_order;


-- Average Absent Periods per Student (Q1 only)
-- Attendance tracking for chronic absenteeism analysis
SELECT 
    t.school_year,
    ROUND(AVG(q.total_absent), 1) as avg_absent_periods
FROM fct_attendance_quarter q
JOIN dim_terms t ON q.term_key = t.term_key
WHERE q.quarter = 'Q1'
GROUP BY t.school_year
ORDER BY t.term_order;


-- ============================================================================
-- ENROLLMENT AND DEMOGRAPHICS
-- ============================================================================

-- International Students by Country (excluding US)
-- Shows diversity of student population across 23 countries
SELECT 
    country, 
    COUNT(*) as count
FROM dim_students
WHERE status = 'Active' 
  AND country IS NOT NULL 
  AND country != 'United States'
GROUP BY country
ORDER BY count DESC;


-- Program Type Distribution
-- Breakdown of Diploma vs Exchange students
SELECT 
    program_type, 
    COUNT(*) as count,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 1) as pct
FROM dim_students
WHERE program_type IS NOT NULL 
  AND status = 'Active'
GROUP BY program_type
ORDER BY count DESC;


-- ============================================================================
-- COURSE ANALYSIS
-- ============================================================================

-- Course Rigor Distribution by Year
-- Tracks AP, Honors, Regular enrollment trends
SELECT 
    t.school_year,
    c.course_rigor,
    COUNT(*) as enrollments
FROM fct_grades g
JOIN dim_courses c ON g.course_key = c.course_key
JOIN dim_terms t ON g.term_key = t.term_key
WHERE g.q1_score IS NOT NULL
GROUP BY t.school_year, c.course_rigor
ORDER BY t.term_order, c.course_rigor;


-- ============================================================================
-- COMPREHENSIVE TREND ANALYSIS
-- ============================================================================

-- Enrollment and Performance Trends
-- Multi-metric view: student count, average grades, failing count, pass rate
SELECT 
    t.school_year,
    COUNT(DISTINCT g.student_key) as total_students,
    ROUND(AVG(g.q1_score), 1) as avg_q1,
    ROUND(AVG(g.q2_score), 1) as avg_q2,
    SUM(CASE WHEN g.q1_score < 75 THEN 1 ELSE 0 END) as failing_grades,
    ROUND(100.0 * SUM(CASE WHEN g.q1_score >= 75 THEN 1 ELSE 0 END) / COUNT(*), 1) as pass_rate
FROM fct_grades g
JOIN dim_terms t ON g.term_key = t.term_key
WHERE g.q1_score IS NOT NULL
GROUP BY t.school_year
ORDER BY t.school_year;


-- ============================================================================
-- RETENTION RISK ANALYSIS
-- ============================================================================

-- Missing Homework Rate by Length of Enrollment
-- Hypothesis: Students who stay longer develop better habits
-- Finding: 3x difference between short-term (1.8%) and long-term (0.6%) students
SELECT 
    terms_enrolled,
    ROUND(AVG(missing_pct), 1) as avg_missing_pct,
    COUNT(*) as num_students
FROM (
    SELECT 
        s.student_key,
        COUNT(DISTINCT e.term_key) as terms_enrolled,
        COUNT(a.assignment_key) as total_assignments,
        SUM(a.is_missing) as missing_assignments,
        ROUND(100.0 * SUM(a.is_missing) / COUNT(a.assignment_key), 1) as missing_pct
    FROM dim_students s
    JOIN fct_student_term_enrollment e ON s.student_key = e.student_key
    JOIN fct_assignments a ON s.student_key = a.student_key
    GROUP BY s.student_key
    HAVING total_assignments >= 20
) student_metrics
GROUP BY terms_enrolled
ORDER BY terms_enrolled;


-- ============================================================================
-- AT-RISK IDENTIFICATION
-- ============================================================================

-- Students with Any Failing Grade by Year
-- Identifies at-risk population for intervention
SELECT 
    t.school_year,
    COUNT(DISTINCT CASE WHEN g.q1_score < 75 THEN g.student_key END) as at_risk_students,
    COUNT(DISTINCT g.student_key) as total_students,
    ROUND(100.0 * COUNT(DISTINCT CASE WHEN g.q1_score < 75 THEN g.student_key END) / 
          COUNT(DISTINCT g.student_key), 1) as at_risk_pct
FROM fct_grades g
JOIN dim_terms t ON g.term_key = t.term_key
WHERE g.q1_score IS NOT NULL
GROUP BY t.school_year
ORDER BY t.term_order;


-- At-Risk Student Detail (Current Year)
-- Lists students meeting at-risk criteria for intervention planning
SELECT 
    s.first_name,
    s.last_name,
    s.program_type,
    COUNT(CASE WHEN g.q1_score < 75 THEN 1 END) as failing_courses,
    ROUND(AVG(g.q1_score), 1) as avg_grade
FROM dim_students s
JOIN fct_grades g ON s.student_key = g.student_key
WHERE g.term_key = 7  -- 2025-26 Fall term
  AND g.q1_score IS NOT NULL
GROUP BY s.student_key
HAVING failing_courses >= 2 OR avg_grade < 75
ORDER BY failing_courses DESC, avg_grade ASC;


-- ============================================================================
-- ATTENDANCE ANALYSIS
-- ============================================================================

-- Attendance Summary by Quarter
-- Shows seasonal patterns in absenteeism
SELECT 
    t.school_year,
    q.quarter,
    COUNT(DISTINCT q.student_key) as students,
    ROUND(AVG(q.instructional_days), 0) as school_days,
    ROUND(AVG(q.present_days), 1) as avg_present,
    ROUND(AVG(q.total_absent), 1) as avg_absent_periods,
    ROUND(AVG(q.total_tardy), 1) as avg_tardy
FROM fct_attendance_quarter q
JOIN dim_terms t ON q.term_key = t.term_key
WHERE q.quarter IN ('Q1', 'Q2')
GROUP BY t.school_year, q.quarter
ORDER BY t.term_order, q.quarter;


-- ============================================================================
-- COURSE PERFORMANCE
-- ============================================================================

-- Lowest Performing Courses (Current Year)
-- Identifies courses needing instructional support
SELECT 
    c.course_name,
    c.course_rigor,
    COUNT(*) as students,
    ROUND(AVG(g.q1_score), 1) as avg_grade,
    ROUND(100.0 * SUM(CASE WHEN g.q1_score < 75 THEN 1 ELSE 0 END) / COUNT(*), 1) as fail_rate
FROM fct_grades g
JOIN dim_courses c ON g.course_key = c.course_key
WHERE g.q1_score IS NOT NULL 
  AND g.term_key = 7
GROUP BY g.course_key
HAVING students >= 10
ORDER BY avg_grade ASC
LIMIT 10;


-- ============================================================================
-- BOARDING VS DAY STUDENT COMPARISON
-- ============================================================================

-- GPA Comparison: Boarding vs Day Students
-- Subgroup analysis for accountability reporting
SELECT 
    t.school_year,
    CASE WHEN e.is_boarding = 1 THEN 'Boarding' ELSE 'Day Student' END as student_type,
    COUNT(DISTINCT g.student_key) as students,
    ROUND(AVG(g.q1_score), 1) as avg_q1
FROM fct_grades g
JOIN dim_terms t ON g.term_key = t.term_key
JOIN fct_student_term_enrollment e ON g.student_key = e.student_key 
  AND g.term_key = e.term_key
WHERE g.q1_score IS NOT NULL
GROUP BY t.school_year, e.is_boarding
ORDER BY t.term_order, e.is_boarding;