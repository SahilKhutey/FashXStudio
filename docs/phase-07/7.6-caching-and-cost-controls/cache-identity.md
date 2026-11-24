# Deterministic Cache Identity & Key Generation

## 1. Overview and Invariants

Every Virtual Try-On (VTO) inference request is computationally expensive and incurs direct third-party credit costs. The caching layer eliminates redundant inference by matching identical authorized inputs.

However, caching must **never** compromise correctness or privacy. The cache identity is governed by four strict invariants:

1. **User Identity Binding**: The requesting shopper's `user_id` is an indispensable component of the hash. Results generated for User A can **never** match or be returned to User B under any circumstances.
2. **Bit-Level Image Cryptographic Verification**: The raw image contents are verified via SHA-256 digests (`shopper_image_sha256` and `garment_image_sha256`). Re-uploading an altered image with the same name or ID invalidates cache matching.
3. **Multi-Dimension Version Tracking**: Model versions, pipeline configurations, preprocessing algorithms, and safety policies each contribute independently to the key.
4. **Canonical Serialization**: JSON output options are sorted and serialized with deterministic delimiters (`separators=(',', ':')`) so that key-value ordering does not create false cache misses.

---

## 2. Canonical Hash Formulation

The canonical cache key is computed as:

$$\text{CacheKey} = \text{SHA256}\Big(\text{user\_id} : \text{canonical\_product\_id} : \text{shopper\_hash} : \text{garment\_hash} : \dots : \text{options\_hash}\Big)$$

Full concatenation format:
```
{user_id}:{canonical_product_id}:{shopper_image_sha256}:{garment_image_sha256}:{shopper_asset_version}:{garment_image_version}:{provider}:{provider_model}:{provider_model_version}:{config_version}:{preprocessing_version}:{policy_version}:{garment_category}:{output_options_hash}
```

### 2.1 Parameter Specification

| Field | Type | Description |
|---|---|---|
| `user_id` | UUID | Requesting shopper UUID. Enforces single-user isolation. |
| `canonical_product_id` | UUID | Authoritative product entity in FashXStudio catalog. |
| `shopper_image_sha256` | String(64) | Hex-encoded SHA-256 digest of the validated shopper portrait. |
| `garment_image_sha256` | String(64) | Hex-encoded SHA-256 digest of the merchant garment photo. |
| `shopper_asset_version` | Integer | Version number of the shopper photo asset. |
| `garment_image_version` | Integer | Version number of the merchant garment asset. |
| `provider` | String | Third-party provider identifier (e.g. `fashn`). |
| `provider_model` | String | Model family (e.g. `tryon-v1.6`). |
| `provider_model_version` | String | Model version string (e.g. `2026.1`). |
| `config_version` | String | Infrastructure rendering configuration version. |
| `preprocessing_version` | String | Image cropping, alignment, and segmentation pipeline version. |
| `policy_version` | String | Moderation and garment category policy version. |
| `garment_category` | String | Garment taxonomy category (e.g. `tops`, `bottoms`, `one-pieces`). |
| `output_options_hash` | String(64) | SHA-256 of canonical sorted JSON dictionary of inference options. |

---

## 3. Collision Resistance

- The hash space is $2^{256}$, providing cryptographic collision resistance.
- Delimiters (`:`) prevent field boundary ambiguity.
- Hexadecimal digests are strictly normalized to lowercase.
