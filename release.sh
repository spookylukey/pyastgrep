#!/bin/sh

# Tests to ensure we don't really break something:
pre-commit run --all --all-files || exit 1
pytest || exit 1


umask 000
rm -rf build dist
git ls-tree --full-tree --name-only -r HEAD | xargs chmod ugo+r
python setup.py sdist || exit 1
python setup.py bdist_wheel || exit 1

NAME=$(python setup.py --name) || exit
VERSION=$(python setup.py --version) || exit 1
twine upload dist/$NAME-$VERSION-py3-none-any.whl dist/$NAME-$VERSION.tar.gz || exit 1
git tag $VERSION || exit 1
git push || exit 1
git push --tags || exit 1
