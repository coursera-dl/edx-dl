# DESCRIPTION

Simple tool to download video lectures from edx.org.  It requires a
Python interpreter (> 2.6), youtube-dl, and BeautifulSoup4. It is
platform independent, and should work fine under Unix, Windows or
Mac OS X.

# DEPENDENCIES

## youtube-dl

We use `youtube-dl` to download video lectures from Youtube, with the main
idea being that "we don't want to reinvent the wheel".  Make sure you have
`youtube-dl` installed in your system.  Also, since Youtube changes its
layout frequently, make sure that the version of `youtube-dl` that you have
installed is the latest. If in doubt, run `youtube-dl --update`.

You can find `youtube-dl` at <http://rg3.github.io/youtube-dl/download.html>.

## BeautifulSoup

Scrapping the web can be very silly task, but BeautifulSoup makes it
so easy :), it isn't included in the python standard library.  Make
sure you have BeautifulSoup installed.

You can install it with

    pip install beautifulsoup4

or

    easy_install beautifulsoup4.

For more information, please see <http://www.crummy.com/software/BeautifulSoup/#Download>.

# Quick Start

To use `edx-dl.py`, simply excute it, as in:

    python edx-dl.py

You will then be asked your username and password.

Your downloaded videos will be placed in a new Directory called
"Downloaded".  The script is very interactive, and if you have a issue
please tell us.

You can also excute it with arguments given: email and password,
as in:

    python edx-dl.py [-u user@user.com] [-p password]

# Supported sites

These are the current supported sites:

- [edX](http://edx.org)
- [Stanford](http://lagunita.stanford.edu/)
- [University of Sydney](http://online.it.usyd.edu.au)
- [France Université Numérique](https://www.france-universite-numerique-mooc.fr/)
- [GW Online SEAS](http://openedx.seas.gwu.edu/) - George Washington University
- [GW Online Open](http://mooc.online.gwu.edu/) - George Washington University

This is the full [list of sites powered by Open
edX](https://github.com/edx/edx-platform/wiki/Sites-powered-by-Open-edX). Feel free to contribute your patches to include them.

# Authors

See the contributors to the project in the [AUTHORS.md][authors] file.  If
you have contributed to the project, we would like to gladly credit you for
your work. Just send us a note to be added to that list.

[authors]: https://github.com/shk3/edx-downloader/blob/master/AUTHORS.md
