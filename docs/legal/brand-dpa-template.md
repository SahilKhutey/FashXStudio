# Standard Data Processing Agreement (DPA) Template

**Between:**  
1. **[Brand Legal Name]** ("Data Fiduciary" or "Brand")  
2. **FashXStudio Private Limited** ("Data Processor" or "FashXStudio")

**Effective Date:** ___________________  
**Governing Law:** Digital Personal Data Protection Act, 2023 (DPDP Act) & DPDP Rules, 2025 (India)

---

## 1. Context & Purpose of Processing

1.1. The Data Fiduciary operates an online retail apparel storefront and wishes to deploy FashXStudio's artificial intelligence fit simulation and size recommendation software to assist consumers ("Data Principals") in determining garment sizing.  
1.2. The parties agree that the Brand is the **Data Fiduciary** and FashXStudio acts strictly as a **Data Processor** under Section 8(1) of the DPDP Act.

---

## 2. Scope & Categories of Data

2.1. **Personal Data Processed:**
- Body photographs uploaded voluntarily by Data Principals on the Brand storefront.
- Stated garment size preferences and product interaction tokens.
- Ephemeral IP hashes for rate limiting and fraud prevention.

2.2. **Permitted Purpose:** Processing is strictly limited to generating an instantaneous virtual fit rendering and size recommendation for the specific transaction session initiated by the Data Principal.

---

## 3. Strict Ephemeral Processing & Zero-Training Guarantee

3.1. **24-Hour Ephemeral Retention:** FashXStudio warrants that all uploaded photographs and generated fit visualization artifacts are purged permanently from all operational storage systems within **twenty-four (24) hours** of generation.  
3.2. **Zero Model Training:** FashXStudio irrevocably covenants that photographs, body representations, and biometric features uploaded through the Brand's widget shall **never** be used to train, retrain, fine-tune, or benchmark any machine learning or generative AI model.  
3.3. **No Secondary Use or Sale:** FashXStudio shall not monetize, sell, or disclose personal data to any third party for advertising, behavioral targeting, or unauthorized commercial purposes.

---

## 4. Technical & Organizational Safeguards (Rule 8)

FashXStudio shall implement and maintain the following technical safeguards:
- **Encryption:** AES-256 encryption at rest for all temporary image buffers; TLS 1.3 enforced for all network transit.
- **Tenant Isolation:** Multi-tenant database partitioning ensuring strict cryptographic and application-level isolation of Brand session data.
- **Access Control:** Role-based access controls with multi-factor authentication; zero engineer access to production ephemeral image storage without audit-logged emergency break-glass approval.
- **Log Retention:** In accordance with Rule 8(3), activity and access audit logs (excluding raw photographs) shall be retained in tamper-evident storage for a minimum of one (1) year.

---

## 5. Security Incident & Breach Notification (Rule 9)

5.1. In the event of a confirmed personal data breach affecting Brand data, FashXStudio shall notify the Brand's designated security contact without undue delay and in any event within **twelve (12) hours** of confirmation.  
5.2. Such notification shall include:
- Nature and scope of the breach.
- Categories of affected Data Principals and estimated record count.
- Remediation actions taken and recommended mitigation steps for the Fiduciary.  
5.3. FashXStudio shall provide all reasonable assistance to enable the Brand to satisfy its statutory notification obligations to the **Data Protection Board of India (DPBI)** and affected Data Principals within seventy-two (72) hours.

---

## 6. Authorized Subprocessors

The Brand hereby grants authorization for FashXStudio to engage the following infrastructure subprocessors:

| Subprocessor | Processing Activity | Location | Data Handled |
|---|---|---|---|
| **Amazon Web Services (AWS)** | Cloud compute, GPU workers, encrypted S3 storage | Mumbai Region (`ap-south-1`), India | Temporary image buffers (24h) |
| **Cloudflare Inc.** | Edge CDN, DDoS mitigation, DNS | Edge PoPs (India) | Encrypted widget script delivery |
| **Supabase / PostgreSQL** | Multi-tenant session state and catalog metadata | India Data Center | Anonymized session IDs, no photos |

---

## 7. Audit Rights & Termination

7.1. Upon written request (no more than once annually), FashXStudio shall provide the Brand with its latest third-party SOC2 Type II audit summary or independent penetration test attestation.  
7.2. Upon termination of the commercial agreement, FashXStudio shall immediately revoke all API keys, delete all cached merchant catalog metadata, and provide a written certificate of data erasure within thirty (30) days.

---

**Signed for and on behalf of:**

**[Brand Legal Name]**  
Name: _______________________________  
Title: ________________________________  
Date: ________________________________  

**FashXStudio Private Limited**  
Name: _______________________________  
Title: ________________________________  
Date: ________________________________  
