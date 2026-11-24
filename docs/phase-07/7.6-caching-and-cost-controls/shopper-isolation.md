# Shopper Isolation & Private Result Caching

## 1. Privacy Threat Model

A virtual try-on render incorporates the shopper's personal photograph (face, body silhouette, skin tone, personal environment) merged with an apparel garment.

Under GDPR, CCPA, and standard privacy practices, this output constitutes personal data.

**Threats Mitigated**:
1. **Cross-User Result Leakage**: If User B tries on the same dress that User A tried on, returning User A's cached render would constitute an egregious privacy violation.
2. **Key Spoofing / Tampering**: An attacker querying an existing cache key directly must never receive another user's visual render.
3. **Storage URI Predictability**: S3 URLs must be private and signed; raw storage paths must not allow cross-tenant enumeration.

---

## 2. Multi-Layer Defense in Depth

```
                        Request from Shopper A
                                  |
                                  v
                   +------------------------------+
                   | Layer 1: Cache Key Binding   |
                   | Key incorporates User A UUID |
                   +--------------+---------------+
                                  |
                                  v
                   +------------------------------+
                   | Layer 2: Database Query      |
                   | SELECT ... WHERE key = ?     |
                   +--------------+---------------+
                                  |
                                  v
                   +------------------------------+
                   | Layer 3: Authorize Ownership |
                   | record.owner == Shopper A?   |
                   +--------------+---------------+
                                  |
                      Yes         |         No (Mismatch)
                                  v              |
                   +---------------------+       v
                   | Return Presigned S3 |  +-------------------------+
                   | Private Asset URI   |  | Security Alert Emitted  |
                   +---------------------+  | CacheSecurityError      |
                                            +-------------------------+
```

### 2.1 Layer 1: Cryptographic Key Binding
`user_id` is an input parameter to `compute_cache_key`. Two users trying on the exact same garment with identical settings produce two completely different SHA-256 keys.

### 2.2 Layer 2: Record-Level Owner Column
The `tryon_result_cache` table explicitly stores `owner_user_id` alongside each cache record with a foreign key cascade to `users.id`.

### 2.3 Layer 3: Application Authorization Check
Even if a key collision were to occur, `TryOnCacheService.get()` performs an explicit assertion:
```python
if record.owner_user_id != requesting_user_id:
    raise CacheSecurityError(...)
```

### 2.4 Layer 4: Private Object Storage Isolation
Cached results are stored in private S3 buckets (`fashx-shopper-results-private/users/{user_id}/tryon/...`). Pre-signed download URLs have a short TTL (15 minutes) and are only minted upon authenticated request.
