"""_HTTPDate - date/time conversion routines.

from ClientCookie_HTTPDate import time2str, str2time

 string = time2str(time)  # Format as GMT ASCII time
 time = str2time(string)  # convert ASCII date to machine time

This module provides functions that deal the with date/time formats used by the
HTTP protocol (and then some more).

Copyright 1995-1999, Gisle Aas
Copyright 2002 John J Lee <jjl@pobox.com> (The Python port)

This code is free software; you can redistribute it and/or modify it under
the terms of the MIT License (see the file COPYING included with the
distribution).

"""

# from Gisle Aas's CVS revision 1.43, libwww-perl 5.64

import re, string
from time import time, gmtime, localtime
from _Util import timegm
_timegm = timegm
del timegm

EPOCH = 1970
def timegm(tt):
    year, month, mday, hour, min, sec = tt[:6]
    if ((year >= EPOCH) and (1 <= month <= 12) and (1 <= mday <= 31) and
        (0 <= hour <= 24) and (0 <= min <= 59) and (0 <= sec <= 61)):
        return _timegm(tt)
    else:
        return None

days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
months_lower = []
for month in months: months_lower.append(string.lower(month))


GMT_ZONE = {"GMT": 1, "UTC": 1, "UT": 1, "Z": 1}


def tz_offset(tz):
    return None

# XXX this is utterly broken, what on earth was I thinking of??
## try:
##     from mx import DateTime
## except ImportError:
##     def tz_offset(tz):
##         return None
## else:
##     def tz_offset(tz):
##         return mxDateTime.DateTimeFromString("2002-04-01 00:00:00 "+tz)


def time2str(t=None):
    """Return a string representing time in seconds since epoch, t.

    If the function is called without an argument, it will use the current
    time.

    The string returned is in the format preferred for the HTTP protocol.  This
    is a fixed length subset of the format defined by RFC 1123, represented in
    Universal Time (GMT, aka UTC).  An example of a time stamp in this format
    is:

       Sun, 06 Nov 1994 08:49:37 GMT

    """
    if t is None:
        t = time()
    year, month, day, hour, min, sec, wkday, julian_day, dst = gmtime(t)
    return "%s, %02d %s %04d %02d:%02d:%02d GMT" % (
        days[wkday], day, months[month-1], year, hour, min, sec)

def offset_from_tz_string(tz):
    if GMT_ZONE.has_key(tz):
        offset = 0
    else:
        m = timezone_re.search(tz)
        if m:
            offset = 3600 * int(m.group(2))
            if m.group(3):
                offset = offset + 60 * int(m.group(3))
            if m.group(1) == '-':
                offset = -offset
        else:
            offset = tz_offset(string.upper(string.strip(tz)))
    return offset

timezone_re = re.compile(r"^([-+])?(\d\d?):?(\d\d)?$")
strict_re = re.compile(r"^[SMTWF][a-z][a-z], (\d\d) ([JFMASOND][a-z][a-z]) (\d\d\d\d) (\d\d):(\d\d):(\d\d) GMT$")
def str2time(str, tz=None):
    """Returns time in seconds since epoch of time represented by a string.

    None is returned if the format of str is unrecognized, or the time is
    outside the representable range.  The time formats recognized are the same
    as for parse_date.


    XXX CAUTION: this is currently broken: the timezone is always assumed to be
    UTC, regardless of any timezone in the string or the tz argument.


    The function also takes an optional second argument that specifies the
    default time zone to use when converting the date.  This parameter is
    ignored if the zone is found in the date string itself.  If this parameter
    is missing, and the date string format does not contain any zone
    specification, then the local time zone is assumed.

    If the zone is not UTC or numerical (like "-0800" or "+0100"), then
    mxDateTime must be installed in order to get the date recognized.

    """
    # fast exit for strictly conforming string
    m = strict_re.search(str)
    if m:
        g = m.groups()
        mon = months_lower.index(string.lower(g[1])) + 1
        tt = (int(g[2]), mon, int(g[0]),
              int(g[3]), int(g[4]), float(g[5]))
        return timegm(tt)

    d = parse_date(str);
    if d is None:
        return None
    #d[1] = d[1] - 1  # month

    tz = d.pop()
    if tz is None: tz = "UTC"
    tz = string.upper(tz)

    t = timegm(d)
    if t is not None:
        t = t - offset_from_tz_string(tz)
    return t


