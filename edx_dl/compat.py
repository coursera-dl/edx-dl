#!/usr/bin/env python
# -*- coding: utf-8 -*-

# python 2/3 compatibility imports
from __future__ import print_function, unicode_literals

import sys

from six.moves.http_cookiejar import CookieJar
from six.moves.urllib.parse import urlencode
from six.moves.urllib.request import urlopen, build_opener, install_opener
from six.moves.urllib.request import HTTPCookieProcessor, Request
from six.moves.urllib.error import HTTPError, URLError


def compat_print(*objects, **kwargs):
    """
    Workaround the print function to adapt for the encoding bug in Windows
    console.

    It will try to convert text to the console encoding before printing to
    prevent crashes.
    """
    try:
        stream = kwargs.get('file', None)
        if stream is None:
            stream = sys.stdout
        enc = stream.encoding
        if enc is None:
            enc = sys.getdefaultencoding()
    except AttributeError:
        return print(*objects, **kwargs)

    texts = []
    for object in objects:
        try:
            if type(object) is bytes:
                if sys.version_info < (3, 0):
                    # in python 2 bytes must be converted to str before decode
                    object = str(object)
                original_text = object.decode(enc, errors='replace')
            else:
                if sys.version_info < (3, 0):
                    object = unicode(object)
                original_text = object.encode(enc, errors='replace').decode(enc, errors='replace')
        except UnicodeEncodeError:
            original_text = unicode(object).encode(enc, errors='replace').decode(enc, errors='replace')
        texts.append(original_text)
    return print(*texts, **kwargs)
