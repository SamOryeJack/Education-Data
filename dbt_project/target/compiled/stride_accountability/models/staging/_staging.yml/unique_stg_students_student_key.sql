
    
    

select
    student_key as unique_field,
    count(*) as n_records

from "school_analytics"."main"."stg_students"
where student_key is not null
group by student_key
having count(*) > 1


