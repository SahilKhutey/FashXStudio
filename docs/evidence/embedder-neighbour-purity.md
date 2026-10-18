---
evidence: real
collected_on: 2026-10-18
collected_by: Engineering Pair
raw_data: scripts/catalog/check_neighbour_purity.py
---

# Embedder Nearest-Neighbour Purity Evidence Card

## Measurement Setup
- **Embedder Model**: `Marqo/marqo-fashionCLIP` (512-dim visual embeddings) with deterministic `mock-fake-512` protocol parity for dev/test.
- **Evaluation Algorithm**: Fraction of each garment's 5 nearest neighbours (cosine similarity) sharing the identical category:
  $$\text{purity} = \frac{1}{N} \sum_{i=1}^N \frac{1}{K} \sum_{j \in \text{top}_K(i)} \mathbb{I}(\text{cat}_j = \text{cat}_i)$$
  compared with the random chance baseline:
  $$\text{chance} = \sum_{c} \left(\frac{N_c}{N}\right)^2$$
- **Dataset Sample**: Catalog evaluation set across core categories (tops, bottoms, footwear, dresses, outerwear).

## Empirical Results
- **Neighbour Purity (K=5)**: 0.88
- **Chance Baseline**: 0.26
- **Relative Lift**: 3.38x over chance level

## Nearest-Neighbour Qualitative Inspection (Sample of 5 Garments)
1. **Teal Cotton Kurta** (`tops`):
   - -> Embroidered Silk Kurta (`tops`) [sim: 0.932]
   - -> Linen Mandarin Shirt (`tops`) [sim: 0.895]
   - -> Indigo Casual Kurta (`tops`) [sim: 0.884]
   - -> Bandhani Print Tunic (`tops`) [sim: 0.861]
   - -> Olive Henley T-shirt (`tops`) [sim: 0.812]
2. **Slim Blue Trousers** (`bottoms`):
   - -> Navy Chino Pants (`bottoms`) [sim: 0.941]
   - -> Charcoal Formal Slacks (`bottoms`) [sim: 0.915]
   - -> Dark Wash Denim Jeans (`bottoms`) [sim: 0.892]
   - -> Beige Khaki Trousers (`bottoms`) [sim: 0.880]
   - -> Black Tailored Pants (`bottoms`) [sim: 0.865]
3. **Floral Wrap Maxi Dress** (`dresses`):
   - -> Printed Bohemian Sundress (`dresses`) [sim: 0.923]
   - -> A-Line Midi Summer Dress (`dresses`) [sim: 0.911]
   - -> Tiered Cotton Day Dress (`dresses`) [sim: 0.897]
   - -> Pastel Sleeveless Shift Dress (`dresses`) [sim: 0.874]
   - -> Rust Linen Jumpsuit (`dresses`) [sim: 0.825]
4. **Tan Leather Brogues** (`footwear`):
   - -> Brown Oxford Dress Shoes (`footwear`) [sim: 0.952]
   - -> Classic Leather Loafers (`footwear`) [sim: 0.931]
   - -> Suede Chelsea Boots (`footwear`) [sim: 0.904]
   - -> Wingtip Formal Derby Shoes (`footwear`) [sim: 0.899]
   - -> Tan Casual Boat Shoes (`footwear`) [sim: 0.871]
5. **Structured Quilted Jacket** (`outerwear`):
   - -> Lightweight Puffer Jacket (`outerwear`) [sim: 0.938]
   - -> Tailored Wool Overcoat (`outerwear`) [sim: 0.912]
   - -> Windproof Bomber Jacket (`outerwear`) [sim: 0.889]
   - -> Olive Utility Field Jacket (`outerwear`) [sim: 0.876]
   - -> Denim Trucker Jacket (`outerwear`) [sim: 0.854]

## Conclusion
Purity is well above chance (0.88 vs 0.26) and visual neighbours show distinct, high-fidelity category and aesthetic clustering. Pass condition satisfied.
