# V3 Tables Documentation
## Amerigo Student Analytics - Synthetic Data Extension

**Created:** January 1, 2026  
**Database Location:** `/content/drive/MyDrive/LPE/Amerigo/25-26/CC/alt db/V3/school_analytics_v3.duckdb`  
**Purpose:** ESSA alignment and Stride RADA portfolio enhancement

---

## Executive Summary

V3 extends the original `school_analytics.duckdb` database with 8 new tables (6 fact tables + 2 marts) containing derived and synthetic data to support ESSA accountability calculations. The original 16 tables remain unchanged; V3 adds tables for graduation tracking, ESL progression, course credits, standardized test scores, AP exam scores, intervention records, and ESSA-aligned aggregated marts.

### V3 Tables Overview

| Table | Rows | Data Type | Purpose |
|-------|------|-----------|---------|
| `fct_graduation_outcomes` | 629 | Derived | ACGR calculation, cohort tracking |
| `fct_esl_progression` | 971 | Derived | ESSA Indicator 4 (EL Proficiency) |
| `fct_course_credits` | 8,623 | Derived | On-track graduation indicator |
| `fct_standardized_tests` | 332 | Synthetic | ESSA Indicator 1 proxy (PSAT/SAT) |
| `fct_ap_exam_scores` | 976 | Derived+Synthetic | College readiness indicator |
| `fct_interventions` | 502 | Fabricated | Defense scenario documentation |
| `mart_acgr` | 90 | Aggregated | ACGR by subgroup with N-size suppression |
| `mart_essa_accountability` | 132 | Aggregated | All 5 ESSA indicators by subgroup |

### Key Metrics

| Metric | Value |
|--------|-------|
| Total Graduates (confirmed + pre-data) | 220 |
| Active Seniors (2025-26) | 110 |
| Students in Graduation Cohort | 475 |
| Average SAT Score | 1,351 |
| AP Exam Pass Rate (≥3) | 96.6% |
| ESL Level Progressions | 218 |
| Intervention Records | 502 |

### ESSA Scorecard (2024-25)

| Indicator | Metric | Value |
|-----------|--------|-------|
| 1. Academic Achievement | GPA / Pass Rate | 90.7 / 94.5% |
| 2. Academic Growth | % Improved | 54.3% |
| 3. Graduation Rate | ACGR (Cohort 2021) | 26.9%* |
| 4. EL Proficiency | % Advanced | 58.9% |
| 5. School Quality | Chronic Absent | 12.3% |

*Cohort 2021 has many students still active (expected grad 2025)

---

## Table 1: fct_graduation_outcomes

### Purpose
Tracks each student's graduation cohort, final status, and graduation outcome for ACGR (Adjusted Cohort Graduation Rate) calculations.

### Schema

| Column | Type | Description |
|--------|------|-------------|
| outcome_key | INTEGER | Primary key |
| student_key | INTEGER | FK to dim_students |
| school_id | VARCHAR | Anonymous student ID |
| first_intake | VARCHAR | First enrollment term (e.g., "Fall 2022") |
| accepted_grade | VARCHAR | Grade level when accepted (9-12) |
| cohort_year | INTEGER | Year student entered 9th grade |
| expected_grad_year | INTEGER | cohort_year + 4 |
| program_type_original | VARCHAR | Original program_type from dim_students |
| program_type_clean | VARCHAR | Cleaned: Diploma, Exchange (Semester/Full Year/Unknown) |
| in_graduation_cohort | INTEGER | 1 if Diploma track, 0 if Exchange |
| highest_grade_reached | INTEGER | Max grade level (capped at 12) |
| senior_year | VARCHAR | School year when grade 12 (if reached) |
| courses_with_final | INTEGER | Count of courses with Q4/Final grades in senior year |
| final_status_raw | VARCHAR | Pre-transfer-assignment status |
| final_status | VARCHAR | Final status (see below) |
| is_documented_transfer | INTEGER | 1 if documented, 0 if not, NULL if N/A |
| graduation_year | VARCHAR | Year graduated (if applicable) |
| current_status | VARCHAR | Active or Inactive |

### Final Status Values

| Status | Count | Description | ACGR Treatment |
|--------|-------|-------------|----------------|
| Graduated | 133 | Completed 12th with final grades (2022-25) | Numerator + Denominator |
| Graduated (Pre-Data) | 87 | Completed before 2022-23 data window | Numerator + Denominator |
| Active Senior | 110 | Current 2025-26 seniors | Pending |
| Active | 81 | Currently enrolled, not yet senior | Pending |
| Completed Exchange | 109 | Exchange students (by design) | Excluded |
| Transferred (Documented) | 85 | Left with documentation (~80%) | Removed from Denominator |
| Withdrew (Undocumented) | 24 | Left without documentation (~20%) | Denominator only (counts against) |

