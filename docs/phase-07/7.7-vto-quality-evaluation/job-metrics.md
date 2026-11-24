# Job Execution, Success & Latency Metrics

## 1. Operational Formulas

### 1.1 Job Success Rate
$$\text{Job Success Rate} = \frac{\text{Count of Completed Eligible Jobs}}{\text{Count of Accepted Eligible Jobs}} \times 100$$

*Note*: Rejections at the input-validation gate (e.g. invalid file format, blurred face) are **not** counted as provider failures. They represent correct pre-inference gate behavior.

### 1.2 Input Rejection Accuracy
$$\text{Input Rejection Accuracy} = \frac{\text{Correctly Rejected Negative Inputs}}{\text{All Submitted Negative Inputs}} \times 100$$

Measures whether the system reliably catches unprocessable or out-of-scope images before they reach the paid inference provider.

---

## 2. Latency Metrics

1. **Inference Duration (`inference_duration_ms`)**:
   $$\Delta t_{\text{inference}} = t_{\text{provider completed}} - t_{\text{provider submitted}}$$
   Measures pure vendor computation time.
2. **End-to-End Duration (`end_to_end_duration_ms`)**:
   $$\Delta t_{\text{e2e}} = t_{\text{result durable}} - t_{\text{job accepted}}$$
   Includes queue delays, image download, output validation, watermarking, and storage persistence.
3. **Percentiles**: The evaluation runner records exact P50, P90, and P95 latency percentiles.
