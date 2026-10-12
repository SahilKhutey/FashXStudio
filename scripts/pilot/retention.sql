-- Pilot Cohort Weekly Retention SQL (Rule 10.7)
WITH a AS (
  SELECT uid, cohort,
    ((created_at AT TIME ZONE 'Asia/Kolkata')::date - (min(created_at) OVER (PARTITION BY uid) AT TIME ZONE 'Asia/Kolkata')::date) AS day_n
  FROM v_pilot_events 
  WHERE event = 'app_open'
)
SELECT cohort,
  count(DISTINCT uid) FILTER (WHERE day_n BETWEEN 0 AND 6)   AS week1_active,
  count(DISTINCT uid) FILTER (WHERE day_n BETWEEN 7 AND 13)  AS week2_active,
  count(DISTINCT uid) FILTER (WHERE day_n BETWEEN 14 AND 20) AS week3_active
FROM a 
GROUP BY cohort 
ORDER BY cohort;