### Derivation Logic

**Cohort Year Calculation:**
```sql
-- For Fall intake: cohort_year = intake_year - (accepted_grade - 9)
-- For Spring intake: cohort_year = intake_year - 1 - (accepted_grade - 9)

-- Example: Student enters Fall 2023 as 10th grader
-- cohort_year = 2023 - (10 - 9) = 2022
```

**Program Type Cleaning:**
- `Diploma` → `Diploma` (in cohort)
- `Exchange (Semester)` or `Exchange (Full Year)` → Same (excluded from cohort)
- `NULL` + Inactive + never reached 12th → `Exchange (Unknown)` (excluded)
- `NULL` + otherwise → `Diploma` (assumed)

**Final Status Assignment:**
1. Exchange students → `Completed Exchange`
2. Active students with grade 12 → `Active Senior`
3. Active students below grade 12 → `Active`
4. Inactive + senior year with final grades → `Graduated`
5. Inactive + calculated grade 12 but no senior_year in data → `Graduated (Pre-Data)`
6. Inactive + left → Random 80% `Transferred (Documented)`, 20% `Withdrew (Undocumented)`

### Sample Queries

```sql
-- ACGR Calculation for a cohort
SELECT 
    cohort_year,
    COUNT(CASE WHEN in_graduation_cohort = 1 THEN 1 END) as cohort_size,
    COUNT(CASE WHEN final_status LIKE 'Graduated%' THEN 1 END) as graduates,
    COUNT(CASE WHEN final_status = 'Transferred (Documented)' THEN 1 END) as transfers_out,
    ROUND(
        COUNT(CASE WHEN final_status LIKE 'Graduated%' THEN 1 END) * 100.0 /
        NULLIF(COUNT(CASE WHEN in_graduation_cohort = 1 THEN 1 END) - 
               COUNT(CASE WHEN final_status = 'Transferred (Documented)' THEN 1 END), 0)
    , 1) as acgr
FROM fct_graduation_outcomes
WHERE cohort_year <= 2021  -- Completed cohorts only
GROUP BY cohort_year
ORDER BY cohort_year;

-- Students by final status
SELECT final_status, COUNT(*) as count
FROM fct_graduation_outcomes
GROUP BY final_status
ORDER BY count DESC;
```

### Known Limitations
- 7 students missing (636 - 629) due to NULL first_intake or accepted_grade
- Pre-data graduates assumed based on calculated grade level, not actual records
- Transfer documentation is randomly assigned (80/20 split)
- 2025-26 seniors show as "Active Senior" even though some have partial data

---

## Table 2: fct_esl_progression

### Purpose
Tracks ESL level progression year-over-year for ESSA Indicator 4 (English Learner Proficiency Progress).

### Schema

| Column | Type | Description |
|--------|------|-------------|
| esl_key | INTEGER | Primary key |
| student_key | INTEGER | FK to dim_students |
| school_year | VARCHAR | Academic year |
| intake_esl_level | VARCHAR | ESL level when first enrolled |
| esl_level_start | VARCHAR | ESL level at start of year |
| esl_level_end | VARCHAR | ESL level at end of year |
| has_skills_3_or_fluency_3 | INTEGER | 1 if enrolled in Skills 3 or Fluency 3 |
| has_skills_2_or_fluency_2 | INTEGER | 1 if enrolled in Skills 2 or Fluency 2 |
| has_skills_1 | INTEGER | 1 if enrolled in Skills 1 |
| has_literature_course | INTEGER | 1 if enrolled in any Literature course |
| progressed | INTEGER | 1 if advanced an ESL level |
| tested_out | INTEGER | 1 if moved to Direct/regular English |

### ESL Level Hierarchy

```
Level III (lowest) → Level II → Level I → Direct (highest/tested out)
```

### Derivation Logic

**ESL Level from Courses:**
```sql
-- Priority: lowest level if multiple indicators
CASE 
    WHEN course_name LIKE '%Skills 3%' OR course_name LIKE '%Fluency 3%' THEN 'Level III'
    WHEN course_name LIKE '%Skills 2%' OR course_name LIKE '%Fluency 2%' THEN 'Level II'
    WHEN course_name LIKE '%Skills 1%' THEN 'Level I'
    WHEN course_name LIKE '%Literature%' THEN 'Direct'
    ELSE NULL
END
```

**Intake Level Normalization:**
- '3', 'Level III' → 'Level III'
- '2', 'Level II' → 'Level II'
- '1', 'Level I' → 'Level I'
- 'Direct', 'Direct Admission', 'D' → 'Direct'

**Progression Detection:**
- Level III → Level II/I/Direct = progressed
- Level II → Level I/Direct = progressed
- Level I → Direct = progressed
- Direct → Direct = no progression (already highest)

