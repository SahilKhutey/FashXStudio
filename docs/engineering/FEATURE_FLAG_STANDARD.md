# Feature Flag Governance Standard

**Status:** Adopted
**Version:** 1.0
**Effective Date:** 2026-11-11
**Category:** Engineering Product Operations

---

## 1. Purpose and Scope

Feature flags allow FashXStudio to decouple software deployment from feature release, run controlled experiments, and maintain operational kill switches for third-party integrations (such as virtual try-on providers).

This standard governs feature flag lifecycles, naming conventions, safety defaults, and deprecation schedules across backend services and mobile applications.

The backend provides foundation support for flags in `backend/fashx/core/settings.py` via:
```python
feature_flags: dict[str, bool] = {}
enable_b2b: bool = False
tryon_enabled: bool = True
enable_frozen: bool = False
```

---

## 2. Feature Flag Categories

| Category | Description | Expected Lifetime | Example |
|---|---|---|---|
| **Release Flag** | Controls progressive rollout of newly developed user capabilities | Short-lived (weeks) | `vto_result_feedback` |
| **Operational Kill Switch** | Emergency cutoff for high-cost, external, or failing services | Long-lived / Permanent | `tryon_enabled` |
| **Experiment Flag** | Enables A/B testing or algorithmic variations (e.g., discovery rankers) | Duration of experiment | `discovery_ranker_v2` |
| **Capability Flag** | Gates tenant or administrative capabilities pending verification | Medium-lived (months) | `merchant_dashboard` |
| **Development-Only Flag** | Gates verbose diagnostics or mock fixtures in local development | Development only | `debug_vto_metadata` |

---

## 3. Flag Naming Conventions

All feature flags must use lowercase, explicit `snake_case` names describing the capability:

### Approved Examples
- `vto_result_feedback`
- `vto_provider_fashn`
- `catalog_partner_feed`
- `discovery_ranker_v2`
- `merchant_dashboard`
- `photo_quality_gate`

### Prohibited Names
- Ambiguous or generic names: `new_feature`, `flag1`, `test_enabled`, `temp_switch`, `toggle`.
- Personal or ticket-based names: `sahil_feature`, `issue_102`.

---

## 4. Twelve Core Feature Flag Rules

1. **Named Ownership:** Every feature flag must have a designated engineering or subsystem owner.
2. **Documented Description:** Every flag must have a written description of its function and intended behavior.
3. **Explicit Defaults:** Every flag must declare an explicit default boolean value.
4. **Rollout and Retirement Plan:** Every non-kill-switch flag must have a documented retirement trigger.
5. **Fail-Safe Defaults:** Flags controlling security, privacy, payment, or external spend must default to the safe/disabled state (`false`).
6. **Safe Fallback for Unknown Flags:** An unknown or unconfigured flag evaluated in code must always evaluate to `false`.
7. **No Client-Controlled Server Flags:** Mobile clients must never be able to enable privileged server-side capabilities by passing flag parameters in API requests.
8. **No Bypassing Governance Gates:** Feature flags must never bypass authentication, tenant isolation, or user consent checks.
9. **Independent Kill Switches:** Critical operational kill switches (e.g., `tryon_enabled`) must be toggleable via environment variables or central configuration without requiring code redeployments.
10. **Prompt Removal:** Once a feature reaches General Availability (100% rollout), the flag and associated dead branching paths must be removed from the codebase within two release cycles.
11. **Not an Authorization Replacement:** Flags control code availability; Role-Based Access Control (RBAC) controls user permissions. Flags must never substitute for authorization checks.
12. **Production Transparency:** Staging and production configurations must explicitly document the state of all active flags.

---

## 5. FashXStudio Suggested Flag Register

| Flag Identifier | Default State | Subsystem Owner | Notes & Operational Context |
|---|---|---|---|
| `tryon_enabled` | `true` | VTO | Master operational kill switch to pause try-on submissions during provider outages. |
| `vto_provider_fashn` | `false` | VTO | Enable live Fashn provider integration (only after credentials and contract tests pass). |
| `catalog_partner_feed`| `false` | Catalog | Enable automated sync from external merchant catalog feeds. |
| `discovery_ranker_v2` | `false` | Discovery | Test vector-augmented recommendation ranking algorithm against baseline. |
| `merchant_dashboard` | `false` | Merchant | Multi-tenant merchant portal (requires tenant isolation audit). |
| `photo_quality_gate` | `true` | Mobile / VTO | Reject blurry, poorly lit, or occluded user photos before provider dispatch. |
| `vto_result_feedback`| `false` | Product / VTO | Enable rating and qualitative feedback prompt on completed try-ons. |

---

## 6. Feature Flag Lifecycle

```text
PROPOSED ──► IMPLEMENTED (default safe) ──► TESTED ──► INTERNAL ──► LIMITED ROLLOUT ──► GENERAL AVAILABILITY ──► FLAG REMOVAL
```

### Reference Register Schema (YAML)

Flag metadata should be tracked according to this schema:

```yaml
flag: vto_result_feedback
description: Enables user feedback on completed virtual try-on results.
owner: vto
default: false
environment_overrides:
  dev: true
  test: true
  prod: false
rollout: internal
created_at: "2026-11-11"
removal_condition: "Remove within 2 sprints after 100% rollout to mobile clients."
security_sensitive: false
```
