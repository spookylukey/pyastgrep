pyastgrep
=========

|badge_fury| |badge_tests| |badge_rtd|

.. |badge_fury| image:: https://badge.fury.io/py/pyastgrep.svg
     :target: https://badge.fury.io/py/pyastgrep

.. |badge_tests| image:: https://github.com/spookylukey/pyastgrep/actions/workflows/tests.yml/badge.svg
     :target: https://github.com/spookylukey/pyastgrep/actions/workflows/tests.yml

.. |badge_rtd| image:: https://readthedocs.org/projects/pyastgrep/badge/?version=latest
   :target: https://pyastgrep.readthedocs.org/en/latest/


A command-line utility for grepping Python files using XPath syntax (or CSS
selectors) against the Python AST (Abstract Syntax Tree).

In other words, this allows you to search Python code against specific syntax
elements (function definitions, arguments, assignments, variables etc), instead
of grepping for string matches.

The interface and behaviour is designed to match grep and ripgrep as far as it
makes sense to do so.

See `the documentation <https://pyastgrep.readthedocs.io/>`_ for more
information, or the ``docs`` folder.


History
-------

This project was forked from https://github.com/hchasestevens/astpath by `H.
Chase Stevens <http://www.chasestevens.com>`__. Main changes:

* Added a test suite
* Many bugs fixed
* Significant rewrite of parts of code
* Changes to match grep/ripgrep, including formatting and automatic filtering.