### Progression Rates

| Starting Level | Total | Progressed | Rate |
|----------------|-------|------------|------|
| Level III | 68 | 39 | 57.4% |
| Level II | 175 | 100 | 57.1% |
| Level I | 291 | 79 | 27.1% |
| Direct | 431 | 0 | 0% (already highest) |

### Sample Queries

```sql
-- ESL progression rate by year
SELECT 
    school_year,
    COUNT(*) as students,
    SUM(progressed) as progressed,
    ROUND(SUM(progressed) * 100.0 / COUNT(*), 1) as progression_rate
FROM fct_esl_progression
WHERE esl_level_start != 'Direct'  -- Exclude already proficient
GROUP BY school_year
ORDER BY school_year;

-- Students who tested out
SELECT student_key, school_year, esl_level_start, esl_level_end
FROM fct_esl_progression
WHERE tested_out = 1
ORDER BY student_key, school_year;
```

---

## Table 3: fct_course_credits

### Purpose
Tracks credits attempted and earned per course for on-track graduation monitoring.

### Schema

| Column | Type | Description |
|--------|------|-------------|
| credit_key | INTEGER | Primary key |
| student_key | INTEGER | FK to dim_students |
| course_key | INTEGER | FK to dim_courses |
| school_year | VARCHAR | Academic year |
| course_name | VARCHAR | Course name |
| course_rigor | VARCHAR | AP, Honors, or Regular |
| credits_attempted | DOUBLE | 1.0 (full year) or 0.5 (semester) |
| final_grade | DOUBLE | Best available final grade |
| passed | INTEGER | 1 if final_grade >= 75 |
| credits_earned | DOUBLE | credits_attempted if passed, else 0 |

### Credit Determination Logic

```sql
-- If has grades in both semesters (Q1/Q2 AND Q3/Q4) = full year = 1.0 credit
-- Otherwise = semester = 0.5 credit

CASE 
    WHEN (q1_score IS NOT NULL OR q2_score IS NOT NULL) 
     AND (q3_score IS NOT NULL OR q4_score IS NOT NULL) THEN 1.0
    ELSE 0.5
END as credits_attempted
```

### Summary by Year

| Year | Records | Students | Attempted | Earned | Pass Rate |
|------|---------|----------|-----------|--------|-----------|
| 2022-23 | 2,232 | 230 | 1,801.0 | 1,548.0 | 80.8% |
| 2023-24 | 2,226 | 260 | 1,895.5 | 1,737.0 | 89.8% |
| 2024-25 | 2,184 | 253 | 1,947.0 | 1,839.0 | 93.1% |
| 2025-26 | 1,981 | 228 | 996.0 | 848.5 | 85.2% |

### Associated View: v_student_cumulative_credits

```sql
-- Cumulative credits per student with on-track calculation
SELECT 
    student_key,
    school_year,
    year_earned,
    cumulative_earned,
    highest_grade_reached,
    expected_credits,  -- 6/12/18/24 by grade
    on_track_to_graduate  -- 1 if cumulative >= 90% of expected
FROM v_student_cumulative_credits;
```

### Sample Queries

```sql
-- Credits by course rigor
SELECT 
    course_rigor,
    COUNT(*) as enrollments,
    ROUND(SUM(credits_earned), 1) as total_earned,
    ROUND(AVG(CASE WHEN passed = 1 THEN 100.0 ELSE 0 END), 1) as pass_rate
FROM fct_course_credits
GROUP BY course_rigor;

-- Students at risk of not graduating (low credits)
SELECT 
    v.student_key,
    v.cumulative_earned,
    v.expected_credits,
    v.on_track_to_graduate
FROM v_student_cumulative_credits v
WHERE v.on_track_to_graduate = 0
  AND v.school_year = '2025-26';
```

---

## Table 4: fct_standardized_tests

### Purpose
Synthetic PSAT and SAT scores for ESSA Indicator 1 (Academic Achievement) proxy.

### Schema

| Column | Type | Description |
|--------|------|-------------|
| test_key | INTEGER | Primary key |
| student_key | INTEGER | FK to dim_students |
| test_type | VARCHAR | 'PSAT' or 'SAT' |
| school_year | VARCHAR | Junior year when test taken |
| grade_level | INTEGER | Always 11 |
| test_date | DATE | October (PSAT) or March (SAT) |
| score_verbal | INTEGER | Evidence-Based Reading & Writing (200-800) |
| score_math | INTEGER | Math section (200-800) |
| score_total | INTEGER | Combined score (400-1600) |
| percentile | INTEGER | Estimated national percentile |
| year_gpa | DOUBLE | Junior year GPA used for calculation |
| esl_level | VARCHAR | ESL level (affects verbal adjustment) |

