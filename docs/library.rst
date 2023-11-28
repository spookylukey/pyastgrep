================
Use as a library
================

pyastgrep is structured internally to make it easy to use as a library as well
as a CLI, with a clear separation of the different layers. For now, the
following API is documented as public and we will strive to maintain backwards
compatibility with it:

.. currentmodule:: pyastgrep.api

.. function:: search_python_files(paths, expression)

   Searches for files with AST matching the given XPath ``expression``, in the given ``paths``.

   If ``paths`` contains directories, then all Python files in that directory
   and below will be found, but ``.gitignore`` and other rules are used to
   ignore files and directories automatically.

   Returns an iterable of :class:`Match` object, plus other objects.

   The other objects are used to indicate errors, usually things like a failure to parse a file that had a ``.py`` extension. The details of these other objects are not being documented yet, so use at own risk, and ensure that you filter the results by doing an ``isinstance`` check for the ``Match`` objects.

   :param paths: List of paths to search, which can be files or directories, of type :class:`pathlib.Path`
   :type paths: list[pathlib.Path]

   :param expression: XPath expression

   :type expression: str

   :return: Iterable[Match | Any]




.. class:: Match

   Represents a matched AST node. The public properties of this are:

   .. property:: path

      The path of the file containing the match.

      :type: pathlib.Path

   .. property:: position

      The position of the matched AST node within the Python file.

      :type: :class:`Position`

   .. property:: ast_node

      The AST node object matched

      :type: ast.AST

   .. property:: matching_line

      The text of the whole line that matched

      :type: str

.. class:: Position

   .. property:: lineno

      Line number, 1-indexed, as per AST module

      :type: int

   .. property:: col_offset

      Column offset, 0-indexed, as per AST module

      :type: int


For other things, we while we will try not to break things without good reason,
at this point we are not documenting or guaranteeing API stability for these
functions. Please contribute to `the discussion
<https://github.com/spookylukey/pyastgrep/discussions/18>`_ if you have needs
here.
