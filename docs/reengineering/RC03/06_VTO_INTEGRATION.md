# RC-03 — Virtual Try-On Integration

## Orchestration Overview
The Virtual Try-On (VTO) subsystem provides virtual dressing room previews for try-on eligible garments.

```mermaid
sequenceDiagram
    participant Mobile as Mobile App
    participant API as FastAPI Gateway
    participant Orchestrator as TryOnOrchestrator
    participant Provider as VTO Provider (Mock / Production)
    participant Storage as Object Storage

    Mobile->>API: POST /api/v1/tryon/jobs {garment_id, photo_id?}
    API->>Orchestrator: CreateTryOnJobCommand
    Orchestrator->>Storage: Resolve user photo & garment image
    Orchestrator->>Provider: Generate Try-On (Mock renders "PREVIEW ONLY")
    Provider-->>Orchestrator: Rendered artifact bytes
    Orchestrator->>Storage: Store generated artifact
    Orchestrator-->>API: TryOnJob {status: "completed", result_image_url}
    API-->>Mobile: 201 Created
```

## Integration Verification
- **API Contracts**: Mobile hook `useTryOn.ts` supports query caching via `queryKeys.tryOnJob(userId, jobId)` and `queryKeys.tryOnJobs(userId, limit)`.
- **Photo Resolution**: Backend automatically resolves the user's active accepted photo if `photo_id` is omitted in the request.
- **Watermarking**: Mock provider consistently burns the `"PREVIEW ONLY"` diagonal watermark onto all synthetic renders to prevent misleading photorealistic representations.
