# Phase 07.8 — Visual Try-On and Fit Prediction Separation

> **Development and technical documentation. Contains no real-world measurements or simulated evidence.**

## 1. Objective
The purpose of Phase 07.8 is to establish a strict, non-negotiable architectural separation between:
1. **Visual Try-On (VTO)**: Generates an AI visual simulation showing how a garment might appear on a shopper's photograph.
2. **Fit Prediction**: Estimates whether a physical garment is likely to fit a shopper based on reliable body measurements, merchant garment measurements, size charts, ease rules, and validated category-specific models.

## 2. Core Architectural Rule
**FashXStudio shows a visual representation of a garment on a shopper, but it NEVER describes that image as proof of fit, verified sizing, or an exact fit recommendation.**

A visually convincing generated image does not establish:
- That the garment's actual physical dimensions match the shopper's body.
- That the selected size is correct.
- That the garment will feel comfortable.
- That fabric stretch, drape, or construction will behave as rendered.
- That the real garment will look identical to the synthesized image.

## 3. Scope of Tasks
- **7.8.1**: Label the result as a visual try-on (`VISUAL_TRY_ON`, `is_ai_generated=True`, `fit_verified=False`).
- **7.8.2**: Display product size-chart information separately (merchant-sourced, explicit basis `BODY` vs `GARMENT`).
- **7.8.3**: Display fit recommendations only when supported by verified data (fails closed to `INSUFFICIENT_DATA`).
- **7.8.4**: Avoid guaranteed-fit language across mobile, API, and merchant widgets (`claims.py`).
- **7.8.5**: Provide a way to report misleading results (fixed reason codes, ownership checks, privacy preservation).
- **7.8.6**: Record user-reported issues for model evaluation (reviewer triage, linking confirmed cases to Phase 07.7 evaluation items).

## 4. Key Deliverables
- Presentation Policy Engine: `backend/fashx/presentation/claims.py`
- Size Chart Service & Schemas: `backend/fashx/catalog/size_charts/`
- Fit Recommendation Service: `backend/fashx/fit/`
- Feedback & Review Pipeline: `backend/fashx/tryon/feedback/`
- Database Models & Alembic Migration: `database/migrations/versions/0055_add_vto_fit_separation_and_size_charts.py`
- Mobile UI Components: `VisualTryOnDisclosure.tsx`, `ProductSizeChart.tsx`, `ReportTryOnModal.tsx`
