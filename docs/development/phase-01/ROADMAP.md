# Stackquay — Phase 01: Release Foundation

> **Status:** PLANNED; P1 implementation NOT authorized by the roadmap.
> **Identity:** Stackquay is the owner-approved project name; external trademark/domain/package registry clearance remains pending.
> **Repository:** `keepithandy/stackquay` (actual GitHub rename completed; default branch `main`).
> **Current release:** historical v1.0.0 tag. **Target:** technical foundations for v1.1.0; no release authorized.
> **Created:** 2026-10-17.

## 0. Objective and non-goals

Establish a reproducible release process and explicit supported-runtime contract **without changing application behavior**. This is the first bounded engineering phase, following the evidence-first, milestone-gated process used for Plex Nano.

**In scope:** immutable baseline audit; release-tag/ZIP naming correction; Python 3.12 runtime acceptance policy; automated tests and reproducible reports; review and authorization gates.

**Out of scope:** additional repository administration; publishing a v1.1.0 release; commercial deployment; authentication changes; database migrations; API/schema changes; frontend product; CLI generation; background jobs; billing; organization support; unexplained dependency upgrades. The Stackquay branding decision does **not** authorize these changes.

## 1. Frozen starting state

| Field | Observed baseline |
| --- | --- |
| Repository | `keepithandy/stackquay` |
| Default branch | `main` |
| Last published release | `v1.0.0` (original published assets preserved) |
| Audited starting commit, prior to branding PR | `f730c6947615038fff8c0de74b97942b5d5e4e3a` |
| Runtime tested by CI | Python 3.12 |
| Backend stack | Django 5.2 LTS / DRF |
| Storage | SQLite development, PostgreSQL production; Redis production |
| Deployment | Single-server Docker Compose, Caddy, Gunicorn |

**Important:** P1-00 must re-fetch `main` after this identity cleanup merges and explicitly freeze the **new** engineering baseline. The earlier commit remains historical evidence, not the current HEAD. The historical commit above remains immutable comparison evidence.

Read the following files before making P1 implementation changes: `.github/workflows/ci.yml`, `.github/workflows/release.yml`, `scripts/setup.py`, `scripts/check_production.py`, `pyproject.toml`, `requirements*.txt`, `core/tests.py`, `README.md`, `CHANGELOG.md`, `docs/INSTALL.md`.

Record actual SHA-256 of reviewed files and link CI runs. Never fabricate hashes, test counts or outcomes.

## 2. Development contract (Plex-style)

1. **One bounded milestone at a time.** Diagnostics are read-only. Implementation needs explicit authorization.
2. **Frozen evidence.** Record baseline commit, file hashes, environment, commands, outcomes, CI URLs and changed files.
3. **No silent branch switches.** If upstream changes, report drift and request or record explicit re-baselining.
4. **No fabricated passes.** A command not executed is `NOT RUN`, not `PASS`. Failures remain in the evidence log.
5. **No API or persistence drift.** Protect existing `/api/v1/`, `/admin/`, `/health/`, token behavior and cross-user record isolation. No migration edits.
6. **No extras.** No opportunistic refactor, dependency bump, naming changes in Django app labels, or feature work.
7. **Reviewable PRs.** Work on a feature branch. Never write directly to `main`.
8. **No self-authorization.** The P1 phase roadmap itself authorizes no implementation, merging, release tagging, or deployment.
9. **Compatibility first.** Keep 1.0 tag/assets, secrets, existing local environments and production restore expectations intact.
10. **Documentation follows results.** Mark `PLANNED`, `IMPLEMENTED`, `VERIFIED` and `RELEASED` separately.

## 3. Milestones and authorization gates

| ID | Work | Deliverable | Exit requirement | State |
| --- | --- | --- | --- | --- |
| **P1-00** | Read-only baseline, risk and scope preflight | `P1-00-PREFLIGHT.md` | Verified current HEAD, checksums, precise defects, approved minimal design | NOT STARTED |
| **P1-01** | Version-safe release workflow | Tests and release workflow change | Tagged commit verified, strict `vMAJOR.MINOR.PATCH`, correct ZIP/prefix/SHA256; no release issued | BLOCKED |
| **P1-02** | Explicit Python runtime support | Installer and targeted tests | Python 3.12 accepted; other versions rejected safely before touching local state | BLOCKED |
| **P1-03** | Regression & deployment validation | `P1-03-VERIFICATION.md` | Lint, tests, coverage, schema, Postgres/Redis, Windows install, container and backup/restore evidence | BLOCKED |
| **P1-04** | PR review and closeout | Reviewed PR + `P1-CLOSEOUT.md` | Owner-approved merge; post-merge checks; recorded merge SHA | BLOCKED |

