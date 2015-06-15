#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import json

import pytest

from edx_dl.parsing import (
    edx_json2srt,
    ClassicEdXPageExtractor,
    NewEdXPageExtractor,
    extract_sections_from_html,
    extract_courses_from_html,
)


# Test conversion of JSON subtitles to srt
def test_empty_json_subtitle():
    with open('test/json/empty.json') as f:
        json_string = f.read()
    with pytest.raises(ValueError):
        json_contents = json.loads(json_string)


def test_minimal_json_subtitle():
    with open('test/json/minimal.json') as f:
        json_contents = json.loads(f.read())
    res = edx_json2srt(json_contents)
    assert res == ''


def test_abridged01_json_subtitle():
    with open('test/json/abridged-01.json') as f:
        json_contents = json.loads(f.read())
    res = edx_json2srt(json_contents)
    expected = ('0\n'
                '00:00:18,104 --> 00:00:20,428\n'
                'I am very glad to see everyone here，\n\n')
    assert res == expected


def test_abridged02_json_subtitle():
    with open('test/json/abridged-02.json') as f:
        json_contents = json.loads(f.read())
    res = edx_json2srt(json_contents)
    expected = ('0\n'
                '00:00:18,104 --> 00:00:20,428\n'
                'I am very glad to see everyone here，\n\n'
                '1\n'
                '00:00:20,569 --> 00:00:24,721\n'
                'so let\'s enjoy the beauty of combinatorics together.\n\n')
    assert res == expected


def test_empty_text_subtitle():
    with open('test/json/empty-text.json') as f:
        json_contents = json.loads(f.read())
    res = edx_json2srt(json_contents)
    expected = ''
    assert res == expected


# Test extraction of video/other assets from HTML
def test_extract_units_from_html_single_unit_multiple_subs():
    site = 'https://courses.edx.org'
    with open("test/html/single_unit_multiple_subs.html", "r") as f:
        units = NewEdXPageExtractor().extract_units_from_html(f.read(), site)

        assert units[0].video_youtube_url == 'https://youtube.com/watch?v=b7xgknqkQk8'
        assert units[0].mp4_urls[0] == 'https://d2f1egay8yehza.cloudfront.net/edx-edx101/EDXSPCPJSP13-H010000_100.mp4'
        assert units[0].sub_template_url == 'https://courses.edx.org/courses/edX/DemoX.1/2014/xblock/i4x:;_;_edX;_DemoX.1;_video;_14459340170c476bb65f73a0a08a076f/handler/transcript/translation/%s'


def test_extract_multiple_units_multiple_resources():
    site = 'https://courses.edx.org'
    with open("test/html/multiple_units.html", "r") as f:
        units = NewEdXPageExtractor().extract_units_from_html(f.read(), site)
        assert len(units) == 3
        # this one has multiple speeds in the data-streams field
        assert 'https://youtube.com/watch?v=CJ482b9r_0g' in [unit[0] for unit in units]
        assert len(units[0].mp4_urls) > 0
        assert 'https://s3.amazonaws.com/berkeley-cs184x/videos/overview-motivation.mp4' in units[0].mp4_urls
        assert units[0].resources_urls[0] == 'https://courses.edx.org/static/content-berkeley-cs184x~2012_Fall/slides/overview.pdf'


def test_extract_multiple_units_no_youtube_ids():
    site = 'https://courses.edx.org'
    with open("test/html/multiple_units_no_youtube_ids.html", "r") as f:
        units = ClassicEdXPageExtractor().extract_units_from_html(f.read(), site)
        video_youtube_url, available_subs_url, sub_template_url, mp4_urls, resources_urls = units[0]
        assert video_youtube_url is None
        assert len(mp4_urls) > 0


def test_extract_sections():
    site = 'https://courses.edx.org'
    with open("test/html/single_unit_multiple_subs.html", "r") as f:
        sections = extract_sections_from_html(f.read(), site)
        assert len(sections) == 6
        num_subsections = sum(len(section.subsections) for section in sections)
        assert num_subsections == 11


def test_extract_courses_from_html():
    site = 'https://courses.edx.org'
    with open("test/html/dashboard.html", "r") as f:
        courses = extract_courses_from_html(f.read(), site)
        assert len(courses) == 18
        available_courses = [course for course in courses if course.state == 'Started']
        assert len(available_courses) == 14
