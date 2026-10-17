# Stackquay — Project Identity and Deployment Compatibility

**Project identity:** Stackquay (approved internally)  
**GitHub repository:** [keepithandy/stackquay](https://github.com/keepithandy/stackquay)  
**Default branch:** `main`  
**Release history:** Existing `v1.0.0` Git tag and published assets remain intact  
**Name availability:** Commercial trademark, domain and package registry clearance is NOT COMPLETE

## Verified repository state

The GitHub repository has already been renamed to `keepithandy/stackquay`. Use this actual URL for clone commands, workflows, documentation and release links.

The current source adopts the Stackquay identity across the website, account emails, API documentation, configuration defaults, developer guides and packaging. Historic commit messages, releases and archived distribution files are not rewritten.

## Critical notice: existing Docker Compose deployments

For **new** deployments, the Compose project identifier defaults to `stackquay`. Compose uses its project name to form named-volume identities, including those used by PostgreSQL and Caddy. A change in project name can make data appear missing when Docker starts fresh empty volumes. Changing a Docker Compose project name **does not migrate existing data**.

If this server has already been deployed using an earlier version:

1. **Before running any new deploy command**, preserve and verify a complete off-server backup, including PostgreSQL, the deployment env file and certificate state as appropriate.
2. Find the previous Compose project name from the running deployment or existing Docker volume labels.
3. Add `STACKQUAY_PROJECT_NAME=<previous-project-name>` to the existing `.env.production` before invoking any bundled deploy/restore helper or direct `docker compose` command.
4. Preserve the current `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `DATABASE_URL`, `REDIS_PASSWORD`, Redis URL, secrets and host configuration. Do not regenerate or replace a deployed env file.
5. Verify that `docker compose --env-file .env.production -f compose.yaml config` shows the **intended existing** project name and named volumes before bringing up containers.
6. Deploy only after verifying a restoration plan. Perform any actual move to new volumes or DB/user names as a separately authorized migration with a restore drill.

Existing DB names, database users and passwords do **not** have to match the new branding. The deployment generator now uses Stackquay values **only for newly generated environments**.

The supplied `scripts/ops.py` and Compose file now use the `STACKQUAY_ENV_FILE` helper-variable interface. Invoke the helper rather than depending on retired environment-variable overrides.

## Protected interfaces

- Django app labels and `core/migrations/` remain unchanged.
- Existing `/api/v1/`, `/admin/`, and `/health/` routes remain unchanged.
- Existing `.env` and `.env.production` values are not overwritten by changes to source templates.
- Git history and published release assets remain intact.

## Name clearance

Before a commercial product launch, complete official exact/similar trademark searches and verify domains and relevant package registry identifiers. GitHub ownership does not establish trademark clearance.

## Next stage

Begin [Phase 01 preflight](development/phase-01/ROADMAP.md) under the defined read-only authorization gate. This identity cleanup is **not** permission to publish v1.1.0.
