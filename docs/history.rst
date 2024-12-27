=======
History
=======

Version 1.4 - unreleased
------------------------

* Added ``python_file_processor`` parameter to :func:`pyastgrep.api.search_python_files`,
  which particularly serves the needs of people using pyastgrep as a library who
  want to apply caching.

Version 1.3.2 - 2024-01-10
--------------------------

* Fixed various crashers for permission errors or broken files
* Documented API for use as a library.

Version 1.3.1 - 2023-07-19
--------------------------

* Improved help text

Version 1.3 - 2023-07-18
------------------------

* Added color, enabled by default, see ``--color`` flag.


Version 1.2.2 - 2023-06-27
--------------------------

* Fixed bug with searching for unicode characters
* Fixed various bugs handling illegal XML characters and byte literals

Version 1.2.1 - 2023-06-22
--------------------------

* Better ``--help`` text
* Fixed bug with printing of decorators when using ``--context=statement``
* Internal refactorings

Version 1.2 - 2023-06-21
------------------------

* Added lots of flags/features:

  * ``--heading``
  * ``--debug``
  * ``--no-global-ignores``
  * ``--no-ignore-vcs``
  * ``--context=statement``

* Handle Ctrl-C cleanly

* Auto-dedenting of code when using ``--heading --context=statement``

* Dropped support for Python 3.7

Version 1.1 - 2023-06-09
------------------------

* Fixed crasher when global ~/.gitignore does not exist

Version 1.0 - 2023-04-17
------------------------

* Added convenience ``Match.matching_line`` for library usage.
* Fixed mypy errors.

Version 0.11 - 2023-02-20
-------------------------

* In recursive filesystem walk, ignore symlinks (as per ripgrep) instead of crashing

Version 0.10 - 2022-11-25
-------------------------

* Automatic dedenting of code from stdin

Version 0.9 - 2022-11-16
------------------------

* Added ``pyastdump`` command to more easily see the XML structure.

Version 0.8 - 2022-11-14
------------------------

* Added ``--css`` option to support CSS selectors instead of XPath.

Version 0.7 - 2022-11-07
------------------------

* Fixed crasher if global gitignore path contained ``~`` (tilde). Thanks
  `@lost-theory <https://github.com/lost-theory>`_!

Version 0.6 - 2022-11-07
------------------------

* Fixed several cases where .gitignore patterns were not being interpreted correctly.

Version 0.5 - 2022-11-07
------------------------

* Fixed bug with XPath expression that don’t select XML nodes. See https://github.com/hchasestevens/astpath/issues/20

Version 0.4 - 2022-11-07
------------------------

* Handle non-UTF8 encodings
* Automatically apply .gitignore for ignoring files

Version 0.3 - 2022-10-27
------------------------

* Fixed various error handling issues

Version 0.2 - 2022-10-26
------------------------

* Changed dev status to ’Beta’

Version 0.1 - 2022-10-26
------------------------

First release. This is a fork of `astpath
<https://github.com/hchasestevens/astpath>`_ with the following major changes:

* Changed CLI interface and behaviour to match grep/ripgrep as far as that is sensible
* Significant rewrite of parts of code to untangling the filesystem/XML/printing work
* Many bugs fixed, various features added.
