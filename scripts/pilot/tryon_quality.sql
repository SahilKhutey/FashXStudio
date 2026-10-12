-- Pilot Try-On Quality, Latency & Error Analysis SQL (Rule 10.7)
SELECT 
  j.cohort,
  count(*) AS total_jobs,
  count(*) FILTER (WHERE j.status = 'completed') AS completed_jobs,
  count(*) FILTER (WHERE j.status = 'failed') AS failed_jobs,
  round((count(*) FILTER (WHERE j.status = 'completed')::numeric / nullif(count(*), 0)) * 100, 1) AS success_rate_pct,
  round(percentile_cont(0.5) WITHIN GROUP (ORDER BY j.duration_seconds)::numeric, 1) AS p50_latency_sec,
  round(percentile_cont(0.95) WITHIN GROUP (ORDER BY j.duration_seconds)::numeric, 1) AS p95_latency_sec,
  round(avg(f.purchase_confidence)::numeric, 2) AS mean_rating
FROM v_pilot_tryon_jobs j
LEFT JOIN v_pilot_tryon_feedback f ON j.job_id = f.tryon_job_id
GROUP BY j.cohort
ORDER BY j.cohort;
