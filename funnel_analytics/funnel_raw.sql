--complete query -- + parameterised ---
DECLARE CUTOFF_DATE  DATE DEFAULT '2021-01-01';
DECLARE WINDOW_DAYS  INT64 DEFAULT 30 ;



--dim channel q
CREATE OR REPLACE VIEW `conversionfunnelanalytics.staging.dim_channel` AS
SELECT
  user_pseudo_id,
  event_name,
   (SELECT value.int_value
     FROM UNNEST(event_params)
     WHERE key = 'ga_session_number') AS session_number,
  event_timestamp,
  traffic_source.medium AS raw_medium,
  traffic_source.source AS raw_source,
  traffic_source.name AS raw_campaign,
  CASE
    WHEN traffic_source.medium = 'cpc' THEN 'Paid'
    WHEN traffic_source.medium = 'organic' THEN 'Organic'
    WHEN traffic_source.medium = '(none)' THEN 'Direct'
    WHEN traffic_source.medium = 'referral' THEN 'Referral'
    ELSE 'Unknown'
  END AS channel_group,
  traffic_source.source IN ('<Other>', '(data deleted)') AS is_source_obfuscated,
  traffic_source.name IN ('<Other>', '(data deleted)') AS is_campaign_obfuscated,
  traffic_source.medium IN ('<Other>', '(data deleted)') AS is_medium_obfuscated
FROM `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`;





