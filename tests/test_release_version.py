import re
from pathlib import Path

from ox1nlp import __version__

ROOT = Path(__file__).resolve().parents[1]


def test_release_metadata_matches_package_version():
    pyproject = (ROOT / "pyproject.toml").read_text()
    changelog = (ROOT / "CHANGELOG.md").read_text()
    assert f'version = "{__version__}"' in pyproject.split("[project.urls]", 1)[0].splitlines()
    assert re.search(rf"^## \[{re.escape(__version__)}\] - \d{{4}}-\d{{2}}-\d{{2}}$", changelog, re.MULTILINE)
