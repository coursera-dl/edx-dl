#!/usr/bin/env python
# -*- coding: utf-8 -*-

# python 2/3 compatibility imports
from __future__ import print_function
from __future__ import unicode_literals

try:
    from http.cookiejar import CookieJar
except ImportError:
    from cookielib import CookieJar

try:
    from urllib.parse import urlencode
except ImportError:
    from urllib import urlencode

try:
    from urllib.request import urlopen
    from urllib.request import build_opener
    from urllib.request import install_opener
    from urllib.request import HTTPCookieProcessor
    from urllib.request import Request
except ImportError:
    from urllib2 import urlopen
    from urllib2 import build_opener
    from urllib2 import install_opener
    from urllib2 import HTTPCookieProcessor
    from urllib2 import Request
# we alias the raw_input function for python 3 compatibility
try:
    input = raw_input
except:
    pass

import json
import os
import re
import sys

from bs4 import BeautifulSoup

EDX_HOMEPAGE = 'https://courses.edx.org/login'
LOGIN_API = 'https://courses.edx.org/login_ajax'
DASHBOARD = 'https://courses.edx.org/dashboard'
YOUTUBE_VIDEO_ID_LENGTH = 11


def get_initial_token():
    """
    Create initial connection to get authentication token for future requests.

    Returns a string to be used in subsequent connections with the
    X-CSRFToken header or the empty string if we didn't find any token in
    the cookies.
    """
    cj = CookieJar()
    opener = build_opener(HTTPCookieProcessor(cj))
    install_opener(opener)
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
    result = urlopen(Request(url, None, headers))
    return result.read()


if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.exit(1)

    user_email = sys.argv[1]
    user_pswd = sys.argv[2]

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
    post_data = urlencode({'email': user_email, 'password': user_pswd,
                           'remember': False}).encode('utf-8')
    request = Request(LOGIN_API, post_data, headers)
    response = urlopen(request)
    resp = json.loads(response.read().decode('utf-8'))
    if not resp.get('success', False):
        print("Wrong Email or Password.")
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
        c_link = 'https://courses.edx.org' + COURSE.a['href']
        if c_link.endswith('info') or c_link.endswith('info/'):
            state = 'Started'
        else:
            state = 'Not yet'
        courses.append((c_name, c_link, state))
    numOfCourses = len(courses)

    # Welcome and Choose Course

    print('Welcome %s' % USERNAME)
    print('You can access %d courses on edX' % numOfCourses)

    c = 0
    for course in courses:
        c += 1
        print('%d - %s -> %s' % (c, course[0], course[2]))

    c_number = int(input('Enter Course Number: '))
    while c_number > numOfCourses or courses[c_number - 1][2] != 'Started':
        print('Enter a valid Number for a Started Course ! between 1 and ',
              numOfCourses)
        c_number = int(input('Enter Course Number: '))
    selected_course = courses[c_number - 1]
    COURSEWARE = selected_course[1].replace('info', 'courseware')

    ## Getting Available Weeks
    courseware = get_page_contents(COURSEWARE, headers)
    soup = BeautifulSoup(courseware)

    data = soup.find("section",
                     {"class": "content-wrapper"}).section.div.div.nav
    WEEKS = data.find_all('div')
    weeks = [(w.h3.a.string, ['https://courses.edx.org' + a['href'] for a in
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
        print("Processing '%s'..." % link)
        page = get_page_contents(link, headers)
        splitter = re.compile(b'data-streams=(?:&#34;|").*1.0[0]*:')
        id_container = splitter.split(page)[1:]
        video_id += [link[:YOUTUBE_VIDEO_ID_LENGTH] for link in
                     id_container]

    video_link = ['http://youtube.com/watch?v=' + v_id.decode("utf-8")
                  for v_id in video_id]

    # Get Available Video_Fmts
    os.system('youtube-dl -F %s' % video_link[-1])
    video_fmt = int(input('Choose Format code: '))

    # Get subtitles
    subtitles = input('Download subtitles (y/n)? ') == 'y'

    # Download Videos
    c = 0
    for v in video_link:
        c += 1
        cmd = 'youtube-dl -o "Downloaded/' + selected_course[0] + '/' + \
              str(c).zfill(2) + '-%(title)s.%(ext)s" -f ' + str(video_fmt)
        if subtitles:
            cmd += ' --write-srt'
        cmd += ' ' + str(v)
        os.system(cmd)
