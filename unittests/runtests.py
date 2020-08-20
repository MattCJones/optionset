#!/usr/bin/env python3
"""
Run unit tests on optionset.
"""
import unittest
import re
import subprocess
import shlex

RUNAPP = "../bin/optionset.py" # run the application

def test_re(regex, strToSearch):
    """Test that regex expression works for given strToSearch"""
    if regex.search(strToSearch):
        return True
    else:
        return False

def run_cmd(cmdStr):
    """Run a command and return the output"""
    subproc = subprocess.run(shlex.split(cmdStr), capture_output=True)
    outStr = subproc.stdout.decode('UTF-8')
    return outStr, subproc.returncode

class TestIO(unittest.TestCase):
    """Test input and output"""
    def setUp(self):
        pass

    def test_basic_io(self):
        """Test basic input and output"""
        reHasInputErr = re.compile(".*InputError.*")
        outputStr, _ = run_cmd(f"{RUNAPP}")
        self.assertTrue(test_re(reHasInputErr, outputStr))

        reShowsUsage = re.compile("^usage:.*")
        outputStr, _ = run_cmd(f"{RUNAPP} -h")
        self.assertTrue(test_re(reShowsUsage, outputStr))

    def test_ignored(self):
        """Test ignored files and directories"""
        reHasIgnoreStr = re.compile(".*shouldIgnore.*")
        outputStr, _ = run_cmd(f"{RUNAPP} -a")
        self.assertFalse(test_re(reHasIgnoreStr, outputStr))

    def test_extensions(self):
        """Test various valid file extensions"""
        outputStr, _ = run_cmd(f"{RUNAPP} -a")
        extensionStrs = ('dat', 'nml', 'none', 'txt', 'org', 'orig', 'yaml',)
        for extensionStr in extensionStrs:
            reHasExtension = re.compile(f".*{extensionStr}.*")
            self.assertTrue(test_re(reHasExtension, outputStr))

class TestValid(unittest.TestCase):
    """Test valid options"""
    def setUp(self):
        pass

    def test_extensions(self):
        """Test various valid file extensions"""
        outputStr, _ = run_cmd(f"{RUNAPP} -a")
        extensionStrs = ('dat', 'nml', 'none', 'txt', 'org', 'orig', 'yaml',)
        for extensionStr in extensionStrs:
            reHasExtension = re.compile(f".*{extensionStr}.*")
            self.assertTrue(test_re(reHasExtension, outputStr))



if __name__ == '__main__':
    unittest.main()
