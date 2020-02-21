[![Build Status](https://github.com/coursera-dl/edx-dl/workflows/Run%20Unit%20Tests/badge.svg)](https://github.com/coursera-dl/edx-dl/workflows)
[![Coverage Status](https://coveralls.io/repos/coursera-dl/edx-dl/badge.svg?branch=master&service=github)](https://coveralls.io/github/coursera-dl/edx-dl?branch=master)
[![Code Climate](https://codeclimate.com/github/coursera-dl/edx-dl/badges/gpa.svg)](https://codeclimate.com/github/coursera-dl/edx-dl)
[![PyPI version](https://badge.fury.io/py/edx-dl.svg)](https://badge.fury.io/py/edx-dl)

# Description

`edx-dl` is a simple tool to download videos and lecture materials from Open
edX-based sites.  It requires a [Python][python] interpreter (>= 2.7) and
very few other dependencies.  It is platform independent, and should work
fine under Unix (Linux, BSDs etc.), Windows or Mac OS X.

We strongly recommend that, if you don't already have a Python interpreter
installed, that you [install Python >= 3.6][python3], if possible, since it
is better in general.

[python]: https://www.python.org/
[python3]: https://www.python.org/downloads/

# Installation (recommended)

To install edx-dl run:

    pip install edx-dl

# Manual Installation

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

    edx-dl -u user@user.com --list-courses

From there, choose the course you are interested in, copy its URL and use it
in the following command:

    edx-dl -u user@user.com COURSE_URL

replacing `COURSE_URL` with the URL that you just copied in the first step.
It should look something like:
https://courses.edx.org/courses/edX/DemoX.1/2014/info

Your downloaded videos will be placed in a new directory called
`Downloaded`, inside your current directory, but you can also choose another
destination with the `-o` argument.

To see all available options and a brief description of what they do, simply
execute:

    edx-dl --help

*Important Note:* To use sites other than <edx.org>, you **have** to specify the
site along with the `-x` option. For example, `-x stanford`, if the course
that you want to get is hosted on Stanford's site.

# Docker container

You can run this application via [Docker](https://docker.com) if you want. Just install docker and run

```
docker run --rm -it \
       -v "$(pwd)/edx/:/Downloaded" \
       strm/edx-dl -u <USER> -p <PASSWORD>
```

# Reporting issues

Before reporting any issue please follow the steps below:

1. Verify that you are running the latest version of all the programs (both
of `edx-dl` and of `youtube-dl`).  Use the following command if in doubt:

        pip install --upgrade edx-dl

2. If you get an error like `"YouTube said: Please sign in to view this
   video."`, then we can't do much about it. You can try to pass your
   credentials to `youtube-dl` (see
   https://github.com/rg3/youtube-dl#authentication-options) with the use of
   `edx-dl`'s option `--youtube-dl-options`. If it doesn't work, then you
   will have to tell `edx-dl` to ignore the download of that particular
   video with the option `--ignore-errors`.

3. If the problem persists, feel free to [open an issue][issue] in our
bugtracker, please fill the issue template with *as much information as
possible*.

[issue]: https://github.com/coursera-dl/edx-dl/issues

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

[authors]: https://github.com/coursera-dl/edx-dl/blob/master/AUTHORS.md
