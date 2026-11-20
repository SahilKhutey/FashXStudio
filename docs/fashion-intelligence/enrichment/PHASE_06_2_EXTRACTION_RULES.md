# Phase 06.2 — Deterministic Extraction Rules

## 1. Title Extraction Order

To prevent regex collision and resolve lexical ambiguities, extraction executes in strict sequential order:

1. **Garment Type**: `t_shirt`, `polo_shirt`, `casual_shirt`, `formal_shirt`, `kurta`, `kurti`, `jeans`, `trousers`, `dress`, `sneakers`, `handbag`.
2. **Intended Audience**: `men`, `women`, `boys`, `girls`, `unisex`.
3. **Fit Type**: `oversized`, `slim`, `regular`, `relaxed`, `loose`, `skinny`, `wide_leg`.
4. **Color**: Controlled shades mapping to primary color families (e.g. `navy` -> `blue`, `bottle_green` -> `green`, `rani_pink` -> `pink`).
5. **Pattern**: `graphic`, `printed`, `striped`, `checked`, `floral`, `bandhani`, `block_print`, `chikankari`, `solid`.
6. **Fabric / Blend**:
   - `cotton_blend` -> assigned to `fabric_blend`, `fabric` marked `UNKNOWN`.
   - `cotton`, `linen`, `denim`, `silk`, `polyester`, `wool`.
7. **Sleeve Type**: `sleeveless`, `short_sleeve`, `long_sleeve`, `three_quarter_sleeve`.
8. **Neckline / Collar**: `round_neck`, `v_neck`, `polo_collar`, `mandarin_collar`, `button_down`.
9. **Occasion**: `casual`, `formal`, `festive`, `party`, `sports`, `everyday`.

## 2. Category Mapping Rules

- Merchant categories are resolved to leaf nodes in the Phase 06.1 taxonomy.
- Exact alias lookup matches strings like `"Men's Clothing / T-shirts"` to `apparel_tops_t_shirts`.
- Unresolved categories are never defaulted to generic tops or shirts; they are quarantined (`CATEGORY_AMBIGUOUS`) and routed to the review queue.
