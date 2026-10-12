-- Pilot Activation & Value Funnel SQL (Rule 10.7)
WITH f AS (
  SELECT uid, cohort,
    min(created_at) FILTER (WHERE event = 'signup_completed') AS signed_up,
    min(created_at) FILTER (WHERE event = 'consent_given')    AS consented,
    min(created_at) FILTER (WHERE event = 'photo_accepted')   AS photo_ok,
    min(created_at) FILTER (WHERE event = 'feed_viewed')      AS saw_feed,
    min(created_at) FILTER (WHERE event = 'tryon_completed')  AS first_tryon,
    min(created_at) FILTER (WHERE event = 'item_saved')       AS first_save,
    min(created_at) FILTER (WHERE event = 'buy_clicked')      AS first_buy
  FROM v_pilot_events 
  GROUP BY uid, cohort
)
SELECT 
  cohort,
  count(*) AS joined,
  count(consented) AS consented,
  count(photo_ok) AS photo_ok,
  count(saw_feed) AS saw_feed,
  count(first_tryon) AS tried_on,
  count(first_save) AS saved,
  count(first_buy) AS clicked_buy,
  round(percentile_cont(0.5) WITHIN GROUP (ORDER BY EXTRACT(EPOCH FROM (first_tryon - signed_up)) / 60)::numeric, 1) AS median_minutes_to_first_tryon
FROM f 
GROUP BY cohort 
ORDER BY cohort;
