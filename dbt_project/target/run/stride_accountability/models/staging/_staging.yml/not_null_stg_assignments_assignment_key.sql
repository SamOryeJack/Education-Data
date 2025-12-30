
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select assignment_key
from "school_analytics"."main"."stg_assignments"
where assignment_key is null



  
  
      
    ) dbt_internal_test