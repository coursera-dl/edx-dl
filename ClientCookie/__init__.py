# Import names from _ClientCookie.py so that they can be imported directly
# from the package, like this:
#from ClientCookie import <whatever>

try: True
except NameError:
    True = 1
    False = 0

from _ClientCookie import VERSION, __doc__, \
     Cookies, NetscapeCookies, MSIECookies
try:
    from urllib2 import AbstractHTTPHandler
except ImportError:
    pass
else:
    from _ClientCookie import HTTPHandler, build_opener, install_opener, \
         urlopen, HTTPRedirectHandler
    import httplib
    if hasattr(httplib, 'HTTPS'):
        from _ClientCookie import HTTPSHandler
    del AbstractHTTPHandler, httplib
from _HTTPDate import str2time

# Global HTTP-level debugging switch (has an effect only if you're using
# ClientCookie.HTTPHandler or ClientCookie.HTTPSHandler -- via
# ClientCookie.urlopen or ClientCookie.build_opener, for example).
# Useful to set if debugging code that uses ClientCookie.
HTTP_DEBUG = False
# Useful to set if debugging ClientCookie itself.
CLIENTCOOKIE_DEBUG = False


# for internal use only
from ClientCookie import _HTTPDate, _HeadersUtil, \
     _Debug, _ClientCookie, _Util
