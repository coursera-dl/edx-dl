from StringIO import StringIO

def startswith(string, initial):
    if len(initial) > len(string): return 0
    return string[:len(initial)] == initial

def endswith(string, final):
    if len(final) > len(string): return 0
    return string[-len(final):] == final


try:
    from calendar import timegm
except:
    # Number of days per month (except for February in leap years)
    mdays = [0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

    # Return 1 for leap years, 0 for non-leap years
    def isleap(year):
	return year % 4 == 0 and (year % 100 <> 0 or year % 400 == 0)

    # Return number of leap years in range [y1, y2)
    # Assume y1 <= y2 and no funny (non-leap century) years
    def leapdays(y1, y2):
	return (y2+3)/4 - (y1+3)/4

    EPOCH = 1970
    def timegm(tuple):
        """Unrelated but handy function to calculate Unix timestamp from GMT."""
        year, month, day, hour, minute, second = tuple[:6]
        assert year >= EPOCH
        assert 1 <= month <= 12
        days = 365*(year-EPOCH) + leapdays(EPOCH, year)
        for i in range(1, month):
            days = days + mdays[i]
        if month > 2 and isleap(year):
            days = days + 1
        days = days + day - 1
        hours = days*24 + hour
        minutes = hours*60 + minute
        seconds = minutes*60 + second
        return seconds

# XXX Andrew Dalke kindly sent me a similar class in response to my request on
# comp.lang.python, which I then proceeded to lose.  I wrote this class
# instead, but I think he's released his code publicly since, could pinch the
# tests from it, at least...
class seek_wrapper:
    """Adds a seek method to a file object.

    This is only designed for seeking on readonly file-like objects.

    Wrapped file-like object must have a read method.  The readline method is
    only supported if that method is present on the wrapped object.  The
    readlines method is always supported.

    Public attribute: wrapped (the wrapped file object).

    WARNING: All other attributes of the wrapped object (ie. those that are not
    one of wrapped, read, readline or readlines) are passed through unaltered,
    which may or may not make sense for your particular file object.

    """
    # General strategy is to check that cache is full enough, then delegate
    # everything to the cache (self._cache, which is a StringIO.StringIO
    # instance -- cStringIO.StringIO won't work, because it has no write
    # method!).

    # Invariant: the end of the cache is always at the same place as the
    # end of the wrapped file:
    # self.wrapped.tell() == len(self._cache.getvalue())

    def __init__(self, wrapped):
        self.wrapped = wrapped
        self.__have_readline = hasattr(self.wrapped, "readline")
        self.__cache = StringIO("")

    def __getattr__(self, name): return getattr(self.wrapped, name)

    def seek(self, offset, whence=0):
        # make sure we have read all data up to the point we are seeking to
        pos = self.__cache.tell()
        if whence == 0:  # absolute
            to_read = offset - pos
        elif whence == 1:  # relative to current position
            to_read = offset
        elif whence == 2:  # relative to end of *wrapped* file
            # since we don't know yet where the end of that file is, we must
            # read everything
            to_read = None
        if to_read >= 0 or to_read is None:
            if to_read is None:
                self.__cache.write(self.wrapped.read())
            else:
                self.__cache.write(self.wrapped.read(to_read))
            self.__cache.seek(pos)

        return self.__cache.seek(offset, whence)

    def read(self, size=-1):
        pos = self.__cache.tell()

        self.__cache.seek(pos)

        end = len(self.__cache.getvalue())
        available = end - pos

        # enough data already cached?
        if size <= available and size != -1:
            return self.__cache.read(size)

        # no, so read sufficient data from wrapped file and cache it
        to_read = size - available
        assert to_read > 0 or size == -1
        self.__cache.seek(0, 2)
        if size == -1:
            self.__cache.write(self.wrapped.read())
        else:
            self.__cache.write(self.wrapped.read(to_read))
        self.__cache.seek(pos)

        return self.__cache.read(size)

    def readline(self, size=-1):
        if not self.__have_readline:
            raise NotImplementedError, "no readline method on wrapped object"

        # line we're about to read might not be complete in the cache, so
        # read another line first
        pos = self.__cache.tell()
        self.__cache.seek(0, 2)
        self.__cache.write(self.wrapped.readline())
        self.__cache.seek(pos)

        data = self.__cache.readline()
        if size != -1:
            r = data[:size]
            self.__cache.seek(pos+size)
        else:
            r = data
        return r

    def readlines(self, sizehint=-1):
        pos = self.__cache.tell()
        self.__cache.seek(0, 2)
        self.__cache.write(self.wrapped.read())
        self.__cache.seek(pos)
        try:
            return self.__cache.readlines(sizehint)
        except TypeError:  # 1.5.2 hack
            return self.__cache.readlines()
