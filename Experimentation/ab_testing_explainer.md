# A/B testing

framework is simple :

1. PLAN
   - define hypothesis ( a good hypothesis should be focused on a single variable only at a time e.g. For example: “If we shorten the onboarding flow, we’ll increase activation by 15%.”)

- set primary and guardrail metrics
- determine sample sizes and test duration
  (You can think of sample size as how many people need to see your experiment to trust the results, like polling enough voters to predict an election. Estimating sample size involves factors like:
  Your current conversion rate (baseline).
  The minimum improvement you're hoping to see (expected lift) (MDE)
  Your desired confidence threshold—often set at 95%, meaning you're 95% sure the result isn’t due to chance.
  The power of your test, which reflects the likelihood of detecting a true effect if one exists)

2. RUN

3. EVALUATE
   - determine if the cariant delivered a stat sig lift on the primary metric
     (Lift: Shows how much better or worse your variant performed compared to the control. It’s expressed as a relative percentage increase or decrease.
     P-value: Tells you how likely it is that the lift seen in your sample group is due to randomness and wouldn’t accurately reflect an actual lift in the general population. A p-value of 0.05 or less typically indicates the result is statistically significant.
     Confidence interval: The range where the lift for the general population is likely to fall, based on your data. It gives you a sense of how precise your result is—narrow intervals mean high precision, while wide intervals mean more uncertainty.)

4. TAKE ACTION

- Decide next steps—deploy a variant, make no change, or revisit your hypothesis. Document learnings, share outcomes, and plan follow-ups
