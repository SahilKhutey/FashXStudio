# Access Control Matrix, Secrets Management & Onboarding Security

- **Version:** 1.0 (Phase 12 Operating Foundation)
- **Review Cadence:** Quarterly
- **Compliance Alignment:** DPDP Act Rule 8 (Security Safeguards), SOC2 Type II Trust Services Criteria

---

## 1. Role-Based Access Control (RBAC) Matrix

| Resource / System | Founder / CTO | Platform Engineer | GTM / Partner Lead | External Auditor |
|---|---|---|---|---|
| **Production AWS Console** | Full Admin | PowerUser (No IAM) | No Access | Read-Only (Audit) |
| **Production Database (RDS)** | Break-glass only | Read Replica only | No Access | Anonymized dump only |
| **Ephemeral S3 Image Buckets** | Break-glass only | Break-glass only | No Access | No Access |
| **Merchant Admin Dashboard** | Admin | Admin / Read | Brand Scoped | Read-Only |
| **GitHub Repository (`main`)** | Admin (PR merge) | Write (Branch + PR) | Read-Only (Docs) | Read-Only |
| **Cloudflare / CDN DNS** | Admin | Config Operator | No Access | No Access |
| **1Password Vaults** | Master Admin | Engineering Vault | Sales Vault | No Access |

---

## 2. Secrets Management & Rotation Policy

1. **Zero Plaintext Secrets:** Under no circumstance may database passwords, JWT signing keys, or third-party API credentials be committed to git, Slack, or unencrypted local drives.
2. **Secrets Storage:** AWS Secrets Manager / Infisical injected into container environments via secure environment variables at runtime.
3. **Rotation Cadence:**
   - Production Database Root Passwords: Every 90 days.
   - Merchant API Signing Secret: Annually or upon employee offboarding.
   - Cloudflare API Tokens: Every 180 days.
4. **Emergency Key Invalidation:** Documented in `docs/operations/support-ops.md` Playbook C.

---

## 3. Intellectual Property (IP) Assignment & Onboarding Pack

Every new engineer, contractor, or advisor joining FashXStudio must execute the following prior to receiving repository access:
- [ ] Proprietary Information and Inventions Agreement (PIIA) assigning 100% of codebase, algorithms, architectures, and documentation to FashXStudio Private Limited.
- [ ] Non-Disclosure Agreement (NDA) with specific restrictions on proprietary Indian garment drape datasets.
- [ ] Workstation Compliance Check: Full-disk encryption (BitLocker / FileVault) enabled; mandatory password manager (1Password) with FIDO2 hardware token or authenticator app.
- [ ] Background check and identity verification on file.

---

## 4. Offboarding Protocol (Termination SLA $< 60$ Minutes)

Upon departure of any team member:
1. Revoke Google Workspace / corporate email account.
2. Terminate GitHub organization membership and revoke all SSH/GPG keys.
3. Invalidate personal AWS IAM access keys and rotate any shared vault credentials the individual had access to.
4. Revoke VPN / Tailscale network access.
5. Remotely wipe company data from registered MDM devices.
