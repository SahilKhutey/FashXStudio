# Catalog Source Register

A source may be enabled in production only when `Status = cleared` and a written reply or agreement is linked.
Unapproved, pending, or suspended sources are rejected by runtime guards and excluded from live discovery queries.

| Source | Access | Legal Basis | Display Images | AI Try-On on Images | Store Image Copies | Refresh | Rate Limit | Takedown Contact | Status | Evidence |
|---|---|---|---|---|---|---|---|---|---|---|
| **FabIndia** | Partner feed (CSV / Google Merchant) | Direct Brand Partnership Agreement | Yes | Yes | Yes (`mirror`) | Daily | N/A | `partnerships@fabindia.net` | `cleared` | [`docs/evidence/fabindia-partnership.md`](../evidence/fabindia-partnership.md) |
| **Snitch** | Partner feed (CSV / Shopify Export) | Direct Brand Partnership Agreement | Yes | Yes | Yes (`mirror`) | Daily | N/A | `partners@snitch.co.in` | `cleared` | [`docs/evidence/snitch-partnership.md`](../evidence/snitch-partnership.md) |
| **Westside** | Partner feed (Google Merchant XML) | Direct Brand Partnership Agreement | Yes | Yes | Yes (`mirror`) | Daily | N/A | `catalog-ops@trent.co.in` | `cleared` | [`docs/evidence/westside-partnership.md`](../evidence/westside-partnership.md) |
| **Flipkart Affiliate API** | REST API (Delta feed) | Affiliate ToU (Derivative works clarification) | Verify | Verify (Derivative-works clause) | Verify | Delta feed (24h) | 5 rps (cap: 20 rps) | `affiliate-support@flipkart.com` | `pending` | Pending written legal clarification on derivative works |
| **Myntra / Ajio (via Admitad)** | Network product feed / Deep links | Network Publisher Agreement | Verify | Verify | Verify | Daily feed | 2 rps | `compliance@admitad.com` | `pending` | Awaiting feed clearance and image rights confirmation |
| **Amazon Associates** | Link-out only (Deep link) | Associates Operating Agreement | N/A | N/A | No | N/A | N/A | `associates@amazon.in` | `link-out only` | PA-API 5.0 deprecated; Creators API requires qualifying sales; no catalog ingestion |
| **Seed Demo (Internal)** | Test Fixtures | Synthetic Test Data | No | No | No | Manual | N/A | `dev@fashx.studio` | `suspended` | Test fixture data only; strictly excluded from production feed |

---

## Source Clearance Checklist

For any new source to transition from `pending` to `cleared`:
1. **Written Permission:** Explicit agreement covering (a) product metadata display, (b) image display, and (c) server-side AI processing (try-on and attribute tagging).
2. **Image Storage Policy:** If `rights_tryon = true`, `image_policy` must be `mirror` (storing a high-resolution processed copy in private object storage `catalog/<slug>/...`). Hotlink-only sources cannot participate in virtual try-on.
3. **Currency Guarantee:** All prices must be strictly formatted in INR.
4. **Takedown SLA:** Verified contact point committed to removal within ≤ 10 minutes.
5. **CLI Clearance:** The source can only be cleared via `scripts/catalog/clear_source.py` with an immutable evidence URL.
