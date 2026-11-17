# Redis Network Security & Encryption Specification

> **Security specification. Pre-pilot status maintained per AGENTS.md.**

---

## 1. Network Perimeter & Security Groups

AWS ElastiCache Redis instances must never be exposed to the public Internet or unauthorized VPC subnets.

### Ingress & Egress Rules (`fashx-redis-sg`):

| Direction | Protocol | Port Range | Source / Destination | Purpose |
| :--- | :--- | :--- | :--- | :--- |
| **Ingress** | TCP | 6379 | `fashx-app-sg` | Allow FastAPI and Celery worker traffic |
| **Ingress** | ALL | ALL | 0.0.0.0/0 | **DENIED** (No direct internet traffic) |
| **Egress** | ALL | ALL | 0.0.0.0/0 | Allowed for AWS internal telemetry and NTP |

---

## 2. In-Transit Encryption (TLS)

1. **Enforcement**: In-transit encryption is enabled at the ElastiCache cluster level (`transit_encryption_enabled = true`).
2. **Protocol Scheme**:
   - Staging & Production clients must connect using the TLS scheme `rediss://`.
   - Any attempt by production services to use plaintext `redis://` is rejected at startup by `validate_release_config()`.
3. **Certificate Validation**:
   - AWS ElastiCache issues TLS certificates signed by the Amazon Trust Services CA.
   - Client Python applications validate certificates using system trust stores (`redis_ssl_cert_reqs = "required"`).

---

## 3. At-Rest Encryption

1. **Storage Encryption**: All data persisted to disk (engine snapshots, swap, and replication buffers) is encrypted at rest.
2. **Key Management**:
   - Staging: Uses the default AWS-managed KMS key for ElastiCache (`aws/elasticache`).
   - Production: Uses a customer-managed AWS KMS key (`arn:aws:kms:ap-south-1:...`) with automated annual rotation.
