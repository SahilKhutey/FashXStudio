# Merchant Identity Verification Standard

**Workstream**: 5.1.2 — Merchant Legal Identity & Verification  
**Status**: Active  
**Enforcement Engine**: `backend/fashx/catalog/merchants/`

---

## 1. Principle
FashXStudio does not permit anonymous, unverified, or pseudo-registered merchants to ingest data or expose products to shoppers. Every merchant must correspond to an identifiable legal entity verified against official corporate registries.

---

## 2. Verification Data Requirements

Each `Merchant` record in the database maintains the following mandatory attributes:

| Field | Type | Description | Verification Standard |
|---|---|---|---|
| `name` | String(255) | Public brand / trading name | Commercial registry or trademark match |
| `legal_name` | String(255) | Full incorporated entity name | Exact match on RoC / Companies House / State filing |
| `country_code` | String(8) | ISO 3166-1 alpha-2 registration jurisdiction | Valid sovereign jurisdiction code |
| `registration_reference` | String(128) | Corporate registration identifier | Official CIN, LLPIN, EIN, or VAT registration number |
| `primary_contact_id` | UUID | User / contact reference for business lead | Corporate domain email verified |
| `technical_contact_id` | UUID | User / contact reference for technical integration | Corporate domain email verified |
| `takedown_contact_id` | UUID | Contact reference for IP takedowns and notices | 24/7 SLA responsiveness confirmed |
| `verification_status` | String(32) | Current verification state | Machine-enforced enum state |

---

## 3. Verification State Machine

```
   [ UNVERIFIED ]  (Initial state upon submission)
          |
          +---> [ UNDER_REVIEW ]  (Assigned to compliance officer)
          |           |
          |           +---> [ VERIFIED ]  (Corporate registration & MSA confirmed)
          |           |          |
          |           |          +---> [ SUSPENDED ]  (Breach, expired license, regulatory order)
          |           |                     |
          |           |                     +---> [ UNDER_REVIEW ] (Cure / re-verification)
          |           |
          |           +---> [ REJECTED ]  (Fraud, invalid docs, sanction match)
          |                      |
          +----------------------+---> [ UNDER_REVIEW ] (New documentation submitted)
```

### Verification States & Semantic Rules:
1. **UNVERIFIED**: Initial state. Ingestion blocked. Sources cannot be activated.
2. **UNDER_REVIEW**: Compliance officer reviewing submitted corporate certificates and authorizations.
3. **VERIFIED**: Validated by compliance officer with review timestamp and reviewer ID. Sources eligible for activation if valid evidence and permissions exist.
4. **SUSPENDED**: Temporarily revoked due to legal notice, security breach, or expired credentials. Cascades immediate suspension to all child sources (`source_status = SUSPENDED`).
5. **REJECTED**: Application denied due to documentation deficiency or compliance failure.

---

## 4. Verification Checkpoints for Compliance Officers

Before marking a merchant `VERIFIED`:
1. Check corporate registry status: Verify that entity is in good standing and not struck off or dissolved.
2. Check trademark rights: Verify that applicant has authorized rights to represent the brands being ingested.
3. Check sanctions / watchlists: Ensure entity and key executives are not subject to applicable trade sanctions.
4. Document attachment: Ensure executed MSA/License agreement is uploaded and verified in `catalog_authorization_evidence`.
