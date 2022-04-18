#!/usr/bin/env python3
"""
Check that PEP8 format is followed

Author: Matthew C. Jones
Email: matt.c.jones.aoe@gmail.com

:copyright: 2020 by Optionset authors, see AUTHORS for more details.
:license: GPLv3, see LICENSE for more details.
"""

import os

from shlex import split
from shutil import which
from subprocess import run


def check_format(py_file_path):
    """Check format of a Python file. """
    run_str = f"pycodestyle -v {py_file_path}"
    run(split(run_str))
    print("")


print("="*60)
print("Running pycodestyle")
print("="*60)
check_format("../optionset/optionset.py")
check_format("runtests.py")
check_format("timetest.py")

if which('flake8'):
    print("="*60)
    print("Running flake8")
    print("="*60)
    os.chdir("../optionset")
    run("flake8")
