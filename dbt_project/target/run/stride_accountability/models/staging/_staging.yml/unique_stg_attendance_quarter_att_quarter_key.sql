
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    

select
    att_quarter_key as unique_field,
    count(*) as n_records

from "school_analytics"."main"."stg_attendance_quarter"
where att_quarter_key is not null
group by att_quarter_key
having count(*) > 1



  
  
      
    ) dbt_internal_test