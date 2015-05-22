#!/usr/bin/env python
# -*- coding: utf-8 -*-

# python 2/3 compatibility imports
from __future__ import print_function
from __future__ import unicode_literals

from six.moves import builtins
from six.moves.http_cookiejar import CookieJar
from six.moves import input
from six.moves.urllib.parse import urlencode
from six.moves.urllib.request import urlopen, build_opener, install_opener
from six.moves.urllib.request import HTTPCookieProcessor, Request
from six.moves.urllib.error import HTTPError, URLError
