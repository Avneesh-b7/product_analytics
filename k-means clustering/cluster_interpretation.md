# Customer Segment Interpretation (RFM K-Means, K=4)

Business interpretation of the four customer segments produced by the K-means clustering in `kmeans_clustering.ipynb`. Recency is measured in **raw days since last purchase**.

## Cluster 0 — Champions / Premium Customers

**Profile:** High monetary value, high frequency, low recency days (i.e. recently active).

**Segment size:** 824 of 3,811 customers (~22%), contributing ~45% of total revenue.

- **Priority:** Retain, not acquire. This segment drives a disproportionate share of revenue relative to its size.
- **Actions:** Loyalty/VIP tier, early access to new products or drops, personalized outreach, exclusive perks — anything that reinforces the relationship rather than pushes another transaction.
- **Watch metric:** Recency drift. A Champion whose days-since-last-purchase starts climbing is your earliest churn signal — they'd typically drift through Cluster 2 (moderate) territory before ever reaching Cluster 1 (dormant), so catching the slide early, while they still resemble Cluster 2, is worth more than winning back a lapsed customer after the fact.
- **Secondary use:** Great source for referral programs, reviews/testimonials, and beta-testing new features, since they're already bought-in.

## Cluster 1 — Lost / Dormant Customers

**Profile:** Low monetary value, low frequency, high recency days (i.e. long time since last purchase).

**Segment size:** 1,110 of 3,811 customers (~29%, the largest segment), contributing only ~8% of total revenue.

- Spend little, buy rarely, haven't purchased in a long time. This segment splits into two populations worth separating before acting:
  - **Previously active customers who drifted away** — worth a win-back nudge (reactivation email, targeted discount) since they've shown buying intent before.
  - **One-and-done low-value buyers** — never really engaged; low ROI to chase, better to fix the onboarding/second-purchase funnel so fewer future customers land here.
- **Next step:** Given it's the biggest segment, splitting it (e.g. by first-purchase value or historical max frequency) before deciding how much win-back budget to spend is the highest-leverage next analysis.

## Cluster 2 — Growth / Potential Loyalists

**Profile:** Moderate monetary value (median ~$950), moderate-to-good frequency (median ~3), decent recency (median ~50-80 days, second-best after Cluster 0).

**Segment size:** 1,028 of 3,811 customers (~27%), contributing ~35% of total revenue.

These customers are engaged and spending reasonably well, but haven't reached Champion-level frequency or spend yet. They're the clearest upsell/cross-sell opportunity — the gap between where they are and Cluster 0 is the biggest addressable growth lever in the dataset.

- **Increase purchase frequency:** Personalized product recommendations, replenishment reminders, subscribe-and-save style nudges.
- **Increase basket size:** Bundle offers, free-shipping thresholds, cross-sell at checkout.
- **Loyalty program enrollment:** Give them a reason to consolidate spend with you rather than splitting it across competitors.
- **Watch metric:** Track how many Cluster 2 customers migrate into Cluster 0 over time — that's a strong success metric for any nurture campaign targeting this segment.

## Cluster 3 — Occasional / New Customers

**Profile:** Low monetary value, low frequency, but low (good) recency days (median ~20 days, second-most recent after Cluster 0).

**Segment size:** 849 of 3,811 customers (~22%).

These customers just bought recently, but they don't spend much or buy often — a "recent but not yet valuable" segment. Two likely sub-populations hide in here, and the play differs a lot depending on which one dominates:

- **New customers still ramping up** — made a small first (or early) purchase, haven't had time to build frequency/spend yet. This is the acquisition funnel's freshest cohort.
- **Low-intent occasional shoppers** — buy small amounts sporadically and always have (e.g. gift buyers, one-category shoppers), unlikely to ever become high-value regardless of nurturing.

Actions:

- **Onboarding/activation campaigns:** Welcome series, second-purchase incentive, product discovery nudges — aimed at converting the "new customer" sub-population into Cluster 2 territory.
- **Segment further before investing:** Cut this cluster by account age (days since first purchase) to separate "genuinely new" from "long-tenured but always low-value" — that tells you how much of this cluster is actually a growth opportunity vs. a permanently low-intent group not worth heavy investment

- **Low cost-per-touch tactics** (email, app nudges) rather than expensive incentives, since value-per-customer here is still unproven.
