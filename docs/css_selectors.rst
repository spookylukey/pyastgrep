=============
CSS selectors
=============

In general, XPath expressions are more powerful than CSS selectors, and CSS
selectors have some things that are specific to HTML (such as specific selectors
for ``id`` and ``class``). However, it may be easier to get started using CSS
selectors, and for some things CSS selectors are easier. In that case, just pass
``--css`` and the expression will be interpreted as a CSS selector instead.

For example, to get the first statement in each ``for`` statement body:

.. code-block:: shell

   pyastgrep --css 'For > body > *:first-child'

The CSS selector will converted to an XPath expression with a prefix of ``.//``
— that is, it will be interpreted as a query over all the document.

Note that unlike CSS selectors in HTML, the expression will be interpreted
case-sensitively.

You can also use the online tool `css2xpath <https://css2xpath.github.io/>`_ to
do translations before passing to ``pyastgrep``. This tool also supports some
things that cssselect (our dependency) `does not yet support
<https://github.com/scrapy/cssselect/issues>`_.
