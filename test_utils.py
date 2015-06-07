#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import logging
import sys
import unittest

import six

from edx_dl import utils


class TestUtils(unittest.TestCase):

    def setUp(self):
        self.log = logging.getLogger('TestUtils')

    def test_clean_filename(self):
        strings = {
            '(23:90)': '23-90',
            '(:': '-',
            'a téest &and a@noòtheèr': 'a_test_and_another',
            'Lecture 2.7 - Evaluation and Operators (16:25)':
            'Lecture_2.7_-_Evaluation_and_Operators_16-25',
            'Week 3: Data and Abstraction':
            'Week_3-_Data_and_Abstraction',
            '  (Week 1) BRANDING:  Marketing Strategy and Brand Positioning':
            'Week_1_BRANDING-__Marketing_Strategy_and_Brand_Positioning',
            'test &amp; &quot; adfas': 'test___adfas',
            '&nbsp;': ''
        }
        for k, v in six.iteritems(strings):
            actual_res = utils.clean_filename(k)
            self.assertEquals(actual_res, v, actual_res)

    def test_clean_filename_minimal_change(self):
        strings = {
            '(23:90)': '(23-90)',
            '(:': '(-',
            'a téest &and a@noòtheèr': 'a téest &and a@noòtheèr',
            'Lecture 2.7 - Evaluation and Operators (16:25)':
            'Lecture 2.7 - Evaluation and Operators (16-25)',
            'Week 3: Data and Abstraction':
            'Week 3- Data and Abstraction',
            '  (Week 1) BRANDING:  Marketing Strategy and Brand Positioning':
            '  (Week 1) BRANDING-  Marketing Strategy and Brand Positioning',
            'test &amp; &quot; adfas': 'test & " adfas',
            '&nbsp;': u'\xa0'
        }
        for k, v in six.iteritems(strings):
            actual_res = utils.clean_filename(k, minimal_change=True)
            self.assertEquals(actual_res, v, actual_res)

    def test_execute_command(self):
        actual_res = utils.execute_command(['ls', '--help'])
        self.assertEquals(actual_res, 0, actual_res)

        actual_res = utils.execute_command(['ls', '--help-does-not-exist'])
        self.assertEquals(actual_res, 2, actual_res)

    def test_get_filename_from_prefix(self):
        target_dir = '.'

        cases = {
            'requirements.txt': 'requirements',
            'does-not-exist': None,
            # 'requirements': 'requirements-dev', # depends on filesystem!
        }

        for k, v in six.iteritems(cases):
            actual_res = utils.get_filename_from_prefix(target_dir, k)
            self.assertEquals(actual_res, v, actual_res)


if __name__ == '__main__':
    logging.basicConfig(stream=sys.stdout)
    logging.getLogger("TestUtils").setLevel(logging.DEBUG)
    suite = unittest.TestLoader().loadTestsFromTestCase(TestUtils)
    unittest.TextTestRunner(verbosity=2).run(suite)
