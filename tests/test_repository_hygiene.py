"""Repository hygiene: the public core must stay client-free and portable."""

from __future__ import annotations

import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

# Binary or opaque formats have no place in a synthetic-only reference.
_BANNED_SUFFIXES = frozenset(
    {".mdb", ".accdb", ".sqlite", ".db", ".parquet", ".sav"}
)

# Case-sensitive whole-word client and deployment markers.
_BANNED_TOKENS = re.compile(r"\b(CCL|GOL|PRW|CHICILON|NIELSEN|MASTER_ROOT)\b")

# Personal mailboxes must never appear in tracked content.
_BANNED_MAILBOXES = re.compile(r"icloud\.com|gmail\.com", re.IGNORECASE)

# Absolute machine paths break portability; /path/to/ placeholders are fine.
# A drive pattern only counts outside URL schemes (https:// must not match).
_MACHINE_PATHS = re.compile(
    r"(?:(?<=\s)|(?<=[\"'])|^)"
    r"(?:[A-Za-z]:[\\/]|\\\\|/home/|/Users/|%APPDATA%|%USERPROFILE%)"
)

# The guard itself names the patterns it hunts; never flag this file.
_SELF = "tests/test_repository_hygiene.py"


def _tracked_text_files() -> list[Path]:
    """Return text files excluding the git directory itself."""
    roots = ("src", "tests", "docs", ".github")
    files: list[Path] = []
    for root in roots:
        files.extend(
            path
            for path in (REPO_ROOT / root).rglob("*")
            if path.is_file()
            and path.suffix != ".pyc"
            and path.relative_to(REPO_ROOT).as_posix() != _SELF
        )
    files.extend(
        path
        for path in REPO_ROOT.iterdir()
        if path.is_file() and path.suffix in {".md", ".toml", ".yml", ".txt"}
    )
    return files


class RepositoryHygieneTests(unittest.TestCase):
    def test_no_dotenv_files(self) -> None:
        """Only the documented .env.example may exist."""
        offenders = [
            str(path.relative_to(REPO_ROOT))
            for path in REPO_ROOT.rglob(".env*")
            if path.is_file()
            and path.name != ".env.example"
            and ".git" not in path.parts
        ]
        self.assertEqual(offenders, [])

    def test_no_binary_or_client_data_files(self) -> None:
        """Synthetic-only reference carries no opaque data formats."""
        offenders = [
            str(path.relative_to(REPO_ROOT))
            for path in REPO_ROOT.rglob("*")
            if path.is_file()
            and ".git" not in path.parts
            and path.suffix.casefold() in _BANNED_SUFFIXES
        ]
        self.assertEqual(offenders, [])

    def test_no_client_or_deployment_markers(self) -> None:
        """Client codes and private deployment roots stay out of content."""
        offenders = [
            f"{path.relative_to(REPO_ROOT)}:{number}"
            for path in _tracked_text_files()
            for number, line in enumerate(
                path.read_text(encoding="utf-8").splitlines(), start=1
            )
            if _BANNED_TOKENS.search(line) or _BANNED_MAILBOXES.search(line)
        ]
        self.assertEqual(offenders, [])

    def test_no_absolute_machine_paths(self) -> None:
        """Content must stay portable across machines."""
        offenders = [
            f"{path.relative_to(REPO_ROOT)}:{number}"
            for path in _tracked_text_files()
            if path.name != ".env.example"
            for number, line in enumerate(
                path.read_text(encoding="utf-8").splitlines(), start=1
            )
            if _MACHINE_PATHS.search(line)
        ]
        self.assertEqual(offenders, [])
