# ARC-08: 10 — Component Slots and Contracts

## 1. Slot Hierarchy
Components may only be mounted into designated slots within the layout hierarchy:
- `menu.root`: Top-level container.
- `header`: Above the primary menu content.
- `navigation`: Category switching and filtering area.
- `content`: Main body containing categories and items.
- `category.header`: Header banner for an individual category.
- `category.items`: Container for dishes within a category.
- `footer`: Bottom informational area.

## 2. Slot Validation
Attempting to mount a component into an unsupported slot (e.g. mounting `restaurant-header` inside `category.items`) is rejected server-side with an `InvalidSlotPlacementError`.
