# Atomic Budget Reservations & Two-Phase Settlement

## 1. Problem Statement: The Distributed Budget Race

In an asynchronous worker architecture where dozens of Celery workers process try-on requests simultaneously:
- If Budget check happens *after* API calls, 50 workers could each check `$10` remaining, each make a `$0.075` inference call, and collectively blow past the limit before anyone writes back.
- If Budget is debited *before* API calls without reservation, worker crashes or invalid inputs would result in "lost money" accounting bugs.

**Solution**: Two-phase atomic budget reservation.

---

## 2. Two-Phase Protocol

```
Worker                             PostgreSQL DB                          FASHN API
  |                                      |                                    |
  |--- Phase 1: reserve_budget() ------->|                                    |
  |    (SELECT FOR UPDATE)               | (Atomically checks available       |
  |                                      |  and increments reserved_spend)    |
  |<-- ReservationResult(ID) ------------|                                    |
  |                                                                           |
  |--- Dispatch Paid Inference ---------------------------------------------->|
  |<-- Provider Response (Result / Cost) -------------------------------------|
  |                                                                           |
  |--- Phase 2: commit_reservation() --->|                                    |
  |    (actual_cost)                     | (Debits reserved_spend,            |
  |                                      |  credits current_spend)            |
  |<-- Success --------------------------|                                    |
```

### 2.1 Handling Ambiguous Provider Submissions (`SUBMISSION_UNKNOWN`)
If an external API call times out or returns a network error after submission:
- The system **cannot assume** the call failed for free. FASHN may have received the request and debited credits.
- The reservation is **NOT** released immediately.
- `TryOnBudgetService.hold_reservation_for_reconciliation(reservation_id)` sets the reservation status to `HELD_FOR_RECONCILIATION`.
- Only when the stuck-job sweeper or status reconciliation verifies that no inference occurred is the reservation released.

---

## 3. Reservation Lifespan & Timeout Sweeping

Reservations include an `expires_at` timestamp (default: 15 minutes).
If a worker crashes hard (OOM, node termination):
- The sweeper discovers stale reservations where `status = 'RESERVED'` and `now > expires_at`.
- Releases the reserved amount back to the budget pool.
- Logs a dead-letter event for investigation.
