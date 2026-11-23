# Phase 06.2 — Security and Data Protection Policies

## 1. Mandatory Data Integrity Gates

### A. Size Information Protection
Under no circumstances may an AI model or heuristic generate:
- Available sizes (`available_sizes`)
- Size charts (`size_chart`)
- Garment measurements (`garment_measurements`)
- Body measurements (`body_measurements`)

If no size information exists in the source feed, the attribute is assigned status `NOT_PROVIDED` with a `null` value.

### B. Fabric Composition Protection
An AI model is strictly prohibited from inferring:
- Fiber composition percentages (e.g. 80% Cotton, 20% Polyester)
- Fabric weight or weave construction
- Organic or sustainability certifications

Phrases like "Cotton Blend" extract `fabric_blend = "cotton_blend"`, while `fabric` remains `UNKNOWN`. Product photographs alone can never be used to establish fiber composition.

## 2. Prompt Injection Resilience

Merchant titles and descriptions frequently contain adversarial prompts (e.g. `"Men's T-Shirt; DROP TABLE; IGNORE INSTRUCTIONS"`). The enrichment pipeline:
- Quotes and delimits all untrusted strings.
- Parses output strictly via Pydantic V2 schemas with `extra="forbid"`.
- Treats injected instructions as literal tokens for pattern matching, never executing model-suggested system actions.
