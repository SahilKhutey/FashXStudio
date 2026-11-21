# Photo Upload & Media API Specification

The Media API enables authenticated shoppers to initiate uploads, transmit binaries directly to isolated object storage via presigned URLs, trigger server-side validation and normalization, retrieve image metadata, and obtain short-lived signed access URLs.

All endpoints require standard Bearer token authentication in the `Authorization` header (`Authorization: Bearer <JWT>`).

---

## 1. Initiate Upload Intent
Authorizes an upload session and issues a short-lived (5-minute) pre-signed PUT URL.

- **Route**: `POST /api/v1/media/uploads`
- **Headers**:
  - `Authorization: Bearer <token>`
  - `Content-Type: application/json`

### Request Body
```json
{
  "purpose": "VTO_PERSONAL_PHOTO",
  "filename": "full_body_standing.jpg",
  "content_type": "image/jpeg",
  "declared_size_bytes": 2457600,
  "client_checksum_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
}
```

### Response (201 Created)
```json
{
  "upload_id": "b3f07a51-3965-4f4e-9b93-1383796f6001",
  "image_id": "a91845cb-1123-455b-9bfa-bca9928124ef",
  "upload_url": "https://fashx-media-private.s3.ap-south-1.amazonaws.com/temporary/uploads/prod/00000000-0000-0000-0000-000000000001/b3f07a51-3965-4f4e-9b93-1383796f6001/original?X-Amz-Algorithm=...",
  "method": "PUT",
  "required_headers": {
    "Content-Type": "image/jpeg"
  },
  "expires_in_seconds": 300,
  "status": "PENDING_UPLOAD"
}
```

---

## 2. Poll Upload Intent Status
Inspects the progress or terminal status of an initiated upload.

- **Route**: `GET /api/v1/media/uploads/{upload_id}`
- **Headers**:
  - `Authorization: Bearer <token>`

### Response (200 OK)
```json
{
  "upload_id": "b3f07a51-3965-4f4e-9b93-1383796f6001",
  "image_id": "a91845cb-1123-455b-9bfa-bca9928124ef",
  "status": "AVAILABLE",
  "message": "Your photo has been validated and is available."
}
```

---

## 3. Complete Upload & Validate
Notifies the server that the mobile client has finished uploading bytes to S3 quarantine. Triggers container inspection, bounded decode, metadata stripping, WebP raster generation, and database promotion.

- **Route**: `POST /api/v1/media/uploads/{upload_id}/complete`
- **Headers**:
  - `Authorization: Bearer <token>`
  - `Content-Type: application/json`

### Request Body (Optional)
```json
{
  "client_checksum_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
}
```

### Response (200 OK)
```json
{
  "upload_id": "b3f07a51-3965-4f4e-9b93-1383796f6001",
  "image_id": "a91845cb-1123-455b-9bfa-bca9928124ef",
  "status": "AVAILABLE",
  "message": "Your photo has been validated and is available."
}
```

---

## 4. Retrieve Media Metadata
Retrieves dimensions, verified checksums, and normalized specifications for an active image.

- **Route**: `GET /api/v1/media/{image_id}`
- **Headers**:
  - `Authorization: Bearer <token>`

### Response (200 OK)
```json
{
  "id": "a91845cb-1123-455b-9bfa-bca9928124ef",
  "user_id": "00000000-0000-0000-0000-000000000001",
  "purpose": "VTO_PERSONAL_PHOTO",
  "status": "AVAILABLE",
  "content_type": "image/webp",
  "size_bytes": 482104,
  "width": 1200,
  "height": 1600,
  "sha256_normalized": "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08",
  "created_at": "2026-11-17T07:15:00Z"
}
```

---

## 5. Generate Ephemeral Access URL
Generates an expiring pre-signed GET URL (60-second TTL) for personal photo rendering.

- **Route**: `POST /api/v1/media/{image_id}/access-url`
- **Headers**:
  - `Authorization: Bearer <token>`

### Response (200 OK)
```json
{
  "image_id": "a91845cb-1123-455b-9bfa-bca9928124ef",
  "url": "https://fashx-media-private.s3.ap-south-1.amazonaws.com/users/00000000-0000-0000-0000-000000000001/images/a91845cb-1123-455b-9bfa-bca9928124ef/original.webp?X-Amz-Algorithm=...",
  "expires_in_seconds": 60
}
```

---

## 6. Delete Media
Requests immediate revocation and scheduled deletion of an image asset.

- **Route**: `DELETE /api/v1/media/{image_id}`
- **Headers**:
  - `Authorization: Bearer <token>`

### Response (200 OK)
```json
{
  "image_id": "a91845cb-1123-455b-9bfa-bca9928124ef",
  "status": "DELETION_PENDING"
}
```

---

## 7. Error Responses (RFC 7807 + Envelope)

| HTTP Status | Error Code | Description |
|---|---|---|
| `401 Unauthorized` | `unauthorized` | Missing, expired, or malformed authentication token |
| `404 Not Found` | `media_not_found` | Resource does not exist, belongs to another user, or has been deleted |
| `413 Payload Too Large` | `image_size_exceeded` | Uploaded raw image exceeds the 10 MB maximum limit |
| `413 Payload Too Large` | `media_storage_quota_exceeded` | User has reached the 100 MB aggregate storage quota |
| `415 Unsupported Media Type`| `unsupported_image_format` | Magic bytes do not correspond to JPEG, PNG, or WebP |
| `422 Unprocessable Entity`| `image_dimensions_exceeded`| Image exceeds 4096×4096 px or 20 megapixels |
| `422 Unprocessable Entity`| `image_decode_failed` | Corrupted byte stream or invalid container structure |
| `422 Unprocessable Entity`| `image_content_type_mismatch` | Declared Content-Type does not match container format |
| `422 Unprocessable Entity`| `animated_image_unsupported` | Multi-frame or animated GIF/WebP rejected |
| `429 Too Many Requests` | `upload_rate_limited` | Exceeded 5 upload intents within a 15-minute window |
| `429 Too Many Requests` | `concurrent_uploads_exceeded` | Exceeded 3 simultaneous uncompleted uploads |