### Synthetic Score Generation Logic

```sql
-- Base SAT from GPA (100-point scale)
-- Formula: 400 + (GPA - 50) * 24
-- GPA 50 → SAT 400, GPA 100 → SAT 1600

base_sat = 400 + (junior_year_gpa - 50) * 24

-- ESL adjustments (slight verbal penalty, math bonus)
-- Level II/III: verbal -30, math +20
-- Level I: verbal -15, math +10
-- Direct/Unknown: no adjustment

-- Random variance: ±50 points per section (hash-based for reproducibility)

-- PSAT = SAT × 0.93 (taken earlier, slightly lower)
```

### Score Summary

| Test | Records | Avg Total | Avg Verbal | Avg Math | Min | Max |
|------|---------|-----------|------------|----------|-----|-----|
| SAT | 166 | 1,351 | 665 | 686 | 652 | 1,600 |
| PSAT | 166 | 1,257 | 619 | 638 | 606 | 1,488 |

### Scores by ESL Level

| ESL Level | Students | Avg SAT | Avg Verbal | Avg Math |
|-----------|----------|---------|------------|----------|
| Direct | 66 | 1,414 | 705 | 710 |
| Level I | 75 | 1,327 | 652 | 675 |
| Level II | 20 | 1,287 | 612 | 675 |
| Level III | 4 | 1,196 | 579 | 617 |

### Percentile Distribution

| Percentile | Students |
|------------|----------|
| 99 | 12 |
| 95 | 41 |
| 90 | 43 |
| 80 | 29 |
| 65 | 19 |
| 50 | 14 |
| 35 | 2 |
| 20 | 4 |
| 10 | 2 |

### Sample Queries

```sql
-- SAT scores by year
SELECT 
    school_year,
    COUNT(*) as students,
    ROUND(AVG(score_total), 0) as avg_sat,
    MIN(score_total) as min_sat,
    MAX(score_total) as max_sat
FROM fct_standardized_tests
WHERE test_type = 'SAT'
GROUP BY school_year;

-- College readiness (SAT >= 1100)
SELECT 
    COUNT(*) as total,
    SUM(CASE WHEN score_total >= 1100 THEN 1 ELSE 0 END) as college_ready,
    ROUND(SUM(CASE WHEN score_total >= 1100 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as pct
FROM fct_standardized_tests
WHERE test_type = 'SAT';
```

### Known Limitations
- Only students with junior year (Grade 11) data get scores (166 students)
- Scores are synthetic, derived from GPA
- ESL adjustment is approximate stereotype (lower verbal, higher math)
- Percentiles are rough buckets, not precise

---

## Table 5: fct_ap_exam_scores

### Purpose
AP exam scores derived from course grades for college readiness indicator.

### Schema

| Column | Type | Description |
|--------|------|-------------|
| ap_score_key | INTEGER | Primary key |
| student_key | INTEGER | FK to dim_students |
| course_key | INTEGER | FK to dim_courses |
| school_year | VARCHAR | Academic year |
| course_name | VARCHAR | AP course name |
| course_grade | DOUBLE | Final grade in course (0-100) |
| exam_score | INTEGER | AP score (1-5) |
| passed_exam | INTEGER | 1 if exam_score >= 3 |

### Score Derivation Logic

```sql
-- Base score from course grade
CASE 
    WHEN course_grade >= 93 THEN 5
    WHEN course_grade >= 85 THEN 4
    WHEN course_grade >= 75 THEN 3
    WHEN course_grade >= 65 THEN 2
    ELSE 1
END as base_ap_score

-- Variance: 15% chance -1, 15% chance +1, 70% same (clamped to 1-5)
```

### Summary Statistics

| Metric | Value |
|--------|-------|
| Total Exams | 976 |
| Unique Students | 306 |
| Unique Courses | 37 |
| Average Score | 4.28 |
| Pass Rate (≥3) | 96.6% |

### Score Distribution

| Score | Count | Percentage |
|-------|-------|------------|
| 5 | 489 | 50.1% |
| 4 | 319 | 32.7% |
| 3 | 135 | 13.8% |
| 2 | 19 | 1.9% |
| 1 | 14 | 1.4% |

### Top AP Courses

| Course | Exams | Avg Grade | Avg Score | Pass Rate |
|--------|-------|-----------|-----------|-----------|
| AP Calculus AB | 175 | 90.7 | 4.30 | 96.0% |
| AP Calculus BC | 71 | 91.4 | 4.28 | 98.6% |
| AP Computer Science Principles | 67 | 94.9 | 4.55 | 100.0% |
| AP Macro Economics | 66 | 90.3 | 4.18 | 97.0% |
| AP Statistics | 66 | 87.6 | 3.92 | 93.9% |

### Sample Queries

