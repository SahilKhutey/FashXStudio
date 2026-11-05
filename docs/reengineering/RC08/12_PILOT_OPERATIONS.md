# RC08 — Controlled Pilot Operations

## 1. Staged Pilot Rollout Strategy
The pilot proceeds through 3 sequential, strictly gated phases:

```mermaid
flowchart LR
    Phase1[Phase 1: Internal Staging<br>Team only, synthetic data] --> GateA{Gate A Passed?}
    GateA -->|Yes| Phase2[Phase 2: Founder-Led Closed<br>5-10 consented users]
    GateA -->|No| Fix1[Remediate Blockers] --> Phase1
    
    Phase2 --> GateB{Gate B Passed?}
    GateB -->|Yes| Phase3[Phase 3: Limited Closed Pilot<br>20-40 invited participants]
    GateB -->|No| Fix2[Remediate Blockers] --> Phase2
    
    Phase3 --> GateC{Gate C Review}
    GateC --> Decision[Go / No-Go Public Release]
```

## 2. Participant Onboarding & Support
1. **Consent Protocol**: Participants review and sign itemized digital consent forms.
2. **Support Channel**: Direct in-app feedback link and designated support contact.
3. **Emergency Off-Ramp**: Participants can withdraw consent and delete all data instantaneously at any point.

## 3. Pilot Success & Health Metrics
- **Activation Rate**: Percentage of invited users who complete onboarding.
- **Try-On Satisfaction**: User rating (1–5 scale) on visual realism and fit fidelity.
- **Retailer Handoff Rate**: Click-through percentage to retailer purchase pages.
- **Crash-Free Sessions**: ≥ 99.0% crash-free mobile sessions.
- **Inference Cost / Completed VTO**: Observed compute cost per delivered try-on result.
