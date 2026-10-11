# Personal Data Breach Response Runbook

**Organization**: FashXStudio  
**Jurisdiction**: Republic of India  
**Applicable Regulations**: CERT-In Directions 2022 (Section 70B IT Act); Digital Personal Data Protection Act, 2023 & DPDP Rules 2025.  

---

## 1. Statutory Breach Notification Clocks

| Reporting Body | Statutory Deadline | Trigger Condition | Mandatory Recipient |
| :--- | :--- | :--- | :--- |
| **CERT-In (Cyber Emergency Response Team)** | **Strict 6 Hours** from notice/becoming aware | Any cybersecurity incident (unauthorized access, ransomware, data leak, compromised credentials, API breach) | `incident@cert-in.org.in` |
| **Data Protection Board of India (DPB)** | **Stage 1: Without Delay**<br>**Stage 2: Detailed 72 Hours** | Any breach of personal data (biometrics, user photos, wardrobe, personal identifiers) | DPB Official Portal / Appointed Email |
| **Affected Data Principals (Users)** | **Concurrent / Immediate** following initial containment | Real risk of harm to individuals from compromised data | Registered user email & in-app modal notice |

---

## 2. Immediate Containment Checklist (Hour 0 - Hour 1)

1. **Declare SEV-1 Security Incident**:
   - Notify Data Protection Officer (DPO), Lead Engineer, and Legal Counsel.
   - Start stopwatch for the **6-hour CERT-In deadline**.
2. **Isolate Compromised Systems**:
   - Rotate database master credentials in AWS Secrets Manager immediately.
   - Revoke compromised IAM credentials / ECS task execution roles.
   - Rotate S3 storage signing keys and Supabase/JWT signing keys.
   - If S3 bucket permissions breached: enable S3 Block Public Access across account immediately.
3. **Preserve Forensic Evidence**:
   - Do NOT terminate or reboot compromised ECS tasks or RDS instances without taking memory dumps / snapshots first.
   - Snapshot RDS database (`aws rds create-db-snapshot`).
   - Export CloudWatch log streams for the last 48 hours to forensic S3 archive with immutable Object Lock (`GOVERNANCE` mode).

---

## 3. Mandatory Reporting Templates

### A. CERT-In Incident Notification (Must file within 6 hours to `incident@cert-in.org.in`)
```text
To: incident@cert-in.org.in
Subject: INCIDENT REPORT - FashXStudio - Cyber Security Incident Notification

1. Name of Organisation: FashXStudio (India)
2. Contact Person / DPO: DPO & Compliance Officer (dpo@fashx.studio, +91-XXXXXXXXXX)
3. Date and Time of Incident Detection: [YYYY-MM-DD HH:MM IST]
4. Nature of Incident: [e.g., Unauthorized access to object storage / API credential compromise]
5. Affected System(s): AWS ap-south-1 ECS Fargate / S3 Bucket
6. Impact: [Assessment of compromised records; zero unencrypted biometrics confirmed]
7. Immediate Action Taken: Credentials rotated, bucket sealed, affected sessions revoked.
8. Logs & Forensic Status: Preserved in AWS ap-south-1 immutable CloudWatch streams.
```

### B. Data Protection Board Notification (DPDP Act 2023)
```text
1. Description of the nature of the personal data breach:
   [Detail breach vector, timestamp, affected data categories]
2. Number of Data Principals likely affected: [Count]
3. Likely consequences of the breach: [Low/Medium/High risk assessment]
4. Mitigation measures implemented and proposed: [Technical safeguards, credential revocation]
5. Contact details of the Data Protection Officer: dpo@fashx.studio
```

---

## 4. Annual Tabletop Drill Scenario (Breach Clock Exercise)

**Simulation Scenario: Leaked S3 Media Presigned URL / Compromised Task Role**
- **09:00 IST**: An external security researcher reports discovering an exposed S3 presigned URL containing generated try-on imagery on a public pastebin.
- **09:15 IST**: On-call engineer initiates SEV-1 security response, logs incident time in `#security-war-room`.
- **09:45 IST**: Forensic analysis identifies that URL expired 14 minutes after issuance, but investigates whether task role IAM credentials were leaked.
- **10:30 IST**: IAM task role rotated in AWS Secrets Manager; all ECS task definitions updated.
- **11:30 IST**: Incident draft notification completed and verified against CERT-In format within 2.5 hours (well within the 6-hour clock).
- **14:00 IST**: Exercise debrief, documentation of learnings, and sign-off by DPO.
