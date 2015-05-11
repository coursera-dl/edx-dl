#!/usr/bin/env python
# -*- coding: utf-8 -*-

import edx_dl
import unittest


class TestEdX(unittest.TestCase):

    def setUp(self):
        return

    def test_failed_login(self):
        resp = edx_dl.edx_login(
            edx_dl.LOGIN_API, edx_dl.edx_get_headers(), "guest", "guest")
        self.assertFalse(resp.get('success', False))

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestEdX)
    unittest.TextTestRunner(verbosity=2).run(suite)
