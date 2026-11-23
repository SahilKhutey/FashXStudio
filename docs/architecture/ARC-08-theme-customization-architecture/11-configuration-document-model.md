# ARC-08: 11 — Configuration Document Model

## 1. Canonical Configuration Envelope
```json
{
  "configuration_version": "1.0.0",
  "schema_version": "1.0.0",
  "theme": {
    "id": "theme-minimal",
    "version": "1.0.0",
    "overrides": {}
  },
  "layout": {
    "id": "layout-grid",
    "version": "1.0.0",
    "settings": {
      "columns": 2,
      "density": "comfortable"
    },
    "responsive": {}
  },
  "components": [
    {
      "id": "header-instance-1",
      "component_id": "restaurant-header",
      "slot": "header",
      "order": 1,
      "visible": true,
      "props": {
        "show_logo": true,
        "alignment": "center"
      }
    }
  ],
  "metadata": {
    "updated_at": "2026-11-21T10:00:00Z"
  }
}
```
