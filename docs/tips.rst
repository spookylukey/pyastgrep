====
Tips
====


Command line flags
==================

There are a growing number of command line flags – see ``pyastgrep --help``

Extracting code snippets
========================

If you want to extract standalone snippets of code, try ``--context=statement
--heading`` which does automatic dedenting. e.g. to extract all functions and
methods, with leading whitespace removed, do:

.. code-block:: shell

   pyastgrep --heading -C statement './/FunctionDef'

Absolute paths
==============
To get pyastgrep to print absolute paths in results, pass the current absolute
path as the directory to search::

  pyastgrep "..." $(pwd)


Debugging XPath expressions
===========================

Use the ``--xml`` option to see the XML for matches. If you need to see more
context, you can use things like the ``parent`` or ``ancestor`` selector. For
example, you might do the following but get back more results than you want:

.. code-block::

   $ pyastgrep './/Assign/targets//Name[@id="foo"]
   example.py:1:1:foo = 1
   example.py:2:2:(foo, bar) = (3, 4)
   example.py:3:1:foo.bar = 2

Here you might be interested in the first two results, which both assign to
the name ``foo``, but not the last one since it does not. You can get the XML for the
whole matching assignment expressions like this:

.. code-block:: shell

   $ pyastgrep './/Assign/targets//Name[@id="foo"]/ancestor::Assign' --xml
   example.py:1:1:foo = 1
   <Assign lineno="1" col_offset="0">
     <targets>
       <Name lineno="1" col_offset="0" type="str" id="foo">
         <ctx>
           <Store/>
         </ctx>
       </Name>
     </targets>
     <value>
       <Constant lineno="1" col_offset="6" type="int" value="1"/>
     </value>
   </Assign>
   ...


You could also go the other way and change the XPath expression to match on the
parent ``Assign`` node — this matches “all ``Assign`` nodes that are parents of
a ``target`` node that is a parent of a ``Name`` node with attribute ``id``
equal to ``"foo"``:

.. code-block:: shell

   pyastgrep './/Assign[./targets//Name[@id="foo"]]' --xml
