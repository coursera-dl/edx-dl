[![Build Status](https://travis-ci.org/coursera-dl/edx-dl.svg?branch=master)](https://travis-ci.org/coursera-dl/edx-dl)
[![Coverage Status](https://coveralls.io/repos/coursera-dl/edx-dl/badge.svg?branch=master&service=github)](https://coveralls.io/github/coursera-dl/edx-dl?branch=master)
[![Code Climate](https://codeclimate.com/github/coursera-dl/edx-dl/badges/gpa.svg)](https://codeclimate.com/github/coursera-dl/edx-dl)

# Description

`edx-dl` is a simple tool to download videos and lecture materials from Open
edX-based sites.  It requires a [Python][python] interpreter (>= 2.7) and
very few other dependencies.  It is platform independent, and should work
fine under Unix (Linux, BSDs etc.), Windows or Mac OS X.

We strongly recommend that, if you don't already have a Python interpreter
installed, that you [install Python >= 3.4][python3], if possible, since it
has better security than Python 2.

[python]: https://www.python.org/
[python3]: https://www.python.org/downloads/

# Dependencies

To install all the dependencies please do:

    pip install -r requirements.txt

## youtube-dl

One of the most important dependencies of `edx-dl` is `youtube-dl`. The
installation step listed above already pulls in the most recent version of
`youtube-dl` for you.

Unfortunately, since many Open edX sites store their videos on Youtube and
Youtube changes their layout from time to time, it may be necessary to
upgrade your copy of `youtube-dl`.  There are many ways to proceed here, but
the simplest is to simply use:

    pip install --upgrade youtube-dl

# Quick Start

Once you have installed everything, to use `edx-dl.py`, let it discover the
courses in which you are enrolled, by issuing:

    python edx-dl.py -u user@user.com --list-courses

From there, choose the course you are interested in, copy its URL and use it
in the following command:

    python edx-dl.py -u user@user.com COURSE_URL

replacing `COURSE_URL` with the URL that you just copied in the first step.
It should look something like:
https://courses.edx.org/courses/edX/DemoX.1/2014/info

Your downloaded videos will be placed in a new Directory called
`Downloaded`, inside your current directory, but you can also choose another
destination with the `-o` argument.

To see all available options and a brief description of what they do, simply
execute:

    python edx-dl.py --help

*Important Note:* To use sites other than edx.org, you have to specify the
site along with the `-x` option. For example, `-x stanford`, if the course
that you want to get is hosted on Stanford's site.

# Reporting issues

Before reporting any issue please follow the steps below:

1. Verify that you are running the latest version of all the programs (both
of `edx-dl` and of `youtube-dl`).  Use the following command if in doubt:

        pip install --upgrade edx-dl

2. If the problem persists, feel free to [open an issue][issue] in our
bugtracker, with *as much information as possible*.  At a bare minimum,
please specify the following information:
following information:

    - Your operating system/version
    - Python version
    - Version of youtube-dl
    - Which course (the URL) you have problems with:
    - If it helps it is better if you refer to a concrete subsection or unit.
    - Any other information that you may think that would help us finding
      the problem.

[issue]: https://github.com/shk3/edx-downloader/issues

If the script fails and throws some exception, please copy the *entire*
output of the command or the stacktrace (but you may be free to obfuscate
your username and password, of course).

If you cannot copy the exception that the script shows, attach a screen
shot/capture to the bug system.

# Supported sites

These are the current supported sites:

- [edX](http://edx.org)
- [Stanford](http://lagunita.stanford.edu/)
- [University of Sydney](http://online.it.usyd.edu.au)
- [France Université Numérique](https://www.france-universite-numerique-mooc.fr/)
- [GW Online SEAS](http://openedx.seas.gwu.edu/) - George Washington University
- [GW Online Open](http://mooc.online.gwu.edu/) - George Washington University

This is the full [list of sites powered by Open edX][sites]. Not all of them
are supported at the moment, we welcome you to contribute support for them
and send a pull request also via our [issue tracker][issue].

[sites]: https://github.com/edx/edx-platform/wiki/Sites-powered-by-Open-edX

# Authors

See the contributors to the project in the [AUTHORS.md][authors] file.  If
you have contributed to the project, we would like to gladly credit you for
your work. Just send us a note to be added to that list.

[authors]: https://github.com/shk3/edx-downloader/blob/master/AUTHORS.md
