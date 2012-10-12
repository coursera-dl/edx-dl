"""HTTP cookie handling for web clients.

ClientCookie is a Python module for handling HTTP cookies on the client
side, useful for accessing web sites that require cookies to be set and
then returned later.  It also provides some other (optional) useful stuff:
HTTP-EQUIV handling, zero-time Refresh handling, and lazily-seekable
responses.  It has developed from a port of Gisle Aas' Perl module
HTTP::Cookies, from the libwww-perl library.

Cookies are a general mechanism which server side connections can use to
both store and retrieve information on the client side of the connection.
More information about cookies:

http://www.netscape.com/newsref/std/cookie_spec.html
http://www.cookiecentral.com/

This module also implements the new style cookies described in RFC 2965.
The two variants of cookies are supposed to be able to coexist happily.
RFC 2965 handling can be switched off completely if required.

http://www.ietf.org/rfc/rfc2965.txt
http://www.ietf.org/rfc/rfc2964.txt


Note about cookie standards
--------------------------------------------------------------------------

The various cookie standards and their history form a case study of the
terrible things that can happen to a protocol.  The long-suffering David
Kristol has written a paper about it, if you want to know the gory details:

http://doi.acm.org/10.1145/502152.502153

Here is a summary.

The Netscape protocol (cookie_spec.html) is still the only standard
supported by most browsers (including Internet Explorer and Netscape).  Be
aware that cookie_spec.html is not, and never was, actually followed to
the letter (or anything close) by anyone (including Netscape, IE and
ClientCookie): the Netscape protocol standard is really defined by the
behaviour of Netscape (and now IE).

RFC 2109 was introduced to fix some problems identified with the Netscape
protocol, while still keeping the same HTTP headers (Cookie and
Set-Cookie).  The most prominent of these problems is the 'third-party'
cookie issue, which was an accidental feature of the Netscape protocol.
When one visits www.bland.org, one doesn't expect to get a cookie from
www.lurid.com, a site one has never visited.  Depending on browser
configuration, this can still happen, because the unreconstructed Netscape
protocol is happy to accept cookies from, say, an image in a webpage (from
www.bland.org) that's included by linking to an advertiser's server
(www.lurid.com).  In addition to the potential for embarrassment caused by
the presence of lurid.com's cookies on one's machine, this may also be
used to track your movements on the web, because advertising agencies like
doubleclick.net place ads on many sites.  RFC 2109 tried to change this by
requiring third-party ('unverifiable') cookies to be turned off unless the
user explicitly asks them to be turned on.  This clashed with the business
model of advertisers like doubleclick.net, who had started to take
advantage of the third-party cookies 'bug'.  Since the browser vendors
were more interested in the advertisers' concerns than those of the
browser users, this arguably doomed both RFC 2109 and its successor, RFC
2965, from the start.  Other problems than the third-party cookie issue
were also fixed by 2109.  However, even ignoring the advertising issue,
2109 was stillborn, because Internet Explorer and Netscape behaved
differently in response to its extended Set-Cookie headers.  This was not
really RFC 2109's fault: it worked the way it did to keep compatibility
with the Netscape protocol as implemented by Netscape.  Microsoft Internet
Explorer (MSIE) was very new when the standard was designed, but was
starting to be very popular when the standard was finalised.  XXX P3P, and
MSIE & Mozilla options

RFC 2965 attempted to fix this by introducing two new headers, Set-Cookie2
and Cookie2.  Unlike the Cookie header, Cookie2 does *not* carry cookies
to the server -- rather, it simply advertises to the server that RFC 2965
is understood.  Set-Cookie2 *does* carry cookies, from server to client:
the new header means that both IE and Netscape completely ignore these
cookies.  This prevents breakage, but introduces a chicken-egg problem
that means 2965 will probably never be widely adopted, especially since
Microsoft shows no interest in it.  Opera is the only browser I know of
that supports the standard.  On the server side, Apache's mod_usertrack
supports it.  One confusing point to note about RFC 2965 is that it uses
the same value (1) of the Version attribute in HTTP headers as does RFC
2109.

Very recently, it was discovered that RFC 2965 does not fully take account
of issues arising when 2965 and Netscape cookies coexist.  At the time of
writing (April 2003), the resulting errata are still being thrashed out.


Examples
--------------------------------------------------------------------------

 import ClientCookie
 response = ClientCookie.urlopen("http://foo.bar.com/")

This function behaves identically to urllib2.urlopen, except that it deals
with cookies automatically.  That's probably all you need to know.

Here is a more complicated example, involving Request objects (useful if
you want to pass Requests around, add headers to them, etc.):

 import ClientCookie
 import urllib2
 request = urllib2.Request("http://www.acme.com/")
 # note we're using the urlopen from ClientCookie, not urllib2
 response = ClientCookie.urlopen(request)
 # let's say this next request requires a cookie that was set in response
 request2 = urllib2.Request("http://www.acme.com/flying_machines.html")
 response2 = ClientCookie.urlopen(request2)

In these examples, the workings are hidden inside the ClientCookie.urlopen
method, which is an extension of urllib2.urlopen.  Redirects, proxies and
cookies are handled automatically by this function.  Other, lower-level,
cookie-aware extensions of urllib2 callables provided are: build_opener,
install_opener, HTTPHandler and HTTPSHandler (if your Python installation
has HTTPS support).  A bugfixed HTTPRedirectHandler is also included (the
bug, related to redirection, should be fixed in 2.3, but hasn't been yet).
Note that extraction and setting of RFC 2965 cookies (but not Netscape
cookies) is currently turned off during automatic urllib2 redirects (until
I figure out exactly when they're allowed).

An example at a slightly lower level shows what the module is doing more
clearly:

 import ClientCookie
 import urllib2
 request = urllib2.Request("http://www.acme.com/")
 response = urllib2.urlopen(request)
 c = ClientCookie.Cookies()
 c.extract_cookies(response, request)
 # let's say this next request requires a cookie that was set in response
 request2 = urllib2.Request("http://www.acme.com/flying_machines.html")
 c.add_cookie_header(request2)
 response2 = urllib2.urlopen(request2)

 print response2.geturl()
 print response2.info()  # headers
 for line in response2.readlines():  # body
     print line

The Cookies class does all the work.  There are essentially two operations:
extract_cookies extracts HTTP cookies from Set-Cookie (the original
Netscape cookie standard) and Set-Cookie2 (RFC 2965) headers from a
response if and only if they should be set given the request, and
add_cookie_header adds Cookie headers if and only if they are appropriate
for a particular HTTP request.  Incoming cookies are checked for
acceptability based on the host name, etc.  Cookies are only set on
outgoing requests if they match the request's host name, path, etc.
Cookies may be also be saved to and loaded from a file.

Note that if you're using ClientCookie.urlopen (or
ClientCookie.HTTPHandler or ClientCookie.HTTPSHandler), you don't need to
call extract_cookies or add_cookie header yourself.  If, on the other
hand, you don't want to use urllib2, you will need to use this pair of
methods.  You can make your own request and response objects, which must
support the interfaces described in the docstrings of extract_cookies and
add_cookie_header.


Important note
--------------------------------------------------------------------------

The distribution includes some associated modules (_HTTPDate and
_HeadersUtil) upon which ClientCookie depends, also ported from
libwww-perl.  These associated modules may change or disappear with time,
so don't rely on them staying put.  Anything you can import directly from
the ClientCookie package, and that doesn't start with a single underscore,
will not go away.


Cooperating with Netscape/Mozilla and Internet Explorer
--------------------------------------------------------------------------

The subclass NetscapeCookies differs from Cookies only in storing cookies
using a different, Netscape-compatible, file format.  This Netscape-
compatible format loses some information when you save cookies to a file.
Cookies itself uses a libwww-perl specific format (`Set-Cookie3').  Python
and Netscape should be able to share a cookies file (note that the file
location here will differ on non-unix OSes):

import os
home = os.environ["HOME"]
cookies = NetscapeCookies(
    file=os.path.join(home, "/.netscape/cookies.txt"),
    autosave=1)

XXX Does this work when Netscape is running?  Probably not.

NetscapeCookies also works with Mozilla, which uses the same format, though
with a slightly different header (the class saves cookies using the Netscape
header).

XXX does Mozilla complain about the Netscape header?  Probably not, but should
check.

MSIECookies does the same for Microsoft Internet Explorer (MSIE) 5.x and
6.x on Windows, but does not allow saving cookies in this format (because
nobody has fully decoded the file format).


Using your own Cookies instance
--------------------------------------------------------------------------

If you want to use the higher-level urllib2-like interface, but need to
get at the cookies (usually only needed for debugging, or saving cookies
between sessions) and/or pass arguments to the Cookies constructor,
HTTPHandler and HTTPSHandler accept a Cookies instance in their cookies
keyword argument.

The urlopen function uses an OpenerDirector instance to do its work, so if
you want to use urlopen, install your own OpenerDirector using the
ClientCookie.install_opener function, then proceed as usual:

import ClientCookie
from ClientCookie import Cookies
cookies = Cookies(netscape_only=1, blocked_domains=["doubleclick.net"])
# Build an OpenerDirector that uses an HTTPHandler that uses the cookies
# instance we've just made.  build_opener will add other handlers (such
# as FTPHandler) automatically, so we only have to pass an HTTPHandler.
opener = ClientCookie.build_opener(ClientCookie.HTTPHandler(cookies))
ClientCookie.install_opener(opener)
r = urlopen("http://www.adverts-r-us.co.uk/")

Note that the OpenerDirector instance used by urlopen is global, and
shares the Cookies instance you pass in: all code that uses
ClientCookie.urlopen will therefore be sharing the same set of cookies.
If you don't want global cookies, build your own OpenerDirector object
using ClientCookie.build_opener as shown above, but don't bother to
call install_opener.  You can use it directly instead of calling
urlopen:

r = opener.open("http://acme.com/")  # GET
r = opener.open("http://acme.com/", data)  # POST


Optional goodies: HTTP-EQUIV, Refresh and seekable responses
--------------------------------------------------------------------------

These are implemented as three arguments to the HTTPHandler and
HTTPSHandler constructors.  Example code is below.

seekable_responses:

By default, ClientCookie's response objects are seekable.  Seeking is done
lazily (ie. the response object only reads from the socket as necessary,
rather than slurping in all the data before the response is returned to
you), but if you don't want it, you can turn it off.

handle_http_equiv:

The <META HTTP-EQUIV> tag is a way of including data in HTML to be treated
as if it were part of the HTTP headers.  ClientCookie can automatically
read these tags and add the HTTP-EQUIV headers to the response object's
real HTTP headers.  The HTML is left unchanged.

handle_refresh:

The Refresh HTTP header is a non-standard header which is widely used.  It
requests that the user-agent follow a URL after a specified time delay.
ClientCookie can treat these headers (which may have been set in <META
HTTP-EQUIV> tags) as if they were 302 redirections.  Only Refresh headers
with zero delay are treated in this way.

import ClientCookie
from ClientCookie import Cookies
cookies = Cookies()
hh = ClientCookie.HTTPHandler(cookies,
    seekable_responses=0, handle_refresh=1)
opener = ClientCookie.build_opener(hh)
opener.open("http://www.rhubarb.com/")


Adding headers
--------------------------------------------------------------------------

Adding headers is done like so:

import ClientCookie, urllib2
req = urllib2.Request("http://foobar.com/")
req.add_header("Referer", "http://wwwsearch.sourceforge.net/ClientCookie/")
r = ClientCookie.urlopen(req)

You can also use the headers argument to the urllib2.Request constructor.

urllib2.Request objects start out with no headers.  urllib2 adds some
headers to Request objects automatically -- see the next section for
details.  Also, urllib2 does send a few standard headers of its own (such
as Content-Length, Content-Type and Host) when the Request is passed to
urlopen, without adding them to the Request object.


Changing the automatically-added headers (User-Agent)
--------------------------------------------------------------------------

urllib2.OpenerDirector automatically adds a User-Agent header to every
request.

Again, since ClientCookie.urlopen uses an OpenerDirector instance, you
need to install your own OpenerDirector using the
ClientCookie.install_opener function to change this behaviour.

import ClientCookie
cookies = ClientCookie.Cookies()
opener = ClientCookie.build_opener(ClientCookie.HTTPHandler(cookies))
opener.addheaders = [("User-agent", "Mozilla/4.76")]
ClientCookie.install_opener(opener)
r = urlopen("http://acme.com/")

Again, you can always call opener.open directly (instead of urlopen) if
you don't want global cookies.


Debugging
--------------------------------------------------------------------------

First, a few common problems.  The most frequent mistake people seem to
make is to use ClientCookie.urlopen, *and* the extract_cookies and
add_cookie_header methods on a cookie object themselves.  If you use
ClientCookie.urlopen, the module handles extraction and adding of cookies
by itself, so you should not call extract_cookies or add_cookie_header.

If things don't seem to be working as expected, the first thing to try is
to switch off RFC 2965 handling, using the netscape_only argument to the
Cookies constructor.  This is because few browsers implement it, so it is
likely that some servers incorrectly implement it.  This switch is also
useful because ClientCookie does not yet fully implement redirects with
RFC 2965 cookies.  2965 cookies are always switched off during redirects,
while the standard allows setting and returning cookies under some
circumstances, which will probably cause some servers to refuse to provide
content.

Are you sure the server is sending you any cookies in the first place?
Maybe the server is keeping track of state in some other way (HIDDEN HTML
form entries (possibly in a separate page referenced by a frame),
URL-encoded session keys, IP address)?  Perhaps some embedded script in
the HTML is setting cookies (see below)?  Maybe you messed up your
request, and the server is sending you some standard failure page (even if
the page doesn't appear to indicate any failure).  Sometimes, a server
wants particular headers set to the values it expects, or it won't play
nicely.  The most frequent offenders here are the Referer [sic] and / or
User-Agent HTTP headers.  See above for how to change the value of the
User-Agent header; otherwise, use Request.add_header.  The User-Agent
header may need to be set to a value like that of a popular browser, as
shown above.  The Referer header may need to be set to the URL that the
server expects you to have followed a link from.  Occasionally, it may
even be that operators deliberately configure a server to insist on
precisely the headers that the popular browsers (MS Internet Explorer,
Netscape/Mozilla, Opera) generate, but remember that incompetence
(possibly on your part) is more probable than deliberate sabotage.

When you save to a file, single-session cookies will expire unless you
explicitly request otherwise by setting ignore_discard to true in the
Cookies constructor.  This may be your problem if you find cookies are
going away after saving and loading.

If none of the advice above seems to solve your problem, the last resort
is to compare the headers and data that you are sending out with those
that a browser emits.  Of course, you'll want to check that the browser is
able to do manually what you're trying to achieve programatically before
minutely examining the headers.  Make sure that what you do manually is
*exactly* the same as what you're trying to do from Python -- you may
simply be hitting a server bug that only gets revealed if you view pages
in a particular order, for example.  In order to see what your browser is
sending to the server, you can use a TCP network sniffer (netcat --
usually installed as nc, or ethereal, for example), or a feature like
lynx's -trace switch, or just turn on ClientCookie.HTTP_DEBUG (see below).
If nothing is obviously wrong with the requests your program is sending,
you may have to temporarily switch to sending HTTP headers (with httplib).
Start by copying Netscape or IE slavishly (apart from session IDs, etc.,
of course), then begin the tedious process of mutating your headers and
data until they match what your higher-level code was sending.  This will
reliably find your problem.

You can globally turn on display of HTTP headers:

import ClientCookie
ClientCookie.HTTP_DEBUG = 1

(Note that doing this won't work:

from ClientCookie import HTTP_DEBUG
HTTP_DEBUG = 1

If you don't understand that, you've misunderstood what the = operator
does.)

Alternatively, you can examine your individual request and response
objects to see what's going on.  ClientCookie's responses are seek()able
unless you request otherwise.

If you would like to see what is going on in ClientCookie's tiny mind, do
this:

ClientCookie.CLIENTCOOKIE_DEBUG = 1


Embedded script that sets cookies
--------------------------------------------------------------------------

It is possible to embed script in HTML pages (within <SCRIPT>here</SCRIPT>
tags) -- Javascript / ECMAScript, VBScript, or even Python -- that causes
cookies to be set in a browser.  If you come across this in a page you
want to automate, you have three options.  Here they are, roughly in order
of simplicity.  First, you can simply figure out what the embedded script
is doing and imitate it by manually adding cookies to your Cookies
instance.  Second, if you're working on a Windows machine (or another
platform where the MSHTML COM library is available) you could give up the
fight and automate Microsoft Internet Explorer (MSIE) with COM.  Third,
you could get ambitious and delegate the work to an appropriate
interpreter (Netscape's Javascript interpreter, for instance).


Parsing HTTP date strings
--------------------------------------------------------------------------

A function named str2time is provided by the package, which may be useful
for parsing dates in HTTP headers.  str2time is intended to be liberal,
since HTTP date/time formats are poorly standardised in practice.  There
is no need to use this function in normal operations: Cookies instances
keep track of cookie lifetimes automatically.  This function will stay
around in some form, though the supported date/time formats may change.

XXX str2time is currently broken for non-UTC timezones: first, the return value
is always in UTC


A final note: docstrings, comments and debug strings in this code refer to
the attributes of the HTTP cookie system as cookie-attributes, to
distinguish them clearly from Python attributes.


Copyright 1997-1999 Gisle Aas (libwww-perl)
Copyright 2002-2003 Johnny Lee <typo_pl@hotmail.com> (MSIE Perl code)
Copyright 2002-2003 John J Lee <jjl@pobox.com> (The Python port)

This code is free software; you can redistribute it and/or modify it under
the terms of the MIT License (see the file COPYING included with the
distribution).

"""

