pyastgrep
=========


.. image:: https://badge.fury.io/py/pyastgrep.svg
     :target: https://badge.fury.io/py/pyastgrep

.. image:: https://github.com/spookylukey/pyastgrep/actions/workflows/tests.yml/badge.svg
     :target: https://github.com/spookylukey/pyastgrep/actions/workflows/tests.yml

A command-line utility for grepping Python files using XPath syntax against the Python AST.

The interface and behaviour is designed to match grep and ripgrep as far as it makes sense to do so.

Status: usable, with test suite, but still cleaning things up and `implementing
some options <https://github.com/spookylukey/pyastgrep/issues>`_

No PyPI package yet.


Example usage
-------------

To get started, dump out the XML structure of top-level statements in a Python file:

.. code:: bash

   $ pyastgrep --xml './*/*' path/to/file.py --xml
   src/pyastgrep/search.py:5:1:import os
   <Import lineno="1" col_offset="0">
     <names>
       <alias lineno="1" col_offset="7" type="str" name="os"/>
     </names>
   </Import>
   ...

This should help in writing XPath expressions.

Note that the XML format is a very direct translation of the Python AST as
produced by the ast module. This AST is not stable across Python versions,
so the XML is not stable either.

Finding all usages of a function called ``open``:

.. code:: bash

   $ pyastgrep ".//Call/func/Name[@id='open']"
   src/pyastgrep/search.py:88:18:            with open(path) as f:

Finding all numbers (Python 3.8+)

.. code:: bash

   $ pyastgrep './/Constant[@type="int" or @type="float"]'
   tests/examples/test_xml/everything.py:5:20:    assigned_int = 123
   tests/examples/test_xml/everything.py:6:22:    assigned_float = 3.14

Integers that are not assigned to a variable:

.. code:: bash

Names longer than 22 characters:

.. code:: bash

   $ pyastgrep './/Name[string-length(@id) > 22]'
   src/pyastgrep/search.py:91:23:            xml_ast = file_contents_to_xml_ast(

Find ``except`` clauses that raise a different exception class than they catch:

.. code:: bash

   $ pyastgrep "//ExceptHandler[body//Raise/exc//Name and not(contains(body//Raise/exc//Name/@id, type/Name/@id))]"

Classes matching a regular expression:

.. code:: bash

   $ pyastgrep ".//ClassDef[re:match('M.*', @name)]"
   src/pyastgrep/search.py:18:1:class Match:

Tips
----

To get pyastgrep to print absolute paths in results, pass the current absolute
path as the directory to search::

  pyastgrep "..." $(pwd)

Installation
------------

Python 3.7+ required.

Using pip:

::

   pip install pyastgrep

If you only want the command line tool and not the library, we recommend `pipx
<https://pipxproject.github.io/pipx/>`_ to install it more conveniently in an
isolated environment:

::

   pipx install pyastgrep


Contributing
------------

Get test suite running::

  pip install -r requirements-test.txt
  pytest

Run against all versions::

  pip install tox
  tox


Install

Links
-----

- `Green tree snakes <https://greentreesnakes.readthedocs.io/en/latest/>`__ - a very readable overview of Python ASTs.
- `ast module documentation <https://docs.python.org/3/library/ast.html>`__.
- `Python AST Explorer <https://python-ast-explorer.com/>`__ for worked  examples of ASTs.
-  A `brief guide to XPath <http://www.w3schools.com/xml/xpath_syntax.asp>`__.

History
-------

This project was forked from https://github.com/hchasestevens/astpath by `H.
Chase Stevens <http://www.chasestevens.com>`__. Main changes:
* Many bugs fixed
* Significant rewrite of parts of code
* Changes to match grep/ripgrep
