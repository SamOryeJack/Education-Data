
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    

select
    att_daily_key as unique_field,
    count(*) as n_records

from "school_analytics"."main"."stg_attendance_daily"
where att_daily_key is not null
group by att_daily_key
having count(*) > 1



  
  
      
    ) dbt_internal_test