# XXXX
# Write new 1.5.2 code to test ClientCookie on new site (Yahoo mail?).
# Test urllib / urllib2 and ClientCookie with 1.5.2.

VERSION = "0.3.5b"  # based on Gisle Aas's CVS revision 1.24, libwww-perl 5.64


# Public health warning: anyone who thought 'cookies are simple, aren't they?',
# run away now :-(


# These quotes from the RFC are sitting here for when I fix the redirect
# behaviour (see TODO file).

# Redirects: RFC 2965, section 3.3.6:
#------------------------------------
#   An unverifiable transaction is to a third-party host if its request-
#   host U does not domain-match the reach R of the request-host O in the
#   origin transaction.

#   When it makes an unverifiable transaction, a user agent MUST disable
#   all cookie processing (i.e., MUST NOT send cookies, and MUST NOT
#   accept any received cookies) if the transaction is to a third-party
#   host.

# request-host: RFC 2965, section 1:
#   Host name (HN) means either the host domain name (HDN) or the numeric
#   Internet Protocol (IP) address of a host.  The fully qualified domain
#   name is preferred; use of numeric IP addresses is strongly
#   discouraged.
 
#   The terms request-host and request-URI refer to the values the client
#   would send to the server as, respectively, the host (but not port)
#   and abs_path portions of the absoluteURI (http_URL) of the HTTP
#   request line.  Note that request-host is a HN.

# Reach: RFC 2965, section 1:

#   The reach R of a host name H is defined as follows:
# 
#      *  If
# 
#         -  H is the host domain name of a host; and,
# 
#         -  H has the form A.B; and
# 
#         -  A has no embedded (that is, interior) dots; and
# 
#         -  B has at least one embedded dot, or B is the string "local".
#            then the reach of H is .B.

#      *  Otherwise, the reach of H is H.

import sys, os, re, urlparse, string, socket, copy, struct, htmllib, formatter
from urllib2 import URLError
from time import time
if os.name == "nt":
    import _winreg

import ClientCookie
from ClientCookie._HTTPDate import str2time, time2isoz
from ClientCookie._HeadersUtil import split_header_words, join_header_words
from ClientCookie._Util import startswith, endswith
from ClientCookie._Debug import debug

try: True
except NameError:
    True = 1
    False = 0

CHUNK = 1024  # size of chunks fed to HTML HEAD parser, in bytes
MISSING_FILENAME_TEXT = ("a filename was not supplied (nor was the Cookies "
                         "instance initialised with one)")


SPACE_DICT = {}
for c in string.whitespace:
    SPACE_DICT[c] = None
del c
def isspace(string):
    for c in string:
        if not SPACE_DICT.has_key(c): return False
    return True

