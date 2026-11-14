# FashXStudio — Analytics & Event Relational Data Models

**Document ID:** `FASHX-DB-001`  
**Version:** `1.0 — Technical Baseline`  
**Date:** `10 November 2026`  
**Scope:** `Phase 01.5 — PostgreSQL 16 Relational Schema Architecture`  

---

## 1. Storage Architecture Overview

FashXStudio separates real-time transactional domain entities from analytical event storage through a hybrid relational and rollup model in PostgreSQL 16:
1. **`domain_events` / `analytics_events`:** Append-only event store partitioned monthly by `occurred_at`.
2. **`vto_jobs` & `vto_attempts`:** Authoritative execution lifecycle tables tracking GPU inference and latency decomposition.
3. **`merchant_metrics_daily`:** Pre-aggregated daily rollup table optimized for sub-50ms dashboard query latency.
4. **`shopper_cohorts`:** Cohort tracking table calculating D1, D7, and D30 retention.

---

## 2. PostgreSQL DDL Specifications

### 2.1 Partitioned Analytics Event Table (`analytics_events`)

```sql
CREATE TABLE analytics_events (
    id UUID NOT NULL,
    event_name VARCHAR(64) NOT NULL,
    event_version SMALLINT NOT NULL DEFAULT 1,
    occurred_at TIMESTAMPTZ NOT NULL,
    
    -- Identity & Tenancy
    session_id UUID NOT NULL,
    shopper_id UUID,
    merchant_id UUID,
    product_id UUID,
    variant_id UUID,
    
    -- Correlation & Governance
    journey_id VARCHAR(64) NOT NULL,
    trace_id UUID NOT NULL,
    is_internal BOOLEAN NOT NULL DEFAULT FALSE,
    
    -- Dynamic Typed Payload
    properties JSONB NOT NULL DEFAULT '{}'::jsonb,
    
    PRIMARY KEY (id, occurred_at)
) PARTITION BY RANGE (occurred_at);

-- Monthly Partition Tables (Example for Q4 2026)
CREATE TABLE analytics_events_2026_11 PARTITION OF analytics_events
    FOR VALUES FROM ('2026-11-01 00:00:00+00') TO ('2026-12-01 00:00:00+00');

CREATE TABLE analytics_events_2026_12 PARTITION OF analytics_events
    FOR VALUES FROM ('2026-12-01 00:00:00+00') TO ('2027-01-01 00:00:00+00');

-- High Performance Composite Indexes
CREATE INDEX ix_analytics_events_name_time 
    ON analytics_events (event_name, occurred_at DESC);

CREATE INDEX ix_analytics_events_merchant_time 
    ON analytics_events (merchant_id, occurred_at DESC) WHERE merchant_id IS NOT NULL;

CREATE INDEX ix_analytics_events_shopper_time 
    ON analytics_events (shopper_id, occurred_at DESC) WHERE shopper_id IS NOT NULL;
```

---

### 2.2 Pre-Aggregated Daily Rollup Table (`merchant_metrics_daily`)

```sql
CREATE TABLE merchant_metrics_daily (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    merchant_id UUID NOT NULL REFERENCES merchants(id) ON DELETE CASCADE,
    metric_date DATE NOT NULL,
    
    -- Product & Discovery Metrics
    total_impressions INT NOT NULL DEFAULT 0,
    unique_viewed_skus INT NOT NULL DEFAULT 0,
    total_detail_views INT NOT NULL DEFAULT 0,
    
    -- VTO Metrics
    vto_initiations INT NOT NULL DEFAULT 0,
    vto_completed INT NOT NULL DEFAULT 0,
    vto_failed INT NOT NULL DEFAULT 0,
    vto_p95_latency_ms INT,
    
    -- Engagement & Conversion
    looks_saved INT NOT NULL DEFAULT 0,
    merchant_handoff_clicks INT NOT NULL DEFAULT 0,
    
    -- Financials
    total_provider_cost_inr NUMERIC(10, 2) NOT NULL DEFAULT 0.00,
    
    -- Metadata
    computed_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    
    CONSTRAINT uq_merchant_metric_daily UNIQUE (merchant_id, metric_date)
);

CREATE INDEX ix_merchant_metrics_daily_lookup 
    ON merchant_metrics_daily (merchant_id, metric_date DESC);
```

---

### 2.3 Shopper Retention Cohorts Table (`shopper_cohorts`)

```sql
CREATE TABLE shopper_cohorts (
    shopper_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    cohort_date DATE NOT NULL,
    first_session_at TIMESTAMPTZ NOT NULL,
    
    -- Retention Milestone Flags
    active_d1 BOOLEAN NOT NULL DEFAULT FALSE,
    active_d7 BOOLEAN NOT NULL DEFAULT FALSE,
    active_d14 BOOLEAN NOT NULL DEFAULT FALSE,
    active_d30 BOOLEAN NOT NULL DEFAULT FALSE,
    
    last_active_at TIMESTAMPTZ NOT NULL,
    total_active_days INT NOT NULL DEFAULT 1
);

CREATE INDEX ix_shopper_cohorts_date ON shopper_cohorts (cohort_date);
```
