import os.path

from tests.utils import run_print

DIR = os.path.dirname(__file__) + "/examples/test_errors"


def test_broken_syntax():
    output = run_print(DIR, "./*/*", ["broken.py-broken"])
    assert output.stderr == "Error: broken.py-broken: invalid syntax (broken.py-broken, line 5)\n"


def test_missing_file():
    output = run_print(DIR, "./*/*", ["missing.py"])
    assert output.stderr == "Error: missing.py could not be found\n"
