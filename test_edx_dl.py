#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import sys
import unittest

from edx_dl import edx_dl, parsing

class TestEdX(unittest.TestCase):

    def setUp(self):
        self.log = logging.getLogger("TestEdX")

    def test_failed_login(self):
        resp = edx_dl.edx_login(
            edx_dl.LOGIN_API, edx_dl.edx_get_headers(), "guest", "guest")
        self.assertFalse(resp.get('success', False))

    def test_remove_repeated_urls(self):
        url = "test/html/multiple_units.html"
        with open(url, "r") as f:
            all_units = {url:
                         parsing.NewEdXPageExtractor().extract_units_from_html(f.read(),
                                                         'https://courses.edx.org')}
            filtered_units = edx_dl.remove_repeated_urls(all_units)
            num_all_urls = edx_dl.num_urls_in_units_dict(all_units)
            num_filtered_urls = edx_dl.num_urls_in_units_dict(filtered_units)
            self.assertEquals(num_all_urls, 18)
            self.assertEquals(num_filtered_urls, 16)
            self.assertNotEquals(num_all_urls, num_filtered_urls)


if __name__ == '__main__':
    logging.basicConfig(stream=sys.stdout)
    logging.getLogger("TestEdX").setLevel(logging.DEBUG)
    suite = unittest.TestLoader().loadTestsFromTestCase(TestEdX)
    unittest.TextTestRunner(verbosity=2).run(suite)
