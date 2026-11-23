# ARC-08 — Theme & Customization Architecture
MODULARMENU · SYSTEM ARCHITECTURE SERIES · VERSION 1.0

## Status: Proposed Architecture Baseline

### 1. Document Control
| Attribute | Value |
| :--- | :--- |
| **Document ID** | ARC-08 |
| **Title** | Theme & Customization Architecture |
| **Product** | ModularMenu |
| **Version** | 1.0.0 |
| **Status** | Proposed |
| **Upstream Architecture** | ARC-01 (Vision), ARC-03 (App), ARC-04 (Domain), ARC-05 (Tenant Security), ARC-06 (Persistence), ARC-07 (APIs) |
| **Downstream Architecture**| ARC-09 (Menu Rendering), ARC-10 (Publishing & Versioning) |

---

### 2. Executive Summary
ARC-08 establishes how restaurants customize the visual appearance and structural layout of their digital menus without modifying application source code. It delivers a unified, schema-validated, versioned, portable theme and customization foundation supporting both the Settings Editor and Visual Editor.

### 3. Core Principles
1. **Configuration Over Code**: Customization is declarative data, never executable customer JavaScript or arbitrary HTML.
2. **Schema-Validated Contracts**: Every configuration document is validated against JSON Schema Draft 2020-12.
3. **Deterministic Resolution**: An explicit 8-tier priority hierarchy resolves defaults, presets, and overrides predictably.
4. **Tenant Isolation**: Tenant ownership is enforced by composite relational keys and PostgreSQL RLS.
5. **Dual-Editor Parity**: The Settings Editor and Visual Editor operate on the identical canonical configuration document.
