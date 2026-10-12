-- Pilot Feed Relevance & Signal Quality SQL (Rule 10.7)
WITH impressions AS (
  SELECT 
    cohort,
    count(*) AS total_impressions,
    count(DISTINCT garment_id) AS distinct_garments_seen
  FROM v_pilot_feed_impressions
  GROUP BY cohort
),
signals AS (
  SELECT 
    cohort,
    count(*) FILTER (WHERE action = 'like') AS likes,
    count(*) FILTER (WHERE action = 'hide') AS hides,
    count(*) FILTER (WHERE action = 'not_interested') AS not_interested
  FROM v_pilot_feed_signals
  GROUP BY cohort
)
SELECT 
  i.cohort,
  i.total_impressions,
  coalesce(s.likes, 0) AS likes,
  coalesce(s.hides, 0) AS hides,
  coalesce(s.not_interested, 0) AS not_interested,
  round(((coalesce(s.hides, 0) + coalesce(s.not_interested, 0))::numeric / nullif(i.total_impressions, 0)) * 100, 2) AS negative_signal_rate_pct
FROM impressions i
LEFT JOIN signals s ON i.cohort = s.cohort
ORDER BY i.cohort;
