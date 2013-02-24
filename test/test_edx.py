#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Unit tests for the edx module.
"""

import unittest

from edx_dl import edx_dl


class TestEdx(unittest.TestCase):  # pylint: disable-msg=R0904
    """
    Unit tests for edx_dl.
    """
    def setUp(self):  # pylint: disable-msg=C0103
        self.token = edx_dl.get_initial_token()

    def test_initial_token(self):
        """
        Test acquisition of the CSRF (Cross-Site Request Forgery) token from
        edx.org.
        """
        self.assertNotEqual(self.token, '')


if __name__ == '__main__':
    unittest.main()
