# RC12: Release Policy and Feature Governance

## 1. Capability Registry
Defined in [`backend/fashx/core/release_policy.py`](file:///c:/Users/ASUS/Documents/FashXStudio/backend/fashx/core/release_policy.py):

| Capability Name | Default State | Allowed Envs | Real Provider Req | Description |
| :--- | :--- | :--- | :--- | :--- |
| `catalog_discovery` | Enabled (100%) | Local, Test, Staging, Prod | No | Product browsing and recommendations |
| `vto_mock_preview` | Enabled (100%) | Local, Test, Staging | No | Local/staging simulated try-on preview |
| `vto_real` | Disabled (0%) | Staging, Prod | **Yes** | Live AI vendor generation |
| `public_registration`| Disabled (0%) | Production | No | Open user registration |
| `affiliate_redirect` | Enabled (100%) | Staging, Prod | No | Partner handoff link generation |

## 2. Server-Side Capability Evaluation
```python
from fashx.core.release_policy import evaluate_capability

decision = evaluate_capability(policy, "vto_real", user_id="user-123")
if not decision.allowed:
    # Reject request or route to fallback
    logger.info("Capability blocked", extra={"reason": decision.reason})
```

## 3. Rollout Bucketing Algorithm
Deterministic hashing ensures a user remains in the exact same cohort across sessions:
$$\text{bucket} = \text{int}(\text{SHA256}(\text{salt} : \text{capability} : \text{user\_id})) \pmod{100}$$
- If $\text{bucket} < \text{rollout\_percent}$, capability is authorized.
- Salt is stored server-side and never exposed over client APIs.
