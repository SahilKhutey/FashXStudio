# FashXStudio — Analytics Aggregation Engine & KPI SQL Queries

**Document ID:** `FASHX-ANL-003`  
**Version:** `1.0 — Technical Baseline`  
**Date:** `10 November 2026`  
**Scope:** `Phase 01.5 — Mathematical Queries & Scheduled Aggregation Engine`  

---

## 1. Batch Aggregation Pipeline Architecture

While real-time event counters power operational views, historical and cohort KPIs are computed via an automated daily batch pipeline:
- **Scheduler:** Celery Beat cron task running daily at `00:05:00 UTC` (`05:35:00 IST`).
- **Worker:** `fashx.workers.analytics_aggregation.run_daily_kpi_rollup`.
- **Output:** Writes immutable aggregated rows to `merchant_metrics_daily` and updates `shopper_cohorts`.

---

## 2. Production SQL Calculation Queries (14 Approved KPIs)

### 2.1 Registration Completion Rate (KPI 1.4.1)
```sql
SELECT 
    COUNT(DISTINCT CASE WHEN event_name = 'registration_completed' THEN session_id END)::FLOAT /
    NULLIF(COUNT(DISTINCT CASE WHEN event_name = 'registration_started' THEN session_id END), 0) * 100 AS reg_completion_rate
FROM analytics_events
WHERE occurred_at >= :start_date AND occurred_at < :end_date
  AND is_internal = FALSE;
```

### 2.2 Profile Completion Rate (KPI 1.4.2)
```sql
SELECT 
    COUNT(DISTINCT CASE WHEN event_name = 'profile_completed' THEN shopper_id END)::FLOAT /
    NULLIF(COUNT(DISTINCT CASE WHEN event_name = 'profile_setup_started' THEN shopper_id END), 0) * 100 AS profile_completion_rate
FROM analytics_events
WHERE occurred_at >= :start_date AND occurred_at < :end_date
  AND is_internal = FALSE;
```

### 2.3 Product Discovery Success Rate (KPI 1.4.3)
```sql
SELECT 
    COUNT(DISTINCT CASE WHEN event_name IN ('vto_started', 'look_saved') THEN session_id END)::FLOAT /
    NULLIF(COUNT(DISTINCT CASE WHEN event_name = 'product_viewed' THEN session_id END), 0) * 100 AS discovery_success_rate
FROM analytics_events
WHERE occurred_at >= :start_date AND occurred_at < :end_date
  AND is_internal = FALSE;
```

### 2.4 VTO Job Success Rate (KPI 1.4.4)
```sql
SELECT 
    COUNT(CASE WHEN status = 'completed' THEN 1 END)::FLOAT /
    NULLIF(COUNT(*), 0) * 100 AS vto_job_success_rate,
    
    COUNT(CASE WHEN status = 'completed' AND attempt_count = 1 THEN 1 END)::FLOAT /
    NULLIF(COUNT(*), 0) * 100 AS first_attempt_success_rate
FROM vto_jobs
WHERE created_at >= :start_date AND created_at < :end_date;
```

### 2.5 VTO Latency P95 (KPI 1.4.5)
```sql
SELECT 
    percentile_cont(0.50) WITHIN GROUP (ORDER BY duration_total_ms) / 1000.0 AS p50_seconds,
    percentile_cont(0.90) WITHIN GROUP (ORDER BY duration_total_ms) / 1000.0 AS p90_seconds,
    percentile_cont(0.95) WITHIN GROUP (ORDER BY duration_total_ms) / 1000.0 AS p95_seconds
FROM vto_jobs
WHERE status = 'completed'
  AND created_at >= :start_date AND created_at < :end_date;
```

### 2.6 Visual Realism & Garment Preservation Ratings (KPI 1.4.6 & 1.4.7)
```sql
SELECT 
    AVG((properties->>'visual_realism_score')::NUMERIC) AS avg_realism_score,
    COUNT(CASE WHEN (properties->>'visual_realism_score')::INT >= 4 THEN 1 END)::FLOAT / 
        NULLIF(COUNT(*), 0) * 100 AS positive_realism_rate,
    AVG((properties->>'garment_preservation_score')::NUMERIC) AS avg_preservation_score
FROM analytics_events
WHERE event_name = 'vto_feedback_submitted'
  AND occurred_at >= :start_date AND occurred_at < :end_date;
```

### 2.7 Pipeline Image Failure Rate (KPI 1.4.8)
```sql
SELECT 
    COUNT(CASE WHEN status = 'failed' AND failure_category IN ('provider_timeout', 'quality_check_failed', 'storage_error') THEN 1 END)::FLOAT /
    NULLIF(COUNT(*), 0) * 100 AS pipeline_image_failure_rate
FROM vto_jobs
WHERE created_at >= :start_date AND created_at < :end_date;
```

### 2.8 Product CTR (KPI 1.4.9)
```sql
SELECT 
    COUNT(DISTINCT CASE WHEN event_name = 'product_clicked' THEN properties->>'product_id' END)::FLOAT /
    NULLIF(COUNT(DISTINCT CASE WHEN event_name = 'product_impression' THEN properties->>'product_id' END), 0) * 100 AS product_ctr
FROM analytics_events
WHERE occurred_at >= :start_date AND occurred_at < :end_date
  AND is_internal = FALSE;
```

### 2.9 Saved-Look Rate (KPI 1.4.10)
```sql
SELECT 
    COUNT(DISTINCT s.shopper_id)::FLOAT /
    NULLIF(COUNT(DISTINCT c.shopper_id), 0) * 100 AS saved_look_rate
FROM (
    SELECT DISTINCT shopper_id FROM analytics_events 
    WHERE event_name = 'vto_completed' AND occurred_at >= :start_date AND occurred_at < :end_date
) c
LEFT JOIN (
    SELECT DISTINCT shopper_id FROM analytics_events 
    WHERE event_name = 'look_saved' AND occurred_at >= :start_date AND occurred_at < :end_date
) s ON c.shopper_id = s.shopper_id;
```

### 2.10 Cost Per Successful VTO (KPI 1.4.14)
```sql
SELECT 
    SUM(provider_cost) AS total_provider_spend,
    COUNT(*) AS total_successful_jobs,
    SUM(provider_cost) / NULLIF(COUNT(*), 0) AS direct_cost_per_successful_vto
FROM vto_jobs
WHERE status = 'completed'
  AND created_at >= :start_date AND created_at < :end_date;
```
