# RC05 — 10 Wardrobe and Feedback Integration

## Objective
Enable users to persist successfully completed try-on looks into their digital closet (wardrobe) and collect structured feedback regarding visual accuracy, purchase confidence, and specific distortion issue tags.

## Existing State
- Wardrobe router: `backend/fashx/commerce_wardrobe/router.py`
- Feedback use case: `SubmitTryOnFeedbackUseCase` (`backend/fashx/commerce_wardrobe/application/tryon_feedback.py`)
- Mobile hook: `useSaveToWardrobe` and `useTryOnFeedback`

## Changes
- Verified wardrobe saving contract: `POST /api/v1/wardrobe/items` accepting `garment_id` and optional `tryon_artifact_id`.
- Verified feedback submission contract: `POST /api/v1/feedback/tryon` accepting `tryon_job_id`, `visual_accuracy` (`very_inaccurate` to `very_accurate`), `purchase_confidence` (integer `[1, 5]`), and `issue_tags` (list of strings).
- Prevented duplicate wardrobe entries for identical garment IDs.
- Ensured feedback records are attributed to the owning user and linked to the try-on job for analytics.

## Contracts
- Save to Wardrobe Request:
  ```json
  {
    "garment_id": "1d658eed-469b-4963-955d-9aad18eba2d9",
    "tryon_artifact_id": "a76427a7-8a89-41f8-9740-394cecd6c2dc"
  }
  ```
- Feedback Request:
  ```json
  {
    "tryon_job_id": "01dc22b0-ffdb-4e5c-a874-9b7547984b49",
    "visual_accuracy": "accurate",
    "purchase_confidence": 5,
    "issue_tags": []
  }
  ```

## Implementation
```python
# backend/fashx/commerce_wardrobe/router.py
@router.post("/feedback/tryon", response_model=TryOnFeedbackResponse, status_code=status.HTTP_201_CREATED)
async def submit_tryon_feedback(
    request: TryOnFeedbackRequest,
    principal: Principal = Depends(get_principal),
    uow: CommerceWardrobeUnitOfWork = Depends(get_commerce_uow),
) -> TryOnFeedbackResponse:
    ...
```

## Execution
```bash
pytest tests/unit/test_vto_phase9_feedback.py -v
npm --prefix mobile test -- tryon_feedback.test.ts
```

## Tests
- `test_vto_phase9_feedback.py` -> 8 passed
- `tryon_feedback.test.ts` -> 7 passed
- Smoke test Steps 7 & 8 -> Both executed and verified (201 Created)

## Risks
- Client submitting un-bounded integers for purchase confidence.
- Mitigation: Validated with Pydantic `Field(ge=1, le=5)`.

## Evidence
- Smoke test:
  - `Look saved to wardrobe: item_id=a76427a7-8a89-41f8-9740-394cecd6c2dc (HTTP 201 Created)`
  - `Feedback submitted successfully (HTTP 201 Created)`

## Exit Criteria
- Complete post-try-on consumer loop (wardrobe saving and feedback) verified.
