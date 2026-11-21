# Operational Template: Takedown Request Form

Use this form to document and track incoming copyright notices, merchant removal requests, licensing disputes, and security incidents.

---

### Incident Information
- **Takedown Incident Reference**: `TD-YYYYMMDD-XXXX`
- **Date & Time Received (UTC)**: 
- **Requesting Entity**: 
- **Authorized Contact Name**: 
- **Contact Email & Phone**: 
- **Target Source ID**: 
- **Target Source Slug**: 
- **Specific Product SKUs (or "ENTIRE_SOURCE")**: 

### Reason & Categorization
- [ ] `IMAGE_RIGHTS_DISPUTE` — Copyright infringement claim regarding photos/imagery
- [ ] `MERCHANT_REQUEST` — Direct request by merchant to halt syndication
- [ ] `LICENSE_EXPIRED` — Licensing agreement concluded without renewal
- [ ] `LICENSE_REVOKED` — Formal contract termination or breach notice
- [ ] `DATA_RIGHTS_DISPUTE` — Pricing error, trademark, or description dispute
- [ ] `PROVIDER_TERMINATION` — Technical provider / network relationship dissolved
- [ ] `CREDENTIAL_COMPROMISE` — Stolen API keys or compromised token
- [ ] `SECURITY_INCIDENT` — Malicious payload, SSRF, or data corruption
- [ ] `INCORRECT_PRODUCT_DATA` — Erroneous or misleading product attributes
- [ ] `LEGAL_REQUEST` — Subpoena, court injunction, or regulatory mandate

### Immediate Execution Log
- **Takedown API Call**: `POST /api/v1/admin/catalog/sources/{id}/takedown`
- **Execution Timestamp**: 
- **Source Suspension Confirmed**: [ ] YES (`source_status = SUSPENDED`, `rights_display = False`)
- **Downstream Unpublishing**: 
  - Worker Task ID: 
  - Products Suspended: 
  - CDN Cache Flushed: [ ] YES
  - Celery AI Queue Purged: [ ] YES

### Investigation & Resolution Log
- **Assigned Reviewer**: 
- **Investigation Findings**: 
- **Remediation Action Taken**: 
- **Resolution Timestamp**: 
- **Resolution API Call**: `POST /api/v1/admin/catalog/takedowns/{id}/resolve`
- **Resolution Notes**: 
