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

import getopt
import getpass

import json
import os
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
DEFAULT_DOWNLOAD_DIRECTORY = "./Downloaded/"
DOWNLOAD_DIRECTORY = DEFAULT_DOWNLOAD_DIRECTORY

## If nothing else is chosen, we chose the default user agent:

DEFAULT_USER_AGENTS = {"google-chrome": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.31 (KHTML, like Gecko) Chrome/26.0.1410.63 Safari/537.31",
                       "firefox": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.8; rv:24.0) Gecko/20100101 Firefox/24.0",
                       "default": 'edX-downloader/0.01'}

USER_AGENT = DEFAULT_USER_AGENTS["default"]

USER_EMAIL = ""
USER_PSWD = ""


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
        charset = result.headers.get_content_charset(failobj="utf-8")  #for python3
    except:
        charset = result.info().getparam('charset') or 'utf-8'

    return result.read().decode(charset)

def directory_name(initial_name):
    import string
    allowed_chars = string.digits+string.ascii_letters+" _."
    result_name = ""
    for ch in initial_name:
        if allowed_chars.find(ch) != -1:
            result_name+=ch
    return result_name if result_name != "" else "course_folder"

def parse_commandline_options(argv):
    global USER_EMAIL, USER_PSWD, DOWNLOAD_DIRECTORY, USER_AGENT
    opts, args = getopt.getopt(argv,
                               "u:p:",
                               ["download-dir=", "user-agent=", "custom-user-agent="])
    for opt, arg in opts :
        if opt == "-u" :
            USER_EMAIL = arg

        elif opt == "-p" :
            USER_PSWD = arg

        elif opt == "--download-dir" :
            if arg.strip()[0] == "~" :
                arg = os.path.expanduser(arg)
            DOWNLOAD_DIRECTORY = arg

        elif opt == "--user-agent" :
            if arg in DEFAULT_USER_AGENTS.keys():
                USER_AGENT = DEFAULT_USER_AGENTS[arg]


        elif opt == "--custom-user-agent":
            USER_AGENT = arg

        elif opt == "-h":
            usage()


def usage() :
    print("command-line options:")
    print("""-u <username>: (Optional) indicate the username.
-p <password>: (Optional) indicate the password.
--download-dir=<path>: (Optional) save downloaded files in <path>
--user-agent=<chrome|firefox>: (Optional) use Google Chrome's of Firefox 24's
             default user agent as user agent
--custom-user-agent="MYUSERAGENT": (Optional) use the string "MYUSERAGENT" as
             user agent
""")


def downloadEdxSubs(url, headers):
    jsonString = get_page_contents(url, headers)
    jsonObject = json.loads(jsonString)

    starts = jsonObject['start']
    ends = jsonObject['end']
    texts = jsonObject['text']

    i = 1

    output = ''

    for (s, e, t) in zip(starts, ends, texts):
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
    global USER_EMAIL, USER_PSWD
    try:
        parse_commandline_options(sys.argv[1:])
    except getopt.GetoptError:
        usage()
        sys.exit(2)

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
    USEREMAIL = data.find_all('span')[3].string
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
    for link in links:
        print("Processing '%s'..." % link)
        page = get_page_contents(link, headers)
        id_container = splitter.split(page)[1:]
        video_id += [link[:YOUTUBE_VIDEO_ID_LENGTH] for link in
                     id_container]

        subsUrls += [BASE_URL + regexpSubs.search(container).group(1) + id + ".srt.sjson"
                        for id, container in zip(video_id[-len(id_container):], id_container)]

    video_link = ['http://youtube.com/watch?v=' + v_id
                  for v_id in video_id]

    # Get Available Video_Fmts
    os.system('youtube-dl -F %s' % video_link[-1])
    video_fmt = int(input('Choose Format code: '))

    # Get subtitles
    temp = input('Download subtitles (Y/n)? ')
    if str.lower(temp) == 'n':
        youtube_subs = False
        edx_subs = False
    else:
        print("""Get from:
1) YouTube with fallback from edX (default)
2) YouTube only
3) edX's subs only""")
        try:
            temp = int(input(""))
            if temp not in (1, 2, 3):
                raise ValueError
        except ValueError:
            temp = 1

        if temp == 1:
            youtube_subs = True
            fallback_subs = True
            edx_subs = False
            print("Selected: YouTube with fallback from edX")
        elif temp == 2:
            youtube_subs = True
            fallback_subs = False
            edx_subs = False
            print("Selected: YouTube only")
        elif temp == 3:
            youtube_subs = False
            fallback_subs = False
            edx_subs = True
            print("Selected: edX's subs only")

    # Say where it's gonna download files, just for clarity's sake.
    print("Saving videos into: " + DOWNLOAD_DIRECTORY)
    print("\n\n")

    # Download Videos
    c = 0
    for v, s in zip(video_link, subsUrls):
        c += 1
        cmd = ["youtube-dl", "-o", DOWNLOAD_DIRECTORY + '/' + directory_name(selected_course[0]) + '/' +
                                   str(c).zfill(2) + "-%(title)s.%(ext)s", "-f", str(video_fmt)]
        if youtube_subs:
            cmd.append('--write-srt')
        cmd.append(str(v))

        popen_youtube = Popen(cmd, stdout=PIPE, stderr=PIPE)

        if edx_subs:  # If the user selected download from edX: download simultaneously video and subs
            subs_string = downloadEdxSubs(s, headers)

        youtube_stdout = b''
        enc = sys.getdefaultencoding()
        while True:  # Save the output to youtube_stdout while this being echoed
            tmp = popen_youtube.stdout.read(1)
            youtube_stdout += tmp
            print(tmp.decode(enc), end="")
            sys.stdout.flush()
            # do it until the process finish and there isn't output
            if tmp == b"" and popen_youtube.poll() is not None:
                break

        if youtube_subs:
            youtube_stderr = popen_youtube.communicate()[1]
            if re.search(b'Some error while getting the subtitles', youtube_stderr):
                if fallback_subs:
                    print("YouTube hasn't subtitles. Fallbacking from edX")
                    edx_subs = True
                else:
                    print("WARNING: Subtitles missing")

        if edx_subs:  # write edX subs
            if fallback_subs:  # if edx_subs and fallback_subs are True this means YouTube hasn't subtitles
                               # and the user select fallback from edX
                subs_string = downloadEdxSubs(s, headers)
            regexp_filename = re.compile(
                b'(?:\[download\] ([^\n^\r]*?)(?: has already been downloaded))|(?:Destination: *([^\n^\r]*))')
            match = re.search(regexp_filename, youtube_stdout)
            subs_filename = (match.group(1) or match.group(2)).decode('utf-8')[:-4]
            open(os.path.join(os.getcwd(), subs_filename)+'.srt', 'w+').write(subs_string)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt :
        print("\n\nCTRL-C detected, shutting down....")
        sys.exit(0)
