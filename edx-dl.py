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
    from urllib.request import URLError
except ImportError:
    from urllib2 import urlopen
    from urllib2 import build_opener
    from urllib2 import install_opener
    from urllib2 import HTTPCookieProcessor
    from urllib2 import Request
    from urllib2 import URLError

# we alias the raw_input function for python 3 compatibility
try:
    input = raw_input
except:
    pass

import argparse
import getpass
import json
import os
import os.path
import re
import sys

from subprocess import Popen, PIPE
from datetime import timedelta, datetime

from bs4 import BeautifulSoup

BASE_URL = 'https://courses.edx.org'
EDX_HOMEPAGE = BASE_URL + '/login_ajax'
LOGIN_API = BASE_URL + '/login_ajax'
DASHBOARD = BASE_URL + '/dashboard'

YOUTUBE_VIDEO_ID_LENGTH = 11


## If no download directory is specified, we use the default one
DEFAULT_DOWNLOAD_DIRECTORY = "Downloaded"
DOWNLOAD_DIRECTORY = DEFAULT_DOWNLOAD_DIRECTORY

## If nothing else is chosen, we chose the default user agent:

DEFAULT_USER_AGENTS = {"chrome": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.31 (KHTML, like Gecko) Chrome/26.0.1410.63 Safari/537.31",
                       "firefox": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.8; rv:24.0) Gecko/20100101 Firefox/24.0",
                       "edx": 'edX-downloader/0.01'}

USER_AGENT = DEFAULT_USER_AGENTS["edx"]

USER_EMAIL = ""
USER_PSWD = ""

video_fmt = None

youtube_subs = None
edx_subs = None


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
    try:
        charset = result.headers.get_content_charset(failobj="utf-8")  # for python3
    except:
        charset = result.info().getparam('charset') or 'utf-8'
    return result.read().decode(charset)


def directory_name(initial_name):
    import string
    allowed_chars = string.digits+string.ascii_letters+" _."
    result_name = ""
    for ch in initial_name:
        if allowed_chars.find(ch) != -1:
            result_name += ch
    return result_name if result_name != "" else "course_folder"


def parse_commandline_options():
    global USER_EMAIL, USER_PSWD, DOWNLOAD_DIRECTORY, USER_AGENT, youtube_subs, edx_subs, video_fmt

    parser = argparse.ArgumentParser(description='A simple tool to download video lectures from edx.org.')
    parser.add_argument('-u', '--user', '--username', action='store', help='username in edX', default='')
    parser.add_argument('-p', '--pswd', '--password', action='store', help='password in edX', default='')
    parser.add_argument('-d', '--dir', '--download-dir', action='store', help='store the files to the specified directory', \
                        default=DEFAULT_DOWNLOAD_DIRECTORY)

    group_ua = parser.add_mutually_exclusive_group()
    group_ua.add_argument('--user-agent', action='store', help='use popular softwares\' user agent', default='edx', \
                          choices=DEFAULT_USER_AGENTS.keys())
    group_ua.add_argument('--custom-user-agent', metavar='USER-AGENT-STRING', action='store', help='specify the user agent string')
    group_st = parser.add_mutually_exclusive_group()
    group_st.add_argument('--subs', '--subtitles', dest='subs', action='store_const', const=(True, True), default=(None, None), help='download the corresponding subtitles')
    group_st.add_argument('--nosubs', '--nosubtitles', dest='subs', action='store_const', const=(False, False), default=(None, None), help='do not download subtitles') 
    parser.add_argument('--format-id', action='store', type=int, help='specify the format id of video files', default=None)
    args = parser.parse_args()

    USER_EMAIL = args.user
    USER_PSWD = args.pswd
    if args.dir.strip()[0] == "~":
        args.dir = os.path.expanduser(args.dir)
    DOWNLOAD_DIRECTORY = args.dir
    USER_AGENT = DEFAULT_USER_AGENTS[args.user_agent]
    if args.custom_user_agent is not None:
        USER_AGENT = args.custom_user_agent
    video_fmt = args.format_id
    youtube_subs, edx_subs = args.subs


def json2srt(o):
    i = 1
    output = ''
    for (s, e, t) in zip(o['start'], o['end'], o['text']):
        if t == "":
            continue
        output += str(i) + '\n'
        s = datetime(1, 1, 1) + timedelta(seconds=s/1000.)
        e = datetime(1, 1, 1) + timedelta(seconds=e/1000.)
        output += "%02d:%02d:%02d,%03d --> %02d:%02d:%02d,%03d" % \
            (s.hour, s.minute, s.second, s.microsecond/1000,
             e.hour, e.minute, e.second, e.microsecond/1000) + '\n'
        output += t + "\n\n"
        i += 1
    return output


