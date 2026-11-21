# Fashion Image Embedding Evaluation Dataset Specification

## 1. Objectives
The evaluation dataset provides a ground-truth benchmark to validate:
- Visual similarity recall and ranking precision.
- Category boundary preservation (e.g. kurtas vs shirts).
- Exact and near-duplicate detection under crop, rotation, and lighting variations.
- Silhouette and color pattern sensitivity.

---

## 2. Dataset Composition
The benchmark comprises **1,000 fashion product images** across 6 core domains:

| Category Segment | Image Count | Ground Truth Pairs | Focus Characteristics |
| :--- | :--- | :--- | :--- |
| **Western Tops (T-shirts, Shirts)** | 250 | 120 pairs | Crew vs V-neck, solid vs striped |
| **Western Bottoms (Jeans, Trousers)** | 150 | 80 pairs | Fit silhouettes (slim, regular, relaxed) |
| **Dresses & Jumpsuits** | 150 | 75 pairs | Maxi, midi, mini, floral vs solid |
| **Indian Wear (Kurtas, Sarees)** | 250 | 140 pairs | Embroidery, zari borders, ethnic cuts |
| **Footwear (Sneakers, Heels)** | 100 | 50 pairs | High-top vs low-top, heel profiles |
| **Accessories (Bags, Belts)** | 100 | 45 pairs | Tote, clutch, crossbody shapes |

---

## 3. Evaluation Tasks & Ground Truth Annotations
1. **Near-Duplicate Identification**: 100 queries testing identical garments shot under different merchant lighting or crops.
2. **Category Coherence**: Testing that nearest neighbors share top-level taxonomy categories ($k=5$).
3. **Cross-Merchant Product Matching**: Testing matching of identical SKU items sold across separate vendor catalogs.