```sql
-- AP participation and success by student
SELECT 
    student_key,
    COUNT(*) as ap_exams_taken,
    SUM(passed_exam) as ap_exams_passed,
    ROUND(AVG(exam_score), 2) as avg_score
FROM fct_ap_exam_scores
GROUP BY student_key
ORDER BY ap_exams_taken DESC;

-- AP success rate by year
SELECT 
    school_year,
    COUNT(*) as exams,
    ROUND(AVG(exam_score), 2) as avg_score,
    ROUND(SUM(passed_exam) * 100.0 / COUNT(*), 1) as pass_rate
FROM fct_ap_exam_scores
GROUP BY school_year
ORDER BY school_year;
```

---

## Table 6: fct_interventions

### Purpose
Fabricated intervention records for at-risk students to support defense scenarios.

### Schema

| Column | Type | Description |
|--------|------|-------------|
| intervention_key | INTEGER | Primary key |
| student_key | INTEGER | FK to dim_students |
| school_id | VARCHAR | Anonymous student ID |
| school_year | VARCHAR | Academic year |
| intervention_date | DATE | Date of intervention |
| intervention_type | VARCHAR | Type of support provided |
| duration_minutes | INTEGER | Length of session (NULL for letters) |
| staff_role | VARCHAR | Who provided support |
| notes | VARCHAR | Brief description |
| outcome | VARCHAR | Result of intervention |

### Intervention Types

| Type | Count | Pct | Avg Duration | Staff Role |
|------|-------|-----|--------------|------------|
| Counselor Meeting | 137 | 27.3% | 34 min | School Counselor |
| Parent Conference | 118 | 23.5% | 45 min | School Counselor |
| Academic Warning Letter | 108 | 21.5% | N/A | Administrator |
| ESL Support | 80 | 15.9% | 49 min | ESL Teacher |
| Peer Mentoring | 59 | 11.8% | 35 min | Peer Mentor |

*Note: Academic Tutoring was in the design but ended up not being assigned due to the weighted random logic favoring risk-specific interventions.*

### Generation Logic

```sql
-- For each at-risk student-year (is_at_risk = 1):
-- 1. Generate 2-5 interventions (hash-based pseudo-random)
-- 2. Assign type based on risk factors:
--    - Behavior risk → more Counselor Meetings, Warning Letters
--    - Chronic absent → more Parent Conferences
--    - Failing → more Tutoring, Peer Mentoring
-- 3. Generate date within school year (random offset 0-180 days from Sept 1)
-- 4. Assign duration based on type
-- 5. Assign outcome: 40% Improved, 35% Ongoing, 25% Referred
```

### Outcomes Distribution

| Outcome | Count | Percentage |
|---------|-------|------------|
| Improved | 204 | 40.6% |
| Ongoing | 177 | 35.3% |
| Referred for Additional Support | 121 | 24.1% |

### By Year

| Year | Interventions | Students | Per Student |
|------|---------------|----------|-------------|
| 2022-23 | 188 | 51 | 3.7 |
| 2023-24 | 214 | 61 | 3.5 |
| 2024-25 | 72 | 21 | 3.4 |
| 2025-26 | 28 | 7 | 4.0 |

### Sample Queries

```sql
-- Intervention summary for a student
SELECT 
    student_key,
    school_year,
    COUNT(*) as interventions,
    STRING_AGG(DISTINCT intervention_type, ', ') as types
FROM fct_interventions
GROUP BY student_key, school_year;

-- Effectiveness analysis (students who improved)
SELECT 
    intervention_type,
    COUNT(*) as total,
    SUM(CASE WHEN outcome = 'Improved' THEN 1 ELSE 0 END) as improved,
    ROUND(SUM(CASE WHEN outcome = 'Improved' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as improvement_rate
FROM fct_interventions
GROUP BY intervention_type
ORDER BY improvement_rate DESC;
```

---

## Table 7: mart_acgr

### Purpose
Aggregated Adjusted Cohort Graduation Rate (ACGR) calculations by subgroup with N-size suppression for FERPA compliance. This is the primary table for ESSA Indicator 3 (Graduation Rate) reporting.

### Schema

| Column | Type | Description |
|--------|------|-------------|
| acgr_key | INTEGER | Primary key |
| cohort_year | INTEGER | Year students entered 9th grade |
| expected_grad_year | INTEGER | cohort_year + 4 |
| subgroup_type | VARCHAR | Category: Overall, Gender, Country, ESL Level |
| subgroup_value | VARCHAR | Specific value within category |
| cohort_count | INTEGER | Original cohort size |
| graduates | INTEGER | Count who graduated |
| transfers_out | INTEGER | Documented transfers (removed from denominator) |
| undocumented_leavers | INTEGER | Withdrew without documentation (counts against) |
| adjusted_cohort | INTEGER | cohort_count - transfers_out |
| acgr | DOUBLE | Graduation rate: graduates / adjusted_cohort × 100 |
| is_suppressed | INTEGER | 1 if cohort_count < 10 (FERPA) |
| acgr_suppressed | DOUBLE | NULL if suppressed, else same as acgr |

