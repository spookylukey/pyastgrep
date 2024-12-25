============
Contributing
============

If you want to contribute to pyastgrep, great! You'll need to:

- Check out the repo using git, ``cd`` into the directory.

- Set up a venv for development. We use `uv <https://docs.astral.sh/uv/>`_ and
  recommend you do the same. With uv, the setup instructions are::

    uv sync

  This will use your default Python version. If you want to use a different
  Python version, instead of the above do this e.g.::

    uv python install 3.10
    uv venv --python 3.10
    uv sync

- Activate the venv::

    source .venv/bin/activate

  (Alternatively, you can add ``uv run`` before most of the commands below)

- Get test suite running::

    pytest

- Run tests against all versions::

    tox

- Please install `pre-commit <https://pre-commit.com/>`_ in the repo::

    pre-commit install

  This will add Git hooks to run linters when committing, which ensures our style
  (black) and other things.

  You can manually run these linters using::

    pre-commit run --all --all-files

- Optionally, run pyright::

    pyright .

  We only expect it to pass on Python 3.11, which you can check by doing::

    tox -e pyright


Bug fixes and other changes can be submitted using pull requests on GitHub. For
large changes, it’s worth opening an issue first to discuss the approach.
