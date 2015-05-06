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

OPENEDX_SITES = {
    'edx': {
        'url': 'https://courses.edx.org',
        'courseware-selector': ('nav', {'aria-label': 'Course Navigation'}),
    },
    'stanford': {
        'url': 'https://class.stanford.edu',
        'courseware-selector': ('nav', {'aria-label': 'Course Navigation'}),
    },
    'usyd-sit': {
        'url': 'http://online.it.usyd.edu.au',
        'courseware-selector': ('nav', {'aria-label': 'Course Navigation'}),
    },
}
BASE_URL = OPENEDX_SITES['edx']['url']
EDX_HOMEPAGE = BASE_URL + '/login_ajax'
LOGIN_API = BASE_URL + '/login_ajax'
DASHBOARD = BASE_URL + '/dashboard'
COURSEWARE_SEL = OPENEDX_SITES['edx']['courseware-selector']

YOUTUBE_VIDEO_ID_LENGTH = 11

# If nothing else is chosen, we chose the default user agent

DEFAULT_USER_AGENTS = {
    "chrome": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.31 (KHTML, like Gecko) Chrome/26.0.1410.63 Safari/537.31",
    "firefox": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.8; rv:24.0) Gecko/20100101 Firefox/24.0",
    "edx": 'edX-downloader/0.01'
}

USER_AGENT = DEFAULT_USER_AGENTS["edx"]

# To replace the print function, the following function must be placed
# before any other call for print


def print(*objects, **kwargs):
    """
    Overload the print function to adapt for the encoding bug in Windows Console.
    It will try to convert text to the console encoding before print to prevent crashes.
    """
    try:
        stream = kwargs.get('file', None)
        if stream is None:
            stream = sys.stdout
        enc = stream.encoding
        if enc is None:
            enc = sys.getdefaultencoding()
    except AttributeError:
        return __builtins__.print(*objects, **kwargs)
    texts = []
    for object in objects:
        try:
            original_text = str(object)
        except UnicodeEncodeError:
            original_text = unicode(object)
        texts.append(original_text.encode(enc, errors='replace').decode(enc))
    return __builtins__.print(*texts, **kwargs)


def change_openedx_site(site_name):
    global BASE_URL
    global EDX_HOMEPAGE
    global LOGIN_API
    global DASHBOARD
    global COURSEWARE_SEL

    if site_name not in OPENEDX_SITES.keys():
        print("OpenEdX platform should be one of: %s" % ', '.join(OPENEDX_SITES.keys()))
        sys.exit(2)

    BASE_URL = OPENEDX_SITES[site_name]['url']
    EDX_HOMEPAGE = BASE_URL + '/login_ajax'
    LOGIN_API = BASE_URL + '/login_ajax'
    DASHBOARD = BASE_URL + '/dashboard'
    COURSEWARE_SEL = OPENEDX_SITES[site_name]['courseware-selector']


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

def get_available_weeks(courseware):
    soup = BeautifulSoup(courseware)
    data = soup.find(*COURSEWARE_SEL)

    if not data:
        WEEKS = soup.find_all('div', attrs={'class': 'chapter'})
    else:
        WEEKS = data.find_all('div')

    weeks = [(w.h3.a.string, [BASE_URL + a['href'] for a in
             w.ul.find_all('a')]) for w in WEEKS]

    return weeks

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
    allowed_chars = string.digits + string.ascii_letters + " _."
    result_name = ""
    for ch in initial_name:
        if allowed_chars.find(ch) != -1:
            result_name += ch
    return result_name if result_name != "" else "course_folder"


def edx_json2srt(o):
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


def edx_get_subtitle(url, headers):
    """ returns a string with the subtitles content from the url """
    """ or None if no subtitles are available """
    try:
        jsonString = get_page_contents(url, headers)
        jsonObject = json.loads(jsonString)
        return edx_json2srt(jsonObject)
    except URLError as e:
        print('[warning] edX subtitles (error:%s)' % e.reason)
        return None
    except ValueError as e:
        print('[warning] edX subtitles (error:%s)' % e.message)
        return None


def parse_args():
    """
    Parse the arguments/options passed to the program on the command line.
    """
    parser = argparse.ArgumentParser(prog='edx-dl',
                                     description='Get videos from the OpenEdX platform',
                                     epilog='For further use information,'
                                     'see the file README.md',)
    # positional
    parser.add_argument('course_id',
                        nargs='*',
                        action='store',
                        default=None,
                        help='target course id '
                        '(e.g., https://courses.edx.org/courses/BerkeleyX/CS191x/2013_Spring/info/)'
                        )

    # optional
    parser.add_argument('-u',
                        '--username',
                        action='store',
                        help='your edX username (email)')
    parser.add_argument('-p',
                        '--password',
                        action='store',
                        help='your edX password')
    parser.add_argument('-f',
                        '--format',
                        dest='format',
                        action='store',
                        default=None,
                        help='format of videos to download')
    parser.add_argument('-s',
                        '--with-subtitles',
                        dest='subtitles',
                        action='store_true',
                        default=False,
                        help='download subtitles with the videos')
    parser.add_argument('-o',
                        '--output-dir',
                        action='store',
                        dest='output_dir',
                        help='store the files to the specified directory',
                        default='Downloaded')
    parser.add_argument('-x',
                        '--platform',
                        action='store',
                        dest='platform',
                        help='OpenEdX platform, currently either "edx", "stanford" or "usyd-sit"',
                        default='edx')

    args = parser.parse_args()
    return args


