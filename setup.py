#!/usr/bin/env python3
"""
Setup file for optionset.

:copyright: 2020 by optionset authors, see AUTHORS for more details.
:license: GPLv3, see LICENSE for more details.
"""

import os
import sys

from setuptools import setup

from optionset import __version__, __author__

scriptList = ["optionset/optionset.py", ]

if __name__ == "__main__":
    with open("README.rst", "r") as fh:
        long_description = fh.read()

    setup(
        name='optionset',
        packages=['optionset', ],
        version=__version__,
        description=("A lightweight tool for conducting parameter studies."),
        long_description=long_description,
        long_description_content_type="text/x-rst",
        url="https://github.com/DrHobo/optionset",
        author=__author__,
        author_email="matt.c.jones.aoe@gmail.com",
        scripts=scriptList,
        license="GPLv3",
        classifiers=[
            "Development Status :: 5 - Production/Stable",
            "Intended Audience :: Developers",
            "Intended Audience :: Information Technology",
            "Intended Audience :: Science/Research",
            "Intended Audience :: System Administrators",
            "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
            "Natural Language :: English",
            "Operating System :: OS Independent",
            "Topic :: Scientific/Engineering",
            "Topic :: Software Development",
            "Topic :: Software Development :: Interpreters",
            "Topic :: Software Development :: Pre-processors",
            "Topic :: Software Development :: User Interfaces",
            "Topic :: Text Processing",
            "Topic :: Text Processing :: General",
            "Topic :: Text Processing :: Indexing",
            "Topic :: Utilities",
            "Programming Language :: Python :: 3.7",
            "Programming Language :: Python :: 3.8",
            "Programming Language :: Python :: 3.9",
            "Programming Language :: Unix Shell",
        ],
        keywords=['utility', 'macro-processor'],
        install_requires=None,
    )
