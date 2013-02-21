#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import http.cookiejar
import json
import logging
import os
import re
import sys
import urllib.request, urllib.parse, urllib.error
import urllib.request, urllib.error, urllib.parse

from bs4 import BeautifulSoup


EDX_HOMEPAGE = 'https://www.edx.org'
LOGIN_API = 'https://www.edx.org/login'
DASHBOARD = 'https://www.edx.org/dashboard'
YOUTUBE_VIDEO_ID_LENGTH = 11


def get_initial_token():
    """
    Create initial connection to get authentication token for future requests.

    Returns a string to be used in subsequent connections with the
    X-CSRFToken header or the empty string if we didn't find any token in
    the cookies.
    """
    cj = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    urllib.request.install_opener(opener)
    opener.open(EDX_HOMEPAGE)

    for cookie in cj:
        if cookie.name == 'csrftoken':
            return cookie.value

    return ''


def get_page_contents(url, headers):
    """
    Get the contents of the page at the URL given by url. While making the
    request, we use the headers given in the dictionary in headers.
    """
    result = urllib.request.urlopen(urllib.request.Request(url, None, headers))
    return result.read()


def parse_args():
    """
    Parse the arguments/options passed to the program on the command line.
    """

    parser = argparse.ArgumentParser(description='Download videos from edX.')

    # positional
    parser.add_argument('username',
                        action='store',
                        help='your edX username (email)')
    parser.add_argument('password',
                        action='store',
                        help='your edX password')

    # optional
    parser.add_argument('-i',
                        '--course_id',
                        dest='course_id',
                        action='store',
                        default=None,
                        help='target course id which can be obtained by \'-l\'')

    parser.add_argument('-s',
                        '--with-subtitles',
                        dest='subtitles',
                        action='store_true',
                        default=False,
                        help='download subtitles with the videos')
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
                        dest='show_courses',
                        action='store_true',
                        default=False,
                        help='show list of courses currently enrolled')


    args = parser.parse_args()

    # The following friendly
    # # FIXME: check arguments
    # if not args.username:
        # logging.error('No username specified.')
        # sys.exit(1)
    # if not args.password:
        # logging.error('No password specified.')
        # sys.exit(1)

    return args


if __name__ == '__main__':
    args = parse_args()

    user_email = args.username
    user_pswd = args.password
    video_fmt = args.format

    # Prepare Headers
    headers = {
        'User-Agent': 'edX-downloader/0.01',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Content-Type': 'application/x-www-form-urlencoded;charset=utf-8',
        'Referer': EDX_HOMEPAGE,
        'X-Requested-With': 'XMLHttpRequest',
        'X-CSRFToken': get_initial_token(),
        }

    # Login
    post_data = urllib.parse.urlencode({'email': user_email,
                                 'password': user_pswd,
                                 'remember': False}).encode('utf-8')
    request = urllib.request.Request(LOGIN_API, post_data, headers)
    response = urllib.request.urlopen(request)
    resp = json.loads(response.read().decode('utf-8'))
    if not resp.get('success', False):
        logging.error('Problems suppling credentials to edX.')
        exit(2)


    # Get user info/courses
    dash = get_page_contents(DASHBOARD, headers)
    soup = BeautifulSoup(dash)
    data = soup.find_all('ul')[1]
    USERNAME = data.find_all('span')[1].string
    USEREMAIL = data.find_all('span')[3].string
    COURSES = soup.find_all('article', 'my-course')
    courses = []
    for COURSE in COURSES:
        c_name = COURSE.h3.string
        c_link = 'https://www.edx.org' + COURSE.a['href']
        if c_link.endswith('info') or c_link.endswith('info/'):
            state = 'Started'
        else:
            state = 'Not yet'
        courses.append((c_name, c_link, state))
    numOfCourses = len(courses)

    # Welcome and Choose Course

    logging.info('Logged as %s.', USERNAME)
    logging.info('Number of courses on edX: %d', numOfCourses)

    c = 0
    for course in courses:
        c += 1
        print('%d - %s -> %s' % (c, course[0], course[2]))

    c_number = int(input('Enter Course Number: '))
    while c_number > numOfCourses or courses[c_number - 1][2] != 'Started':
        print('Enter a valid Number for a Started Course ! between 1 and ', \
            numOfCourses)
        c_number = int(input('Enter Course Number: '))
    selected_course = courses[c_number - 1]
    COURSEWARE = selected_course[1].replace('info', 'courseware')


    ## Getting Available Weeks
    courseware = get_page_contents(COURSEWARE, headers)
    soup = BeautifulSoup(courseware)
    data = soup.section.section.div.div.nav
    WEEKS = data.find_all('div')
    weeks = [(w.h3.a.string, ['https://www.edx.org' + a['href'] for a in
             w.ul.find_all('a')]) for w in WEEKS]
    numOfWeeks = len(weeks)


    # Choose Week or choose all
    print('%s has %d weeks so far' % (selected_course[0], numOfWeeks))
    w = 0
    for week in weeks:
        w += 1
        print('%d - Download %s videos' % (w, week[0]))
    print('%d - Download them all' % (numOfWeeks + 1))

    w_number = int(input('Enter Your Choice: '))
    while w_number > numOfWeeks + 1:
        print('Enter a valid Number between 1 and %d' % (numOfWeeks + 1))
        w_number = int(input('Enter Your Choice: '))

    if w_number == numOfWeeks + 1:
        links = [link for week in weeks for link in week[1]]
    else:
        links = weeks[w_number - 1][1]


    video_id = []
    for link in links:
        logging.info("Processing '%s'...", link)
        page = get_page_contents(link, headers)
        splitter = re.compile('data-streams=(?:&#34;|").*:')
        id_container = splitter.split(page)[1:]
        video_id += [link[:YOUTUBE_VIDEO_ID_LENGTH] for link in
                     id_container]

    video_link = ['http://youtube.com/watch?v=' + v_id for v_id in video_id]



    # Download Videos
    c = 0
    for v in video_link:
        c += 1
        cmd = 'youtube-dl -o "Downloaded/' + selected_course[0] + '/' + str(c).zfill(2) + '-%(title)s.%(ext)s" -f ' + str(video_fmt)
        if args.subtitles:
            cmd += ' --write-srt'
        cmd += ' ' + v
        os.system(cmd)