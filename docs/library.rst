================
Use as a library
================

pyastgrep is structured internally to make it easy to use as a library as well
as a CLI, with a clear separation of the different layers. For now, the
following API is documented as public and we will strive to maintain backwards
compatibility with it.

For other things, while we will try not to break things without good reason,
at this point we are not documenting or guaranteeing API stability for these
functions. Please contribute to `the discussion
<https://github.com/spookylukey/pyastgrep/discussions/18>`_ if you have needs
here.


.. currentmodule:: pyastgrep.api

.. function:: search_python_files(paths, expression, python_file_processor=process_python_file)

   Searches for files with AST matching the given XPath ``expression``, in the given ``paths``.

   If ``paths`` contains directories, then all Python files in that directory
   and below will be found, but ``.gitignore`` and other rules are used to
   ignore files and directories automatically.

   Returns an iterable of :class:`Match` object, plus other objects.

   The other objects are used to indicate errors, usually things like a failure
   to parse a file that had a ``.py`` extension. The details of these other
   objects are not being documented yet, so use at own risk, and ensure that you
   filter the results by doing an ``isinstance`` check for the ``Match``
   objects.

   By default, ``search_python_files`` does no caching of the conversion of
   Python to XML, which is appropriate for the normal command line usage.
   However, this conversion is relatively expensive, and for various use cases
   as a library, you might want to cache this operation.

   To achieve this, you can pass the ``python_file_processor`` argument. This
   value must be a callable that takes a :class:`pathlib.Path` objects and
   returns a :class:`ProcessedPython` object or a :class:`ReadError` object.

   By default this is :func:`process_python_file` but an alternative can be
   provided, such as :func:`process_python_file_cached`, or your own callable
   that typically will wrap :func:`process_python_file` in some other way.

   :param paths: List of paths to search, which can be files or directories, of type :class:`pathlib.Path`
   :type paths: list[pathlib.Path]

   :param expression: XPath expression
   :type expression: str

   :param python_file_processor: callable that takes a :class:`pathlib.Path` objects and returns a :class:`ProcessedPython` object or a :class:`ReadError` object.

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

.. function:: process_python_file(path)

   Default value of ``python_file_processor`` parameter above: a function that
   parses a Python file to create the AST and the XML version. This does no
   caching. You should not need to call this yourself.


.. function:: process_python_file_cached(path)

   Wrapper for :func:`process_python_file` that caches infinitely in memory, based
   on the input filename only.

   This can be an appropriate caching strategy:

   - if you are operating on a fairly limited number of Python files (or, if
     available memory is not a problem)

   - if you have a fairly short-lived process

   - if you don’t need to respond to on-disk changes to file contents
     for the life-time of the process.

.. class:: ProcessPython

   Return type of :func:`process_python_file`. For now, this is an opaque type,
   as you should not need to construct this yourself – you should be wrapping
   :func:`process_python_file` which will construct this for you.

.. class:: ReadError

   Return type of :func:`process_python_file` for the case of error reading the
   file. This is again an opaque type for now.


Example
=======

For example usage of ``search_python_files``, see the blog post `pyastgrep and
custom linting
<https://lukeplant.me.uk/blog/posts/pyastgrep-and-custom-linting/>`_.
