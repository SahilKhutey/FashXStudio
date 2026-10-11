# Break-Glass & Emergency Access Runbook

## Overview
This runbook defines emergency recovery procedures for FashX Studio production infrastructure. As a solo founder with MFA enforced across all critical accounts, a documented break-glass procedure ensures service survivability and disaster recovery if primary devices or keys are lost.

## Critical Production Accounts & Custodianship

| Service | Primary Auth | Break-Glass Secret Location | Emergency Custodian |
| :--- | :--- | :--- | :--- |
| **AWS Cloud (ap-south-1)** | Root account hardware FIDO2 key + IAM SSO | Sealed physical envelope with root recovery credentials and 24-word seed phrase in bank safety deposit box | Trusted emergency contact |
| **GitHub (`SahilKhutey`)** | Hardware security key + Passkey | Printed recovery codes in fireproof safe | Trusted emergency contact |
| **Supabase (fashx-prod)** | MFA Authenticator + Security Key | Backup recovery code in sealed envelope | Self / Escrow |
| **Apple Developer & Play Console** | Hardware 2FA + Phone verification | Account recovery keys in safe | Self / Escrow |
| **Domain Registrar & DNS** | Hardware security key + Registrar Lock | Emergency authorization codes in sealed vault | Self / Escrow |
| **Password Vault (Bitwarden/1Password)** | Master password + Hardware Key | Emergency kit PDF with Master Key & recovery code stored offline | Designated emergency contact |

## Emergency Incident Declaration & Execution

1. **Trigger Condition:** Primary engineer incapacitated, lost all hardware MFA tokens, or active credential extortion.
2. **Access Procedure:**
   - Retrieve the sealed emergency packet from physical escrow.
   - Verify tamper-evident seals intact.
   - Access the offline recovery document containing root credentials and recovery codes.
   - Log into cloud console under witness; immediately revoke compromised IAM sessions.
   - Put application into maintenance mode if security incident:
     ```bash
     # Flip maintenance mode flag via Secrets Manager or parameter store
     aws ssm put-parameter --name "/fashx/prod/MAINTENANCE_MODE" --value "true" --overwrite
     ```
3. **Post-Recovery Audit:**
   - Rotate all passwords, access keys, and API secrets within 24 hours.
   - Re-generate MFA hardware keys and print new recovery codes.
   - Document root access timestamp and actions in `docs/logs/incident-timeline.md`.
