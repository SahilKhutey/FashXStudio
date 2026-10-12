# Support Operations, Abuse Handling & Incident Playbooks

- **Version:** 1.0 (Phase 12 Operating Foundation)
- **Scope:** B2B Merchant Support, Shopper Inquiries, and Trust & Safety Operations

---

## 1. Support Tiers & SLAs

| Severity / Tier | Definition & Examples | First Response SLA | Resolution SLA | Channel |
|---|---|---|---|---|
| **P1 - Critical** | Widget down across all PDPs; try-on worker pool failure; data breach report | $< 15\text{ minutes}$ | $< 2\text{ hours}$ | PagerDuty + Emergency Phone + `#merchant-urgent` |
| **P2 - Major** | Specific brand widget rendering defect; catalog sync pipeline stalled | $< 1\text{ hour}$ | $< 6\text{ hours}$ | Shared Slack Connect channel |
| **P3 - Standard** | Sizing chart alignment question; dashboard analytics export query | $< 4\text{ hours}$ | $< 24\text{ hours}$ | Email (`support@fashxstudio.com`) |
| **P4 - Low** | Feature requests, cosmetic CSS customization suggestions | $< 24\text{ hours}$ | 1 sprint | Support ticketing portal |
| **DPDP Request** | Shopper or brand request for biometric deletion or data portability | $< 12\text{ hours}$ | $< 48\text{ hours}$ | `privacy@fashxstudio.com` |

---

## 2. Playbooks

### Playbook A: Merchant PDP Widget Collision
**Symptoms:** Brand reports widget button does not appear or overlaps sticky "Add to Cart" button.
1. Inspect brand PDP via browser console:
   - Check if shadow DOM was blocked by aggressive brand CSP (Content Security Policy).
   - Check z-index collision with brand theme floating navigation elements.
2. In Merchant Dashboard (`/merchant/settings`), adjust `custom_css_offset` or mount target selector (e.g., `#fashx-custom-mount-container`).
3. Deploy override to CDN cache without requiring brand theme code redeployment.
4. Verify rendering on mobile viewports (iOS Safari, Android Chrome).

### Playbook B: DPDP Shopper Erasure Request
**Symptoms:** Shopper emails privacy contact requesting deletion of photo uploaded via Brand X storefront.
1. Authenticate requester identity (session token or email verification).
2. Execute automated erasure workflow:
   ```powershell
   python scripts/run_erasure.py --user-id $USER_ID --immediate
   ```
3. Verify that S3 storage keys under `t/{tenant_id}/s/{session_id}/` return 404.
4. Verify entry created in `erasure_tombstones`.
5. Send statutory confirmation receipt to user within 48 hours.

### Playbook C: Compromised Tenant API Key
**Symptoms:** Suspicious try-on request volume originating from unverified origin domains.
1. Invalidate compromised key immediately in database:
   ```sql
   UPDATE tenant_keys SET is_active = FALSE WHERE key_prefix = :compromised_prefix;
   ```
2. Generate new secret key pair and deliver securely to brand CTO via 1Password / encrypted channel.
3. Review audit logs (`v_tenant_usage`) to calculate unauthorized compute consumption.

---

## 3. Trust & Safety: Abuse Handling & Content Moderation

1. **Automated Pre-Inference NSFW Filter:**
   - Every shopper photo uploaded to the widget is evaluated by a lightweight local NSFW classifier prior to GPU worker dispatch.
   - Non-compliant images (explicit nudity, non-human objects, graphic imagery) are rejected synchronously with HTTP 422: `"Image does not meet quality and safety requirements"`.
   - Zero storage or model inference is performed for rejected images.
2. **Shopper Rate Limiting (Per IP & Session):**
   - Max 10 try-on requests per shopper IP per hour across all partner PDPs.
   - Max 25 try-on requests per session lifetime.
3. **Bot & Scraper Mitigation:**
   - Automated Cloudflare Turnstile verification challenged on suspicious request patterns or rapid sequential requests.
