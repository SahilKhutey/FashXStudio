# Operational Template: Source Registration Form

Use this form to define the technical parameters, credentials, and constraints for each ingestion channel of an approved merchant.

---

### Section 1: Source Identification
- **Merchant ID**: 
- **Merchant Legal Name**: 
- **Source Slug** (lowercase, kebab-case, e.g. `zara-in-api`): 
- **Source Display Name**: 
- **Source Description**: 
- **Source Owner / Internal Lead**: 

### Section 2: Technical Channel & Ingestion Spec
- **Source Type**: 
  - [ ] `MERCHANT_API`
  - [ ] `AFFILIATE_API`
  - [ ] `MERCHANT_FEED`
  - [ ] `PARTNER_EXPORT`
  - [ ] `SHOPIFY_APP`
  - [ ] `OTHER_AUTHORIZED`
- **Access Method**:
  - [ ] `OAUTH2`
  - [ ] `API_KEY`
  - [ ] `SIGNED_REQUEST`
  - [ ] `HTTPS_FEED`
  - [ ] `SFTP`
  - [ ] `MANUAL_PARTNER_EXPORT`
- **Secrets Manager ARN / Path (`credential_secret_ref`)**: 
- **Rate Limit (`max_rps`)**: 
- **Refresh Frequency (`refresh_hours`)**: 

### Section 3: Geographic & Merchandise Scope
- **Authorized Market Codes** (e.g. `["IN"]`): 
- **Authorized Merchandise Categories** (e.g. `["apparel", "footwear"]`): 
- **Agreement Version / Reference**: 
- **Effective Timestamp**: 
- **Expiration Timestamp**: 
- **Scheduled Next Review Date**: 

### Section 4: Operational Clearance Checklist
- [ ] Merchant verification status confirmed == `VERIFIED`
- [ ] Credential handshake validated in sandbox
- [ ] Contractual authorization evidence uploaded and verified
- [ ] Granular permission matrix recorded
