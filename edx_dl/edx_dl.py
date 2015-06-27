#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Main module for the edx-dl downloader.
It corresponds to the cli interface
"""

import argparse
import json
import os
import pickle
import re
import sys

from functools import partial
from multiprocessing.dummy import Pool as ThreadPool

from six.moves.http_cookiejar import CookieJar
from six.moves.urllib.error import HTTPError, URLError
from six.moves.urllib.parse import urlencode
from six.moves.urllib.request import (
    urlopen,
    build_opener,
    install_opener,
    HTTPCookieProcessor,
    Request,
    urlretrieve,
)

from .common import YOUTUBE_DL_CMD, DEFAULT_CACHE_FILENAME, Unit, Video
from .compat import compat_print
from .parsing import (
    edx_json2srt,
    extract_courses_from_html,
    extract_sections_from_html,
    get_page_extractor,
    is_youtube_url,
)
from .utils import (
    clean_filename,
    directory_name,
    execute_command,
    get_filename_from_prefix,
    get_page_contents,
    get_page_contents_as_json,
    mkdir_p,
    remove_duplicates,
)


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
    'mitprox': {
        'url': 'https://mitprofessionalx.mit.edu',
        'courseware-selector': ('nav', {'aria-label': 'Course Navigation'}),
    },
}
BASE_URL = OPENEDX_SITES['edx']['url']
EDX_HOMEPAGE = BASE_URL + '/login_ajax'
LOGIN_API = BASE_URL + '/login_ajax'
DASHBOARD = BASE_URL + '/dashboard'
COURSEWARE_SEL = OPENEDX_SITES['edx']['courseware-selector']


def change_openedx_site(site_name):
    """
    Changes the openedx website for the given one via the key
    """
    global BASE_URL
    global EDX_HOMEPAGE
    global LOGIN_API
    global DASHBOARD
    global COURSEWARE_SEL

    if site_name not in OPENEDX_SITES.keys():
        compat_print("OpenEdX platform should be one of: %s" % ', '.join(OPENEDX_SITES.keys()))
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
    compat_print('You can access %d courses' % len(courses))

    for i, course in enumerate(courses, 1):
        compat_print('%2d - %s [%s]' % (i, course.name, course.id))
        compat_print('     %s' % course.url)


def get_courses_info(url, headers):
    """
    Extracts the courses information from the dashboard.
    """
    page = get_page_contents(url, headers)
    courses = extract_courses_from_html(page, BASE_URL)
    return courses


def _get_initial_token(url):
    """
    Create initial connection to get authentication token for future
    requests.

    Returns a string to be used in subsequent connections with the
    X-CSRFToken header or the empty string if we didn't find any token in
    the cookies.
    """
    cookiejar = CookieJar()
    opener = build_opener(HTTPCookieProcessor(cookiejar))
    install_opener(opener)
    opener.open(url)

    for cookie in cookiejar:
        if cookie.name == 'csrftoken':
            return cookie.value

    return ''


def get_available_sections(url, headers):
    """
    Extracts the sections and subsections from a given url
    """
    page = get_page_contents(url, headers)
    sections = extract_sections_from_html(page, BASE_URL)
    return sections


def edx_get_subtitle(url, headers):
    """
    Return a string with the subtitles content from the url or None if no
    subtitles are available.
    """
    try:
        json_object = get_page_contents_as_json(url, headers)
        return edx_json2srt(json_object)
    except URLError as exception:
        compat_print('[warning] edX subtitles (error:%s)' % exception.reason)
        return None
    except ValueError as exception:
        compat_print('[warning] edX subtitles (error:%s)' % exception.message)
        return None


def edx_login(url, headers, username, password):
    """
    logins user into the openedx website
    """
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
                        '(e.g., https://courses.edx.org/courses/BerkeleyX/CS191x/2013_Spring/info)')

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
    parser.add_argument('--list-courses',
                        dest='list_courses',
                        action='store_true',
                        default=False,
                        help='list available courses')
    parser.add_argument('--filter-section',
                        dest='filter_section',
                        action='store',
                        default=None,
                        help='filters sections to be downloaded')
    parser.add_argument('--list-sections',
                        dest='list_sections',
                        action='store_true',
                        default=False,
                        help='list available sections')
    parser.add_argument('--youtube-options',
                        dest='youtube_options',
                        action='store',
                        default='',
                        help='set extra options to pass to youtube-dl')
    parser.add_argument('--prefer-cdn-videos',
                        dest='prefer_cdn_videos',
                        action='store_true',
                        default=False,
                        help='prefer CDN video downloads over youtube (BETA)')
    parser.add_argument('--cache',
                        dest='cache',
                        action='store_true',
                        default=False,
                        help='create and use a cache of extracted resources')
    parser.add_argument('--dry-run',
                        dest='dry_run',
                        action='store_true',
                        default=False,
                        help='makes a dry run, only lists the resources')
    parser.add_argument('--sequence',
                        dest='sequence',
                        action='store_true',
                        default=False,
                        help='extracts the resources from the pages sequentially')

    args = parser.parse_args()

    return args


def edx_get_headers():
    """
    Builds the openedx headers to create requests
    """
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
    compat_print("Processing '%s'" % url)
    page = get_page_contents(url, headers)
    page_extractor = get_page_extractor(url)
    units = page_extractor.extract_units_from_html(page, BASE_URL)

    return units


def extract_all_units_in_sequence(urls, headers):
    """
    Returns a dict of all the units in the selected_sections: {url, units}
    sequentially, this is clearer for debug purposes
    """
    units = [extract_units(url, headers) for url in urls]
    all_units = dict(zip(urls, units))

    return all_units


def extract_all_units_in_parallel(urls, headers):
    """
    Returns a dict of all the units in the selected_sections: {url, units}
    in parallel
    """
    mapfunc = partial(extract_units, headers=headers)
    pool = ThreadPool(16)
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

    compat_print('%s [%s] has %d sections so far' % (course.name, course.id, num_sections))
    for i, section in enumerate(sections, 1):
        compat_print('%2d - Download %s videos' % (i, section.name))


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


def _display_sections(sections):
    """
    Displays a tree of section(s) and subsections
    """
    compat_print('Downloading %d section(s)' % len(sections))

    for section in sections:
        compat_print('Section %2d: %s' % (section.position, section.name))
        for subsection in section.subsections:
            compat_print('  %s' % subsection.name)


def parse_courses(args, available_courses):
    """
    Parses courses options and returns the selected_courses
    """
    if args.list_courses:
        _display_courses(available_courses)
        exit(0)

    if len(args.course_urls) == 0:
        compat_print('You must pass the URL of at least one course, check the correct url with --list-courses')
        exit(3)

    selected_courses = [available_course
                        for available_course in available_courses
                        for url in args.course_urls
                        if available_course.url == url]
    if len(selected_courses) == 0:
        compat_print('You have not passed a valid course url, check the correct url with --list-courses')
        exit(4)
    return selected_courses


def parse_sections(args, selections):
    """
    Parses sections options and returns selections filtered by
    selected_sections
    """
    if args.list_sections:
        for selected_course, selected_sections in selections.items():
            _display_sections_menu(selected_course, selected_sections)
        exit(0)

    if not args.filter_section:
        return selections

    filtered_selections = {selected_course:
                           _filter_sections(args.filter_section, selected_sections)
                           for selected_course, selected_sections in selections.items()}
    return filtered_selections


def _display_selections(selections):
    """
    Displays the course, sections and subsections to be downloaded
    """
    for selected_course, selected_sections in selections.items():
        compat_print('Downloading %s [%s]' % (selected_course.name,
                                              selected_course.id))
        _display_sections(selected_sections)


def parse_units(all_units):
    """
    Parses units options and corner cases
    """
    flat_units = [unit for units in all_units.values() for unit in units]
    if len(flat_units) < 1:
        compat_print('WARNING: No downloadable video found.')
        exit(6)


def get_subtitles_urls(available_subs_url, sub_template_url, headers):
    """
    Request the available subs and builds the urls to download subs
    """
    if available_subs_url is not None and sub_template_url is not None:
        try:
            available_subs = get_page_contents_as_json(available_subs_url,
                                                       headers)
        except HTTPError:
            available_subs = ['en']

        return {sub_lang: sub_template_url % sub_lang
                for sub_lang in available_subs}

    return {}


def _build_subtitles_downloads(video, target_dir, filename_prefix, headers):
    """
    Builds a dict {url: filename} for the subtitles, based on the
    filename_prefix of the video
    """
    downloads = {}
    filename = get_filename_from_prefix(target_dir, filename_prefix)

    if filename is None:
        compat_print('[warning] no video downloaded for %s' % filename_prefix)
        return downloads
    if video.sub_template_url is None:
        compat_print('[warning] no subtitles downloaded for %s' % filename_prefix)
        return downloads

    # This is a fix for the case of retrials because the extension would be
    # .lang (from .lang.srt), so the matching does not detect correctly the
    # subtitles name
    re_is_subtitle = re.compile(r'(.*)(?:\.[a-z]{2})')
    match_subtitle = re_is_subtitle.match(filename)
    if match_subtitle:
        filename = match_subtitle.group(1)

    subtitles_download_urls = get_subtitles_urls(video.available_subs_url,
                                                 video.sub_template_url,
                                                 headers)
    for sub_lang, sub_url in subtitles_download_urls.items():
        subs_filename = os.path.join(target_dir,
                                     filename + '.' + sub_lang + '.srt')
        downloads[sub_url] = subs_filename
    return downloads


def _build_url_downloads(urls, target_dir, filename_prefix):
    """
    Builds a dict {url: filename} for the given urls
    If it is a youtube url it uses the valid template for youtube-dl
    otherwise just takes the name of the file from the url
    """
    downloads = {url:
                 _build_filename_from_url(url, target_dir, filename_prefix)
                 for url in urls}
    return downloads


def _build_filename_from_url(url, target_dir, filename_prefix):
    """
    Builds the appropriate filename for the given args
    """
    if is_youtube_url(url):
        filename_template = filename_prefix + "-%(title)s-%(id)s.%(ext)s"
        filename = os.path.join(target_dir, filename_template)
    else:
        original_filename = url.rsplit('/', 1)[1]
        filename = os.path.join(target_dir,
                                filename_prefix + '-' + original_filename)

    return filename


def download_url(url, filename, headers, args):
    """
    Downloads the given url in filename
    """
    if is_youtube_url(url):
        download_youtube_url(url, filename, headers, args)
    else:
        try:
            urlretrieve(url, filename)
        except HTTPError as e:
            compat_print('[warning] Got HTTP error: %s' % e)


def download_youtube_url(url, filename, headers, args):
    """
    Downloads a youtube URL and applies the filters from args
    """
    video_format_option = args.format + '/mp4' if args.format else 'mp4'
    cmd = YOUTUBE_DL_CMD + ['-o', filename, '-f', video_format_option]

    if args.subtitles:
        cmd.append('--all-subs')
    cmd.extend(args.youtube_options.split())
    cmd.append(url)

    execute_command(cmd)


def download_subtitle(url, filename, headers, args):
    """
    Downloads the subtitle from the url and transforms it to the srt format
    """
    subs_string = edx_get_subtitle(url, headers)
    if subs_string:
        open(os.path.join(os.getcwd(), filename),
             'wb+').write(subs_string.encode('utf-8'))


def skip_or_download(downloads, headers, args, f=download_url):
    """
    downloads url into filename using download function f,
    if filename exists it skips
    """
    for url, filename in downloads.items():
        if os.path.exists(filename):
            compat_print('[skipping] %s => %s' % (url, filename))
            continue
        else:
            compat_print('[download] %s => %s' % (url, filename))
        if args.dry_run:
            continue
        f(url, filename, headers, args)


def download_video(video, args, target_dir, filename_prefix, headers):
    if args.prefer_cdn_videos:
        mp4_downloads = _build_url_downloads(video.mp4_urls, target_dir,
                                             filename_prefix)
        skip_or_download(mp4_downloads, headers, args)
    else:
        if video.video_youtube_url is not None:
            youtube_downloads = _build_url_downloads([video.video_youtube_url],
                                                     target_dir,
                                                     filename_prefix)
            skip_or_download(youtube_downloads, headers, args)

    # the behavior with subtitles is different, since the subtitles don't know
    # the destination name until the video is downloaded with youtube-dl
    # also, subtitles must be transformed from the raw data to the srt format
    if args.subtitles:
        sub_downloads = _build_subtitles_downloads(video, target_dir,
                                                   filename_prefix, headers)
        skip_or_download(sub_downloads, headers, args, download_subtitle)


def download_unit(unit, args, target_dir, filename_prefix, headers):
    """
    Downloads the urls in unit based on args in the given target_dir
    with filename_prefix
    """
    if len(unit.videos) == 1:
        download_video(unit.videos[0], args, target_dir, filename_prefix,
                       headers)
    else:
        # we change the filename_prefix to avoid conflicts when downloading
        # subtitles
        for i, video in enumerate(unit.videos, 1):
            new_prefix = filename_prefix + ('-%02d' % i)
            download_video(video, args, target_dir, new_prefix, headers)

    res_downloads = _build_url_downloads(unit.resources_urls, target_dir,
                                         filename_prefix)
    skip_or_download(res_downloads, headers, args)


def download(args, selections, all_units, headers):
    """
    Downloads all the resources based on the selections
    """
    compat_print("[info] Output directory: " + args.output_dir)

    # Download Videos
    # notice that we could iterate over all_units, but we prefer to do it over
    # sections/subsections to add correct prefixes and show nicer information.

    for selected_course, selected_sections in selections.items():
        coursename = directory_name(selected_course.name)
        for selected_section in selected_sections:
            section_dirname = "%02d-%s" % (selected_section.position,
                                           selected_section.name)
            target_dir = os.path.join(args.output_dir, coursename,
                                      clean_filename(section_dirname))
            mkdir_p(target_dir)
            counter = 0
            for subsection in selected_section.subsections:
                units = all_units.get(subsection.url, [])
                for unit in units:
                    counter += 1
                    filename_prefix = "%02d" % counter
                    download_unit(unit, args, target_dir, filename_prefix,
                                  headers)


def remove_repeated_urls(all_units):
    """
    Removes repeated urls from the units, it does not consider subtitles.
    This is done to avoid repeated downloads.
    """
    existing_urls = set()
    filtered_units = {}
    for url, units in all_units.items():
        reduced_units = []
        for unit in units:
            videos = []
            for video in unit.videos:
                # we don't analyze the subtitles for repetition since
                # their size is negligible for the goal of this function
                video_youtube_url = None
                if video.video_youtube_url not in existing_urls:
                    video_youtube_url = video.video_youtube_url
                    existing_urls.add(video_youtube_url)

                mp4_urls, existing_urls = remove_duplicates(video.mp4_urls, existing_urls)

                if video_youtube_url is not None or len(mp4_urls) > 0:
                    videos.append(Video(video_youtube_url=video_youtube_url,
                                        available_subs_url=video.available_subs_url,
                                        sub_template_url=video.sub_template_url,
                                        mp4_urls=mp4_urls))

            resources_urls, existing_urls = remove_duplicates(unit.resources_urls, existing_urls)

            if len(videos) > 0 or len(resources_urls) > 0:
                reduced_units.append(Unit(videos=videos,
                                          resources_urls=resources_urls))

        filtered_units[url] = reduced_units
    return filtered_units


def num_urls_in_units_dict(units_dict):
    """
    Counts the number of urls in a all_units dict, it ignores subtitles from
    its counting.
    """
    num_urls = 0

    for units in units_dict.values():
        for unit in units:
            for video in unit.videos:
                if video.video_youtube_url is not None:
                    num_urls += 1
                if video.available_subs_url is not None:
                    num_urls += 1
                if video.sub_template_url is not None:
                    num_urls += 1
                num_urls += len(video.mp4_urls)
            num_urls += len(unit.resources_urls)

    return num_urls


def extract_all_units_with_cache(all_urls, headers,
                                 filename=DEFAULT_CACHE_FILENAME,
                                 extractor=extract_all_units_in_parallel):
    """
    Extracts the units which are not in the cache and extract their resources
    returns the full list of units (cached+new)

    The cache is used to improve speed because it avoids requesting already
    known (and extracted) objects from URLs. This is useful to follow courses
    week by week since we won't parse the already known subsections/units,
    additionally it speeds development of code unrelated to extraction.
    """
    cached_units = {}

    if os.path.exists(filename):
        with open(filename, 'rb') as f:
            cached_units = pickle.load(f)

    # we filter the cached urls
    new_urls = [url for url in all_urls if url not in cached_units]
    compat_print('loading %d urls from cache [%s]' % (len(cached_units.keys()),
                                                      filename))
    new_units = extractor(new_urls, headers)
    all_units = cached_units.copy()
    all_units.update(new_units)

    return all_units


def write_units_to_cache(units, filename=DEFAULT_CACHE_FILENAME):
    """
    writes units to cache
    """
    compat_print('writing %d urls to cache [%s]' % (len(units.keys()),
                                                    filename))
    with open(filename, 'wb') as f:
        pickle.dump(units, f)


def main():
    """
    Main program function
    """
    args = parse_args()

    change_openedx_site(args.platform)

    if not args.username or not args.password:
        compat_print("You must supply username and password to log-in")
        exit(1)

    # Prepare Headers
    headers = edx_get_headers()

    # Login
    resp = edx_login(LOGIN_API, headers, args.username, args.password)
    if not resp.get('success', False):
        compat_print(resp.get('value', "Wrong Email or Password."))
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

    extractor = extract_all_units_in_parallel
    if args.sequence:
        extractor = extract_all_units_in_sequence

    if args.cache:
        all_units = extract_all_units_with_cache(all_urls, headers, extractor=extractor)
    else:
        all_units = extractor(all_urls, headers)

    parse_units(selections)

    if args.cache:
        write_units_to_cache(all_units)

    # This removes all repeated important urls
    # FIXME: This is not the best way to do it but it is the simplest, a
    # better approach will be to create symbolic or hard links for the repeated
    # units to avoid losing information
    filtered_units = remove_repeated_urls(all_units)
    num_all_urls = num_urls_in_units_dict(all_units)
    num_filtered_urls = num_urls_in_units_dict(filtered_units)
    compat_print('Removed %d duplicated urls from %d in total' %
                 ((num_all_urls - num_filtered_urls), num_all_urls))

    # finally we download all the resources
    download(args, selections, all_units, headers)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        compat_print("\n\nCTRL-C detected, shutting down....")
        sys.exit(0)
