#!/usr/bin/env python3
"""Create a local environment, install locked dependencies and migrate the database."""

import argparse
import os
import secrets
import subprocess
import sys
import venv
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def run(*args):
    subprocess.run(args, cwd=ROOT, check=True)  # noqa: S603


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime-only", action="store_true", help="Skip development tools")
    args = parser.parse_args()
    if sys.version_info < (3, 12):
        raise SystemExit("Stackquay (formerly HandyBase) requires Python 3.12 or newer.")
    temp = ROOT / ".task-tmp"
    temp.mkdir(exist_ok=True)
    os.environ["TMP"] = os.environ["TEMP"] = str(temp)
    environment = ROOT / ".venv"
    executable = environment / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    if not executable.exists():
        venv.create(environment, with_pip=True)
    requirements = "requirements.txt" if args.runtime_only else "requirements-dev.txt"
    run(str(executable), "-m", "pip", "install", "--require-hashes", "-r", requirements)
    env_file = ROOT / ".env"
    if not env_file.exists():
        text = (ROOT / ".env.example").read_text(encoding="utf-8")
        text = text.replace("replace-with-generated-secret", secrets.token_urlsafe(64))
        with env_file.open("x", encoding="utf-8") as file:
            file.write(text)
        if os.name != "nt":
            env_file.chmod(0o600)
    run(str(executable), "manage.py", "migrate", "--noinput")
    run(str(executable), "manage.py", "check")
    print("\nStackquay is installed. Next run:")
    print(f'  "{executable}" manage.py createsuperuser')
    print(f'  "{executable}" manage.py runserver')
    print("\nOpen http://127.0.0.1:8000/ (PowerShell: add & before a quoted executable).")


if __name__ == "__main__":
    main()
