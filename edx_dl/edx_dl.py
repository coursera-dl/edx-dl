#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
edx-dl is a simple tool to download video lectures from edx.org.

It requires a Python interpreter (>= 2.6), youtube-dl, BeautifulSoup4 and
should be platform independent, meaning that it should work fine in your
Unix box, in Windows or in Mac OS X.
"""

import argparse
import json
import logging
import re
import sys
import urllib
import urllib2

from bs4 import BeautifulSoup


def parse_args():
    """
    Parse the arguments/options passed to the program on the command line.
    """

    parser = argparse.ArgumentParser(prog='edx-dl',
                                     description='Get videos from edx.org',
                                     epilog='For further use information,'
                                     'see the file README.md',)

    # positional
    parser.add_argument('course_id',
                        nargs='*',
                        action='store',
                        default=None,
                        help='target course id '
                        '(e.g., BerkeleyX/CS191x/2013_Spring);'
                        ' the list can be obtained by \'-l\'')

    # optional
    parser.add_argument('-u',
                        '--username',
                        action='store',
                        help='your edX username (email)')
    parser.add_argument('-p',
                        '--password',
                        action='store',
                        help='your edX password')
    parser.add_argument('-w',
                        '--weeks',
                        dest='weeks',
                        action='store',
                        default=None,
                        help='weeks of classes to download (default: all)')
    parser.add_argument('-f',
                        '--format',
                        dest='format',
                        action='store',
                        default=None,
                        help='format of videos to download (default: best)')
    parser.add_argument('-l',
                        '--list-courses',
                        dest='list_courses',
                        action='store_true',
                        default=False,
                        help='list courses currently enrolled')
    parser.add_argument('-s',
                        '--with-subtitles',
                        dest='subtitles',
                        action='store_true',
                        default=False,
                        help='download subtitles with the videos')
    parser.add_argument('-d',
                        '--debug',
                        dest='debug',
                        action='store_true',
                        default=False,
                        help='print debugging information')

    args = parser.parse_args()

    # FIXME: check arguments
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)

    if not args.username:
        logging.error('No username specified.')
        sys.exit(1)
    if not args.password:
        logging.error('No password specified.')
        sys.exit(1)

    if not args.list_courses and len(args.course_id) == 0:
        logging.error('You must specify at least one course_id'
                      ' or the \'-l\' switch. Please see the documentation.')
        sys.exit(1)

    return args

from utils import (EDX_HOMEPAGE, LOGIN_URL, YOUTUBE_VIDEO_ID_LENGTH,
                   get_initial_token, get_course_list, get_page_contents)


if __name__ == '__main__':
    args = parse_args()

    user_email = args.username
    user_pswd = args.password
    video_fmt = args.format

    logging.debug('Preparing headers.')
    headers = {
        'User-Agent': 'edX-downloader/0.01',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Content-Type': 'application/x-www-form-urlencoded;charset=utf-8',
        'Referer': EDX_HOMEPAGE,
        'X-Requested-With': 'XMLHttpRequest',
        'X-CSRFToken': get_initial_token(),
    }

    logging.debug('Preparing login information.')
    post_data = urllib.urlencode({'email': user_email,
                                 'password': user_pswd,
                                 'remember': False}).encode('utf-8')
    request = urllib2.Request(LOGIN_URL, post_data, headers)
    response = urllib2.urlopen(request)
    logging.debug('Opened request to %s', LOGIN_URL)

    logging.debug('Grabbing response data')
    data = response.read().decode('utf-8')
    resp = json.loads(data)
    logging.debug('Got: %s', data)
    if not resp.get('success', False):
        logging.error('Problems suppling credentials to edX.')
        exit(2)

    # This doesn't belong here, probably, but in the validation of the
    # command line options, instead.
    if args.list_courses:
        courses = get_course_list(headers)
        for course in courses:
            print '%s:%s:%s' % course
        sys.exit(0)

    course_urls = []
    for c_id in args.course_id:
        new_url = "%s/courses/%s/courseware" % (EDX_HOMEPAGE, c_id)
        logging.info('Found new course URL: %s', new_url)
        course_urls.append(new_url)

    # FIXME: Put this in a function called get_week_urls_for_course() or
    # similar in intent.

    # FIXME: Consider all courses here.
    # ...
    url = course_urls[0]

    courseware = get_page_contents(url, headers)
    soup = BeautifulSoup(courseware)
    data = soup.find("section",
                     {"class": "content-wrapper"}).section.div.div.nav

    weeks_soup = data.find_all('div')

    weeks = []
    for week_soup in weeks_soup:
        week_name = week_soup.h3.a.string
        week_urls = [
            '%s/%s' % (EDX_HOMEPAGE, a['href'])
            for a in week_soup.ul.find_all('a')
        ]

        weeks.append((week_name, week_urls))

    # FIXME: Take the week into consideration
    # FIXME: Transform this into a function
    # FIXME: Consider all courses here.
    c_id = args.course_id[0]
    logging.info('%s has %d weeks so far.', c_id, len(weeks))

    links = [lec_url for week in weeks for lec_url in week[1]]

    video_ids = []
    for link in links:
        logging.info("Processing '%s'...", link)
        page = get_page_contents(link, headers)
        splitter = re.compile(b'data-streams=(?:&#34;|").*?(?:1.0)?:')
        id_container = splitter.split(page)[1:]
        video_ids += [link[:YOUTUBE_VIDEO_ID_LENGTH] for link in
                      id_container]

    # FIXME: call here download_videos
    for video_id in video_ids:
        print video_id
