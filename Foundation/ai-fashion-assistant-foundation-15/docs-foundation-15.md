# AI Fashion Assistant — Production Build Foundation 15

## Try-On Result Quality & Delivery

Foundation 15 adds a formal quality gate between provider output and a user-visible try-on artifact.

### Quality pipeline

```text
Provider result
    ↓
Download
    ↓
Byte-size guard
    ↓
Content-type validation
    ↓
Image integrity verification
    ↓
Resolution validation
    ↓
Aspect-ratio validation
    ↓
SHA-256
    ↓
Quality score
    ↓
ACCEPTED → R2 artifact
REJECTED → QUALITY_REJECTED job failure
```

### Stored result metadata

`tryon_artifacts` now stores:

- `quality_status`
- `quality_score`
- width / height
- byte size
- content type
- SHA-256
- quality reasons

### Delivery

`GET /api/v1/tryon/{job_id}` returns a short-lived signed result URL only when the artifact passed the quality gate.

The permanent R2 object key remains server-side.

### Safety boundary

A provider result is never marked `completed` merely because the provider returned HTTP 200. It must pass application-side image validation first.

The quality gate is deliberately deterministic and lightweight. It does not claim semantic judgment of whether the garment transformation itself is visually correct; that is a later VTO evaluation/quality-model layer.
