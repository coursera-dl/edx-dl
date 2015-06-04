#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import sys
import unittest

from edx_dl import edx_dl


class TestEdX(unittest.TestCase):

    def setUp(self):
        self.log = logging.getLogger("TestEdX")

    def test_failed_login(self):
        resp = edx_dl.edx_login(
            edx_dl.LOGIN_API, edx_dl.edx_get_headers(), "guest", "guest")
        self.assertFalse(resp.get('success', False))

    def test_extract_units_from_html_single_unit_multiple_subs(self):
        with open("test/html/single_unit_multiple_subs.html", "r") as myfile:
            page = myfile.read()
            units = edx_dl.extract_units_from_html(page)
            self.assertEquals(units[0].video_youtube_url, 'https://youtube.com/watch?v=b7xgknqkQk8')
            self.assertEquals(units[0].mp4_urls[0], 'https://d2f1egay8yehza.cloudfront.net/edx-edx101/EDXSPCPJSP13-H010000_100.mp4')
            self.assertEquals(units[0].sub_template_url, 'https://courses.edx.org/courses/edX/DemoX.1/2014/xblock/i4x:;_;_edX;_DemoX.1;_video;_14459340170c476bb65f73a0a08a076f/handler/transcript/translation/%s')
            # self.log.info(units)

    def test_extract_multiple_units_multiple_resources(self):
        with open("test/html/multiple_units.html", "r") as myfile:
            page = myfile.read()
            units = edx_dl.extract_units_from_html(page)
            self.assertEquals(len(units), 3)
            self.assertTrue('https://youtube.com/watch?v=CJ482b9r_0g' in [unit.video_youtube_url for unit in units])
            self.assertTrue(len(units[0].mp4_urls) > 0)
            self.assertTrue('https://s3.amazonaws.com/berkeley-cs184x/videos/overview-motivation.mp4' in units[0].mp4_urls)
            self.assertEquals(units[0].pdf_urls[0], 'https://courses.edx.org/static/content-berkeley-cs184x~2012_Fall/slides/overview.pdf')


if __name__ == '__main__':
    logging.basicConfig(stream=sys.stdout)
    logging.getLogger("TestEdX").setLevel(logging.DEBUG)
    suite = unittest.TestLoader().loadTestsFromTestCase(TestEdX)
    unittest.TextTestRunner(verbosity=2).run(suite)
