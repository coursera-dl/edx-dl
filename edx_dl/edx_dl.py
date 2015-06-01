#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import json
import os
import re
import sys

from collections import namedtuple
from datetime import timedelta, datetime
from functools import partial
from multiprocessing.dummy import Pool as ThreadPool

from bs4 import BeautifulSoup as BeautifulSoup_

from .compat import *
from .compat import _print
from .utils import *

# Force use of bs4 with html5lib
BeautifulSoup = lambda page: BeautifulSoup_(page, 'html5lib')

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

#
# The next four named tuples represent the structure of courses in edX.  The
# structure is:
#
# * A Course contains Sections
# * Each Section contains Subsections
# * Each Subsection contains Units
#
# Notice that we don't represent the full tree structure for both performance
# and UX reasons:
#
# Course ->  [Section] -> [SubSection] -> [Unit]
#
# In the script the data structures used are:
#
# 1. The data structures to represent the course information:
#    Course, Section->[SubSection]
#
# 2. The data structures to represent the chosen courses and sections:
#    selections = {Course, [Section]}
#
# 3. The data structure of all the downloable resources which represent each
#    subsection via its URL and the of resources who can be extracted from the
#    Units it contains:
#    all_units = {Subsection.url: [Unit]}
#
Course = namedtuple('Course', ['id', 'name', 'url', 'state'])
Section = namedtuple('Section', ['position', 'name', 'url', 'subsections'])
SubSection = namedtuple('SubSection', ['position', 'name', 'url'])
Unit = namedtuple('Unit', ['video_youtube_url', 'available_subs_url', 'sub_template_url'])


def change_openedx_site(site_name):
    global BASE_URL
    global EDX_HOMEPAGE
    global LOGIN_API
    global DASHBOARD
    global COURSEWARE_SEL

    if site_name not in OPENEDX_SITES.keys():
        _print("OpenEdX platform should be one of: %s" % ', '.join(OPENEDX_SITES.keys()))
        sys.exit(2)

    BASE_URL = OPENEDX_SITES[site_name]['url']
    EDX_HOMEPAGE = BASE_URL + '/login_ajax'
    LOGIN_API = BASE_URL + '/login_ajax'
    DASHBOARD = BASE_URL + '/dashboard'
    COURSEWARE_SEL = OPENEDX_SITES[site_name]['courseware-selector']


def _display_courses(courses):
    """
    List the courses that the user has enrolled.
    """
    _print('You can access %d courses' % len(courses))
    for i, course in enumerate(courses, 1):
        _print('%2d - %s [%s]' % (i, course.name, course.id))
        _print('     %s' % course.url)


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


def edx_json2srt(o):
    """
    Transform the dict 'o' into the srt subtitles format
    """
    BASE_TIME = datetime(1, 1, 1)
    output = []

    for i, (s, e, t) in enumerate(zip(o['start'], o['end'], o['text'])):
        if t == '':
            continue

        output.append(str(i) + '\n')

        s = BASE_TIME + timedelta(seconds=s/1000.)
        e = BASE_TIME + timedelta(seconds=e/1000.)
        time_range = "%02d:%02d:%02d,%03d --> %02d:%02d:%02d,%03d\n" % \
                     (s.hour, s.minute, s.second, s.microsecond/1000,
                      e.hour, e.minute, e.second, e.microsecond/1000)

        output.append(time_range)
        output.append(t + "\n\n")

    return ''.join(output)


