# ARC-08: 20 — Security and Tenant Isolation

## 1. Security Controls
- **Cross-Tenant Guard**: Organization A cannot read or modify Organization B's customizations.
- **Payload Forgery Protection**: Any tenant ID supplied inside the JSON payload is ignored in favor of the trusted token context.
- **XSS & Injection Prevention**: Token overrides and component properties are validated against strict regexes. Scripts (`<script>`, `javascript:`) are rejected immediately.
- **Platform Authorization**: Only platform administrators may manage themes or components.
