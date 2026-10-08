# FashXStudio Feature Platform

The Core is the stable platform. Product features consume its contracts and
capabilities; they do not recreate identity, consent, catalog, commerce,
observability, or error handling inside a feature module.

## Feature contract

Every production feature has a registry entry (`FX-FEAT-NNN`) containing an
owner domain, lifecycle, dependencies, and the Core capabilities it consumes.
The public read surface is `GET /api/v1/features`,
`GET /api/v1/features/{feature_id}`, and `GET /api/v1/features/runtime`.
Feature metadata includes a semantic version. A feature is available only when
it, all direct dependencies, and runtime configuration are enabled.

## Runtime configuration and lifecycle

`FEATURE_FLAGS` is an optional JSON object mapping a feature ID to `true` or
`false`; it is an environment-level rollout control, not a user permission
system. Example: `FEATURE_FLAGS={"FX-FEAT-003":false}`. Unknown IDs are
ignored, and a disabled feature reports an explicit disabled runtime state.

The standard runtime states are `uninitialized`, `initializing`, `ready`,
`loading`, `empty`, `error`, and `disabled`. Lifecycle events use the stable
names `feature.initialized`, `feature.loaded`, `feature.action`,
`feature.updated`, `feature.failed`, and `feature.completed`.

Route and deep-link ownership is declared by each future mobile feature, while
access enforcement remains an explicit dependency on Core Identity. F01 does
not add a second authentication mechanism or treat a feature flag as security.

Feature events use `schemas.features.v1.FeatureEvent`. Event producers must
provide the feature ID, event type, timestamp, trace ID when one exists, and
only product-safe properties. The contract intentionally has no feature-local
database schema: each later feature chooses persistence through Core ports.

## Module boundary

Backend feature code lives at `api/app/features/<feature-name>/`; shared
platform code remains at `api/app/features/`. Mobile code lives at
`mobile/features/<feature-name>/`. A feature may import versioned `/schemas`
contracts and Core ports, but must not import another feature's implementation.

## Required delivery artifacts

Each registry feature must ship a specification, user story and flow, UI states
(loading/success/empty/error), API contract, accessibility criteria, telemetry,
unit tests, integration tests, and one end-to-end acceptance flow before its
lifecycle moves to `enabled`.
