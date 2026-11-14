# Database Network Security & Firewall Rules

## 1. Network Topology & Isolation Model

PostgreSQL instances are deployed strictly inside isolated private database subnets with no public IPv4 addresses, no direct Internet Gateway route, and zero ingress from the public internet.

```mermaid
flowchart TD
    subgraph VPC ["AWS Virtual Private Cloud (ap-south-1)"]
        subgraph AppSubnets ["Private Application Subnets"]
            ECS_API["ECS API Tasks (Security Group: sg-fashx-api)"]
            ECS_Worker["ECS Celery Workers (Security Group: sg-fashx-worker)"]
            ECS_Migration["ECS Migration Task (Security Group: sg-fashx-migration)"]
        end

        subgraph DatabaseSubnets ["Isolated Database Subnets (No IGW Route)"]
            RDS_Postgres["Amazon RDS PostgreSQL 16 (Security Group: sg-fashx-db)\nPort 5432"]
        end
    end

    ECS_API -->|TCP 5432 (TLS 1.3)| RDS_Postgres
    ECS_Worker -->|TCP 5432 (TLS 1.3)| RDS_Postgres
    ECS_Migration -->|TCP 5432 (TLS 1.3)| RDS_Postgres

    Internet([Internet / External Traffic]) -.->|BLOCKED / DROP| RDS_Postgres
    DevApp([Development Services]) -.->|BLOCKED / DROP| RDS_Postgres
```

---

## 2. Ingress & Egress Security Group Rules

### Database Security Group (`sg-fashx-db`)
- **Inbound Rules**:
  - `Type: PostgreSQL (TCP), Port: 5432, Source: sg-fashx-api` (Allow API runtime queries)
  - `Type: PostgreSQL (TCP), Port: 5432, Source: sg-fashx-worker` (Allow Celery worker queries)
  - `Type: PostgreSQL (TCP), Port: 5432, Source: sg-fashx-migration` (Allow Alembic migration executions)
  - **All other inbound traffic**: Implicit Deny (`0.0.0.0/0` strictly prohibited).
- **Outbound Rules**:
  - `Type: All traffic, Destination: VPC internal` (RDS replication & monitoring).

---

## 3. Mandatory TLS Invariant

1. **Parameter Group Enforcement**: `rds.force_ssl=1` rejects any client attempting unencrypted plaintext connection.
2. **Client Connection Strings**:
   - Application connections must append `?ssl=require` or `?sslmode=verify-full`.
   - Driver specification: `postgresql+asyncpg://<user>:<secret>@<host>:5432/<db>?ssl=require`.

---

## 4. Acceptance Verification Tests

1. **Allowed Connection**: ECS API task container inside the private subnet connects and executes `SELECT 1`.
2. **Denied Connection (External)**: Attempting `nc -zv <rds-endpoint> 5432` from an external internet host or non-peered VPC times out with zero response.
3. **Denied Connection (Cross-Environment)**: Tasks running in the Development cluster attempting to connect to `fashx-pg-prod` are rejected at the security group boundary.
4. **Unencrypted Refusal**: Connecting with `sslmode=disable` produces: `FATAL: no pg_hba.conf entry for host ..., SSL off`.
