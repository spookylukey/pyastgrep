pyastgrep
=========


.. image:: https://badge.fury.io/py/pyastgrep.svg
     :target: https://badge.fury.io/py/pyastgrep

.. image:: https://github.com/spookylukey/pyastgrep/actions/workflows/tests.yml/badge.svg
     :target: https://github.com/spookylukey/pyastgrep/actions/workflows/tests.yml

A command-line utility for grepping Python files using XPath syntax against the
Python AST (Abstract Syntax Tree).

In other words, this allows you to search Python code against specific syntax
elements (function definitions, arguments, assignments, variables etc), instead
of grepping for string matches.

The interface and behaviour is designed to match grep and ripgrep as far as it
makes sense to do so.


Installation
------------

Python 3.7+ required.

We recommend `pipx <https://pipxproject.github.io/pipx/>`_ to install it
conveniently in an isolated environment:

::

   pipx install pyastgrep


You can also use pip:

::

   pip install pyastgrep

Understanding the XML structure
-------------------------------

To get started, you’ll need some understanding of how Python AST is structured,
and how that is mapped to XML. Some methods for doing that are below:

1. Use `Python AST Explorer <https://python-ast-explorer.com/>`_ to play around
   with what AST looks like.

2. Dump out the AST and/or XML structure of the top-level statements in a Python file. The
   top-level XML elements are ``<Module><body>``, and don’t correspond to actual
   source lines. To get the statements within the body, you can use an XPath
   expression ``/Module/body/*`` or ``./*/*``:

  .. code:: bash

     $ pyastgrep --xml --ast './*/*' myfile.py
     myfile.py:1:1:import os
     Import(
         lineno=1,
         col_offset=0,
         end_lineno=1,
         end_col_offset=9,
         names=[alias(lineno=1, col_offset=7, end_lineno=1, end_col_offset=9, name='os', asname=None)],
     )
     ...
     <Import lineno="1" col_offset="0">
       <names>
         <alias lineno="1" col_offset="7" type="str" name="os"/>
       </names>
     </Import>
     ...


Note that the XML format is a very direct translation of the Python AST as
produced by the `ast module <https://docs.python.org/3/library/ast.html>`_ (with
some small additions made to improve usability for a few cases). This AST is not
stable across Python versions, so the XML is not stable either. Normally changes
in the AST correspond to new syntax that is added to Python, but in some cases a
new Python version will make significant changes made to the AST generated for
the same code.

You can also pipe specific Python fragments using ``-`` to specify stdin as the
input file:

.. code:: bash

   $ echo 'a + b' | pyastgrep --xml './*/*' -
   <stdin>:1:1:a + b
   <Expr lineno="1" col_offset="0">
     <value>
       <BinOp lineno="1" col_offset="0">
         <left>
           <Name lineno="1" col_offset="0" type="str" id="a">
             <ctx>
               <Load/>
             </ctx>
           </Name>
         </left>
         <op>
           <Add/>
         </op>
     ...

You’ll also need some understanding of how to write XPath expressions (see links
at the bottom), but the examples below should get you started.

Examples
--------

Find all usages of a function called ``open``:

.. code:: bash

   $ pyastgrep ".//Call/func/Name[@id='open']"
   src/pyastgrep/search.py:88:18:            with open(path) as f:

Find all literal numbers (Python 3.8+):

.. code:: bash

   $ pyastgrep './/Constant[@type="int" or @type="float"]'
   tests/examples/test_xml/everything.py:5:20:    assigned_int = 123
   tests/examples/test_xml/everything.py:6:22:    assigned_float = 3.14

Names longer than 42 characters:

.. code:: bash

   $ pyastgrep './/Name[string-length(@id) > 42]'

``except`` clauses that raise a different exception class than they catch:

.. code:: bash

   $ pyastgrep "//ExceptHandler[body//Raise/exc//Name and not(contains(body//Raise/exc//Name/@id, type/Name/@id))]"

Functions whose name contain a certain substring:

.. code:: bash

   $ pyastgrep './/FunctionDef[contains(@name, "something")]'

Classes whose name matches a regular expression:

.. code:: bash

   $ pyastgrep ".//ClassDef[re:match('M.*', @name)]"


This uses the Python `re.match
<https://docs.python.org/3/library/re.html#re.match>`_ method. You can also use
``re:search`` to use the Python `re.search
<https://docs.python.org/3/library/re.html#re.search>`_ method.

Docstrings of functions/methods whose value contains “hello”:

.. code:: bash

   $ pyastgrep './/FunctionDef/body/Expr[1]/value/Constant[@type="str"][contains(@value, "hello")]'

For-loop variables called ``i`` or ``j`` (including those created by tuple unpacking):

.. code:: bash

   $ pyastgrep './/For/target//Name[@id="i" or @id="j"]'

Ignoring files
--------------

Files/directories matching ``.gitignore`` entries (global and local) are
automatically ignored, unless specified as paths on the command line.

Currently there are no other methods to add or remove this ignoring logic.
Please open a ticket if you want this feature. Most likely we should try to make
it work like `ripgrep filtering
<https://github.com/BurntSushi/ripgrep/blob/master/GUIDE.md#manual-filtering-globs>`_
if that makes sense.

Tips
----

To get pyastgrep to print absolute paths in results, pass the current absolute
path as the directory to search::

  pyastgrep "..." $(pwd)

Limitations
-----------

pyastgrep is useful for grepping Python code at a fairly low level. It can be
used for various refactoring or linting tasks. Some linting tasks require higher
level understanding of a code base. For example, to detect use of a certain
function, you need to cope with various ways that the function may be imported
and used, and avoid detecting a function with the same name but from a different
module. For these kinds of tasks, you might be interested in:

* `Semgrep <https://semgrep.dev/>`_
* `Fixit <https://github.com/Instagram/Fixit>`_

If you are using this as a library, you should note that while AST works well
for linting, it’s not as good for rewriting code, because AST does not contain
or preserve things like formatting and comments. For a better approach, have a
look at `libCST <https://github.com/Instagram/LibCST>`_.


Use as a library
----------------

pyastgrep is structured internally to make it easy to use a library as well as
a CLI. However, while we will try not to break things without good reason, at this
point we are not documenting or guaranteeing API stability for these functions.


Contributing
------------

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

Links
-----

- `Green tree snakes <https://greentreesnakes.readthedocs.io/en/latest/>`__ - a very readable overview of Python ASTs.
- `ast module documentation <https://docs.python.org/3/library/ast.html>`__.
- `Python AST Explorer <https://python-ast-explorer.com/>`__ for worked  examples of ASTs.
- A `brief guide to XPath <http://www.w3schools.com/xml/xpath_syntax.asp>`__.
  See also the `XPath Axes <https://www.w3schools.com/xml/xpath_axes.asp>`_ guide
  which can be very helpful for matching related AST nodes.
- `Online XPath Tester <https://extendsclass.com/xpath-tester.html>`_

History
-------

This project was forked from https://github.com/hchasestevens/astpath by `H.
Chase Stevens <http://www.chasestevens.com>`__. Main changes:

* Added a test suite
* Many bugs fixed
* Significant rewrite of parts of code
* Changes to match grep/ripgrep, including formatting and automatic filtering.