def edx_get_subtitle(url, headers):
    """
    Return a string with the subtitles content from the url or None if no
    subtitles are available.
    """
    try:
        json_object = get_page_contents_as_json(url, headers)
        return edx_json2srt(json_object)
    except URLError as e:
        _print('[warning] edX subtitles (error:%s)' % e.reason)
        return None
    except ValueError as e:
        _print('[warning] edX subtitles (error:%s)' % e.message)
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
    parser.add_argument('course_urls',
                        nargs='*',
                        action='store',
                        default=[],
                        help='target course urls'
                        '(e.g., https://courses.edx.org/courses/BerkeleyX/CS191x/2013_Spring/info)'
                        )

    # optional
    parser.add_argument('-u',
                        '--username',
                        required=True,
                        action='store',
                        help='your edX username (email)')
    parser.add_argument('-p',
                        '--password',
                        required=True,
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
    parser.add_argument('-cl',
                        '--course-list',
                        dest='course_list',
                        action='store_true',
                        default=False,
                        help='list available courses')
    parser.add_argument('-sf',
                        '--section-filter',
                        dest='section_filter',
                        action='store',
                        default=None,
                        help='filters sections to be downloaded')
    parser.add_argument('-sl',
                        '--section-list',
                        dest='section_list',
                        action='store_true',
                        default=False,
                        help='list available sections')
    parser.add_argument('-yo',
                        '--youtube-options',
                        dest='youtube_options',
                        action='store',
                        default='',
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
    _print("Processing '%s'..." % url)
    page = get_page_contents(url, headers)

    re_splitter = re.compile(r'data-streams=(?:&#34;|").*1.0[0]*:')
    re_subs = re.compile(r'data-transcript-translation-url=(?:&#34;|")([^"&]*)(?:&#34;|")')
    re_available_subs = re.compile(r'data-transcript-available-translations-url=(?:&#34;|")([^"&]*)(?:&#34;|")')
    re_units = re_splitter.split(page)[1:]
    units = []
    for unit_html in re_units:
        video_id = unit_html[:YOUTUBE_VIDEO_ID_LENGTH]
        video_youtube_url = 'https://youtube.com/watch?v=' + video_id

        match_subs = re_subs.search(unit_html)
        if match_subs:
            match_available_subs = re_available_subs.search(unit_html)
            if match_available_subs:
                available_subs_url = BASE_URL + match_available_subs.group(1)
                sub_template_url = BASE_URL + match_subs.group(1) + "/%s?videoId=" + video_id

        units.append(Unit(video_youtube_url=video_youtube_url,
                          available_subs_url=available_subs_url,
                          sub_template_url=sub_template_url))

    # Try to download some extra videos which is referred by iframe
    re_extra_youtube = re.compile(r'//w{0,3}\.youtube.com/embed/([^ \?&]*)[\?& ]')
    extra_ids = re_extra_youtube.findall(page)
    for extra_id in extra_ids:
        video_youtube_url = 'https://youtube.com/watch?v=' + extra_id[:YOUTUBE_VIDEO_ID_LENGTH]
        units.append(Unit(video_youtube_url=video_youtube_url,
                          available_subs_url=None,
                          sub_template_url=None))  # FIXME: verify subtitles

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


def _display_sections_menu(course, sections):
    """
    List the weeks for the given course.
    """
    num_sections = len(sections)
    _print('%s [%s] has %d sections so far' % (course.name, course.id, num_sections))
    for i, section in enumerate(sections, 1):
        _print('%2d - Download %s videos' % (i, section.name))


def _filter_sections(index, sections):
    """
    Get the sections for the given index, if the index is not valid chooses all
    """
    num_sections = len(sections)
    if index is not None:
        try:
            index = int(index)
            if index > 0 and index <= num_sections:
                return [sections[index - 1]]
        except ValueError:
            pass
    return sections


def _display_sections_and_subsections(sections):
    """
    Displays a tree of section(s) and subsections
    """
    _print('Downloading %d section(s)' % len(sections))
    for section in sections:
        _print('Section %2d: %s' % (section.position, section.name))
        for subsection in section.subsections:
            _print('  %s' % subsection.name)


def parse_courses(args, available_courses):
    """
    Parses courses options and returns the selected_courses
    """
    if args.course_list:
        _display_courses(available_courses)
        exit(0)

    if len(args.course_urls) == 0:
        _print('You must pass the URL of at least one course, check the correct url with --course-list')
        exit(3)

    selected_courses = [available_course
                        for available_course in available_courses
                        for url in args.course_urls
                        if available_course.url == url]
    if len(selected_courses) == 0:
        _print('You have not passed a valid course url, check the correct url with --course-list')
        exit(4)
    return selected_courses


def parse_sections(args, selections):
    """
    Parses sections options and returns selections filtered by
    selected_sections
    """
    if args.section_list:
        for selected_course, selected_sections in selections.items():
            _display_sections_menu(selected_course, selected_sections)
        exit(0)

    if not args.section_filter:
        return selections

    filtered_selections = {selected_course:
                           _filter_sections(args.section_filter, selected_sections)
                           for selected_course, selected_sections in selections.items()}
    return filtered_selections


def _display_selections(selections):
    """
    Displays the course, sections and subsections to be downloaded
    """
    for selected_course, selected_sections in selections.items():
        _print('Downloading %s [%s]' % (selected_course.name,
                                        selected_course.id))
        _display_sections_and_subsections(selected_sections)


def parse_units(all_units):
    """
    Parses units options and corner cases
    """
    flat_units = [unit for units in all_units.values() for unit in units]
    if len(flat_units) < 1:
        _print('WARNING: No downloadable video found.')
        exit(6)


def download(args, selections, all_units, headers):
    BASE_EXTERNAL_CMD = ['youtube-dl', '--ignore-config']
    _print("[info] Output directory: " + args.output_dir)

    # Download Videos
    # notice that we could iterate over all_units, but we prefer to do it over
    # sections/subsections to add correct prefixes and shows nicer information
    video_format_option = args.format + '/mp4' if args.format else 'mp4'
    for selected_course, selected_sections in selections.items():
        coursename = directory_name(selected_course.name)
        for selected_section in selected_sections:
            section_dirname = "%02d-%s" % (selected_section.position, selected_section.name)
            target_dir = os.path.join(args.output_dir, coursename, section_dirname)
            counter = 0
            for subsection in selected_section.subsections:
                units = all_units.get(subsection.url, [])
                for unit in units:
                    counter += 1
                    filename_prefix = "%02d" % counter
                    if unit.video_youtube_url is not None:
                        filename = filename_prefix + "-%(title)s-%(id)s.%(ext)s"
                        fullname = os.path.join(target_dir, filename)

                        cmd = BASE_EXTERNAL_CMD + ['-o', fullname, '-f',
                                                   video_format_option]
                        if args.subtitles:
                            cmd.append('--all-subs')
                        cmd.extend(args.youtube_options.split())
                        cmd.append(unit.video_youtube_url)
                        execute_command(cmd)

                    if args.subtitles:
                        filename = get_filename_from_prefix(target_dir, filename_prefix)
                        if filename is None:
                            _print('[warning] no video downloaded for %s' % filename_prefix)
                            continue
                        if unit.sub_template_url is None:
                            _print('[warning] no subtitles downloaded for %s' % filename_prefix)
                            continue

                        try:
                            available_subs = get_page_contents_as_json(unit.available_subs_url, headers)
                        except HTTPError:
                            available_subs = ['en']

                        for sub_lang in available_subs:
                            sub_url = unit.sub_template_url % sub_lang
                            subs_filename = os.path.join(target_dir, filename + '.' + sub_lang + '.srt')
                            if not os.path.exists(subs_filename):
                                subs_string = edx_get_subtitle(sub_url, headers)
                                if subs_string:
                                    _print('[info] Writing edX subtitle: %s' % subs_filename)
                                    open(os.path.join(os.getcwd(), subs_filename),
                                         'wb+').write(subs_string.encode('utf-8'))
                            else:
                                _print('[info] Skipping existing edX subtitle %s' % subs_filename)


def main():
    args = parse_args()

    change_openedx_site(args.platform)

    if not args.username or not args.password:
        _print("You must supply username and password to log-in")
        exit(1)

    # Prepare Headers
    headers = edx_get_headers()

    # Login
    resp = edx_login(LOGIN_API, headers, args.username, args.password)
    if not resp.get('success', False):
        _print(resp.get('value', "Wrong Email or Password."))
        exit(2)

    # Parse and select the available courses
    courses = get_courses_info(DASHBOARD, headers)
    available_courses = [course for course in courses if course.state == 'Started']
    selected_courses = parse_courses(args, available_courses)

    # Parse the sections and build the selections dict filtered by sections
    all_selections = {selected_course:
                      get_available_sections(selected_course.url.replace('info', 'courseware'), headers)
                      for selected_course in selected_courses}
    selections = parse_sections(args, all_selections)
    _display_selections(selections)

    # Extract the unit information (downloadable resources)
    # This parses the HTML of all the subsection.url and extracts
    # the URLs of the resources as Units.
    all_urls = [subsection.url
                for selected_sections in selections.values()
                for selected_section in selected_sections
                for subsection in selected_section.subsections]
    all_units = extract_all_units(all_urls, headers)
    parse_units(selections)

    # finally we download all the resources
    download(args, selections, all_units, headers)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        _print("\n\nCTRL-C detected, shutting down....")
        sys.exit(0)
