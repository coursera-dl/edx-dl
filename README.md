# DESCRIPTION

Simple tool to download video lectures from edx.org.  It requires a
Python interpreter (> 2.6), youtube-dl, and BeautifulSoup4. It is
platform independent, and should work fine under Unix, Windows or
Mac OS X.

# DEPENDENCIES

To install all the dependencies please do:

    pip install -r requirements.txt

You also need to install youtube-dl

## youtube-dl

We use `youtube-dl` to download video lectures from Youtube, with the main
idea being that "we don't want to reinvent the wheel".  Make sure you have
`youtube-dl` installed in your system.  Also, since Youtube changes its
layout frequently, make sure that the version of `youtube-dl` that you have
installed is the latest. If in doubt, run `youtube-dl --update`.

You can find `youtube-dl` at <http://rg3.github.io/youtube-dl/download.html>
or via pip:

    pip install youtube-dl

## BeautifulSoup

Scrapping the web can be very silly task, but BeautifulSoup makes it
so easy :), it isn't included in the python standard library.  Make
sure you have BeautifulSoup installed.

You can install it with

    pip install beautifulsoup4

or

    easy_install beautifulsoup4.

For more information, please see <http://www.crummy.com/software/BeautifulSoup/#Download>.

## html5lib

OpenEdX as a platform uses HTML5 to render its pages. The default html parser
of python used by BeautifulSoup can have issues with the new HTML5 elements so
it is important to include this dependency to avoid further issues.

You can install it with

    pip install html5lib

For more details, please see <https://github.com/html5lib/html5lib-python>

## six

six deals with compatibility support between python 2/3

    pip install six

More info, see <https://pythonhosted.org/six/>

# Quick Start

To use `edx-dl.py`, simply execute it, as in:

    python edx-dl.py -u user@user.com -p password COURSE_URL

The COURSE_URL must correspond to a course you are enregistered, it is the one
who ends in '/info', e.g.
https://courses.edx.org/courses/edX/DemoX.1/2014/info

You must pass the URL of at least one course, you can check the correct url

    python edx-dl.py -u user@user.com -p password --course-list

Your downloaded videos will be placed in a new Directory called
"Downloaded", but you can also choose another destination with the '-o'
argument.

To see all available options:

    python edx-dl.py

# Reporting issues

Before reporting any issue please verify that you are running the latest version
of the script and of youtube-dl. Please include in your report the
following information:

OS:
Python version:
youtube-dl version:
Course URL:

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
