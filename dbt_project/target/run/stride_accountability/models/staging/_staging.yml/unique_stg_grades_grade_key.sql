
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    

select
    grade_key as unique_field,
    count(*) as n_records

from "school_analytics"."main"."stg_grades"
where grade_key is not null
group by grade_key
having count(*) > 1



  
  
      
    ) dbt_internal_test