# -*- coding: utf-8 -*-

"""
Common type definitions and constants for edx-dl
"""
from collections import namedtuple


# The next four named tuples represent the structure of courses in edX.  The
# structure is:
#
# * A Course contains Sections
# * Each Section contains Subsections
# * Each Subsection contains Units
#
# Notice that we don't represent the full tree structure for both performance
# and UX reasons:
#
# Course ->  [Section] -> [SubSection] -> [Unit]
#
# In the script the data structures used are:
#
# 1. The data structures to represent the course information:
#    Course, Section->[SubSection]
#
# 2. The data structures to represent the chosen courses and sections:
#    selections = {Course, [Section]}
#
# 3. The data structure of all the downloable resources which represent each
#    subsection via its URL and the of resources who can be extracted from the
#    Units it contains:
#    all_units = {Subsection.url: [Unit]}
#
Course = namedtuple('Course', ['id', 'name', 'url', 'state'])
Section = namedtuple('Section', ['position', 'name', 'url', 'subsections'])
SubSection = namedtuple('SubSection', ['position', 'name', 'url'])
Unit = namedtuple('Unit',
                  ['video_youtube_url', 'available_subs_url',
                   'sub_template_url', 'mp4_urls', 'resources_urls'])

YOUTUBE_DL_CMD = ['youtube-dl', '--ignore-config']
DEFAULT_CACHE_FILENAME = 'edx-dl.cache'
