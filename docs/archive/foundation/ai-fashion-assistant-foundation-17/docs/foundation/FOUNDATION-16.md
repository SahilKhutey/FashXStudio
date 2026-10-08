# Foundation 16 — Complete Try-On Experience

## Scope

Foundation 16 connects the mobile Try-On experience to the existing asynchronous Try-On runtime.

## Delivered

- Try-On mobile API client.
- TanStack Query mutation/status/cancel hooks.
- Adaptive polling until terminal state.
- Product → Try-On navigation.
- Try-On progress, cancellation, retry, failure and success states.
- Accepted result rendering from the short-lived signed URL returned by the API.
- Save-to-wardrobe action after generation.
- Buy continuation back to the selected product/offer.
- Contract tests for the mobile-consumed Try-On response shape.

## Security rules

- The mobile client never supplies `user_id` to Try-On.
- The backend derives identity from the authenticated request.
- Result URLs are temporary signed URLs; permanent object keys are never exposed.
- Try-On jobs remain asynchronous.
- TanStack Query owns server state; Zustand remains local UI state.

## UX state machine

`idle → starting → queued → processing → completed`

Failure branches:

`starting → failed`
`processing → failed`
`processing → cancelled`

A retry starts a new idempotent client request and does not directly manipulate server job state.

## Validation boundary

The mobile UI displays technical result-quality metadata but does not claim that the generated image proves physical garment fit. Physical fit prediction remains a future fit-intelligence capability.
