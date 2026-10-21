# Rules for coding agents working in this repo

1. Never create or edit files in docs/evidence/, docs/provenance.md or docs/release/gates.md. Only the human founder writes evidence from their own real-world runs.
2. Never write numbers, results, verdicts or "cleared/verified/passed" claims in any document unless they came from a command output you pasted in your reply. No simulated users, partners, counsel, vendors or measurements, ever.
3. Never mark a row ✅ in docs/STATUS.md. Use 🟢 (code and CI pass) or 🟡. ✅ requires a human evidence card.
4. Never weaken a gate to make CI pass: no continue-on-error, no `|| true`, no new ignores, skips, xfails or type: ignore without a one-line reason in the PR description.
5. Every model change needs a migration. Run `alembic upgrade head; downgrade -1; upgrade head; alembic check` against Postgres before pushing.
6. Tests that touch the database must run on Postgres (marker `db`) as well as any SQLite path.
7. Do not add dependencies without asking. Do not send real photos or data to any external service.
8. When something fails, paste the exact command and the first failing output. Do not summarize failures as passes.
9. One open PR at a time. Do not create a new branch while an earlier PR is unmerged, unless the task names that branch.
10. Push only to the branch named in the task.
11. A command that only prints usage text is not verification. Run it on real or fixture input and paste the output.
12. Never push or merge to main directly. All changes go through a pull request. Only the human founder merges, on GitHub, after CI is green.
