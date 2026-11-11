# Contributing

- Work on a branch (`feat/…`, `fix/…`, `chore/…`); open a PR to `main`. No direct pushes to `main`.
- Commit style: `type(scope): summary`, using feat, fix, chore, docs, test, refactor.
- One logical change per commit, especially for code moves (move first, edit later).
- Every PR: tests green locally, `ruff check .`, `mypy .`, and `docs/STATUS.md` updated if a status changed.
- Do not extend frozen modules (docs/architecture/FROZEN.md).
- Never commit secrets, `.env`, archives (`*.zip`) or model weights.

## Engineering standards

All contributors must follow the engineering standards in
`docs/engineering/ENGINEERING_STANDARDS.md`.

Before creating a pull request:

1. Use an approved branch prefix.
2. Use the commit message convention.
3. Add or update relevant tests.
4. Run the applicable lint and type-check commands.
5. Run PostgreSQL integration tests when database behaviour changes.
6. Add or update database migrations when schemas change.
7. Update API documentation when contracts change.
8. Review security, authorization and personal-data handling.
9. Update implementation status documentation when status changes.
10. Complete the pull request template.

Never push directly to `main`.

Never commit secrets, `.env` files, personal photographs, customer data
or model weights.

Do not add dependencies without approval.

See `docs/engineering/` for detailed standards.
