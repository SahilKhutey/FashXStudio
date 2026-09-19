# Dependency Register: Privacy, Consent & Biometric Data Governance

| Attribute | Specification |
| :--- | :--- |
| **Regulatory Frameworks** | Digital Personal Data Protection Act (DPDPA 2023), GDPR, CCPA |
| **Sensitive Assets** | User full-body photos, facial geometry, body measurements |
| **Data Controller** | FashXStudio Identity Subsystem |
| **Owner** | Security & Privacy Lead |

---

## 1. The Core Legal & Architectural Distinction

> [!IMPORTANT]
> **Processing Consent != Model Training Consent**
> - **`body_photo_processing`**: Permits ephemeral memory loading on GPU workers solely to generate the requested try-on render.
> - **`ml_model_training`**: STRICTLY OPT-IN (`default=False`). Requires explicit, unbundled user consent before any portrait may be anonymized for internal diffusion fine-tuning.

---

## 2. Hard Data Purge Lifecycle

1. **User Account Deletion / Consent Revocation**:
   - Triggers an immediate transactional cascade in PostgreSQL (`ON DELETE CASCADE`).
   - Dispatches a background purge task deleting all associated portrait objects from R2/S3.
   - Any active Try-On jobs referencing the user photo are immediately aborted and marked `cancelled`.
2. **Short-Lived Capability Token Expiry**:
   - Capability access tokens expire after 15 minutes (900s). Once expired, signed object storage links reject all further read requests.
