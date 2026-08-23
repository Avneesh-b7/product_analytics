# Marketing-to-Customer Funnel Analysis — Project README

**Dataset:** `bigquery-public-data.ga4_obfuscated_sample_ecommerce`
**Tools:** BigQuery (sandbox) → Looker Studio
**Date range:** 2020-11-01 to 2021-01-31 (92 days, 4,295,584 events, 270,154 users)
**Goal:** Build a rigorous, defensible funnel analysis as a portfolio project, demonstrating a methodology that generalizes to other funnel-shaped conversion problems (e.g. B2B marketing-channel-to-lead funnels).

---

## 1. The Funnel

| Stage          | Event              | Why this event                                                      |
| -------------- | ------------------ | ------------------------------------------------------------------- |
| 1. Entry       | `session_start`    | Captures all sessions, including returning users.                   |
| 2. Browse      | `view_item`        | First deliberate product view — real interest, not passive landing. |
| 3. Add to Cart | `add_to_cart`      | First explicit purchase-intent signal.                              |
| 4. Checkout    | `begin_checkout`   | User has committed to attempting a purchase.                        |
| 5. Payment     | `add_payment_info` | Deep-funnel commitment — payment details entered.                   |
| 6. Purchase    | `purchase`         | Conversion.                                                         |

**Events considered and deliberately excluded:**

- `user_engagement`, `first_visit`, `page_view` — too passive to serve as meaningful gates.
- `add_shipping_info` — ~99.99% overlap with `begin_checkout`; treated as a near-duplicate, not a separate stage.
- `view_promotion` — passive impression, not an action.
- `select_promotion` — deliberate, but kept as an optional segment dimension rather than a mandatory sequential stage.

---

## 2. Channel Attribution

**Model:** First-touch, strictly anchored to the user's true first session — never re-anchored to a later, more "convenient" session.

**Why not multi-touch:** multi-touch answers a budget-allocation question ("how much credit does each channel deserve"). This funnel answers a drop-off question ("which channel converts through the funnel better"). Shelved as an optional future project, not needed here.

**Known limitation:** first-touch undercounts users who convert slowly across multiple sessions — real engagement, just not credited past the window. Accepted tradeoff, meant to be paired with a separate engagement/retention view later, not fixed inside this funnel.

---

## 3. Conversion Window & Population

**Window: 30 days** from each user's first `session_start`.

Chosen from the days-to-purchase distribution across 4,372 converters:

| Percentile | Days |
| ---------- | ---- |
| p50        | 0    |
| p90        | 19   |
| p95        | 29   |
| p99        | 59   |
| max        | 89   |

30 days sits between p90 and p95 — captures the large majority of real converters while excluding genuine long-tail outliers that likely represent a disconnected, later purchase rather than a continuation of the original visit.

**Two different reasons a real converter can look like a drop-off — worth keeping distinct:**

- **Window truncation:** the user got their full 30-day window, they just converted slower than that.
- **Right-censoring:** the user never got a full 30-day window at all, because the dataset ended too soon after they arrived.

**Fix for right-censoring:** only users whose first `session_start` occurred on or before 2021-01-01 are included, guaranteeing everyone included had the full 30 days to convert.

---

## 4. Build Process — What Was Actually Done

### Profiling (Phase 2)

Before building anything: checked for nulls on key fields, checked for exact duplicate events, checked for date-coverage gaps across the 92-day range, and manually spot-checked one purchasing user's event sequence for sane ordering. All clean.

### Join (Phase 4)

Six stage CTEs each collapse the raw event stream to one row per user via `MIN(event_timestamp)` — this is what enforces first-touch. The main funnel table `LEFT JOIN`s every downstream stage onto `first_session`, which is the choice that preserves drop-off users as `NULL` rows instead of silently deleting them. The 30-day window is enforced inside each join's `ON` clause (not `WHERE`), which is what makes "dropped off" and "converted but outside window" distinguishable at all.

