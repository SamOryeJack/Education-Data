
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select att_quarter_key
from "school_analytics"."main"."stg_attendance_quarter"
where att_quarter_key is null



  
  
      
    ) dbt_internal_test