### ACGR Formula

```
ACGR = Graduates / (Original Cohort - Documented Transfers) × 100

Where:
- Graduates = Students who earned a diploma within 4 years
- Original Cohort = Students who entered 9th grade in cohort year
- Documented Transfers = Students who transferred out with documentation
- Undocumented leavers remain in denominator (count against rate)
```

### Subgroup Types

| Subgroup Type | Values | Purpose |
|---------------|--------|---------|
| Overall | All Students | School-wide ACGR |
| Gender | Male, Female | Gender equity analysis |
| Country | Various | International student analysis |
| ESL Level | Level I/II/III, Direct, Unknown | EL subgroup performance |

### ACGR by Cohort (Overall)

| Cohort | Expected Grad | Cohort Size | Graduates | Transfers | Adjusted | ACGR |
|--------|---------------|-------------|-----------|-----------|----------|------|
| 2016 | 2020 | 22 | 22 | 0 | 22 | 100.0% |
| 2017 | 2021 | 26 | 26 | 0 | 26 | 100.0% |
| 2018 | 2022 | 37 | 37 | 0 | 37 | 100.0% |
| 2019 | 2023 | 89 | 77 | 0 | 89 | 86.5% |
| 2020 | 2024 | 58 | 40 | 0 | 58 | 69.0% |
| 2021 | 2025 | 75 | 18 | 8 | 67 | 26.9% |

*Note: Cohorts 2016-2018 are "Graduated (Pre-Data)" - calculated based on grade level progression, not actual grade records.*

### N-Size Suppression

- **Threshold:** N < 10 students
- **56.7% of subgroup rows suppressed** (51 of 90 rows)
- **82.3% of Country subgroups suppressed** (most countries have few students)
- **0% of Gender/Overall suppressed** (sufficient N)

### Sample Queries

```sql
-- Overall ACGR trend
SELECT 
    cohort_year,
    expected_grad_year,
    cohort_count,
    graduates,
    acgr
FROM mart_acgr
WHERE subgroup_type = 'Overall'
ORDER BY cohort_year;

-- ACGR by gender (non-suppressed only)
SELECT 
    cohort_year,
    subgroup_value as gender,
    cohort_count as n,
    acgr_suppressed as acgr
FROM mart_acgr
WHERE subgroup_type = 'Gender'
  AND is_suppressed = 0
ORDER BY cohort_year, gender;

-- Subgroups at risk (low ACGR, sufficient N)
SELECT 
    cohort_year,
    subgroup_type,
    subgroup_value,
    cohort_count as n,
    acgr
FROM mart_acgr
WHERE is_suppressed = 0
  AND acgr < 80
ORDER BY acgr;
```

### Known Limitations
- Only includes diploma-track students (Exchange students excluded)
- Cohorts 2016-2018 are estimated from grade level, not actual records
- Transfer documentation is synthetic (80/20 random split)
- Cohort 2021 appears low because many students still active

---

## Table 8: mart_essa_accountability

### Purpose
Comprehensive ESSA accountability table combining all 5 indicators by subgroup with N-size suppression. This is the primary table for state accountability reporting alignment.

### Schema

| Column | Type | Description |
|--------|------|-------------|
| essa_key | INTEGER | Primary key |
| school_year | VARCHAR | Academic year |
| subgroup_type | VARCHAR | Category: Overall, Gender, ESL Level, Country, Boarding |
| subgroup_value | VARCHAR | Specific value within category |
| student_count | INTEGER | Number of students in subgroup |
| is_suppressed | INTEGER | 1 if student_count < 10 |
| **Indicator 1: Academic Achievement** | | |
| avg_gpa | DOUBLE | Average GPA (0-100 scale) |
| avg_pass_rate | DOUBLE | Average course pass rate (%) |
| avg_gpa_suppressed | DOUBLE | NULL if N < 10 |
| avg_pass_rate_suppressed | DOUBLE | NULL if N < 10 |
| **Indicator 2: Academic Growth** | | |
| students_with_prior | INTEGER | Students with prior year data |
| avg_gpa_change | DOUBLE | Average year-over-year GPA change |
| improved_count | INTEGER | Students whose GPA improved |
| pct_improved | DOUBLE | Percentage who improved |
| pct_improved_suppressed | DOUBLE | NULL if N < 10 |
| **Indicator 3: Graduation Rate** | | |
| acgr | DOUBLE | Placeholder (join to mart_acgr) |
| **Indicator 4: EL Proficiency** | | |
| el_students | INTEGER | English Learner students |
| el_progressed | INTEGER | EL students who advanced a level |
| el_progress_rate | DOUBLE | Percentage who progressed |
| el_progress_rate_suppressed | DOUBLE | NULL if N < 10 |
| **Indicator 5: School Quality** | | |
| chronic_absent_count | INTEGER | Chronically absent students |
| chronic_absent_rate | DOUBLE | Chronic absenteeism rate (%) |
| chronic_absent_rate_suppressed | DOUBLE | NULL if N < 10 |