-- funnel_raw q
-- things to parametrise - time window(30 d currently) ; and cutoff date
-- CREATE OR REPLACE VIEW `conversionfunnelanalytics.staging.funnel_raw` AS (
WITH dim_channel_table AS (
SELECT user_pseudo_id,event_name,channel_group,is_campaign_obfuscated,is_medium_obfuscated,is_source_obfuscated,MIN(event_timestamp) AS min_session
FROM staging.dim_channel
WHERE event_name='session_start'
GROUP BY 1,2,3,4,5,6
),
first_session AS (
SELECT user_pseudo_id,MIN(event_timestamp) AS first_session
FROM `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`
WHERE event_name='session_start'
GROUP BY 1
),
view_item AS (
SELECT user_pseudo_id,MIN(event_timestamp) AS first_view_item
FROM `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`
WHERE event_name='view_item'
GROUP BY 1
),
add_to_cart AS (
SELECT user_pseudo_id,MIN(event_timestamp) AS first_add_to_cart
FROM `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`
WHERE event_name='add_to_cart'
GROUP BY 1
),
begin_checkout AS (
SELECT user_pseudo_id,MIN(event_timestamp) AS first_begin_checkout
FROM `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`
WHERE event_name='begin_checkout'
GROUP BY 1
),
add_payment_info AS (
SELECT user_pseudo_id,MIN(event_timestamp) AS first_add_payment_info
FROM `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`
WHERE event_name='add_payment_info'
GROUP BY 1
),
purchase AS (
SELECT user_pseudo_id,MIN(event_timestamp) AS first_purchase
FROM `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`
WHERE event_name='purchase'
GROUP BY 1
),
funnel_table AS (
SELECT fs.user_pseudo_id,dc.channel_group,fs.first_session,vi.first_view_item,atc.first_add_to_cart,bc.first_begin_checkout,api.first_add_payment_info,p.first_purchase
FROM first_session fs
LEFT JOIN view_item vi
ON fs.user_pseudo_id=vi.user_pseudo_id
AND TIMESTAMP_MICROS(vi.first_view_item) BETWEEN TIMESTAMP_MICROS(fs.first_session) AND TIMESTAMP_ADD(TIMESTAMP_MICROS(fs.first_session),INTERVAL WINDOW_DAYS DAY)
LEFT JOIN add_to_cart atc
ON fs.user_pseudo_id=atc.user_pseudo_id
AND TIMESTAMP_MICROS(atc.first_add_to_cart) BETWEEN TIMESTAMP_MICROS(fs.first_session) AND TIMESTAMP_ADD(TIMESTAMP_MICROS(fs.first_session),INTERVAL WINDOW_DAYS DAY)
LEFT JOIN begin_checkout bc
ON fs.user_pseudo_id=bc.user_pseudo_id
AND TIMESTAMP_MICROS(bc.first_begin_checkout) BETWEEN TIMESTAMP_MICROS(fs.first_session) AND TIMESTAMP_ADD(TIMESTAMP_MICROS(fs.first_session),INTERVAL WINDOW_DAYS DAY)
LEFT JOIN add_payment_info api
ON fs.user_pseudo_id=api.user_pseudo_id
AND TIMESTAMP_MICROS(api.first_add_payment_info) BETWEEN TIMESTAMP_MICROS(fs.first_session) AND TIMESTAMP_ADD(TIMESTAMP_MICROS(fs.first_session),INTERVAL WINDOW_DAYS DAY)
LEFT JOIN purchase p
ON fs.user_pseudo_id=p.user_pseudo_id
AND TIMESTAMP_MICROS(p.first_purchase) BETWEEN TIMESTAMP_MICROS(fs.first_session) AND TIMESTAMP_ADD(TIMESTAMP_MICROS(fs.first_session),INTERVAL WINDOW_DAYS DAY)
LEFT JOIN dim_channel_table dc
ON fs.user_pseudo_id=dc.user_pseudo_id
AND fs.first_session=dc.min_session
WHERE TIMESTAMP_MICROS(fs.first_session)<TIMESTAMP(CUTOFF_DATE)
),
final_table AS (
SELECT user_pseudo_id,channel_group,TIMESTAMP_MICROS(first_session) AS first_session,TIMESTAMP_MICROS(first_view_item) AS first_view_item,TIMESTAMP_MICROS(first_add_to_cart) AS first_add_to_cart,TIMESTAMP_MICROS(first_begin_checkout) AS first_begin_checkout,TIMESTAMP_MICROS(first_add_payment_info) AS first_add_payment_info,TIMESTAMP_MICROS(first_purchase) AS first_purchase,
CASE
WHEN first_session IS NULL THEN 'No session'
WHEN first_view_item IS NOT NULL AND first_view_item<first_session THEN 'Invalid chronology: view_item before session'
WHEN first_add_to_cart IS NOT NULL AND first_view_item IS NOT NULL AND first_add_to_cart<first_view_item THEN 'Invalid chronology: add_to_cart before view_item'
WHEN first_begin_checkout IS NOT NULL AND first_add_to_cart IS NOT NULL AND first_begin_checkout<first_add_to_cart THEN 'Invalid chronology: checkout before add_to_cart'
WHEN first_add_payment_info IS NOT NULL AND first_begin_checkout IS NOT NULL AND first_add_payment_info<first_begin_checkout THEN 'Invalid chronology: payment_info before checkout'
WHEN first_purchase IS NOT NULL AND first_add_payment_info IS NOT NULL AND first_purchase<first_add_payment_info THEN 'Invalid chronology: purchase before payment_info'
ELSE 'Chronologically valid'
END AS chronology_status,
CASE
WHEN first_purchase IS NOT NULL AND first_add_payment_info IS NULL AND first_begin_checkout IS NOT NULL THEN 'Missing payment_info'
WHEN first_purchase IS NOT NULL AND first_begin_checkout IS NULL THEN 'Missing begin_checkout'
WHEN first_begin_checkout IS NOT NULL AND first_add_to_cart IS NULL THEN 'Missing add_to_cart'
WHEN first_add_to_cart IS NOT NULL AND first_view_item IS NULL THEN 'Missing view_item'
ELSE 'No missing intermediate step'
END AS missing_step,
IF(first_session IS NOT NULL,1,0) AS had_session,
IF(first_view_item IS NOT NULL,1,0) AS had_view_item,
IF(first_add_to_cart IS NOT NULL,1,0) AS had_add_to_cart,
IF(first_begin_checkout IS NOT NULL,1,0) AS had_begin_checkout,
IF(first_add_payment_info IS NOT NULL,1,0) AS had_payment_info,
IF(first_purchase IS NOT NULL,1,0) AS had_purchase
FROM funnel_table
)
SELECT * FROM final_table;








-- -- conversion metrics q --
WITH stage_counts AS (
SELECT
-- channel_group,
COUNT(DISTINCT user_pseudo_id) AS total_users,
COUNT(DISTINCT CASE WHEN had_session=1 THEN user_pseudo_id END) AS session_stage,
COUNT(DISTINCT CASE WHEN had_view_item=1 THEN user_pseudo_id END) AS view_item_stage,
COUNT(DISTINCT CASE WHEN had_add_to_cart=1 THEN user_pseudo_id END) AS add_to_cart_stage,
COUNT(DISTINCT CASE WHEN had_begin_checkout=1 THEN user_pseudo_id END) AS begin_checkout_stage,
COUNT(DISTINCT CASE WHEN had_payment_info=1 THEN user_pseudo_id END) AS payment_info_stage,
COUNT(DISTINCT CASE WHEN had_purchase=1 THEN user_pseudo_id END) AS purchase_stage
FROM staging.funnel_raw
-- group by 1
)
SELECT
'Users' AS metric,
total_users,
session_stage,
view_item_stage,
add_to_cart_stage,
begin_checkout_stage,
payment_info_stage,
purchase_stage
FROM stage_counts
UNION ALL
SELECT
'% of total users' AS metric,
100.0,
100.0*session_stage/total_users,
100.0*view_item_stage/total_users,
100.0*add_to_cart_stage/total_users,
100.0*begin_checkout_stage/total_users,
100.0*payment_info_stage/total_users,
100.0*purchase_stage/total_users
FROM stage_counts;











