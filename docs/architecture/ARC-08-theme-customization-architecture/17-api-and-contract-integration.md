# ARC-08: 17 — API Architecture & Contracts

## 1. REST Endpoints
Base URL: `/api/v1`
- `GET /themes`: List available themes.
- `GET /themes/{theme_id}`: Retrieve theme definition.
- `GET /themes/{theme_id}/versions/{version}`: Retrieve exact version.
- `GET /layouts`: List supported layouts.
- `GET /layouts/{layout_id}`: Retrieve layout definition.
- `GET /components`: List registered components.
- `GET /components/{component_id}`: Retrieve component definition.
- `GET /menus/{menu_id}/customization`: Retrieve current draft with ETag.
- `PUT /menus/{menu_id}/customization`: Save validated draft (`If-Match` revision concurrency).
- `POST /menus/{menu_id}/customization/validate`: Validate without saving.
- `POST /menus/{menu_id}/customization/preview`: Generate preview tokens and layout.
- `POST /menus/{menu_id}/customization/reset`: Reset overrides to defaults.
- `GET /menus/{menu_id}/customization/revisions`: View draft revision history.
- `POST /menus/{menu_id}/customization/revisions/{revision}/restore`: Restore earlier revision.
