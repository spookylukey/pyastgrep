from pathlib import Path

from pyastgrep.files import get_files_to_search

from tests.utils import chdir

DIR = Path(__file__).resolve().parent / "examples" / "test_symlinks"
REPO_ROOT = Path(__file__).resolve().parent.parent
DIR_FROM_ROOT = DIR.relative_to(REPO_ROOT)


def test_symlinks_ignored_by_default():
    with chdir(DIR):
        assert list(get_files_to_search([Path(".")])) == [Path("non_link.py")]
