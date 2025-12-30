
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select student_key
from "school_analytics"."main"."mart_student_accountability"
where student_key is null



  
  
      
    ) dbt_internal_test