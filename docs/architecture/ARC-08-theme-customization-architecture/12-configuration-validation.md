# ARC-08: 12 — Configuration Validation

## 1. Validation Pipeline
Validation is performed in four consecutive stages:
1. **Size & Depth Safeguards**: Rejects payloads exceeding 512 KB or nesting deeper than 8 levels.
2. **JSON Schema Draft 2020-12 Structural Validation**: Validates top-level envelope, required fields, and rejects unknown properties.
3. **Semantic Policy Checks**:
   - Theme and layout existence and mutual compatibility.
   - Design token format and font allowlists.
   - Component registry existence, retirement checks, and slot placement.
   - Duplicate component ID detection.
   - Malicious script scanning (`<script>`, `javascript:`).
4. **Error Formatting**: Generates RFC 9457-compliant Problem Details with exact property paths.