def getheaders(msg, name):
    """Get all values for a header.

    This returns a list of values for headers given more than once; each
    value in the result list is stripped in the same way as the result of
    getheader().  If the header is not given, return an empty list.
    """
    result = []
    current = ''
    have_header = 0
    for s in msg.getallmatchingheaders(name):
        if isspace(s[0]):
            if current:
                current = "%s\n %s" % (current, string.strip(s))
            else:
                current = string.strip(s)
        else:
            if have_header:
                result.append(current)
            current = string.strip(s[string.find(s, ":") + 1:])
            have_header = 1
    if have_header:
        result.append(current)
    return result


IPV4_RE = re.compile(r"\.\d+$")
def is_HDN(text):
    """Return True if text is a host domain name."""
    # XXX
    # This may well be wrong.  Which RFC is HDN defined in, if any?
    # For the current implementation, what about IPv6?  Remember to look
    # at other uses of IPV4_RE also, if change this.
    if IPV4_RE.search(text):
        return False
    if text == "":
        return False
    if text[0] == "." or text[-1] == ".":
        return False
    return True

def domain_match(A, B):
    """Return True if domain A domain-matches domainB, according to RFC 2965.

    A and B may be host domain names or IP addresses.

    RFC 2965, section 1:

    Host names can be specified either as an IP address or a HDN string.
    Sometimes we compare one host name with another.  (Such comparisons SHALL
    be case-insensitive.)  Host A's name domain-matches host B's if

         *  their host name strings string-compare equal; or

         * A is a HDN string and has the form NB, where N is a non-empty
            name string, B has the form .B', and B' is a HDN string.  (So,
            x.y.com domain-matches .Y.com but not Y.com.)

    Note that domain-match is not a commutative operation: a.b.c.com
    domain-matches .c.com, but not the reverse.

    """
    # Note that, if A or B are IP addresses, the only relevant part of the
    # definition of the domain-match algorithm is the direct string-compare.
    A = string.lower(A)
    B = string.lower(B)
    if A == B:
        return True
    if not is_HDN(A):
        return False
    i = string.rfind(A, B)
    if i == -1 or i == 0:
        # A does not have form NB, or N is the empty string
        return False
    if not startswith(B, "."):
        return False
    if not is_HDN(B[1:]):
        return False
    return True

def liberal_is_HDN(text):
    """Return True if text is a host domain name; for blocking domains."""
    if IPV4_RE.search(text):
        return False
    return True

def liberal_domain_match(A, B):
    """For blocking domains.

    A and B may be host domain names or IP addresses.

    "" is matched by everything, including all IP addresses:

    assert liberal_domain_match(whatever, "")

    """
    A = string.lower(A)
    B = string.lower(B)
    if B == "":
        return True
    if A == B:
        return True
    if not (liberal_is_HDN(A) and liberal_is_HDN(B)):
        return False
    if endswith(A, B):
        return True
    return False

## # XXXX I'm pretty sure this is incorrect -- we only need to check the
## # original request's absoluteURL.
## cut_port_re = re.compile(r":\d+$")
## def request_host(request):
##     header = request.headers.get("Host")
##     if header is not None:
##         host = header
##     else:
##         # XXX I think these two actually do the same thing, essentially, but
##         #  I'm not sure of the precise semantics of request.get_host.
##         #  Actually, I think urllib2's behaviour here is wrong (SF Python bug
##         #  413135).
##         url = request.get_full_url()
##         host = urlparse.urlparse(url)[1]
##         #host = request.get_host()

##     return cut_port_re.sub("", host, 1)  # remove port, if present

cut_port_re = re.compile(r":\d+$")
def request_host(request):
    url = request.get_full_url()
    host = urlparse.urlparse(url)[1]
    if host == "":
        host = request.headers.get("Host", "")

    return cut_port_re.sub("", host, 1)  # remove port, if present

def request_path(request):
    url = request.get_full_url()
    #scheme, netloc, path, parameters, query, frag = urlparse.urlparse(url)
    req_path = normalize_path(string.join(urlparse.urlparse(url)[2:], ""))
    if not startswith(req_path, "/"):
        # fix bad RFC 2396 absoluteURI
        req_path = "/"+req_path
    return req_path

unescape_re = re.compile(r"%([0-9a-fA-F][0-9a-fA-F])")
normalize_re = re.compile(r"([\0-\x20\x7f-\xff])")
def normalize_path(path):
    """Normalise URI path so that plain string compare can be used.

    >>> normalize_path("%19\xd3%Fb%2F%25%26")
    '%19%D3%FB%2F%25&'
    >>> 

    In normalised form, all non-printable characters are %-escaped, and all
    printable characters are given literally (not escaped).  All remaining
    %-escaped characters are capitalised.  %25 and %2F are special-cased,
    because they represent the printable characters "%" and "/", which are used
    as escape and URI path separator characters respectively.

    """
    def unescape_fn(match):
        x = string.upper(match.group(1))
        if x == "2F" or x == "25":
            return "%%%s" % (x,)
        else:
            # string.atoi deprecated in 2.0, but 1.5.2 int function won't do
            # radix conversion
            return struct.pack("B", string.atoi(x, 16))
    def normalize_fn(match):
        return "%%%02X" % ord(match.group(1))
    path = unescape_re.sub(unescape_fn, path)
    path = normalize_re.sub(normalize_fn, path)
    return path


