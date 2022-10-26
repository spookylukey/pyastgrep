from pathlib import Path

from pyastgrep.files import get_files_to_search
from pyastgrep.ignores import find_gitignore_files
from tests.utils import chdir

DIR = Path(__file__).resolve().parent / "examples" / "test_ignores"
REPO_ROOT = Path(__file__).resolve().parent.parent
DIR_FROM_ROOT = DIR.relative_to(REPO_ROOT)


def test_find_gitignore_files():
    with chdir(DIR):
        ignore_files = find_gitignore_files(Path("."), recurse_up=True)
        rel_ignore_files = [p.relative_to(REPO_ROOT) for p in ignore_files]
        assert rel_ignore_files == [
            Path("tests/examples/test_ignores/.gitignore"),
            Path(".gitignore"),
        ]


def test_default_ignores():
    FOUND = ["__init__.py", "not_ignored.py", "subdir/not_ignored.py"]

    IGNORED = [
        # `.custom_hidden` should be ignored by default
        ".custom_hidden/__init__.py",
        ".custom_hidden/should_be_ignored.py",
        "subdir/.custom_hidden/__init__.py",
        # node_modules is in this repo's .gitignore
        "node_modules/__init__.py",
        "node_modules/should_be_ignored.py",
        "node_modules/subdir/should_be_ignored.py",
        # custom_gitignored is in this subdir's .gitignore
        "custom_gitignored/__init__.py",
        "custom_gitignored/should_be_ignored2.py",
        "custom_gitignored/subdir/should_be_ignored2.py",
    ]

    with chdir(DIR):
        files = list(get_files_to_search(["."]))

    for p in FOUND:
        assert Path(p) in files

    for p in IGNORED:
        # Sanity check:
        assert (DIR / Path(p)).exists()
        # Test:
        assert Path(p) not in files

    # We should get the same results if we start the search higher up.
    # This is important for testing whether we are discovering .gitignore
    # files as we walk sub directories

    with chdir(REPO_ROOT):
        files2 = list(get_files_to_search(["."]))

    for p in FOUND:
        assert (DIR_FROM_ROOT / Path(p)) in files2

    for p in IGNORED:
        # Sanity check:
        assert (DIR / Path(p)).exists()
        # Test:
        assert (DIR_FROM_ROOT / Path(p)) not in files2


def test_override_on_cli():
    """
    Directories specified on command line should always be searched.
    """
    with chdir(DIR):
        files = list(get_files_to_search(["node_modules"]))

    for p in ["node_modules/subdir/should_be_ignored.py", "node_modules/should_be_ignored.py"]:
        assert Path(p) in files
