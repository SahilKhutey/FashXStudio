## Summary

<!-- Explain what changed and why. -->

## Related task / issue

- Task:
- Issue:
- Related ADR:

## Change classification

- [ ] Feature
- [ ] Bug fix
- [ ] Refactor
- [ ] Documentation
- [ ] Tests
- [ ] Security
- [ ] Infrastructure / CI
- [ ] Database migration

## Scope

### Included
-

### Explicitly excluded
-

## Implementation details

- Backend:
- Mobile:
- Database:
- API:
- Integrations:
- Feature flags:

## Architecture and compatibility

- [ ] Existing architecture reused where possible.
- [ ] No unintended direct cross-subsystem database access.
- [ ] API compatibility reviewed.
- [ ] Database migration reviewed, if applicable.
- [ ] Feature flags and defaults reviewed, if applicable.
- [ ] No frozen module extended without explicit authorization.

## Testing evidence

| Check | Command / CI job | Result | Evidence |
|---|---|---|---|
| Unit tests | | | |
| Integration tests (Postgres) | | | |
| Mobile tests | | | |
| Lint | | | |
| Type checking | | | |
| Migration upgrade/downgrade | | | |
| Documentation lint | | | |
| Security checks | | | |

- [ ] No relevant tests skipped or weakened.
- [ ] New behaviour has tests.
- [ ] Failure output is recorded accurately.
- [ ] CI is green, or unresolved failures are explicitly explained.

## Security, privacy and data

- [ ] No secrets or credentials committed.
- [ ] No real user photographs or personal data sent to an external service without approval and valid consent.
- [ ] Authentication and ownership checks reviewed.
- [ ] Tenant isolation reviewed, if applicable.
- [ ] Logs do not expose tokens, raw images, body measurements or personal data.
- [ ] Image access, retention and deletion behaviour reviewed.
- [ ] External vendor permissions and data-processing requirements reviewed.

## Documentation

- [ ] README updated if public behaviour or setup changed.
- [ ] docs/STATUS.md updated if implementation status changed.
- [ ] ADR added or updated if an architectural decision changed.
- [ ] API documentation updated if a contract changed.
- [ ] Migration and configuration instructions updated, if applicable.

## Release impact

- [ ] No release gate weakened.
- [ ] No unsupported market, partner, user or performance claims added.
- [ ] Simulated data explicitly labelled.
- [ ] Unverified integrations explicitly labelled.
- [ ] Rollback or recovery procedure documented where needed.

## Deployment / rollback

- Deployment steps:
- Rollback steps:
- Data migration compatibility:
- Feature flag / kill switch:

## Reviewer notes

<!-- Explain anything that requires special reviewer attention. -->

## Author declaration

- [ ] I reviewed the complete diff.
- [ ] I have not claimed a test passed unless its output or CI evidence supports that claim.
- [ ] This PR contains only the intended scope.
