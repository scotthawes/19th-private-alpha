"""Shared helpers for the 19th alpha scripts.

Deliberately small and dependency-light: everything here is either stdlib or
already needed to talk to the API.
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
import pathlib
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
RUNS_DIR = REPO_ROOT / "runs"
DATA_DIR = REPO_ROOT / "data"

TRAINING_ORIGIN = os.environ.get("TRAINING_ORIGIN", "https://training.19th.com")
INFERENCE_ORIGIN = os.environ.get("INFERENCE_ORIGIN", "https://inference.get19th.com")

# States where the API is still working. Everything else is terminal.
PENDING_STATES = {"preparing", "training", "packaging", "cancelling"}
TERMINAL_STATES = {"ready", "failed", "cancelled"}


def load_env(path: pathlib.Path | None = None) -> None:
    """Load KEY=VALUE pairs from .env without pulling in a dependency."""
    path = path or REPO_ROOT / ".env"
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip("'\""))


def die(message: str, payload: object | None = None) -> None:
    print(f"error: {message}", file=sys.stderr)
    if payload is not None:
        print(json.dumps(payload, indent=2, ensure_ascii=False), file=sys.stderr)
    raise SystemExit(1)


def note(message: str = "") -> None:
    print(message, flush=True)


def require_env(name: str, hint: str = "") -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        die(f"{name} is not set. {hint}".strip())
    return value


def sha256_of(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_table(path: pathlib.Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        return list(reader.fieldnames or []), rows


def coerce(value: object) -> object:
    """Turn a CSV cell into the scalar type the API expects.

    The API matches declared label types exactly, so '1' and 1 are different
    values. Empty cells and common null spellings become None.
    """
    if value is None:
        return None
    if isinstance(value, (int, float, bool)):
        return value
    text = str(value).strip()
    if text == "" or text.lower() in {"na", "nan", "null", "none"}:
        return None
    try:
        return int(text)
    except ValueError:
        pass
    try:
        return float(text)
    except ValueError:
        return text


def check_api_error(response, context: str) -> None:
    """Print the API's error envelope instead of a bare status code."""
    try:
        payload = response.json()
    except ValueError:
        die(f"{context} failed ({response.status_code}): {response.text[:400]}")
        return
    message = payload.get("message") or payload.get("error") or payload
    die(f"{context} failed ({response.status_code})", message)


def point_latest(run_dir: pathlib.Path) -> None:
    """Make runs/latest resolve to the newest run."""
    latest = RUNS_DIR / "latest"
    try:
        if latest.is_symlink() or latest.exists():
            latest.unlink()
        latest.symlink_to(run_dir.name)
    except OSError:
        # Cosmetic only — never fail a run over this.
        pass
