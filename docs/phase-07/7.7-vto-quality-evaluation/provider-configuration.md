# Provider Configuration & Version Tracking

## 1. Frozen Snapshot Schema

Every evaluation run must record an immutable snapshot of all system versions to guarantee reproducibility:

```json
{
  "evaluation_run_id": "eval-2026-001",
  "provider": "fashn",
  "model": "tryon-v1.6",
  "model_version": "2026.1",
  "provider_api_version": "v1",
  "configuration_version": "vto-config-12",
  "preprocessing_version": "preprocess-4",
  "policy_version": "vto-policy-3",
  "prompt_version": "prompt-5",
  "git_commit_sha": "9ab31be...",
  "started_at": "2026-11-24T11:00:00Z"
}
```

---

## 2. Unexposed Provider Model Handling

If a commercial provider updates internal weights without bumping their exposed API model name:
- The runner explicitly records `model_version: "NOT_EXPOSED"`.
- If a regression or material output variance is detected, the run is archived and a new `evaluation_run_id` is created.
- Benchmark comparisons between runs conducted months apart must never assume model identity unless cryptographically or contractually guaranteed by the vendor.
