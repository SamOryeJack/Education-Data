
    
    

select
    assignment_key as unique_field,
    count(*) as n_records

from "school_analytics"."main"."stg_assignments"
where assignment_key is not null
group by assignment_key
having count(*) > 1


