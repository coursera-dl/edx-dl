#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import getpass
import json
import os
import os.path
import re
import sys

from collections import namedtuple
from datetime import timedelta, datetime
from functools import partial
from multiprocessing.dummy import Pool as ThreadPool

from subprocess import Popen, PIPE

from bs4 import BeautifulSoup as BeautifulSoup_
# Force use of bs4 with html5lib
BeautifulSoup = lambda page: BeautifulSoup_(page, 'html5lib')

from .compat import *

OPENEDX_SITES = {
    'edx': {
        'url': 'https://courses.edx.org',
        'courseware-selector': ('nav', {'aria-label': 'Course Navigation'}),
    },
    'stanford': {
        'url': 'https://lagunita.stanford.edu',
        'courseware-selector': ('nav', {'aria-label': 'Course Navigation'}),
    },
    'usyd-sit': {
        'url': 'http://online.it.usyd.edu.au',
        'courseware-selector': ('nav', {'aria-label': 'Course Navigation'}),
    },
    'fun': {
        'url': 'https://www.france-universite-numerique-mooc.fr',
        'courseware-selector': ('section', {'aria-label': 'Menu du cours'}),
    },
    'gwu-seas': {
        'url': 'http://openedx.seas.gwu.edu',
        'courseware-selector': ('nav', {'aria-label': 'Course Navigation'}),
    },
    'gwu-open': {
        'url': 'http://mooc.online.gwu.edu',
        'courseware-selector': ('nav', {'aria-label': 'Course Navigation'}),
    },
}
BASE_URL = OPENEDX_SITES['edx']['url']
EDX_HOMEPAGE = BASE_URL + '/login_ajax'
LOGIN_API = BASE_URL + '/login_ajax'
DASHBOARD = BASE_URL + '/dashboard'
COURSEWARE_SEL = OPENEDX_SITES['edx']['courseware-selector']

YOUTUBE_VIDEO_ID_LENGTH = 11

# This four tuples represent the structure of courses in edX.
# Notice that we don't represent the full tree structure for both performance
# and UX reasons:
# Course ->  [Section] -> [SubSection] -> [Unit]
# In the script the data structures used are:
# Course, Section->[SubSection], all_units = {Subsection.url: [Unit]}
Course = namedtuple('Course', ['id', 'name', 'url', 'state'])
# Notice that subsection is a list of SubSection tuples and it is the only
# part where we explicitly represent the parent-children relation.
Section = namedtuple('Section', ['position', 'name', 'url', 'subsections'])
SubSection = namedtuple('SubSection', ['position', 'name', 'url'])
Unit = namedtuple('Unit', ['video_youtube_url', 'sub_urls'])


# To replace the print function, the following function must be placed
# before any other call for print
def print(*objects, **kwargs):
    """
    Overload the print function to adapt for the encoding bug in Windows
    console.

    It will try to convert text to the console encoding before printing to
    prevent crashes.
    """
    try:
        stream = kwargs.get('file', None)
        if stream is None:
            stream = sys.stdout
        enc = stream.encoding
        if enc is None:
            enc = sys.getdefaultencoding()
    except AttributeError:
        return builtins.print(*objects, **kwargs)

    texts = []
    for object in objects:
        try:
            if type(object) is bytes:
                if sys.version_info < (3, 0):
                    # in python 2 bytes must be converted to str before decode
                    object = str(object)
                original_text = object.decode(enc, errors='replace')
            else:
                if sys.version_info < (3, 0):
                    object = unicode(object)
                original_text = object.encode(enc, errors='replace').decode(enc, errors='replace')
        except UnicodeEncodeError:
            original_text = unicode(object).encode(enc, errors='replace').decode(enc, errors='replace')
        texts.append(original_text)
    return builtins.print(*texts, **kwargs)


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


def display_courses(courses):
    """
    List the courses that the user has enrolled.
    """

    print('You can access %d courses' % len(courses))
    for i, course in enumerate(courses, 1):
        print('%d - [%s] - %s' % (i, course.state, course.name))


