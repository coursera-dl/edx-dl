# -*- coding: utf-8 -*-
#
# you can install this to a local test virtualenv like so:
#   virtualenv venv
#   ./venv/bin/pip install --editable .
#   ./venv/bin/pip install --editable .[dev]  # with dev requirements, too

from __future__ import print_function

import os.path
import subprocess
import sys

from setuptools import setup

from edx_dl._version import __version__


def read_file(filename, alt=None):
    """
    Read the contents of filename or give an alternative result instead.
    """
    lines = None

    try:
        with open(filename) as f:
            lines = f.read()
    except IOError:
        lines = [] if alt is None else alt
    return lines


long_description = read_file(
    'README.md',
    'Cannot find README.md'
)
requirements = read_file('requirements.txt')
dev_requirements = read_file('requirements-dev.txt')

trove_classifiers = [
    'Development Status :: 4 - Beta',
    'Environment :: Console',
    'Intended Audience :: End Users/Desktop',
    'License :: OSI Approved :: GNU Lesser General Public License v3 or later (LGPLv3+)',
    'Operating System :: OS Independent',
    'Programming Language :: Python :: 2',
    'Programming Language :: Python :: 2.7',
    'Programming Language :: Python :: 3',
    'Programming Language :: Python :: 3.4',
    'Programming Language :: Python :: 3.5',
    'Programming Language :: Python :: 3.6',
    'Programming Language :: Python :: 3.7',
    'Programming Language :: Python :: Implementation :: CPython',
    'Programming Language :: Python :: Implementation :: PyPy',
    'Programming Language :: Python',
    'Topic :: Education',
]

setup(
    name='edx-dl',
    version=__version__,
    maintainer='Ismaël Mejía, Rogério Theodoro de Brito, Yuri Bochkarev',
    maintainer_email='iemejia@gmail.com, rbrito@ime.usp.br, baltazar.bz@gmail.com',

    license='LGPL',
    url='https://github.com/coursera-dl/edx-dl',

    install_requires=requirements,
    extras_require={
        'dev': dev_requirements,
    },

    description='Simple tool to download video and lecture materials from edx.org.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    keywords=['edx-dl','edX', 'download', 'education', 'MOOCs', 'video'],
    classifiers=trove_classifiers,

    packages=["edx_dl"],
    entry_points=dict(
        console_scripts=[
            'edx-dl=edx_dl.edx_dl:main'
        ]
    ),

    platforms=['any'],
)
