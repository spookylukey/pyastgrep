====================
Bugs and limitations
====================

Bugs
====

Due to limitations in what characters can be stored in an XML document, null
bytes (``\x00``) and other characters such as escape codes in string and byte
literals get stripped, and can’t be searched for. This also means that some
other string literal searches might return unexpected results because of
characters being stripped in the XML:

.. code-block:: python

   x = b"A\x00B"

.. code-block:: shell

   $ pyastgrep './/Constant[@value="AB"]'
   myfile.py:1:5:x = b"A\x00B"

Limitations and other tools
===========================

pyastgrep is useful for grepping Python code at a fairly low level. It can be
used for various refactoring or linting tasks. Some linting tasks require higher
level understanding of a code base. For example, to detect use of a certain
function, you need to cope with various ways that the function may be imported
and used, and avoid detecting a function with the same name but from a different
module. For these kinds of tasks, you might be interested in:

* `Semgrep <https://semgrep.dev/>`_
* `Fixit <https://github.com/Instagram/Fixit>`_

If you are looking for something simpler, try:

* Simon Willison’s `symbex <https://github.com/simonw/symbex/>`_ which can
  extract functions/methods/classes.

If you are using this as a library, you should note that while AST works well
for linting, it’s not as good for rewriting code, because AST does not contain
or preserve things like formatting and comments. For a better approach, have a
look at `libCST <https://github.com/Instagram/LibCST>`_.
