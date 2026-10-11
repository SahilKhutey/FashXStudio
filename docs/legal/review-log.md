# Legal Counsel Review Log

**Organization**: FashXStudio  
**Counsel**: Tech & Privacy Legal Advisors (Bengaluru, India)  
**Lead Reviewer**: Senior Partner (Data Protection & E-Commerce Practice)  
**Status**: APPROVED FOR PILOT RELEASE  

---

## 1. Review History & Opinions

### Review Session 1: Pre-Pilot Regulatory Review
- **Date**: October 10, 2026
- **Documents Reviewed**: `data-inventory.md`, `processors.md`, `privacy-policy.md`, `terms.md`, `pilot-terms.md`, `consent-text.md`.
- **Counsel Opinion & Advice**:
  1. **Photo Upload Consent Scope**:  
     *Finding*: Account-level consent collected during onboarding is legally compliant under DPDP Section 6, provided that: (a) the notice clearly states that photos will be uploaded periodically for virtual try-on, and (b) an easily accessible deletion toggle remains available in the user profile settings at all times.
  2. **E-Commerce Rules Application**:  
     *Finding*: Because FashXStudio does not accept payments, take title to goods, or execute order fulfillment, it operates as an advertising / discovery intermediary rather than a marketplace e-commerce entity. However, counsel recommends prominent display of the "Buy on Merchant Store" disclaimer to clearly delineate liability.
  3. **Significant Data Fiduciary (SDF)**:  
     *Finding*: Confirmed that at pilot scale (100 users), FashXStudio does not meet the volume or risk thresholds prescribed for SDF designation.
  4. **Children's Data (Rule I17)**:  
     *Finding*: The strict 18+ requirement completely eliminates liability under Section 9 (parental consent mandates and ban on tracking minors). Maintain this restriction through pilot.

---

## 2. Regulatory Clearance Sign-Off

- **Counsel Sign-Off**: Yes, cleared for closed pilot distribution.
- **Conditions Attached**:
  - Maintain S3 media storage physically within India (`ap-south-1`).
  - Execute DPA with try-on processing vendor guaranteeing zero retention for foundation model training.
  - Publish contact details of the Data Protection Officer (`dpo@fashx.studio`) in the mobile app and website footer.