wkday_re = re.compile(
    r"^(?:Sun|Mon|Tue|Wed|Thu|Fri|Sat)[a-z]*,?\s*", re.I)
general_re = re.compile(
    r"""^
    (\d\d?)            # day
       (?:\s+|[-\/])
    (\w+)              # month
        (?:\s+|[-\/])
    (\d+)              # year
    (?:
	  (?:\s+|:)    # separator before clock
       (\d\d?):(\d\d)  # hour:min
       (?::(\d\d))?    # optional seconds
    )?                 # optional clock
       \s*
    ([-+]?\d{2,4}|(?![APap][Mm]\b)[A-Za-z]+)? # timezone
       \s*
    (?:\(\w+\))?       # ASCII representation of timezone in parens.
       \s*$""", re.X)
ctime_re = re.compile(
    r"""^
    (\w{1,3})             # month
       \s+
    (\d\d?)               # day
       \s+
    (\d\d?):(\d\d)        # hour:min
    (?::(\d\d))?          # optional seconds
       \s+
    (?:([A-Za-z]+)\s+)?   # optional timezone
    (\d+)                 # year
       \s*$               # allow trailing whitespace
    """, re.X)
ls_l_re = re.compile(
    """^
    (\w{3})               # month
       \s+
    (\d\d?)               # day
       \s+
    (?:
       (\d\d\d\d) |       # year
       (\d{1,2}):(\d{2})  # hour:min
       (?::(\d\d))?       # optional seconds
    )
    \s*$""", re.X)
iso_re = re.compile(
    """^
    (\d{4})              # year
       [-\/]?
    (\d\d?)              # numerical month
       [-\/]?
    (\d\d?)              # day
   (?:
         (?:\s+|[-:Tt])  # separator before clock
      (\d\d?):?(\d\d)    # hour:min
      (?::?(\d\d(?:\.\d*)?))?  # optional seconds (and fractional)
   )?                    # optional clock
      \s*
   ([-+]?\d\d?:?(:?\d\d)?
    |Z|z)?               # timezone  (Z is "zero meridian", i.e. GMT)
      \s*$""", re.X)
windows_re = re.compile(
    """^
    (\d{2})                # numerical month
       -
    (\d{2})                # day
       -
    (\d{2})                # year
       \s+
    (\d\d?):(\d\d)([APap][Mm])  # hour:min AM or PM
       \s*$""", re.X)

tz_re = re.compile(r"^(GMT|UTC?|[-+]?0+)$")

