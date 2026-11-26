# 04 — Manual Measurement Entry Workflow

## 1. Workflow Guarantees

1. Authenticated shopper identity is resolved solely from the server principal (`get_principal`); client-supplied `shopper_id` fields are forbidden (`extra="forbid"`).
2. Writing any measurement requires granted `FIT_PROFILE_STORAGE` consent.
3. Single-field and partial-profile entries are permitted; shoppers never have to complete all measurements at once.
4. Batch requests (`MeasurementBatchRequest`) validate every item before any persistence occurs (all-or-nothing semantics).
5. Every manually entered record preserves `source = MANUAL`, `measurement_subject = BODY`, and `measurement_method` (`SELF_MEASURED`, `ASSISTED_MEASUREMENT`, `OTHER`).
6. VTO image outputs are strictly rejected via `FitProfileService.reject_vto_as_measurement_evidence`.
