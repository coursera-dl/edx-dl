"""Header value parsing utility functions.

  from ClientCookie._HeadersUtil import split_header_words
  values = split_header_words(h.headers["Content-Type"])

This module provides a few functions that helps parsing and
construction of valid HTTP header values.


Copyright 1997-1998, Gisle Aas
Copyright 2002, John J. Lee

This code is free software; you can redistribute it and/or modify it under
the terms of the MIT License (see the file COPYING included with the
distribution).

"""

# from Gisle Aas's CVS revision 1.9, libwww-perl 5.64

import re, string
from types import StringType
try:
    from types import UnicodeType
    STRING_TYPES = StringType, UnicodeType
except:
    STRING_TYPES = StringType,

from _Util import startswith

def pair_up(l):
    """Return list of pairs, given a list.

    pair_up([1,2,3,4]) => [(1,2), (3,4)]

    """
    assert len(l)%2 == 0
    result = []
    pair = [None, None]
    for i in xrange(len(l)):
        pair[i%2] = l[i]
        if i%2 == 1:
            result.append(tuple(pair))
    return result

def unmatched(match):
    """Return unmatched part of re.Match object."""
    start, end = match.span(0)
    return match.string[:start]+match.string[end:]

token_re = re.compile(r"^\s*(=*[^\s=;,]+)")
quoted_value_re = re.compile(r"^\s*=\s*\"([^\"\\]*(?:\\.[^\"\\]*)*)\"")
escape_re = re.compile(r"\\(.)")
value_re = re.compile(r"^\s*=\s*([^;,\s]*)")
def split_header_words(header_values):
    r"""Parse header values into a list of lists containing key,value pairs.

    The function knows how to deal with ",", ";" and "=" as well as quoted
    values after "=".  A list of space separated tokens are parsed as if they
    were separated by ";".

    If the header_values passed as argument contains multiple values, then they
    are treated as if they were a single value separated by comma ",".

    This means that this function is useful for parsing header fields that
    follow this syntax (BNF as from the HTTP/1.1 specification, but we relax
    the requirement for tokens).

      headers           = #header
      header            = (token | parameter) *( [";"] (token | parameter))

      token             = 1*<any CHAR except CTLs or separators>
      separators        = "(" | ")" | "<" | ">" | "@"
                        | "," | ";" | ":" | "\" | <">
                        | "/" | "[" | "]" | "?" | "="
                        | "{" | "}" | SP | HT

      quoted-string     = ( <"> *(qdtext | quoted-pair ) <"> )
      qdtext            = <any TEXT except <">>
      quoted-pair       = "\" CHAR

      parameter         = attribute "=" value
      attribute         = token
      value             = token | quoted-string

    Each header is represented by an anonymous array of key/value pairs.  The
    value for a simple token (not part of a parameter) is undef.  Syntactically
    incorrect headers will not necessary be parsed as you would want.

    This is easier to describe with some examples:

    >>> split_header_words(['foo="bar"; port="80,81"; discard, bar=baz'])
    [[('foo', 'bar'), ('port', '80,81'), ('discard', None)], [('bar', 'baz')]]
    >>> split_header_words(['text/html; charset="iso-8859-1"'])
    [[('text/html', None), ('charset', 'iso-8859-1')]]
    >>> split_header_words([r'Basic realm="\"foo\bar\""'])
    [[('Basic', None), ('realm', '"foobar"')]]

    """
    # XXX yuck
    assert type(header_values) not in STRING_TYPES
    res = []
    for thing in header_values:
        cur = []
        while len(thing) != 0:
            matched = 0
            m = token_re.search(thing)
            if m:  # 'token' or parameter 'attribute'
                matched = 1
                thing = unmatched(m)
                cur.append(m.group(1))
                matched_inner = 0
                m = quoted_value_re.search(thing)
                if m:  # a quoted value
                    matched_inner = 1
                    thing = unmatched(m)
                    val = m.group(1)
                    val = escape_re.sub(r"\1", val)
		    cur.append(val)
                if not matched_inner:
                    m = value_re.search(thing)
                    if m:  # some unquoted value
                        matched_inner = 1
                        thing = unmatched(m)
                        val = m.group(1)
                        val = string.rstrip(val)
                        cur.append(val)
                if not matched_inner:  # no value, a lone token
                    cur.append(None)
            if not matched:
                if startswith(string.lstrip(thing), ","):
                    matched = 1
                    thing = string.lstrip(thing)[1:]
                    if cur: res.append(pair_up(cur))
                    cur = []
            if not matched:
                assert startswith(thing, " ") or startswith(thing, ";"), (
                    "This should not happen: '%s'\n cur: %s" % (thing, cur))
                thing = string.lstrip(thing)
                if startswith(thing, ";"):
                    thing = thing[1:]
        if cur: res.append(pair_up(cur))
    return res

join_escape_re = re.compile(r"([\"\\])")
def join_header_words(lists):
    """Do the inverse of the conversion done by split_header_words.

    Takes a list of lists of (key, value) pairs and produces a single header
    value.  Attribute values are quoted if needed.

    >>> join_header_words([[("text/plain", None), ("charset", "iso-8859/1")]])
    'text/plain; charset="iso-8859/1"'
    >>> join_header_words([[("text/plain", None)], [("charset", "iso-8859/1")]])
    'text/plain, charset="iso-8859/1"'

    """
    res = []
    for pairs in lists:
        attr = []
        for k, v in pairs:
            if v is not None:
                if re.search(r"^\w+$", v):
                    k = k + ("=%s" % (v,))
                else:
                    v = join_escape_re.sub(r"\\\1", v)  # escape " and \
                    k = k + ('="%s"' % (v,))
            attr.append(k)
        if attr: res.append(string.join(attr, "; "))
    return string.join(res, ", ")

def _test():
   import doctest, _HeadersUtil
   return doctest.testmod(_HeadersUtil)

if __name__ == "__main__":
   _test()
