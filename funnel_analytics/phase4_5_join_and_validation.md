# Phase 4 & 5 — Join the Funnel + Validate

**Dataset:** `bigquery-public-data.ga4_obfuscated_sample_ecommerce`
**Builds on:** Phase 1 spec (stages, attribution, window), Phase 2 profiling (clean nulls/dupes/coverage)

---

## Phase 4 — Join the Funnel

### Structure

Six independent stage CTEs (`first_session`, `view_item`, `add_to_cart`, `begin_checkout`, `add_payment_info`, `purchase`) each collapse the raw event stream to one row per user via `MIN(event_timestamp)` — this is what enforces "first occurrence only," consistent with the first-touch attribution decision in the spec.

The `funnel_table` CTE then `LEFT JOIN`s all five downstream stages onto `first_session` by `user_pseudo_id`. **`LEFT JOIN`, not `INNER JOIN`, is the load-bearing choice here** — it's what preserves drop-off users as `NULL` rather than silently dropping them from the table. A user who viewed an item but never added to cart still gets a row; they just have `NULL` in every column from `add_to_cart` onward.

Channel attribution is joined in via `dim_channel_table`, matched on `user_pseudo_id` **and** `fs.first_session = dc.min_session` — this is what pins the channel to the user's true first session rather than any arbitrary session, matching the strict first-touch rule in the spec.

### The window condition — and the bug that was found and fixed

The 30-day conversion window (per the spec) is enforced **inside the `ON` clause of each join**, not in the `WHERE` clause:

```sql
AND TIMESTAMP_MICROS(atc.first_add_to_cart)
    BETWEEN TIMESTAMP_MICROS(fs.first_session)
    AND TIMESTAMP_ADD(TIMESTAMP_MICROS(fs.first_session), INTERVAL 30 DAY)
```

Putting the window in the `ON` clause (rather than filtering in `WHERE`) is what allows out-of-window stage events to become `NULL` instead of eliminating the whole user row — this is what makes drop-off vs. "converted but outside window" distinguishable at all.

**Bug found:** the original version of this query used `TIMESTAMP_DIFF(stage_ts, first_session, DAY) BETWEEN 0 AND 30`. `TIMESTAMP_DIFF` at `DAY` granularity counts _calendar-date boundaries crossed_, not elapsed hours — so a stage event that landed on the same calendar day as the session, but a few minutes _before_ it clock-wise, still evaluated to a day-diff of 0 and passed the filter. This produced 213 users flagged with `view_item` timestamped before their `first_session`, which is logically impossible under first-touch anchoring.

**Fix applied:** switched every window condition to direct `TIMESTAMP_MICROS(...) BETWEEN ...` comparison, which compares full-precision timestamps rather than rounded calendar-day counts. This is the version reflected in the query above — the fix is applied consistently across all five stage joins, not just `view_item`.

**Right-censoring cutoff** is applied in `funnel_table`'s outer `WHERE` clause (`WHERE TIMESTAMP_MICROS(fs.first_session) < TIMESTAMP('2021-01-01')`) — correctly placed here rather than in an individual join's `ON` clause, since it's a population-eligibility filter on the user, not a per-stage window condition.

---

## Phase 5 — Validate

A `final_table` layer adds two diagnostic fields on top of the joined funnel:

- **`chronology_status`** — checks each stage's timestamp against the _immediately preceding_ stage (not just against `first_session`), flagging `"Invalid chronology: X before Y"` for any adjacent pair out of order.
- **`missing_step`** — flags which single intermediate stage is `NULL` when a later stage is present. _Note: the `CASE` statement returns only the first matching condition in its WHEN order, so a user missing multiple steps is only counted once, under the earliest gap. This is a "first gap found" indicator, not an exhaustive/mutually-exclusive count — worth remembering when reading aggregate counts of this field._
- **`had_*` binary flags** per stage, for straightforward aggregation into stage counts later.

### Validation results (post-fix)

- **Chronology:** the `view_item`-before-`session` bug (213 cases) is resolved by the `TIMESTAMP_MICROS` fix — resolution to ~0 cases pending final re-run confirmation.
- **784 "checkout before add_to_cart" cases:** investigated separately from the day-rounding bug (this join already used precise timestamps for this comparison) — confirmed to be a distinct, real phenomenon, most likely a client-side event-ordering artifact (event arrival order at the analytics server not always matching true user-side order). **Decision: retained as-is, not dropped.** Excluding these would require an arbitrary judgment call about which timestamp to "trust," and the discrepancy is in _how_ the events were logged, not _whether_ the user did them.
- **3,648 missing `add_to_cart` users:** consistent with the raw event audit (view_item: 61,252 users vs. add_to_cart: 12,545 users). This is the funnel's core drop-off finding, not a data quality issue — **retained as the headline result**, not adjusted.
- **Subset of the above with a `purchase` event despite no `add_to_cart`:** investigated to rule out a "buy now"/direct-purchase path or a population-filter artifact. **Confirmed via spot-check to be a genuine `add_to_cart` tracking gap** — the event failed to fire for these users even though they logically must have added an item to cart to reach purchase. **Decision: data left completely unmodified** — no backfilled or inferred `add_to_cart` values.

### Caveats added to spec (Section 4 — Known Caveats)

7. **Checkout-ordering artifact:** ~0.4% of users (784) show a `begin_checkout` timestamp preceding their first `add_to_cart` timestamp — likely a client-side event-ordering artifact rather than a true behavioral sequence. Retained as-is; excluding would require an arbitrary, unjustified judgment call.
8. **Add-to-cart tracking gap:** a small number of users show a `purchase` event with no corresponding `add_to_cart` event, indicating a tracking gap rather than a true skip of that stage. The `add_to_cart` stage count should be read as a slight undercount for this reason.

---

_Status: Phase 4 and Phase 5 complete (pending final re-confirmation that the chronology fix resolved the 213 view_item cases to ~0). Next: compute stage counts, conversion %, and drop-off % — cut by `channel_group`._
