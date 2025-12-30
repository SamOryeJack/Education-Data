
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select student_key
from "school_analytics"."main"."stg_students"
where student_key is null



  
  
      
    ) dbt_internal_test