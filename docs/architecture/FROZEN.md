# Frozen modules (post-MVP)

Do not extend. Excluded from MVP release gates. Unmounting from the production router happens in Phase 2.

| Ref | Domain | Paths |
|---|---|---|
| C05 | Inventory | app/domain/inventory, app/repositories/inventory, app/api/v1/inventory.py, tests/inventory |
| C06 | Promotions | app/domain/promotions, app/repositories/promotions, app/api/v1/promotions.py, tests/promotions |
| C07 | Cart | app/domain/cart, app/repositories/cart, app/api/v1/cart.py, tests/cart |
| C08 | Checkout/Orders | app/domain/checkout, app/domain/order, app/domain/orders, app/repositories/order, app/repositories/orders, app/api/v1/orders.py, tests/orders, tests/checkout |
| C09 | Payments | app/domain/payments, app/repositories/payments, app/api/v1/payments.py, tests/payments |
| C10 | Fulfilment | app/domain/fulfillment, app/repositories/fulfillment, app/api/v1/fulfillment.py, tests/fulfillment |
| C11 | Returns | app/domain/returns, app/repositories/returns, app/api/v1/returns.py, tests/returns |
| F12-F13 | Regional, engagement | api/app/features/* (regional, engagement) |

Un-freeze only if pilot data justifies it (Phase 11 decision).
