# Frozen modules (post-MVP)

Do not extend. Excluded from MVP release gates. Unmounted from the production router in Phase 2 unless explicitly enabled via `FASHX_ENABLE_FROZEN=1`.

| Ref | Domain | Canonical Paths |
|---|---|---|
| C05 | Inventory | backend/fashx/domain/inventory, backend/fashx/repositories/inventory, backend/fashx/api/v1/inventory.py, tests/inventory |
| C06 | Promotions | backend/fashx/domain/promotions, backend/fashx/repositories/promotions, backend/fashx/api/v1/promotions.py, tests/promotions |
| C07 | Cart | backend/fashx/domain/cart, backend/fashx/repositories/cart, backend/fashx/api/v1/cart.py, tests/cart |
| C08 | Checkout/Orders | backend/fashx/domain/checkout, backend/fashx/domain/order, backend/fashx/domain/orders, backend/fashx/repositories/order, backend/fashx/repositories/orders, backend/fashx/api/v1/orders.py, tests/orders, tests/checkout |
| C09 | Payments | backend/fashx/domain/payments, backend/fashx/repositories/payments, backend/fashx/api/v1/payments.py, tests/payments |
| C10 | Fulfilment | backend/fashx/domain/fulfillment, backend/fashx/repositories/fulfillment, backend/fashx/api/v1/fulfillment.py, tests/fulfillment |
| C11 | Returns | backend/fashx/domain/returns, backend/fashx/repositories/returns, backend/fashx/api/v1/returns.py, tests/returns |
| F12-F13 | Regional, engagement | backend/fashx/features/* (regional, engagement) |

---

## Gating Architecture
- **Router Gating:** In `backend/fashx/main.py`, the 8 frozen commerce routers (inventory, promotions, cart, checkout, orders, payments, fulfillment, returns) are gated behind `enable_frozen = settings.enable_frozen or os.getenv("FASHX_ENABLE_FROZEN", "0") == "1"`. By default (`FASHX_ENABLE_FROZEN=0`), these routers are completely unmounted from the OpenAPI schema and FastAPI runtime (reducing endpoints from 233 to 206).
- **Test Suite Partitioning:** Configured `tests/conftest.py` with `pytest_collection_modifyitems` to automatically assign `pytest.mark.frozen` to tests in frozen directories and `test_cross_core.py`.
  - Non-frozen MVP tests: 1,027 tests (`pytest -m "not frozen"`) — required in CI.
  - Frozen tests: 244 tests (`pytest -m "frozen"`) — isolated non-blocking CI job with `FASHX_ENABLE_FROZEN=1`.
  - Total: 1,271 tests.

---

## Dependencies on frozen modules
Audit conducted in Phase 2C confirmed zero MVP domain dependencies on frozen modules:
- No MVP features, services, or domain logic import from `inventory`, `promotions`, `cart`, `checkout`, `order`, `orders`, `payments`, `fulfillment`, or `returns`.
- Monolith kernel wiring in `backend/fashx/core/bootstrap.py` registers in-memory services for tests.
- Un-freeze only if pilot data justifies direct commerce operations (Phase 11 decision).
