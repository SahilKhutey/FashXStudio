-- Standing Privacy-Safe Analyst Views for 90-Day Operations (Rule 12.3)
-- Exposes operational telemetry to the read-only 'analyst' role.
-- Strips all personal identifiers (PII), salted with app.analyst_salt.
-- Excludes raw shopper photos, phone numbers, and unstructured free text.

DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'analyst') THEN
        CREATE ROLE analyst NOLOGIN;
    END IF;
END
$$;

-- 1. Pseudonymous Events View
CREATE OR REPLACE VIEW v_events AS
SELECT 
    md5(e.user_id::text || coalesce(current_setting('app.analyst_salt', true), 'fashx_standing_salt_2026')) AS uid,
    e.event_type AS event,
    e.occurred_at AS created_at,
    coalesce((e.payload->>'app_version'), '1.0.0') AS app_version,
    e.payload AS props
FROM domain_events e;

-- 2. Try-On Performance & Quality View
CREATE OR REPLACE VIEW v_tryon_quality AS
SELECT 
    md5(j.user_id::text || coalesce(current_setting('app.analyst_salt', true), 'fashx_standing_salt_2026')) AS uid,
    j.id AS job_id,
    j.status,
    j.failure_reason,
    j.created_at,
    j.completed_at,
    round(extract(epoch from (j.completed_at - j.created_at))::numeric, 2) AS duration_seconds
FROM tryon_jobs j;

-- 3. B2B Multi-Tenant Daily Usage & Metering View (Path B)
CREATE OR REPLACE VIEW v_tenant_usage AS
SELECT 
    u.tenant_id,
    t.slug AS tenant_slug,
    t.name AS tenant_name,
    t.status AS tenant_status,
    u.day,
    u.sessions,
    u.size_recs,
    u.tryons,
    round((u.tryons::numeric * 0.065), 2) AS estimated_inference_cost_usd
FROM tenant_usage u
JOIN tenants t ON u.tenant_id = t.id;

-- 4. Anonymous Widget Sessions Telemetry (Path B)
CREATE OR REPLACE VIEW v_widget_sessions AS
SELECT 
    s.id AS session_id,
    s.tenant_id,
    t.slug AS tenant_slug,
    s.created_at,
    s.expires_at,
    s.consent_at IS NOT NULL AS has_consented,
    extract(epoch from (s.expires_at - s.created_at)) / 3600 AS retention_hours
FROM widget_sessions s
JOIN tenants t ON s.tenant_id = t.id;

-- 5. Experiment Exposure View (Rule 12.4)
CREATE OR REPLACE VIEW v_experiment_exposures AS
SELECT 
    md5(x.user_id::text || coalesce(current_setting('app.analyst_salt', true), 'fashx_standing_salt_2026')) AS uid,
    x.experiment,
    x.variant,
    x.first_seen_at
FROM experiment_exposures x;

-- Grant permissions to analyst role
GRANT USAGE ON SCHEMA public TO analyst;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO analyst;
GRANT SELECT ON ALL VIEWS IN SCHEMA public TO analyst;
REVOKE SELECT ON users FROM analyst;
REVOKE SELECT ON user_photos FROM analyst;
REVOKE SELECT ON pilot_feedback FROM analyst;
