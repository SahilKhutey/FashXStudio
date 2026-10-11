# Third-Party Data Processor Register (DPDP Section 8)

**Data Fiduciary**: FashXStudio  
**Jurisdiction**: Republic of India  
**Applicable Rules**: DPDP Rules 2025 (Rule 7: Data Processor Agreements)  

---

## 1. Registered Data Processors

| Processor Name | Legal Entity & Jurisdiction | Role / Service Provided | Personal Data Shared | Security Guarantees & Safeguards | DPA Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Amazon Web Services (AWS)** | Amazon Web Services India Pvt. Ltd. (India) | Cloud infrastructure, RDS PostgreSQL, ECS Fargate, S3 Media Storage (`ap-south-1` Mumbai) | User account data, encrypted photos, presigned URLs, logs | ISO 27001, SOC 1/2/3, encryption at rest (`AES-256`), AWS DPA executed with India region restriction. | **EXECUTED** (Standard AWS DPA with India addendum) |
| **Supabase** | Supabase, Inc. (USA / AWS ap-south-1) | Authentication identity provider, email OTP delivery | User email address, hashed auth tokens | SOC 2 Type II, encrypted credentials, JWT signing via private keys. | **EXECUTED** (Standard Data Processing Addendum) |
| **FASHN AI** | Fashn AI Inc. (USA) | Hosted Virtual Try-On API (Inference Processor) | Transient photo URL & garment image URL during active job execution | Ephemeral processing only. DPA terms stipulate zero retention for model training; images deleted from cache within 24 hours. | **EXECUTED** (API Terms of Service & Enterprise DPA) |
| **Sentry** | Functional Software, Inc. (USA) | Application performance and crash monitoring | Stack traces, error codes (PII redacted via client SDK & `RedactFilter`) | SOC 2 Type II, pre-redaction filter strips emails, tokens, and query strings before dispatch. | **EXECUTED** (Standard DPA with PII scrubbing) |
| **Affiliate Networks** | Cuelinks / EarnKaro / vCommission (India) | Affiliate link attribution and clickout tracking | Pseudonymous click ID and timestamp only (zero user email, zero photos, zero user names) | Standard publisher affiliate agreement. Strictly pseudonymous transaction logs. | **EXECUTED** (Network Terms of Service) |

---

## 2. Processor Compliance Requirements

Under DPDP Act Section 8(2), FashXStudio as Data Fiduciary maintains continuous oversight:
1. **Contractual Safeguards**: All processors are bound by contract to process data only upon valid instructions from FashXStudio and never for independent model training or secondary commercial exploitation.
2. **Breach Notification Flow**: Processors are contractually mandated to report any security incident or personal data breach to FashXStudio within **2 hours** of detection, allowing FashXStudio to meet the statutory **6-hour CERT-In** and **72-hour DPB** clocks.
3. **Sub-processor Approval**: Processors must obtain prior written consent from FashXStudio before onboarding subsequent sub-processors handling user biometrics.