def get_courses_info(url, headers):
    """
    Extracts the courses information from the dashboard.
    """
    dash = get_page_contents(url, headers)
    soup = BeautifulSoup(dash)
    courses_soup = soup.find_all('article', 'course')
    courses = []
    for course_soup in courses_soup:
        course_id = None
        course_name = course_soup.h3.text.strip()
        course_url = None
        course_state = 'Not yet'
        try:
            # started courses include the course link in the href attribute
            course_url = BASE_URL + course_soup.a['href']
            if course_url.endswith('info') or course_url.endswith('info/'):
                course_state = 'Started'
            # The id of a course in edX is composed by the path
            # {organization}/{course_number}/{course_run]
            course_id = course_soup.a['href'][9:-5]
        except KeyError:
            pass
        courses.append(Course(id=course_id,
                              name=course_name,
                              url=course_url,
                              state=course_state))
    return courses


def get_selected_course(courses):
    """
    Retrieve the course that the user selected.
    """
    num_of_courses = len(courses)

    c_number = None
    while True:
        c_number = int(input('Enter Course Number: '))

        if c_number not in range(1, num_of_courses+1):
            print('Enter a valid number between 1 and ', num_of_courses)
            continue
        elif courses[c_number - 1].state != 'Started':
            print('The course has not started!')
            continue
        else:
            break

    selected_course = courses[c_number - 1]
    return selected_course


def _get_initial_token(url):
    """
    Create initial connection to get authentication token for future
    requests.

    Returns a string to be used in subsequent connections with the
    X-CSRFToken header or the empty string if we didn't find any token in
    the cookies.
    """
    cj = CookieJar()
    opener = build_opener(HTTPCookieProcessor(cj))
    install_opener(opener)
    opener.open(url)

    for cookie in cj:
        if cookie.name == 'csrftoken':
            return cookie.value

    return ''


def get_available_sections(url, headers):
    """
    Extracts the sections and subsections from a given url
    """
    def _make_url(section_soup):  # FIXME: Extract from here and test
        return BASE_URL + section_soup.ul.find('a')['href']

    def _get_section_name(section_soup):  # FIXME: Extract from here and test
        return section_soup.h3.a.string.strip()

    def _make_subsections(section_soup):
        subsections_soup = section_soup.ul.find_all("li")
        # FIXME correct extraction of subsection.name (unicode)
        subsections = [SubSection(position=i,
                                  url=BASE_URL + s.a['href'],
                                  name=s.p.string)
                       for i, s in enumerate(subsections_soup, 1)]
        return subsections

    courseware = get_page_contents(url, headers)
    soup = BeautifulSoup(courseware)
    sections_soup = soup.find_all('div', attrs={'class': 'chapter'})

    sections = [Section(position=i,
                        name=_get_section_name(section_soup),
                        url=_make_url(section_soup),
                        subsections=_make_subsections(section_soup))
                for i, section_soup in enumerate(sections_soup, 1)]
    return sections


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
    """
    Transform the name of a directory into an ascii version
    """
    import string
    allowed_chars = string.digits + string.ascii_letters + " _."
    result_name = ""
    for ch in initial_name:
        if allowed_chars.find(ch) != -1:
            result_name += ch
    return result_name if result_name != "" else "course_folder"


def edx_json2srt(o):
    """
    Transform the dict 'o' into the srt subtitles format
    """
    output = ''
    for i, (s, e, t) in enumerate(zip(o['start'], o['end'], o['text'])):
        if t == "":
            continue
        output += str(i) + '\n'
        s = datetime(1, 1, 1) + timedelta(seconds=s/1000.)
        e = datetime(1, 1, 1) + timedelta(seconds=e/1000.)
        output += "%02d:%02d:%02d,%03d --> %02d:%02d:%02d,%03d" % \
            (s.hour, s.minute, s.second, s.microsecond/1000,
             e.hour, e.minute, e.second, e.microsecond/1000) + '\n'
        output += t + "\n\n"
    return output


def get_page_contents_as_json(url, headers):
    """
    Makes a request to the url and immediately parses the result asuming it is
    formatted as json
    """
    json_string = get_page_contents(url, headers)
    json_object = json.loads(json_string)
    return json_object


