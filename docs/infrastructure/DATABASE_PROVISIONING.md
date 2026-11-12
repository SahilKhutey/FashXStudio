# PostgreSQL Database Provisioning Guide

## 1. AWS RDS Parameter Group Setup

Prior to instance creation, create a custom parameter group enforcing SSL connections and query logging:

```bash
# Create custom parameter group for PostgreSQL 16
aws rds create-db-parameter-group \
  --db-parameter-group-name fashx-postgres16-params \
  --db-parameter-group-family postgres16 \
  --description "FashXStudio PostgreSQL 16 security and performance parameters" \
  --region ap-south-1

# Enforce TLS encryption for all connections
aws rds modify-db-parameter-group \
  --db-parameter-group-name fashx-postgres16-params \
  --parameters \
    "ParameterName=rds.force_ssl,ParameterValue=1,ApplyMethod=immediate" \
    "ParameterName=shared_preload_libraries,ParameterValue=pg_stat_statements,ApplyMethod=pending-reboot" \
    "ParameterName=log_connections,ParameterValue=1,ApplyMethod=immediate" \
    "ParameterName=log_disconnections,ParameterValue=1,ApplyMethod=immediate" \
    "ParameterName=log_min_duration_statement,ParameterValue=500,ApplyMethod=immediate" \
  --region ap-south-1
```

---

## 2. Production Database Provisioning

```bash
aws rds create-db-instance \
  --db-instance-identifier fashx-pg-prod \
  --db-instance-class db.r6g.large \
  --engine postgres \
  --engine-version 16.3 \
  --master-username fashx_admin \
  --manage-master-user-password \
  --master-user-secret-kms-key-id "arn:aws:kms:ap-south-1:<ACCOUNT_ID>:key/fashx-rds-key" \
  --allocated-storage 100 \
  --max-allocated-storage 1000 \
  --storage-type gp3 \
  --storage-encrypted \
  --kms-key-id "arn:aws:kms:ap-south-1:<ACCOUNT_ID>:key/fashx-rds-key" \
  --multi-az \
  --db-subnet-group-name fashx-private-db-subnet-group \
  --vpc-security-group-ids "sg-fashx-prod-db" \
  --db-parameter-group-name fashx-postgres16-params \
  --backup-retention-period 35 \
  --preferred-backup-window "01:30-02:30" \
  --preferred-maintenance-window "Sun:03:00-Sun:04:00" \
  --auto-minor-version-upgrade \
  --copy-tags-to-snapshot \
  --deletion-protection \
  --tags Key=Environment,Value=production Key=Project,Value=FashXStudio \
  --region ap-south-1
```

---

## 3. Non-Production (Development & Staging) Database Provisioning

```bash
aws rds create-db-instance \
  --db-instance-identifier fashx-pg-nonprod \
  --db-instance-class db.t4g.small \
  --engine postgres \
  --engine-version 16.3 \
  --master-username fashx_admin \
  --manage-master-user-password \
  --allocated-storage 20 \
  --max-allocated-storage 100 \
  --storage-type gp3 \
  --storage-encrypted \
  --no-multi-az \
  --db-subnet-group-name fashx-nonprod-db-subnet-group \
  --vpc-security-group-ids "sg-fashx-nonprod-db" \
  --db-parameter-group-name fashx-postgres16-params \
  --backup-retention-period 7 \
  --tags Key=Environment,Value=non-production Key=Project,Value=FashXStudio \
  --region ap-south-1
```

---

## 4. Initial Database Bootstrap Script

Once instances enter the `available` state, connect via bastion host using the admin role to initialize databases and extensions:

```sql
-- Connect to fashx-pg-nonprod
CREATE DATABASE fashx_dev;
CREATE DATABASE fashx_staging;

-- Connect to fashx-pg-prod
CREATE DATABASE fashx_prod;

-- Enable extensions on each database
\c fashx_dev
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

\c fashx_staging
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

\c fashx_prod
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;
```
