# -*- coding: utf-8 -*-

import re

from datetime import timedelta, datetime


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


def extract_units_from_html(page, BASE_URL):
    """
    Extract Units from the html of a subsection webpage as a list of resources
    """
    # in this function we avoid using beautifulsoup for performance reasons

    # parsing html with regular expressions is really nasty, don't do this if
    # you don't need to !
    re_units = re.compile('(<div?[^>]id="seq_contents_\d+".*?>.*?<\/div>)', re.DOTALL)
    re_video_youtube_url = re.compile(r'data-streams=&#34;.*?1.0\d+\:(?:.*?)(.{11})')
    re_sub_template_url = re.compile(r'data-transcript-translation-url=(?:&#34;|")([^"&]*)(?:&#34;|")')
    re_available_subs_url = re.compile(r'data-transcript-available-translations-url=(?:&#34;|")([^"&]*)(?:&#34;|")')

    # mp4 urls may be in two places, in the field data-sources, and as <a> refs
    # This regex tries to match all the appearances, however we exclude the ';'
    # character in the urls, since it is used to separate multiple urls in one
    # string, however ';' is a valid url name character, but it is not really
    # common.
    re_mp4_urls = re.compile(r'(?:(https?://[^;]*?\.mp4))')
    re_resources_urls = re.compile(r'href=(?:&#34;|")([^"&]*pdf)')

    units = []
    for unit_html in re_units.findall(page):
        video_youtube_url = None
        match_video_youtube_url = re_video_youtube_url.search(unit_html)
        if match_video_youtube_url is not None:
            video_id = match_video_youtube_url.group(1)
            video_youtube_url = 'https://youtube.com/watch?v=' + video_id

        available_subs_url = None
        sub_template_url = None
        match_subs = re_sub_template_url.search(unit_html)
        if match_subs:
            match_available_subs = re_available_subs_url.search(unit_html)
            if match_available_subs:
                available_subs_url = BASE_URL + match_available_subs.group(1)
                sub_template_url = BASE_URL + match_subs.group(1) + "/%s"

        mp4_urls = list(set(re_mp4_urls.findall(unit_html)))
        resources_urls = [url
                          if url.startswith('http') or url.startswith('https')
                          else BASE_URL + url
                          for url in re_resources_urls.findall(unit_html)]

        if video_youtube_url is not None or len(mp4_urls) > 0 or len(resources_urls) > 0:
            units.append((video_youtube_url, available_subs_url,
                          sub_template_url, mp4_urls, resources_urls))

    return units
