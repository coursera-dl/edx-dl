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

    def test_extract_units_from_html_single_unit(self):
        with open("test/html/courses.edx.org/courses/edX/DemoX.1/2014/courseware/6156e0e685ee4a2ab017258108c0bccd/194bd1729fab47aba6507f737d9b90ba", "r") as myfile:
            page = myfile.read()
            units = edx_dl.extract_units_from_html(page)
            self.assertEquals(units[0].video_youtube_url, 'https://youtube.com/watch?v=b7xgknqkQk8')
            self.assertEquals(units[0].mp4_urls[0], 'https://d2f1egay8yehza.cloudfront.net/edx-edx101/EDXSPCPJSP13-H010000_100.mp4')
            # self.log.info(units)

    def test_extract_units_from_html_multiple_units(self):
        with open("test/html/courses.edx.org/courses/edX/DemoX.1/2014/courseware/0af8db2309474971bfa70cda98668a30/ec3364075f2845baa625bfecd5970410", "r") as myfile:
            page = myfile.read()
            units = edx_dl.extract_units_from_html(page)
            self.assertEquals(len(units), 3)


if __name__ == '__main__':
    logging.basicConfig(stream=sys.stdout)
    logging.getLogger("TestEdX").setLevel(logging.DEBUG)
    suite = unittest.TestLoader().loadTestsFromTestCase(TestEdX)
    unittest.TextTestRunner(verbosity=2).run(suite)
