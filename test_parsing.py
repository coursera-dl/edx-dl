#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import json
import logging
import sys
import unittest


from edx_dl.parsing import (
    edx_json2srt,
    extract_units_from_html,
)


class TestParsing(unittest.TestCase):

    def setUp(self):
        self.log = logging.getLogger('TestParsing')

    def test_empty_json_subtitle(self):
        with open('test/json/empty.json') as f:
            json_string = f.read()
        with self.assertRaises(ValueError):
            json_contents = json.loads(json_string)

    @unittest.skip("Should harden edx_json2srt")
    def test_minimal_json_subtitle(self):
        with open('test/json/minimal.json') as f:
            json_contents = json.loads(f.read())
        res = edx_json2srt(json_contents)
        self.assertEquals(res, '')

    def test_abridged01_json_subtitle(self):
        with open('test/json/abridged-01.json') as f:
            json_contents = json.loads(f.read())
        res = edx_json2srt(json_contents)
        expected = ('0\n'
                    '00:00:18,104 --> 00:00:20,428\n'
                    'I am very glad to see everyone here，\n\n')
        self.assertEquals(res, expected)

    def test_abridged02_json_subtitle(self):
        with open('test/json/abridged-02.json') as f:
            json_contents = json.loads(f.read())
        res = edx_json2srt(json_contents)
        expected = ('0\n'
                    '00:00:18,104 --> 00:00:20,428\n'
                    'I am very glad to see everyone here，\n\n'
                    '1\n'
                    '00:00:20,569 --> 00:00:24,721\n'
                    'so let\'s enjoy the beauty of combinatorics together.\n\n')
        self.assertEquals(res, expected)

    def test_extract_units_from_html_single_unit_multiple_subs(self):
        with open("test/html/single_unit_multiple_subs.html", "r") as f:
            units = extract_units_from_html(f.read(), 'https://courses.edx.org')
            video_youtube_url, available_subs_url, sub_template_url, mp4_urls, pdf_urls = units[0]
            self.assertEquals(video_youtube_url, 'https://youtube.com/watch?v=b7xgknqkQk8')
            self.assertEquals(mp4_urls[0], 'https://d2f1egay8yehza.cloudfront.net/edx-edx101/EDXSPCPJSP13-H010000_100.mp4')
            self.assertEquals(sub_template_url, 'https://courses.edx.org/courses/edX/DemoX.1/2014/xblock/i4x:;_;_edX;_DemoX.1;_video;_14459340170c476bb65f73a0a08a076f/handler/transcript/translation/%s')
            # self.log.info(units)

    def test_extract_multiple_units_multiple_resources(self):
        with open("test/html/multiple_units.html", "r") as f:
            units = extract_units_from_html(f.read(), 'https://courses.edx.org')
            self.assertEquals(len(units), 3)
            # this one has multiple speeds in the data-streams field
            self.assertTrue('https://youtube.com/watch?v=CJ482b9r_0g' in [unit[0] for unit in units])
            mp4_urls = units[0][3]
            self.assertTrue(mp4_urls > 0)
            self.assertTrue('https://s3.amazonaws.com/berkeley-cs184x/videos/overview-motivation.mp4' in mp4_urls)
            pdf_urls = units[0][4]
            self.assertEquals(pdf_urls[0], 'https://courses.edx.org/static/content-berkeley-cs184x~2012_Fall/slides/overview.pdf')

    def test_extract_multiple_units_no_youtube_ids(self):
        with open("test/html/multiple_units_no_youtube_ids.html", "r") as f:
            units = extract_units_from_html(f.read(), 'https://courses.edx.org')
            video_youtube_url, available_subs_url, sub_template_url, mp4_urls, pdf_urls = units[0]
            self.assertEquals(video_youtube_url, None)
            self.assertTrue(len(mp4_urls) > 0)



if __name__ == '__main__':
    logging.basicConfig(stream=sys.stdout)
    logging.getLogger("TestParsing").setLevel(logging.DEBUG)
    suite = unittest.TestLoader().loadTestsFromTestCase(TestParsing)
    unittest.TextTestRunner(verbosity=2).run(suite)
