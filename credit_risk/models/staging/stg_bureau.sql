-- Staging model for the raw bureau table.
-- Grain: one row per PRIOR LOAN (SK_ID_BUREAU). A person can have many.
-- Light cleaning only — no aggregation yet.

with source as (
    select * from {{ source('credit_raw', 'raw_bureau') }}
)

select
    SK_ID_CURR           as applicant_id,    -- links back to the application
    SK_ID_BUREAU         as bureau_loan_id,  -- the grain: one prior loan
    CREDIT_ACTIVE        as credit_status,   -- 'Active', 'Closed', etc.
    CREDIT_DAY_OVERDUE   as days_overdue,    -- days past due (a delinquency signal)
    AMT_CREDIT_SUM       as credit_amount,   -- total amount of that prior credit
    AMT_CREDIT_SUM_DEBT  as current_debt     -- current outstanding debt on it
from source