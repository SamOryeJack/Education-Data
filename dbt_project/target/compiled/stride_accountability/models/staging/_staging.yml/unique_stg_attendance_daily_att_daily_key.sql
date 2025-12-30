
    
    

select
    att_daily_key as unique_field,
    count(*) as n_records

from "school_analytics"."main"."stg_attendance_daily"
where att_daily_key is not null
group by att_daily_key
having count(*) > 1


