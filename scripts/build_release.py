#!/usr/bin/env python3
"""Build the public Squigit release catalog from its Markdown sources."""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent if SCRIPT_DIR.name == "scripts" else SCRIPT_DIR
RELEASES_DIR = ROOT / "releases"
OUTPUT_PATH = ROOT / "releases.json"

CALVER_PATTERN = re.compile(r"^\d{2}\.\d{2}\.\d{2}$")
SEMVER_PATTERN = re.compile(
    r"^(?:0|[1-9]\d*)\."
    r"(?:0|[1-9]\d*)\."
    r"(?:0|[1-9]\d*)"
    r"(?:-(?:0|[1-9]\d*|\d*[A-Za-z-][0-9A-Za-z-]*)"
    r"(?:\.(?:0|[1-9]\d*|\d*[A-Za-z-][0-9A-Za-z-]*))*)?"
    r"(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?$"
)


class BuildError(RuntimeError):
    """Raised when release inputs cannot produce a valid catalog."""


@dataclass(frozen=True, slots=True)
class ProductSource:
    key: str
    filename: str

    @property
    def path(self) -> Path:
        return RELEASES_DIR / self.filename


PRODUCTS = (
    ProductSource("app", "squigit-app.md"),
    ProductSource("cli", "squigit-cli.md"),
    ProductSource("ocr", "squigit-ocr.md"),
)


def git_path_is_dirty(path: Path) -> bool:
    """Return whether Git sees local changes for ``path``.

    A Git failure is treated as dirty so a stale release date is never reused
    when the generator cannot prove that the source is unchanged.
    """

    try:
        relative_path = path.relative_to(ROOT)
        result = subprocess.run(
            (
                "git",
                "status",
                "--porcelain=v1",
                "--untracked-files=all",
                "--",
                str(relative_path),
            ),
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError, ValueError):
        return True
    return bool(result.stdout.strip())


def parse_version(header: str, source: Path) -> tuple[str, str]:
    """Extract and validate the version token from a Markdown H1."""

    if not header.startswith("# "):
        raise BuildError(f"{source}: first line must be a Markdown H1")

    parts = header.split()
    if len(parts) < 3:
        raise BuildError(f"{source}: first line does not contain a version")

    version = parts[-1]
    if CALVER_PATTERN.fullmatch(version):
        try:
            datetime.strptime(version, "%y.%m.%d")
        except ValueError as error:
            raise BuildError(f"{source}: invalid CalVer {version!r}") from error
        return version, "calver"

    if SEMVER_PATTERN.fullmatch(version):
        return version, "semver"

    raise BuildError(f"{source}: unsupported version {version!r}")


def load_existing_catalog() -> dict[str, Any]:
    """Load the previous catalog when it is usable for date preservation."""

    if not OUTPUT_PATH.exists():
        return {}

    try:
        value = json.loads(OUTPUT_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        print(
            f"warning: ignoring unreadable {OUTPUT_PATH.name}: {error}",
            file=sys.stderr,
        )
        return {}

    if not isinstance(value, dict):
        print(
            f"warning: ignoring invalid {OUTPUT_PATH.name}: root must be an object",
            file=sys.stderr,
        )
        return {}
    return value


def preserved_release_date(
    existing_catalog: dict[str, Any],
    product: ProductSource,
    version: str,
    today: str,
) -> str:
    """Keep a trustworthy date only for an unchanged release source."""

    existing = existing_catalog.get(product.key)
    if not isinstance(existing, dict):
        return today
    if existing.get("latest_version") != version:
        return today
    if git_path_is_dirty(product.path):
        return today

    released_at = existing.get("released_at")
    if not isinstance(released_at, str):
        return today
    try:
        date.fromisoformat(released_at)
    except ValueError:
        return today
    return released_at


def build_catalog() -> dict[str, dict[str, Any]]:
    """Read every required source and return a complete release catalog."""

    existing_catalog = load_existing_catalog()
    today = datetime.now(timezone.utc).date().isoformat()
    catalog: dict[str, dict[str, Any]] = {}

    for product in PRODUCTS:
        try:
            content = product.path.read_text(encoding="utf-8")
        except FileNotFoundError as error:
            raise BuildError(f"missing release source: {product.path}") from error
        except OSError as error:
            raise BuildError(f"cannot read {product.path}: {error}") from error

        first_line = content.splitlines()[0] if content else ""
        version, version_type = parse_version(first_line, product.path)
        released_at = preserved_release_date(
            existing_catalog,
            product,
            version,
            today,
        )

        catalog[product.key] = {
            "current_version": None,
            "latest_version": version,
            "version_type": version_type,
            "released_at": released_at,
            "content": content,
        }

    return catalog


def write_catalog(catalog: dict[str, dict[str, Any]]) -> None:
    """Atomically publish deterministic, minified, single-line JSON."""

    payload = (
        json.dumps(
            catalog,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
        )
        + "\n"
    )

    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            prefix=f".{OUTPUT_PATH.name}.",
            suffix=".tmp",
            dir=OUTPUT_PATH.parent,
            delete=False,
        ) as temporary:
            temporary_path = Path(temporary.name)
            temporary.write(payload)
            temporary.flush()
            os.fsync(temporary.fileno())

        if os.name != "nt":
            temporary_path.chmod(0o644)
        os.replace(temporary_path, OUTPUT_PATH)
        if os.name != "nt":
            directory_fd = os.open(OUTPUT_PATH.parent, os.O_RDONLY)
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def main() -> int:
    try:
        catalog = build_catalog()
        write_catalog(catalog)
    except (BuildError, OSError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1

    versions = ", ".join(
        f"{key}={entry['latest_version']}" for key, entry in catalog.items()
    )
    print(f"generated {OUTPUT_PATH.name}: {versions}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
