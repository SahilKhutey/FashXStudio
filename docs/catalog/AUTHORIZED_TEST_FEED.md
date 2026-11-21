# Authorized Remote HTTP Test Feed Adapter

## 1. Overview and Purpose

`AuthorizedHttpFeedAdapter` (`backend/fashx/catalog/acquisition/adapters/authorized_http_feed.py`) provides a reference implementation of a production remote catalog connector. It connects to an approved merchant HTTPS feed URL (e.g. JSON or CSV exports) while enforcing all FashXStudio security and sync invariants.

## 2. Capabilities and Features

- **Protocol Conformance**: Implements both `BaseSourceAdapter` and `CatalogSourceAdapterV2`.
- **SSRF Hardening**: Uses `SourceHttpClient` with explicit hostname allowlisting, scheme enforcement (HTTPS strictly required), and private IP blocking.
- **Conditional HTTP Requests**: Tracks `ETag` and `Last-Modified` headers. When upstream returns HTTP 304 Not Modified, the adapter yields an empty batch without re-processing identical payloads.
- **Payload Size Limits**: Aborts feeds exceeding 10MB streaming size to prevent memory exhaustion attacks.
- **Schema Validation**: Parses JSON product records and maps fields to canonical `SourceProduct` representation, raising `SchemaChangedError` if required keys (`source_product_id`, `title`) are missing.

## 3. Configuration Example

```python
config = SourceConfig(
    source_slug="acme-apparel-feed",
    name="Acme Apparel HTTPS Feed",
    max_rps=2.0,
    refresh_hours=12,
)

auth = ApiKeyAuthProvider(api_key=secrets["acme_api_key"], header_name="X-API-Key")

adapter = AuthorizedHttpFeedAdapter(
    config=config,
    feed_url="https://feeds.acmeapparel.com/catalog/v1/products.json",
    auth_provider=auth,
    allowed_hostnames=["feeds.acmeapparel.com"],
    integration_status=IntegrationStatus.SANDBOX_VERIFIED,
)
```
