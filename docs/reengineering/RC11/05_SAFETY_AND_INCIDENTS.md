# RC11: Safety, Incidents and Hard Stop Rules

## 1. Hard Stop Rules
Safety stop rules override all average satisfaction scores and engagement metrics. If any rule triggers, invitations pause immediately and containment begins.

| # | Trigger Event | Threshold | Immediate Action |
| :--- | :--- | :--- | :--- |
| **1** | **Suspected Data Exposure** | $\ge 1$ incident | Toggle `tryon_enabled = False`, pause invites, activate breach response runbook. |
| **2** | **Stability Crash Spike** | Crash-free sessions $< 98.0\%$ over 3 days | Pause invites, triage crash traces, deploy hotfix. |
| **3** | **Try-On Outage Spike** | Failure rate $> 25.0\%$ across 30 jobs | Pause invites, inspect Redis queue and vendor circuit breakers. |
| **4** | **API 5xx Error Wave** | Global HTTP 5xx $> 2.0\%$ over 24 hours | Pause invites, initiate SEV-1 infrastructure review. |
| **5** | **Spend Budget Breach** | Spend $> 80\%$ of budget ($\ge \$280 / \$350$) prior to Wave 3 | Freeze Wave 3 recruitment, review per-user generation limits. |
| **6** | **Privacy Attrition** | $\ge 3$ participants withdraw citing privacy | Pause recruitment, review consent clarity and capture guidance. |
| **7** | **Offensive AI Output** | $\ge 1$ inappropriate/offensive generation | Disable affected category immediately, contact user, log SEV-1. |

## 2. Incident Record Template
```markdown
## Incident Record
- **Incident ID**: INC-YYYYMMDD-XX
- **Detected At (UTC)**: YYYY-MM-DDTHH:MM:SSZ
- **Severity**: SEV-1 / SEV-2 / SEV-3
- **Affected Feature**: VTO / Feed / Onboarding / Auth
- **Affected Participant Codes**: P-xxxx, P-yyyy
- **Data Involved**: Logs / Queue / Telemetry
- **Containment Action**: Kill switch toggled / Feature disabled
- **Root Cause**: Identified technical defect
- **Remediation**: Hotfix commit SHA
- **Verification**: Command output verifying fix
- **Closed By**: Name & Date
```

## 3. Emergency Kill Switches
- **Backend Try-On Kill Switch**: `tryon_enabled = False` in settings dynamically disables all worker processing and informs mobile clients.
- **Rollout Pause**: Setting `registration_enabled = False` stops new invite code redemptions without disrupting active cohort sessions.
