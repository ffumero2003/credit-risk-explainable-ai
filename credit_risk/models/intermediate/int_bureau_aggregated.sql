-- Intermediate model: collapse the bureau table from one-row-per-loan
-- DOWN to one-row-per-applicant, so it can be joined to applications.
-- This is the grain fix — "summarize first, then join."

with bureau as (
    select * from {{ ref('stg_bureau') }}   -- ref() = read another dbt model
)

select
    applicant_id,

    count(*)                           as num_prior_loans,     -- how many prior loans
    countif(credit_status = 'Active')  as num_active_loans,    -- still-open loans
    countif(days_overdue > 0)          as num_overdue_loans,   -- delinquent loans
    max(days_overdue)                  as max_days_overdue,    -- worst delinquency
    sum(credit_amount)                 as total_credit_amount, -- summed prior credit
    sum(current_debt)                  as total_current_debt   -- summed outstanding debt

from bureau
group by applicant_id   -- one output row per applicant