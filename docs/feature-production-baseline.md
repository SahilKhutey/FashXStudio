# F00 — Feature Production Baseline

F00 freezes the Core-to-Feature boundary. Feature modules live below
`api/app/features/`; they consume versioned schemas and Core ports rather than
accessing database sessions, external services, or another feature's internal
implementation directly.

The canonical feature namespace is `FX-F00` through `FX-F16`. F00 is the
baseline; F01 is the executable Feature Foundation; F02–F16 are registered
contracts, not implementations.

## F00 completion gate

- Feature identity and metadata: `FeatureDefinition`
- Dependency graph and cycle detection: `DependencyResolver`
- Configuration / runtime flags: `FeatureConfigStore` and `FEATURE_FLAGS`
- Lifecycle and UI-compatible state: `FeatureRuntime`
- Lifecycle events: `FeatureEventBus`
- Structured feature errors: `api/app/features/foundation/errors.py`
- Runtime coordination: `FeatureManager`
- Bootstrap catalog: `api/app/features/feature_catalog.py`

F01 is isolated in `api/app/features/foundation/`, has no database or network
dependency, and is validated by `tests/unit/test_feature_foundation.py`.
