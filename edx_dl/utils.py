#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This module contains generic functions, ideally useful to any other module
from six.moves.urllib.request import urlopen, Request

import errno
import json
import os
import string
import subprocess


def get_filename_from_prefix(target_dir, filename_prefix):
    """
    Return the basename for the corresponding filename_prefix.
    """
    # This whole function is not the nicest thing, but isolating it makes
    # things clearer. A good refactoring would be to get the info from the
    # video_url or the current output, to avoid the iteration from the
    # current dir.
    filenames = os.listdir(target_dir)
    for name in filenames:  # Find the filename of the downloaded video
        if name.startswith(filename_prefix):
            (basename, ext) = os.path.splitext(name)
            return basename
    return None


def execute_command(cmd):
    """
    Creates a process with the given command cmd.
    """
    return subprocess.call(cmd)


def strip_non_ascii_chars(name):
    """
    Strips the non ascii characters from a str
    """
    allowed_chars = string.digits + string.ascii_letters + " _.-"
    result = ""
    for char in name:
        if allowed_chars.find(char) != -1:
            result += char
    return result


def directory_name(initial_name):
    """
    Transform the name of a directory into an ascii version
    """
    result = strip_non_ascii_chars(initial_name)
    return result if result != "" else "course_folder"


def get_page_contents(url, headers):
    """
    Get the contents of the page at the URL given by url. While making the
    request, we use the headers given in the dictionary in headers.
    """
    result = urlopen(Request(url, None, headers))
    try:
        # for python3
        charset = result.headers.get_content_charset(failobj="utf-8")
    except:
        charset = result.info().getparam('charset') or 'utf-8'
    return result.read().decode(charset)


def get_page_contents_as_json(url, headers):
    """
    Makes a request to the url and immediately parses the result asuming it is
    formatted as json
    """
    json_string = get_page_contents(url, headers)
    json_object = json.loads(json_string)
    return json_object


# this one comes from coursera-dl/coursera
def mkdir_p(path, mode=0o777):
    """
    Create subdirectory hierarchy given in the paths argument.
    """
    try:
        os.makedirs(path, mode)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise
