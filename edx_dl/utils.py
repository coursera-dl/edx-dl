#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This module contains a set of functions to be used by edx-dl.
"""

import cookielib
import logging
import subprocess
import urllib2

from bs4 import BeautifulSoup

EDX_HOMEPAGE = 'https://courses.edx.org'
LOGIN_URL = 'https://courses.edx.org/login_ajax'
DASHBOARD = 'https://courses.edx.org/dashboard'
YOUTUBE_VIDEO_ID_LENGTH = 11


def get_page_contents(url, headers):
    """
    Get the contents of the page at the URL given by url. While making the
    request, we use the headers given in the dictionary in headers.
    """
    logging.debug('Getting page at %s with headers %s', url, headers)
    req = urllib2.Request(url, None, headers)
    logging.debug('Created request: %s', req)
    result = urllib2.urlopen(req)
    logging.debug('Got result %s', result)

    return result.read()


def get_initial_token(homepage):
    """
    Create initial connection to get authentication token for future requests.

    Returns a string to be used in subsequent connections with the
    X-CSRFToken (Cross-Site Request Forgery) header or the empty string if
    we didn't find any token in the cookies.
    """
    cj = cookielib.CookieJar()
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
    urllib2.install_opener(opener)
    opener.open(homepage)

    for cookie in cj:
        if cookie.name == 'csrftoken':
            return cookie.value

    return ''


def get_course_list(headers, dashboard):
    """
    Returns a list of tuples with each tuple consisting of:

    * Course name: name of the course we are currently enrolled in.
    * Course ID: the 'id' of the course.
    * State: a string saying if the course has started or not.
    """
    dash = get_page_contents(dashboard, headers)
    soup = BeautifulSoup(dash)
    courses = soup.find_all('article', 'my-course')

    courses_list = []
    for course in courses:
        c_name = course.h3.text.strip()
        c_id = course.a['href'].lstrip('/courses/')

        if c_id.endswith('info') or c_id.endswith('info/'):
            c_id = c_id.rstrip('/info/')
            state = 'Started'
        else:
            c_id = c_id.rstrip('/about/')
            state = 'Not started'

        courses_list.append((c_id, c_name, state))

    return courses_list


def download_videos(video_urls, opts):
    """
    Receives a list of URLs given in video_urls and a dictionary called opts
    with the preferences made by the user and performs the actual download
    of the videos with URLs with the options given in opts.
    """
    # FIXME: Create subdirectories for each lecture and name the files under
    # those directories

    cmd = ['youtube-dl', '-A']

    if opts.format:
        cmd.append('-f %d' % opts.format)
    if opts.subtitles:
        cmd.append('--write-srt')

    cmd.extend(video_urls)

    subprocess.call(cmd)
