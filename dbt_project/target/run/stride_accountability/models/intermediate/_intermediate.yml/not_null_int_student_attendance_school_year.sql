
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select school_year
from "school_analytics"."main"."int_student_attendance"
where school_year is null



  
  
      
    ) dbt_internal_test