def edx_get_subtitle(url, headers):
    """
    Return a string with the subtitles content from the url or None if no
    subtitles are available.
    """
    try:
        json_object = get_page_contents_as_json(url, headers)
        return edx_json2srt(json_object)
    except URLError as e:
        print('[warning] edX subtitles (error:%s)' % e.reason)
        return None
    except ValueError as e:
        print('[warning] edX subtitles (error:%s)' % e.message)
        return None


def edx_login(url, headers, username, password):
    post_data = urlencode({'email': username,
                           'password': password,
                           'remember': False}).encode('utf-8')
    request = Request(url, post_data, headers)
    response = urlopen(request)
    resp = json.loads(response.read().decode('utf-8'))
    return resp


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
    parser.add_argument('-l',
                        '--list',
                        dest='list',
                        action='store_true',
                        default=False,
                        help='list available courses without downloading')

    args = parser.parse_args()
    return args


def edx_get_headers():
    headers = {
        'User-Agent': 'edX-downloader/0.01',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Content-Type': 'application/x-www-form-urlencoded;charset=utf-8',
        'Referer': EDX_HOMEPAGE,
        'X-Requested-With': 'XMLHttpRequest',
        'X-CSRFToken': _get_initial_token(EDX_HOMEPAGE),
    }
    return headers


def extract_units(url, headers):
    """
    Parses a webpage and extracts its resources e.g. video_url, sub_url, etc.
    """
    print("Processing '%s'..." % url)
    page = get_page_contents(url, headers)

    re_splitter = re.compile(r'data-streams=(?:&#34;|").*1.0[0]*:')
    re_subs = re.compile(r'data-transcript-translation-url=(?:&#34;|")([^"&]*)(?:&#34;|")')
    re_available_subs = re.compile(r'data-transcript-available-translations-url=(?:&#34;|")([^"&]*)(?:&#34;|")')
    re_units = re_splitter.split(page)[1:]
    units = []
    for unit_html in re_units:
        video_id = unit_html[:YOUTUBE_VIDEO_ID_LENGTH]
        sub_urls = {}
        match_subs = re_subs.search(unit_html)
        if match_subs:
            match_available_subs = re_available_subs.search(unit_html)
            if match_available_subs:
                available_subs_url = BASE_URL + match_available_subs.group(1)
                try:
                    available_subs = get_page_contents_as_json(available_subs_url, headers)
                except HTTPError:
                    available_subs = ['en']

                for sub_prefix in available_subs:
                    sub_urls[sub_prefix] = BASE_URL + match_subs.group(1) + "/" + sub_prefix + "?videoId=" + video_id

        video_youtube_url = 'https://youtube.com/watch?v=' + video_id
        units.append(Unit(video_youtube_url=video_youtube_url,
                          sub_urls=sub_urls))

    # Try to download some extra videos which is referred by iframe
    re_extra_youtube = re.compile(r'//w{0,3}\.youtube.com/embed/([^ \?&]*)[\?& ]')
    extra_ids = re_extra_youtube.findall(page)
    for extra_id in extra_ids:
        video_youtube_url = 'https://youtube.com/watch?v=' + extra_id[:YOUTUBE_VIDEO_ID_LENGTH]
        units.append(Unit(video_youtube_url=video_youtube_url))

    return units


def extract_all_units(urls, headers):
    """
    Returns a dict of all the units in the selected_sections: {url, units}
    """
    # for development purposes you may want to uncomment this line
    # to test serial execution, and comment all the pool related ones
    # units = [extract_units(url, headers) for url in urls]
    mapfunc = partial(extract_units, headers=headers)
    pool = ThreadPool(20)
    units = pool.map(mapfunc, urls)
    pool.close()
    pool.join()

    all_units = dict(zip(urls, units))
    return all_units


def display_sections(course_name, sections):
    """
    List the weeks for the given course.
    """
    num_sections = len(sections)
    print('%s has %d sections so far' % (course_name, num_sections))
    for i, section in enumerate(sections, 1):
        print('%d - Download %s videos' % (i, section.name))
    print('%d - Download them all' % (num_sections + 1))


