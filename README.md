# DESCRIPTION

Simple tool to download video lectures from edx.org.  It requires the
Python interpreter (> 2.6), youtube-dl, BeautifulSoup4 and it's
platform independent.  It should work fine in your Unix box, in
Windows or in Mac OS X.

# DEPENDENCIES

## youtube-dl

We use youtube-dl to download video lectures from youtube "We don't wanna
reinvent the wheel :)".  Make sure you have youtube-dl installed in your
system.

You can find youtube-dl at <https://github.com/rg3/youtube-dl>.

## BeautifulSoup

Scrapping the web can be very silly task, but BeautifulSoup makes it
so easy :), it isn't included in the python standard library.  Make
sure you have BeautifulSoup installed.

You can install it with

    pip install beautifulsoup4

or

    easy_install beautifulsoup4.

For more info, see <http://www.crummy.com/software/BeautifulSoup/#Download>.

# Files

## edx-dl.py
Python implementation for edx-downloader

The original file was written by @shk3 in/for `python3` then updated
by @emadshaaban92 for python2, and migrated for versions superior to
2.6 by @iemejia.

# USAGE

To use `edx-dl.py`, simply excute it with 2 arguments: email and password,
as in:

    python edx-dl.py user@user.com password

Your downloaded videos will be placed in a new Directory called
"Downloaded".  The script is very interactive, and if you have a issue
please tell us.
