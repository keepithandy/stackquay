# Stackquay — Brand Transition Record

**Decision date:** 2026-10-17  
**Owner preference:** Stackquay is the approved project-facing name replacing HandyBase.  
**Public clearance status:** NOT COMPLETE. Approval by the owner is not a trademark registration or legal clearance.

## Current implementation state

- The *public-facing project identity* in the README, development homepage and installer messages is Stackquay (formerly HandyBase).
- The **actual GitHub repository** remains `keepithandy/handybase`; this document does not claim it has been renamed.
- The actual default branch is `main` (not `master`).
- The latest historically published release is `v1.0.0`, under the HandyBase name.
- Clone commands, CI links, and release artifacts still use the existing GitHub slug.
- Django app labels (`core`), existing migrations, API routes, databases, environment variable names, container/service names, and operational credentials are **unchanged**.

## Clearance checkpoint before a GitHub slug/package release rename

1. Complete official USPTO searching for exact, phonetic and similar marks in related software/IT services. Obtain professional advice if planning commercial adoption.
2. Confirm domain registration availability and possible existing use of `stackquay.com`, `stackquay.dev`, and `stackquay.io`; search alone is not a domain registration check.
3. Verify `stackquay` on PyPI, npm and other intended registries, including confusingly similar package names.
4. Confirm GitHub slug `keepithandy/stackquay` is available immediately before a rename.
5. Record evidence links, findings, risk acceptance and a go/no-go decision.

Preliminary searches did not surface an obvious exact-name GitHub project. **Absence in a search is not proof of legal or namespace availability.**

## GitHub repository rename procedure (separate operation)

When clearance is accepted, rename via **GitHub → Repository Settings → General → Repository name** to `stackquay`. The currently connected GitHub editing tools cannot execute that repository-level administration operation.

After rename, audit internal and external clone URLs, CI badges, documentation links, version badges, deployment automation and any integrations. Verify GitHub redirects rather than assuming every integration updates. Do not rename database tables, Django apps or migration directories merely because the repository slug changes.

## Release history and compatibility

Do not retroactively change the v1.0.0 release. Keep users informed that Stackquay succeeds HandyBase. Defer versioned distribution filenames and infrastructure identifier changes until separately approved P1 release-engineering work.

## Next step

The next engineering step is **P1-00 — read-only baseline & preflight**, as described in [the Phase 01 roadmap](development/phase-01/ROADMAP.md). No P1 implementation work or 1.1 release is implied by this branding update.