def get_selected_sections(sections):
    """
    Retrieve the section(s) that the user selected.
    """
    num_sections = len(sections)
    number = int(input('Enter Your Choice: '))
    while number > num_sections + 1:
        print('Enter a valid Number between 1 and %d' % (num_sections + 1))
        number = int(input('Enter Your Choice: '))

    if number == num_sections + 1:
        return sections
    return [sections[number - 1]]


def execute_command(cmd):
    """
    Creates a process with the given command cmd and writes its output.
    """
    popen = Popen(cmd, stdout=PIPE, stderr=PIPE)
    stdout = b''
    while True:  # Save output to youtube_stdout while this being echoed
        tmp = popen.stdout.read(1)
        stdout += tmp
        print(tmp, end="")
        sys.stdout.flush()
        # do it until the process finish and there isn't output
        if tmp == b"" and popen.poll() is not None:
            break


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
    headers = edx_get_headers()

    # Login
    resp = edx_login(LOGIN_API, headers, args.username, args.password)
    if not resp.get('success', False):
        print(resp.get('value', "Wrong Email or Password."))
        exit(2)

    courses = get_courses_info(DASHBOARD, headers)
    display_courses(courses)
    selected_course = get_selected_course(courses)

    # Get Available Sections
    courseware_url = selected_course.url.replace('info', 'courseware')
    sections = get_available_sections(courseware_url, headers)

    # Choose Section or choose all
    display_sections(selected_course.name, sections)
    selected_sections = get_selected_sections(sections)

    if is_interactive:
        args.subtitles = input('Download subtitles (y/n)? ').lower() == 'y'

    all_urls = [subsection.url for selected_section in selected_sections for subsection in selected_section.subsections]
    all_units = extract_all_units(all_urls, headers)

    flat_units = [unit for units in all_units.values() for unit in units]
    if len(flat_units) < 1:
        print('WARNING: No downloadable video found.')
        sys.exit(0)

    if is_interactive:
        # Get Available Video formats
        os.system('youtube-dl -F %s' % flat_units[-1].video_youtube_url)
        print('Choose a valid format or a set of valid format codes e.g. 22/17/...')
        args.format = input('Choose Format code: ')

    print("[info] Output directory: " + args.output_dir)

    # Download Videos
    # notice that we could iterate over all_units, but we prefer to do it over
    # sections/subsections to add correct prefixes and shows nicer information
    video_format_option = args.format + '/mp4' if args.format else 'mp4'
    subtitles_option = '--all-subs' if args.subtitles else ''
    counter = 0
    for i, selected_section in enumerate(selected_sections, 1):
        for j, subsection in enumerate(selected_section.subsections, 1):
            units = all_units.get(subsection.url, [])
            for unit in units:
                counter += 1
                if unit.video_youtube_url is not None:
                    coursename = directory_name(selected_course.name)
                    target_dir = os.path.join(args.output_dir, coursename)
                    filename_prefix = str(counter).zfill(2)
                    filename = filename_prefix + "-%(title)s.%(ext)s"
                    fullname = os.path.join(target_dir, filename)
                    cmd = ['youtube-dl', '-o', fullname,
                           '-f', video_format_option,
                           subtitles_option, unit.video_youtube_url]
                    execute_command(cmd)
                if args.subtitles:
                    filename = get_filename(target_dir, filename_prefix)
                    if filename is None:
                        print('[warning] no video downloaded for %s' % filename_prefix)
                        continue
                    for sub_lang, sub_url in unit.sub_urls.items():
                        subs_filename = os.path.join(target_dir, filename + '.' + sub_lang + '.srt')
                        if not os.path.exists(subs_filename):
                            subs_string = edx_get_subtitle(sub_url, headers)
                            if subs_string:
                                print('[info] Writing edX subtitle: %s' % subs_filename)
                                open(os.path.join(os.getcwd(), subs_filename),
                                     'wb+').write(subs_string.encode('utf-8'))
                        else:
                            print('[info] Skipping existing edX subtitle %s' % subs_filename)


def get_filename(target_dir, filename_prefix):
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


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nCTRL-C detected, shutting down....")
        sys.exit(0)