class Cookies:
    """Collection of HTTP cookies.

    The major methods are extract_cookies and add_cookie_header; these are all
    you are likely to need.  In fact, you probably don't even need to know
    about this class: use the cookie-aware extensions to the urllib2 callables
    provided by this module: urlopen in particular (and perhaps also
    build_opener, install_opener, HTTPHandler, HTTPSHandler (only if your
    Python has https support compiled in), and HTTPRedirectHandler).

    You can give a sequence of domain names from which we never accept cookies,
    nor return cookies to.  Use the blocked_domains argument to the
    constructor, or use the blocked_domains and set_blocked_domains methods.
    Note that all domains which end with elements of blocked_domains are
    blocked.  IP addresses are an exception, and must match exactly.  For
    example, if blocked_domains == ["acme.com", "roadrunner.org",
    "192.168.1.2", ".168.1.2"], then "www.acme.com", "acme.com",
    "roadrunner.org" and 192.168.1.2 are all blocked, but 193.168.1.2 is not
    blocked.

    Methods:

    Cookies(filename=None,
            autosave=False, ignore_discard=False,
            hide_cookie2=False, netscape_only=False,
            blocked_domains=None)
    add_cookie_header(request)
    extract_cookies(response, request)
    set_cookie(version, key, val, path, domain, port, path_spec,
               secure, maxage, discard, rest=None)
    blocked_domains()
    set_blocked_domains(blocked_domains)
    save(filename=None)
    load(filename=None)
    revert(filename=None)
    clear(domain=None, path=None, key=None)
    clear_temporary_cookies()
    scan(callback)
    as_string(skip_discard=False)  (str(cookie) also works)


    Public attributes

    cookies: a three-level dictionary [domain][path][key]; you probably don't
     need to use this
    filename: default name of file in which to load and save cookies
    autosave: save cookies on instance destruction
    ignore_discard: save even cookies that are requested to be discarded

    """
    non_word_re = re.compile(r"\W")
    quote_re = re.compile(r"([\"\\])")
    port_re = re.compile(r"^_?\d+(?:,\d+)*$")
    domain_re = re.compile(r"[^.]*")
    dots_re = re.compile(r"^\.+")

    magic_re = r"^\#LWP-Cookies-(\d+\.\d+)"

    def __init__(self, filename=None,
                 autosave=False, ignore_discard=False,
                 hide_cookie2=False, netscape_only=False,
                 blocked_domains=None, delayload=False):
        """
        filename: name of file in which to save and restore cookies
        autosave: save to file during destruction
        ignore_discard: save even cookies that the server indicates should be
         discarded
        hide_cookie2: don't add Cookie2 header to requests (the presence of
         this header indicates to the server that we understand RFC 2965
         cookies)
        netscape_only: switch off RFC 2965 cookie handling altogether (implies
         hide_cookie2 also)
        blocked_domains: sequence of domain names that we never accept cookies
         from, nor return cookies to
        delayload: request that cookies are lazily loaded per-domain from disk;
         this is only a hint since this only affects performance, not behaviour
         (unless the cookies on disk are changing); a Cookies object may ignore
         it (in fact, only MSIECookies lazily loads cookies at the moment)

        If a filename is given and refers to a valid cookies file (as defined
        by the class documentation), all cookies are loaded from it.  This will
        happen immediately, unless delayload is true.  An invalid cookies file
        will NOT cause an exception to be raised here.

        Future keyword arguments might include (not yet implemented):

        max_cookies=None
        max_cookies_per_domain=None
        max_cookie_size=None

        """
        self.autosave = autosave
        self.filename = filename
        self.ignore_discard = ignore_discard
        self._hide_cookie2 = hide_cookie2
        self._disallow_2965 = netscape_only
        if self._disallow_2965:
            self._hide_cookie2 = True
        self._delayload = delayload

        if blocked_domains is not None:
            self._blocked_domains = tuple(blocked_domains)
        else:
            self._blocked_domains = ()
        self.cookies = {}

        if filename is None:
            if autosave is None:
                raise ValueError, \
                      "a filename must be given if autosave is requested"
        else:
            try: self.load(filename)
            except IOError: pass

    def blocked_domains(self):
        """Return the sequence of blocked domains (as a tuple)."""
        return self._blocked_domains
    def set_blocked_domains(self, blocked_domains):
        """Set the sequence of blocked domains."""
        self._blocked_domains = tuple(blocked_domains)

    def _is_blocked(self, domain):
        for blocked_domain in self._blocked_domains:
            if liberal_domain_match(domain, blocked_domain):
                return True
        return False

    def __len__(self):
        """Return number of contained cookies."""
        count = [0]
        def callback(args, c=count): c[0] = c[0] + 1
        self.scan(callback)
        return count[0]

    def _return_cookie_path_ok(self, path, req_path):
        """Decide whether cookie should be returned to server, given only path.

        If cookie should be returned to server, return True.  Otherwise, return
        False.

        path: path set in cookie
        req_path: request path

        """
        # this is identical for Netscape and RFC 2965
        debug("- checking cookie path=%s" % path)
        if not startswith(req_path, path):
            debug("  %s does not path-match %s" % (req_path, path))
            return False
        return True

    def _return_cookie_ok(self, domain, path, key, value,
                          request, redirect, now):
        """Decide whether cookie should be returned to server, given all info.

        If cookie should be returned to server, return true.  Otherwise, return
        false.

        """
        # path has already been checked by _return_cookie_path_ok
        # domain should be OK thanks to the algorithm in add_cookie_header
        #  that found this cookie in the first place
        (version, val, port, path_specified,
         secure, expires, discard, rest) = value
        debug(" - checking cookie %s=%s" % (key, val))
        secure_request = (request.get_type() == "https")
        req_port = request.port
        if req_port is None:
            req_port = "80"

        if self._disallow_2965 and int(version) > 0:
            debug("   RFC 2965 cookie disallowed by user")
            return False
        if redirect and int(version) > 0:
            debug("   RFC 2965 cookie disallowed during redirect")
            return False
        if secure and not secure_request:
            debug("   not a secure request")
            return False
        if expires and expires < now:
            debug("   expired")
            return False
        if port:
            for p in string.split(port, ","):
                if p == req_port:
                    break
            else:
                debug("   request port %s does not match cookie port %s" % (
                    req_port, port))
                return False
        if int(version) > 0 and self._is_netscape_domain:
            debug("   domain %s applies to Netscape-style cookies only" %
                  domain)
            return False
        if self._is_blocked(domain):
            debug("   domain %s is in user block-list")
            return False

        ehn = request_host(request)
        if string.find(ehn, ".") == -1:
            ehn = ehn + ".local"
        if int(version) > 0:
            # origin server effective host name should domain-match
            # domain attribute of cookie
            assert domain_match(ehn, domain)
        else:
            assert endswith(ehn, domain)

        debug("   it's a match")
        return True

    def _get_cookie_attributes(self, cookies, domain, request,
                               req_path, redirect, now):
        """Return a list of cookie-attributes to be returned to server.

        like ['$Path="/"', ...]

        The $Version attribute is also added when appropriate (currently only
        once per request).

        Also adds Cookie2 header to request, unless hide_cookie2 argument
        to Cookies constructor was true.

        """
        # Add cookies in order of most specific path first (i.e. longest
        # path first).
        paths = cookies.keys()
        def decreasing_size(a, b): return cmp(len(b), len(a))
        paths.sort(decreasing_size)

        cattrs = []
        for path in paths:

            if not self._return_cookie_path_ok(path, req_path):
                continue

            for key, value in cookies[path].items():
                if not self._return_cookie_ok(domain, path, key, value,
                                              request, redirect, now):
                    continue

                (version, val, port, path_specified,
                 secure, expires, discard, rest) = value

                # set version of Cookie header, and add Cookie2 header
                # XXX
                # What should it be if multiple matching Set-Cookie headers
                #  have different versions themselves?
                # Answer: this is undecided as of 2003-04-29 -- will be
                #  settled when RFC 2965 errata appears.
                if not self._version_has_been_set:
                    self._version_has_been_set = True
                    if (int(version) > 0):
                        cattrs.append("$Version=%s" % version)
                    elif not self._hide_cookie2:
                        # advertise that we know RFC 2965
                        request.add_header("Cookie2", '$Version="1"')

                # quote cookie value if necessary
                # (not for Netscape protocol, which already has any quotes
                #  intact, due to the poorly-specified Netscape Cookie: syntax)
                if self.non_word_re.search(val) and int(version):
                    val = self.quote_re.sub(r"\\\1", val)

                # add cookie-attributes to be returned in Cookie header
                cattrs.append("%s=%s" % (key, val))
                if int(version) > 0:
                    if path_specified:
                        cattrs.append('$Path="%s"' % path)
                    if startswith(domain, "."):
                        cattrs.append('$Domain="%s"' % domain)
                    if port is not None:
                        p = "$Port"
                        if port != "":
                            p = p + ('="%s"' % port)
                        cattrs.append(p)

        return cattrs

    def add_cookie_header(self, request, redirect=False):
        """Add correct Cookie: header to request (urllib2.Request object).

        The Cookie2 header is also added unless the hide_cookie2 argument
        to the Cookies constructor was false.

        The request object (usually a urllib2.Request instance) must support
        the methods get_full_url, get_host, get_type and add_header, as
        documented by urllib2, and the attributes headers (a mapping containing
        the request's HTTP headers) and port (the port number).

        If redirect is true, it will be assumed that the request is to a
        redirect URL, and appropriate action will be taken.  This has no effect
        for Netscape cookies.  At the moment, adding of RFC 2965 cookies is
        switched off entirely if the redirect argument is true: this will
        change in future, to follow the RFC, which allows some cookie use
        during redirections.

        """
        now = time()

        # origin server effective host name
        erhn = string.lower(request_host(request))
        if string.find(erhn, ".") == -1:
            erhn = erhn + ".local"

        req_path = request_path(request)

        cattrs = []  # cookie-attributes to be put in the "Cookie" header

        self._version_has_been_set = False
        self._is_netscape_domain = False

        # Start with origin server effective host name (erhn -- say
        # foo.bar.baz.com), and check all possible domains (foo.bar.baz.com,
        # .bar.baz.com, bar.baz.com) for cookies.  For resulting domains that
        # begin with a dot, this should ensure we have an RFC 2965
        # domain-match.  For domains that don't start with a dot, we still
        # have a match for Netscape protocol, but not for RFC 2965; in this
        # case, self._is_netscape_domain is true.
        domain = erhn
        while string.find(domain, ".") != -1:
            # Do we have any cookies to send back to the server for this
            # domain?
            debug("Checking %s for cookies" % domain)
            cookies = self.cookies.get(domain)
            if cookies is None:
                # XXX I *think* the only reason why we'd get a domain back
                # from _next_domain that doesn't domain-match the erhn is that
                # domain is in fact an IP address, so check for that.
                if IPV4_RE.search(domain):
                    # no point in continuing, since IP addresses must string-
                    # compare equal in order to domain-match
                    break
                domain = self._next_domain(domain)
                continue

            # What cookie-attributes do we need to send back?
            # (get_cookie_attributes also, as necessary, adds the $Version
            # attribute to the returned list, and the Cookie2 header to
            # request)
            attrs = self._get_cookie_attributes(
                cookies, domain, request, req_path, redirect, now)
            cattrs.extend(attrs)

            domain = self._next_domain(domain)

        if cattrs:
            request.add_header("Cookie", string.join(cattrs, "; "))

    def _next_domain(self, domain):
        """Return next domain string in which to look for stored cookies.

        Domain string must contain at least one dot.

        I say 'domain string' rather than 'domain name' because many of these
        domain strings start with a dot, unlike real DNS domain names.

        """
        # Return a more general domain, alternately stripping leading name
        # components and leading dots.  When this results in a domain with
        # no leading dot, it is for Netscape cookie compatibility only:
        #
        # a.b.c.net     Any cookie
        # .b.c.net      Any cookie
        # b.c.net       Netscape cookie only
        # .c.net        Any cookie
        # (further stripping shouldn't match any cookies that we stored)

        if startswith(domain, "."):
            domain = domain[1:]
            self._is_netscape_domain = True
        else:
            domain = self.domain_re.sub("", domain, 1)
            self._is_netscape_domain = False
        return domain

    def _set_cookie_if_ok(self, key, val, hash, rest, request,
                          have_ns_cookies, redirect):
        """Decide whether cookie should be set, and if it should, set it."""
        # find request host, path and port
        # in fact we need the effective request-host name here:
        erhn = string.lower(request_host(request))
        if string.find(erhn, ".") == -1:
            erhn = erhn + ".local"
        req_path = request_path(request)
        req_port = request.port
        if req_port is None:
            req_port = "80"
        else:
            req_port = str(req_port)

        # Now get the cookie info from hash, checking whether cookie is ok and
        # setting defaults.

        max_age = hash.get("max-age")
        version = hash.get("version")
        domain = hash.get("domain")
        path = hash.get("path")

        if max_age is not None:
            max_age = float(max_age)

        # check version
        if version is None:
            # Version is always set to 0 by _parse_ns_attrs if it's a Netscape
            # cookie, so this must be an invalid RFC 2965 cookie.
            debug("Set-Cookie2 without version attribute disallowed (%s=%s)" % (key, val))
            return
        if int(version) > 0:
            if redirect:
                debug("Setting RFC 2965 cookie during redirect disallowed")
                return
            if self._disallow_2965:
                debug("Setting RFC 2965 cookie disallowed by user")
                return

        # check path
        path_specified = False
        if path is not None and path != "":
            path_specified = True
            path = normalize_path(path)
            if not have_ns_cookies and not startswith(req_path, path):
                debug("Path attribute %s is not a prefix of request path %s" %
                      (path, req_path))
                return
        else:
            path = req_path
            i = string.rfind(path, "/")
            if i != -1:
                if int(version) == 0:
                    # Netscape spec parts company from reality here
                    path = path[:i]
                    #path = re.sub(r"/[^/]*$", "", path, 1)
                else:
                    path = path[:i+1]
            if len(path) == 0: path = "/"

        # check domain
        if (domain is None or
            # XXX is this the best hack for Netscape protocol?  We need
            # *something*, because explicitly-set cookie domain like acme.com
            # must match erhn acme.com, whereas RFC 2965 logic below would
            # rewrite domain attribute to .acme.com, erroneously resulting in
            # no match.
            (int(version) == 0 and (domain == erhn or domain == "."+erhn))):
            domain = erhn
        else:
            if not startswith(domain, "."):
                # Netscape protocol doesn't ask for this, but doesn't make
                # sense otherwise (two-component domain names, like acme.com,
                # could never set cookies if we didn't do this).
                domain = ".%s" % domain
            if startswith(domain, "."):
                undotted_domain = domain[1:]
            else:
                undotted_domain = domain
            nr_embedded_dots = string.count(undotted_domain, ".")
            if nr_embedded_dots == 0 and domain != ".local":
                debug("Non-local domain %s contains no embedded dot" % domain)
                return
            if int(version) == 0:
                # XXX maybe should just do RFC 2965 domain-match here?
                if IPV4_RE.search(domain):
                    debug("IP-address %s illegal as domain" % domain)
                    return
                if not endswith(erhn, domain):
                    debug("Effective request-host %s does not end with %s" % (
                          erhn, domain))
                    return
            else:
                if not domain_match(erhn, domain):
                    debug("Effective request-host %s does not domain-match "
                          "%s" % (erhn, domain))
                    return
                host_prefix = erhn[:-len(domain)]
                if string.find(host_prefix, ".") != -1 and int(version) > 0:
                    debug("Host prefix %s for domain %s contains a dot" % (
                        host_prefix, domain))
                    return
        if self._is_blocked(domain):
            debug("Domain %s is in user block-list")
            return

        # check port
        if hash.has_key("port"):
            port = hash["port"]
            if port is None:
                # Port attr is present, but has no value: need to remember
                # request port so we can ensure that cookie is only sent
                # back on that port.
                port = req_port
            else:
                port = re.sub(r"\s+", "", port)
                for p in string.split(port, ","):
                    try:
                        int(p)
                    except ValueError:
                        debug("Bad port %s (not numeric)" % port)
                        return
                    if p == req_port:
                        break
                else:
                    debug("Request port (%s) not found in %s" % (
                        req_port, port))
                    return
        else:
            # No port attr present, so will be able to send back this
            # cookie on any port.
            port = None

        all_attrs = hash.copy()
        all_attrs.update(rest)

        if self._set_cookie_ok(all_attrs):
            h = hash.get
            self.set_cookie(h("version"), key, val, path, domain, port,
                            path_specified, h("secure"), max_age,
                            h("discard"), rest)

    def _parse_ns_attrs(self, ns_set_strings):
        """Ad-hoc parser for Netscape protocol cookie-attributes.

        The old Netscape cookie format for Set-Cookie

        http://www.netscape.com/newsref/std/cookie_spec.html

        can for instance contain an unquoted "," in the expires field, so we
        have to use this ad-hoc parser instead of split_header_words.

        """
        now = time()
        ns_set = []
        for attrs_string in ns_set_strings:
            ns_attrs = []
            expires = False
            for param in re.split(r";\s*", attrs_string):
                if string.rstrip(param) == "": continue
                if "=" not in param:
                    k, v = string.rstrip(param), None
                    if k != "secure":
                        debug("unrecognised Netscape protocol boolean "
                              "cookie-attribute '%s'" % k)
                else:
                    k, v = re.split(r"\s*=\s*", param, 1)
                    v = string.rstrip(v)
                lc = string.lower(k)
                if lc == "expires":
                    # convert expires date to max-age delta
                    etime = str2time(v)
                    if etime is not None:
                        ns_attrs.append(("max-age", etime - now))
                        expires = True
                else:
                    ns_attrs.append((k, v))

            # XXX commented out in original Perl -- should it be here,
            #   or not?
            #ns_attrs.append(("port", req_port))
            #  anyway, it should really be this, if anything at all:
            #ns_attrs.append(("port", None))

            # XXX surely this is wrong: RFC 2965 *also* states that a
            # missing expiry date means should be set to expire -- so
            # why are we only doing this for Netscape cookies??
            if not expires: ns_attrs.append(("discard", None))
            ns_attrs.append(("version", "0"))
            ns_set.append(ns_attrs)

        return ns_set

    def _normalized_cookie_info(self, set):
        """Return list of tuples containing normalised cookie information.

        Tuples are name, value, hash, rest, where name and value are the cookie
        name and value, hash is a dictionary containing the most important
        cookie-attributes (discard, secure, version, max-age, domain, path and
        port) and rest is a dictionary containing the rest of the cookie-
        attributes.

        """
        cookie_tuples = []

        boolean_attrs = "discard", "secure"
        value_attrs = "version", "max-age", "domain", "path", "port"
        #print "set", set

        for cookie_attrs in set:
            name, value = cookie_attrs[0]
            debug("Attempt to set cookie %s=%s" % (name, value))

            # Build dictionary of common cookie-attributes (hash) and
            # dictionary of other cookie-attributes (rest).
            hash = {}
            rest = {}
            for k, v in cookie_attrs[1:]:
                lc = string.lower(k)
                # don't lose case distinction for unknown fields
                if (lc in value_attrs) or (lc in boolean_attrs):
                    k = lc
                if k in boolean_attrs:
                    if v is None:
                        # set boolean default
                        # Note that this is a default for the case where the
                        # cookie-attribute *is* present, but has no value
                        # (like "discard", as contrasted with "path=/").
                        # If the cookie-attribute *isn't* present (if "path"
                        # is missing, for example), the value stored for it
                        # will always be false.
                        v = True
                if hash.has_key(k):
                    # only first value is significant
                    continue
                if k == "domain":
                    # RFC 2965 section 3.3.3
                    v == string.lower(v)
                if (k in value_attrs) or (k in boolean_attrs):
                    hash[k] = v
                else:
                    rest[k] = v

            cookie_tuples.append((name, value, hash, rest))

        return cookie_tuples

    def extract_cookies(self, response, request, redirect=0):
        """Extract cookies from response, where allowable given the request.

        Look for allowable Set-Cookie: and Set-Cookie2: headers in the response
        object passed as argument.  Any of these headers that are found are
        used to update the state of the object (subject to the _set_cookie_ok
        method's approval).

        The response object (which will usually be the result of a call to
        ClientCookie.urlopen, or similar) must support the methods read,
        readline, readlines, fileno, close and info, as described in the
        documentation for the standard urllib and urllib2 modules.  In
        particular, these methods work like those on standard file objects,
        with the exception of info, which returns a mimetools.Message object.

        The request object (usually a urllib2.Request instance) must support
        the methods get_full_url and get_host, as documented by urllib2, and
        the attributes headers (a mapping containing the request's HTTP
        headers) and port (the port number).

        If redirect is true, it will be assumed that the request was to a
        redirect URL, and appropriate action will be taken.  This has no effect
        for Netscape cookies.  At the moment, extraction of RFC 2965 cookies is
        switched off entirely if the redirect argument is true: this will
        change in future, to follow the RFC, which allows some cookie use
        during redirections.

        """
        # get cookie-attributes for RFC 2965 and Netscape protocols
        headers = response.info()
        rfc2965_strings = getheaders(headers, "Set-Cookie2")
        ns_strings = getheaders(headers, "Set-Cookie")

        if ((not rfc2965_strings and not ns_strings) or
            (not ns_strings and self._disallow_2965)):
            return  # no cookie headers: quick exit

        # Parse out cookie-attributes from RFC 2965 Set-Cookie2 headers.
        set = split_header_words(rfc2965_strings)
        cookie_tuples = self._normalized_cookie_info(set)

        have_ns_cookies = False
        if ns_strings:
            #print ns_strings
            # Parse out cookie-attributes from Netscape Set-Cookie headers.
            ns_set = self._parse_ns_attrs(ns_strings)
            ns_cookie_tuples = self._normalized_cookie_info(ns_set)

            # Look for Netscape cookies (from a Set-Cookie headers) that match
            # corresponding RFC 2965 cookies (from Set-Cookie2 headers).
            # For each match, keep the RFC 2965 cookie and ignore the Netscape
            # cookie (RFC 2965 section 9.1).
            if not self._disallow_2965:
                # Build a dictionary of cookies that are present in Set-Cookie2
                # headers.
                rfc2965_cookies = {}
                for name, value, hash, rest in cookie_tuples:
                    key = hash.get("domain", ""), hash.get("path", ""), name
                    rfc2965_cookies[key] = None

                def no_matching_rfc2965(ns_cookie_tuple,
                                        rfc2965_cookies=rfc2965_cookies):
                    name, value, hash, rest = ns_cookie_tuple
                    key = hash.get("domain", ""), hash.get("path", ""), name
                    if not rfc2965_cookies.has_key(key):
                        return True
                ns_cookie_tuples = filter(no_matching_rfc2965, ns_cookie_tuples)

            if ns_cookie_tuples:
                have_ns_cookies = True
                cookie_tuples.extend(ns_cookie_tuples)

        for name, value, hash, rest in cookie_tuples:
            self._set_cookie_if_ok(name, value, hash, rest,
                                   request, have_ns_cookies, redirect)

    def _set_cookie_ok(self, headers):
        """Return False if the cookie should not be set.

        This is intended for overloading by subclasses.  Do not call this
        method.

        The cookie has already been approved by the extract_cookies method by
        the time it gets here, so there's no need to reimplement the standard
        acceptance rules.

        headers: dictionary containing HTTP "Cookie" and "Cookie2" headers.

        """
        return True

    def set_cookie(self, version, key, val, path, domain, port, path_spec,
                   secure, max_age, discard, rest=None):
        """Add a cookie.

        The version, key, val, path, domain and port arguments are strings.
        The path_spec, secure, discard arguments are boolean values.  The
        max_age argument is a number indicating number of seconds that this
        cookie will live.  A value <= 0 will delete this cookie.  The
        dictionary rest defines various other cookie-attributes like "Comment"
        and "CommentURL".

        """