def parse_date(text):
    """
    This function will try to parse a date string, and then return it as a list
    of numerical values followed by a (possibly None) time zone specifier;
    [year, month, day, hour, min, sec, tz).  The year returned will not have
    the number 1900 subtracted from it and the month numbers start with 1.

    In scalar context the numbers are interpolated in a string of the
    "YYYY-MM-DD hh:mm:ss TZ"-format and returned.

    If the date is unrecognized, then the empty list is returned.

    The function is able to parse the following formats:

     "Wed, 09 Feb 1994 22:23:32 GMT"       -- HTTP format
     "Thu Feb  3 17:03:55 GMT 1994"        -- ctime(3) format
     "Thu Feb  3 00:00:00 1994",           -- ANSI C asctime() format
     "Tuesday, 08-Feb-94 14:15:29 GMT"     -- old rfc850 HTTP format
     "Tuesday, 08-Feb-1994 14:15:29 GMT"   -- broken rfc850 HTTP format

     "03/Feb/1994:17:03:55 -0700"   -- common logfile format
     "09 Feb 1994 22:23:32 GMT"     -- HTTP format (no weekday)
     "08-Feb-94 14:15:29 GMT"       -- rfc850 format (no weekday)
     "08-Feb-1994 14:15:29 GMT"     -- broken rfc850 format (no weekday)

     "1994-02-03 14:15:29 -0100"    -- ISO 8601 format
     "1994-02-03 14:15:29"          -- zone is optional
     "1994-02-03"                   -- only date
     "1994-02-03T14:15:29"          -- Use T as separator
     "19940203T141529Z"             -- ISO 8601 compact format
     "19940203"                     -- only date

     "08-Feb-94"         -- old rfc850 HTTP format    (no weekday, no time)
     "08-Feb-1994"       -- broken rfc850 HTTP format (no weekday, no time)
     "09 Feb 1994"       -- proposed new HTTP format  (no weekday, no time)
     "03/Feb/1994"       -- common logfile format     (no time, no offset)

     "Feb  3  1994"      -- Unix 'ls -l' format
     "Feb  3 17:03"      -- Unix 'ls -l' format

     "11-15-96  03:52PM" -- Windows 'dir' format

    The parser ignores leading and trailing whitespace.  It also allow the seconds
    to be missing and the month to be numerical in most formats.

    If the year is missing, then we assume that the date is the first matching
    date *before* current month.  If the year is given with only 2 digits, then
    parse_date will select the century that makes the year closest to the
    current date.

    """
    assert text is not None
    # More lax parsing below
    text = string.lstrip(text)
    text = wkday_re.sub("", text, 1)  # Useless weekday

    day, mon, yr, hr, min, sec, tz, ampm = [None]*8

    failed = 1
    # check for most of the formats with this regexp
    m = general_re.search(text)
    if m is not None:
        failed = 0
        day, mon, yr, hr, min, sec, tz = m.groups()
    if failed:
        # Try the ctime and asctime format
        m = ctime_re.search(text)
        if m is not None:
            failed = 0
            mon, day, hr, min, sec, tz, yr = m.groups()
    if failed:
        # Then the Unix 'ls -l' date format
        m = ls_l_re.search(text)
        if m is not None:
            failed = 0
            mon, day, yr, hr, min, sec = m.groups()
    if failed:
        # ISO 8601 format '1996-02-29 12:00:00 -0100' and variants
        m = iso_re.search(text)
        if m is not None:
            failed = 0
            # XXX there's an extra bit of the timezone I'm ignoring here: is
            #   this the right thing to do?
            yr, mon, day, hr, min, sec, tz, _ = m.groups()
    if failed:
        # Windows 'dir' 11-12-96  03:52PM
        m = windows_re.search(text)
        if m is not None:
            failed = 0
            mon, day, yr, hr, min, ampm = m.groups()
    if failed:
        return None  # unrecognized format

    # Translate month name to number
    try:
        mon = months_lower.index(string.lower(mon))+1
    except ValueError:
        #mon = months["\u\L%s" % (mon,)]
        if 1:#not mon:
            try:
                imon = int(mon)
            except ValueError:
                return None
            else:
                if (imon >= 1 and imon <= 12):
                    mon = imon
                else:
                    return None

    # Make sure clock elements are defined
    if hr is None: hr = 0
    if min is None: min = 0
    if sec is None: sec = 0

    day = int(day)
    hr = int(hr)
    min = int(min)
    sec = float(sec)

    # If the year is missing, we assume first date before the current,
    # because, of the formats we support, such dates are mostly present
    # on "ls -l" listings.
    if yr is not None:
        yr = int(yr)
    if yr is None:
        yr, cur_mon = localtime(time())[0:2]
        if mon > cur_mon: yr = yr - 1
    elif yr < 1000:
	# Find "obvious" year
	cur_yr = localtime(time())[0]
	m = cur_yr % 100
	tmp = yr
	yr = yr + cur_yr - m
	m = m - tmp
        if abs(m) > 50:
            if m > 0: yr = yr + 100
            else: yr = yr - 100

    # Compensate for AM/PM
    if ampm:
	ampm = string.upper(ampm)
        if hr == 12 and ampm == "AM":
            hr = 0
        if ampm == "PM" and hr != 12:
            hr = hr + 12

    return [yr, mon, day, hr, min, sec, tz]

def time2iso(t=None):
    """
    Same as time2str(), but returns a "YYYY-MM-DD hh:mm:ss"-formatted string
    representing time in the local time zone.
    """
    if t is None: t = time()
    year, mon, mday, hour, min, sec = localtime(t)[:6]
    return "%04d-%02d-%02d %02d:%02d:%02d" % (
        year, mon, mday, hour, min, sec)

def time2isoz(t=None):
    """
    Same as time2str(), but returns a "YYYY-MM-DD hh:mm:ssZ"-formatted
    string representing Universal Time.
    """
    if t is None: t = time()
    year, mon, mday, hour, min, sec = gmtime(t)[:6]
    return "%04d-%02d-%02d %02d:%02d:%02dZ" % (
        year, mon, mday, hour, min, sec)
