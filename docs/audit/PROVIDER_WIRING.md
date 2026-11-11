# FashXStudio — Phase 02.4: Provider Wiring Audit

**Document ID:** `FASHX-AUD-006`  
**Phase:** 02.4 — Audit Mock Versus Real Integrations (Execution B)  
**Date:** 2026-11-11  
**Author:** Antigravity Agent (Auditor)  
**Status:** COMPLETE (Audited Baseline)  
**Branch:** `recovery/rc13.1-governance-correction`  

---

## 1. Executive Summary

This document audits the dynamic dependency injection, factory resolution, and provider wiring across FashXStudio. It traces how abstract ports are bound to concrete adapters at runtime, identifying where mock adapters serve as default fallbacks and how production guards enforce live commercial adapters.

---

## 2. Virtual Try-On (VTO) Provider Wiring

**Source Location:** [`backend/fashx/core/dependencies.py:58-89`](file:///c:/Users/ASUS/Documents/FashXStudio/backend/fashx/core/dependencies.py#L58-L89)

### 2.1 Factory Logic (`get_tryon_adapter`)
```python
def get_tryon_adapter() -> TryOnAdapter:
    s = get_settings()
    if s.tryon_provider == "fashn_api":
        if not s.fashn_api_key or not s.fashn_api_key.get_secret_value():
            raise ValueError("FASHN_API_KEY required when TRYON_PROVIDER=fashn_api")
        adapter = FashnApiAdapter(
            api_key=s.fashn_api_key.get_secret_value(),
            base_url=s.fashn_base_url,
            model=s.fashn_model,
            mode=s.fashn_mode,
            cost_usd_est=s.tryon_est_cost_usd,
            timeout_s=float(s.tryon_timeout_s),
        )
    elif s.tryon_provider == "fashn_selfhost":
        raise NotImplementedError(
            "fashn_selfhost try-on adapter is not implemented; mock fallback is forbidden"
        )
    elif s.tryon_provider == "mock":
        adapter = MockAdapter()
    else:
        raise ValueError(f"Unknown or unsupported tryon_provider: {s.tryon_provider}")

    if s.env == "prod":
        assert_production_license(adapter)

    return adapter
```

### 2.2 Findings:
- **Default Resolution:** `s.tryon_provider` defaults to `"mock"`, constructing `MockTryOnAdapter`.
- **Mock Behavior:** PIL-based fast compositing with an unmistakable `PREVIEW ONLY - MOCK VTO` banner watermark; reports `is_commercial_cleared = False`.
- **Production Guard:** If `s.env == "prod"`, `assert_production_license(adapter)` checks `adapter.is_commercial_cleared`. If `MockAdapter` is supplied, it immediately crashes the process.
- **Hosted Real Adapter:** `FashnApiAdapter` is fully implemented in `backend/fashx/infrastructure/tryon/fashn_api.py`. It requires `FASHN_API_KEY`.
- **Self-Hosted Option:** `fashn_selfhost` raises `NotImplementedError` directly. Mock fallback is forbidden.

---

## 3. Object Storage Provider Wiring

**Source Location:** [`backend/fashx/core/dependencies.py:36-55`](file:///c:/Users/ASUS/Documents/FashXStudio/backend/fashx/core/dependencies.py#L36-L55)

### 3.1 Factory Logic (`get_storage`)
```python
def get_storage() -> ObjectStorage:
    settings = get_settings()
    if settings.storage_backend == "s3":
        return S3Storage(
            bucket=settings.s3_bucket or "fashx-media",
            endpoint_url=settings.s3_endpoint_url,
            region=settings.s3_region,
            key_id=settings.s3_access_key_id.get_secret_value()
            if settings.s3_access_key_id else None,
            secret=settings.s3_secret_access_key.get_secret_value()
            if settings.s3_secret_access_key else None,
        )
    return LocalStorage(root_dir=settings.local_storage_dir)
```

### 3.2 Findings:
- **Default Resolution:** `settings.storage_backend` defaults to `"local"`, returning `LocalStorage(root_dir="./.local_storage")`.
- **Local Dev Guard:** `LocalStorage.__init__` raises `RuntimeError("LocalStorage cannot be used in production (ENV=prod)")`.
- **Local Dev URLs:** Local storage generates HMAC-signed URLs pointing to `http://127.0.0.1:8000/dev-files/{key}`, which are served exclusively when `ENV in ("dev", "test")`.
- **Cloud S3 Adapter:** `S3Storage` (`backend/fashx/infrastructure/storage/s3.py`) implements standard AWS S3 and Cloudflare R2 protocols using `boto3`.

---

## 4. Authentication & Identity Provider Wiring

**Source Location:** [`backend/fashx/security/deps.py:27-48`](file:///c:/Users/ASUS/Documents/FashXStudio/backend/fashx/security/deps.py#L27-L48)

### 4.1 Factory Logic (`get_verifier`)
```python
@lru_cache(maxsize=1)
def get_verifier() -> TokenVerifier:
    settings = get_settings()
    if settings.auth_mode == "local":
        if not settings.auth_jwt_secret:
            raise ValueError("AUTH_JWT_SECRET required in local auth mode")
        return LocalJWTVerifier(
            secret=settings.auth_jwt_secret.get_secret_value(),
            issuer=settings.auth_issuer,
            audience=settings.auth_audience,
        )
    elif settings.auth_mode == "jwks":
        if not settings.auth_jwks_url:
            raise ValueError("AUTH_JWKS_URL required in jwks auth mode")
        return JWKSVerifier(
            jwks_url=settings.auth_jwks_url,
            issuer=settings.auth_issuer,
            audience=settings.auth_audience,
        )
    else:
        raise ValueError(f"Unsupported auth_mode: {settings.auth_mode}")
```

### 4.2 Findings:
- **Default Resolution:** `settings.auth_mode` defaults to `"local"`. Tokens are signed and verified symmetrically using `AUTH_JWT_SECRET`.
- **External Identity Provider:** When `auth_mode == "jwks"`, `JWKSVerifier` downloads public keys from `AUTH_JWKS_URL` with RSA/ECDSA signature verification and key rotation caching.
- **Production Gate:** `Settings._fail_fast()` demands `AUTH_MODE=jwks` and `AUTH_JWKS_URL` when `is_production` is true.

---

## 5. Embeddings & Multimodal Enrichment Wiring

### 5.1 Embedding Provider Wiring
**Source Location:** [`backend/fashx/catalog/embeddings/service.py:143-153`](file:///c:/Users/ASUS/Documents/FashXStudio/backend/fashx/catalog/embeddings/service.py#L143-L153)

```python
def get_default_embedder() -> ImageTextEmbedder:
    env = os.getenv("ENV", "dev").lower()
    if env == "production":
        from fashx.catalog.embeddings.marqo_fashionclip import MarqoFashionClipEmbedder
        return MarqoFashionClipEmbedder()

    from fashx.catalog.embeddings.fake import FakeEmbedder
    return FakeEmbedder()
```

- **In `dev` / `test` / `local`:** Returns `FakeEmbedder()`. It computes SHA-256-derived normalized 512-dim vectors without downloading neural network weights. It raises a runtime error if executed in an environment other than `dev`, `test`, or `local`.
- **In `production`:** Dynamically imports and instantiates `MarqoFashionClipEmbedder`, which loads `hf-hub:Marqo/marqo-fashionCLIP` via `open_clip` to produce genuine multimodal fashion embeddings.

### 5.2 Garment Enrichment Wiring
**Source Location:** [`backend/fashx/catalog/application/enrich_garment.py:30-36`](file:///c:/Users/ASUS/Documents/FashXStudio/backend/fashx/catalog/application/enrich_garment.py#L30-L36)

```python
class EnrichGarmentUseCase:
    def __init__(self, uow: CatalogUnitOfWork, enricher: GarmentEnricherPort | None = None) -> None:
        self.uow = uow
        self.enricher = enricher or HeuristicGarmentEnricher()
```

- **Default Enrichment:** Resolves to `HeuristicGarmentEnricher` (rule-based pattern, color, and category extraction).
- **VLM Client:** `MockVlmClient` provides deterministic rule-based attribute extraction; `AnthropicVlm` provides live Anthropic Claude Messages API attribute extraction. Neither is wired as the default in `EnrichGarmentUseCase` unless passed explicitly.

---

## 6. Repository & Persistence Wiring

### 6.1 Active Consumer API Routers
The active HTTP API routers (`catalog`, `tryon`, `profile`, `commerce_wardrobe`, `recommendation`, `onboarding`) are wired to SQLAlchemy Unit of Work instances:
```python
def get_tryon_uow() -> TryOnUnitOfWork:
    return TryOnUnitOfWork(get_session_factory())

def get_catalog_uow() -> CatalogUnitOfWork:
    return CatalogUnitOfWork(get_session_factory())

def get_profile_uow() -> ProfileUnitOfWork:
    return ProfileUnitOfWork(get_session_factory())

def get_commerce_uow() -> CommerceWardrobeUnitOfWork:
    return CommerceWardrobeUnitOfWork(get_session_factory())
```
All of these connect through `get_session_factory()`, which connects to PostgreSQL via `DATABASE_URL`.

### 6.2 Core Runtime Bootstrap Registry
**Source Location:** [`backend/fashx/core/bootstrap.py`](file:///c:/Users/ASUS/Documents/FashXStudio/backend/fashx/core/bootstrap.py)
In `bootstrap.py`, the `CoreRuntime` registers in-memory repositories (`InMemoryCartRepository`, `InMemoryOrderRepository`, `InMemoryPaymentRepository`, `TestPaymentProvider`, `TestCarrierProvider`) on `runtime.registry`. These correspond to the **frozen post-MVP commerce domains (C05–C11)**, which are decoupled and unmounted from the active MVP consumer router.