##         print "set_cookie:"
##         print " version", version
##         print " key", key
##         print " val", val
##         print " path", path
##         print " domain", domain
##         print " port", port
##         print " path_spec", path_spec
##         print " secure", secure
##         print " max_age", max_age
##         print " discard", discard
##         print " rest", rest
##         if rest: print " rest is not empty"
##         else: print " rest is empty"

        if path is None or not startswith(path, "/"):
            raise ValueError, "Illegal path: '%s'" % path
        if key is None or key == "" or startswith(key, "$"):
            raise ValueError, "Illegal key: '%s'" % key

        if port is not None:
            if not self.port_re.search(port):
                msg = "Illegal port: '%s'" % port
                debug(msg)
                raise ValueError, msg

        # normalise case, as per RFC 2965 section 3.3.3
        # XXX RFC 1034 says should preserve case, but use case-insensitive
        # string compare.  This would complicate things here, because we're
        # using a dictionary to store cookies by domain.  I don't think this
        # really matters here.
        domain = string.lower(domain)

        # If no Max-Age cookie-attribute, cookie will be set to discarded. This
        # will happen on next call to clear_temporary_cookies, or on next save.
        expires = 0
        if max_age is not None:
            if max_age <= 0:
                try:
                    del self.cookies[domain][path][key]
                except KeyError:
                    pass
                else:
                    debug("Expiring cookie, "
                          "domain='%s', path='%s', key='%s'" % (
                        domain, path, key))
                return
            expires = str(time() + float(max_age))

        if version is None:
            version = "0"

        debug("Set cookie %s=%s" % (key, val))
        self._set_cookie(
            domain, path, key,
            [version, val, port, path_spec, secure, expires, discard,
             rest])

    def _set_cookie(self, domain, path, key, cookie_info):
        c = self.cookies
        if not c.has_key(domain): c[domain] = {}
        c2 = c[domain]
        if not c2.has_key(path): c2[path] = {}
        c3 = c2[path]
        c3[key] = cookie_info

    def save(self, filename=None):
        """Save cookies to a file.

        The file is overwritten if it already exists, thus wiping all its
        cookies.  Saved cookies can be restored later using the load or revert
        methods.  If filename is not specified, the name specified during
        construction (if any) is used.  Cookies set to be discarded are only
        saved if the ignore_discard attribute is set.

        The Cookies base class saves a sequence of "Set-Cookie3" lines.
        "Set-Cookie3" is the format used by the libwww-perl libary, not known
        to be compatible with any browser.  The NetscapeCookies subclass can be
        used to save in a format compatible with the Netscape browser.

        The implementation of this method in the Cookies base class always
        saves cookies which have expired by outliving their Max-Age
        cookie-attribute (unlike the NetscapeCookies implementation).  This may
        change in future.

        """
        if filename is None:
            if self.filename is not None: filename = self.filename
            else: raise ValueError, MISSING_FILENAME_TEXT
        f = open(filename, "w")
        f.write("#LWP-Cookies-1.0\n")
        f.write(self.as_string(not self.ignore_discard))
        f.close()
        self.filename = filename

    def load(self, filename=None):
        """Load cookies from a file.

        Old cookies are kept unless overwritten by newly loaded ones.

        The named file must be in the format understood by the class, or
        IOError will be raised.  This format will be identical to that written
        by the save method, unless the load format is not sufficiently well
        understood (as is the case for MSIECookies).

        Note for subclassers: overridden versions of this method should not
        alter the object's state other than by setting self.filename (if and
        only if the load was successful) and calling self.set_cookie.

        """
        if filename is None:
            if self.filename is not None: filename = self.filename
            else: raise ValueError, MISSING_FILENAME_TEXT
        f = open(filename)
        magic = f.readline()
        if not re.search(self.magic_re, magic):
            msg = "%s does not seem to contain cookies" % filename
            raise IOError, msg

        boolean_attrs = "path_spec", "secure", "discard"
        value_attrs = "version", "port", "path", "domain", "expires"

        try:
            while 1:
                line = f.readline()
                if line == "": break
                header = "Set-Cookie3:"
                if not startswith(line, header):
                    continue
                line = string.strip(line[len(header):])
                for cookie in split_header_words([line]):
                    key, val = cookie[0]
                    hash = {}
                    rest = {}
                    for name in boolean_attrs:
                        hash[name] = False
                    for k, v in cookie[1:]:
                        if k in boolean_attrs:
                            if v is None: v = True
                            hash[k] = v
                        elif k in value_attrs:
                            hash[k] = v
                        else:
                            rest[k] = v
                    h = hash.get
                    expires = h("expires")
                    if expires is not None:
                        expires = str2time(expires)
                    value = [h("version"), val, h("port"), h("path_spec"),
                             h("secure"), expires, h("discard"), rest]
                    self._set_cookie(h("domain"), h("path"), key, value)
        except:
            type = sys.exc_info()[0]
            if issubclass(type, IOError):
                raise
            else:
                raise IOError, "invalid Set-Cookie3 format file %s" % filename
        self.filename = filename

    def revert(self, filename=None):
        """Clear all cookies and reload cookies from a saved file.

        Raises IOError if reversion is not successful; the object's state will
        not be altered if this happens.

        """
        if filename is None:
            if self.filename is not None: filename = self.filename
            else: raise ValueError, MISSING_FILENAME_TEXT
        old_state = copy.deepcopy(self.cookies)
        self.clear()
        try:
            self.load()
        except IOError:
            self.cookies = old_state
            raise

    def clear(self, domain=None, path=None, key=None):
        """Clear some cookies.

        Invoking this method without arguments will clear all cookies.  If
        given a single argument, only cookies belonging to that domain will be
        removed.  If given two arguments, cookies belonging to the specified
        path within that domain are removed.  If given three arguments, then
        the cookie with the specified key, path and domain is removed.

        Raises KeyError if no matching cookie exists.

        """
        if key is not None:
            if (domain is None) or (path is None):
                raise ValueError, \
                      "domain and path must be given to remove a cookie by key"
            del self.cookies[domain][path][key]
        elif path is not None:
            if domain is None:
                raise ValueError, \
                      "domain must be given to remove cookies by path"
            del self.cookies[domain][path]
        elif domain is not None:
            del self.cookies[domain]
        else:
            self.cookies = {}

    def clear_temporary_cookies(self):
        """Discard all temporary cookies.

        Scans for all cookies held by object having either no Max-Age
        cookie-attribute or a true discard flag.  RFC 2965 says you should call
        this when the user agent shuts down.

        """
        def callback(args, self=self):
            if (args[9] or not args[8]):
                # "Discard" flag set or there was no Max-Age cookie-attribute.
                # clear the cookie, by setting negative Max-Age
                args[8] = -1
                apply(self.set_cookie, args)
        self.scan(callback)

    def __del__(self):
        if self.autosave: self.save()

    def scan(self, callback):
        """Apply supplied function to each stored cookie.

        The callback function will be invoked with a sequence argument:

          index  content
          --------------
          0      version
          1      key
          2      value
          3      path
          4      domain
          5      port
          6      path_specified
          7      secure
          8      expires
          9      discard
         10      dictionary containing other cookie-attributes, eg. "Comment"

        """
        domains = self.cookies.keys()
        domains.sort()
        for domain in domains:
            paths = self.cookies[domain].keys()
            paths.sort()
            for path in paths:
                for key, value in self.cookies[domain][path].items():
                    (version, val, port, path_specified,
                     secure, expires, discard, rest) = value
                    if rest is None:
                        rest = {}
                    callback([version, key, val, path, domain, port,
                        path_specified, secure, expires, discard, rest])

    def __str__(self): return self.as_string()

    def as_string(self, skip_discard=False):
        """Return cookies as a string of "\n"-separated "Set-Cookie3" headers.

        If skip_discard is true, it will not return lines for cookies with the
        Discard cookie-attribute.

        str(cookies) also works.

        """
        result = []
        def callback(args, result=result, skip_discard=skip_discard):
            (version, key, val, path, domain, port,
             path_specified, secure, expires, discard, rest) = args
            if discard and skip_discard: return
            h = [(key, val),
                 ("path", path),
                 ("domain", domain)]
            if port is not None: h.append(("port", port))
            if path_specified: h.append(("path_spec", None))
            if secure: h.append(("secure", None))
            if expires: h.append(("expires", time2isoz(float(expires))))
            if discard: h.append(("discard", None))
            keys = rest.keys()
            keys.sort()
            for k in keys:
                h.append((k, str(rest[k])))
            h.append(("version", version))
            result.append(("Set-Cookie3: %s" % (join_header_words([h]),)))
        self.scan(callback)
        return string.join(result+[""], "\n")


