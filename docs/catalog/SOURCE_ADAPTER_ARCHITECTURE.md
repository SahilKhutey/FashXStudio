# Source Adapter Architecture

## 1. Overview and Core Philosophy

In FashXStudio, product acquisition is built on a strict permission-aware foundation:
> **An adapter is not a live integration merely because it accepts product records and returns normalized products. A live integration must authenticate against an authorized source, retrieve data through its documented access method, handle pagination and rate limits, synchronize changes, and produce independently verifiable results.**

The architecture enforces a strict boundary:
- **Retailer adapters** (`backend/fashx/catalog/acquisition/adapters/`) contain provider-specific transport, authentication, schema parsing, and field mapping.
- **Common services** (`backend/fashx/catalog/acquisition/`) govern synchronization schedules, checkpoint persistence, authorization guards, rate limiting, SSRF security, and catalog offer reconciliation.
- **Shopper catalog isolation**: Retailer adapters must never write directly to shopper-facing catalog tables or publish items without authorization verification.

```
+-------------------------------------------------------------+
|                Authorized Source Registry                   |
| (Merchant, Source, Credentials, Rights, Expirations, Status)|
+-------------------------------------------------------------+
                              |
                     [Authorization Guard]
                              |
+-------------------------------------------------------------+
|                 Source Adapter Framework                    |
|  - Auth Providers (ApiKey, Bearer, OAuth2, Signed Request)  |
|  - Secure Transport (SSRF Filtering, Streaming Limits)      |
|  - Rate Limiter (Token Bucket, Retry-After Header Handling) |
|  - Safe Pagination (Loop & Bounded Empty Page Detection)    |
|  - Error Mapping (CatalogSourceError -> SourceErrorCode)    |
+-------------------------------------------------------------+
                              |
+-------------------------------------------------------------+
|                 Catalog Sync Engine                         |
|  - Atomic Checkpoint Persistence (Checkpoints Table)        |
|  - Durable Execution Telemetry (Sync Runs Table)            |
|  - Safe Stale Reconciliation (100% Full Success Only)       |
+-------------------------------------------------------------+
                              |
+-------------------------------------------------------------+
|                 Acquisition Pipeline & DB                   |
|  - Canonical Garments, Merchant Products, Merchant Offers   |
+-------------------------------------------------------------+
```

## 2. Integration Status Classification

Every catalog adapter explicitly advertises its `integration_status` via `IntegrationStatus`:

| Status | Definition | Examples |
| :--- | :--- | :--- |
| `MOCK` | Simulated fixtures, synthetic payloads, or static contract tests. Not connected to external servers. | `AmazonAdapter`, `MyntraAdapter`, `FlipkartAdapter` |
| `LOCAL` | Local file drop or internal filesystem feed. Operates on authorized offline data dumps. | `PartnerFeedAdapter` (CSV/JSON file drop) |
| `SANDBOX_VERIFIED` | Connected to verified external merchant sandbox environment with real credentials. | `AuthorizedHttpFeedAdapter` (in staging) |
| `PRODUCTION_VERIFIED` | Connected to production retailer API under signed bilateral contract and active evidence. | Future live bilateral connectors |

## 3. Protocol Contracts

The v2 adapter contract is defined in `backend/fashx/catalog/acquisition/contracts_v2.py`:

```python
@runtime_checkable
class CatalogSourceAdapterV2(Protocol):
    source_slug: str
    integration_status: IntegrationStatus

    def capabilities(self) -> SourceCapabilities: ...
    async def health_check(self) -> SourceHealthReport: ...
    async def fetch_page(self, cursor: str | None = None, limit: int = 100) -> AcquisitionBatch: ...
    async def start_full_sync(self) -> str: ...
    async def start_incremental_sync(self, watermark: datetime | None = None, cursor: str | None = None) -> str: ...
    def normalize_product(self, raw_record: dict[str, Any]) -> SourceProduct: ...
    def map_error(self, exc: Exception) -> SourceErrorCode: ...
```

## 4. Key Subsystems

1. **Authentication Layer (`auth.py`)**: Supports API keys, Bearer tokens, HTTP Basic, HMAC signed requests, and OAuth2 Client Credentials with automatic token caching and proactive refresh.
2. **SSRF & Transport Security (`http_client.py`)**: Blocks loopback, RFC 1918 private subnets, link-local metadata services, DNS rebinding, and enforces a 10MB streaming response limit.
3. **Loop-Protected Pagination (`pagination.py`)**: Detects repeated pagination cursors and empty-page cycles, terminating runaway requests.
4. **Resilient Synchronization (`sync_engine.py` & `checkpoints.py`)**: Implements durable checkpoint tracking with strict transactional sequencing: database records are committed before checkpoints advance.
