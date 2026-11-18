# Source Authentication Framework

## 1. Authentication Material and Protocol

All adapter requests requiring authentication obtain credentials through `SourceAuthProvider` implementations in `backend/fashx/catalog/acquisition/auth.py`.

The core abstraction is `AuthMaterial`:
```python
@dataclass(frozen=True)
class AuthMaterial:
    headers: dict[str, str]
    expires_at_epoch: int | None = None

    @property
    def is_expired(self) -> bool:
        if self.expires_at_epoch is None:
            return False
        # Buffer 60 seconds before hard expiration to avoid in-flight 401s
        return time.time() >= (self.expires_at_epoch - 60)
```

## 2. Supported Authentication Schemes

| Scheme | Class | Headers / Behavior |
| :--- | :--- | :--- |
| **None** | `NoAuthProvider` | Empty headers; used for public or fixture feeds. |
| **API Key Header** | `ApiKeyAuthProvider` | Configurable header (e.g. `X-API-Key`, `Authorization`). Fails closed if empty. |
| **Bearer Token** | `BearerTokenAuthProvider` | Injects `Authorization: Bearer <token>`. Fails closed if empty. |
| **HTTP Basic** | `BasicAuthProvider` | Base64-encodes `username:password` into `Authorization: Basic <base64>`. |
| **Signed Request** | `SignedRequestAuthProvider` | HMAC-SHA256 signature calculated over `access_key:timestamp`, setting `X-FashX-Access-Key`, `X-FashX-Timestamp`, and `X-FashX-Signature`. |
| **OAuth2 Client Credentials** | `OAuth2ClientCredentialsProvider` | Automatically exchanges `client_id` and `client_secret` at token endpoint, caches token until 60s before expiry, and refreshes proactively. |

## 3. Credential Redaction and Security Safeguards

1. **Strict Secret Masking**: All provider classes implement `__repr__` and `__str__` methods that mask secrets as `'***REDACTED***'`. API keys, bearer tokens, client secrets, and passwords are never logged or exposed in stack traces.
2. **403 Forbidden Backoff (No Infinite Refresh)**: An HTTP 403 Forbidden indicates permission denial or revocation, **not** token expiration. `OAuth2ClientCredentialsProvider.mark_forbidden()` blocks repeated refresh attempts and raises `PermissionError` to prevent flooding the auth server.
3. **Single Refresh on 401**: When an adapter receives an HTTP 401 Unauthorized, `SourceRetryPolicy` triggers `auth_provider.invalidate(source_id)` exactly once. If the re-attempt still returns 401, the error is immediately raised as non-retryable.
