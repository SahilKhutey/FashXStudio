# 02 — Measurement Requirements Policy

## 1. Category-Aware Requirement Levels

FashXStudio does not gate registration or browsing behind full-body measurement forms. Requirement evaluation is governed by `backend/fashx/profile/fit_policy.py` (`FIT_POLICY_VERSION = "1.0"`).

| Category | Required Candidate Fields | Optional Fields | Rationale |
|---|---|---|---|
| `TSHIRTS` | `CHEST` | `SHOULDER`, `SLEEVE_LENGTH`, `HEIGHT` | Upper-body chest circumference anchors T-shirt sizing |
| `SHIRTS` | `CHEST` | `NECK`, `SHOULDER`, `SLEEVE_LENGTH`, `HEIGHT` | Chest anchors sizing; collar/neck and sleeve refine fit |
| `KURTAS` | `CHEST` | `SHOULDER`, `SLEEVE_LENGTH`, `WAIST`, `HEIGHT` | Chest anchors drape; waist/height provide context |
| `TOPS` | `BUST` | `WAIST`, `SHOULDER`, `SLEEVE_LENGTH` | Bust drives upper-torso sizing |
| `TROUSERS` | `WAIST`, `HIP` | `INSEAM`, `OUTSEAM`, `THIGH`, `HEIGHT` | Waist and hip anchor waistband and seat |
| `JEANS` | `WAIST`, `HIP` | `INSEAM`, `THIGH`, `HEIGHT` | Waist and hip govern denim rise and seat |
| `DRESSES` | `BUST`, `WAIST`, `HIP` | `HEIGHT`, `SHOULDER` | Three-point upper-to-lower silhouette bounds |
| `SKIRTS` | `WAIST`, `HIP` | `HEIGHT` | Waistband and hip ease |

## 2. Unsupported Categories

Unsupported categories return `UNSUPPORTED_CATEGORY` via `evaluate_category_readiness` and raise `UnsupportedCategoryPolicyError` from `get_category_policy`. Requirements are never inherited silently across categories.
