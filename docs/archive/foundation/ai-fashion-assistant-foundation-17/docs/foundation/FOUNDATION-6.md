# Foundation 6 — Pose & Capture Intelligence

Adds structured capture-quality scoring to the profile-photo pipeline. The worker now produces pose/framing/landmark-confidence signals and a `ready_for_tryon` decision. The production pose boundary is an adapter: `opencv_heuristic` is the local-safe fallback; MediaPipe Pose Landmarker is an explicit provider that fails closed when its runtime/model asset is not installed.

## Pipeline

Upload → basic media validation → pose estimator → quality scorer → accepted/rejected → persisted metadata.

## Important boundary

The heuristic provider is not a substitute for landmark-level pose accuracy. It is a conservative pre-flight gate. A production deployment that requires landmark-grade validation should set `POSE_PROVIDER=mediapipe` and supply `POSE_MODEL_PATH`. MediaPipe 1.0.1 is available for Python 3.12 builds as of August 2026. citeturn143121search0
