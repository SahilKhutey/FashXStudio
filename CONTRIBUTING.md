# Contributing

- Work on a branch (`feat/…`, `fix/…`, `chore/…`); open a PR to `main`. No direct pushes to `main`.
- Commit style: `type(scope): summary`, using feat, fix, chore, docs, test, refactor.
- One logical change per commit, especially for code moves (move first, edit later).
- Every PR: tests green locally, `ruff check .`, `mypy .`, and `docs/STATUS.md` updated if a status changed.
- Do not extend frozen modules (docs/architecture/FROZEN.md).
- Never commit secrets, `.env`, archives (`*.zip`) or model weights.