class NetscapeCookies(Cookies):
    """
    This class differs from Cookies only in the format it uses to save and load
    cookies to and from a file.  This class uses the Netscape `cookies.txt'
    format.

    Note that the Netscape format will lose information on saving and
    restoring.  In particular, the port number and cookie protocol version
    information is lost.  XXX path_specified, discard??

    Unlike the Cookies base class, this class currently checks cookie expiry
    times on saving, and expires cookies appropriately.  Cookies instead waits
    until you call clear_temporary_cookies.  This may change in future.

    """
    magic_re = "#( Netscape)? HTTP Cookie File"
    header = """\
    # Netscape HTTP Cookie File
    # http://www.netscape.com/newsref/std/cookie_spec.html
    # This is a generated file!  Do not edit.

"""

    def load(self, filename=None):
        if filename is None:
            if self.filename is not None: filename = self.filename
            else: raise ValueError, MISSING_FILENAME_TEXT
        cookies = []
        f = open(filename)
        magic = f.readline()
        if not re.search(self.magic_re, magic):
            f.close()
            raise IOError, (
                "%s does not look like a Netscape format cookies file" % (
                filename,))
        now = time()

        try:
            while 1:
                line = f.readline()
                if line == "": break

                # last field may be absent, so keep any trailing tab
                line = string.lstrip(line)
                if endswith(line, "\n"): line = line[:-1]

                # skip comments and blank lines XXX what is $ for?
                if (startswith(line, "#") or startswith(line, "$") or
                    line == ""):
                    continue

                domain, bool1, path, secure, expires, key, val = \
                        string.split(line, "\t")
                secure = (secure == "TRUE")
                self.set_cookie(None, key, val, path, domain, None,
                                0, secure, float(expires)-now, 0)
        except:
            type = sys.exc_info()[0]
            if issubclass(type, IOError):
                raise
            else:
                raise IOError, "invalid Netscape format file %s" % filename
        self.filename = filename

    def save(self, filename=None):
        if filename is None:
            if self.filename is not None: filename = self.filename
            else: raise ValueError, MISSING_FILENAME_TEXT
        f = open(filename, "w")

        f.write(self.header)
        now = time()
        debug("Saving Netscape cookies.txt file")
        def callback(args, f=f, now=now, self=self):
            (version, key, val, path, domain, port,
             path_specified, secure, expires, discard, rest) = args
            expires = float(expires)
            if discard and not self.ignore_discard:
                debug("   Not saving %s: marked for discard" % key)
                return
            if not expires: expires = 0
            if now > expires:
                debug("   Not saving %s: expired" % key)
                return
            if secure: secure = "TRUE"
            else: secure = "FALSE"
            if startswith(domain, "."): bool = "TRUE"
            else: bool = "FALSE"
            f.write(
                string.join([domain, bool, path, secure,
                             str(expires), key, val], "\t")+"\n")

        self.scan(callback)
        f.close()
        self.filename = filename


def binary_to_char(c): return "%02X" % ord(c)
def binary_to_str(d): return string.join(map(binary_to_char, list(d)), "")

