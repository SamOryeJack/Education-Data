
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select school_year
from "school_analytics"."main"."mart_student_accountability"
where school_year is null



  
  
      
    ) dbt_internal_test