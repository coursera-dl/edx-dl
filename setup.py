# -*- coding: utf-8 -*-

from setuptools import setup

# you can install this to a local test virtualenv like so:
#   virtualenv venv
#   ./venv/bin/pip install --editable .
#   ./venv/bin/pip install --editable .[dev]  # with dev requirements, too

#
# FIXME: This won't work until we have a README file in .rst format (which
# is what PyPI knows how to parse).  In the mean time, we can use the following:
#
# pandoc --from=markdown --to=rst --output=README.rst README.md
#

setup(
    name='edx-dl',
    version='0.0',
    maintainer='FIXME',
    maintainer_email='FIXME@example.com',

    license='LGPL',
    url='https://github.com/shk3/edx-downloader',

    install_requires=open('requirements.txt').readlines(),
    # FIXME: For later
    # extras_require=dict(
    #     dev=open('requirements-dev.txt').readlines()
    # ),

    description='A simple tool to download video lectures from edx.org.',
    long_description=open('README.rst', 'r').read(),
    keywords=['exX', 'download', 'education', 'MOOCs', 'video', 'FIXME'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: GNU Lesser General Public License v3 or later (LGPLv3+)',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',  # FIXME: confirm
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Programming Language :: Python',
        'Topic :: Education',
    ],

    packages=["edx_dl"],
    entry_points=dict(
        console_scripts=[
            'edx-dl=edx_dl.edx_dl:main'
        ]
    ),

    platforms=['any'],
)
