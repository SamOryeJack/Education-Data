# Education Data Warehouse

School data warehouse tracking 636 Foreign Exchange students across 4 school years. Star schema design with 312K+ records integrating data from 3 source systems (SIS, CRM, boarding). Built for accountability analytics and at-risk identification.
## Database Schema
```mermaid
erDiagram
	dim_students {
		int student_key PK
		text school_id UK
		text sf_id
		text amerigo_id
		text reach_id
		text first_name
		text last_name
		text program_type
		text status
	}

	dim_terms {
		int term_key PK
		text term_name
		text school_year
		int term_order
	}

	dim_courses {
		int course_key PK
		text course_code UK
		text course_name
		text department
		text course_rigor
	}

	fct_grades {
		int grade_key PK
		int student_key FK
		int course_key FK
		int term_key FK
		real q1_score
		real q2_score
		real final_score
	}

	fct_assignments {
		int assignment_key PK
		int student_key FK
		int course_key FK
		int term_key FK
		text quarter
		real points_earned
		real points_possible
		int is_missing
	}

	fct_attendance_quarter {
		int att_quarter_key PK
		int student_key FK
		int term_key FK
		text quarter
		int total_absent
		int total_tardy
	}

	fct_attendance_course {
		int att_course_key PK
		int student_key FK
		int course_key FK
		int term_key FK
		int absent
		int tardy
	}

	fct_attendance_daily {
		int att_daily_key PK
		int student_key FK
		int term_key FK
		text date
		text homeroom
	}

	fct_student_term_enrollment {
		int enrollment_key PK
		int student_key FK
		int term_key FK
		int is_boarding
		text housing_type
	}

	ref_attendance_codes {
		text code PK
		text description
		text category
	}

	dim_students||--o{fct_grades:"student_key"
	dim_courses||--o{fct_grades:"course_key"
	dim_terms||--o{fct_grades:"term_key"
	dim_students||--o{fct_assignments:"student_key"
	dim_courses||--o{fct_assignments:"course_key"
	dim_terms||--o{fct_assignments:"term_key"
	dim_students||--o{fct_attendance_quarter:"student_key"
	dim_terms||--o{fct_attendance_quarter:"term_key"
	dim_students||--o{fct_attendance_course:"student_key"
	dim_courses||--o{fct_attendance_course:"course_key"
	dim_terms||--o{fct_attendance_course:"term_key"
	dim_students||--o{fct_attendance_daily:"student_key"
	dim_terms||--o{fct_attendance_daily:"term_key"
	dim_students||--o{fct_student_term_enrollment:"student_key"
	dim_terms||--o{fct_student_term_enrollment:"term_key"
```

*Star schema design: 3 dimension tables, 6 fact tables, 1 reference table. 312,439 total records across 4 school years (2022-2026).*

## Database Tables

| Table | Rows |
|-------|------|
| dim_students | 636 |
| dim_terms | 8 |
| dim_courses | 1,058 |
| fct_grades | 8,623 |
| fct_assignments | 265,571 |
| fct_attendance_quarter | 3,884 |
| fct_attendance_course | 7,792 |
| fct_attendance_daily | 22,884 |
| fct_student_term_enrollment | 1,942 |
| ref_attendance_codes | 41 |
| **Total** | **312,439** |


