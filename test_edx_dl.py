#!/usr/bin/env python
# -*- coding: utf-8 -*-

from edx_dl import edx_dl, parsing


def test_failed_login():
    resp = edx_dl.edx_login(
        edx_dl.LOGIN_API, edx_dl.edx_get_headers(), "guest", "guest")
    assert not resp.get('success', False)


def test_remove_repeated_urls():
    url = "test/html/multiple_units.html"
    site = 'https://courses.edx.org'
    with open(url, "r") as f:
        html_contents = f.read()
        page_extractor = parsing.NewEdXPageExtractor()
        units_extracted = page_extractor.extract_units_from_html(html_contents, site)

        all_units = {url: units_extracted}
        filtered_units = edx_dl.remove_repeated_urls(all_units)
        num_all_urls = edx_dl.num_urls_in_units_dict(all_units)
        num_filtered_urls = edx_dl.num_urls_in_units_dict(filtered_units)

        assert num_all_urls == 18
        assert num_filtered_urls == 16
        assert num_all_urls != num_filtered_urls
