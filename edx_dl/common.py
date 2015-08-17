# -*- coding: utf-8 -*-

"""
Common type definitions and constants for edx-dl
"""


# The next four classes represent the structure of courses in edX.  The
# structure is:
#
# * A Course contains Sections
# * Each Section contains Subsections
# * Each Subsection contains Units
#
# Notice that we don't represent the full tree structure for both performance
# and UX reasons:
#
# Course ->  [Section] -> [SubSection] -> [Unit] -> [Video]
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
# 4. The units can contain multiple videos:
#    Unit -> [Video]
#

class Course(object):
    def __init__(self, id, name, url, state):
        self.id = id
        self.name = name
        self.url = url
        self.state = state


class Section(object):
    def __init__(self, position, name, url, subsections):
        self.position = position
        self.name = name
        self.url = url
        self.subsections = subsections


class SubSection(object):
    def __init__(self, position, name, url):
        self.position = position
        self.name = name
        self.url = url


class Unit(object):
    def __init__(self, videos, resources_urls):
        self.videos = videos
        self.resources_urls = resources_urls


class Video(object):
    def __init__(self, video_youtube_url, available_subs_url,
                 sub_template_url, mp4_urls):
        self.video_youtube_url = video_youtube_url
        self.available_subs_url = available_subs_url
        self.sub_template_url = sub_template_url
        self.mp4_urls = mp4_urls


YOUTUBE_DL_CMD = ['youtube-dl', '--ignore-config']
DEFAULT_CACHE_FILENAME = 'edx-dl.cache'
