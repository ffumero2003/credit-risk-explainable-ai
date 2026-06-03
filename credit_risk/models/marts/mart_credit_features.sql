-- Final feature mart: one row per applicant, combining cleaned application
-- attributes with their aggregated bureau history. This is THE table the model
-- trains on. Materialized as a real table (set in dbt_project.yml).

with applications as (
    select * from {{ ref('stg_applications') }}
),

bureau as (
    select * from {{ ref('int_bureau_aggregated') }}
)

select
    -- all the cleaned application columns
    a.*,

    -- bureau history. LEFT JOIN keeps applicants with NO history, so we
    -- COALESCE their NULLs to 0 ("no prior loans" = 0, not unknown).
    coalesce(b.num_prior_loans, 0)      as num_prior_loans,
    coalesce(b.num_active_loans, 0)     as num_active_loans,
    coalesce(b.num_overdue_loans, 0)    as num_overdue_loans,
    coalesce(b.max_days_overdue, 0)     as max_days_overdue,
    coalesce(b.total_credit_amount, 0)  as total_credit_amount,
    coalesce(b.total_current_debt, 0)   as total_current_debt

from applications a
left join bureau b
    on a.applicant_id = b.applicant_id   -- join on the shared applicant key