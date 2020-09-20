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
    with open("README.md", "r") as fh:
        longDescription = fh.read()

    setup(
        name='optionset',
        version=__version__,
        packages=['optionset', ],
        description="Enable/disable user-predefined options in text-based "
        "dictionaries",
        long_description=longDescription,
        long_description_content_type="text/markdown",
        url=None,
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
            "Natural Language :: English",
            "Operating System :: OS Independent",
            "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
            "Topic :: Scientific/Engineering",
            "Topic :: Software Development",
            "Topic :: Software Development :: Pre-processors",
            "Topic :: Text Processing",
            "Topic :: Utilities",
            "Programming Language :: Python :: 3.4",
            "Programming Language :: Python :: 3.5",
            "Programming Language :: Python :: 3.6",
            "Programming Language :: Python :: 3.7",
            "Programming Language :: Python :: 3.8",
            "Programming Language :: Python :: 3.9",
        ],
        keywords='utility tool',
        install_requires=None,
    )
