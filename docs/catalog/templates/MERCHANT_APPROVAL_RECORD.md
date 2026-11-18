# Operational Template: Merchant Approval Record

Use this form to document formal administrative and legal clearance before transitioning a merchant or catalog source into `VERIFIED` or `ACTIVE` status.

---

### Record Identification
- **Record Reference ID**: `REC-APPR-YYYYMMDD-XXXX`
- **Merchant ID**: 
- **Merchant Legal Name**: 
- **Source ID**: 
- **Source Slug**: 

### Attestation of Legal Due Diligence
- [ ] Corporate registration active and validated against sovereign registrar (MCA/RoC/etc.)
- [ ] Corporate signatory authority confirmed via board resolution or authorized signatory letter
- [ ] Executed Master Services Agreement (MSA) countersigned by both parties
- [ ] Cryptographic SHA-256 hash verified and stored in `catalog_authorization_evidence`
- [ ] No active trade sanctions, trademark infringement disputes, or unresolved DMCA notices

### Technical & Security Attestation
- [ ] Credentials securely vaulted in AWS Secrets Manager (no plaintext tokens)
- [ ] Rate limits and backoff circuit breaker parameters calibrated
- [ ] Ingestion endpoint validated against SSRF protection policies
- [ ] Test batch parsed and verified in staging

### Approval Sign-Off
- **Approving Legal Officer**:
  - Name:
  - Role:
  - Date:
- **Approving Engineering Lead**:
  - Name:
  - Role:
  - Date:
- **Final Action Recorded**:
  - API Executed: `POST /api/v1/admin/catalog/merchants/{id}/verify`
  - Target Status: `VERIFIED`
  - Audit Reason: 
