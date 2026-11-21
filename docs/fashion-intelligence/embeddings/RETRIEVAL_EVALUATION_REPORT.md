# Fashion Image Retrieval Evaluation Report

## 1. Evaluation Methodology
Retrieval quality was evaluated against the 1,000-image Fashion Intelligence Benchmark using:
- **Recall@K** ($K \in \{1, 5, 10\}$): Proportion of queries where relevant matching item is within top $K$ results.
- **Mean Reciprocal Rank (MRR)**: Average reciprocal rank of the first relevant result.
- **Category Consistency@5**: Percentage of top-5 returned items sharing the query's taxonomy category.

---

## 2. Benchmark Retrieval Results

| Model Architecture | Recall@1 | Recall@5 | Recall@10 | MRR | Category Consistency@5 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **OpenCLIP ViT-B/32 (Approved Baseline)** | **79.4%** | **91.2%** | **95.6%** | **0.846** | **96.8%** |
| DINOv2 ViT-B/14 (Visual-Only Candidate) | 81.2% | 92.5% | 96.1% | 0.858 | 94.2% |
| ResNet-50 (Legacy Baseline) | 61.3% | 76.8% | 83.4% | 0.682 | 87.5% |

---

## 3. Qualitative Findings
1. **Indian Wear Discrimination**: OpenCLIP reliably separated `kurta` from `western_shirt` without category bleed, and preserved distinct visual features of sarees vs dupattas.
2. **Color and Pattern Fidelity**: Solid colored queries returned matches with >98% color fidelity in top 5; fine houndstooth and floral prints clustered accurately.
3. **Robustness to Background Clutter**: Studio model shots and ghost-mannequin cutouts mapped closely when garments shared identical silhouettes.
