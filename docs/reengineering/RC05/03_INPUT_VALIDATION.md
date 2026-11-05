# RC05 — 03 Input Validation

## Objective
Enforce strict multi-stage validation on personal portraits and catalog garments prior to queuing and inference. Ensure that consent, photo ownership, image quality, and garment eligibility are verified.

## Existing State
- Validations were distributed between route handlers and use cases.
- Missing active consent or unaccepted photo statuses required explicit scenario testing to guarantee uniform error responses.

## Changes
- Hardened `SubmitTryOnJobUseCase` (`backend/fashx/tryon/application/submit_job.py`):
  1. **Consent Gate:** Rejects user if `body_photo` consent is missing (`ConsentRequiredError`).
  2. **Photo Ownership & Status:** If `photo_id` provided, verifies ownership by authenticated user. If omitted, resolves active `tryon_reference` photo. Requires `photo.status == "accepted"`.
  3. **Garment Eligibility:** Checks `garment.tryon_supported is True` and category is within `tryon_supported_categories` (`tops`, `bottoms`, `one-pieces`).
  4. **Image Byte Integrity:** Checks input bytes for corruption, empty payloads, or unsupported dimensions in `ProcessTryOnJobUseCase`.

## Contracts
- Missing consent: HTTP 403 / `ConsentRequiredError`
- Photo not owned: HTTP 422 / `ValidationError("Photo not found or not owned by user")`
- Photo not accepted: HTTP 422 / `ValidationError("must be 'accepted' to run try-on")`
- Garment not eligible: HTTP 422 / `ApiError("unsupported_garment")`

## Implementation
```python
# Check active consent
has_consent = await self.profile_uow.consents.has_consent(cmd.user_id, "body_photo")
if not has_consent:
    raise ConsentRequiredError("body_photo")

# Validate photo status
if photo.status != "accepted":
    raise ValidationError(
        f"User portrait photo status is '{photo.status}'; must be 'accepted' to run try-on.",
        field="photo_status",
    )
```

## Execution
```bash
pytest tests/unit/test_rc05_vto_scenarios.py -k "consent or photo or garment" -v
```

## Tests
- `test_rc05_t01_no_consent_rejects_submission` -> PASSED
- `test_rc05_t02_photo_of_another_user_rejects_submission` -> PASSED
- `test_rc05_t03_photo_not_accepted_rejects_submission` -> PASSED
- `test_rc05_t04_ineligible_garment_rejects_submission` -> PASSED

## Risks
- Client supplying expired or deleted photo references.
- Mitigation: Backend resolves latest active accepted photo from database if client does not provide an explicit ID.

## Evidence
- Unit scenarios passed in `test_rc05_vto_scenarios.py`.

## Exit Criteria
- Ineligible inputs are rejected before queueing, protecting infrastructure and budget limits.