def main():
    global USER_EMAIL, USER_PSWD, youtube_subs, edx_subs, video_fmt
    parse_commandline_options()

    if USER_EMAIL == "":
        USER_EMAIL = input('Username: ')
    if USER_PSWD == "":
        USER_PSWD = getpass.getpass()

    if USER_EMAIL == "" or USER_PSWD == "":
        print("You must supply username AND password to log-in")
        sys.exit(2)

    # Prepare Headers
    headers = {
        'User-Agent': USER_AGENT,
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Content-Type': 'application/x-www-form-urlencoded;charset=utf-8',
        'Referer': EDX_HOMEPAGE,
        'X-Requested-With': 'XMLHttpRequest',
        'X-CSRFToken': get_initial_token(),
    }

    # Login
    post_data = urlencode({'email': USER_EMAIL, 'password': USER_PSWD,
                           'remember': False}).encode('utf-8')
    request = Request(LOGIN_API, post_data, headers)
    response = urlopen(request)
    resp = json.loads(response.read().decode('utf-8'))
    if not resp.get('success', False):
        print(resp.get('value', "Wrong Email or Password."))
        exit(2)

    # Get user info/courses
    dash = get_page_contents(DASHBOARD, headers)
    soup = BeautifulSoup(dash)
    data = soup.find_all('ul')[1]
    USERNAME = data.find_all('span')[1].string
    COURSES = soup.find_all('article', 'course')
    courses = []
    for COURSE in COURSES:
        c_name = COURSE.h3.text.strip()
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
        print('%d - Download %s videos' % (w, week[0].strip()))
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
    subsUrls = []
    regexpSubs = re.compile(r'data-caption-asset-path=(?:&#34;|")([^"&]*)(?:&#34;|")')
    splitter = re.compile(r'data-streams=(?:&#34;|").*1.0[0]*:')
    extra_youtube = re.compile(r'//w{0,3}\.youtube.com/embed/([^ \?&]*)[\?& ]')
    for link in links:
        print("Processing '%s'..." % link)
        page = get_page_contents(link, headers)

        id_container = splitter.split(page)[1:]
        video_id += [link[:YOUTUBE_VIDEO_ID_LENGTH] for link in
                     id_container]
        subsUrls += [BASE_URL + regexpSubs.search(container).group(1) + id + ".srt.sjson"
                        for id, container in zip(video_id[-len(id_container):], id_container)]
        # Try to download some extra videos which is referred by iframe
        extra_ids = extra_youtube.findall(page)
        video_id += [link[:YOUTUBE_VIDEO_ID_LENGTH] for link in
                     extra_ids]
        subsUrls += ['' for link in extra_ids]

    video_link = ['http://youtube.com/watch?v=' + v_id
                  for v_id in video_id]

    if len(video_link) < 1:
      print('WARNING: No downloadable video found.')
      sys.exit(0)
    if video_fmt is None:
        # Get Available Video_Fmts
        os.system('youtube-dl -F %s' % video_link[-1])
        video_fmt = int(input('Choose Format code: '))

    # Get subtitles
    if (youtube_subs is None or edx_subs is None):
        down_subs = input('Download subtitles (y/n)? ')
        if str.lower(down_subs) == 'y':
            youtube_subs = True
            edx_subs = True
        else:
            youtube_subs = False
            edx_subs = False

    # Say where it's gonna download files, just for clarity's sake.
    print("[download] Saving videos into: " + DOWNLOAD_DIRECTORY)

    # Download Videos
    c = 0
    for v, s in zip(video_link, subsUrls):
        c += 1
        target_dir = os.path.join(DOWNLOAD_DIRECTORY,
                                  directory_name(selected_course[0]))
        filename_prefix = str(c).zfill(2)
        cmd = ["youtube-dl",
               "-o", os.path.join(target_dir, filename_prefix + "-%(title)s.%(ext)s"),
               "-f", str(video_fmt)]
        if youtube_subs:
            cmd.append('--write-sub')
        cmd.append(str(v))

        popen_youtube = Popen(cmd, stdout=PIPE, stderr=PIPE)

        youtube_stdout = b''
        enc = sys.getdefaultencoding()
        while True:  # Save output to youtube_stdout while this being echoed
            tmp = popen_youtube.stdout.read(1)
            youtube_stdout += tmp
            print(tmp.decode(enc), end="")
            sys.stdout.flush()
            # do it until the process finish and there isn't output
            if tmp == b"" and popen_youtube.poll() is not None:
                break

        if youtube_subs:
            youtube_stderr = popen_youtube.communicate()[1]
            if re.search(b'Some error while getting the subtitles',
                         youtube_stderr):
                if edx_subs:
                    print("YouTube hasn't subtitles. Fallbacking from edX")
                else:
                    print("WARNING: Subtitles missing")

        if edx_subs and s != '':  # write edX subs
            filenames = os.listdir(target_dir)
            subs_filename = filename_prefix
            for name in filenames:  # Find the filename of the downloaded video
                if name.startswith(filename_prefix):
                    (basename, ext) = os.path.splitext(name)
                    subs_filename = basename
                    if ext == '.srt':
                        subs_filename = ''  # Don't download if sub is there
                        break
            if subs_filename != '':
                try:
                    jsonString = get_page_contents(s, headers)
                    jsonObject = json.loads(jsonString)
                    subs_string = json2srt(jsonObject)

                    subs_filename += '.srt'
                    print('[download] edX subtitles: %s' % subs_filename)
                    open(os.path.join(os.getcwd(), subs_filename),
                         'wb+').write(subs_string.encode('utf-8'))
                except URLError as e:
                    print('Warning: edX subtitles (error:%s)' % e.reason)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nCTRL-C detected, shutting down....")
        sys.exit(0)
