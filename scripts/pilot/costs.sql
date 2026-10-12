-- Pilot Inference Spend & Unit Economics Tracking SQL (Rule 10.7)
SELECT 
  (created_at AT TIME ZONE 'Asia/Kolkata')::date AS date_ist,
  provider,
  count(*) AS total_renders,
  count(*) FILTER (WHERE outcome = 'completed') AS successful_renders,
  count(*) FILTER (WHERE outcome = 'failed') AS failed_renders,
  round(sum(cost_usd_est)::numeric, 4) AS daily_spend_usd,
  round(avg(latency_ms)::numeric, 0) AS avg_latency_ms
FROM tryon_usage
WHERE created_at >= NOW() - INTERVAL '30 days'
GROUP BY (created_at AT TIME ZONE 'Asia/Kolkata')::date, provider
ORDER BY date_ist DESC;
