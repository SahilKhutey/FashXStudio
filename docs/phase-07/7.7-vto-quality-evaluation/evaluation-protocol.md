# Reproducible Evaluation Protocol

## 1. Execution Protocol

To ensure benchmark reproducibility and comparability across provider releases:

### Step 1: Dataset Freeze
1. Select target dataset release (e.g. `vto-benchmark-1.0`).
2. Verify all `permission_record_id` entries are currently valid.
3. Lock manifest file.

### Step 2: Configuration Snapshot
1. Generate `EvaluationRunConfig` capturing:
   - Git commit SHA
   - Provider (`fashn`)
   - Model identifier & version
   - Configuration & policy versions
2. Commit run config to `tryon_evaluation_runs`.

### Step 3: Spending Allocation
1. Estimate total billable submissions: $N_{\text{pairs}} \times \text{Unit Cost} \times (1 + \text{Retry Factor})$.
2. Verify available Platform Evaluation Budget.
3. Set `spending_ceiling_usd`.

### Step 4: Batch Execution
1. Dispatch pairs through `TryOnEvaluationRunner.run_benchmark()`.
2. Monitor real-time progress and provider latencies.
3. Automatically quarantine anomalous responses.

### Step 5: Blind Review & Gate Decision
1. Assign anonymized rendered outputs to 3 independent reviewers.
2. Aggregate ratings into `tryon_evaluation_ratings`.
3. Execute `evaluate_category()` for each garment category.
4. Record release decisions in `tryon_evaluation_category_gates`.
