# AI Fashion Assistant — Foundation 13

## Purpose
Virtual Try-On Job Infrastructure: async job contract, version-aware artifact identity, idempotency, atomic worker claiming, cancellation, GPU-provider boundary, internal worker APIs, and secure R2 result lifecycle.

## Runtime boundary

```text
Mobile
  ↓
POST /api/v1/tryon
  ↓
TryOnApplicationService
  ├── accepted profile photo
  ├── catalog garment/image
  ├── artifact-key computation
  ├── request idempotency
  └── queue submission
        ↓
     Redis Queue
        ↓
   GPU Worker
        ↓
 Internal Try-On API
        ↓
 Commercial-approved VTO provider (future stage)
        ↓
      R2 result
```

## State machine

`queued → validating → preprocessing → inference → postprocessing → quality_check → completed`

Terminal states: `failed`, `cancelled`.

Only a worker that atomically claims a queued/stale job can execute it.

## Identity rules

Idempotency key answers: **have I already received this client request?**

Artifact key answers: **have I already computed this exact photo + garment + model + pipeline configuration?**

They are deliberately different concepts.

## Provider boundary

The production model/provider is not selected in Foundation 13. The adapter is fail-closed until a commercially approved provider is configured. This prevents research-only checkpoints from silently becoming the production runtime.

## Worker contract

Workers use the internal Try-On API for claim/progress/complete/fail. They do not write Try-On domain tables directly.
