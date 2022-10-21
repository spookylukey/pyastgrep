import re
from lxml import etree
from lxml.etree import tostring

import elementpath  # XPath 2.0 functions


__all__ = ['tostring', 'lxml_query']

def lxml_query(element, expression):
    return element.xpath(expression)


def elementpath_query(element, expression):
    return elementpath.select(element, expression)



regex_ns = etree.FunctionNamespace('https://github.com/spookylukey/pyastgrep')
regex_ns.prefix = 're'


@regex_ns
def match(ctx, pattern, strings):
    return any(
        re.match(pattern, s) is not None
        for s in strings
    )

@regex_ns
def search(ctx, pattern, strings):
    return any(
        re.search(pattern, s) is not None
        for s in strings
    )
