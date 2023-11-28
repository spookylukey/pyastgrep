========
Examples
========


* Find usages of a function called ``open``:

  .. code-block:: shell

     $ pyastgrep './/Call/func/Name[@id="open"]'
     src/pyastgrep/search.py:88:18:            with open(path) as f:

* Literal numbers:

  .. code-block:: shell

     $ pyastgrep './/Constant[@type="int" or @type="float"]'
     tests/examples/test_xml/everything.py:5:20:    assigned_int = 123
     tests/examples/test_xml/everything.py:6:22:    assigned_float = 3.14

* Function calls where:

  * the function is named ``open``:
  * the second positional argument is a string literal containing the character ``b``:

  .. code-block:: shell

     pyastgrep './/Call[./func/Name[@id="open"]][./args/Constant[position()=1][contains(@value, "b")]]'

* Usages of ``open`` that are **not** in a ``with`` item expression:

  .. code-block:: shell

     pyastgrep './/Call[not(ancestor::withitem)]/func/Name[@id="open"]'

* Names longer than 42 characters, wherever they are used.

  .. code-block:: shell

     pyastgrep './/Name[string-length(@id) > 42]'

* ``except`` clauses that raise a different exception class than they catch:

  .. code-block:: shell

     pyastgrep "//ExceptHandler[body//Raise/exc//Name and not(contains(body//Raise/exc//Name/@id, type/Name/@id))]"

* Functions whose name contain a certain substring:

  .. code-block:: shell

     pyastgrep './/FunctionDef[contains(@name, "something")]'

* Classes whose name matches a regular expression:

  .. code-block:: shell

     pyastgrep ".//ClassDef[re:match('M.*', @name)]"


  The above uses the Python `re.match
  <https://docs.python.org/3/library/re.html#re.match>`_ method. You can also use
  ``re:search`` to use the Python `re.search
  <https://docs.python.org/3/library/re.html#re.search>`_ method.

* Case-insensitive match of names on the left hand side of an assignment
  containing a certain string. This can be achieved using the ``lower-case``
  function from XPath2:

  .. code-block:: shell

     pyastgrep './/Assign/targets//Name[contains(lower-case(@id), "something")]' --xpath2


  You can also use regexes, passing the ``i`` (case-insensitive flag) as below, as
  described in the Python `Regular Expression Syntax docs
  <https://docs.python.org/3/library/re.html#regular-expression-syntax>`_

  .. code-block:: shell

     pyastgrep './/Assign/targets//Name[re:search("(?i)something", @id)]'


* Assignments to the name ``foo``, including type annotated assignments, which
  use ``AnnAssign``, and tuple unpacking assignments (while avoiding things like
  ``foo.bar = ...``). Note the use of the ``|`` operator to do a union.

  .. code-block:: shell

     pyastgrep '(.//AnnAssign/target|.//Assign/targets|.//Assign/targets/Tuple/elts)/Name[@id="foo"]'

* Docstrings of functions/methods whose value contains “hello”:

  .. code-block:: shell

     pyastgrep './/FunctionDef/body/Expr[1]/value/Constant[@type="str"][contains(@value, "hello")]'

* For-loop variables called ``i`` or ``j`` (including those created by tuple unpacking):

  .. code-block:: shell

     pyastgrep './/For/target//Name[@id="i" or @id="j"]'


* Method calls: These are actually “calls” on objects that are attributes of other
  objects. This will match the top-level object:

  .. code-block:: shell

     pyastgrep './/Call/func/Attribute'


* Individual positional arguments to a method call named ``encode``, where the
  arguments are literal strings or numbers. Note the use of ``Call[…]`` to match
  “Call nodes that have descendants that match …”, rather than matching those
  descendant nodes themselves.

  .. code-block:: shell

     pyastgrep './/Call[./func/Attribute[@attr="encode"]]/args/Constant'


* For a Django code base, find all ``.filter`` and ``.exclude`` method calls, and
  all ``Q`` object calls, which have a keyword argument where the name contains
  the string ``"user"``, for finding ORM calls like
  ``.filter(user__id__in=...)`` or ``Q(thing__user=...)``:

  .. code-block:: shell

     pyastgrep '(.//Call[./func/Attribute[@attr="filter" or @attr="exclude"]] | .//Call[./func/Name[@id="Q"]]) [./keywords/keyword[contains(@arg, "user")]]'
