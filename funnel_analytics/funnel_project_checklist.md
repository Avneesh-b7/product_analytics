# Marketing-to-customer funnel — project checklist

Dataset: `bigquery-public-data.ga4_obfuscated_sample_ecommerce`
Tools: BigQuery (sandbox) → Looker Studio

## Phase 1 — Define the spec

- [ ] Run event-name audit query (distinct events, counts, user counts)
- [ ] Run traffic-source audit query (medium/source split at session_start)
- [ ] Pick exact stages and the event/field that defines each one
- [ ] Decide attribution model (first-touch vs last-touch)
- [ ] Decide conversion window (e.g. 30 days)
- [ ] Write the spec down (1-pager: stages, definitions, attribution, window, known caveats)

## Phase 2 — Profile the raw data

- [ ] Check null rates on `traffic_source.medium`, `traffic_source.source`, `user_pseudo_id`
- [ ] Check for duplicate events per user per day (dedup risk)
- [ ] Confirm date range coverage (min/max event date)
- [ ] Spot-check a few users manually — does their event sequence make sense?

## Phase 3 — Build staging views

- [ ] `stg_entry` — first paid/organic touch per user
- [ ] `stg_lead` — signup/account-creation equivalent event
- [ ] `stg_activation` — first meaningful product action
- [ ] `stg_trial` — begin_checkout / cart equivalent
- [ ] `stg_customer` — purchase event

## Phase 4 — Join the funnel

- [ ] LEFT JOIN each stage onto the previous, by user_pseudo_id
- [ ] Add "happened after previous stage AND within window" condition
- [ ] Aggregate into stage counts + conversion % table
- [ ] Add channel (paid/organic) as a cross-cut dimension

## Phase 5 — Validate

- [ ] Compare funnel purchase count against raw COUNT(\*) of purchase events
- [ ] Check no stage conversion % exceeds 100%
- [ ] Check drop-off is never negative
- [ ] Re-run on a smaller date slice and sanity check the numbers scale sensibly

## Phase 6 — Parameterize (optional, time-permitting)

- [ ] Convert hardcoded dates to variables
- [ ] Convert channel filter to a parameter

## Phase 7 — Document

- [ ] Write README: stage definitions, attribution choice, window choice, limitations
- [ ] Note any data quality issues found in Phase 2

## Phase 8 — Visualize & package

- [ ] Connect BigQuery table/query to Looker Studio
- [ ] Build funnel chart (stage-by-stage drop-off)
- [ ] Add channel breakdown view (paid vs organic)
- [ ] Save SQL + views + README together (e.g. GitHub repo)
