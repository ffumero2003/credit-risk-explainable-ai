-- Staging model for the raw applications table.
-- Grain: one row per applicant (SK_ID_CURR).
-- Light cleaning only: rename to clean names, fix sentinel values, select the
-- columns we'll actually use. No joins or aggregation here (that comes later).

with source as (
    -- read straight from the raw table we declared in _sources.yml
    select * from {{ source('credit_raw', 'raw_applications') }}
)

select
    -- identifier + label
    SK_ID_CURR                     as applicant_id,
    TARGET                         as target_default,   -- 1 = payment difficulties, 0 = repaid

    -- demographics
    CODE_GENDER                    as gender,
    round(-DAYS_BIRTH / 365.25, 1) as age_years,        -- DAYS_BIRTH is stored as negative days

    -- employment length: 365243 is a junk placeholder (unemployed/pensioners) -> NULL
    case
        when DAYS_EMPLOYED = 365243 then null
        else round(-DAYS_EMPLOYED / 365.25, 1)
    end                            as years_employed,

    -- finances
    AMT_INCOME_TOTAL               as annual_income,
    AMT_CREDIT                     as loan_amount,
    AMT_ANNUITY                    as loan_annuity,

    -- external credit scores (strong predictors of default)
    EXT_SOURCE_1                   as ext_source_1,
    EXT_SOURCE_2                   as ext_source_2,
    EXT_SOURCE_3                   as ext_source_3,

    -- categorical attributes
    NAME_EDUCATION_TYPE            as education_type,
    NAME_FAMILY_STATUS             as family_status,
    NAME_INCOME_TYPE               as income_type,
    CNT_CHILDREN                   as num_children,
    FLAG_OWN_CAR                   as owns_car,
    FLAG_OWN_REALTY                as owns_realty

from source