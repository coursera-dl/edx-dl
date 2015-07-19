#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import subprocess

import pytest
import six

from edx_dl import utils


def test_clean_filename():
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
        assert actual_res == v, actual_res


def test_clean_filename_minimal_change():
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
        assert actual_res == v, actual_res


@pytest.mark.skipif(True,
                    reason="Needs change in interface")
def test_execute_command_should_succeed():
    actual_res = utils.execute_command(['ls', '--help'])
    assert actual_res == 0, actual_res


@pytest.mark.skipif(True,
                    reason="Needs change in interface")
def test_execute_command_should_fail():
    try:
        actual_res = utils.execute_command(['ls', '--help-does-not-exist'])
    except subprocess.CalledProcessError as e:
        assert True, "Expected exception thrown."
    else:
        assert False, "Unexpected exception (or no exception) thrown"

    # For the future
    # actual_res == 2, actual_res


def test_get_filename_from_prefix():
    target_dir = '.'

    cases = {
        'requirements.txt': 'requirements',
        'does-not-exist': None,
        # 'requirements': 'requirements-dev', # depends on filesystem!
    }

    for k, v in six.iteritems(cases):
        actual_res = utils.get_filename_from_prefix(target_dir, k)
        assert actual_res == v, actual_res


def test_remove_duplicates_without_seen():
    empty_set = set()
    lists = [
        ([], [], empty_set),
        ([1], [1], {1}),
        ([1, 1], [1], {1}),

        ([None], [None], {None}),
        ([None, None], [None], {None}),
        ([1, None], [1, None], {1, None}),

        (['a'], ['a'], {'a'}),
        (['a', 'a'], ['a'], {'a'}),
        (['a', 'b'], ['a', 'b'], {'a', 'b'}),

        (['a', 'b', 'a'], ['a', 'b'], {'a', 'b'}),
        (['a', 'a', 'b'], ['a', 'b'], {'a', 'b'}),
        (['b', 'a', 'b'], ['b', 'a'], {'a', 'b'}),
        (['b', 'a', 'a'], ['b', 'a'], {'a', 'b'}),

        ([1, 2, 1, 2], [1, 2], {1, 2}),
    ]
    for l, reduced_l, seen in lists:
        actual_res = utils.remove_duplicates(l)
        assert actual_res == (reduced_l, seen), actual_res


def test_remove_duplicates_with_seen():
    empty_set = set()
    lists = [
        ([], empty_set, [], empty_set),
        ([], {None}, [], {None}),
        ([], {1}, [], {1}),
        ([], {1, 2}, [], {1, 2}),

        ([1], empty_set, [1], {1}),
        ([1], {1}, [], {1}),

        ([1, 1], empty_set, [1], {1}),
        ([1, 1], {1}, [], {1}),
        ([1, 1], {None}, [1], {1, None}),
        ([1, 1], {2}, [1], {1, 2}),
        ([1, 1], {1, 2}, [], {1, 2}),

        ([None], empty_set, [None], {None}),
        ([None], {1}, [None], {1, None}),
        ([None], {1, 2}, [None], {1, 2, None}),
        ([None], {1, 2}, [None], {2, 1, None}),
        ([None], {1, 2}, [None], {None, 2, 1}),
        ([None], {1, 2}, [None], {2, None, 1}),
        ([None], {1, 2, None}, [], {1, 2, None}),

        ([1, None], empty_set, [1, None], {1, None}),
        ([1, None], {1}, [None], {1, None}),
        ([1, None], {None}, [1], {1, None}),
        ([1, None], {1, None}, [], {1, None}),
        ([1, None], {1, None, 2}, [], {1, None, 2}),

        ([None, 1], empty_set, [None, 1], {1, None}),
        ([None, 1], {1}, [None], {1, None}),
        ([None, 1], {None}, [1], {1, None}),
        ([None, 1], {1, None}, [], {1, None}),
        ([None, 1], {1, None, 2}, [], {1, None, 2}),

        (['a'], empty_set, ['a'], {'a'}),
        (['a'], {'a'}, [], {'a'}),
        (['a'], {None}, ['a'], {'a', None}),
        (['a'], {'b'}, ['a'], {'a', 'b'}),
        (['a'], {'a', 'b'}, [], {'a', 'b'}),

        (['a'], {'a', 'b', tuple()}, [], {'a', 'b', tuple()}),


        # (['a', 'a'], ['a'], {'a'}),
        # (['a', 'b'], ['a', 'b'], {'a', 'b'}),
        # (['a', 'b', 'a'], ['a', 'b'], {'a', 'b'}),
        # (['a', 'a', 'b'], ['a', 'b'], {'a', 'b'}),
        # (['b', 'a', 'b'], ['b', 'a'], {'a', 'b'}),
        # (['b', 'a', 'a'], ['b', 'a'], {'a', 'b'}),
        # ([1, 2, 1, 2], [1, 2], {1, 2}),
        # ([1, 2, 1, 2], [1, 2], {1, 2}),
    ]
    for l, seen_before, reduced_l, seen_after in lists:
        actual_res = utils.remove_duplicates(l, seen_before)
        assert actual_res == (reduced_l, seen_after), actual_res
