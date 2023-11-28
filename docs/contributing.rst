============
Contributing
============

If you want to contribute to pyastgrep, great! You'll need to:


Get test suite running::

  pip install -r requirements-test.txt
  pytest

Run tests against all versions::

  pip install tox
  tox

Please install `pre-commit <https://pre-commit.com/>`_ in the repo::

  pre-commit install

This will add Git hooks to run linters when committing, which ensures our style
(black) and other things.

You can manually run these linters using::

  pre-commit run --all --all-files

Run mypy (we only expect it to pass on Python 3.10)::

  mypy .

Bug fixes and other changes can be submitted using pull requests on GitHub. For
large changes, it’s worth opening an issue first to discuss the approach.
