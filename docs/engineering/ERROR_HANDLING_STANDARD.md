# Error Handling and Response Standard

**Status:** Adopted
**Version:** 1.0
**Effective Date:** 2026-11-11
**Category:** Engineering Reliability

---

## 1. Purpose and Scope

This standard establishes a unified, predictable error contract across all public and mobile-facing APIs in FashXStudio. Historically, error handling was dispersed across `backend/fashx/core/errors.py`, `backend/fashx/gateway/errors.py`, and `backend/fashx/security/errors.py`.

This standard unifies the public error envelope for `/api/v1` while preserving backward compatibility for existing clients.

---

## 2. Standard Public Error Envelope

All error responses from `/api/v1` endpoints must return a standardized JSON structure with a top-level `error` object and request correlation ID:

```json
{
  "error": {
    "code": "tryon_provider_unavailable",
    "message": "Virtual try-on is temporarily unavailable. Please try again shortly.",
    "details": null,
    "field_errors": []
  },
  "request_id": "e4c5d6a7-1234-4567-8901-123456789abc"
}
```

### Schema Definitions

| Field | Type | Description |
|---|---|---|
| `error.code` | string (snake_case) | Stable, machine-readable application error identifier |
| `error.message` | string | Human-readable, user-safe description suitable for UI presentation |
| `error.details` | object / null | Optional dictionary providing structured, safe debugging context |
| `error.field_errors` | array of objects | List of validation failures for multi-field form inputs |
| `request_id` | string (UUID) | Unique correlation ID for support and log tracing |

---

## 3. Validation Errors Envelope

When request payloads fail Pydantic or schema validation (HTTP 422 Unprocessable Entity), the `field_errors` array must be populated:

```json
{
  "error": {
    "code": "validation_error",
    "message": "The request payload contains one or more validation errors.",
    "details": null,
    "field_errors": [
      {
        "field": "garment_id",
        "code": "required",
        "message": "A valid garment ID is required."
      },
      {
        "field": "category",
        "code": "invalid_choice",
        "message": "Category must be one of: tops, bottoms, dresses, outerwear."
      }
    ]
  },
  "request_id": "e4c5d6a7-1234-4567-8901-123456789abc"
}
```

---

## 4. HTTP Status Code Mapping

Use standard HTTP status codes according to RFC 9110:

| HTTP Status | Category | Usage in FashXStudio | Example Scenario |
|---|---|---|---|
| **400 Bad Request** | Client Error | Malformed JSON syntax, invalid query syntax | Missing required header |
| **401 Unauthorized** | Client Error | Missing or invalid authentication token | Expired JWT bearer token |
| **403 Forbidden** | Client Error | Authenticated user lacks permission for action | Accessing another user's try-on job |
| **404 Not Found** | Client Error | Requested resource does not exist | Invalid `product_id` or `job_id` |
| **409 Conflict** | Client Error | State conflict with current resource state | Duplicate profile creation |
| **413 Payload Too Large**| Client Error | Uploaded asset exceeds size boundary | Photo upload > 10 MB limit |
| **415 Unsupported Media**| Client Error | Content-Type or file format not supported | Uploading a `.gif` or `.bmp` file |
| **422 Unprocessable Entity**| Client Error | Schema validation failure | Missing required field in JSON payload |
| **429 Too Many Requests**| Client Error | Rate limit exceeded | VTO submission cap reached |
| **500 Internal Error** | Server Error | Unhandled server exception | Database query execution crash |
| **502 Bad Gateway** | Server Error | Upstream vendor returned invalid response | FASHN API returned malformed HTTP |
| **503 Service Unavailable**| Server Error | Essential backend dependency is down | PostgreSQL or Redis offline |
| **504 Gateway Timeout** | Server Error | Upstream vendor timed out | VTO generation exceeded 60s timeout |

---

## 5. Standard Error Codes (snake_case)

All newly introduced public error codes must use lowercase `snake_case`:

```text
# Authentication & Identity
authentication_required
token_expired
invalid_credentials
permission_denied

# Resource Management
resource_not_found
resource_conflict
payload_too_large
unsupported_media_type
validation_error

# Privacy & Consent
consent_required
consent_revoked

# Virtual Try-On
tryon_provider_unavailable
tryon_timeout
tryon_failed
tryon_rate_limit_exceeded

# Catalog & Partner
catalog_source_unavailable
merchant_unauthorized

# System & Infrastructure
service_unavailable
internal_error
```

### Backward Compatibility Policy

Existing clients may still expect legacy uppercase codes (e.g., `CORE_NOT_FOUND`, `AUTH_UNAUTHORIZED`, `VALIDATION_FAILED`).
1. Do not rename legacy codes in place on existing endpoints.
2. New endpoints must strictly adopt the lowercase `snake_case` standard.
3. Transition existing endpoints to the new error schema via versioned deprecation cycles.

---

## 6. Security and Error Handling Rules

1. **No Stack Traces to Clients:** Never expose Python tracebacks, exception class names, or internal file paths in API responses.
2. **No Database Leakage:** Never expose SQL queries, table names, or constraint names in error messages.
3. **No Vendor Secrets:** Never expose vendor API keys, raw upstream HTTP headers, or external provider error payloads to the client.
4. **No Silent 200s:** Never return HTTP 200 OK with an error payload in the response body.
5. **Ownership Privacy:** To prevent resource enumeration, querying another user's private resource (e.g., `/api/v1/tryons/{foreign_job_id}`) must return HTTP 404 Not Found rather than HTTP 403 Forbidden.
6. **Supportability:** Always include a valid, traceable `request_id` in every error response.