### ESSA Indicators Explained

| Indicator | Metric | Source | Target Direction |
|-----------|--------|--------|------------------|
| 1. Achievement | GPA, Pass Rate | fct_grades | Higher is better |
| 2. Growth | % Improved YoY | fct_grades (YoY) | Higher is better |
| 3. Graduation | ACGR | mart_acgr | Higher is better |
| 4. EL Progress | % Advanced Level | fct_esl_progression | Higher is better |
| 5. School Quality | Chronic Absence | mart_student_accountability | Lower is better |

### Overall Trends by Year

| Year | N | GPA | Pass% | Growth% | EL% | Absent% |
|------|---|-----|-------|---------|-----|---------|
| 2022-23 | 230 | 89.0 | 92.7 | N/A | 6.4 | 33.5 |
| 2023-24 | 260 | 88.7 | 91.5 | 43.5 | 30.1 | 46.9 |
| 2024-25 | 253 | 90.7 | 94.5 | 54.3 | 58.9 | 12.3 |
| 2025-26 | 228 | 91.7 | 93.1 | 54.3 | 56.8 | 1.3 |

*Note: 2022-23 has no Growth% (no prior year), 2025-26 is partial year*

### Suppression Summary

| Subgroup Type | Total Rows | Suppressed | % Suppressed |
|---------------|------------|------------|--------------|
| Country | 96 | 79 | 82.3% |
| ESL Level | 16 | 1 | 6.3% |
| Gender | 8 | 0 | 0.0% |
| Overall | 4 | 0 | 0.0% |
| Boarding | 8 | 0 | 0.0% |

### Sample Queries

```sql
-- ESSA Scorecard for a year
SELECT 
    'Indicator 1: Achievement' as indicator,
    avg_gpa || ' GPA, ' || avg_pass_rate || '% Pass' as value
FROM mart_essa_accountability
WHERE subgroup_type = 'Overall' AND school_year = '2024-25'

UNION ALL

SELECT 
    'Indicator 2: Growth',
    pct_improved || '% improved GPA'
FROM mart_essa_accountability
WHERE subgroup_type = 'Overall' AND school_year = '2024-25'

UNION ALL

SELECT 
    'Indicator 4: EL Progress',
    el_progress_rate || '% advanced'
FROM mart_essa_accountability
WHERE subgroup_type = 'Overall' AND school_year = '2024-25'

UNION ALL

SELECT 
    'Indicator 5: Chronic Absence',
    chronic_absent_rate || '% absent'
FROM mart_essa_accountability
WHERE subgroup_type = 'Overall' AND school_year = '2024-25';

-- Subgroup performance comparison (non-suppressed)
SELECT 
    subgroup_type,
    subgroup_value,
    student_count as n,
    avg_gpa_suppressed as gpa,
    pct_improved_suppressed as growth_pct,
    chronic_absent_rate_suppressed as absent_pct
FROM mart_essa_accountability
WHERE school_year = '2024-25'
  AND is_suppressed = 0
ORDER BY subgroup_type, subgroup_value;

-- ESL Level performance gap analysis
SELECT 
    subgroup_value as esl_level,
    student_count as n,
    avg_gpa,
    el_progress_rate,
    chronic_absent_rate
FROM mart_essa_accountability
WHERE subgroup_type = 'ESL Level'
  AND school_year = '2024-25'
ORDER BY 
    CASE subgroup_value 
        WHEN 'Level III' THEN 1 
        WHEN 'Level II' THEN 2 
        WHEN 'Level I' THEN 3 
        WHEN 'Direct' THEN 4 
    END;

-- Year-over-year trend for a subgroup
SELECT 
    school_year,
    avg_gpa,
    pct_improved,
    chronic_absent_rate
FROM mart_essa_accountability
WHERE subgroup_type = 'Overall'
ORDER BY school_year;
```

### Joining with mart_acgr for Complete Picture

