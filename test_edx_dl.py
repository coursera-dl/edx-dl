#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pytest
from edx_dl import edx_dl, parsing
from edx_dl.common import Unit, Video


def test_failed_login():
    resp = edx_dl.edx_login(
        edx_dl.LOGIN_API, edx_dl.edx_get_headers(), "guest", "guest")
    assert not resp.get('success', False)


def test_remove_repeated_urls():
    url = "test/html/multiple_units.html"
    site = 'https://courses.edx.org'
    with open(url, "r") as f:
        html_contents = f.read()
        page_extractor = parsing.CurrentEdXPageExtractor()
        units_extracted = page_extractor.extract_units_from_html(html_contents, site)

        all_units = {url: units_extracted}
        filtered_units = edx_dl.remove_repeated_urls(all_units)
        num_all_urls = edx_dl.num_urls_in_units_dict(all_units)
        num_filtered_urls = edx_dl.num_urls_in_units_dict(filtered_units)

        assert num_all_urls == 18
        assert num_filtered_urls == 16
        assert num_all_urls != num_filtered_urls


@pytest.fixture
def all_units():
    return {
        'empty_section': [],
        'nonempty_section': [Unit(videos=[], resources_urls=[]),
                             Unit(videos=[Video(video_youtube_url=None,
                                                available_subs_url=None,
                                                sub_template_url=None,
                                                mp4_urls=[])], resources_urls=[]),
                             Unit(videos=[Video(video_youtube_url=None,
                                                available_subs_url=None,
                                                sub_template_url=None,
                                                mp4_urls=['1', '2'])], resources_urls=['3']),
                             ]
    }


@pytest.fixture
def unknown_units():
    return {
        'nonempty_section': ['shouldfail']
    }


@pytest.fixture
def unknown_videos():
    return {
        'nonempty_section': [Unit(videos=['shoudfail'], resources_urls=['3'])]
    }


def test_extract_urls_from_units(all_units):
    """
    Make sure that urls are grabbed from both mp4_urls and from
    resources_urls of Unit class.
    """
    urls = edx_dl.extract_urls_from_units(all_units, '%(url)s')
    expected = ['1\n', '2\n', '3\n']
    assert sorted(urls) == sorted(expected)


def test_extract_urls_from_units_unknown_units(unknown_units):
    """
    Make sure that we only expect Units in the list of units.
    """
    with pytest.raises(TypeError):
        edx_dl.extract_urls_from_units(unknown_units, '%(url)s')


def test_extract_urls_from_units_unknown_videos(unknown_videos):
    """
    Make sure that we only expect Video in the list of Unit videos.
    """
    with pytest.raises(TypeError):
        edx_dl.extract_urls_from_units(unknown_videos, '%(url)s')


def test_edx_get_subtitle():
    """
    Make sure Stanford subtitle URLs are distinguished from EdX ones.
    """

    def mock_get_page_contents(u, h):
        assert u == url
        assert h == headers
        return u
    
    def mock_get_page_contents_as_json(u, h):
        assert u == url
        assert h == headers
        return { 'start' : [123], 'end' : [456], 'text' : ["subtitle content"] }

    url = "https://lagunita.stanford.edu/courses/Engineering/QMSE02./Winter2016/xblock/i4x:;_;_Engineering;_QMSE02.;_video;_7f4f16e3eb294538aa8db4c43877132b/handler/transcript/download"
    headers = {}
    get_page_contents = lambda u, h: u
    
    expected = url
    actual = edx_dl.edx_get_subtitle(url, headers, mock_get_page_contents, mock_get_page_contents_as_json)
    assert expected == actual

    # Make sure Non-Stanford URLs still work
    url = "https://www.edx.org/could/be/more/realistic"

    expected = '0\n00:00:00,123 --> 00:00:00,456\nsubtitle content\n\n'
    actual = edx_dl.edx_get_subtitle(url, headers, mock_get_page_contents, mock_get_page_contents_as_json)
    assert expected == actual


def test_extract_subtitle_urls():
    text = """
&lt;li class="video-tracks video-download-button"&gt;
            &lt;a href="/courses/Engineering/QMSE02./Winter2016/xblock/i4x:;_;_Engineering;_QMSE02.;_video;_1a4c7ff41e484a15927987b745a5c779/handler/transcript/download"&gt;Download transcript&lt;/a&gt;
            &lt;div class="a11y-menu-container"&gt;
                &lt;a class="a11y-menu-button" href="#" title=".srt" role="button" aria-disabled="false"&gt;.srt&lt;/a&gt;
                &lt;ol class="a11y-menu-list" role="menu"&gt;
                  &lt;li class="a11y-menu-item active"&gt;
                  
                      &lt;a class="a11y-menu-item-link" href="#srt" title="SubRip (.srt) file" data-value="srt" role="menuitem" aria-disabled="false"&gt;
                        SubRip (.srt) file
                      &lt;/a&gt;
                  &lt;/li&gt;
                  &lt;li class="a11y-menu-item"&gt;
                  
                      &lt;a class="a11y-menu-item-link" href="#txt" title="Text (.txt) file" data-value="txt" role="menuitem" aria-disabled="false"&gt;
                        Text (.txt) file
                      &lt;/a&gt;
                  &lt;/li&gt;
                &lt;/ol&gt;
            &lt;/div&gt;
        &lt;/li&gt;
    """

    page_extractor = parsing.CurrentEdXPageExtractor()
    expected = (None, 'https://base.url/courses/Engineering/QMSE02./Winter2016/xblock/i4x:;_;_Engineering;_QMSE02.;_video;_1a4c7ff41e484a15927987b745a5c779/handler/transcript/download')
    actual = page_extractor.extract_subtitle_urls(text, "https://base.url")
    print("actual", actual)
    assert expected == actual

