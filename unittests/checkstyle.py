#!/usr/bin/env python3
"""
Check that PEP8 format is followed
"""
import subprocess

def check_format(pyFilePath):
    """Check format of Python file. """
    print("="*60)
    runStr = f"pycodestyle -v {pyFilePath}"
    subproc = subprocess.run(runStr, shell=True, capture_output=True)
    print(subproc.stdout.decode('UTF-8'), end='')
    print("="*60)

check_format("../optionset/optionset.py")
check_format("runtests.py")
check_format("timetest.py")
