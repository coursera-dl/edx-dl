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

    def test_extract_units_from_html_single_unit_multiple_subs(self):
        with open("test/html/courses.edx.org/courses/edX/DemoX.1/2014/courseware/6156e0e685ee4a2ab017258108c0bccd/194bd1729fab47aba6507f737d9b90ba", "r") as myfile:
            page = myfile.read()
            units = edx_dl.extract_units_from_html(page)
            headers ={}
            subtitles_download_urls = edx_dl.get_subtitles_download_urls(units[0].available_subs_url,
                                                                         units[0].sub_template_url,
                                                                         headers)

            self.assertTrue('https://courses.edx.org/courses/edX/DemoX.1/2014/xblock/i4x:;_;_edX;_DemoX.1;_video;_14459340170c476bb65f73a0a08a076f/handler/transcript/translation/en' in subtitles_download_urls.values())
            # FIXME once that correct headers are passed test for 'zh' language and this:
            # self.assertEquals(len(subtitles_download_urls), 2)

    def test_extract_units_from_html_multiple_units(self):
        with open("test/html/courses.edx.org/courses/edX/DemoX.1/2014/courseware/0af8db2309474971bfa70cda98668a30/ec3364075f2845baa625bfecd5970410", "r") as myfile:
            page = myfile.read()
            units = edx_dl.extract_units_from_html(page)
            self.assertEquals(len(units), 3)

    def test_extract_units_from_html_multiple_units_multiple_youtube_ids(self):
        with open("test/html/courses.edx.org/courses/BerkeleyX/Stat2.1x/2013_Spring/courseware/36bcbc2a9dbd4f4b8546f13c035b2759/85a8eeb47206447ca769f74d93d3db6c", "r") as myfile:
            page = myfile.read()
            units = edx_dl.extract_units_from_html(page)
            self.assertEquals(len(units), 3)
            self.assertEquals(units[0].video_youtube_url, 'https://youtube.com/watch?v=23kSGHRaLlI')

    def test_extract_units_from_html_multiple_units_multiple_videos_and_pdf(self):
        with open("test/html/courses.edx.org/courses/BerkeleyX/CS184.1x/2012_Fall/courseware/Unit_0/L1", "r") as myfile:
            page = myfile.read()
            units = edx_dl.extract_units_from_html(page)
            self.assertEquals(len(units), 3)
            self.assertTrue('https://s3.amazonaws.com/berkeley-cs184x/videos/overview-motivation.mp4' in units[0].mp4_urls)
            self.assertEquals(units[0].pdf_urls[0], 'https://courses.edx.org/static/content-berkeley-cs184x~2012_Fall/slides/overview.pdf')


if __name__ == '__main__':
    logging.basicConfig(stream=sys.stdout)
    logging.getLogger("TestEdX").setLevel(logging.DEBUG)
    suite = unittest.TestLoader().loadTestsFromTestCase(TestEdX)
    unittest.TextTestRunner(verbosity=2).run(suite)
