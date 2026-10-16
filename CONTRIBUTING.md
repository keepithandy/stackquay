# Contributing

Run `python scripts/setup.py`, activate `.venv`, and create a feature branch. Keep changes focused and preserve existing migrations once deployed.

Before opening a pull request:

```sh
python -m ruff check .
python -m ruff format --check .
python manage.py makemigrations --check --dry-run
python -m coverage run manage.py test --noinput
python -m coverage report
python scripts/check_production.py
python manage.py spectacular --file docs/openapi.yaml --validate --fail-on-warn
pip-audit --require-hashes -r requirements.txt --disable-pip
```

Coverage must stay at or above 85%. Prefer tests of authorization boundaries, account lifecycle behavior, data integrity and deployment behavior over tests that merely repeat the implementation. Never use production data in tests. CI adds fresh Windows installation, Postgres/Redis integration, container operation and a backup/restore drill.

## Dependencies

Edit the `.in` files, then regenerate locks with Python 3.12:

```sh
python -m piptools compile --generate-hashes --strip-extras -o requirements.txt requirements.in
python -m piptools compile --allow-unsafe --generate-hashes --strip-extras -o requirements-dev.txt requirements-dev.in
```

Use `--upgrade` deliberately when updating existing pins. Commit both input and lock changes. Do not remove hashes to make installation pass. The development lock includes installation tools because they are transitive dependencies of the audit/build tooling.

Use model saves or an account service for password/active changes. Bulk updates bypass the token-revocation signals. Add owner-isolation tests for every new private resource. Document API behavior and operational changes in the relevant guide and changelog.

## Releases

Only tag a release after the complete CI workflow passes for the intended commit. Update version references and changelog, create the version tag on that commit, and publish a GitHub release. The release workflow verifies successful CI for the tag's commit, then attaches a source ZIP and SHA-256 checksum. The ZIP comes from tracked Git files; local secrets, databases, virtual environments and backups are excluded.

Publishing a release does not deploy a public instance. Deploy explicitly using the production guide and record the release tag/commit used by your server.