class MSIECookies(Cookies):
    """
    This class differs from Cookies only in the format it uses to load cookies
    from a file.

    MSIECookies can read the cookie files of Microsoft Internet Explorer (MSIE)
    for Windows, versions 5 and 6, on Windows NT and XP respectively.  Other
    configurations may also work, but are untested.  Saving cookies in MSIE
    format is NOT supported.  If you save cookies, they'll be in the usual
    Set-Cookie3 format, which you can read back in using an instance of the
    plain old Cookies class.  Don't call the save method without explicitly
    supplying a filename, because you may end up clobbering your MSIE cookies
    index file!  For this reason, autosave is not supported by this class, and
    it will raise NotImplementedError if you try to use it.

    You should be able to have LWP share Internet Explorer's cookies like
    this:

    cookies = MSIECookies(delayload=1)
    opener = ClientCookie.build_opener(ClientCookie.HTTPHandler(cookies))
    response = opener.open("http://foo.bar.com/")

    Note that the implmentation of the delayload feature mucks around with the
    data stored in the MSIECookies.cookies dictionary -- the data will be bogus
    unless the particular cookie you're looking at happens to have been loaded.
    You probably shouldn't be using the cookies attribute anyway.

    Additional methods:

    load_cookie_data(filename)

    """
    magic = "Client UrlCache MMF Ver 5.2"
    padding = "\x0d\xf0\xad\x0b"

    msie_domain_re = re.compile(r"^([^/]+)(/.*)$")
    cookie_re = re.compile("Cookie\:.+\@([\x21-\xFF]+).*?"
                           "(.+\@[\x21-\xFF]+\.txt)")

    # path under HKEY_CURRENT_USER to look for location of index.dat
    reg_path = r"software\microsoft\windows" \
               r"\currentversion\explorer\shell folders"
    reg_key = "Cookies"

    win32_epoch = 0x019db1ded53e8000L  # 1970 Jan 01 00:00:00 in Win32 FILETIME

    def __init__(self, filename=None, autosave=False, *args, **kwargs):
        """
        The filename argument should be the cookies 'index.dat' file.  This
        filename is looked up in the registry if no filename is supplied.

        """
        if autosave:
            raise NotImplementedError, "MSIECookies does not support autosave"

        if filename is None:
            filename = self._regload_current_user(self.reg_path, self.reg_key)
            if filename is not None:
                filename = os.path.normpath(
                    os.path.join(filename, "INDEX.DAT"))

        apply(Cookies.__init__, (self, filename, autosave)+args, kwargs)

    def __del__(self): pass

    def __setattr__(self, name, value):
        if name == "autosave" and value:
            raise NotImplementedError, "MSIECookies does not support autosave"
        self.__dict__[name] = value

    def _regload_current_user(self, path, leaf):
        key = _winreg.OpenKey(_winreg.HKEY_CURRENT_USER, path, 0, _winreg.KEY_ALL_ACCESS)
        try:
            value = _winreg.QueryValueEx(key, leaf)[0]
        except WindowsError:
            value = None
        return value

    def _epoch_time_offset_from_win32_filetime(self, filetime):
        """Convert from win32 filetime to seconds-since-epoch value.

        MSIE stores create and expire times as Win32 FILETIME, which is 64
        bits of 100 nanosecond intervals since Jan 01 1601.

        Cookies code expects time in 32-bit value expressed in seconds since
        the epoch (Jan 01 1970).

        """
        if filetime < self.win32_epoch:
            raise ValueError, "filetime (%d) is before epoch (%d)" % (
                filetime, self.win32_epoch)

        return (filetime - self.win32_epoch) / 10000000L

    def _get_cookie_attributes(self, cookies, domain,
                               request, req_path, now, redirect):
        # lazily load cookies for this domain
        if self._delayload and cookies["//+delayload"] is not None:
            # Extract cookie filename from the cookie value, into which it was
            # stuffed by the load method.
            cookie_file = cookies["//+delayload"]["cookie"][1]
            if self.cookies.has_key(domain):
                del self.cookies[domain]
            self.load_cookie_data(cookie_file)
            cookies = self.cookies[domain]
        return Cookies._get_cookie_attributes(self, cookies, domain,
                                              request, req_path, now, redirect)

    def _load_cookies_from_file(self, filename):
        cookies = []

        cookies_fh = open(filename)

        while 1:
            key = cookies_fh.readline()
            if key == "": break

            rl = cookies_fh.readline
            def getlong(rl=rl): return long(rl().rstrip())

            key = key.rstrip()
            value = getlong()
            domain_path = getlong()
            # 0x2000 bit is for secure I think
            flags = getlong()
            lo_expire = getlong()
            hi_expire = getlong()
            lo_create = getlong()
            hi_create = getlong()
            sep = rl().rstrip()

            if "" in (key, value, domain_path, flags, hi_expire, lo_expire,
                      hi_create, lo_create, sep) or (sep != "*"):
                break

            m = self.msie_domain_re.search(domain_path)
            if m:
                domain = m.group(1)
                path = m.group(2)

                cookies.append({"KEY": key, "VALUE": value, "DOMAIN": domain,
                                "PATH": path, "FLAGS": flags, "HIXP": hi_expire,
                                "LOXP": lo_expire, "HICREATE": hi_create,
                                "LOCREATE": lo_create})

        return cookies

    def load_cookie_data(self, filename):
        """Load cookies from file containing actual cookie data.

        Old cookies are kept unless overwritten by newly loaded ones.

        I think each of these files contain all cookies for one user, domain,
        and path.

        filename: file containing cookies for a single user and a single domain
         -- usually found in a file like
         C:\WINNT\Profiles\joe\Cookies\joe@blah[1].txt

        """
        now = time()

        cookie_data = self._load_cookies_from_file(filename)

        for cookie in cookie_data:
            secure = ((cookie["FLAGS"] & 0x2000) != 0)
            filetime = (cookie["HIXP"] << 32) + cookie["LOXP"]
            expires = self._epoch_time_offset_from_win32_filetime(filetime)

            self.set_cookie(None, cookie["KEY"], cookie["VALUE"],
                            cookie["PATH"], cookie["DOMAIN"], None,
                            0, secure, expires - now, 0)

    def load(self, filename=None):
        """Load cookies from an MSIE 'index.dat' cookies index file.

        filename: full path to cookie index file

        """
        if filename is None:
            if self.filename is not None: filename = self.filename
            else: raise ValueError, MISSING_FILENAME_TEXT

        now = time()

        # XXX is there a better way of getting the user name than looking in
        # the environment?
        # XXX Is this really needed?  Surely there's only one user per index
        # file anyway??  Maybe not, on win9x.  :(
        user_name = string.lower(os.environ['USERNAME'])

        cookie_dir = os.path.dirname(filename)

        index = open(filename, "rb")
        data = index.read(256)
        if len(data) != 256:
            raise IOError, "%s file is too short" % filename

        # Cookies' index.dat file starts with 32 bytes of signature
        # followed by an offset to the first record, stored as a little-
        # endian DWORD.
        sig, size, data = data[:32], data[32:36], data[36:]
        size = struct.unpack("<L", size)[0]

        # check that sig is valid
        if not sig.startswith(self.magic) or size != 0x4000:
            raise IOError, ("%s ['%s' %s] does not seem to contain cookies" % (
                filename, sig, size))

        # skip to start of first record
        index.seek(size, 0)

        sector = 128  # size of sector in bytes

        while 1:
            data = ""

            # Cookies are usually in two contiguous sectors, so read in two
            # sectors and adjust if not a Cookie.
            to_read = 2 * sector
            d = index.read(to_read)
            if len(d) != to_read:
                break
            data = data + d

            # Each record starts with a 4-byte signature and a count
            # (little-endian DWORD) of sectors for the record.
            sig, size, data = data[:4], data[4:8], data[8:]
            size = struct.unpack("<L", size)[0]

            to_read = (size - 2) * sector

##             from urllib import quote
##             print "data", quote(data)
##             print "sig", quote(sig)
##             print "size in sectors", size
##             print "size in bytes", size*sector
##             print "size in units of 16 bytes", (size*sector) / 16
##             print "size to read in bytes", to_read
##             print

            if sig != "URL ":
                #assert (sig in ("HASH", "LEAK",
                #                self.padding, "\x00\x00\x00\x00"),
                #        "unrecognized MSIE index.dat record: %s" %
                #        binary_to_str(sig))
                if sig == "\x00\x00\x00\x00":
                    # assume we've got all the cookies, and stop
                    break
                if sig == self.padding:
                    continue
                # skip the rest of this record
                assert to_read >= 0
                if size != 2:
                    assert to_read != 0 or sector_adjusted
                    index.seek(to_read, 1)
                continue

            # read in rest of record if necessary
            if size > 2:
                more_data = index.read(to_read)
                if len(more_data) != to_read: break
                data = data + more_data

            cookie_re = ("Cookie\:%s\@([\x21-\xFF]+).*?" % user_name +
                         "(%s\@[\x21-\xFF]+\.txt)" % user_name)
            m = re.search(cookie_re, data)
            if m:
                cookie_file = os.path.join(cookie_dir, m.group(2))
                if not self._delayload:
                    self.load_cookie_data(cookie_file)
                else:
                    domain = m.group(1)
                    i = domain.find("/")
                    if i != -1:
                        domain = domain[:i]

                    # Set a fake cookie for this domain, whose cookie value is
                    # in fact the cookie file for this domain / user.  This
                    # is used in the _get_cookie_attributes method to lazily
                    # load cookies.
                    self.set_cookie(
                        version=None,
                        key="cookie", val=cookie_file, path="//+delayload",
                        domain=domain, port=None, path_spec=False,
                        secure=False, max_age=now + 86400, discard=False)


# urllib2 support

try:
    from urllib2 import AbstractHTTPHandler
except ImportError:
    pass
