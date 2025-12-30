
    
    

with all_values as (

    select
        abc_risk_score as value_field,
        count(*) as n_records

    from "school_analytics"."main"."mart_student_accountability"
    group by abc_risk_score

)

select *
from all_values
where value_field not in (
    '0','1','2','3'
)


