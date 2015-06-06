# DESCRIPTION

`edx-dl` is a simple tool to download video lectures from Open edX-based
sites.  It requires a Python interpreter (>= 2.7) and very few other
dependencies.  It is platform independent, and should work fine under Unix
(Linux, BSDs etc.), Windows or Mac OS X.

# DEPENDENCIES

To install all the dependencies please do:

    pip install -r requirements.txt

## youtube-dl

One of the dependencies that `edx-dl` uses is `youtube-dl`. The installation
step listed above already pulls in the morst recent version of `youtube-dl`
for you.

Unfortunately, since many Open edX sites store their videos on Youtube and
Youtube changes their layout from time to time, it may be necessary to
upgrade your copy of `youtube-dl`.  There are many ways to proceed here, but
the simplest is to simply use:

    pip install --upgrade youtube_dl

# Quick Start

To use `edx-dl.py`, simply execute it, as in:

    python edx-dl.py -u user@user.com -p password COURSE_URL

The `COURSE_URL` must correspond to a course you are enregistered, it is the
one that ends in `/info`, e.g.
https://courses.edx.org/courses/edX/DemoX.1/2014/info

You must pass the URL of at least one course, you can check the correct url

    python edx-dl.py -u user@user.com -p password --list-courses

Your downloaded videos will be placed in a new Directory called
`Downloaded`, but you can also choose another destination with the `-o`
argument.

To see all available options:

    python edx-dl.py

# Reporting issues

Before reporting any issue please verify that you are running the latest
version of the script and of `youtube-dl`. Please include in your report the
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
