#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import json

import pytest

from edx_dl.parsing import (
    edx_json2srt,
    ClassicEdXPageExtractor,
    CurrentEdXPageExtractor,
    is_youtube_url,
)


# Test conversion of JSON subtitles to srt
def test_empty_json_subtitle():
    with open('test/json/empty.json') as f:
        json_string = f.read()
    with pytest.raises(ValueError):
        json_contents = json.loads(json_string)


@pytest.mark.parametrize(
    'file,expected', [
        ('test/json/empty-text.json', ''),
        ('test/json/minimal.json', ''),
        ('test/json/abridged-01.json', ('0\n'
                                        '00:00:18,104 --> 00:00:20,428\n'
                                        'I am very glad to see everyone here，\n\n')),
        ('test/json/abridged-02.json', ('0\n'
                                        '00:00:18,104 --> 00:00:20,428\n'
                                        'I am very glad to see everyone here，\n\n'
                                        '1\n'
                                        '00:00:20,569 --> 00:00:24,721\n'
                                        'so let\'s enjoy the beauty of combinatorics together.\n\n'))
    ]
)
def test_subtitles_from_json(file, expected):
    with open(file) as f:
        json_contents = json.loads(f.read())
    res = edx_json2srt(json_contents)
    assert res == expected


# Test extraction of video/other assets from HTML
def test_extract_units_from_html_single_unit_multiple_subs():
    site = 'https://courses.edx.org'
    with open("test/html/single_unit_multiple_subs.html", "r") as f:
        units = CurrentEdXPageExtractor().extract_units_from_html(f.read(), site)

        assert units[0].videos[0].video_youtube_url == 'https://youtube.com/watch?v=b7xgknqkQk8'
        assert units[0].videos[0].mp4_urls[0] == 'https://d2f1egay8yehza.cloudfront.net/edx-edx101/EDXSPCPJSP13-H010000_100.mp4'
        assert units[0].videos[0].sub_template_url == 'https://courses.edx.org/courses/edX/DemoX.1/2014/xblock/i4x:;_;_edX;_DemoX.1;_video;_14459340170c476bb65f73a0a08a076f/handler/transcript/translation/%s'


def test_extract_multiple_units_multiple_resources():
    site = 'https://courses.edx.org'
    with open("test/html/multiple_units.html", "r") as f:
        units = CurrentEdXPageExtractor().extract_units_from_html(f.read(), site)
        assert len(units) == 3
        # this one has multiple speeds in the data-streams field
        assert 'https://youtube.com/watch?v=CJ482b9r_0g' in [video.video_youtube_url for video in units[0].videos]
        assert len(units[0].videos[0].mp4_urls) > 0
        assert 'https://s3.amazonaws.com/berkeley-cs184x/videos/overview-motivation.mp4' in units[0].videos[0].mp4_urls
        assert 'https://courses.edx.org/static/content-berkeley-cs184x~2012_Fall/slides/overview.pdf' in units[0].resources_urls


def test_extract_multiple_units_no_youtube_ids():
    site = 'https://courses.edx.org'
    with open("test/html/multiple_units_no_youtube_ids.html", "r") as f:
        units = ClassicEdXPageExtractor().extract_units_from_html(f.read(), site)
        assert units[0].videos[0].video_youtube_url is None
        assert len(units[0].videos[0].mp4_urls) > 0


def test_extract_multiple_units_youtube_link():
    site = 'https://courses.edx.org'
    with open("test/html/multiple_units_youtube_link.html", "r") as f:
        units = CurrentEdXPageExtractor().extract_units_from_html(f.read(), site)
        assert 'https://www.youtube.com/watch?v=5OXQypOAbdI' in units[0].resources_urls


def test_extract_multiple_units_multiple_youtube_videos():
    site = 'https://courses.edx.org'
    with open("test/html/multiple_units_multiple_youtube_videos.html", "r") as f:
        units = CurrentEdXPageExtractor().extract_units_from_html(f.read(), site)
        assert len(units[0].videos) == 3
        assert 'https://youtube.com/watch?v=3atHHNa2UwI' in [video.video_youtube_url for video in units[0].videos]


@pytest.mark.parametrize(
    'file,num_sections_expected,num_subsections_expected', [
        ('test/html/new_sections_structure.html', 2, 12),
        ('test/html/empty_sections.html', 0, 0)
    ]
)
def test_extract_sections(file, num_sections_expected, num_subsections_expected):
    site = 'https://courses.edx.org'
    with open(file, "r") as f:
        sections = CurrentEdXPageExtractor().extract_sections_from_html(f.read(), site)
        assert len(sections) == num_sections_expected
        num_subsections = sum(len(section.subsections) for section in sections)
        assert num_subsections == num_subsections_expected


def test_extract_courses_from_html():
    site = 'https://courses.edx.org'
    with open("test/html/dashboard.html", "r") as f:
        courses = CurrentEdXPageExtractor().extract_courses_from_html(f.read(), site)
        assert len(courses) == 18
        available_courses = [course for course in courses if course.state == 'Started']
        assert len(available_courses) == 14


def test_is_youtube_url():
    invalid_urls = [
        'http://www.google.com/', 'TODO',
        'https://d2f1egay8yehza.cloudfront.net/mit-24118/MIT24118T314-V015000_DTH.mp4',
        'https://courses.edx.org/courses/course-v1:MITx+24.118x+2T2015/xblock/block-v1:MITx+24.118x+2T2015+type@video+block@b1588e7cccff4d448f4f9676c81184d9/handler/transcript/available_translations'
    ]
    valid_urls = [
        'http://www.youtu.be/rjOpZ3i6pRo',
        'http://www.youtube.com/watch?v=rjOpZ3i6pRo',
        'http://youtu.be/rjOpZ3i6pRo',
        'http://youtube.com/watch?v=rjOpZ3i6pRo',
        'https://www.youtu.be/rjOpZ3i6pRo',
        'https://www.youtube.com/watch?v=rjOpZ3i6pRo',
        'https://youtu.be/rjOpZ3i6pRo',
        'https://youtube.com/watch?v=rjOpZ3i6pRo',
    ]
    for url in invalid_urls:
        assert not is_youtube_url(url)
    for url in valid_urls:
        assert is_youtube_url(url)