**Bug found and fixed:** the first version of the window logic used day-level `TIMESTAMP_DIFF`, which rounds by calendar date rather than elapsed time — this let some stage events slip through even when they technically preceded the session on the same calendar day. Switched to precise `TIMESTAMP_MICROS` comparisons everywhere; confirmed via re-run that this dropped the resulting chronology errors from 213 to 0.

### Validate (Phase 5)

Built two diagnostic fields on top of the join: `chronology_status` (flags any stage timestamped before its immediately preceding stage) and `missing_step` (flags the first missing intermediate stage). Three anomalies were investigated and resolved:

1. **784 users (~0.4%)** with `begin_checkout` timestamped before their first `add_to_cart` — investigated and attributed to a client-side event-ordering artifact, not a real behavioral sequence. **Kept as-is** — this is ambiguity in _how_ something was logged, not _whether_ it happened, and excluding it would be an arbitrary call.
2. **3,648 users missing `add_to_cart`** — consistent with the broader event audit (view_item: 61,252 users vs. add_to_cart: 12,545 users). This is the funnel's real, core drop-off finding, not a data problem — kept as the headline result.
3. **A subset of those 3,648 who still have a `purchase` event** — investigated to rule out a "buy now" path. Confirmed to be a genuine `add_to_cart` tracking gap (the event just didn't fire). **Data left completely unmodified** — no backfilling. Documented as a caveat: the `add_to_cart` count should be read as a slight undercount.

### Parameterize (Phase 6)

Hardcoded values (the 30-day window, the right-censoring cutoff date) were converted into `DECLARE`d variables at the top of the script, so the query is reusable without editing the query body. Re-ran after parameterizing and confirmed identical stage counts to before — parameterizing changed nothing about the output, only where the values live.

---

## 5. Results

Stage counts, conversion %, and drop-off % were computed both overall and cut by `channel_group` (see query outputs — not reproduced here since these will be finalized/visualized in Looker Studio in Phase 8).

---

## 6. Known Caveats (Full List)

1. ~5–10% of real converters (p90–p99 tail) are excluded from "converted" status due to the 30-day window — they did convert, just outside the defined window.
2. First-touch attribution undercounts users who convert slowly across multiple sessions.
3. Right-censoring: users whose first session is after 2021-01-01 are excluded entirely, since they didn't have a fair chance to convert within the window.
4. Some `traffic_source.medium` / `source` / `campaign` values are obfuscated (`<Other>`, `(data deleted)`) — privacy-masking artifacts, not real values, flagged via `is_*_obfuscated` fields rather than guessed at.
5. This is a retrospective, single-snapshot funnel over a fixed 92-day dataset, not a live rolling-cohort funnel.
6. Dataset is ecommerce (B2C, single purchase event = conversion) — a B2B funnel (e.g. marketing channel to qualified lead) would be structurally different, needing event-to-CRM-record joins instead of pure event-to-event joins.
7. ~0.4% of users (784) show a `begin_checkout` timestamp preceding their first `add_to_cart` — likely a client-side event-ordering artifact. Retained as-is.
8. A small number of users show `purchase` with no corresponding `add_to_cart` — a tracking gap, not a true skip. `add_to_cart` count should be read as a slight undercount.

---

## 7. What's Left

- **Phase 8 — Visualization (Looker Studio):** stage-count output has been reshaped from wide (stages as columns) to long (one row per stage, with `pct_of_total_users` and `pct_of_prev_stage`) — both overall and split by `channel_group` — since that's what funnel-chart visuals expect. Remaining: connect these queries to Looker Studio and build the funnel chart and channel breakdown visuals.
- **Phase 9 — Generalize the approach:** adapt this same methodology to a B2B-style marketing-channel-to-lead funnel, accounting for the structural differences noted in caveat 6.

---

_This README consolidates the full Phase 1–6 spec, build log, and decisions into one document. Detailed per-phase reasoning also lives in `phase1_spec.md` and `phase4_5_join_and_validation.md`._
