# Database Restore Drill Protocol and Report

## 1. Test Metadata Template

Every scheduled restore drill requires completing this verification report:

```markdown
# Database Restore Drill Report

## Test Metadata
- Environment Under Test: Staging / Production Snapshot
- Rehearsal Date (UTC): [YYYY-MM-DD HH:MM:SS]
- Lead Operator: [Human Founder / Lead Engineer]
- Recovery Point Timestamp: [Target PITR Timestamp]
- Source DB Instance: [fashx-pg-prod]
- Destination Restore Target: [fashx-rehearsal-temp-db]
- Database Engine: PostgreSQL 16.3 (AWS RDS)

## Recovery Measurements
- Drill Initiated: [HH:MM:SS]
- Instance Available: [HH:MM:SS]
- Total Restore Duration: [MM minutes, SS seconds]
- Target Recovery Point Objective (RPO): < 5 minutes
- Measured RPO: [0 seconds (PITR target reached)]
- Target Recovery Time Objective (RTO): < 30 minutes
- Measured RTO: [Actual Duration]

## Schema & Data Integrity Checklist
- [ ] Database accepts TLS connections on port 5432
- [ ] Schema `public` present with identical table count
- [ ] Migration revision in `alembic_version` matches production commit
- [ ] Extension `vector` present and functional
- [ ] Table row counts match source snapshot:
  - `users` count parity verified
  - `user_style_profiles` count parity verified
  - `catalog_garments` count parity verified
  - `tryon_jobs` count parity verified
- [ ] Foreign key constraints validated
- [ ] Non-destructive sample read query executed
- [ ] Sample insert and rollback executed
- [ ] No production write traffic routed to rehearsal target
- [ ] Temporary instance terminated and deleted upon completion

## Final Outcome & Sign-Off
- Status: [PASS / FAIL]
- Variance / Findings: [Notes on latency, disk growth, or configuration anomalies]
- Signed Off By: [Name & Role]
```

---

## 2. Automated Logical Restore Command (Sandbox Target)

To test a custom-format dump produced by `scripts/db/backup_postgres.sh`:

```bash
# 1. Initialize disposable local or sandbox database
createdb fashx_restore_test

# 2. Execute pg_restore
pg_restore \
  --dbname="$RESTORE_DATABASE_URL" \
  --no-owner \
  --no-acl \
  --exit-on-error \
  ./backups/fashx-<TIMESTAMP>.dump

# 3. Verify public table count and extensions
psql "$RESTORE_DATABASE_URL" -c "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public';"
psql "$RESTORE_DATABASE_URL" -c "SELECT extname, extversion FROM pg_extension;"
psql "$RESTORE_DATABASE_URL" -c "SELECT version_num FROM alembic_version;"
```
