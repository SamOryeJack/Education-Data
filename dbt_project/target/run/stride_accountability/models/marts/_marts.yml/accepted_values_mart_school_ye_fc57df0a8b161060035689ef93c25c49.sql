
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    

with all_values as (

    select
        subgroup_type as value_field,
        count(*) as n_records

    from "school_analytics"."main"."mart_school_year_summary"
    group by subgroup_type

)

select *
from all_values
where value_field not in (
    'Overall','Gender','Program','Boarding'
)



  
  
      
    ) dbt_internal_test