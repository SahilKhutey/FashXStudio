# Phase 05.8: Catalog Security and Compliance Validation

## 1. Security Architecture & Threat Model

The FashXStudio catalog operating system acts as the gateway between external merchant feeds, partner networks, and internal user-facing AI services. Due to this boundary position, the architecture strictly enforces five defensive controls:

1. **Multi-Tenant Isolation**: Complete isolation between merchant datasets.
2. **SSRF & Egress Protection**: Ingestion connectors and image fetchers cannot reach internal metadata services or private networks.
3. **Secret Masking & Redaction**: API keys, contract hashes, and bearer tokens are never leaked in logs or error traces.
4. **Default-Deny Permission Scopes**: Image storage and VTO processing require explicit, granular, time-bounded legal permissions.
5. **Immediate Takedown & Discovery Severance**: Removed products immediately become unreachable in shopper APIs (HTTP 404).

---

## 2. Multi-Tenant Isolation Enforcement

### 2.1 Threat Scenario
Merchant A attempts to modify, override, deactivate, or read the product records or offers belonging to Merchant B.

### 2.2 Defensive Implementation
In `MerchantProductUpdateService`, `MerchantProductRemovalService`, and related operational services:
```python
if product.merchant_id != merchant_id:
    raise CatalogAuthorizationError(
        "Merchant does not own this product",
        code="tenant_isolation_violation",
    )
```
The caller's authenticated `merchant_id` is extracted from verified JWT claims or administrative session context and matched against the owning entity's `merchant_id`. If a mismatch occurs, the operation is rejected immediately with code `tenant_isolation_violation`.

### 2.3 Automated Test Verification
Verified in test case `test_p58_026_merchant_tenant_isolation`:
- Merchant A calls `apply_product_override` on Merchant B's product -> Rejected with `CatalogAuthorizationError`.
- Merchant A calls `deactivate_offer` on Merchant B's offer -> Rejected with `CatalogAuthorizationError`.

---

## 3. SSRF & Network Boundary Protection

### 3.1 Threat Scenario
A compromised or malicious feed provides product URLs or image URLs resolving to local or cloud metadata addresses (e.g., `http://169.254.169.254/latest/meta-data/` or `http://127.0.0.1:8000/internal/admin`).

### 3.2 Defensive Implementation
In `fashx.catalog.acquisition.security`:
- All feed endpoints and image URLs are resolved against DNS and validated before socket connection.
- Private IPv4/IPv6 ranges (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`, `127.0.0.0/8`, `169.254.0.0/16`, `::1/128`, `fc00::/7`) are blocked.
- Redirection chains are bounded (maximum 3 hops) and re-validated at every hop.

---

## 4. Secret Masking & Audit Trail Redaction

### 4.1 Threat Scenario
Audit trails or debug logs expose merchant API keys, basic authentication credentials, or S3 signed query strings.

### 4.2 Defensive Implementation
In `SourceAuditService.log_event` and logging interceptors:
- Payload sanitization scrubs keys matching `(?i)(token|key|secret|password|auth|authorization|credential)`.
- Sensitive values are replaced with `[REDACTED]`.
- Credential references in `CatalogSource` are stored encrypted or referenced via external KMS identifiers.

---

## 5. Granular Permission Scopes & AI/VTO Gating

### 5.1 Threat Scenario
A public product feed is mirrored into the catalog, and its images are automatically routed to virtual try-on models without merchant authorization, violating copyright or likeness rights.

### 5.2 Defensive Implementation
In `AcquisitionPipeline` and image lifecycle handlers:
- `CatalogPermissionCode.IMAGE_STORE`: If absent, image bytes are not saved to disk or object storage (`P58-011`).
- `CatalogPermissionCode.VTO_PROCESS`: If absent, `rights_tryon` is set to `False`, and images cannot be dispatched to virtual try-on pipelines (`P58-012`).
- Image ingestion is decoupled from AI processing: display permission does not grant AI processing rights.

---

## 6. Takedown Enforcement & Shopper Discovery Severance

### 6.1 Threat Scenario
A merchant issues a DMCA takedown or removes a product due to counterfeit suspicion. Cached or stale catalog entries continue serving the product to shoppers.

### 6.2 Defensive Implementation
- `SourceTakedownService.execute_takedown` sets `takedown_status = COMPLETED` and `status = INACTIVE`.
- `customer_router._resolve_garment_detail` filters out offers where `takedown_status != "NONE"` or `status != "ACTIVE"`.
- If no active offers remain, the router raises `EntityNotFoundError`, returning HTTP 404 to the shopper (`P58-021`, `P58-024`).
- `AcquisitionPipeline` guards against reactivation: subsequent normal sync runs recognize the active takedown and reject re-activation (`P58-025`).
