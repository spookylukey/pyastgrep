==================
How to do releases
==================

* Make sure you are on master branch, and have pulled latest changes.

* Check test suite passes on all supported versions::

    tox

* Change docs/history.rst to remove " - unreleased"

* Update the version number (removing the ``-dev1`` part):

  * src/pyastgrep/__init__.py
  * docs/conf.py

* Commit with "Version bump"

* Release to PyPI::

    $ ./release.sh


Post release
------------

* Bump version numbers to next version, and add ``-dev1`` suffix, for example
  ``0.9.0-dev1``, in the same places as above.

* Add new section to HISTORY.rst, with " - unreleased".

* Commit and push