def main():
    args = parse_args()

    # if no args means we are calling the interactive version
    is_interactive = len(sys.argv) == 1
    if is_interactive:
        args.platform = input('Platform: ')
        args.username = input('Username: ')
        args.password = getpass.getpass()

    change_openedx_site(args.platform)

    if not args.username or not args.password:
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
    post_data = urlencode({'email': args.username, 'password': args.password,
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
    COURSES = soup.find_all('article', 'course')
    courses = []
    for COURSE in COURSES:
        c_name = COURSE.h3.text.strip()
        c_link = None
        state = 'Not yet'
        try:
            # started courses include the course link in the href attribute
            c_link = BASE_URL + COURSE.a['href']
            if c_link.endswith('info') or c_link.endswith('info/'):
                state = 'Started'
        except KeyError:
            pass
        courses.append((c_name, c_link, state))
    numOfCourses = len(courses)

    # Welcome and Choose Course

    print('You can access %d courses' % numOfCourses)

    for idx, course in enumerate(courses, 1):
        print('%d - %s -> %s' % (idx, course[0], course[2]))

    c_number = int(input('Enter Course Number: '))
    while c_number > numOfCourses or courses[c_number - 1][2] != 'Started':
        print('Enter a valid Number for a Started Course ! between 1 and ',
              numOfCourses)
        c_number = int(input('Enter Course Number: '))
    selected_course = courses[c_number - 1]
    COURSEWARE = selected_course[1].replace('info', 'courseware')

    # Get Available Weeks
    courseware = get_page_contents(COURSEWARE, headers)
    weeks = get_available_weeks(courseware)
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

    if is_interactive:
        args.subtitles = input('Download subtitles (y/n)? ').lower() == 'y'

    video_ids = []
    sub_urls = []
    splitter = re.compile(r'data-streams=(?:&#34;|").*1.0[0]*:')
    re_subs = re.compile(r'data-transcript-translation-url=(?:&#34;|")([^"&]*)(?:&#34;|")')
    extra_youtube = re.compile(r'//w{0,3}\.youtube.com/embed/([^ \?&]*)[\?& ]')
    for link in links:
        print("Processing '%s'..." % link)
        page = get_page_contents(link, headers)
        sections = splitter.split(page)[1:]
        for section in sections:
            video_id = section[:YOUTUBE_VIDEO_ID_LENGTH]
            sub_url = ''
            if args.subtitles:
                match_subs = re_subs.search(section)
                if match_subs:
                    sub_url = BASE_URL + match_subs.group(1) + "/en" + "?videoId=" + video_id
            video_ids += [video_id]
            sub_urls += [sub_url]
        # Try to download some extra videos which is referred by iframe
        extra_ids = extra_youtube.findall(page)
        video_ids += [link[:YOUTUBE_VIDEO_ID_LENGTH] for link in
                      extra_ids]
        sub_urls += ['' for e_id in extra_ids]

    video_urls = ['http://youtube.com/watch?v=' + v_id
                  for v_id in video_ids]

    if len(video_urls) < 1:
        print('WARNING: No downloadable video found.')
        sys.exit(0)

    if is_interactive:
        # Get Available Video formats
        os.system('youtube-dl -F %s' % video_urls[-1])
        print('Choose a valid format or a set of valid format codes e.g. 22/17/...')
        args.format = input('Choose Format code: ')

    print("[info] Output directory: " + args.output_dir)

    # Download Videos
    c = 0
    for v, s in zip(video_urls, sub_urls):
        c += 1
        target_dir = os.path.join(args.output_dir,
                                  directory_name(selected_course[0]))
        filename_prefix = str(c).zfill(2)
        cmd = ["youtube-dl",
               "-o", os.path.join(target_dir, filename_prefix + "-%(title)s.%(ext)s")]
        if args.format:
            cmd.append("-f")
            # defaults to mp4 in case the requested format isn't available
            cmd.append(args.format + '/mp4')
        if args.subtitles:
            cmd.append('--write-sub')
        cmd.append(str(v))

        popen_youtube = Popen(cmd, stdout=PIPE, stderr=PIPE)

        youtube_stdout = b''
        while True:  # Save output to youtube_stdout while this being echoed
            tmp = popen_youtube.stdout.read(1)
            youtube_stdout += tmp
            print(tmp, end="")
            sys.stdout.flush()
            # do it until the process finish and there isn't output
            if tmp == b"" and popen_youtube.poll() is not None:
                break

        if args.subtitles:
            filename = get_filename(target_dir, filename_prefix)
            subs_filename = os.path.join(target_dir, filename + '.srt')
            if not os.path.exists(subs_filename):
                subs_string = edx_get_subtitle(s, headers)
                if subs_string:
                    print('[info] Writing edX subtitles: %s' % subs_filename)
                    open(os.path.join(os.getcwd(), subs_filename),
                         'wb+').write(subs_string.encode('utf-8'))


def get_filename(target_dir, filename_prefix):
    """ returns the basename for the corresponding filename_prefix """
    # this whole function is not the nicest thing, but isolating it makes
    # things clearer , a good refactoring would be to get
    # the info from the video_url or the current output, to avoid the
    # iteration from the current dir
    filenames = os.listdir(target_dir)
    for name in filenames:  # Find the filename of the downloaded video
        if name.startswith(filename_prefix):
            (basename, ext) = os.path.splitext(name)
            return basename

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nCTRL-C detected, shutting down....")
        sys.exit(0)
