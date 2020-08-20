#!/usr/bin/env python3
"""
Setup file for optionset.
"""
from setuptools import setup

import glob
import os
import sys

from src.optionset import __version__, __author__

scriptlist = glob.glob(os.path.join('bin', '*.py'))

sys.path.insert(0, "src")

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name='optionset',
    version=__version__,
    packages=['optionset', ],
    package_dir={'':'src'},
    description="Enable/disable user-predefined options in text-based dictionaries",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url=None,
    author=__author__,
    author_email="matt.c.jones.aoe@gmail.com",
    scripts=scriptlist,
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