### P1-00: Preflight (read-only)

Inspect current branch/HEAD, tags, workflow, installer, docs and CI. Collect:

- `git status --short`, `git branch --show-current`, `git rev-parse HEAD`, `git tag --list`, `python --version`.
- SHA-256 of workflow, installer, lockfiles and relevant documentation.
- Exactly what `release.yml` hardcodes and what archive output/tag checks are required.
- Whether installer accepts unsupported newer versions versus documented CI runtime.
- Required/optional CI gates, threat model and regression boundaries.

Produce a concise `P1-00-PREFLIGHT.md`: baseline, findings with severity, proposed edits, risk, test plan, unknowns, authorization request. **Stop** before code changes.

### P1-01: Release contract

Original defect: the earlier release workflow hardcoded a single archive version. The identity update introduces tag-derived Stackquay filenames, but the release path has not been independently exercised.

During P1-01, review and test the new tag-derived artifact names (`stackquay-<version>.zip`). Verify stable-tag checks, exact tagged commit selection, passing CI for that commit, matching ZIP prefix and SHA256SUMS, and safe non-overwriting behavior. Until then, this fix is implemented but NOT VERIFIED for publication.

Test correct result for `v1.1.0`, malformed/missing tags, mismatched SHA/CI, and archived content. Never publish to test this step; keep historical `v1.0.0` assets unchanged.

### P1-02: Runtime compatibility

Current `scripts/setup.py` accepts `sys.version_info >= (3, 12)`, while CI/docs standardize on Python 3.12. The target policy is **Python 3.12.x only for 1.1** (subject to authorized review), not an assertion that later interpreters are inherently incompatible.

Require early version checking before creating `.venv`, editing `.env`, or migrating databases. Test acceptance of 3.12 and safe refusal of 3.11/3.13 with a helpful message. Update docs to match the actual contract. Keep existing user-generated secrets and data untouched.

### P1-03: Reproducible verification

Required verification includes:

- `ruff check .` and `ruff format --check .`
- `manage.py makemigrations --check --dry-run`
- Django test suite and coverage threshold >= 85%
- `scripts/check_production.py`
- Regenerated OpenAPI schema matches committed schema
- Dependency audit
- Fresh Windows setup; Postgres/Redis integration; container lifecycle; database backup/restore and post-restore checks in CI
- Specific tests for release tag handling and runtime rejection

Use the interpreter inside the project environment. Each result must include command, exit code, system, commit SHA, date and CI link where applicable. If a required platform is unavailable, record `NOT RUN` and leave the gate open.

### P1-04: Review and closeout

Prepare a scoped PR titled `P1: Deterministic release and runtime contract` against `main`. The change list should ordinarily be limited to release workflow, installer, tests and relevant docs. Do not touch `core/models.py`, `core/migrations/`, `core/authentication.py`, or API routes without a scope-change approval.

Report exact changed files, baseline/final SHAs, tests, failed/retried results, risks, and rollback instructions. **Merge only when separately authorized; recheck CI on `main` after merge.** Do not tag or publish 1.1 without separate approval.

## 4. Risk register

| Risk | Mitigation |
| --- | --- |
| Inaccurate version in archive | Strict tag parsing; tests against ZIP name and top-level folder |
| Incorrect successful CI considered | Validate exact target commit and expected workflow |
| Local installer damages data | Early interpreter check; test no writes on rejection; preserve `.env` |
| Branding breaks persistence | Keep `core` labels, migrations, API, DB and Docker deployment identities stable |
| Existing release assets overwritten | Never modify `v1.0.0`; no publication during P1 |
| Incomplete validation | Log `PASS/FAIL/NOT RUN` plus CI evidence |
| GitHub repository address and links diverge | Check actual clone URL, badges and release links against the current repo |

## 5. Planned evidence directory

```text
docs/development/phase-01/
  ROADMAP.md
  P1-00-PREFLIGHT.md             (write only when performed)
  P1-03-VERIFICATION.md         (write only when performed)
  P1-CLOSEOUT.md                (write only when performed)
```

Never create empty evidence files or claim completion from planning alone.

## 6. First authorized action when ready

**Authorize P1-00 (read-only):** inspect current Stackquay `main`, freeze exact HEAD and hashes, review release/archive and Python-runtime discrepancies, produce the preflight report, and stop. No code edits, PR merge, repository rename, release, or follow-on milestone execution.

## 7. Status and brand relationship

Stackquay is approved by the owner as the project identity. **External trademark, domain and package availability checks are incomplete.** See [Brand transition](../../BRAND_TRANSITION.md). Engineering milestones remain valid even if the final publishable name changes.

**Roadmap status: PLANNED. The name alignment does not authorize P1 engineering implementation.**
