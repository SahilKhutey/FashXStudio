# Scheduled Synchronization

## 1. Purpose and Architecture
Scheduled synchronization ensures that FashXStudio's catalog offers reflect live merchant inventory, current pricing, and seasonal availability without requiring manual intervention.

---

## 2. Schedule Data Model
Schedules are stored in the `catalog_source_schedules` table with the following schema:
- `id`: UUID primary key.
- `source_id`: Unique foreign key to `catalog_sources.id`.
- `merchant_id`: Foreign key to `merchants.id`.
- `enabled`: Boolean flag indicating whether the schedule is active.
- `sync_mode`: Default sync mode (`INCREMENTAL` or `FULL`).
- `interval_minutes`: Recurrence interval (enforced minimum: 15 minutes; maximum: 10,080 minutes / 7 days).
- `cron_expression`: Optional standard 5-part cron syntax for specific wall-clock execution.
- `timezone`: IANA timezone name (e.g. `UTC`, `Asia/Kolkata`, `America/New_York`).
- `last_scheduled_at`: Timestamp when the job was last dispatched to workers.
- `next_run_at`: Timestamp index indicating when the source is next due for execution.

---

## 3. Cadence & Rate-Limit Safeguards
1. **Minimum Interval Guardrail**:
   - Automated synchronization intervals below 15 minutes are strictly disallowed to prevent source feed overload and denial-of-service risks against merchant servers.
   - Any API request specifying `interval_minutes < 15` is rejected with `invalid_interval`.
2. **Timezone Accuracy**:
   - Timezones must be valid IANA string identifiers.
   - Offsets and day-boundary calculations are handled using Python's `zoneinfo.ZoneInfo`.
3. **Scheduler Due Queue (`get_due_schedules`)**:
   - The scheduler queries due schedules matching:
     `enabled == True AND next_run_at <= current_time AND catalog_sources.is_enabled == True`.
   - When dispatched, `last_scheduled_at` is set to `current_time` and `next_run_at` is advanced immediately in the same transaction by `interval_minutes` to prevent duplicate dispatching across worker threads.
