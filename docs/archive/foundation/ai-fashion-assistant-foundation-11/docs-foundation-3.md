# AI Fashion Assistant — Production Build Foundation 3

## Scope

Foundation 3 adds the first application-facing contracts to the Foundation 0/1/2 baseline.

### Implemented

- Development authentication bridge behind a FastAPI dependency.
- Authenticated `/api/v1/profile` creation using the authenticated subject as the user identity.
- Self-access `/api/v1/profile/me` read endpoint.
- Permission-gated derived profile endpoint.
- Typed profile request/response contracts.
- Catalog search endpoint with cursor pagination and price/category filters.
- Catalog detail endpoint.
- Internal catalog intake endpoint with fail-closed service-token authentication.
- Catalog repository upsert/read methods.
- Application service wiring through FastAPI dependency injection.
- Standard application-error propagation through the existing gateway handlers.
- Foundation 3 API contract tests with mocked persistence boundaries.

## Security boundary

The MVP uses `X-User-ID` only as a development identity bridge. The production authentication provider remains behind the same dependency boundary and can later be replaced by Supabase/Auth0 without changing the application use cases.

The internal catalog-intake path requires `INTERNAL_SERVICE_TOKEN` to be configured and supplied; missing configuration fails closed with `403`.

## API surface

### Profile

- `POST /api/v1/profile`
- `GET /api/v1/profile/me`
- `GET /api/v1/profile/{user_id}/derived`

### Catalog

- `GET /api/v1/catalog/search`
- `GET /api/v1/catalog/{product_id}`
- `POST /api/v1/catalog/intake`

## Testing

Foundation 3 tests cover:

- authentication rejection when the development identity header is absent;
- authenticated profile creation contract;
- catalog search response contract using a mocked repository;
- the accumulated Foundation 0–2 suite.
