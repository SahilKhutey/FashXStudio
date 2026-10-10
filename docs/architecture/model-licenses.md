# Model and Vendor License Register

A model reaches production only if its row says YES with evidence. Update this file in the PR that adds or changes a model.

| Option | Type | License / terms | Evidence | Commercial OK | Decision |
|---|---|---|---|---|---|
| FASHN API (tryon-v1.6 / Max) | hosted | Vendor ToS + DPA | FASHN Terms of Service & DPA (August 2026) | YES | Candidate A (Pilot Default) |
| Google Vertex virtual-try-on-001 | hosted | Google Cloud terms | Vertex AI ToS + Lifecycle page | YES (Verify deprecation) | Candidate B (Challenger) |
| FASHN VTON v1.5 weights+code | self-host | Apache-2.0 (repo), HF weights page | Apache-2.0 License in GitHub repo | YES | Candidate C (Spike only) |
| fashn-human-parser | self-host dep | Separate license | Repo LICENSE check required | Verify | Blocks Candidate C until cleared |
| IDM-VTON, CatVTON, OOTDiffusion, StableVITON, VITON-HD, HR-VITON | open | CC non-commercial | Model cards & licenses | NO | Rejected (Rule I08) |

## Enforcement
Production builds enforce these license requirements automatically at application startup in `backend/fashx/ml/licenses.py`.
Any adapter whose `license_id` is not in `ALLOWED_LICENSE_IDS = {"commercial-api", "apache-2.0", "mit"}` causes an immediate fatal startup error (`RuntimeError`).
Mock adapters (`license_id = "mock"`) and research-only models are blocked from production by rule I08 and gate G5.
