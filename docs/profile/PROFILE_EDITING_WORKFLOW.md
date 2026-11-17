# Profile Editing Workflow and Optimistic Concurrency Control

## 1. Concurrency Model
To prevent lost updates in multi-device mobile sessions (e.g. tablet and phone concurrently editing preferences), `shopper_profiles` implements integer-based optimistic concurrency control.

```
Device 1 (Phone)                      Backend                    Device 2 (Tablet)
      |                                  |                              |
      |--- GET /profile/me ------------->|                              |
      |<-- returns profile (version=1) --|                              |
      |                                  |<-- GET /profile/me ----------|
      |                                  |--- returns (version=1) ----->|
      |                                  |                              |
      |--- PATCH (expected_version=1) -->|                              |
      |    version increments to 2       |                              |
      |<-- 200 OK (version=2) -----------|                              |
      |                                  |                              |
      |                                  |<-- PATCH (expected_version=1)|
      |                                  |    Version mismatch! (2 != 1)|
      |                                  |--- 409 Conflict ------------>|
      |                                  |    (Must reload version 2)   |
```

## 2. Partial Update Mechanics (PATCH)
- In `PATCH /profile/me`, `exclude_unset=True` ensures that fields omitted by the client are NOT overwritten with `None` or defaults.
- To explicitly clear an optional field (e.g. remove weight), the client must supply `"weight_kg": null`.
