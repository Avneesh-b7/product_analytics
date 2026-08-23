# Phase 1 Spec — Marketing-to-Customer Funnel Analysis

**Dataset:** `bigquery-public-data.ga4_obfuscated_sample_ecommerce`
**Tools:** BigQuery (sandbox) → Looker Studio
**Date range:** 2020-11-01 to 2021-01-31 (92 days)

---

## 1. Funnel Stages

| Stage          | Event              | Rationale                                                                                            |
| -------------- | ------------------ | ---------------------------------------------------------------------------------------------------- |
| 1. Entry       | `session_start`    | Captures all sessions, including returning users (unlike `first_visit`, which only fires once ever). |
| 2. Browse      | `view_item`        | First deliberate product view — signals real interest, not just passive landing.                     |
| 3. Add to Cart | `add_to_cart`      | First explicit purchase intent signal.                                                               |
| 4. Checkout    | `begin_checkout`   | User has committed to attempting a purchase.                                                         |
| 5. Payment     | `add_payment_info` | Payment details entered — deep-funnel commitment.                                                    |
| 6. Purchase    | `purchase`         | Conversion.                                                                                          |

### Events considered and excluded

- **`user_engagement`, `first_visit`, `page_view`** — too passive / high-volume to serve as meaningful funnel gates.
- **`add_shipping_info`** — 9,713 of 9,715 `begin_checkout` users also fired this event (~99.99% overlap). Treated as a near-duplicate of `begin_checkout`, not a separate stage. Kept as a staging view for potential deeper analysis later.
- **`view_promotion`** — passive impression, not a deliberate action.
- **`select_promotion`** — deliberate click, but treated as an optional cross-cut segment/dimension on the funnel rather than a mandatory sequential stage. Not yet built.

### Open validation item

- Overlap between `begin_checkout` (9,715 users) and `add_payment_info` (5,751 users) has not yet been checked to confirm the gap is genuine drop-off rather than a data/tracking artifact. Recommended before final reporting.

---

## 2. Channel Attribution

**Model:** First-touch, strictly anchored to the user's true first session.

- Every user is assigned exactly one `channel_group` (Paid / Organic / Direct / Referral / Unknown), based on `traffic_source.medium` at their **very first** `session_start` event.
- No re-anchoring: even if a later session appears more "convenient" for window purposes, the first real session is always used.
- Rationale: re-anchoring to a later session to make a user appear converted within a window would open the door to selectively choosing whichever session flatters the metric. A strict, non-negotiable first-touch rule keeps the metric objective and reproducible.

**Known limitation:** first-touch will undercount users who took multiple sessions and a long time to convert — their engagement is real, but the funnel (by definition) won't credit it past the window. This is expected to be paired with a separate retention/engagement view later, not fixed within the funnel itself.

**Multi-touch / linear attribution** was considered and explicitly shelved — it answers a budget-allocation question ("how much credit does each channel deserve"), not the funnel's drop-off question ("which channel converts through the funnel better"). Flagged as an optional Phase 10 follow-on project.

---

## 3. Conversion Window

**Window: 30 days**, measured from each user's first `session_start` to each subsequent funnel stage.

### How this was chosen

Days-to-purchase distribution across 4,372 converters:

| Percentile | Days |
| ---------- | ---- |
| p50        | 0    |
| p90        | 19   |
| p95        | 29   |
| p99        | 59   |
| max        | 89   |

30 days sits between p90 and p95 — capturing roughly 90–95% of real converters as legitimate funnel completions, while excluding genuine long-tail outliers (p99+) who likely represent a disconnected, unrelated later purchase rather than a continuation of the original visit.

### What happens to users outside the window

Users whose real purchase falls after their personal 30-day cutoff are **not excluded from the dataset** — they still appear in earlier funnel stages (session_start, view_item, add_to_cart, etc.). They are simply **not counted as having reached "purchase"** in this funnel, because their actual purchase timestamp falls outside the join condition to that stage. This means the funnel will slightly undercount true conversion rate for slow converters — an accepted, documented tradeoff, not a data bug.

**Note — not the same as right-censoring (below):** this case is about a user who _got_ their full 30-day window and simply converted slower than that. Right-censoring, by contrast, is about a user who never got a full 30-day window in the first place, because the dataset ended too soon after they arrived. Same symptom (a real converter looks like a drop-off), different cause — one is "gave them the full window, they were just slow," the other is "never gave them the full window at all."

### Right-censoring adjustment

Dataset spans only 92 days. A user whose first session falls too close to the end of the dataset cannot possibly have a full 30-day window to convert within the observed data — including them would artificially bias later cohorts toward looking like they convert less, purely due to lack of observation time, not real behavior.

**Fix applied:** only users whose first `session_start` occurred **on or before 2021-01-01** are included in the funnel population. This guarantees every included user had the full 30 days to convert, so no cohort is penalized for arriving late in the dataset.

```sql
WHERE first_session_date <= '2021-01-01'
```

---

## 4. Known Caveats (full list)

1. ~5–10% of real converters (p90–p99 tail) are excluded from "converted" status due to the 30-day window — they did convert, just outside the defined window.
2. First-touch attribution undercounts users who convert slowly across multiple sessions — a known, accepted limitation, intended to be paired with a separate engagement/retention metric rather than fixed inside the funnel itself.
3. Right-censoring: users whose first session is after 2021-01-01 are excluded from this funnel entirely, since they didn't have a fair chance to convert within the window given the dataset's end date.
4. Some `traffic_source.medium` / `source` / `campaign` values are obfuscated in this dataset (`<Other>`, `(data deleted)`) — these are privacy-masking artifacts, not real channel values, and are flagged via `is_source_obfuscated` / `is_campaign_obfuscated` / `is_medium_obfuscated` fields in `dim_channel` rather than guessed at.
5. This is a retrospective, single-snapshot funnel over a fixed 92-day dataset — not a live, rolling-cohort funnel as would typically run in production. In a live system, this same logic would normally be recomputed on a rolling cadence and sliced by weekly/monthly acquisition cohort.

---

_Status: Phase 1 complete. Next: Phase 2 — profile raw data (nulls, dedup, date coverage, spot-checks)._