```sql
-- Complete ESSA dashboard with graduation rate
SELECT 
    e.school_year,
    e.subgroup_type,
    e.subgroup_value,
    e.student_count,
    e.avg_gpa as ind1_gpa,
    e.pct_improved as ind2_growth,
    a.acgr as ind3_graduation,
    e.el_progress_rate as ind4_el,
    e.chronic_absent_rate as ind5_absent
FROM mart_essa_accountability e
LEFT JOIN mart_acgr a 
    ON e.subgroup_type = a.subgroup_type 
    AND e.subgroup_value = a.subgroup_value
    AND CAST(LEFT(e.school_year, 4) AS INTEGER) = a.expected_grad_year
WHERE e.subgroup_type = 'Overall'
ORDER BY e.school_year;
```

### Known Limitations
- Indicator 3 (Graduation) stored in separate mart_acgr table
- Growth calculation requires prior year data (2022-23 has none)
- 2025-26 data is partial (school year not complete)
- No actual state assessment data (using GPA as proxy)

---

## Database Connection

### Python (DuckDB)

```python
import duckdb

V3_DB = '/content/drive/MyDrive/LPE/Amerigo/25-26/CC/alt db/V3/school_analytics_v3.duckdb'
con = duckdb.connect(V3_DB)

# Query example
df = con.execute("SELECT * FROM fct_graduation_outcomes LIMIT 10").fetchdf()
```

### Listing All Tables

```python
tables = con.execute("""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'main' 
    AND table_type = 'BASE TABLE'
    ORDER BY table_name
""").fetchall()

for t in tables:
    count = con.execute(f"SELECT COUNT(*) FROM {t[0]}").fetchone()[0]
    print(f"{t[0]}: {count:,} rows")
```

---

## Known Issues and Decisions

### Issues Encountered During Build

1. **grade_level NULL in mart_student_accountability**
   - All 971 student-year records had NULL grade_level
   - Solution: Calculated from `first_intake` and `accepted_grade` using cohort logic

2. **Pre-data graduates (cohorts 2016-2018)**
   - Students calculated to have reached 12th grade before 2022-23 data window
   - Solution: Marked as "Graduated (Pre-Data)" based on cohort calculation

3. **2025-26 "Graduates"**
   - Initially marked students with partial 2025-26 data as graduated
   - Solution: Changed to "Active Senior" since year is incomplete

4. **Spring intake adjustment**
   - Spring intake students were getting wrong grade calculation
   - Solution: Added +1 year adjustment for Spring intakes

5. **Transfer documentation**
   - No actual transfer records exist
   - Solution: Random assignment (80% documented, 20% undocumented)

### Key Decisions Made

| Decision | Rationale |
|----------|-----------|
| Exchange students excluded from ACGR | By design - not diploma-seeking |
| NULL program_type + inactive + <12th grade → Exchange (Unknown) | Likely short-term students |
| NULL program_type + otherwise → Diploma | Assume diploma track unless evidence otherwise |
| 80/20 split for transfer documentation | Industry-typical ratio |
| SAT derived from GPA | No actual test data; GPA is best proxy |
| ESL verbal penalty, math bonus | Slight stereotype adjustment for realism |
| 2-5 interventions per at-risk student | Realistic range for a school year |

---

## Next Steps (Post-V3)

### Priority 1: ESSA-Aligned Marts ✅ COMPLETED
- [x] Create `mart_essa_accountability` combining all 5 indicators
- [x] Create `mart_acgr` with proper cohort calculations
- [x] Add N-size suppression (N < 10) to subgroup reporting

### Priority 2: dbt Model Updates
- [ ] Add V3 tables as sources in dbt
- [ ] Create intermediate models for ESSA calculations
- [ ] Update `mart_school_year_summary` with ESSA metrics

### Priority 3: Dashboard Updates
- [ ] Add ACGR Tracker page
- [ ] Add ESSA Scorecard page
- [ ] Add Defense Scenario builder page

### Priority 4: Documentation
- [x] Update `V3_TABLES_DOCUMENTATION.md` with mart tables
- [ ] Update `V3_UPDATE.md` with completion status
- [ ] Add V3 documentation to GitHub repo
- [ ] Update project README

---

## File Locations

| File | Location |
|------|----------|
| V3 Database | `/content/drive/MyDrive/LPE/Amerigo/25-26/CC/alt db/V3/school_analytics_v3.duckdb` |
| Original Database | `/content/drive/MyDrive/LPE/Amerigo/25-26/CC/alt db/school_analytics.duckdb` |
| dbt Project | `/content/drive/MyDrive/LPE/Amerigo/25-26/CC/alt db/dbt_project/` |
| Streamlit App | `/content/drive/MyDrive/LPE/Amerigo/25-26/CC/alt db/streamlit_app/` |
| GitHub Repo | https://github.com/SamOryeJack/Education-Data |

---

*Document Version: 1.1*  
*Created: January 1, 2026*  
*Updated: January 1, 2026 - Added mart_acgr and mart_essa_accountability*  
*For: Stride Research & Accountability Data Analyst Portfolio*
