"""Bump the release version in pyproject.toml, ox1nlp/__init__.py and CHANGELOG.md.

Usage: python3 scripts/release_version.py [patch|minor|major|X.Y.Z]   (or `make release-version`)
The CHANGELOG [Unreleased] notes become the new version's section; when it is empty, the
notes come from the conventional commit subjects since the last version's tag.
Pushing the bumped version to main publishes it to PyPI (.github/workflows/publish.yml).
"""

from __future__ import annotations

import datetime
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
_VERSION = re.compile(r"\d+\.\d+\.\d+")


def next_version(current: str, bump: str) -> str:
    if _VERSION.fullmatch(bump):
        new = bump
    else:
        major, minor, patch = map(int, current.split("."))
        steps = {"major": f"{major + 1}.0.0", "minor": f"{major}.{minor + 1}.0", "patch": f"{major}.{minor}.{patch + 1}"}
        if bump not in steps:
            raise SystemExit(f"unknown bump {bump!r}: use patch, minor, major or X.Y.Z")
        new = steps[bump]
    if tuple(map(int, new.split("."))) <= tuple(map(int, current.split("."))):
        raise SystemExit(f"{new} is not above the current {current}")
    return new


_SECTIONS = {"feat": "Added", "fix": "Fixed", "perf": "Fixed"}
_CONVENTIONAL = re.compile(r"^(\w+)(?:\([^)]*\))?!?:\s*(.+)$")


def notes_from_commits(subjects: list[str]) -> str:
    """Group conventional commit subjects into Keep a Changelog sections (Added, Fixed, Changed)."""
    grouped: dict[str, list[str]] = {}
    for subject in subjects:
        if subject.startswith("chore(release)"):
            continue
        match = _CONVENTIONAL.match(subject)
        kind, text = (match.group(1), match.group(2)) if match else ("", subject)
        grouped.setdefault(_SECTIONS.get(kind, "Changed"), []).append(text[:1].upper() + text[1:])
    return "\n\n".join(
        f"### {section}\n" + "\n".join(f"- {line}" for line in grouped[section])
        for section in ("Added", "Fixed", "Changed")
        if section in grouped
    )


def commit_subjects_since(root: Path, tag: str) -> list[str]:
    def log() -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", "log", f"{tag}..HEAD", "--format=%s"], cwd=root, capture_output=True, text=True, check=False
        )

    result = log()
    if result.returncode != 0:  # tags come from the GitHub release; fetch them once
        subprocess.run(["git", "fetch", "--quiet", "--tags"], cwd=root, check=False)
        result = log()
    if result.returncode != 0:
        raise SystemExit(f"no tag {tag}: write the notes under [Unreleased] in CHANGELOG.md")
    return [line for line in result.stdout.splitlines() if line.strip()]


def release(root: Path, bump: str, today: datetime.date) -> tuple[str, str]:
    pyproject = root / "pyproject.toml"
    init = root / "ox1nlp" / "__init__.py"
    changelog = root / "CHANGELOG.md"

    text = pyproject.read_text()
    match = re.search(r'^version = "([^"]+)"', text, re.MULTILINE)
    if match is None:
        raise SystemExit("no version in pyproject.toml")
    current = match.group(1)
    new = next_version(current, bump)

    head, marker, rest = changelog.read_text().partition("## [Unreleased]\n")
    if not marker:
        raise SystemExit("CHANGELOG.md has no '## [Unreleased]' heading")
    notes, older_marker, older = rest.partition("\n## [")
    if not notes.strip():
        notes = notes_from_commits(commit_subjects_since(root, f"v{current}"))
    if not notes.strip():
        raise SystemExit(f"nothing to release: no commits since v{current} and [Unreleased] is empty")

    pyproject.write_text(text.replace(match.group(0), f'version = "{new}"', 1))
    init.write_text(re.sub(r'^__version__ = "[^"]+"', f'__version__ = "{new}"', init.read_text(), count=1, flags=re.MULTILINE))
    changelog.write_text(
        f"{head}{marker}\n## [{new}] - {today.isoformat()}\n\n{notes.strip()}\n{older_marker}{older}"
    )
    return current, new


if __name__ == "__main__":
    old, new = release(ROOT, sys.argv[1] if len(sys.argv) > 1 else "patch", datetime.date.today())
    print(f"0x1-nlp {old} -> {new}. Review the diff, commit, push to main: CI publishes {new} to PyPI.")
