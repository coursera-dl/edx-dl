#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import json
import logging
import sys
import unittest


from edx_dl.parsing import edx_json2srt


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


if __name__ == '__main__':
    logging.basicConfig(stream=sys.stdout)
    logging.getLogger("TestParsing").setLevel(logging.DEBUG)
    suite = unittest.TestLoader().loadTestsFromTestCase(TestParsing)
    unittest.TextTestRunner(verbosity=2).run(suite)
