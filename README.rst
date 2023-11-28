pyastgrep
=========


.. image:: https://badge.fury.io/py/pyastgrep.svg
     :target: https://badge.fury.io/py/pyastgrep

.. image:: https://github.com/spookylukey/pyastgrep/actions/workflows/tests.yml/badge.svg
     :target: https://github.com/spookylukey/pyastgrep/actions/workflows/tests.yml

A command-line utility for grepping Python files using XPath syntax (or CSS
selectors) against the Python AST (Abstract Syntax Tree).

In other words, this allows you to search Python code against specific syntax
elements (function definitions, arguments, assignments, variables etc), instead
of grepping for string matches.

The interface and behaviour is designed to match grep and ripgrep as far as it
makes sense to do so.

Documentation: in the process of migration to readthedocs, see docs/ for now.


History
-------

This project was forked from https://github.com/hchasestevens/astpath by `H.
Chase Stevens <http://www.chasestevens.com>`__. Main changes:

* Added a test suite
* Many bugs fixed
* Significant rewrite of parts of code
* Changes to match grep/ripgrep, including formatting and automatic filtering.
