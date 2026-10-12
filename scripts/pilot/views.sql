-- Pseudonymous Analyst Views for Closed Pilot Evaluation (Rule 10.6)
-- Salts user_id with app.pilot_salt so analysts query behaviors without exposing raw identities.
-- Free-text fields (feedback messages, survey comments) are deliberately excluded.

-- 1. Pilot Events View
CREATE OR REPLACE VIEW v_pilot_events AS
SELECT 
    md5(e.user_id::text || coalesce(current_setting('app.pilot_salt', true), 'fashx_pilot_default_salt_2026')) AS uid,
    p.cohort,
    e.event_type AS event,
    e.occurred_at AS created_at,
    coalesce((e.payload->>'app_version'), '1.0.0') AS app_version,
    e.payload AS props
FROM domain_events e
JOIN pilot_participants p ON e.user_id = p.user_id;

-- 2. Try-On Jobs View
CREATE OR REPLACE VIEW v_pilot_tryon_jobs AS
SELECT 
    md5(j.user_id::text || coalesce(current_setting('app.pilot_salt', true), 'fashx_pilot_default_salt_2026')) AS uid,
    p.cohort,
    j.id AS job_id,
    j.garment_id,
    j.status,
    j.failure_reason,
    j.created_at,
    j.completed_at,
    round(extract(epoch from (j.completed_at - j.created_at))::numeric, 2) AS duration_seconds
FROM tryon_jobs j
JOIN pilot_participants p ON j.user_id = p.user_id;

-- 3. Try-On Feedback View
CREATE OR REPLACE VIEW v_pilot_tryon_feedback AS
SELECT 
    md5(f.user_id::text || coalesce(current_setting('app.pilot_salt', true), 'fashx_pilot_default_salt_2026')) AS uid,
    p.cohort,
    f.tryon_job_id,
    f.visual_accuracy,
    f.purchase_confidence,
    f.created_at
FROM tryon_feedback f
JOIN pilot_participants p ON f.user_id = p.user_id;

-- 4. Feed Impressions View
CREATE OR REPLACE VIEW v_pilot_feed_impressions AS
SELECT 
    md5(i.user_id::text || coalesce(current_setting('app.pilot_salt', true), 'fashx_pilot_default_salt_2026')) AS uid,
    p.cohort,
    i.garment_id,
    i.position,
    i.ranker_version,
    i.created_at
FROM feed_impressions i
JOIN pilot_participants p ON i.user_id = p.user_id;

-- 5. Feed Signals View
CREATE OR REPLACE VIEW v_pilot_feed_signals AS
SELECT 
    md5(s.user_id::text || coalesce(current_setting('app.pilot_salt', true), 'fashx_pilot_default_salt_2026')) AS uid,
    p.cohort,
    s.garment_id,
    s.action,
    s.created_at
FROM feed_signals s
JOIN pilot_participants p ON s.user_id = p.user_id;

-- 6. Buy Clicks View
CREATE OR REPLACE VIEW v_pilot_buy_clicks AS
SELECT 
    md5(b.user_id::text || coalesce(current_setting('app.pilot_salt', true), 'fashx_pilot_default_salt_2026')) AS uid,
    p.cohort,
    b.garment_id,
    b.affiliate_network,
    b.clicked_at
FROM buy_clicks b
JOIN pilot_participants p ON b.user_id = p.user_id;