else:
    import urllib2, urllib, httplib, urlparse, types
    from cStringIO import StringIO
    from _Util import seek_wrapper

    def request_method(req):
        try:
            return req.method()
        except AttributeError:
            if req.has_data():
                return "POST"
            else:
                return "GET"

    # This fixes a bug in urllib2 as of Python 2.1.3 and 2.2.1
    #  (sourceforge bug #549151 -- see file 'patch v2')
    class HTTPRedirectHandler(urllib2.BaseHandler):
        # maximum number of redirections before assuming we're in a loop
        max_redirections = 10

        # Implementation notes:

        # To avoid the server sending us into an infinite loop, the request
        # object needs to track what URLs we have already seen.  Do this by
        # adding a handler-specific attribute to the Request object.

        # Another handler-specific Request attribute, original_url, is used to
        # remember the URL of the original request so that it is possible to
        # decide whether or not RFC 2965 cookies should be turned on during
        # redirect.

        # Always unhandled redirection codes:
        # 300 Multiple Choices: should not handle this here.
        # 304 Not Modified: no need to handle here: only of interest to caches
        #     that do conditional GETs
        # 305 Use Proxy: probably not worth dealing with here
        # 306 Unused: what was this for in the previous versions of protocol??

        def redirect_request(self, newurl, req, fp, code, msg, headers):
            """Return a Request or None in response to a redirect.

            This is called by the http_error_30x methods when a redirection
            response is received.  If a redirection should take place, return a
            new Request to allow http_error_30x to perform the redirect;
            otherwise, return None to indicate that an HTTPError should be
            raised.

            """
            method = request_method(req)
            if (code in (301, 302, 303, 307) and method in ("GET", "HEAD") or
                code in (301, 302, 303) and method == "POST"):
                return urllib2.Request(newurl, headers=req.headers)
            else:
                return None

        def http_error_302(self, req, fp, code, msg, headers):
            if headers.has_key('location'):
                newurl = headers['location']
            elif headers.has_key('uri'):
                newurl = headers['uri']
            else:
                return
            newurl = urlparse.urljoin(req.get_full_url(), newurl)

            # XXX Probably want to forget about the state of the current
            # request, although that might interact poorly with other
            # handlers that also use handler-specific request attributes
            new = self.redirect_request(newurl, req, fp, code, msg, headers)
            if new is None:
                return
            new.original_url = req.get_full_url()

            # loop detection
            new.error_302_dict = {}
            if hasattr(req, 'error_302_dict'):
                if len(req.error_302_dict)>=self.max_redirections or \
                       req.error_302_dict.has_key(newurl):
                    raise HTTPError(req.get_full_url(), code,
                                    self.inf_msg + msg, headers, fp)
                new.error_302_dict.update(req.error_302_dict)
            new.error_302_dict[newurl] = newurl

            # Don't close the fp until we are sure that we won't use it
            # with HTTPError.  
            fp.read()
            fp.close()

            return self.parent.open(new)

        http_error_301 = http_error_303 = http_error_307 = http_error_302

        inf_msg = "The HTTP server returned a redirect error that would" \
                  "lead to an infinite loop.\n" \
                  "The last 302 error message was:\n"

    class addinfourlseek(seek_wrapper):
        def __init__(self, fp, hdrs, url):
            seek_wrapper.__init__(self, fp)
            self.fp = fp
            self.headers = hdrs
            self.url = url
            self.seek(0)

        def info(self):
            return self.headers

        def geturl(self):
            return self.url

    class AbstractHTTPHandler(urllib2.BaseHandler):
        def __init__(self, cookies=None,
                     handle_http_equiv=False, handle_refresh=False,
                     seekable_responses=True):
            if cookies is None:
                cookies = Cookies()
            self.c = cookies

            if handle_http_equiv and not seekable_responses:
                raise ValueError, ("seekable responses are required if "
                                   "handling HTTP-EQUIV headers")

            self._http_equiv = handle_http_equiv
            self._refresh = handle_refresh
            self._seekable_responses = seekable_responses

        def do_open(self, http_class, req):
            if hasattr(req, "error_302_dict") and req.error_302_dict:
                redirect = 1
            else:
                redirect = 0
            self.c.add_cookie_header(req, redirect=redirect)
            host = req.get_host()
            if not host:
                raise URLError('no host given')

            try:
                h = http_class(host) # will parse host:port
                if ClientCookie.HTTP_DEBUG:
                    h.set_debuglevel(1)
                if req.has_data():
                    data = req.get_data()
                    h.putrequest('POST', req.get_selector())
                    if not req.headers.has_key('Content-type'):
                        h.putheader('Content-type',
                                    'application/x-www-form-urlencoded')
                    if not req.headers.has_key('Content-length'):
                        h.putheader('Content-length', '%d' % len(data))
                else:
                    h.putrequest('GET', req.get_selector())
            except socket.error, err:
                raise URLError(err)

            h.putheader('Host', host)
            for args in self.parent.addheaders:
                apply(h.putheader, args)
            for k, v in req.headers.items():
                h.putheader(k, v)
            h.endheaders()
            if req.has_data():
                h.send(data)

            code, msg, hdrs = h.getreply()
            fp = h.getfile()

            if self._seekable_responses:
                response = addinfourlseek(fp, hdrs, req.get_full_url())
            else:
                response = urllib.addinfourl(fp, hdrs, req.get_full_url())
            self.c.extract_cookies(response, req, redirect=redirect)

            if self._refresh and hdrs.has_key("refresh"):
                refresh = hdrs["refresh"]
                i = string.find(refresh, ";")
                if i != -1:
                    time, newurl_spec = refresh[:i], refresh[i+1:]
                    i = string.find(newurl_spec, "=")
                    if i != -1:
                        if int(time) == 0:
                            newurl = newurl_spec[i+1:]
                            # fake a 302 response
                            hdrs["location"] = newurl
                            return self.parent.error(
                                'http', req, fp, 302, msg, hdrs)

            if code == 200:
                return response
            else:
                return self.parent.error('http', req, fp, code, msg, hdrs)


    class EndOfHeadError(Exception): pass
    class HeadParser(htmllib.HTMLParser):
        # only these elements are allowed in or before HEAD of document
        head_elems = ("html", "head",
                      "title", "base",
                      "script", "style", "meta", "link", "object")
        def __init__(self):
            htmllib.HTMLParser.__init__(self, formatter.NullFormatter())
            self.http_equiv = []

        def start_meta(self, attrs):
            http_equiv = content = None
            for key, value in attrs:
                if key == "http-equiv":
                    http_equiv = value
                elif key == "content":
                    content = value
            if http_equiv is not None:
                self.http_equiv.append((http_equiv, content))

        def handle_starttag(self, tag, method, attrs):
            if tag in self.head_elems:
                method(attrs)
            else:
                raise EndOfHeadError

        def handle_endtag(self, tag, method):
            if tag in self.head_elems:
                method()
            else:
                raise EndOfHeadError

        def end_head(self):
            raise EndOfHeadError

    def parse_head(file):
        """Return a list of key, value pairs"""
        hp = HeadParser()
        while 1:
            data = file.read(CHUNK)
            try:
                hp.feed(data)
            except EndOfHeadError:
                break
            if len(data) != CHUNK:
                # this should only happen if there is no HTML body, or if
                # CHUNK is big
                break
        return hp.http_equiv

    class EQUIVMixin:
        def getreply(self):
            """Returns information about response from the server.

            Return value is a tuple consisting of:
            - server status code (e.g. '200' if all goes well)
            - server "reason" corresponding to status code
            - any RFC822 headers in the response from the server

            """
            try:
                # response supports httplib.HTTPResponse interface
                response = self._conn.getresponse()
            except httplib.BadStatusLine, e:
                ### hmm. if getresponse() ever closes the socket on a bad request,
                ### then we are going to have problems with self.sock

                ### should we keep this behavior? do people use it?
                # keep the socket open (as a file), and return it
                self.file = self._conn.sock.makefile('rb', 0)

                # close our socket -- we want to restart after any protocol error
                self.close()

                self.headers = None
                return -1, e.line, None

            # response supports mimetools.Message interface
            self.headers = response.msg
            # grab HTTP-EQUIV headers and add them to the true HTTP headers
            self.file = seek_wrapper(response.fp)
            equiv_hdrs = parse_head(self.file)
            self.file.seek(0)
            for hdr, val in equiv_hdrs:
                self.headers[hdr] = val

            return response.status, response.reason, response.msg


    class HTTP(EQUIVMixin, httplib.HTTP):
        """Extends httplib.HTTP to deal with HTTP-EQUIV headers.

        HTTP-EQUIV headers (HTTP headers in the HEAD section of the HTML
        document) are treated by this class as if they're normal HTTP
        headers.

        """
        pass

    class HTTPHandler(AbstractHTTPHandler):
        """Extends urllib2.HTTPHandler with automatic cookie handling.

        This class also honours zero-time Refresh headers, if the
        handle_refresh argument to the constructor is true.

        """
        def http_open(self, req):
            if self._http_equiv:
                klass = HTTP
            else:
                klass = httplib.HTTP
            return self.do_open(klass, req)

    if hasattr(httplib, 'HTTPS'):
        class HTTPS(EQUIVMixin, httplib.HTTPS):
            """Extends httplib.HTTPS to deal with HTTP-EQUIV headers.

            HTTP-EQUIV headers (HTTP headers in the HEAD section of the HTML
            document) are treated by this class as if they're normal HTTP
            headers.

            """
            pass

        class HTTPSHandler(AbstractHTTPHandler):
            """Extends urllib2.HTTPHandler with automatic cookie handling.

            This class also honours zero-time Refresh headers, if the
            handle_refresh argument to the constructor is true.

            """
            def https_open(self, req):
                if self._http_equiv:
                    klass = HTTPS
                else:
                    klass = httplib.HTTPS
                return self.do_open(klass, req)

    def build_opener(*handlers):
        """Create an opener object from a list of handlers.

        The opener will use several default handlers, including support
        for HTTP and FTP.  If there is a ProxyHandler, it must be at the
        front of the list of handlers.  (Yuck.)

        If any of the handlers passed as arguments are subclasses of the
        default handlers, the default handlers will not be used.
        """

        opener = urllib2.OpenerDirector()
        default_classes = [urllib2.ProxyHandler, urllib2.UnknownHandler,
                           HTTPHandler,  # from this module (extended)
                           urllib2.HTTPDefaultErrorHandler,
                           HTTPRedirectHandler,  # from this module (bugfixed)
                           urllib2.FTPHandler, urllib2.FileHandler]
        if hasattr(httplib, 'HTTPS'):
            default_classes.append(HTTPSHandler)
        skip = []
        for klass in default_classes:
            for check in handlers:
                if type(check) == types.ClassType:
                    if issubclass(check, klass):
                        skip.append(klass)
                elif type(check) == types.InstanceType:
                    if isinstance(check, klass):
                        skip.append(klass)
        for klass in skip:
            default_classes.remove(klass)

        for klass in default_classes:
            opener.add_handler(klass())

        for h in handlers:
            if type(h) == types.ClassType:
                h = h()
            opener.add_handler(h)
        return opener

    _opener = None
    def urlopen(url, data=None):
        global _opener
        if _opener is None:
            cookies = Cookies()
            _opener = build_opener(
                HTTPHandler(cookies),  # from this module (extended)
                )
        return _opener.open(url, data)

    def install_opener(opener):
        global _opener
        _opener = opener
