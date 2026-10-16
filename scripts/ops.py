#!/usr/bin/env python3
"""Manage the included single-server Docker deployment."""

import argparse
import os
import subprocess
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env-file", default=".env.production")
    parser.add_argument("--ci", action="store_true", help=argparse.SUPPRESS)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("deploy", help="Build, migrate, collect static files and start services")
    backup = commands.add_parser("backup", help="Write a private PostgreSQL custom-format dump")
    backup.add_argument("--output", help="New backup filename (never overwrite an existing file)")
    restore = commands.add_parser("restore", help="Stop web traffic and restore a PostgreSQL dump")
    restore.add_argument("backup_file")
    restore.add_argument("--confirm-replace-database", action="store_true", required=True)
    commands.add_parser("prune", help="Delete expired API tokens and Django sessions")
    args = parser.parse_args()
    env_file = (ROOT / args.env_file).resolve()
    if not env_file.is_file():
        parser.error("Environment file is missing. Run scripts/production_env.py first.")
    os.environ["HANDYBASE_ENV_FILE"] = str(env_file)
    base = ["docker", "compose", "--env-file", str(env_file), "-f", "compose.yaml"]
    if args.ci:
        base += ["-f", "compose.ci.yaml"]

    def run(*parts, **kwargs):
        return subprocess.run([*base, *parts], cwd=ROOT, check=True, **kwargs)  # noqa: S603

    if args.command == "deploy":
        run("build", "--pull", "web")
        run(
            "run",
            "--rm",
            "--no-deps",
            "proxy",
            "caddy",
            "validate",
            "--config",
            "/etc/caddy/Caddyfile",
            "--adapter",
            "caddyfile",
        )
        run("up", "-d", "--wait", "db", "redis")
        run("run", "--rm", "web", "python", "manage.py", "migrate", "--noinput")
        run("run", "--rm", "web", "python", "manage.py", "collectstatic", "--noinput")
        run(
            "run",
            "--rm",
            "web",
            "python",
            "manage.py",
            "check",
            "--deploy",
            "--fail-level",
            "WARNING",
        )
        run("up", "-d", "--wait", "--wait-timeout", "180")
        print("Deployment started and health checks passed. Create your admin account next.")
    elif args.command == "backup":
        name = args.output or f"backups/handybase-{datetime.now(UTC):%Y%m%dT%H%M%S%fZ}.dump"
        target = (ROOT / name).resolve()
        target.parent.mkdir(parents=True, exist_ok=True)
        try:
            with target.open("xb") as file:
                if os.name != "nt":
                    target.chmod(0o600)
                run(
                    "exec",
                    "-T",
                    "db",
                    "sh",
                    "-c",
                    'exec pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" --format=custom',
                    stdout=file,
                )
        except subprocess.CalledProcessError:
            target.unlink(missing_ok=True)
            raise
        print(f"Backup saved to {target}. Copy it to private off-server storage.")
    elif args.command == "restore":
        source = Path(args.backup_file).resolve()
        if not source.is_file():
            parser.error("Backup file does not exist.")
        with source.open("rb") as file:
            run("exec", "-T", "db", "pg_restore", "--list", stdin=file, stdout=subprocess.DEVNULL)
        run("stop", "proxy", "web")
        # Keep the service stopped on failure so a partial restore cannot serve traffic.
        with source.open("rb") as file:
            run(
                "exec",
                "-T",
                "db",
                "sh",
                "-c",
                'exec pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" '
                "--clean --if-exists --no-owner --exit-on-error --single-transaction",
                stdin=file,
            )
        run("run", "--rm", "web", "python", "manage.py", "migrate", "--noinput")
        run("up", "-d", "--wait", "--wait-timeout", "180")
        print("Database restored and health checks passed.")
    elif args.command == "prune":
        for command in ("prune_tokens", "clearsessions"):
            run("exec", "-T", "web", "python", "manage.py", command)


if __name__ == "__main__":
    main()
